import main

# Chainlink
# UniV3
# Uniswap V2
# SushiSwap
# Curve

def get_price_checker_and_price_checker_data(token_from, token_to, amount_in, allowed_slippage):
    # first, create a list of POSSIBLE expected out checkers (e.g., Chainlink may not work for all)
