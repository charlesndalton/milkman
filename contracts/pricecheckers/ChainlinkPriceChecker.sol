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

/// @notice Checks a swap against Chainlink-compatible price feeds. For example, someone doing a BAT -> ALCX swap would pass in addresses to the BAT/USD feed and the ALCX/USD feed. The price checker would check that the conversion rate between these two is roughly equivalent to _amountIn / _minOut.
/// @dev This price checker doesn't care about how long ago the price feed answer was. Another price checker can be built if this is desired.
contract ChainlinkPriceChecker is IPriceChecker {
    using SafeMath for uint256;

    uint256 internal constant MAX_BPS = 10_000;

    /// @param _data Encoded [maxSlippage, priceFeed[0], priceFeed[1], ...], where `maxSlippage` is in basis points and defaults to 3% (300), and `priceFeed[x]` is an addresss that implements the Chainlink interface.
    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256 _minOut,
        bytes calldata _data
    ) external view override returns (bool) {
        (uint256 _maxSlippage, address[] memory _priceFeeds) = abi.decode(
            _data,
            (uint256, address[])
        );

        if (_maxSlippage == 0) {
            _maxSlippage = 300;
        }
        require(_maxSlippage <= 10_000); // dev: max slippage too high

        uint256 _expectedOutFromChainlink = getExpectedOutFromChainlink(
            _priceFeeds,
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
        uint256 _amountIn
    ) internal view returns (uint256 _expectedOutFromChainlink) {
        uint256 _priceFeedsLen = _priceFeeds.length;

        require(_priceFeedsLen > 0); // dev: need to pass at least one price feed

        for (uint256 _i = 0; _i < _priceFeedsLen; _i++) {
            IPriceFeed _priceFeed = IPriceFeed(_priceFeeds[_i]);

            int256 _latestAnswer = _priceFeed.latestAnswer();
            {
                require(_latestAnswer > 0); // dev: latest answer from the price feed needs to be positive
            }

            uint256 _scaleAnswerBy = 10**uint256(_priceFeed.decimals());
            // if this is first price feed, multiply amountIn by latest answer (e.g., amount of BAT * price of BAT in ETH)
            // else, divide previous answer by latest answer (e.g., (amount of BAT * price of BAT in ETH) / price of ETH in ALCX)
            // note that we're assuming that the pairs need to be reversed
            _expectedOutFromChainlink = _i == 0
                ? _amountIn.mul(uint256(_latestAnswer)).div(_scaleAnswerBy)
                : _expectedOutFromChainlink.mul(_scaleAnswerBy).div(
                    uint256(_latestAnswer)
                );
        }
    }
}
