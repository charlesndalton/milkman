import requests
import brownie
from brownie import accounts, Contract, ZERO_ADDRESS, Milkman, network
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
    # if you want to run this on your own, you need to have a brownie account with the same name
    account = accounts.load("goerli-tester")
    network.disconnect()
    network.connect('goerli')

    milkman = Milkman.deploy({"from": account}, publish_source=True)

    print(f"Deployed Milkman address: {milkman}")