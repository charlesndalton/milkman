// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "../../interfaces/IPriceChecker.sol";
import "./PriceCheckerLib.sol";

interface IUniswapV3StaticQuoter {
    /// @notice Returns the amount out received for a given exact input swap without executing the swap
    /// @param path The path of the swap, i.e. each token pair and the pool fee
    /// @param amountIn The amount of the first token to swap
    /// @return amountOut The amount of the last token that would be received
    function quoteExactInput(bytes memory path, uint256 amountIn)
        external
        view
        returns (uint256 amountOut);
}

contract UniV3PriceChecker is IPriceChecker {
    using SafeMath for uint256;

    IUniswapV3StaticQuoter internal constant QUOTER =
        IUniswapV3StaticQuoter(0x7637Aaeb5BD58269B782726680d83f72C651aE74);

    /**
     * @param _data Encoded [maxSlippage, swapPath, poolFees].
     *
     * maxSlippage (optional<uint>): Number of basis points of acceptable slippage (e.g., 500 for 5% slippage). If 0 is passed in, the default is 300 (3%).
     * swapPath (address[]): List of ERC20s to swap through.
     * poolFees (uint24[]): Pool fee for the pool to swap through, denominated in bips.
     *
     * Some examples:
     * AAVE -> DAI w/ default slippage: [0, [address(AAVE), address(WETH), address(DAI)], [30, 5]]
     * USDT -> USDC w/ 0.5% slippage: [50, [address(USDT), address(USDC)]]
     */
    function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256,
        uint256 _minOut,
        bytes calldata _data
    ) external view override returns (bool) {
        (
            uint256 _maxSlippage,
            address[] memory _swapPath,
            uint24[] memory _poolFees
        ) = abi.decode(_data, (uint256, address[], uint24[]));

        _maxSlippage = PriceCheckerLib.getMaxSlippage(_maxSlippage, 300);

        uint256 _expectedOut = _getExpectedOut(_amountIn, _swapPath, _poolFees);

        return
            PriceCheckerLib.isMinOutAcceptable(
                _minOut,
                _expectedOut,
                _maxSlippage
            );
    }

    function _getExpectedOut(
        uint256 _amountIn,
        address[] memory _swapPath,
        uint24[] memory _poolFees
    ) internal view returns (uint256) {
        require(_swapPath.length >= 2); // dev: must have at least two assets in swap path
        require(_poolFees.length.add(1) == _swapPath.length); // dev: must be one more asset in swap path than pool fee

        // path is packed bytes with the form [asset0, poolFee0, asset1, poolFee1, asset2]
        bytes memory _path = abi.encodePacked(_swapPath[0]);

        for (uint256 _i = 0; _i < _poolFees.length; _i++) {
            // they ingest fees in 1 100ths of a bip, so we multiply by 100
            _path = abi.encodePacked(
                _path,
                uint24(uint256(_poolFees[_i]).mul(100)),
                _swapPath[_i.add(1)]
            );
        }

        return QUOTER.quoteExactInput(_path, _amountIn);
    }
}
