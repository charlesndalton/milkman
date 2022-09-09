from brownie import Contract
from eth_abi import encode_abi
import pytest


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
# aREP (Aave REP) -> YFI, $100 & 1inch as the price checker
# WETH -> WBTC, $80M & Uniswap as the price checker
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
}

sell_to_buy_map = {
    "TOKE": "DAI",
    "USDC": "USDT",
    "GUSD": "USDC",
    "AAVE": "WETH",
    "BAT": "ALCX",
}


@pytest.fixture(
    params=[
        # "TOKE",
        "USDC",
        "GUSD",
        # "AAVE",
        # "BAT",
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
}


@pytest.fixture(scope="session", autouse=True)
def whale(accounts, token_to_sell):
    yield accounts.at(whale_address[token_to_sell.symbol()], force=True)


@pytest.fixture
def price_checker(UniV2PriceChecker, CurvePriceChecker, ChainlinkPriceChecker, deployer, token_to_sell):
    symbol = token_to_sell.symbol()

    if symbol == "TOKE":
        univ2_price_checker = deployer.deploy(UniV2PriceChecker)
        yield univ2_price_checker
    if symbol == "USDC" or symbol == "GUSD":
        curve_price_checker = deployer.deploy(CurvePriceChecker)
        yield curve_price_checker
    if symbol == "AAVE" or symbol == "BAT":
        chainlink_price_checker = deployer.deploy(ChainlinkPriceChecker)
        yield chainlink_price_checker


# which price checker data to use for each swap
price_checker_datas = {
    "TOKE": encode_abi(["uint8"], [int(0)]),  # doesn't matter
    "USDC": encode_abi(["uint8"], [int(0)]),  # default slippage
    "GUSD": encode_abi(["uint256"], [int(500)]),  # 5% slippage to allow for gas
    "AAVE": encode_abi(["uint256", "address[]", "bool[]"], [int(0), ["0x6Df09E975c830ECae5bd4eD9d90f3A95a4f88012"], [False]]), # AAVE/ETH feed
    "BAT": encode_abi(["uint256", "address[]", "bool[]"], [int(700), ["0x0d16d4528239e9ee52fa531af613acdb23d88c94", "0x194a9aaf2e0b67c35915cd01101585a33fe25caa"], [False, True]]), # BAT/ETH & ALCX/ETH feeds, allow 7% slippage since these are relatively illiquid
}


@pytest.fixture(scope="session", autouse=True)
def price_checker_data(token_to_sell):
    yield price_checker_datas[token_to_sell.symbol()]


@pytest.fixture
def milkman(Milkman, deployer):
    milkman = deployer.deploy(Milkman)

    yield milkman


@pytest.fixture
def gnosis_settlement():
    contract_address = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"

    yield Contract(contract_address)
