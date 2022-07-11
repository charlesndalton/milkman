from eth_abi import encode_abi
from eth_utils import keccak

def test_submit_sell(cow_anywhere, user, gno, dai):
    tx = cow_anywhere.submitMarketSell(user, gno, dai, int(100e18), {"from": user})

    assert tx.events.count('OrderSubmitted') == 1

    # user, receiver, from_token, to_token, order_amount, order_type, nonce
    encoded_market_order = encode_abi(['address', 'address', 'address', 'address', 'uint256', 'uint256', 'uint256'], [user.address, user.address, gno.address, dai.address, int(100e18), 1, 0])
    assert cow_anywhere.approvedOrders(keccak(encoded_market_order))


def test_submit_buy(cow_anywhere, user, deployer, usdc, weth):
    # sending the WETH to the deployer
    tx = cow_anywhere.submitMarketBuy(deployer, usdc, weth, int(5e18), {"from": user})

    assert tx.events.count('OrderSubmitted') == 1

    # user, receiver, from_token, to_token, order_amount, order_type, nonce
    encoded_market_order = encode_abi(['address', 'address', 'address', 'address', 'uint256', 'uint256', 'uint256'], [user.address, deployer.address, usdc.address, weth.address, int(5e18), 0, 0])
    assert cow_anywhere.approvedOrders(keccak(encoded_market_order))