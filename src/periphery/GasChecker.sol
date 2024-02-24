// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

interface EIP1271 {
    function isValidSignature(bytes32, bytes calldata) external returns (bytes4);
}

/// Check that `isValidSignature` doesn't take up too much gas
contract GasChecker {
    function isValidSignatureCheck(address milkman, bytes32 orderDigest, bytes calldata encodedOrder)
        external
        returns (bytes4)
    {
        return EIP1271(milkman).isValidSignature(orderDigest, encodedOrder);
    }
}
