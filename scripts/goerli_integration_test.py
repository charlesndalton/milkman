import requests
import brownie
from brownie import accounts, Contract, ZERO_ADDRESS
from brownie.network.state import Chain
from eth_abi import encode_abi
from brownie.convert import to_bytes
import time
from web3 import Web3

EMPTY_BYTES = encode_abi(["uint8"], [int(0)])

# to run this test:
# $ brownie run --network goerli goerli_integration_test.py

APP_DATA = "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24"  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
KIND_SELL = "0xf3b277728b3fee749481eb3e0b3b48980dbbab78658fc419025cb16eee346775"
ERC20_BALANCE = "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9"
DOMAIN_SEPARATOR = "0xfb378b35457022ecc5709ae5dafad9393c1387ae6d8ce24913a0c969074c07fb"  # goerli domain separator
EIP_1271_MAGIC_VALUE = "0x1626ba7e"

UNI_ADDRESS = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
SUSHI_DYNAMIC_SLIPPAGE_PRICE_CHECKER_ADDRESS = (
    "0x5A5633909060c75e5B7cB4952eFad918c711F587"
)

MILKMAN_ADDRESS = "0x5D9C7CBeF995ef16416D963EaCEEC8FcA2590731"
PRICE_CHECKER_ADDRESS = SUSHI_DYNAMIC_SLIPPAGE_PRICE_CHECKER_ADDRESS
HASH_HELPER_ADDRESS = "0x429A101f42781C53c088392956c95F0A32437b8C"

INFURA_KEY = ""  # put your own here :)


