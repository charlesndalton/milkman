from eth_abi import encode_abi
from eth_utils import keccak


def test_request_swap(cow_anywhere, user, gno_whale, gno, dai, univ2_price_checker):
    amount = 100e18
    gno.transfer(user, amount, {"from": gno_whale})

    gno.approve(cow_anywhere, amount, {"from": user})

    tx = cow_anywhere.requestSwapExactTokensForTokens(
        int(amount), gno, dai, user, univ2_price_checker, {"from": user}
    )

    assert tx.events.count("SwapRequested") == 1

    assert cow_anywhere.nonces(user) == 1

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
    assert cow_anywhere.validSwapRequests(keccak(encoded_market_order))
