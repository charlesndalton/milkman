from brownie import Contract
import pytest


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def deployer(accounts):
    yield accounts[1]


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
