#!/usr/bin/env python

#
# Code for the Experimental Results: Part 2 of the article
#

import matplotlib.pyplot as pl
import numpy as np
from ing_theme_matplotlib import mpl_style
from dex import DEX, POOL_FEE_PIPS
from common import *
from simulation import get_price_paths, estimate_performance, generate_trades
# Constants for plotting
pl.rcParams["savefig.dpi"] = 200

############################################################

# this is from the paper, but does not give accurate results
def lvr_with_fees_formula():
    sigma_per_block = ETH_VOLATILITY_PER_BLOCK
    block_time = BLOCK_TIME_SEC
    gamma = POOL_FEE_PIPS / 1e6
    blocks_per_day = 86400 / block_time
    result_per_block = (sigma_per_block ** 3) * sqrt(block_time / 2) / (8 * gamma)
    return result_per_block * blocks_per_day

############################################################

def plot_performance_arb_only(all_prices):
    fig, ax = pl.subplots()
    fig.set_size_inches((5, 3.5))

    for liquidity_usd in [5e6, 1e7]:
        print("liquidity_usd=", liquidity_usd / 1e6, "M")

        all_volume = []
        all_lp_pnl = []

        for sim in range(all_prices.shape[1]):
            prices = all_prices[:,sim]
            num_blocks = len(prices)
            lvr, lp_fees, lp_fees_arb, volume, volume_arb = \
                estimate_performance(prices, None, liquidity_usd)
            all_volume.append(volume)
            lp_pnl = lp_fees - lvr
            all_lp_pnl.append(lp_pnl)

        duration_days = num_blocks * BLOCK_TIME_SEC / 86400
        avg_total_pnl = sum(all_lp_pnl) / NUM_SIMULATIONS

        pnl_per_day_analytical = -lvr_with_fees_formula()
        pnl_per_day_analytical *= liquidity_usd
        
        pnl_per_day = avg_total_pnl / duration_days

        x = range(int(10 * duration_days))
        #pl.plot(x, [u * pnl_per_day_analytical for u in x], label=f"Liquidity=${liquidity_usd/1e6:.0f}M, analytical", linestyle="-")
        pl.plot(x, [u * pnl_per_day for u in x], label=f"Liquidity=${liquidity_usd/1e6:.0f}M")


    pl.xlabel("Days")
    pl.ylabel("LP profit, $")
    pl.legend()

    pl.savefig(f"2_pnl_arbonly.png", bbox_inches='tight')

############################################################

def plot_performance_both(all_prices):
    for liquidity_usd in [1e6, 1e7]:

        all_lp_fees = []
        all_lp_fees_arb = []

        fig, ax = pl.subplots()
        fig.set_size_inches((5, 3.5))

        for sim in range(all_prices.shape[1]):
            prices = all_prices[:,sim]
            num_blocks = len(prices)
            lvr, lp_fees, lp_fees_arb, volume, volume_arb = \
                estimate_performance(prices, generate_trades(), liquidity_usd)
            all_lp_fees.append(lp_fees)
            all_lp_fees_arb.append(lp_fees_arb)

        duration_days = num_blocks * BLOCK_TIME_SEC / 86400

        revenue_per_day = np.mean(all_lp_fees) / duration_days
        revenue_per_day_arb = np.mean(all_lp_fees_arb) / duration_days
        revenue_per_day_other = revenue_per_day - revenue_per_day_arb

        x = range(int(10 * duration_days))
        pl.plot(x, [u * revenue_per_day for u in x], label="Total revenue", color="black")
        pl.plot(x, [u * revenue_per_day_arb for u in x], label="Toxic arbitrage revenue", linestyle="--", color="red")
        pl.plot(x, [u * revenue_per_day_other for u in x], label="Other revenue", linestyle="--", color="green")

        pl.xlabel("Days")
        pl.ylabel("LP revenue, $")
        pl.legend()
        pl.ylim(0, 300_000)
        pl.savefig(f"2_revenue_L_{int(liquidity_usd)}.png", bbox_inches='tight')
        pl.close()


############################################################

def plot_pnl_vs_liquidity(all_prices):
    fig, ax = pl.subplots()
    fig.set_size_inches((5, 3.5))

    logliq = np.linspace(MIN_LIQUIDITY_EXPONENT_USD, MAX_LIQUIDITY_EXPONENT_USD - 0.5, 40)
    liq = [10 ** u for u in logliq]

    pnls_per_day = []

    for liquidity_usd in liq:
        print(liquidity_usd)
        all_lp_pnl = []

        for sim in range(all_prices.shape[1]):
            prices = all_prices[:,sim]
            num_blocks = len(prices)
            lvr, lp_fees, lp_fees_arb, volume, volume_arb = \
                estimate_performance(prices, generate_trades(), liquidity_usd)

            lp_pnl = lp_fees - lvr
            all_lp_pnl.append(lp_pnl)

        duration_days = num_blocks * BLOCK_TIME_SEC / 86400
        avg_total_pnl = sum(all_lp_pnl) / NUM_SIMULATIONS

        pnl_per_day = avg_total_pnl / duration_days
        pnls_per_day.append(pnl_per_day)

    pl.plot(liq, pnls_per_day)
    pl.axhline(y=0, color='black', linestyle='-')

    ax.fill_between(liq, 0, [max(u, 0) for u in pnls_per_day], color="darkgreen")
    ax.fill_between(liq, 0, [min(u, 0) for u in pnls_per_day], color="red")

    pl.xlabel("Liquidity, $")
    pl.ylabel("LP profit per day, $")
    pl.xscale("log")
    pl.ylim(-2000, 1000)

    pl.savefig(f"2_pnl_both.png", bbox_inches='tight')

############################################################
 
def main():
    mpl_style(False)
    np.random.seed(123456)
    n = SIMULATION_DURATION_BLOCKS
    all_prices = get_price_paths(n, sigma=ETH_VOLATILITY_PER_BLOCK, mu=0.0)
    plot_performance_arb_only(all_prices)
    plot_performance_both(all_prices)
    plot_pnl_vs_liquidity(all_prices)


if __name__ == '__main__':
    main()
    print("all done!")
