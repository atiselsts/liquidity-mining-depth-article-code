#!/usr/bin/env python

#
# Code for the Experimental Results: Part 3 of the article
#

import matplotlib.pyplot as pl
import numpy as np
from ing_theme_matplotlib import mpl_style
from dex import DEX, POOL_FEE_PIPS
from common import *
from simulation import get_price_paths, estimate_performance, estimate_performance_twopools, generate_trades, OTHER_DEX_LIQUDITY_USD

# Constants for plotting
pl.rcParams["savefig.dpi"] = 200

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
            lvr, lp_fees, lp_fees_arb, volume, volume_arb, _ = \
                estimate_performance_twopools(prices, generate_trades(), liquidity_usd)
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
        pl.ylim(0, 250000)
        pl.savefig(f"3_competing_revenue_{int(liquidity_usd)}.png", bbox_inches='tight')
        pl.close()


############################################################

def plot_pnl_vs_liquidity(all_prices):
    fig, ax = pl.subplots()
    fig.set_size_inches((5, 3.5))

    logliq = np.linspace(MIN_LIQUIDITY_EXPONENT_USD, MAX_LIQUIDITY_EXPONENT_USD - 0.5, 40)
    liq = [10 ** u for u in logliq]

    pnls_per_day_twopool = []
    pnls_per_day_singlepool = []

    market_shares = []

    apr_twopool = []
    apr_otherpool = []
    apr_singlepool = []

    for liquidity_usd in liq:
        print(liquidity_usd)
        lp_pnl_singlepool = []
        lp_pnl_twopool = []
        volumes_my = []
        volumes_other = []
        volumes_my_singlepool = []

        for sim in range(all_prices.shape[1]):
            prices = all_prices[:,sim]
            num_blocks = len(prices)
            trades = generate_trades()
            lvr, lp_fees, lp_fees_arb, volume, volume_arb, volume_other = \
                estimate_performance_twopools(prices, trades, liquidity_usd)

            volumes_my.append(volume)
            volumes_other.append(volume_other)

            lp_pnl = lp_fees - lvr
            lp_pnl_twopool.append(lp_pnl)

            lvr, lp_fees, lp_fees_arb, volume, volume_arb = \
                estimate_performance(prices, trades, liquidity_usd)

            lp_pnl = lp_fees - lvr
            lp_pnl_singlepool.append(lp_pnl)
            volumes_my_singlepool.append(volume)

        duration_days = num_blocks * BLOCK_TIME_SEC / 86400
        avg_volume_my = np.mean(volumes_my)
        avg_volume_other = np.mean(volumes_other)
        avg_volume_my_singlepool = np.mean(volumes_my_singlepool)
        print("avg volumes:", avg_volume_my, avg_volume_other)

        pnl_per_day = np.mean(lp_pnl_singlepool) / duration_days
        pnls_per_day_singlepool.append(pnl_per_day)

        pnl_per_day = np.mean(lp_pnl_twopool) / duration_days
        pnls_per_day_twopool.append(pnl_per_day)

        market_shares.append(100 * avg_volume_my / (avg_volume_my + avg_volume_other))

        fees_my = avg_volume_my * POOL_FEE_PIPS / 1e6
        fees_otherpool = avg_volume_other * POOL_FEE_PIPS / 1e6
        fees_singlepool = avg_volume_my_singlepool * POOL_FEE_PIPS / 1e6

        apr_twopool.append(100 * 365 / duration_days * fees_my / liquidity_usd)
        apr_otherpool.append(100 * 365 / duration_days * fees_otherpool / OTHER_DEX_LIQUDITY_USD)
        apr_singlepool.append(100 * 365 / duration_days * fees_singlepool / liquidity_usd)

        print("   APR:", apr_twopool[-1], apr_otherpool[-1])
  

    pl.plot(liq, pnls_per_day_singlepool, color="green", label="100% market share")
    pl.plot(liq, pnls_per_day_twopool, color="red", label="Competitive market")

    # plot the line y=0 (separates profit/loss)
    pl.axhline(y=0, color='black', linestyle='-')

    pl.xlabel("Liquidity, $")
    pl.ylabel("LP profit per day, $")
    pl.xscale("log")
    pl.legend()
    pl.ylim(-1000, 1000)
    pl.savefig(f"3_competing_pnl.png", bbox_inches='tight')
    pl.close()


    fig, ax = pl.subplots()
    fig.set_size_inches((5, 3.5))
    pl.plot(liq, market_shares)
    pl.xlabel("Liquidity, $")
    pl.ylabel("Market share, %")
    pl.xscale("log")

    pl.savefig(f"3_competing_marketshare.png", bbox_inches='tight')
    pl.close()


    fig, ax = pl.subplots()
    fig.set_size_inches((5, 3.5))
    pl.plot(liq, apr_singlepool, color="green", label="100% market share")
    pl.plot(liq, apr_twopool, color="red", label="Competitive market")
    pl.plot(liq, apr_otherpool, color="brown", label="Alternative DEX in a competitive market")

    pl.xlabel("Liquidity, $")
    pl.ylabel("APR, %")
    pl.xscale("log")
    pl.legend()
    pl.ylim(ymin=0)
    pl.savefig(f"3_competing_apr.png", bbox_inches='tight')
    pl.close()


############################################################x
    
def main():
    mpl_style(False)
    np.random.seed(123456)
    n = SIMULATION_DURATION_BLOCKS
    all_prices = get_price_paths(n, sigma=ETH_VOLATILITY_PER_BLOCK, mu=0.0)
    plot_performance_both(all_prices)
    plot_pnl_vs_liquidity(all_prices)


if __name__ == '__main__':
    main()
    print("all done!")
