// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

interface IUniV2 {

    function getAmountsOut(uint256 amountIn, address[] memory path)
        external
        view
        returns (uint256[] memory amounts);

}