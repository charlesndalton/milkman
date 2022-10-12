from os import times
import requests
from eth_abi import encode_abi
from eth_utils import keccak
import time
from brownie.convert import to_bytes

APP_DATA = "0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24"  # maps to https://bafybeiblq2ko2maieeuvtbzaqyhi5fzpa6vbbwnydsxbnsqoft5si5b6eq.ipfs.dweb.link
KIND_SELL = "0xf3b277728b3fee749481eb3e0b3b48980dbbab78658fc419025cb16eee346775"
ERC20_BALANCE = "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9"
DOMAIN_SEPARATOR = "0xc078f884a2676e1345748b1feace7b0abee5d00ecadb6e574dcdd109a63e8943"
EIP_1271_MAGIC_VALUE = "0x1626ba7e"


def check_swap_requested(
    order_contract,
    receiver,
    from_token,
    to_token,
    amount,
    price_checker,
    price_checker_data,
):
    # user, receiver, from_token, to_token, amount_in, price_checker, price_checker_data, nonce
    encoded_market_order = encode_market_order_for_milkman(
        receiver,
        from_token,
        to_token,
        amount,
        price_checker,
        price_checker_data,
    )
    swap_hash = keccak(encoded_market_order)

    print(f"Swap Hash: {order_contract.swapHash().hex()}")
    print(f"Calculated Swap Hash: {swap_hash.hex()}")

    assert order_contract.swapHash().hex() == swap_hash.hex()


# encode a market order in the way that milkman encodes it as the swapHash pre-image
def encode_market_order_for_milkman(
    receiver,
    from_token,
    to_token,
    amount,
    price_checker,
    price_checker_data,
):
    return encode_abi(
        [
            "address",
            "address",
            "address",
            "uint256",
            "address",
            "bytes",
        ],
        [
            receiver.address,
            from_token.address,
            to_token.address,
            amount,
            price_checker.address,
            price_checker_data,
        ],
    )


def encode_order_into_gpv2_order(
    sell_token,
    buy_token,
    receiver,
    sell_amount,
    buy_amount,
    valid_to,
    fee_amount,
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
            to_bytes(KIND_SELL, "bytes32"),
            False,
            to_bytes(ERC20_BALANCE, "bytes32"),
            to_bytes(ERC20_BALANCE, "bytes32"),
        ],
    )


# encode a market order in the way tha `signature`
def encode_order_for_is_valid_signature(
    sell_token,
    buy_token,
    receiver,
    sell_amount,
    buy_amount,
    valid_to,
    fee_amount,
    price_checker,
    price_checker_data,
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
            to_bytes(KIND_SELL, "bytes32"),
            False,
            to_bytes(ERC20_BALANCE, "bytes32"),
            to_bytes(ERC20_BALANCE, "bytes32"),
            price_checker.address,
            price_checker_data,
        ],
    )


def unpair_swap(gnosis_settlement, milkman, swap_id, order_uid):
    assert gnosis_settlement.preSignature(order_uid) != 0
    milkman.unpairSwap(swap_id)
    assert gnosis_settlement.preSignature(order_uid) == 0


def pair_swap(
    nonce,
    chain,
    gnosis_settlement,
    milkman,
    user,
    receiver,
    token_to_sell,
    token_to_buy,
    amount,
    price_checker,
    price_checker_data,
    allowed_slippage_bps,
):
    (order_uid, order_payload) = create_offchain_order(
        chain,
        milkman,
        receiver,
        token_to_sell,
        token_to_buy,
        amount,
        allowed_slippage_bps,
    )

    gpv2_order = convert_offchain_order_into_gpv2_order(order_payload)

    assert gnosis_settlement.preSignature(order_uid) == 0
    milkman.pairSwap(gpv2_order, user, price_checker, price_checker_data, nonce)
    assert gnosis_settlement.preSignature(order_uid) != 0

    return (order_uid, order_payload)


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
        KIND_SELL,
        False,  # fill or kill
        ERC20_BALANCE,
        ERC20_BALANCE,
    )

    return gpv2_order


# submit the order to the cow.fi endpoint
def create_offchain_order(
    chain, milkman, receiver, sell_token, buy_token, amount, allowed_slippage_in_bips
):
    (fee_amount, buy_amount_after_fee) = get_quote(sell_token, buy_token, amount)

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
        "appData": APP_DATA,
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

        r = requests.post(orders_url, json=order_payload)
        times_to_retry -= 1
    assert r.ok and r.status_code == 201
    order_uid = r.json()
    print(f"Payload: {order_payload}")
    print(f"Order uid: {order_uid}")

    return (order_uid, order_payload)


def get_quote(sell_token, buy_token, sell_amount):
    # get the fee + the buy amount after fee
    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
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
