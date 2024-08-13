# Code for AMM simulations: liquidity depth vs revenue and PnL

This repository contains Python code for AMM revenue and PnL simulations as function of liquidity depth.

This model includes both arbitragers and other ("uninformed") swappers.

Overall, this aims to model the performance of the short-tail or blue-chip altcoin-to-stable
pools on L2 and alt-L1 chains, rather than on Eth mainnet, mirroring the conditions
where most liquidity mining campaigns are carried out.

# Assumptions

About the uninformed participants, the models assumes:

* Real demands from participants of swap volume up to ~$1M per day.
* Price-impact-sensitive swappers: up to 0.01% max price impact per swap.
  Swaps that go beyond this level of price impact are rejected.
* Log-normally distributed swap sizes from these actors.

About the AMM, it assumes:

* A DEX with liquidity depth from $10k to $500M.
  For Uniswap v3 the modeled number is most closely approximated by the *virtual* liquidity depth,
  i.e. the real amount of $ in the pool multiplied by the liquidity concentration factor.
  For Uniswap v2 it directly matches the `balanceOf` the assets in the pool.
* The DEX has a `xy=k` pool with a stable / volatile asset pair.
* The annual volatility of the volatile asset is set to 90%.
  This matches the performance of ETH is a volatile period, or a less stable altcoin in general.
* The gas fee for swaps is constant and small (0.1$) and does not depend on the price action.
* The liquidity provider fees are not compounding.
* Block time is set to 2 seconds (as in Optimism)

It also makes the standard assumptions behind the LVR model:

* There is a CEX which trades the volatile asset.
* The traders are not required to pay any trading fees on the CEX.
* The liquidity on the CEX is infinitely deep.
* There is a CEX/DEX arbitrager that has unlimited amount of stable assets, fast connections
  to both CEX and DEX, and will take all profitable trades at their maximum volume.


# Contents

- `common.py`: main configuration constants
- `dex.py`: a standard DEX model, low-level swap function
- `simulation.py`: higher-level simulation function
- `1_volume_from_liquidity.py`: code for plots in the experimental section #1 in the article
- `2_revenue_and_costs.py`: same for section #2 in the article
- `3_competing_pools.py`: same for section #3 in the article
