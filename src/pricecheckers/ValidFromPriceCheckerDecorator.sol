// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import {IPriceChecker} from "../../interfaces/IPriceChecker.sol";

/// Specify a validFrom timestamp, which the current block has to have surpassed in order for the order to be valid.
/// This decorates an existing price checker to allow for composability.
contract ValidFromPriceCheckerDecorator is IPriceChecker {
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
        (uint256 _validFrom, address _priceChecker, bytes memory _data) = abi.decode(_data, (uint256, address, bytes));

        if (_validFrom > block.timestamp) {
            return false;
        }

        return IPriceChecker(_priceChecker).checkPrice(_amountIn, _fromToken, _toToken, _feeAmount, _minOut, _data);
    }
}
