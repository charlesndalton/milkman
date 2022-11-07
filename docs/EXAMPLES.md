# Examples

These examples will be Python-based and use [ape-safe](https://github.com/banteg/ape-safe).

#### Example #1 – TOKE -> DAI swap, Sushiswap price checker with fixed 5% slippage allowance

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

DUMMY_BYTES = encode_abi(["uint8"], [int(0)])

safe = ApeSafe('ychad.eth')
toke = safe.contract('0x2e9d63788249371f1DFC918a52f8d799F4a38C94')
dai = safe.contract('0x6B175474E89094C44Da98b954EedeAC495271d0F')
toke_to_sell = int(400 * 1e18) # 400 TOKE
milkman = safe.contract('0xdeadbeef') # placeholders, will replace once we have audited Milkman in prod
sushiswap_price_checker = safe.contract('0x123456789') # Sushiswap price checker that allows up to 5% price discrepency
price_checker_data = DUMMY_BYTES # SushiSwap price checker doesn't need data

milkman.requestSwapExactTokensForTokens(
    toke_to_sell,
    toke,
    dai,
    sushiswap_price_checker,
    price_checker_data,
)
```

#### Example #2 – TOKE -> DAI swap, Sushiswap price checker with user-set 6% slippage allowance

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

DUMMY_BYTES = encode_abi(["uint8"], [int(0)])

safe = ApeSafe('ychad.eth')
toke = safe.contract('0x2e9d63788249371f1DFC918a52f8d799F4a38C94')
dai = safe.contract('0x6B175474E89094C44Da98b954EedeAC495271d0F')
toke_to_sell = int(400 * 1e18) # 400 TOKE
milkman = safe.contract('0xdeadbeef') 
sushiswap_price_checker = safe.contract('0x987654321') # SushiSwap price checker with dynamic slippage checking, based on price_checker_data

# dynamic slippage price checkers intake data of the form [uint256, bytes],
# where the uint is the allowed slippage in bps and the bytes are any other
# data that should be passed to the underlying expected out calculator.
# in this case, the expected out calculator is UniV2, which doesn't need anything
price_checker_data = encode_abi(["uint256", "bytes"], [int(600), DUMMY_BYTES]) # allow 6% slippage

milkman.requestSwapExactTokensForTokens(
    toke_to_sell,
    toke,
    dai,
    sushiswap_price_checker,
    price_checker_data,
)
```

#### Example #3 – USDC -> USDT, Curve price checker with fixed slippage allowance

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

DUMMY_BYTES = encode_abi(["uint8"], [int(0)])

safe = ApeSafe('ychad.eth')
usdc = safe.contract('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')
usdt = safe.contract('0xdAC17F958D2ee523a2206206994597C13D831ec7')
usdc_to_sell = int(5_000_000 * 1e6) # $5M USDC
milkman = safe.contract('0xdeadbeef') 
curve_price_checker = safe.contract('0xfeefa') 
price_checker_data = DUMMY_BYTES # Curve price checker doesn't need data

milkman.requestSwapExactTokensForTokens(
    usdc_to_sell,
    usdc,
    usdt,
    curve_price_checker,
    price_checker_data,
)
```

#### Example #4 – AAVE -> WETH, Chainlink price checker with fixed slippage allowance

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

safe = ApeSafe('ychad.eth')
aave = safe.contract('0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9')
weth = safe.contract('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
aave_to_sell = int(10 * 1e18)
milkman = safe.contract('0xdeadbeef') 

# chainlink price checker accepts data of form [address[], bool[]], where the 
# addresses are chainlink price feeds and the bool tells the price checker whether
# or not to reverse those feeds. This is an AAVE/WETH feed, so we don't need to
# reverse it. If it were a WETH/AAVE feed, we would need to.
chainlink_price_checker = safe.contract('0x1337') 
aave_weth_chainlink_feed = '0x6Df09E975c830ECae5bd4eD9d90f3A95a4f88012'
price_checker_data = encode_abi(
    ["address[]", "bool[]"],
    [[aave_weth_chainlink_feed], [False]],
),

milkman.requestSwapExactTokensForTokens(
    aave_to_sell,
    aave,
    weth,
    chainlink_price_checker,
    price_checker_data,
)
```

#### Example #5 – BAT -> ALCX, Chainlink price checker with dynamic slippage allowance

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

safe = ApeSafe('ychad.eth')
bat = safe.contract('0x0D8775F648430679A709E98d2b0Cb6250d2887EF')
alcx = safe.contract('0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF')
bat_to_sell = int(1_000_000 * 1e18)
milkman = safe.contract('0xdeadbeef') 

chainlink_price_checker_dynamic_slippage = safe.contract('0x101010') 
bat_weth_chainlink_feed = '0x0d16d4528239e9ee52fa531af613acdb23d88c94'
alcx_weth_chainlink_feed = '0x194a9aaf2e0b67c35915cd01101585a33fe25caa'
expected_out_calculator_data = encode_abi(
    ["address[]", "bool[]"],
    [[bat_weth_chainlink_feed, alcx_weth_chainlink_feed], [False, True]],
),
price_checker_data = encode_abi(
    ["uint256", "bytes"],
    [int(1000), expected_out_calculator_data] # 10% slippage
)

milkman.requestSwapExactTokensForTokens(
    bat_to_sell,
    bat,
    alcx,
    chainlink_price_checker_dynamic_slippage,
    price_checker_data,
)
```

#### Example #6 – WETH -> WBTC, UniV3 as the price checker with fixed slippage

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

safe = ApeSafe('ychad.eth')
weth = safe.contract('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
wbtc = safe.contract('0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599')
weth_to_sell = int(100 * 1e18)
milkman = safe.contract('0xdeadbeef') 

univ3_price_checker = safe.contract('0x101010') 
price_checker_data = 
        encode_abi(
            ["address[]", "uint24[]"],
            [weth.address, wbtc.address], [int(30)]],
        )

milkman.requestSwapExactTokensForTokens(
    weth_to_sell,
    weth,
    wbtc,
    univ3_price_checker,
    price_checker_data,
)
```

#### Example #7 (COMPLEX) – ALCX -> TOKE, Meta price checker using both Chainlink and Sushiswap price checkers 

```python
from eth_abi import encode_abi
from ape_safe import ApeSafe

DUMMY_BYTES = encode_abi(["uint8"], [int(0)])

safe = ApeSafe('ychad.eth')
alcx = safe.contract('0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF')
toke = safe.contract('0x2e9d63788249371f1DFC918a52f8d799F4a38C94')
weth = safe.contract('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
alcx_to_sell = int(100 * 1e18)
milkman = safe.contract('0xdeadbeef') 

sushiswap_price_checker = safe.contract('0x123456789') 
chainlink_price_checker = safe.contract('0x1337') 
meta_price_checker = safe.contract('0xabcdef')
# meta price checker data is encoded as [address[], address[], and bytes[]], where
# the first address[] is the desired swap path, the second address[] are the
# expected out calculators to use, and the bytes[] is the data to pass into each
# expected out checker
alcx_weth_price_feed = '0x194a9aaf2e0b67c35915cd01101585a33fe25caa'
chainlink_data = encode_abi(
    ["address[]", "bool[]"],
    [[alcx_weth_price_feed], [False]]
)
sushiswap_data = DUMMY_BYTES
price_checker_data = encode_abi(
    ["address[]", "address[]", "bytes[]"],
    [
        [
            alcx.address, # ALCX -> WETH -> TOKE
            weth.address,
            toke.address,
        ],
        [
            chainlink_price_checker.EXPECTED_OUT_CALCULATOR(),
            sushiswap_price_checker.EXPECTED_OUT_CALCULATOR(),
        ],
        [
            chainlink_data,
            sushiswap_data,
        ]
    ]
)

milkman.requestSwapExactTokensForTokens(
    alcx_to_sell,
    alcx,
    toke,
    meta_price_checker,
    price_checker_data,
)
```




