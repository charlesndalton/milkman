// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.7.6;
pragma abicoder v2;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IGPv2Settlement {
    function setPreSignature(bytes calldata orderUid, bool signed) external;

    function filledAmount(bytes calldata orderUid)
        external
        view
        returns (uint256);
}
