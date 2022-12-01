from eth_abi import encode_abi

EMPTY_BYTES = encode_abi(["uint8"], [int(0)])


def univ2_expected_out_data():
    return EMPTY_BYTES


def curve_expected_out_data():
    return EMPTY_BYTES


def chainlink_expected_out_data(price_feed_addresses, reverses):
    return encode_abi(
        ["address[]", "bool[]"],
        [
            price_feed_addresses,
            reverses,
        ],
    )


def univ3_expected_out_data(swap_path, pool_fees):
    return encode_abi(["address[]", "uint24[]"], [swap_path, pool_fees])


def meta_expected_out_data(swap_path, expected_out_calculators, expected_out_data):
    return encode_abi(
        ["address[]", "address[]", "bytes[]"],
        [
            swap_path,
            expected_out_calculators,
            expected_out_data,
        ],
    )


def dynamic_slippage_price_checker_data(allowed_slippage_bips, expected_out_data):
    return encode_abi(
        ["uint256", "bytes"], [int(allowed_slippage_bips), expected_out_data]
    )


def fixed_slippage_price_checker_data(expected_out_data):
    return expected_out_data
