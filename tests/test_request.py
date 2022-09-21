from brownie import ZERO_ADDRESS, reverts, Contract
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

    order_contract = Contract.from_abi("Milkman", tx.events["SwapRequested"]["orderContract"], milkman.abi)

    utils.check_swap_requested(
        order_contract,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
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

    amount_for_each = int(amount * 0.49)

    tx = milkman.requestSwapExactTokensForTokens(
        amount_for_each,
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    assert tx.events.count("SwapRequested") == 1

    order_contract_1 = Contract.from_abi("Milkman", tx.events["SwapRequested"]["orderContract"], milkman.abi)

    tx = milkman.requestSwapExactTokensForTokens(
        amount_for_each,
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    assert tx.events.count("SwapRequested") == 1

    order_contract_2 = Contract.from_abi("Milkman", tx.events["SwapRequested"]["orderContract"], milkman.abi)


    utils.check_swap_requested(
        order_contract_1,
        user,
        token_to_sell,
        token_to_buy,
        amount_for_each,
        price_checker,
        price_checker_data,
    )
    utils.check_swap_requested(
        order_contract_2,
        user,
        token_to_sell,
        token_to_buy,
        amount_for_each,
        price_checker,
        price_checker_data,
    )


# brownie not allowing this test for now

# def test_revert_without_token_move(
#     milkman,
#     user,
#     token_to_sell,
#     token_to_buy,
#     amount,
#     price_checker,
#     price_checker_data,
# ):
#     with reverts():
#         milkman.requestSwapExactTokensForTokens(
#             int(amount / 2),
#             token_to_sell,
#             token_to_buy,
#             user,
#             price_checker,
#             price_checker_data,
#             {"from": user},
#         )
