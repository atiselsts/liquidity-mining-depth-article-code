#!/usr/bin/env python

#
# Code for the Experimental Results: Part 1 of the article
#

import numpy as np
import matplotlib.pyplot as pl
from ing_theme_matplotlib import mpl_style
from common import *
from rng import generate_lognormal_numbers

pl.rcParams["savefig.dpi"] = 200

MIN_LIQUIDITY_EXPONENT_USD = 4
MAX_LIQUIDITY_EXPONENT_USD = 8

TESTED_PRICE_IMPACTS_PCT = [0.01, 0.1]

def plot_max_size():
    logliq = np.linspace(MIN_LIQUIDITY_EXPONENT_USD, MAX_LIQUIDITY_EXPONENT_USD, 100)
    liq = [10 ** u for u in logliq]
    pl.figure(figsize=(5, 3.5))
    for max_price_impact_pct in TESTED_PRICE_IMPACTS_PCT:
        pl.plot(liq, [swap_size_from_liquidity(u, max_price_impact_pct / 100) for u in liq],
                label=f"Requires price impact ≤{max_price_impact_pct:.2f}%")

    pl.xlabel('Liquidity, $')
    pl.ylabel('Max swap size, $')
    pl.legend()
    pl.yscale("log")
    pl.xscale("log")
    pl.savefig("1_impact_and_max_size.png", bbox_inches='tight')
    pl.close()



def get_volume(swap_sizes, max_size):
    return np.sum(swap_sizes[swap_sizes < max_size])

def get_num_tx(swap_sizes, max_size):
    return np.sum(swap_sizes < max_size)


def plot_volume(swap_sizes):
    logliq = np.linspace(MIN_LIQUIDITY_EXPONENT_USD, MAX_LIQUIDITY_EXPONENT_USD, 100)
    liq = [10 ** u for u in logliq]
    pl.figure(figsize=(5, 3.5))
    for max_price_impact_pct in TESTED_PRICE_IMPACTS_PCT:
        max_size = [swap_size_from_liquidity(u, max_price_impact_pct / 100) for u in liq]
        pl.plot(liq, [get_volume(swap_sizes, size) for size in max_size],
                label=f"Requires price impact ≤{max_price_impact_pct:.2f}%")

    pl.xlabel('Liquidity, $')
    pl.ylabel('Total non-arb swap volume, $')
    pl.legend()
    pl.yscale("log")
    pl.xscale("log")
    pl.savefig("1_impact_and_volume.png", bbox_inches='tight')
    pl.close()


def plot_num_tx(swap_sizes):
    total = len(swap_sizes)
    logliq = np.linspace(MIN_LIQUIDITY_EXPONENT_USD, MAX_LIQUIDITY_EXPONENT_USD, 100)
    liq = [10 ** u for u in logliq]
    pl.figure(figsize=(5, 3.5))
    for max_price_impact_pct in TESTED_PRICE_IMPACTS_PCT:
        max_size = [swap_size_from_liquidity(u, max_price_impact_pct / 100) for u in liq]
        num_tx = [get_num_tx(swap_sizes, size) for size in max_size]
        pl.plot(liq, [(1.0 - u / total) * 100 for u in num_tx],
                label=f"Requires price impact ≤{max_price_impact_pct:.2f}%")

    pl.xlabel('Liquidity, $')
    pl.ylabel('Transactions rejected, %')
    pl.legend()
    pl.xscale("log")
    pl.savefig("1_impact_and_num_tx.png", bbox_inches='tight')
    pl.close()


def main():
    np.random.seed(1234)
    mpl_style(False)
    # approximately a year worth of trading in a med-sized pool
    # ($700M volume in total, ~$2M average per day).
    # e.g. on Optimism the USDC/ETH 0,05% pool has $1.5 TVL (real, not virtual)
    # and ~$2B swap volume during the past year
    swap_sizes = generate_lognormal_numbers(size=1_000_000)
    print("total volume:", sum(swap_sizes) / 1e6, "M")
    plot_max_size()
    plot_volume(swap_sizes)
    plot_num_tx(swap_sizes)



if __name__ == '__main__':
    main()
    print("all done!")
