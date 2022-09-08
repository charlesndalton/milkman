from eth_abi import encode_abi
from eth_utils import keccak
import requests
import brownie
import utils


def test_pair(
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
        50,
    )


def test_pair_multiple_swaps(
    chain,
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    gnosis_settlement,
    price_checker,
    price_checker_data,
):
    token_to_sell.approve(milkman, amount, {"from": user})

    amount_for_each = int(amount / 2)

    milkman.requestSwapExactTokensForTokens(
        amount_for_each,
        token_to_sell,
        token_to_buy,
        user,
        price_checker,
        price_checker_data,
        {"from": user},
    )

    milkman.requestSwapExactTokensForTokens(
        amount_for_each,
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
        amount_for_each,
        price_checker,
        price_checker_data,
        50,
    )

    utils.pair_swap(
        1,
        chain,
        gnosis_settlement,
        milkman,
        user,
        user,
        token_to_sell,
        token_to_buy,
        amount_for_each,
        price_checker,
        price_checker_data,
        50,
    )


def test_pair_bad_min_out(
    chain,
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    gnosis_settlement,
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

    (order_uid, order_payload) = utils.create_offchain_order(
        chain,
        milkman,
        user,
        token_to_sell,
        token_to_buy,
        amount,
        5000,  # 50% slippage allowed, which shouldn't pass
    )

    gpv2_order = utils.convert_offchain_order_into_gpv2_order(order_payload)

    with brownie.reverts("invalid_min_out"):
        milkman.pairSwap(gpv2_order, user, price_checker, price_checker_data, 0)

    # can still do it the correct way

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
        50,
    )


# milkman should only accept uids that are selling, not buying
def test_pair_buy_to_sell(
    chain,
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    gnosis_settlement,
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

    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
    get_params = {
        "sellToken": token_to_sell.address,
        "buyToken": token_to_buy.address,
        "sellAmountBeforeFee": int(amount),
    }
    r = requests.get(fee_and_quote, params=get_params)
    assert r.ok and r.status_code == 200

    buy_amount = int(r.json()["buyAmountAfterFee"])

    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/buy"
    get_params = {
        "sellToken": token_to_sell.address,
        "buyToken": token_to_buy.address,
        "buyAmountAfterFee": buy_amount,
    }
    r = requests.get(fee_and_quote, params=get_params)
    assert r.ok and r.status_code == 200

    # These two values are needed to create an order
    fee_amount = int(r.json()["fee"]["amount"])
    buy_amount_after_fee = buy_amount
    buy_amount_after_fee_with_slippage = int(buy_amount_after_fee * 0.99)  # 1% slippage
    assert fee_amount > 0
    assert buy_amount_after_fee_with_slippage > 0

    # Pretty random order deadline :shrug:
    deadline = chain.time() + 60 * 60 * 24 * 2  # 10 days

    # Submit order
    order_payload = {
        "sellToken": token_to_sell.address,
        "buyToken": token_to_buy.address,
        "sellAmount": str(
            int(amount - fee_amount)
        ),  # amount that we have minus the fee we have to pay
        "buyAmount": str(
            buy_amount_after_fee_with_slippage
        ),  # buy amount fetched from the previous call
        "validTo": deadline,
        "appData": "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24",  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
        "feeAmount": str(fee_amount),
        "kind": "buy",
        "partiallyFillable": False,
        "receiver": user.address,
        "signature": milkman.address,
        "from": milkman.address,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "signingScheme": "presign",  # Very important. this tells the api you are going to sign on chain
    }

    orders_url = f"https://api.cow.fi/mainnet/api/v1/orders"
    r = requests.post(orders_url, json=order_payload)
    assert r.ok and r.status_code == 201
    order_uid = r.json()

    gpv2_order = (
        order_payload["sellToken"],
        order_payload["buyToken"],
        order_payload["receiver"],
        int(order_payload["sellAmount"]),
        int(order_payload["buyAmount"]),
        order_payload["validTo"],
        order_payload["appData"],
        int(order_payload["feeAmount"]),
        "0x6ed88e868af0a1983e3886d5f3e95a2fafbd6c3450bc229e27342283dc429ccc",  # KIND_BUY, which should cause revert
        False,
        "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",  # ERC20 BALANCE
        "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",
    )

    with brownie.reverts("!kind_sell"):
        milkman.pairSwap(gpv2_order, user, price_checker, price_checker_data, 0)

    # can still do it the correct way

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
        50,
    )


