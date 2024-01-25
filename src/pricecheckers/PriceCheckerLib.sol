// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";

library PriceCheckerLib {
    using SafeMath for uint256;

    uint256 internal constant MAX_BPS = 10_000;

    function getMaxSlippage(
        uint256 _inputMaxSlippage,
        uint256 _defaultMaxSlippage
    ) internal pure returns (uint256) {
        require(_inputMaxSlippage <= 10_000); // dev: max slippage too high

        if (_inputMaxSlippage == 0) {
            return _defaultMaxSlippage;
        } else {
            return _inputMaxSlippage;
        }
    }

    /// @dev performs a double-ended slippage check, ensuring that minOut is both greater than market value - max slippage and less than market value + max slippage.
    function isMinOutAcceptable(
        uint256 _minOut,
        uint256 _marketValueOfAmountIn,
        uint256 _maxSlippageInBips
    ) internal pure returns (bool) {
        return
            _minOut >
            _marketValueOfAmountIn.mul(MAX_BPS.sub(_maxSlippageInBips)).div(
                MAX_BPS
            ) &&
            _minOut <
            _marketValueOfAmountIn.mul(MAX_BPS.add(_maxSlippageInBips)).div(
                MAX_BPS
            );
    }
}
