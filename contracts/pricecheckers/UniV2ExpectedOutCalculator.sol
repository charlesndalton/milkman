// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {IExpectedOutCalculator} from "./IExpectedOutCalculator.sol";
import "../../interfaces/IUniV2.sol";

contract UniV2ExpectedOutCalculator is IExpectedOutCalculator {
    using SafeMath for uint256;

    address internal constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    string public NAME;
    address public immutable UNIV2_ROUTER;

    constructor(string memory _name, address _univ2Router) {
        NAME = _name;
        UNIV2_ROUTER = _univ2Router;
    }

    function getExpectedOut(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        bytes calldata
    ) external view override returns (uint256) {
        uint256[] memory amounts;

        if (_fromToken == WETH || _toToken == WETH) {
            address[] memory path = new address[](2);

            path[0] = _fromToken;
            path[1] = _toToken;

            amounts = IUniV2(UNIV2_ROUTER).getAmountsOut(_amountIn, path);
        } else {
            address[] memory path = new address[](3);
            path[0] = _fromToken; // token to swap
            path[1] = WETH; // weth
            path[2] = _toToken;

            amounts = IUniV2(UNIV2_ROUTER).getAmountsOut(_amountIn, path);
        }

        return amounts[amounts.length - 1];
    }
}