def main():
    w3 = Web3(Web3.HTTPProvider(f"https://goerli.infura.io/v3/{INFURA_KEY}"))

    unscaled_weth_to_sell = 0.005
    milkman = Contract(MILKMAN_ADDRESS)
    uni = Contract(UNI_ADDRESS)
    weth = Contract(WETH_ADDRESS)
    hash_helper = Contract(HASH_HELPER_ADDRESS)

    price_checker = Contract(PRICE_CHECKER_ADDRESS)
    price_checker_data = encode_abi(
        ["uint256", "bytes"], [int(600), EMPTY_BYTES]
    )  # allow 6% slippage
    web3_price_checker = w3.eth.contract(
        address=PRICE_CHECKER_ADDRESS, abi=price_checker.abi
    )  # use web3 instead of Brownie so we can do gas estimation

    weth_to_sell = int(unscaled_weth_to_sell * 1e18)

    print(weth_to_sell)

    # PART 1: USER CALLS `requestSwapExactTokensForTokens`

    # if you want to run this on your own, you need to have a brownie account with the same name
    account = accounts.load("goerli-tester")

    if weth.allowance(account, milkman) < weth_to_sell:
        weth.approve(milkman, 2**256 - 1, {"from": account})

    chain = Chain()
    # valid_to = chain.time() + 60 * 60 * 24 * 1  # 1 day

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

    # STEP 2: ESTIMATE GAS COST OF VERIFICATION

    web3_order_contract = w3.eth.contract(
        address=order_contract, abi=milkman.abi
    )  # use web3 instead of Brownie so we can do gas estimation

    mock_buy_amount = int(100_000 * 1e18)
    mock_valid_to = int(2668808292)  # should be valid until 2054 :)
    mock_fee_amount = 0

    mock_gpv2_order = (
        weth.address,
        uni.address,
        account.address,
        weth_to_sell,
        mock_buy_amount,
        mock_valid_to,
        APP_DATA,
        mock_fee_amount,
        KIND_SELL,
        False,  # fill or kill
        ERC20_BALANCE,
        ERC20_BALANCE,
    )

    mock_order_digest = hash_helper.hash(
        mock_gpv2_order, to_bytes(DOMAIN_SEPARATOR, "bytes32")
    )

    mock_signature = encode_order_for_is_valid_signature(
        order_creator=account,
        sell_token=weth,
        buy_token=uni,
        receiver=account,
        sell_amount=weth_to_sell,
        buy_amount=mock_buy_amount,
        valid_to=mock_valid_to,
        fee_amount=mock_fee_amount,
        price_checker=price_checker,
        price_checker_data=price_checker_data,
    )

    estimated_verification_gas = (
        web3_order_contract.functions.isValidSignature(
            mock_order_digest, mock_signature
        ).estimate_gas()
        - 21_000
    )

    # PART 3: GET QUOTE

    (fee_amount, buy_amount_after_fee, valid_to) = get_quote(
        order_contract,
        account,
        weth,
        uni,
        weth_to_sell,
        verification_gas_limit=int(
            estimated_verification_gas * 1.7
        ),  # add some padding for safety
    )

    # PART 3: VERIFY THAT AN ORDER COULD BE FULFILLED BEFORE SUBMITTING IT

    buy_amount_after_fee_with_slippage = int(buy_amount_after_fee * 0.99)

    signature_encoded_order = encode_order_for_is_valid_signature(
        order_creator=account,
        sell_token=weth,
        buy_token=uni,
        receiver=account,
        sell_amount=weth_to_sell - fee_amount,
        buy_amount=buy_amount_after_fee_with_slippage,
        valid_to=valid_to,
        fee_amount=fee_amount,
        price_checker=price_checker,
        price_checker_data=price_checker_data,
    )

    print(f"signature: {signature_encoded_order}")

    gpv2_order = (
        weth.address,
        uni.address,
        account.address,
        weth_to_sell - fee_amount,
        buy_amount_after_fee_with_slippage,
        valid_to,
        APP_DATA,
        fee_amount,
        KIND_SELL,
        False,  # fill or kill
        ERC20_BALANCE,
        ERC20_BALANCE,
    )

    order_digest = hash_helper.hash(gpv2_order, to_bytes(DOMAIN_SEPARATOR, "bytes32"))

    print(f"order digest: {order_digest}")

    is_valid_sig = Contract(order_contract).isValidSignature(
        order_digest, signature_encoded_order
    )

    print(f"magic value?: {is_valid_sig}")

    assert is_valid_sig == EIP_1271_MAGIC_VALUE

    # PART 4: SUBMIT OFF-CHAIN ORDER

    submit_offchain_order(
        order_contract,
        account,
        weth,
        uni,
        weth_to_sell - fee_amount,
        fee_amount,
        buy_amount_after_fee_with_slippage,
        valid_to,
        signature_encoded_order,
    )

    # PART 5: WAIT, AND CHECK THAT ALL TOKENS HAVE BEEN SOLD

    num_checks = 0
    while True:
        time.sleep(5)
        num_checks += 1

        if num_checks > 200:
            print("After 200 checks, tokens are still in order contract. Exiting...")
            break

        if weth.balanceOf(order_contract) == 0:
            break

    # TODO


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
            price_checker.address,
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

    # assert fee_amount > 0
    assert buy_amount > 0

    # Submit order
    order_payload = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "sellAmount": str(
            sell_amount
        ),  # amount that we have minus the fee we have to pay
        "buyAmount": str(buy_amount),  # buy amount fetched from the previous call
        "validTo": valid_to,
        "appData": APP_DATA,
        "feeAmount": str(fee_amount),  # limit order
        "kind": "sell",
        "partiallyFillable": False,
        "receiver": receiver.address,
        "signature": "0x" + signature.hex(),
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


def get_quote(
    order_contract,
    receiver,
    sell_token,
    buy_token,
    sell_amount,
    verification_gas_limit=50000,
):
    # get the fee + the buy amount after fee
    quote_url = "https://barn.api.cow.fi/goerli/api/v1/quote"

    quote_payload = {
        "sellToken": sell_token.address,
        "buyToken": buy_token.address,
        "receiver": receiver.address,
        "appData": APP_DATA,
        "partiallyFillable": False,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "from": order_contract,
        "priceQuality": "fast",
        "signingScheme": "eip1271",
        "onchainOrder": True,
        "kind": "sell",
        "sellAmountBeforeFee": str(sell_amount),
        "verificationGasLimit": verification_gas_limit,
    }

    r = requests.post(quote_url, json=quote_payload)

    print(f"Response: {r}")
    assert r.ok and r.status_code == 200

    # These two values are needed to create an order
    quote = r.json()["quote"]
    fee_amount = int(quote["feeAmount"])
    buy_amount_after_fee = int(quote["buyAmount"])
    valid_to = int(quote["validTo"])

    return (fee_amount, buy_amount_after_fee, valid_to)
