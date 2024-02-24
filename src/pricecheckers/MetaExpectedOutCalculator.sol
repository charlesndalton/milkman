// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {IExpectedOutCalculator} from "./IExpectedOutCalculator.sol";

/**
 * @notice Uses multiple other expected out calculators to generate an expected out.
 */
contract MetaExpectedOutCalculator is IExpectedOutCalculator {
    using SafeMath for uint256;

    /**
     * @param _data Encoded [swapPath, priceCheckers, priceCheckerData].
     *
     * swapPath (address[]): List of ERC20s to swap through.
     * expectedOutCalculators (address[]): List of expected out calculators to use.
     * expectedOutCalculatorData (bytes[]): List of bytes to pass to each expected out calculator
     */
    function getExpectedOut(uint256 _amountIn, address _fromToken, address _toToken, bytes calldata _data)
        external
        view
        override
        returns (uint256)
    {
        (
            address[] memory _swapPath, address[] memory _expectedOutCalculators, bytes[] memory _expectedOutCalculatorData
        ) = abi.decode(_data, (address[], address[], bytes[]));

        require(
            _swapPath.length.sub(1) == _expectedOutCalculators.length
                && _expectedOutCalculators.length == _expectedOutCalculatorData.length,
            "invalid_length"
        );

        uint256 _runningExpectedOut;
        for (uint256 i = 0; i < _swapPath.length.sub(1); i++) {
            _runningExpectedOut =
                i == 0
                ? IExpectedOutCalculator(_expectedOutCalculators[i]).getExpectedOut(
                    _amountIn, _swapPath[i], _swapPath[i + 1], _expectedOutCalculatorData[i]
                )
                : IExpectedOutCalculator(_expectedOutCalculators[i]).getExpectedOut(
                    _runningExpectedOut, _swapPath[i], _swapPath[i + 1], _expectedOutCalculatorData[i]
                );
        }

        return _runningExpectedOut;
    }
}
