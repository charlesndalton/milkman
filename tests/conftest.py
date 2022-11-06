from lib2to3.pgen2 import token
from brownie import Contract
from eth_abi import encode_abi
import pytest
import utils


@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture(scope="session", autouse=True)
def user(accounts):
    yield accounts[0]


@pytest.fixture(scope="session", autouse=True)
def deployer(accounts):
    yield accounts[1]


# test the following paths:
# TOKE -> DAI, $75k, Sushiswap price checker
# USDC -> USDT, $5M, Curve price checker
# GUSD -> USDC, $1k, Curve price checker
# AAVE -> WETH, $250k, Chainlink price checker
# BAT -> ALCX, $100k, Chainlink price checker
# WETH -> WBTC, $80M & Uniswap as the price checker
# UNI -> USDT, $500k & Uniswap as the price checker
# ALCX -> TOKE, $100k, Meta price checker with Chainlink and Sushiswap
token_address = {
    "TOKE": "0x2e9d63788249371f1DFC918a52f8d799F4a38C94",
    "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "GUSD": "0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd",
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "BAT": "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",
    "ALCX": "0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "ALCX": "0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF",
}

sell_to_buy_map = {
    "TOKE": "DAI",
    "USDC": "USDT",
    "GUSD": "USDC",
    "AAVE": "WETH",
    "BAT": "ALCX",
    "WETH": "WBTC",
    "UNI": "USDT",
    "ALCX": "TOKE",
}


@pytest.fixture(
    params=[
        "TOKE",
        "USDC",
        "GUSD",
        "AAVE",
        "BAT",
        "WETH",
        "UNI",
        "ALCX",
    ],
    scope="session",
    autouse=True,
)
def token_to_sell(request):
    yield Contract(token_address[request.param])


@pytest.fixture(scope="session", autouse=True)
def token_to_buy(token_to_sell):
    yield Contract(token_address[sell_to_buy_map[token_to_sell.symbol()]])


amounts = {
    "TOKE": 80_000,
    "USDC": 5_000_000,
    "GUSD": 1_000,
    "AAVE": 2_500,
    "BAT": 280_000,
    "WETH": 50_000,
    "UNI": 80_000,
    "ALCX": 4_000,
}


@pytest.fixture(scope="function", autouse=True)
def amount(token_to_sell, user, whale):
    amount = int(amounts[token_to_sell.symbol()] * 10 ** token_to_sell.decimals())
    token_to_sell.transfer(user, amount, {"from": whale})

    yield int(amount)


whale_address = {
    "GUSD": "0x5f65f7b609678448494De4C87521CdF6cEf1e932",
    "USDT": "0xa929022c9107643515f5c777ce9a910f0d1e490c",
    "WETH": "0x030ba81f1c18d280636f32af80b9aad02cf0854e",
    "WBTC": "0xccf4429db6322d5c611ee964527d42e5d685dd6a",
    "DAI": "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
    "USDC": "0x0A59649758aa4d66E25f08Dd01271e891fe52199",
    "LINK": "0x98C63b7B319dFBDF3d811530F2ab9DfE4983Af9D",
    "GNO": "0x4f8AD938eBA0CD19155a835f617317a6E788c868",
    "TOKE": "0x96F98Ed74639689C3A11daf38ef86E59F43417D3",
    "AAVE": "0x4da27a545c0c5B758a6BA100e3a049001de870f5",
    "BAT": "0x6C8c6b02E7b2BE14d4fA6022Dfd6d75921D90E4E",
    "UNI": "0x1a9C8182C09F50C8318d769245beA52c32BE35BC",
    "ALCX": "0x000000000000000000000000000000000000dEaD",
}


@pytest.fixture(scope="session", autouse=True)
def whale(accounts, token_to_sell):
    yield accounts.at(whale_address[token_to_sell.symbol()], force=True)


@pytest.fixture
def price_checker(
    token_to_sell,
    sushiswap_price_checker,
    curve_price_checker,
    chainlink_price_checker,
    univ3_price_checker,
    meta_price_checker,
):
    symbol = token_to_sell.symbol()

    if symbol == "TOKE":
        yield sushiswap_price_checker
    if symbol == "USDC" or symbol == "GUSD":
        yield curve_price_checker
    if symbol == "AAVE" or symbol == "BAT":
        yield chainlink_price_checker
    if symbol == "WETH" or symbol == "UNI":
        yield univ3_price_checker
    if symbol == "ALCX":
        yield meta_price_checker


@pytest.fixture
def chainlink_expected_out_calculator(ChainlinkExpectedOutCalculator, deployer):
    yield deployer.deploy(ChainlinkExpectedOutCalculator)


@pytest.fixture
def curve_expected_out_calculator(CurveExpectedOutCalculator, deployer):
    yield deployer.deploy(CurveExpectedOutCalculator)


