// SPDX-License-Identifier: AGPL-3.0 
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "../interfaces/IPriceChecker.sol";
import "../interfaces/IUniV2.sol";

// Super basic & dumb price checker. Checks that minOut is at least 90% of what you'd get by selling to SushiSwap
contract UniV2PriceChecker is IPriceChecker {
    using SafeMath for uint256;

    address internal constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address internal constant UNIV2_ROUTER = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F; // Sushi

    function checkPrice(
        uint256 _amountIn,
        address _fromToken, 
        address _toToken,
        uint256 _minOut
    ) external view override returns (bool) {
        address[] memory path = new address[](3);
        path[0] = _fromToken; // token to swap
        path[1] = WETH; // weth
        path[2] = _toToken;

        uint256[] memory amounts = IUniV2(UNIV2_ROUTER).getAmountsOut(_amountIn, path);

        uint256 _toTokenFromUni = amounts[amounts.length - 1];

        if (_minOut > _toTokenFromUni.mul(9).div(10)) {
            return true;
        } else {
            return false;
        }
    }

}