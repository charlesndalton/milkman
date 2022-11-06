from eth_abi import encode_abi
from eth_utils import keccak
import requests
from brownie import ZERO_ADDRESS, reverts, Contract
import utils
from brownie.convert import to_bytes
import brownie


def test_complete_swap(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
    chain,
    hash_helper,
    chainlink_price_checker,
    sushiswap_price_checker,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
    )

    # we can't create orders via API, so we need to fake it
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
        order_digest, signature_encoded_order
    )

    assert to_bytes(is_valid_sig) == to_bytes(utils.EIP_1271_MAGIC_VALUE)


# the keeper passes in order data that doesn't match the canonical order (what was used to generate the UID)
def test_mismatched_order(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to + 10,  # keeper tries manipulating valid_to
        fee_amount,
        price_checker,
        price_checker_data,
    )

    # we can't create orders via API, so we need to fake it
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

    with brownie.reverts("!match"):
        order_contract.isValidSignature(order_digest, signature_encoded_order)


# the keeper generates a buy order, which should be rejected
def test_buy_order(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
        buy_or_sell=utils.KIND_BUY,
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
        utils.KIND_BUY,
        False,  # fill or kill
        utils.ERC20_BALANCE,
        utils.ERC20_BALANCE,
    )

    order_digest = hash_helper.hash(
        gpv2_order, to_bytes(utils.DOMAIN_SEPARATOR, "bytes32")
    )

    with brownie.reverts("!kind_sell"):
        order_contract.isValidSignature(order_digest, signature_encoded_order)


def test_expires_too_soon_order(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 2  # only 2 minutes instead of 5

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
    )

    # we can't create orders via API, so we need to fake it
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

    with brownie.reverts("expires_too_soon"):
        order_contract.isValidSignature(order_digest, signature_encoded_order)


def test_non_fill_or_kill_order(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
        partially_fillable=True,
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
        True,  # partially fillable
        utils.ERC20_BALANCE,
        utils.ERC20_BALANCE,
    )

    order_digest = hash_helper.hash(
        gpv2_order, to_bytes(utils.DOMAIN_SEPARATOR, "bytes32")
    )

    with brownie.reverts("!fill_or_kill"):
        order_contract.isValidSignature(order_digest, signature_encoded_order)


def test_non_erc20_sell_order(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
        sell_token_balance=utils.BALANCE_EXTERNAL,
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
        False,  # fill_or_kill
        utils.BALANCE_EXTERNAL,
        utils.ERC20_BALANCE,
    )

    order_digest = hash_helper.hash(
        gpv2_order, to_bytes(utils.DOMAIN_SEPARATOR, "bytes32")
    )

    with brownie.reverts("!sell_erc20"):
        order_contract.isValidSignature(order_digest, signature_encoded_order)


def test_non_erc20_buy_order(
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
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
        user,
        token_to_sell,
        token_to_buy,
        amount,
        price_checker,
        price_checker_data,
    )

    (fee_amount, buy_amount_after_fee) = utils.get_quote(
        token_to_sell, token_to_buy, amount
    )

    valid_to = chain.time() + 60 * 60 * 24

    signature_encoded_order = utils.encode_order_for_is_valid_signature(
        token_to_sell,
        token_to_buy,
        user,
        user,
        amount - fee_amount,
        buy_amount_after_fee,
        valid_to,
        fee_amount,
        price_checker,
        price_checker_data,
        buy_token_balance=utils.BALANCE_INTERNAL,
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
        False,  # fill_or_kill
        utils.ERC20_BALANCE,
        utils.BALANCE_INTERNAL,
    )

    order_digest = hash_helper.hash(
        gpv2_order, to_bytes(utils.DOMAIN_SEPARATOR, "bytes32")
    )

    with brownie.reverts("!buy_erc20"):
        order_contract.isValidSignature(order_digest, signature_encoded_order)
