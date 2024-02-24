## Price Checker Internals

Price checking can be split into two stages: one to determine an 'expected out' 
and another to determine how far away the minOut can be from that expected out.
For example, for a TOKE -> WETH swap, we could determine the expected out by 
calling getAmountsOut on the TOKE/WETH SushiSwap pool and then fulfill the second
stage by only returning true if minOut is at least 90% of what getAmountsOut returned.

To make things modular, we split these two steps across contracts: a slippage
checker and an expected out calculator (creative names, amirite?). The slippage
checker implements the IPriceChecker interface and calls the expected out calculator. 
This allows the two to independently vary. In other words, you can write your 
own expected out calculator (e.g., for UniV4) without needing to write any 
slippage checking logic.

Of course, if you write your own price checker, you don't need to conform to this
pattern. If you wanted, you could have a monolithic price checker or even split
price checkers into more contracts.
