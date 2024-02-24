// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IPriceChecker} from "../interfaces/IPriceChecker.sol";

import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import {SafeMath} from "@openzeppelin/contracts/math/SafeMath.sol";
import {GPv2Order} from "@cow-protocol/contracts/libraries/GPv2Order.sol";

/// @title Milkman
/// @author @charlesndalton
/// @notice A layer on top of the CoW Protocol that allows smart contracts (DAOs, Gnosis Safes, protocols, etc.) to submit swaps. Swaps are MEV-protected. Use with atypical tokens (e.g., rebasing tokens) not recommended.
/// @dev For each requested swap, Milkman creates a clone of itself, and moves `amountIn` of `fromToken` into the clone. The clone pre-approves the amount to the CoW settlement contract. The clone also stores a hash of the swap's variables, something like hash({amountIn: 1000, fromToken: USDC, toToken: DAI, etc.}). Then, an off-chain server creates a CoW order on behalf of the clone. Before this CoW order can be 'settled' (before amountIn can be pulled out of the clone), the clone runs checks on the order. These checks include calling a user-provided `priceChecker`, which could for example check SushiSwap to see if what they could get out of SushiSwap was at least 90% of the order's `minOut`.
contract Milkman {
    using SafeERC20 for IERC20;
    using GPv2Order for GPv2Order.Data;
    using SafeMath for uint256;

    event SwapRequested(
        address orderContract,
        address orderCreator,
        uint256 amountIn,
        address fromToken,
        address toToken,
        address to,
        address priceChecker,
        bytes priceCheckerData
    );

    /// @dev The contract Milkman needs to give allowance.
    address internal constant VAULT_RELAYER = 0xC92E8bdf79f0507f65a392b0ab4667716BFE0110;
    /// @dev The settlement contract's EIP-712 domain separator. Milkman uses this to verify that a provided UID matches provided order parameters.
    bytes32 public constant DOMAIN_SEPARATOR = 0xc078f884a2676e1345748b1feace7b0abee5d00ecadb6e574dcdd109a63e8943;
    bytes4 internal constant MAGIC_VALUE = 0x1626ba7e;
    bytes4 internal constant NON_MAGIC_VALUE = 0xffffffff;
    bytes32 internal constant ROOT_MILKMAN_SWAP_HASH =
        0xca11ab1efacade00000000000000000000000000000000000000000000000000;

    /// @dev the Milkman deployed by an EOA, in contrast to Milkman 'order contracts' deployed in invocations of requestSwapExactTokensForTokens
    address internal immutable ROOT_MILKMAN;

    /// @dev Hash of the order data, hashed like so:
    ///      kekkak256(abi.encode(orderCreator, receiver, fromToken, toToken, amountIn, priceChecker, priceCheckerData)).
    ///      In the root contract, it's set to `ROOT_MILKMAN_SWAP_HASH`.
    bytes32 public swapHash = ROOT_MILKMAN_SWAP_HASH;

    constructor() {
        ROOT_MILKMAN = address(this);
    }

    /// @notice Asynchronously swap an exact amount of tokenIn for a market-determined amount of tokenOut.
    /// @dev Swaps are usually completed in ~2 minutes.
    /// @param amountIn The number of tokens to sell.
    /// @param fromToken The token that the user wishes to sell.
    /// @param toToken The token that the user wishes to receive.
    /// @param to Who should receive the tokens.
    /// @param priceChecker A contract that verifies an order (mainly its minOut and fee) before Milkman signs it.
    /// @param priceCheckerData Data that gets passed to the price checker.
    function requestSwapExactTokensForTokens(
        uint256 amountIn,
        IERC20 fromToken,
        IERC20 toToken,
        address to,
        address priceChecker,
        bytes calldata priceCheckerData
    )
        external
    {
        require(address(this) == ROOT_MILKMAN, "!root_milkman"); // can't call `requestSwapExactTokensForTokens` from order contracts
        require(priceChecker != address(0), "!price_checker"); // need to supply a valid price checker

        address orderContract = createOrderContract();

        fromToken.safeTransferFrom(msg.sender, orderContract, amountIn);

        bytes32 _swapHash =
            keccak256(abi.encode(msg.sender, to, fromToken, toToken, amountIn, priceChecker, priceCheckerData));

        Milkman(orderContract).initialize(fromToken, _swapHash);

        emit SwapRequested(
            orderContract, msg.sender, amountIn, address(fromToken), address(toToken), to, priceChecker, priceCheckerData
            );
    }

    function initialize(IERC20 fromToken, bytes32 _swapHash) external {
        require(swapHash == bytes32(0) && _swapHash != bytes32(0), "!reinit"); // also prevents root contract from being initialized
        swapHash = _swapHash;

        fromToken.safeApprove(VAULT_RELAYER, type(uint256).max);
    }

    /// @notice Cancel a requested swap, sending the tokens back to the order creator.
    /// @dev `msg.sender` must be the original order creator. The other parameters are required to verify that this is the case (kind of like a merkle proof).
    function cancelSwap(
        uint256 amountIn,
        IERC20 fromToken,
        IERC20 toToken,
        address to,
        address priceChecker,
        bytes calldata priceCheckerData
    )
        external
    {
        bytes32 _storedSwapHash = swapHash;

        require(_storedSwapHash != ROOT_MILKMAN_SWAP_HASH, "!cancel_from_root");

        bytes32 _calculatedSwapHash =
            keccak256(abi.encode(msg.sender, to, fromToken, toToken, amountIn, priceChecker, priceCheckerData));

        require(_storedSwapHash == _calculatedSwapHash, "!valid_creator_proof");

        fromToken.safeTransfer(msg.sender, amountIn);
    }

    /// @param orderDigest The EIP-712 signing digest derived from the order
    /// @param encodedOrder Bytes-encoded order information, originally created by an off-chain bot. Created by concatening the order data (in the form of GPv2Order.Data), the price checker address, and price checker data.
    function isValidSignature(bytes32 orderDigest, bytes calldata encodedOrder) external view returns (bytes4) {
        bytes32 _storedSwapHash = swapHash;

        require(_storedSwapHash != ROOT_MILKMAN_SWAP_HASH, "!is_valid_sig_from_root");

        (GPv2Order.Data memory _order, address _orderCreator, address _priceChecker, bytes memory _priceCheckerData) =
            decodeOrder(encodedOrder);

        require(_order.hash(DOMAIN_SEPARATOR) == orderDigest, "!match");

        require(_order.kind == GPv2Order.KIND_SELL, "!kind_sell");

        require(_order.validTo >= block.timestamp + 5 minutes, "expires_too_soon");

        require(!_order.partiallyFillable, "!fill_or_kill");

        require(_order.sellTokenBalance == GPv2Order.BALANCE_ERC20, "!sell_erc20");

        require(_order.buyTokenBalance == GPv2Order.BALANCE_ERC20, "!buy_erc20");

        require(
            IPriceChecker(_priceChecker).checkPrice(
                _order.sellAmount.add(_order.feeAmount),
                address(_order.sellToken),
                address(_order.buyToken),
                _order.feeAmount,
                _order.buyAmount,
                _priceCheckerData
            ),
            "invalid_min_out"
        );

        bytes32 _calculatedSwapHash = keccak256(
            abi.encode(
                _orderCreator,
                _order.receiver,
                _order.sellToken,
                _order.buyToken,
                _order.sellAmount.add(_order.feeAmount),
                _priceChecker,
                _priceCheckerData
            )
        );

        if (_calculatedSwapHash == _storedSwapHash) {
            // should be true as long as the keeper isn't submitting bad orders
            return MAGIC_VALUE;
        } else {
            return NON_MAGIC_VALUE;
        }
    }

    function decodeOrder(bytes calldata _encodedOrder)
        internal
        pure
        returns (
            GPv2Order.Data memory _order,
            address _orderCreator,
            address _priceChecker,
            bytes memory _priceCheckerData
        )
    {
        (_order, _orderCreator, _priceChecker, _priceCheckerData) =
            abi.decode(_encodedOrder, (GPv2Order.Data, address, address, bytes));
    }

    function createOrderContract() internal returns (address _orderContract) {
        // Copied from https://github.com/optionality/clone-factory/blob/master/contracts/CloneFactory.sol

        bytes20 addressBytes = bytes20(address(this));
        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(clone_code, 0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000)
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(add(clone_code, 0x28), 0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000)
            _orderContract := create(0, clone_code, 0x37)
        }
    }
}
