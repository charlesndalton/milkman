// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "./PriceCheckerLib.sol";

import "../../interfaces/IPriceChecker.sol";

/**
 * @notice A price checker that itself uses multiple price checkers. For example, for a BOND -> DOT swap, a user could use a UNIV3 price checker for BOND -> USDC and then a Chainlink price checker for USDC -> DOT.
 */
contract MetaPriceChecker is IPriceChecker {
    using SafeMath for uint256;

    /**
     * @param _data Encoded [maxSlippage, priceCheckers, priceCheckerData].
     *
     * maxSlippage (optional<uint>): Number of basis points of acceptable slippage (e.g., 500 for 5% slippage). If 0 is passed in, the default is 300 (3%).
     * priceCheckers (address[]): The price checkers to route through.
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
        uint256,
        uint256 _minOut,
        bytes calldata _data
    ) external view override returns (bool) {}
}
