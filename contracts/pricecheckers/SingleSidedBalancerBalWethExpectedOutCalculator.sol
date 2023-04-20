// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "@openzeppelin/contracts/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@balancer/lib/math/FixedPoint.sol";

import {IExpectedOutCalculator} from "./IExpectedOutCalculator.sol";

interface IPriceFeed {
    function latestAnswer() external view returns (int256);

    function decimals() external view returns (uint8);
}

interface IWeightedPool {
    function getInvariant() external view returns (uint256);

    function getVault() external view returns (address);

    function totalSupply() external view returns (uint256);
}

interface IVault {
    struct UserBalanceOp {
        UserBalanceOpKind kind;
        address asset;
        uint256 amount;
        address sender;
        address payable recipient;
    }

    function manageUserBalance(UserBalanceOp[] memory ops) external payable;

    enum UserBalanceOpKind {
        DEPOSIT_INTERNAL,
        WITHDRAW_INTERNAL,
        TRANSFER_INTERNAL,
        TRANSFER_EXTERNAL
    }
}

library VaultReentrancyLib {
    function ensureNotInVaultContext(IVault vault) internal {
        IVault.UserBalanceOp[] memory noop = new IVault.UserBalanceOp[](0);
        vault.manageUserBalance(noop);
    }
}

contract SingleSidedBalancerBalWethExpectedOutCalculator is
    IExpectedOutCalculator
{
    using SafeMath for uint256;
    using FixedPoint for uint256;
    using VaultReentrancyLib for IVault;

    address internal constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address internal constant BAL = 0xba100000625a3754423978a60c9317c58a424e3D;
    address internal constant BAL_WETH_POOL =
        0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56;
    address internal constant BALANCER_VAULT =
        0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    IPriceFeed internal constant BAL_ETH_FEED =
        IPriceFeed(0xC1438AA3823A6Ba0C159CfA8D98dF5A994bA120b);

    uint256 internal constant ZERO_POINT_EIGHT = 8e17;
    uint256 internal constant ZERO_POINT_TWO = 2e17;
    uint256 internal constant TEN = 1e19;

    function getExpectedOut(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        bytes calldata
    ) external view override returns (uint256) {
        // require(_toToken == BAL_WETH_POOL);
        // require(_fromToken == WETH || _fromToken == BAL);

        IWeightedPool pool = IWeightedPool(BAL_WETH_POOL);
        IVault vault = IVault(BALANCER_VAULT);

        // need to troubleshoot this since this is a read-only function
        // vault.ensureNotInVaultContext();

        uint256 kOverS = pool.getInvariant().mul(1e18).div(pool.totalSupply());

        uint256 ethPriceOfBal = uint256(BAL_ETH_FEED.latestAnswer());

        uint256 balFactor = ethPriceOfBal.mul(1e18).div(ZERO_POINT_EIGHT).powUp(
            ZERO_POINT_EIGHT
        );
        uint256 ethFactor = FixedPoint.ONE.mul(1e18).div(ZERO_POINT_TWO).powUp(
            ZERO_POINT_TWO
        );

        // this doesn't return the actual output, just what a BPT is worth in 1 ETH
        return kOverS.mul(balFactor).div(1e18).mul(ethFactor).div(1e18);
    }
}