@pytest.fixture
def sushiswap_expected_out_calculator(UniV2ExpectedOutCalculator, deployer):
    sushi_router = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
    yield deployer.deploy(
        UniV2ExpectedOutCalculator, "SUSHI_EXPECTED_OUT_CALCULATOR", sushi_router
    )


@pytest.fixture
def univ3_expected_out_calculator(UniV3ExpectedOutCalculator, deployer):
    yield deployer.deploy(UniV3ExpectedOutCalculator)


@pytest.fixture
def meta_expected_out_calculator(MetaExpectedOutCalculator, deployer):
    yield deployer.deploy(MetaExpectedOutCalculator)


@pytest.fixture
def chainlink_price_checker(
    DynamicSlippageChecker, chainlink_expected_out_calculator, deployer
):
    yield deployer.deploy(
        DynamicSlippageChecker,
        "CHAINLINK_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
        chainlink_expected_out_calculator,
    )


@pytest.fixture
def curve_price_checker(
    DynamicSlippageChecker, curve_expected_out_calculator, deployer
):
    yield deployer.deploy(
        DynamicSlippageChecker,
        "CURVE_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
        curve_expected_out_calculator,
    )


@pytest.fixture
def sushiswap_price_checker(
    FixedSlippageChecker, sushiswap_expected_out_calculator, deployer
):
    yield deployer.deploy(
        FixedSlippageChecker,
        "SUSHISWAP_STATIC_500_BPS_SLIPPAGE_PRICE_CHECKER",
        500,
        sushiswap_expected_out_calculator,
    )  # 5% slippage


@pytest.fixture
def univ3_price_checker(
    DynamicSlippageChecker, univ3_expected_out_calculator, deployer
):
    yield deployer.deploy(
        DynamicSlippageChecker,
        "UNIV3_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
        univ3_expected_out_calculator,
    )


@pytest.fixture
def meta_price_checker(DynamicSlippageChecker, meta_expected_out_calculator, deployer):
    yield deployer.deploy(
        DynamicSlippageChecker,
        "META_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
        meta_expected_out_calculator,
    )


# which price checker data to use for each swap
price_checker_datas = {
    "TOKE": utils.EMPTY_BYTES,
    "USDC": utils.dynamic_slippage_data(400, utils.EMPTY_BYTES),
    "GUSD": utils.dynamic_slippage_data(500, utils.EMPTY_BYTES),
    "AAVE": utils.dynamic_slippage_data(
        400,
        encode_abi(
            ["address[]", "bool[]"],
            [["0x6Df09E975c830ECae5bd4eD9d90f3A95a4f88012"], [False]],
        ),
    ),  # AAVE/ETH feed
    "BAT": utils.dynamic_slippage_data(
        2000,
        encode_abi(
            ["address[]", "bool[]"],
            [
                [
                    "0x0d16d4528239e9ee52fa531af613acdb23d88c94",
                    "0x194a9aaf2e0b67c35915cd01101585a33fe25caa",
                ],
                [False, True],
            ],
        ),
    ),  # BAT/ETH & ALCX/ETH feeds, allow 10% slippage since these are relatively illiquid
    "WETH": utils.dynamic_slippage_data(
        1400,
        encode_abi(
            ["address[]", "uint24[]"],
            [[token_address["WETH"], token_address["WBTC"]], [int(30)]],
        ),
    ),  # 14% slippage for such a large trade
    "UNI": utils.dynamic_slippage_data(
        600,
        encode_abi(
            ["address[]", "uint24[]"],
            [
                [
                    token_address["UNI"],
                    token_address["WETH"],
                    token_address["USDC"],
                    token_address["USDT"],
                ],
                [int(30), int(30), int(1)],
            ],
        ),
    ),  # 6% slippage
}


@pytest.fixture
def price_checker_data(token_to_sell, chainlink_expected_out_calculator, sushiswap_expected_out_calculator):
    if token_to_sell.symbol() == "ALCX":
        yield utils.dynamic_slippage_data(
            1000,
            encode_abi(
                ["address[]", "address[]", "bytes[]"],
                [
                    [
                        token_address["ALCX"],
                        token_address["WETH"],
                        token_address["TOKE"],
                    ],
                    [
                        chainlink_expected_out_calculator.address,
                        sushiswap_expected_out_calculator.address,
                    ],
                    [
                        encode_abi(
                            ["address[]", "bool[]"],
                            [["0x194a9aaf2e0b67c35915cd01101585a33fe25caa"], [False]], # if you're reading this, forgive me pls
                        ),
                        utils.EMPTY_BYTES,
                    ],
                ],
            ),
        )
    else:
        yield price_checker_datas[token_to_sell.symbol()]


@pytest.fixture
def milkman(Milkman, deployer):
    milkman = deployer.deploy(Milkman)

    yield milkman


@pytest.fixture
def hash_helper(HashHelper, deployer):
    hash_helper = deployer.deploy(HashHelper)

    yield hash_helper


@pytest.fixture
def gnosis_settlement():
    contract_address = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"

    yield Contract(contract_address)
