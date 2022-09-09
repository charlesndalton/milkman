# Milkman

<img src="https://i.imgur.com/SOwYtIJ.jpg" width=150>


[![Tests](https://github.com/charlesndalton/milkman/actions/workflows/test.yml/badge.svg)](https://github.com/charlesndalton/milkman/actions/workflows/test.yml/badge.svg)
[![License: LGPL-3.0](https://img.shields.io/github/license/charlesndalton/milkman)](https://img.shields.io/github/license/charlesndalton/milkman)


Allows smart contracts to use the CoW Protocol.

## How to use

Call `milkman.requestSwapExactTokensForTokens`, passing in the following parameters:
- `amountIn`: an amount of tokens to sell
- `fromToken`: ERC20 you're swapping out of
- `toToken`: ERC20 you're swapping into
- `to`: the intended receiver of the bought tokens
- `priceChecker`: the address of a price checker, or `address(0)` for none; explained below
- `priceCheckerData`: encoded data to pass to the price checker; explained below

After you submit a swap request, it should be picked up and completed within 1-2 minutes.

### Price checkers

Bots generate off-chain CoW orders for each swap request. Milkman needs to validate these off-chain orders before it signs them. To do so, it calls a price checker. 

Price checkers validate that the bot-supplied `minOut` approximates the true value of the tokens that a user is swapping. To do so, they can use a variety of sources, such as AMMs and oracles. 

For example, if Alice wanted to swap YFI -> DAI, she could pass in the Chainlink price checker. When a bot generates a CoW order and tries to get Milkman to sign it, it asks the price checker whether the bot-configured `minOut` is in line with the current value of YFI. In turn, this price checker would check the YFI/USD price feed, and calculate how much USD `amountIn` of YFI is worth. If this amount is close enough to `minOut`, it will declare the order valid and Milkman will sign it.

Many price checkers can exist, and new price checkers don't need to be whitelisted. The user simply passes a `IPriceChecker`-compatible contract into the `priceChecker` argument. Some price checkers may need extra data from the user (e.g., the Chainlink one needs the price feed(s) to use). This can be passed in `priceCheckerData` in a byte-encoded form.

## Developing new price checkers

To be valid, price checkers need to implement the following function:

```solidity
function checkPrice(
        uint256 _amountIn,
        address _fromToken,
        address _toToken,
        uint256 _minOut,
        bytes calldata _data
    ) external view returns (bool);
```

The process of building one is straightforward, and can be abbreviated by using the [Price Checker Library](./contracts/pricecheckers/PriceCheckerLib.sol). Examples can be found in the [pricecheckers](./contracts/pricecheckers) folder.