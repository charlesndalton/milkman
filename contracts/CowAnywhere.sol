// SPDX-License-Identifier: AGPL-3.0 
pragma solidity ^0.7.6;
pragma abicoder v2;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import {GPv2Order} from "@cow-protocol/contracts/libraries/GPv2Order.sol";
import {GPv2Settlement} from "@cow-protocol/contracts/GPv2Settlement.sol";

enum OrderType { SELL, BUY }

contract CowAnywhere {
    using SafeERC20 for IERC20;
    using GPv2Order for GPv2Order.Data;
    using GPv2Order for bytes;

    event OrderSubmitted(address user, IERC20 fromToken, IERC20 toToken, uint256 orderAmount, OrderType orderType);

    mapping(address => uint128) public nonces;
    mapping(bytes32 => bool) public approvedOrders;

    // Who we give allowance
    address internal constant gnosisVaultRelayer = 0xC92E8bdf79f0507f65a392b0ab4667716BFE0110; 
    // Where we pre-sign
    GPv2Settlement internal constant settlement = GPv2Settlement(0x9008D19f58AAbD9eD0D60971565AA8510560ab41);
    // Settlement's domain separator, used to hash order IDs
    bytes32 internal constant domainSeparator = 0xc078f884a2676e1345748b1feace7b0abee5d00ecadb6e574dcdd109a63e8943;

    function submitMarketSell(
        IERC20 _sellToken, 
        IERC20 _buyToken,
        uint256 _sellAmount
    ) external {
        _submitOrder(msg.sender, _sellToken, _buyToken, _sellAmount, OrderType.SELL);
    }

    function submitMarketBuy(
        IERC20 _sellToken,
        IERC20 _buyToken,
        uint256 _buyAmount
    ) external {
        _submitOrder(msg.sender, _sellToken, _buyToken, _buyAmount, OrderType.BUY);
    }

    // Called by a bot who has generated a UID via the API
    function signOrderUid(
        bytes calldata _orderUid,
        GPv2Order.Data calldata _order
    ) external {
        bytes32 _orderDigestFromOrderDetails = _order.hash(domainSeparator);
        (bytes32 _orderDigestFromUid, address _owner, ) = _orderUid.extractOrderUidParams();

        require(_orderDigestFromOrderDetails == _orderDigestFromUid, "!digest_match");
    }

    function _submitOrder(
        address _user,
        IERC20 _fromToken,
        IERC20 _toToken,
        uint256 _orderAmount,
        OrderType _orderType
    ) internal {
        
        uint128 _currentUserNonce = nonces[_user];

        approvedOrders[keccak256(abi.encode(_user, 
                                            _fromToken, 
                                            _toToken, 
                                            _orderAmount, 
                                            _orderType, 
                                            _currentUserNonce))] = true;

        emit OrderSubmitted(_user, _fromToken, _toToken, _orderAmount, _orderType);
    }
}
