// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import {GPv2Order} from "@cow-protocol/contracts/libraries/GPv2Order.sol";

contract HashHelper {
    using GPv2Order for GPv2Order.Data;
    using GPv2Order for bytes;

    function hash(GPv2Order.Data memory order, bytes32 domainSeparator)
        external
        pure
        returns (bytes32 orderDigest)
    {
        return order.hash(domainSeparator);
    }
}
