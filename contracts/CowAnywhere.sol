// SPDX-License-Identifier: AGPL-3.0 
pragma solidity ^0.7.6;
pragma abicoder v2;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import {GPv2Order} from "@cow-protocol/contracts/libraries/GPv2Order.sol";
import {GPv2Settlement} from "@cow-protocol/contracts/GPv2Settlement.sol";

import {IPriceChecker} from "../interfaces/IPriceChecker.sol";

enum OrderType { BUY, SELL }

contract CowAnywhere {
    using SafeERC20 for IERC20;
    using GPv2Order for GPv2Order.Data;
    using GPv2Order for bytes;

    event SwapRequested(address user, address receiver, IERC20 fromToken, IERC20 toToken, uint256 amountIn, address priceChecker);

    mapping(address => uint128) public nonces;
    mapping(bytes32 => bool) public validSwapRequests;

    // Who we give allowance
    address internal constant gnosisVaultRelayer = 0xC92E8bdf79f0507f65a392b0ab4667716BFE0110; 
    // Where we pre-sign
    GPv2Settlement internal constant settlement = GPv2Settlement(0x9008D19f58AAbD9eD0D60971565AA8510560ab41);
    // Settlement's domain separator, used to hash order IDs
    bytes32 internal constant domainSeparator = 0xc078f884a2676e1345748b1feace7b0abee5d00ecadb6e574dcdd109a63e8943;
    
    // Request to asynchronously swap exact tokens for market value of other tokens through cowswap
    function requestSwapExactTokensForTokens(
        uint256 _amountIn,
        IERC20 _fromToken, 
        IERC20 _toToken,
        address _to,
        address _priceChecker // used to verify that any UIDs passed in are setting reasonable minOuts. Set to 0 if you don't want.
    ) external {
        _fromToken.transferFrom(msg.sender, address(this), _amountIn);

        uint128 _currentUserNonce = nonces[msg.sender];

        validSwapRequests[keccak256(abi.encode(msg.sender,
                                               _to,
                                               _fromToken, 
                                               _toToken, 
                                               _amountIn, 
                                               _priceChecker,
                                               _currentUserNonce))] = true;

        emit SwapRequested(msg.sender, _to, _fromToken, _toToken, _amountIn, _priceChecker);
    }

    // Called by a bot who has generated a UID via the API
    function signOrderUid(
        bytes calldata _orderUid,
        GPv2Order.Data calldata _order,
        address _user,
        address _priceChecker
    ) external {
        bytes32 _orderDigestFromOrderDetails = _order.hash(domainSeparator);
        (bytes32 _orderDigestFromUid, address _owner, ) = _orderUid.extractOrderUidParams();

        require(_orderDigestFromOrderDetails == _orderDigestFromUid, "!digest_match");

        uint128 _currentUserNonce = nonces[_user];
        require(validSwapRequests[keccak256(abi.encode(_user,
                                               _order.receiver,
                                               _order.sellToken, 
                                               _order.buyToken, 
                                               _order.sellAmount + _order.feeAmount, // do we need to worry about fee manipulation?
                                               _priceChecker,
                                               _currentUserNonce))], "!no_swap_request");

        if (_priceChecker != address(0)) {
            require(IPriceChecker(_priceChecker).checkPrice(_order.sellAmount, address(_order.sellToken), address(_order.buyToken), _order.buyAmount), "invalid_min_out");
        }

        nonces[_user] += 1;

        settlement.setPreSignature(_orderUid, true);
    }
}
