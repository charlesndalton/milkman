from eth_abi import encode_abi
from eth_utils import keccak
import requests
import brownie
import utils


def test_cancel(
    chain,
    milkman,
    user,
    gnosis_settlement,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
):
    token_to_sell.approve(milkman, amount, {"from": user})

    milkman.requestSwapExactTokensForTokens(
        amount,
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    assert token_to_sell.balanceOf(user) == 0
    # should be 0 nonce
    tx = milkman.cancelSwapRequest(
        amount, token_to_sell, token_to_buy, user, price_checker, price_checker_data, 0, {"from": user}
    )

    
    assert tx.events.count("SwapCancelled") == 1
    assert token_to_sell.balanceOf(user) == amount


def test_pair_unpair_then_cancel(
    chain,
    milkman,
    user,
    gnosis_settlement,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
):
    token_to_sell.approve(milkman, amount, {"from": user})

    milkman.requestSwapExactTokensForTokens(
        amount,
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    (order_uid, _) = utils.pair_swap(
        0,
        chain,
        gnosis_settlement,
        milkman,
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
        100,
    )

    chain.mine(51)

    encoded_market_order = utils.encode_market_order(
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
        0,
    )
    swap_id = keccak(encoded_market_order)

    utils.unpair_swap(gnosis_settlement, milkman, swap_id, order_uid)

    assert token_to_sell.balanceOf(user) == 0
    tx = milkman.cancelSwapRequest(
        amount, token_to_sell, token_to_buy, user, price_checker, price_checker_data, 0, {"from": user}
    )

    
    assert tx.events.count("SwapCancelled") == 1
    assert token_to_sell.balanceOf(user) == amount


# test that we can't cancel paired trades
def test_cant_cancel_paired_swap(
    chain,
    milkman,
    user,
    gnosis_settlement,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
):
    token_to_sell.approve(milkman, amount, {"from": user})

    milkman.requestSwapExactTokensForTokens(
        amount,
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    utils.pair_swap(
        0,
        chain,
        gnosis_settlement,
        milkman,
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
        100,
    )

    with brownie.reverts("!swap_requested"):
        milkman.cancelSwapRequest(
            amount, token_to_sell, token_to_buy, user, price_checker, price_checker_data, 0, {"from": user}
        )

