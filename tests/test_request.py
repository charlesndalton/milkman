from eth_abi import encode_abi
from eth_utils import keccak


def test_request_swap(milkman, user, gno_whale, gno, dai, univ2_price_checker):
    amount = 100e18
    gno.transfer(user, amount, {"from": gno_whale})

    gno.approve(milkman, amount, {"from": user})

    tx = milkman.requestSwapExactTokensForTokens(
        int(amount), gno, dai, user, univ2_price_checker, {"from": user}
    )

    assert tx.events.count("SwapRequested") == 1

    assert milkman.nonce() == 1

    # user, receiver, from_token, to_token, amount_in, price_checker, nonce
    encoded_market_order = encode_abi(
        ["address", "address", "address", "address", "uint256", "address", "uint256"],
        [
            user.address,
            user.address,
            gno.address,
            dai.address,
            int(amount),
            univ2_price_checker.address,
            0,
        ],
    )
    swap_id = keccak(encoded_market_order)
    swap_data = milkman.swaps(swap_id)

    swap_requested_data = encode_abi(
        ["uint256"],
        [int(1)]
    )
    
    print(f"Swap Data: {swap_data}")
    print(f"Swap Requested Data: {swap_requested_data}")
    assert swap_data.hex() == swap_requested_data.hex()
    
