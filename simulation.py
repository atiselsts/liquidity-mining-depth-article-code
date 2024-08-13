import numpy as np
from dex import DEX
from common import *
from rng import generate_lognormal_numbers, approximate_mean

############################################################

def get_price_paths(n, sigma, mu, M=NUM_SIMULATIONS):
    St = np.exp((mu - sigma ** 2 / 2) + sigma * np.random.normal(0, 1, size=(M, n-1)).T)

    # we want the initial prices to be randomly distributed in the pool's non-arbitrage space
    price_low, price_high = DEX().get_non_arbitrage_region()
    initial_prices = np.random.uniform(price_low / ETH_PRICE, price_high / ETH_PRICE, M)
    St = np.vstack([initial_prices, St])

    St = ETH_PRICE * St.cumprod(axis=0)
    return St

############################################################

def estimate_performance(prices, noise_trades=None, liquidity_usd=None):
    dex = DEX()
    if liquidity_usd is not None:
        dex.set_liquidity_usd(liquidity_usd)
    n = len(prices)
    if noise_trades is None:
        for p in prices:
            dex.maybe_arbitrage(p)
    else:
        noise_trades_per_block = len(noise_trades) / n
        #print("noise_trades_per_block=", noise_trades_per_block)
        max_swap = swap_size_from_liquidity(dex.liquidity_usd(), MAX_PRICE_IMPACT_PCT / 100)
        print("max swap=", max_swap)
        last_noise_trade = -1
        for i in range(n):
            # first execute the arbitrage (may include a backrun)
            cex_price = prices[i]
            dex.maybe_arbitrage(cex_price)
            # then execute the noise trades
            k = last_noise_trade + 1
            next_noise_trade = int(i * noise_trades_per_block)
            while k <= next_noise_trade:
                trade_amount = noise_trades[k]
                if abs(trade_amount) <= max_swap:
                    if trade_amount < 0:
                        trade_amount = -trade_amount / cex_price
                        dex.swap_x_to_y(trade_amount)
                    elif trade_amount > 0:
                        dex.swap_y_to_x(trade_amount)
                k += 1
            last_noise_trade = next_noise_trade
            # check if backrun can be done in the same block
            dex.maybe_arbitrage(cex_price, account_lvr=False)

    return dex.lvr, dex.lp_fees, dex.lp_fees_arb, dex.volume, dex.volume_arb

############################################################

#
# Note: instead of implementing the full & exact routing with gas,
#   here I use a simpler approach that:
#   1) for small swaps, simply routes through the best pool alone
#   2) for larger swaps, split them by liquidity, after equalizing the price
#
SMALL_SWAP_SIZE_USD = 10.0

def route_swap_x_to_y(trade_amount_x, dex_my, dex_other):
    price = dex_my.price()
    if trade_amount_x * price <= SMALL_SWAP_SIZE_USD:
        return route_swap_x_to_y_single_tx(trade_amount_x, dex_my, dex_other)

    # first, swap sufficient amount of x to equalize the price between the pools
    sp1 = sqrt(price)
    sp2 = sqrt(dex_other.price())
    if abs(sp1 - sp2) < 1e-8:
        # both prices are almost equal, do not bother (avoid numerical errors)
        delta_x = 0
        swap_step_amount = 0
    elif sp1 < sp2:
        # there are more X in dex_my than dex_other; add X to the other DEX
        delta_x = dex_other.get_x_amount_to_target_price(sp1)
        swap_step_amount = min(trade_amount_x, delta_x)
        dex_other.swap_x_to_y(swap_step_amount)
    else:
        delta_x = dex_my.get_x_amount_to_target_price(sp2)
        swap_step_amount = min(trade_amount_x, delta_x)
        dex_my.swap_x_to_y(swap_step_amount)

    assert delta_x >= 0

    trade_amount_x -= swap_step_amount
    if trade_amount_x > 0:
        # then, if necessary, divide the remaining swap amounts
        # proportional to the liquidity in the pools
        liq_my = dex_my.liquidity()
        liq_other = dex_other.liquidity()
        prop_my = liq_my / (liq_my + liq_other)
        swap_step_amount_my = trade_amount_x * prop_my
        swap_step_amount_other = trade_amount_x - swap_step_amount_my
        dex_my.swap_x_to_y(swap_step_amount_my)
        dex_other.swap_x_to_y(swap_step_amount_other)

############################################################

