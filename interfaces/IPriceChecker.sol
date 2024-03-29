// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.7.6;
pragma abicoder v2;

interface IPriceChecker {
    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256 _feeAmount,
        uint256 _minOut,
        bytes calldata _data
    ) external view returns (bool);
}
