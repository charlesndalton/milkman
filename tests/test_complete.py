from eth_abi import encode_abi
from eth_utils import keccak
import requests
from brownie import ZERO_ADDRESS, reverts, Contract
import utils
from brownie.convert import to_bytes


def test_complete_swap(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
    gnosis_settlement,
    accounts,
    chain,
    hash_helper,
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

    order_contract = Contract.from_abi(
        "Milkman", tx.events["SwapRequested"]["orderContract"], milkman.abi
    )

    utils.check_swap_requested(
        order_contract,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    settlement_account = accounts.at(gnosis_settlement.address, force=True)

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    # assert False

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
    )

    gpv2_order = (
        token_to_sell.address,
        token_to_buy.address,
        user.address,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        utils.APP_DATA,
        fee_amount,
        utils.KIND_SELL,
        False,  # fill or kill
        utils.ERC20_BALANCE,
        utils.ERC20_BALANCE,
    )

    order_digest = hash_helper.hash(
        gpv2_order, to_bytes(utils.DOMAIN_SEPARATOR, "bytes32")
    )

    is_valid_sig = order_contract.isValidSignature(
        order_digest, signature_encoded_order, {"from": settlement_account}
    )

    # for now, we can't create orders via API, so we need to fake it

    assert False
