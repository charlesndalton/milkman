// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {IExpectedOutCalculator} from "./IExpectedOutCalculator.sol";

interface IPriceFeed {
    function latestAnswer() external view returns (int256);

    function decimals() external view returns (uint8);
}

interface IERC20MetaData {
    function decimals() external view returns (uint8);
}

/**
 * @notice Checks a swap against Chainlink-compatible price feeds.
 * @dev Doesn't care about how long ago the price feed answer was. Another expected out calculator can be built if this is desired.
 */
contract ChainlinkExpectedOutCalculator is IExpectedOutCalculator {
    using SafeMath for uint256;

    uint256 internal constant MAX_BPS = 10_000;

    /**
     * @param _data Encoded [priceFeeds, reverses].
     *
     * priceFeeds (address[]): The price feeds to route through. For example, if the user is swapping BAT -> ALCX, this would contain the BAT/ETH and ALCX/ETH price feeds.
     * reverses (bool[]): For each price feed, whether or not it should be reversed. For example, if a user was swapping USDC for XYZ, they would pass in the XYZ/USD price feed and set reversed[0] to true.
     *
     * Some examples:
     * BOND -> ETH: [bond-eth.data.eth], [false]]
     * ETH -> BOND: [[bond-eth.data.eth], [true]]
     * BOND -> DAI: [bond-eth.data.eth, eth-usd.data.eth], [false, false]]
     * alternative: [both-eth.data.eth, eth-usd.data.eth, dai-usd.data.eth], [false, false, true]]
     * BOND -> YFI: [[bond-eth.data.eth, yfi-eth.data.eth], [false, true]]
     * BOND -> FXS (FXS has no fxs-eth feed): [[bond-eth.data.eth, eth-usd.data.eth, fxs-usd.data.eth], [false, false, true]]
     */
    function getExpectedOut(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        bytes calldata _data
    ) external view override returns (uint256) {
        (address[] memory _priceFeeds, bool[] memory _reverses) = abi.decode(
            _data,
            (address[], bool[])
        );

        return
            getExpectedOutFromChainlink(
                _priceFeeds,
                _reverses,
                _amountIn,
                _fromToken,
                _toToken
            ); // how much Chainlink says we'd get out of this trade
    }

    function getExpectedOutFromChainlink(
        address[] memory _priceFeeds,
        bool[] memory _reverses,
        uint256 _amountIn,
        address _fromToken,
        address _toToken
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

        uint256 _fromTokenDecimals = uint256(
            IERC20MetaData(_fromToken).decimals()
        );
        uint256 _toTokenDecimals = uint256(IERC20MetaData(_toToken).decimals());

        if (_fromTokenDecimals > _toTokenDecimals) {
            // if fromToken has more decimals than toToken, we need to divide
            _expectedOutFromChainlink = _expectedOutFromChainlink.div(
                10**_fromTokenDecimals.sub(_toTokenDecimals)
            );
        } else if (_fromTokenDecimals < _toTokenDecimals) {
            _expectedOutFromChainlink = _expectedOutFromChainlink.mul(
                10**_toTokenDecimals.sub(_fromTokenDecimals)
            );
        }
    }
}
