from brownie import Contract
import pytest


@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def deployer(accounts):
    yield accounts[1]


# test the following paths:
# GNO -> DAI, $75k & Uniswap as the price checker
# aREP (Aave REP) -> YFI, $100 & 1inch as the price checker
# WETH -> WBTC, $80M & Uniswap as the price checker
# USDC -> USDT, $5M and Curve as the price checker
token_address = {
    "GNO": "0x6810e776880C02933D47DB1b9fc05908e5386b96",
    "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "YFI": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
}

sell_to_buy_map = {
    "GNO": "DAI",
    "USDC": "WBTC",
    "WETH": "YFI",
}


@pytest.fixture(
    params=[
        "GNO",
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
    "GNO": 10_000,  # $1.5M at current prices
    "USDC": 50,
    "WETH": 50_000,  # ~$100M, good for testing the high slippage scenario
    "USDT": 10_000_000,  # USDT via Aave
    "WETH": 10_000,  # WETH via Aave
    "WBTC": 1_000,  # WBTC via Compound
    "DAI": 10_000_000,  # DAI via BProtocol/Aave
    "USDC": 10_000_000,  # USDC via Cream
    "LINK": 500_000,  # LINK via Compound
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
}


@pytest.fixture(scope="session", autouse=True)
def whale(accounts, token_to_sell):
    yield accounts.at(whale_address[token_to_sell.symbol()], force=True)


@pytest.fixture
def dai():
    token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

    yield Contract(token_address)


@pytest.fixture
def gno():
    token_address = "0x6810e776880C02933D47DB1b9fc05908e5386b96"

    yield Contract(token_address)


@pytest.fixture
def wbtc():
    token_address = "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"

    yield Contract(token_address)


@pytest.fixture
def wbtc_whale(accounts):
    address = "0xBF72Da2Bd84c5170618Fbe5914B0ECA9638d5eb5"
    yield accounts.at(address, force=True)


@pytest.fixture
def gno_whale(accounts):
    address = "0x4f8AD938eBA0CD19155a835f617317a6E788c868"
    yield accounts.at(address, force=True)


@pytest.fixture
def usdc():
    token_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

    yield Contract(token_address)


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    yield Contract(token_address)


@pytest.fixture
def milkman(Milkman, deployer):
    milkman = deployer.deploy(Milkman)

    yield milkman


@pytest.fixture
def univ2_price_checker(UniV2PriceChecker, deployer):
    univ2_price_checker = deployer.deploy(UniV2PriceChecker)

    yield univ2_price_checker


@pytest.fixture
def gnosis_settlement():
    contract_address = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"

    yield Contract(contract_address)
