// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";

import {IPriceChecker} from "../../interfaces/IPriceChecker.sol";
import {IExpectedOutCalculator} from "./IExpectedOutCalculator.sol";

/// Specify a maximum allowed fee, denominated in `fromToken`.
/// This decorates an existing price checker to allow for composability.
contract FixedMaxFeePriceCheckerDecorator is IPriceChecker {
    using SafeMath for uint256;

    string public NAME;
    IPriceChecker public immutable PRICE_CHECKER;

    constructor(string memory _name, address _expectedOutCalculator) {
        NAME = _name;
        PRICE_CHECKER = IPriceChecker(_expectedOutCalculator);
    }

    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256 _feeAmount,
        uint256 _minOut,
        bytes calldata _data
    )
        external
        view
        override
        returns (bool)
    {
        (uint256 _allowedFeeAmount, bytes memory _data) = abi.decode(_data, (uint256, bytes));

        if (_feeAmount > _allowedFeeAmount) {
            return false;
        }

        return PRICE_CHECKER.checkPrice(_amountIn, _fromToken, _toToken, _feeAmount, _minOut, _data);
    }
}
