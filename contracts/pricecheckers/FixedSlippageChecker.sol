// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";

import {IPriceChecker} from "../../interfaces/IPriceChecker.sol";
import {IExpectedOutCalculator} from "./IExpectedOutCalculator.sol";

// Very basic slippage checker that checks that minOut is at least 100 - x% of
// expected out, where x is set at deployment time. E.g., could check that minOut
// is at least 90% of expected out.
contract FixedSlippageChecker is IPriceChecker {
    using SafeMath for uint256;

    string public immutable NAME;
    uint256 public immutable ALLOWED_SLIPPAGE_IN_BPS;
    address public immutable EXPECTED_OUT_CALCULATOR;

    uint256 internal constant MAX_BPS = 10_000;

    constructor(
        string _name,
        uint256 _allowedSlippageInBps,
        address _expectedOutCalculator
    ) {
        require(_allowedSlippageInBps <= MAX_BPS);

        NAME = _name;
        ALLOWED_SLIPPAGE_IN_BPS = _allowedSlippageInBps;
        EXPECTED_OUT_CALCULATOR = _expectedOutCalculator;
    }

    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256,
        uint256 _minOut,
        bytes calldata _data
    ) external view override returns (bool) {
        uint256 _expectedOut = EXPECTED_OUT_CALCULATOR.getExpectedOut(
            _amountIn,
            _fromToken,
            _toToken,
            _data
        );

        return
            _minOut >
            _expectedOut.mul(MAX_BPS.sub(ALLOWED_SLIPPAGE_IN_BPS)).div(MAX_BPS);
    }
}
