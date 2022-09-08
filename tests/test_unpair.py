from eth_abi import encode_abi
from eth_utils import keccak
import requests
import brownie
import utils


def test_unpair(
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


def test_unpair_not_enough_time_elapsed(
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

    chain.mine(25)

    with brownie.reverts("!unpairable"):
        milkman.unpairSwap(swap_id)

    chain.mine(40)

    utils.unpair_swap(gnosis_settlement, milkman, swap_id, order_uid)


def test_unpair_and_pair_again(
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
    chain.sleep(5 * 60)

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


def test_cannot_unpair_swap_that_hasnt_been_paired(
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

    chain.mine(51)
    chain.sleep(5 * 60)

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

    with brownie.reverts(""):
        milkman.unpairSwap(swap_id)

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

    utils.unpair_swap(gnosis_settlement, milkman, swap_id, order_uid)


def test_cannot_unpair_swap_that_hasnt_been_created(
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

    with brownie.reverts(""):
        milkman.unpairSwap(swap_id)
