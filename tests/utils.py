from os import times
import requests


def pair_swap(
    chain,
    gnosis_settlement,
    milkman,
    user,
    receiver,
    token_to_sell,
    token_to_buy,
    amount_to_sell,
    price_checker,
    allowed_slippage_bps,
    nonce,
):
    (order_uid, order_payload) = create_offchain_order(
        chain,
        milkman,
        receiver,
        token_to_sell,
        token_to_buy,
        amount_to_sell,
        allowed_slippage_bps,
    )

    gpv2_order = convert_offchain_order_into_gpv2_order(order_payload)

    assert gnosis_settlement.preSignature(order_uid) == 0
    milkman.pairSwap(gpv2_order, user, price_checker, nonce)
    assert gnosis_settlement.preSignature(order_uid) != 0


def convert_offchain_order_into_gpv2_order(order_payload):
    # struct Data {
    #     IERC20 sellToken;
    #     IERC20 buyToken;
    #     address receiver;
    #     uint256 sellAmount;
    #     uint256 buyAmount;
    #     uint32 validTo;
    #     bytes32 appData;
    #     uint256 feeAmount;
    #     bytes32 kind;
    #     bool partiallyFillable;
    #     bytes32 sellTokenBalance;
    #     bytes32 buyTokenBalance;
    # }
    # src: https://github.com/cowprotocol/contracts/blob/b5224fac50d050efec0d72ab303c0420576ab2ae/src/contracts/libraries/GPv2Order.sol#L11
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
        False,  # fill or kill
        "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",  # ERC20 BALANCE
        "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9",
    )

    return gpv2_order


# submit the order to the cow.fi endpoint
def create_offchain_order(
    chain, milkman, receiver, sell_token, buy_token, amount, allowed_slippage_in_bips
):
    # get the fee + the buy amount after fee
    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
    get_params = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "sellAmountBeforeFee": int(amount),
    }

    r = requests.get(fee_and_quote, params=get_params)
    times_to_retry = 3
    while times_to_retry > 0:
        if r.ok and r.status_code == 200:
            break

        r = requests.get(fee_and_quote, params=get_params)
        times_to_retry -= 1
    assert r.ok and r.status_code == 200

    # These two values are needed to create an order
    fee_amount = int(r.json()["fee"]["amount"])
    buy_amount_after_fee = int(r.json()["buyAmountAfterFee"])
    buy_amount_after_fee_with_slippage = int(
        (buy_amount_after_fee * (10_000 - allowed_slippage_in_bips)) / 10_000
    )
    assert fee_amount > 0
    assert buy_amount_after_fee_with_slippage > 0

    deadline = chain.time() + 60 * 60 * 24 * 1  # 1 day

    # Submit order
    order_payload = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "sellAmount": str(
            amount - fee_amount
        ),  # amount that we have minus the fee we have to pay
        "buyAmount": str(
            buy_amount_after_fee_with_slippage
        ),  # buy amount fetched from the previous call
        "validTo": deadline,
        "appData": "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24",  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
        "feeAmount": str(fee_amount),
        "kind": "sell",
        "partiallyFillable": False,
        "receiver": receiver.address,
        "signature": milkman.address,
        "from": milkman.address,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "signingScheme": "presign",  # Very important. this tells the api you are going to sign on chain
    }

    orders_url = f"https://api.cow.fi/mainnet/api/v1/orders"
    r = requests.post(orders_url, json=order_payload)

    times_to_retry = 3
    while times_to_retry > 0:
        if r.ok and r.status_code == 201:
            break

        r = requests.get(fee_and_quote, params=get_params)
        times_to_retry -= 1
    assert r.ok and r.status_code == 201
    order_uid = r.json()
    print(f"Payload: {order_payload}")
    print(f"Order uid: {order_uid}")

    return (order_uid, order_payload)
