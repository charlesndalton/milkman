from eth_abi import encode_abi
from eth_utils import keccak
import requests
import brownie

def test_pair(
    milkman,
    user,
    wbtc_whale,
    wbtc,
    dai,
    chain,
    gnosis_settlement,
    univ2_price_checker,
):
    amount = 1e8  # 1 btc
    wbtc.transfer(user, amount, {"from": wbtc_whale})

    wbtc.approve(milkman, amount, {"from": user})

    milkman.requestSwapExactTokensForTokens(
        int(amount), wbtc, dai, user, univ2_price_checker, {"from": user}
    )

    (order_uid, order_payload) = cowswap_create_order_id(
        chain, milkman, wbtc, dai, wbtc.balanceOf(milkman), user
    )

    gpv2_order = construct_gpv2_order(order_payload)

    assert gnosis_settlement.preSignature(order_uid) == 0
    milkman.pairSwap(order_uid, gpv2_order, user, univ2_price_checker, 0)
    assert gnosis_settlement.preSignature(order_uid) != 0


def test_pair_parameter_mismatch(
    milkman,
    user,
    wbtc_whale,
    wbtc,
    dai,
    chain,
    gnosis_settlement,
    univ2_price_checker,
):
    amount = 1e8  # 1 btc
    wbtc.transfer(user, amount, {"from": wbtc_whale})

    wbtc.approve(milkman, amount, {"from": user})

    milkman.requestSwapExactTokensForTokens(
        int(amount), wbtc, dai, user, univ2_price_checker, {"from": user}
    )

    (order_uid, order_payload) = cowswap_create_order_id(
        chain, milkman, wbtc, dai, wbtc.balanceOf(milkman), wbtc_whale # try to set the whale as the receiver
    )

    gpv2_order = construct_gpv2_order(order_payload)

    with brownie.reverts():
        milkman.pairSwap(order_uid, gpv2_order, user, univ2_price_checker, 0)
    
    (order_uid, order_payload) = cowswap_create_order_id(
        chain, wbtc_whale, wbtc, dai, wbtc.balanceOf(milkman), user # try to set the whale as the owner
    )

    gpv2_order = construct_gpv2_order(order_payload)

    with brownie.reverts():
        milkman.pairSwap(order_uid, gpv2_order, user, univ2_price_checker, 0)

    # can still do it the correct way

    (order_uid, order_payload) = cowswap_create_order_id(
        chain, milkman, wbtc, dai, wbtc.balanceOf(milkman), user
    )

    gpv2_order = construct_gpv2_order(order_payload)

    assert gnosis_settlement.preSignature(order_uid) == 0
    milkman.pairSwap(order_uid, gpv2_order, user, univ2_price_checker, 0)
    assert gnosis_settlement.preSignature(order_uid) != 0

    
    

def construct_gpv2_order(order_payload):
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
    order = (
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

    return order


def cowswap_create_order_id(
    chain, milkman, sell_token, buy_token, amount, receiver
):
    # get the fee + the buy amount after fee
    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
    get_params = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "sellAmountBeforeFee": amount,
    }
    r = requests.get(fee_and_quote, params=get_params)
    assert r.ok and r.status_code == 200

    # These two values are needed to create an order
    fee_amount = int(r.json()["fee"]["amount"])
    buy_amount_after_fee = int(r.json()["buyAmountAfterFee"])
    buy_amount_after_fee_with_slippage = int(
        buy_amount_after_fee * 0.97
    )  # 1% slippage. Website default is 0.05%
    assert fee_amount > 0
    assert buy_amount_after_fee_with_slippage > 0

    # Pretty random order deadline :shrug:
    deadline = chain.time() + 60 * 60 * 24 * 2  # 10 days

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
    assert r.ok and r.status_code == 201
    order_uid = r.json()
    print(f"Payload: {order_payload}")
    print(f"Order uid: {order_uid}")

    return (order_uid, order_payload)
