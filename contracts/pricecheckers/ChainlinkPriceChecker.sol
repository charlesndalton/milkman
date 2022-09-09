// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "../../interfaces/IPriceChecker.sol";

interface IPriceFeed {
    function latestAnswer() external view returns (int256);

    function decimals() external view returns (uint8);
}

/**
 * @notice Checks a swap against Chainlink-compatible price feeds.
 * @dev This price checker doesn't care about how long ago the price feed answer was. Another price checker can be built if this is desired.
 */
contract ChainlinkPriceChecker is IPriceChecker {
    using SafeMath for uint256;

    uint256 internal constant MAX_BPS = 10_000;

    /**
     * @param _data Encoded [maxSlippage, priceFeeds, reverses].
     *
     * maxSlippage (optional<uint>): Number of basis points of acceptable slippage (e.g., 500 for 5% slippage). If 0 is passed in, the default is 300 (3%).
     * priceFeeds (address[]): The price feeds to route through. For example, if the user is swapping BAT -> ALCX, this would contain the BAT/ETH and ALCX/ETH price feeds.
     * reverses (bool[]): For each price feed, whether or not it should be reversed. For example, if a user was swapping USDC for XYZ, they would pass in the XYZ/USD price feed and set reversed[0] to true.
     *
     * Some examples:
     * BOND -> ETH w/ default slippage: [0, [bond-eth.data.eth], [false]]
     * ETH -> BOND w/ 5% slippage: [500, [bond-eth.data.eth], [true]]
     * BOND -> DAI w/ default slippage: [0, [bond-eth.data.eth, eth-usd.data.eth], [false, false]]
     * alternative w/ better precision: [0, [both-eth.data.eth, eth-usd.data.eth, dai-usd.data.eth], [false, false, true]]
     * BOND -> YFI w/ 0.5% slippage: [50, [bond-eth.data.eth, yfi-eth.data.eth], [false, true]]
     * BOND -> FXS w/ 7% slippage (FXS has no fxs-eth feed): [700, [bond-eth.data.eth, eth-usd.data.eth, fxs-usd.data.eth], [false, false, true]]
     */
    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256 _minOut,
        bytes calldata _data
    ) external view override returns (bool) {
        (
            uint256 _maxSlippage,
            address[] memory _priceFeeds,
            bool[] memory _reverses
        ) = abi.decode(_data, (uint256, address[], bool[]));

        if (_maxSlippage == 0) {
            _maxSlippage = 300;
        }
        require(_maxSlippage <= 10_000); // dev: max slippage too high

        uint256 _expectedOutFromChainlink = getExpectedOutFromChainlink(
            _priceFeeds,
            _reverses,
            _amountIn
        ); // how much Chainlink says we'd get out of this trade

        return
            _expectedOutFromChainlink.mul(MAX_BPS - _maxSlippage).div(MAX_BPS) <
            _minOut &&
            _minOut <
            _expectedOutFromChainlink.mul(MAX_BPS + _maxSlippage).div(MAX_BPS);
    }

    function getExpectedOutFromChainlink(
        address[] memory _priceFeeds,
        bool[] memory _reverses,
        uint256 _amountIn
    ) internal view returns (uint256 _expectedOutFromChainlink) {
        uint256 _priceFeedsLen = _priceFeeds.length;

        require(_priceFeedsLen > 0); // dev: need to pass at least one price feed
        require(_priceFeedsLen == _reverses.length); // dev: price feeds and reverse need to have the same length

        for (uint256 _i = 0; _i < _priceFeedsLen; _i++) {
            IPriceFeed _priceFeed = IPriceFeed(_priceFeeds[_i]);

            int256 _latestAnswer = _priceFeed.latestAnswer();
            {
                require(_latestAnswer > 0); // dev: latest answer from the price feed needs to be positive
            }

            uint256 _scaleAnswerBy = 10**uint256(_priceFeed.decimals());

            // If it's first iteration, use amountIn to calculate. Else, use the result from the previous iteration.
            uint256 _amountIntoThisIteration = _i == 0
                ? _amountIn
                : _expectedOutFromChainlink;

            // Without a reverse, we multiply amount * price
            // With a reverse, we divide amount / price
            _expectedOutFromChainlink = _reverses[_i]
                ? _amountIntoThisIteration.mul(_scaleAnswerBy).div(
                    uint256(_latestAnswer)
                )
                : _amountIntoThisIteration.mul(uint256(_latestAnswer)).div(
                    _scaleAnswerBy
                );
        }
    }
}
