from math import log, sqrt

# range for the plots
MIN_LIQUIDITY_EXPONENT_USD = 4
MAX_LIQUIDITY_EXPONENT_USD = 8

MIN_LIQUIDITY_USD = 10 ** MIN_LIQUIDITY_EXPONENT_USD
MAX_LIQUIDITY_USD = 10 ** MAX_LIQUIDITY_EXPONENT_USD

ETH_PRICE = 3000

# L = sqrt(xy)
# V = x * P + y

# V = 2 * L * sqrt(P)
def liquidity_to_value(liquidity):
    return 2 * liquidity * sqrt(ETH_PRICE)

# L = V / (2 * sqrt(P))
def value_to_liquidity(value):
    return value / (2 * sqrt(ETH_PRICE))

# I = size / (L * sqrt(P))
def price_impact_formula(swap_size, liquidity):
    return swap_size / (liquidity * sqrt(ETH_PRICE))

# size = I * L * sqrt(P)
def swap_size_from_liquidity(liquidity, max_price_impact):
    return max_price_impact * liquidity * sqrt(ETH_PRICE)


# As on Optimism
BLOCK_TIME_SEC = 2

# the volatility of the volatile asset's price per one year (90%: a typical altcoin rather than ETH)
ETH_VOLATILITY = 0.9

ETH_VOLATILITY_PER_SECOND = ETH_VOLATILITY / sqrt(365 * 24 * 60 * 60)

ETH_VOLATILITY_PER_BLOCK = ETH_VOLATILITY_PER_SECOND * sqrt(BLOCK_TIME_SEC)

SIMULATION_DURATION_SEC = 86400 * 10
SIMULATION_DURATION_BLOCKS = SIMULATION_DURATION_SEC // BLOCK_TIME_SEC

SIMULATION_DURATION_DAYS = SIMULATION_DURATION_SEC // 86400

NUM_SIMULATIONS = 40 # this is very small, but enough for recognizable patterns in the results

MAX_PRICE_IMPACT_PCT = 0.01

# this is the expected upper bound of the noise volume
EXPECTED_VOLUME_PER_DAY = 1e6

# always 2 million
OTHER_DEX_LIQUDITY_USD = 2e6