def route_swap_y_to_x(trade_amount_y, dex_my, dex_other):
    if trade_amount_y <= SMALL_SWAP_SIZE_USD:
        return route_swap_y_to_x_single_tx(trade_amount_y, dex_my, dex_other)

    sp1 = sqrt(dex_my.price())
    sp2 = sqrt(dex_other.price())

    # First, swap sufficient amount of Y to equalize the price between the pools
    if abs(sp1 - sp2) < 1e-8:
        # Both prices are almost equal, do not bother (avoid numerical errors)
        delta_y = 0
        swap_step_amount = 0
    elif sp1 < sp2:
        # There are more X in dex_my than dex_other; remove Y from the other DEX
        delta_y = dex_my.get_y_amount_to_target_price(sp2)
        swap_step_amount = min(trade_amount_y, delta_y)
        dex_my.swap_y_to_x(swap_step_amount)
    else:
        delta_y = dex_other.get_y_amount_to_target_price(sp1)
        swap_step_amount = min(trade_amount_y, delta_y)
        dex_other.swap_y_to_x(swap_step_amount)

    assert delta_y >= 0

    trade_amount_y -= swap_step_amount
    if trade_amount_y > 0:
        # Then, if necessary, divide the remaining swap amounts
        # proportional to the liquidity in the pools
        liq_my = dex_my.liquidity()
        liq_other = dex_other.liquidity()
        prop_my = liq_my / (liq_my + liq_other)
        swap_step_amount_my = trade_amount_y * prop_my
        swap_step_amount_other = trade_amount_y - swap_step_amount_my
        dex_my.swap_y_to_x(swap_step_amount_my)
        dex_other.swap_y_to_x(swap_step_amount_other)

############################################################

def route_swap_x_to_y_single_tx(trade_amount_x, dex_my, dex_other):
    amount_my = dex_my.get_output_x_to_y(trade_amount_x)
    amount_other = dex_other.get_output_x_to_y(trade_amount_x)
    if amount_my >= amount_other:
        dex_my.swap_x_to_y(trade_amount_x)
    else:
        dex_other.swap_x_to_y(trade_amount_x)

############################################################

def route_swap_y_to_x_single_tx(trade_amount_y, dex_my, dex_other):
    amount_my = dex_my.get_output_y_to_x(trade_amount_y)
    amount_other = dex_other.get_output_y_to_x(trade_amount_y)
    if amount_my >= amount_other:
        dex_my.swap_y_to_x(trade_amount_y)
    else:
        dex_other.swap_y_to_x(trade_amount_y)

############################################################

def estimate_performance_twopools(prices, noise_trades, liquidity_usd):
    dex_my = DEX()
    dex_other = DEX()
    dex_my.set_liquidity_usd(liquidity_usd)
    dex_other.set_liquidity_usd(OTHER_DEX_LIQUDITY_USD)
    n = len(prices)

    noise_trades_per_block = len(noise_trades) / n
    max_swap_my = swap_size_from_liquidity(dex_my.liquidity_usd(), MAX_PRICE_IMPACT_PCT / 100)
    max_swap_other = swap_size_from_liquidity(dex_other.liquidity_usd(), MAX_PRICE_IMPACT_PCT / 100)
    max_swap_both = swap_size_from_liquidity(
        dex_my.liquidity_usd() + dex_other.liquidity_usd(), MAX_PRICE_IMPACT_PCT / 100)
    #print("max swap=", max_swap_my, max_swap_other, max_swap_both)

    last_noise_trade = -1
    for i in range(n):
        # first execute the arbitrage (may include a backrun)
        cex_price = prices[i]
        dex_my.maybe_arbitrage(cex_price)
        dex_other.maybe_arbitrage(cex_price)
        # then execute the noise trades
        k = last_noise_trade + 1
        next_noise_trade = int(i * noise_trades_per_block)
        while k <= next_noise_trade:
            trade_amount = noise_trades[k]

            # as a quick approximation of the price impact, use L_cumulative = L1 + L2 for the filter
            # XXX: this is not 100% correct, because not all swaps are shared by both DEX!
            if abs(trade_amount) <= max_swap_both:
                if trade_amount < 0:
                    trade_amount_x = -trade_amount / cex_price
                    route_swap_x_to_y(trade_amount_x, dex_my, dex_other)
                else:
                    trade_amount_y = trade_amount
                    route_swap_y_to_x(trade_amount_y, dex_my, dex_other)

            k += 1
        last_noise_trade = next_noise_trade
        # check if backrun can be done in the same block
        dex_my.maybe_arbitrage(cex_price, account_lvr=False)
        dex_other.maybe_arbitrage(cex_price, account_lvr=False)

    return dex_my.lvr, dex_my.lp_fees, dex_my.lp_fees_arb, dex_my.volume, dex_my.volume_arb, dex_other.volume

############################################################

# this is normalized to generate ~1M volume per day
def generate_trades():
    swap_sizes = generate_lognormal_numbers(size=int(EXPECTED_VOLUME_PER_DAY * SIMULATION_DURATION_DAYS / approximate_mean()))

    #print("total volume per day=", sum(swap_sizes) / SIMULATION_DURATION_DAYS)
    #print("total fees per day  =", sum(swap_sizes) * 0.05 / 100 / SIMULATION_DURATION_DAYS)

    # make half the results negative (determines trade direction)
    n = len(swap_sizes)
    indices = np.random.permutation(n)
    num_to_invert = n // 2
    swap_sizes[indices[:num_to_invert]] *= -1
    return swap_sizes
