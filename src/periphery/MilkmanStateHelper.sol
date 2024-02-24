// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import {IGPv2Settlement} from "../../interfaces/IGPv2Settlement.sol";

interface IMilkman {
    function swaps(bytes32 _swapID) external view returns (bytes memory);
}

/// @title Milkman State Helper
/// @dev Helper contract that can be used by off-chain bots to fetch the state of a Milkman swap.
contract MilkmanStateHelper {
    enum SwapState {
        NULL,
        REQUESTED,
        PAIRED,
        PAIRED_AND_UNPAIRABLE,
        PAIRED_AND_EXECUTED
    }

    IMilkman public constant milkman = IMilkman(0x3E40B8c9FcBf02a26Ff1c5d88f525AEd00755575);

    IGPv2Settlement internal constant settlement = IGPv2Settlement(0x9008D19f58AAbD9eD0D60971565AA8510560ab41);

    function getState(bytes32 _swapID) external view returns (SwapState) {
        bytes memory _swapData = milkman.swaps(_swapID);

        if (_swapData.length == 0) {
            return SwapState.NULL;
        } else if (_swapData.length == 32 && _swapData[31] == bytes1(uint8(1))) {
            return SwapState.REQUESTED;
        }

        (uint256 _blockNumberWhenPaired, bytes memory _orderUid) = abi.decode(_swapData, (uint256, bytes));

        if (settlement.filledAmount(_orderUid) != 0) {
            return SwapState.PAIRED_AND_EXECUTED;
        } else if (block.number >= _blockNumberWhenPaired + 50) {
            return SwapState.PAIRED_AND_UNPAIRABLE;
        } else {
            return SwapState.PAIRED;
        }
    }
}