# the paired order should be valid for at least 5 mins
def test_pair_invalid_valid_to(
    chain,
    milkman,
    user,
    token_to_sell,
    token_to_buy,
    amount,
    gnosis_settlement,
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

    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
    get_params = {
        "sellToken": token_to_sell.address,
        "buyToken": token_to_buy.address,
        "sellAmountBeforeFee": int(amount),
    }
    r = requests.get(fee_and_quote, params=get_params)
    assert r.ok and r.status_code == 200

    fee_amount = int(r.json()["fee"]["amount"])
    buy_amount_after_fee = int(r.json()["buyAmountAfterFee"])
    buy_amount_after_fee_with_slippage = int(buy_amount_after_fee * 0.99)  # 1% slippage
    assert fee_amount > 0
    assert buy_amount_after_fee_with_slippage > 0

    deadline = chain.time() + 60 * 4  # 4 minutes

    order_payload = {
        "sellToken": token_to_sell.address,
        "buyToken": token_to_buy.address,
        "sellAmount": str(int(amount - fee_amount)),
        "buyAmount": str(buy_amount_after_fee_with_slippage),
        "validTo": deadline,
        "appData": "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24",  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
        "feeAmount": str(fee_amount),
        "kind": "sell",
        "partiallyFillable": False,
        "receiver": user.address,
        "signature": milkman.address,
        "from": milkman.address,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "signingScheme": "presign",  # Very important. this tells the api you are going to sign on chain
    }

    orders_url = f"https://api.cow.fi/mainnet/api/v1/orders"
    r = requests.post(orders_url, json=order_payload)
    assert r.ok and r.status_code == 201
    order_uid = r.json()

    gpv2_order = (
        order_payload["sellToken"],
        order_payload["buyToken"],
        order_payload["receiver"],
        int(order_payload["sellAmount"]),
        int(order_payload["buyAmount"]),
        order_payload["validTo"],
        order_payload["appData"],
        int(order_payload["feeAmount"]),
        "0xf3b277728b3fee749481eb3e0b3b48980dbbab78658fc419025cb16eee346775",  # KIND_SELL
        False,
        "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",  # ERC20 BALANCE
        "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",
    )

    with brownie.reverts("expires_too_soon"):
        milkman.pairSwap(gpv2_order, user, price_checker, price_checker_data, 0)

    # can still do it the correct way

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
        50,
    )


# # API doesn't currently accept non-fill-or-kill, so we can't test yet
# # # milkman should only accept fill or kill orders
# # def test_partially_fillable_order(
# #     milkman,
# #     user,
# #     wbtc_whale,
# #     wbtc,
# #     dai,
# #     chain,
# #     gnosis_settlement,
# #     univ2_price_checker,
# # ):
# #     amount = 1e8  # 1 btc
# #     wbtc.transfer(user, amount, {"from": wbtc_whale})

# #     wbtc.approve(milkman, amount, {"from": user})

# #     milkman.requestSwapExactTokensForTokens(
# #         int(amount), wbtc, dai, user, univ2_price_checker, {"from": user}
# #     )

# #     fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
# #     get_params = {
# #         "sellToken": wbtc.address,
# #         "buyToken": dai.address,
# #         "sellAmountBeforeFee": int(amount),
# #     }
# #     r = requests.get(fee_and_quote, params=get_params)
# #     assert r.ok and r.status_code == 200

# #     fee_amount = int(r.json()["fee"]["amount"])
# #     buy_amount_after_fee = int(r.json()["buyAmountAfterFee"])
# #     buy_amount_after_fee_with_slippage = int(buy_amount_after_fee * 0.99)  # 1% slippage
# #     assert fee_amount > 0
# #     assert buy_amount_after_fee_with_slippage > 0

# #     deadline = chain.time() + 60 * 4  # 4 minutes

# #     order_payload = {
# #         "sellToken": wbtc.address,
# #         "buyToken": dai.address,
# #         "sellAmount": str(int(amount - fee_amount)),
# #         "buyAmount": str(buy_amount_after_fee_with_slippage),
# #         "validTo": deadline,
# #         "appData": "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24",  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
# #         "feeAmount": str(fee_amount),
# #         "kind": "sell",
# #         "partiallyFillable": True,
# #         "receiver": user.address,
# #         "signature": milkman.address,
# #         "from": milkman.address,
# #         "sellTokenBalance": "erc20",
# #         "buyTokenBalance": "erc20",
# #         "signingScheme": "presign",  # Very important. this tells the api you are going to sign on chain
# #     }

# #     orders_url = f"https://api.cow.fi/mainnet/api/v1/orders"
# #     r = requests.post(orders_url, json=order_payload)
# #     assert r.ok and r.status_code == 201
# #     order_uid = r.json()

# #     gpv2_order = (
# #         order_payload["sellToken"],
# #         order_payload["buyToken"],
# #         order_payload["receiver"],
# #         int(order_payload["sellAmount"]),
# #         int(order_payload["buyAmount"]),
# #         order_payload["validTo"],
# #         order_payload["appData"],
# #         int(order_payload["feeAmount"]),
# #         "0xf3b277728b3fee749481eb3e0b3b48980dbbab78658fc419025cb16eee346775",  # KIND_SELL
# #         True,
# #         "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",  # ERC20 BALANCE
# #         "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",
# #     )

# #     with brownie.reverts("!fill_or_kill"):
# #         milkman.pairSwap( gpv2_order, user, univ2_price_checker, 0)

# #     # can still do it the correct way

# #     (order_uid, order_payload) = cowswap_create_order_id(
# #         chain, milkman, wbtc, dai, wbtc.balanceOf(milkman), user, 100
# #     )

# #     gpv2_order = construct_gpv2_order(order_payload)

# #     assert gnosis_settlement.preSignature(order_uid) == 0
# #     milkman.pairSwap( gpv2_order, user, univ2_price_checker, 0)
# #     assert gnosis_settlement.preSignature(order_uid) != 0
