## Open-End Mutual Fund Liquidity Haircut and Redemption Stress Test Model

An institutional portfolio risk engine designed to model capital asset depletion, trading volume degradation, and non-linear market-impact costs (slippage) under severe investor liquidation stress. This framework simulates multi-day fund runs on open-end investment portfolios (such as UCITS or mutual funds) and evaluates the structural mechanics of **Anti-Dilution Swing Pricing** to insulate remaining investor assets from capital dilution.

The system is configured to identify the structural limits of distinct liquidation rules—contrasting pro-rata slicing mechanisms against liquidity-waterfall strategies and is bound within an interactive Streamlit visual deployment interface.

## Core Features

*   **Stochastic Fund Run Simulation**: Models unexpected, multi-day investor redemption waves as an aggressive percentage draw against total Assets Under Management (AUM).
*   **Liquidation Strategy Prototyping**: Contrasts uniform Pro-Rata portfolio rebalancing against Liquidity-Waterfall routines (liquidating high average-daily-volume Blue-Chips first).
*   **Non-Linear Microstructure Slippage**: Implements a square-root/quadratic execution price haircut model that penalizes trade execution velocity based on the fund's participation rate relative to historical Average Daily Volume (ADV).
*   **Anti-Dilution Swing Pricing Module**: Dynamically computes daily portfolio swing thresholds to calculate adjusted, counter-cyclical NAV write-downs.
*   **First-Mover Advantage Neutralization**: Provides a game-theoretic framework to strip out the structural mathematical edge that incentivizes panicking investors to redeem capital early at the expense of long-term holders.
