# Milkman

[![Tests](https://github.com/charlesndalton/milkman/actions/workflows/test.yml/badge.svg)](https://github.com/charlesndalton/milkman/actions/workflows/test.yml/badge.svg)
[![License: LGPL-3.0](https://img.shields.io/github/license/charlesndalton/milkman)](https://img.shields.io/github/license/charlesndalton/milkman)

Fulfills all of your smart contract's CoW needs. 🐮

A simple way for smart contracts to sell their tokens via the CoW Protocol, reaping
the benefits of MEV protection even when tx.origin is malicious (e.g., a liquidator
bot in a borrow/lend protocol).

## How to use

To swap via Milkman, call `milkman.requestSwapExactTokensForTokens`, passing in 
the following parameters:
- `amountIn`: an amount of tokens to sell
- `fromToken`: ERC20 you're swapping out of
- `toToken`: ERC20 you're swapping into
- `to`: the intended receiver of the bought tokens
- `priceChecker`: the address of a price checker, or `address(0)` for none; explained below
- `priceCheckerData`: encoded data to pass to the price checker; explained below

After you submit a swap request, it should be picked up and executed within 1-2 minutes.

See [docs/EXAMPLES](./docs/EXAMPLES.md) for examples.

### Price checkers

After token have been sent to Milkman, it functions like a 'conditional signer', only
releasing those tokens to CoW protocol under certain conditions. Anyone can generate
an off-chain order for an on-chain swap request, but Milkman will only sign off
on orders that pass its checks.

Many of these checks are baked into Milkman itself, such as ensuring that the
off-chain order is a sell order (not a buy order). However, an important one is
not: validating that the bot-supplied `minOut` approximates the true value of
the tokens that a user is swapping. Users who don't want to trust the CoW
off-chain system can use `price checkers`. Price checkers verify that a `minOut`
is in-line with some on-chain price feed. For example, one price checker could
verify that `minOut` is at least 90% of what they could get from selling the tokens
via SushiSwap.

The only requirement for a price checker is that it needs to be compatible with 
the `IPriceChecker` interface. Anyone can create a new one, and new ones don't 
need to be whitelisted. 

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

The process of building one is straightforward. Examples can be found in the [pricecheckers](./contracts/pricecheckers) folder.