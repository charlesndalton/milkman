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
def usdc():
    token_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

    yield Contract(token_address)


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    yield Contract(token_address)

@pytest.fixture
def cow_anywhere(CowAnywhere, deployer):
    cow_anywhere = deployer.deploy(CowAnywhere)

    yield cow_anywhere
