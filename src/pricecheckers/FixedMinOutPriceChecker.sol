// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import {IPriceChecker} from "../../interfaces/IPriceChecker.sol";

/// Specify a minimimum allowed out amount, denominated in `buyToken` you are willing to accept.
contract FixedMinOutPriceChecker is IPriceChecker {
    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256 _feeAmount,
        uint256 _out,
        bytes calldata _data
    )
        external
        view
        override
        returns (bool)
    {
        uint256 minOut = abi.decode(_data, (uint256));
        return minOut <= _out;
    }
}
