import numpy as np
import pandas as pd

class FundLiquidityEngine:
    def __init__(self, asset_names, shares_held, spot_prices, avg_daily_volumes):
        """
        Models a mutual fund or UCITS fund portfolio's underlying liquidity constraints.
        """
        self.assets = asset_names
        self.shares = np.array(shares_held)
        self.prices = np.array(spot_prices)
        self.adv = np.array(avg_daily_volumes) # Average Daily Volume (Shares)
        
        # Calculate Base Portfolio Metrics
        self.position_values = self.shares * self.prices
        self.total_aum = np.sum(self.position_values)
        self.weights = self.position_values / self.total_aum

    def simulate_redemption_run(self, redemption_pct=0.25, max_adv_participation=0.10, impact_parameter=0.0005):
        """
        Simulates meeting a massive redemption request using two distinct corporate actions.
        Returns the post-run portfolio structure and the transaction cost drag.
        """
        cash_needed = self.total_aum * redemption_pct
        
        # --- STRATEGY 1: PRO-RATA LIQUIDATION ---
        # We sell exactly redemption_pct of every single holding
        shares_to_sell_pr = self.shares * redemption_pct
        value_sold_pr = shares_to_sell_pr * self.prices
        
        # Days required to liquidate each asset under participation limits
        days_to_liquidate_pr = shares_to_sell_pr / (self.adv * max_adv_participation)
        
        # Market impact cost calculation (Slippage/Haircut model)
        # Higher percentage of ADV traded in a day = worse price execution
        adv_pct_per_day = (shares_to_sell_pr / np.maximum(1, np.ceil(days_to_liquidate_pr))) / self.adv
        price_haircut_pct = impact_parameter * (adv_pct_per_day ** 2)
        total_slippage_cost_pr = np.sum(value_sold_pr * price_haircut_pct)
        
        # --- STRATEGY 2: WATERFALL LIQUIDATION (Liquid Assets First) ---
        # Sort positions by liquidity density: ADV Dollar Volume / Position Value
        dollar_adv = self.adv * self.prices
        liquidity_score = dollar_adv / self.position_values
        sorted_indices = np.argsort(-liquidity_score) # Most liquid first
        
        cash_raised = 0.0
        total_slippage_cost_wf = 0.0
        shares_left_wf = self.shares.copy()
        
        for idx in sorted_indices:
            if cash_raised >= cash_needed:
                break
                
            cash_still_needed = cash_needed - cash_raised
            max_value_available = shares_left_wf[idx] * self.prices[idx]
            
            # Determine how much of this specific asset to liquidate
            value_to_liquidate = min(cash_still_needed, max_value_available)
            shares_liquidated = value_to_liquidate / self.prices[idx]
            
            # Calculate market impact for this specific asset chunk
            days_needed = shares_liquidated / (self.adv[idx] * max_adv_participation)
            chunk_adv_pct = (shares_liquidated / max(1, np.ceil(days_needed))) / self.adv[idx]
            haircut = impact_parameter * (chunk_adv_pct ** 2)
            
            total_slippage_cost_wf += value_to_liquidate * haircut
            cash_raised += value_to_liquidate
            shares_left_wf[idx] -= shares_liquidated

        return {
            "Total AUM": self.total_aum,
            "Cash Required": cash_needed,
            "Pro-Rata Slippage Loss": total_slippage_cost_pr,
            "Waterfall Slippage Loss": total_slippage_cost_wf,
            "Max Days to Liquidate (Pro-Rata)": np.max(days_to_liquidate_pr)
        }

# --- EXECUTE TEST CASE ---
if __name__ == "__main__":
    # Portfolio of 3 assets: 1 highly liquid, 1 medium, 1 highly illiquid small-cap
    assets = ["Liquid BlueChip", "MidCap Stock", "Illiquid SmallCap"]
    shares = [500000, 200000, 150000]
    prices = [150.0, 50.0, 20.0]
    volumes = [2000000, 300000, 15000] # Notice the tiny volume on SmallCap
    
    fund = FundLiquidityEngine(assets, shares, prices, volumes)
    results = fund.simulate_redemption_run(redemption_pct=0.30) # 30% Fund Run
    
    print(f"Initial Fund Assets Under Management: ${results['Total AUM']:,.2f}")
    print(f"Sudden Investor Redemption Shock (30%): ${results['Cash Required']:,.2f}")
    print("-" * 60)
    print(f"Pro-Rata Liquidation Transaction Cost:  ${results['Pro-Rata Slippage Loss']:,.2f}")
    print(f"Waterfall Liquidation Transaction Cost: ${results['Waterfall Slippage Loss']:,.2f}")
    print(f"Time required to exit illiquid pockets: {results['Max Days to Liquidate (Pro-Rata)']:.1f} Days")
