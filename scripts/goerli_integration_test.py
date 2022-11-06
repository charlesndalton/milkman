import requests
import brownie
from brownie import accounts, Contract, ZERO_ADDRESS
from brownie.network.state import Chain
from eth_abi import encode_abi
from brownie.convert import to_bytes

# to run this test:
# $ brownie run --network goerli goerli_integration_test.py

APP_DATA = "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24"  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
KIND_SELL = "0xf3b277728b3fee749481eb3e0b3b48980dbbab78658fc419025cb16eee346775"
ERC20_BALANCE = "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9"
DOMAIN_SEPARATOR = "0xfb378b35457022ecc5709ae5dafad9393c1387ae6d8ce24913a0c969074c07fb"
EIP_1271_MAGIC_VALUE = "0x1626ba7e"


def main():
    unscaled_weth_to_sell = 0.01
    milkman = Contract("0xe80a1C615F75AFF7Ed8F08c9F21f9d00982D666c")
    uni = Contract("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984")
    weth = Contract("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6")
    hash_helper = Contract("0x429A101f42781C53c088392956c95F0A32437b8C")

    weth_to_sell = int(unscaled_weth_to_sell * 1e18)

    print(weth_to_sell)

    # PART 1: USER TRANSACTION

    # if you want to run this on your own, you need to have a brownie account with the same name
    account = accounts.load("goerli-tester")

    if weth.allowance(account, milkman) < weth_to_sell:
        weth.approve(milkman, 2**256 - 1, {"from": account})

    price_checker = ZERO_ADDRESS
    price_checker_data = encode_abi(["uint8"], [int(0)])

    chain = Chain()
    valid_to = chain.time() + 60 * 60 * 24 * 1  # 1 day

    tx = milkman.requestSwapExactTokensForTokens(
        weth_to_sell,
        weth,
        uni,
        account,
        price_checker,
        price_checker_data,
        {"from": account},
    )

    order_contract = tx.events["SwapRequested"]["orderContract"]
    print(f"order contract address: {order_contract}")

    # PART 2: KEEPER HANDLING

    # (fee_amount, buy_amount_after_fee) = get_quote(weth, uni, weth_to_sell)

    # buy_amount_after_fee_with_slippage = int(buy_amount_after_fee * 0.995)

    # signature_encoded_order = encode_order_for_is_valid_signature(
    #     account,
    #     weth,
    #     uni,
    #     account,
    #     weth_to_sell - fee_amount,
    #     buy_amount_after_fee_with_slippage,
    #     valid_to,
    #     fee_amount,
    #     price_checker,
    #     price_checker_data,
    # )

    # print(f"signature: {signature_encoded_order}")

    # submit_offchain_order(order_contract, account, weth, uni, weth_to_sell - fee_amount, fee_amount, buy_amount_after_fee_with_slippage, valid_to, signature_encoded_order)

    # # PART 3: VERIFICATION 
    # gpv2_order = (
    #     weth.address,
    #     uni.address,
    #     account.address,
    #     weth_to_sell - fee_amount,
    #     buy_amount_after_fee_with_slippage,
    #     valid_to,
    #     APP_DATA,
    #     fee_amount,
    #     KIND_SELL,
    #     False,  # fill or kill
    #     ERC20_BALANCE,
    #     ERC20_BALANCE,
    # )

    # order_digest = hash_helper.hash(
    #     gpv2_order, to_bytes(DOMAIN_SEPARATOR, "bytes32")
    # )

    # print(f"order digest: {order_digest}")

    # is_valid_sig = Contract(order_contract).isValidSignature(
    #     order_digest, signature_encoded_order
    # )

    # print(f"magic value?: {is_valid_sig}")


# encode a market order in the way that Milkman's isValidSignature function accepts it
def encode_order_for_is_valid_signature(
    order_creator,
    sell_token,
    buy_token,
    receiver,
    sell_amount,
    buy_amount,
    valid_to,
    fee_amount,
    price_checker,
    price_checker_data,
    buy_or_sell=KIND_SELL,
    sell_token_balance=ERC20_BALANCE,
    buy_token_balance=ERC20_BALANCE,
    partially_fillable=False,
):
    return encode_abi(
        [
            "address",
            "address",
            "address",
            "uint256",
            "uint256",
            "uint32",
            "bytes32",
            "uint256",
            "bytes32",
            "bool",
            "bytes32",
            "bytes32",
            "address",
            "address",
            "bytes",
        ],
        [
            sell_token.address,
            buy_token.address,
            receiver.address,
            sell_amount,
            buy_amount,
            valid_to,
            to_bytes(APP_DATA, "bytes32"),
            fee_amount,
            to_bytes(buy_or_sell, "bytes32"),
            partially_fillable,
            to_bytes(sell_token_balance, "bytes32"),
            to_bytes(buy_token_balance, "bytes32"),
            order_creator.address,
            price_checker,
            price_checker_data,
        ],
    )


# submit the order to the cow.fi endpoint
def submit_offchain_order(
    order_contract,
    receiver,
    sell_token,
    buy_token,
    sell_amount,
    fee_amount,
    buy_amount,
    valid_to,
    signature,
):

    assert fee_amount > 0
    assert buy_amount > 0

    # Submit order
    order_payload = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "sellAmount": str(
            sell_amount
        ),  # amount that we have minus the fee we have to pay
        "buyAmount": str(
            buy_amount
        ),  # buy amount fetched from the previous call
        "validTo": valid_to,
        "appData": APP_DATA,
        "feeAmount": str(fee_amount),
        "kind": "sell",
        "partiallyFillable": False,
        "receiver": receiver.address,
        "signature": '0x' + signature.hex(),
        "from": order_contract,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "signingScheme": "eip1271",  # Very important. this tells the api you are going to sign on chain
    }

    orders_url = f"https://barn.api.cow.fi/goerli/api/v1/orders"
    r = requests.post(orders_url, json=order_payload)

    times_to_retry = 3
    while times_to_retry > 0:
        if r.ok and r.status_code == 201:
            break

        r = requests.post(orders_url, json=order_payload)
        times_to_retry -= 1
    assert r.ok and r.status_code == 201
    order_uid = r.json()
    print(f"Payload: {order_payload}")
    print(f"Order uid: {order_uid}")

    return (order_uid, order_payload)


def get_quote(sell_token, buy_token, sell_amount):
    # get the fee + the buy amount after fee
    fee_and_quote = "https://barn.api.cow.fi/goerli/api/v1/feeAndQuote/sell"
    get_params = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "sellAmountBeforeFee": int(sell_amount),
    }

    r = requests.get(fee_and_quote, params=get_params)
    times_to_retry = 3
    while times_to_retry > 0:
        if r.ok and r.status_code == 200:
            break

        time.sleep(1)

        r = requests.get(fee_and_quote, params=get_params)
        times_to_retry -= 1
    print(f"Response: {r}")
    assert r.ok and r.status_code == 200

    # These two values are needed to create an order
    fee_amount = int(r.json()["fee"]["amount"])
    buy_amount_after_fee = int(r.json()["buyAmountAfterFee"])

    return (fee_amount, buy_amount_after_fee)
