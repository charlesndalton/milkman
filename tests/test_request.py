from brownie import ZERO_ADDRESS, reverts
import utils


def test_request_swap(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
):
    token_to_sell.approve(milkman, amount, {"from": user})

    tx = milkman.requestSwapExactTokensForTokens(
        int(amount),
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    assert tx.events.count("SwapRequested") == 1

    assert milkman.nonce() == 1

    utils.check_swap_requested(
        milkman,
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker.address,
        price_checker_data,
        0,
    )


def test_request_swap_twice(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
):

    token_to_sell.approve(milkman, amount, {"from": user})

    tx = milkman.requestSwapExactTokensForTokens(
        int(amount / 2),
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    assert tx.events.count("SwapRequested") == 1

    tx = milkman.requestSwapExactTokensForTokens(
        int(amount / 2),
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    assert tx.events.count("SwapRequested") == 1

    assert milkman.nonce() == 2

    utils.check_swap_requested(
        milkman,
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount / 2,
        price_checker.address,
        price_checker_data,
        0,
    )
    utils.check_swap_requested(
        milkman,
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount / 2,
        price_checker.address,
        price_checker_data,
        1,
    )


def test_revert_without_token_move(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
):
    with reverts():
        milkman.requestSwapExactTokensForTokens(
            int(amount / 2),
            token_to_sell,
            token_to_buy,
            user,
            price_checker,
            price_checker_data,
            {"from": user},
        )
