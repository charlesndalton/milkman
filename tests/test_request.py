from brownie import ZERO_ADDRESS, reverts
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

    check_swap_requested(
        milkman, user, user, gno, dai, amount, univ2_price_checker.address, 0
    )


def test_request_swap_twice(milkman, user, gno_whale, gno, dai):
    amount = 100e18
    gno.transfer(user, amount, {"from": gno_whale})

    gno.approve(milkman, amount, {"from": user})

    tx = milkman.requestSwapExactTokensForTokens(
        int(amount / 2), gno, dai, user, ZERO_ADDRESS, {"from": user}
    )

    assert tx.events.count("SwapRequested") == 1

    tx = milkman.requestSwapExactTokensForTokens(
        int(amount / 2), gno, dai, user, ZERO_ADDRESS, {"from": user}
    )

    assert tx.events.count("SwapRequested") == 1

    assert milkman.nonce() == 2

    check_swap_requested(milkman, user, user, gno, dai, amount / 2, ZERO_ADDRESS, 0)
    check_swap_requested(milkman, user, user, gno, dai, amount / 2, ZERO_ADDRESS, 1)


def test_request_without_sufficient_tokens(
    milkman, user, gno, dai, univ2_price_checker
):
    amount = 100e18

    with reverts():
        milkman.requestSwapExactTokensForTokens(
            int(amount), gno, dai, user, univ2_price_checker, {"from": user}
        )

    gno.approve(milkman, amount, {"from": user})

    with reverts():
        milkman.requestSwapExactTokensForTokens(
            int(amount), gno, dai, user, univ2_price_checker, {"from": user}
        )


def check_swap_requested(
    milkman, user, receiver, from_token, to_token, amount, price_checker_address, nonce
):
    # user, receiver, from_token, to_token, amount_in, price_checker, nonce
    encoded_market_order = encode_abi(
        ["address", "address", "address", "address", "uint256", "address", "uint256"],
        [
            user.address,
            receiver.address,
            from_token.address,
            to_token.address,
            int(amount),
            price_checker_address,
            nonce,
        ],
    )
    swap_id = keccak(encoded_market_order)
    swap_data = milkman.swaps(swap_id)

    swap_requested_data = encode_abi(["uint256"], [int(1)])

    print(f"Swap Data: {swap_data}")
    print(f"Swap Requested Data: {swap_requested_data}")
    assert swap_data.hex() == swap_requested_data.hex()
