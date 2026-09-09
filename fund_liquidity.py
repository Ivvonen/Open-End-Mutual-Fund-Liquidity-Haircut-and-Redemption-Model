import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- 1. QUANTITATIVE FUND MODEL ---

class FundLiquidityEngine:
    def __init__(self, asset_names, shares_held, spot_prices, avg_daily_volumes):
        self.assets = asset_names
        self.shares = np.array(shares_held, dtype=float)
        self.prices = np.array(spot_prices, dtype=float)
        self.adv = np.array(avg_daily_volumes, dtype=float)
        
        self.position_values = self.shares * self.prices
        self.total_aum = np.sum(self.position_values)
        self.weights = self.position_values / self.total_aum

    def simulate_liquidation_run(self, redemption_pct, max_adv_participation, impact_parameter=0.0005):
        """
        Simulates meeting redemptions under dynamic slider limits.
        """
        cash_needed = self.total_aum * redemption_pct
        dollar_adv = self.adv * self.prices
        
        # Calculate liquidity scores (Volume / Position Size)
        liquidity_score = dollar_adv / self.position_values
        sorted_indices = np.argsort(-liquidity_score) # Most liquid first
        
        cash_raised = 0.0
        total_slippage_cost = 0.0
        shares_left = self.shares.copy()
        
        for idx in sorted_indices:
            if cash_raised >= cash_needed:
                break
                
            cash_still_needed = cash_needed - cash_raised
            max_value_available = shares_left[idx] * self.prices[idx]
            
            value_to_liquidate = min(cash_still_needed, max_value_available)
            shares_liquidated = value_to_liquidate / self.prices[idx]

            
            # Bound the maximum dollar volume we are legally allowed to trade per day
            max_daily_dollar_volume = dollar_adv[idx] * max_adv_participation
            
            # Calculate execution days required under the slider constraint
            days_needed = max(1.0, np.ceil(value_to_liquidate / max(1.0, max_daily_dollar_volume)))
            
            # Decompose the execution footprint into daily chunks
            daily_shares_liquidated = shares_liquidated / days_needed
            chunk_adv_pct = daily_shares_liquidated / self.adv[idx]
            
            # Calculate market impact haircut
            haircut = impact_parameter * (chunk_adv_pct ** 2)
            total_slippage_cost += (value_to_liquidate * haircut)
            
            cash_raised += value_to_liquidate
            shares_left[idx] -= shares_liquidated

        post_values = shares_left * self.prices
        return total_slippage_cost, post_values

# --- 2. STREAMLIT INTERFACE & SLIDER ---

st.set_page_config(page_title="Fund Liquidity Risk Engine", layout="wide")
st.title("Asset Management Liquidity Risk & Swing Pricing Simulator")
st.markdown("Model fund run behaviors, asset liquidation horizons, and calculate anti-dilution swing adjustments.")

st.sidebar.header("⚙️ Fund Capital Controls")

# ALL SLIDER VARIABLE NAME KEYS DECLARED HERE
redemption_slider = st.sidebar.slider("Investor Redemption Shock (% of AUM)", 5, 60, 25) / 100
participation_limit = st.sidebar.slider("Max Daily Volume Participation Limit (% ADV)", 1, 25, 10) / 100
slippage_severity = st.sidebar.slider("Market Impact Severity Factor", 0.0001, 0.0020, 0.0005, step=0.0001, format="%.4f")
enable_swing_pricing = st.sidebar.checkbox("Deploy Anti-Dilution Swing Factor", value=True)

# Define Base Portfolio
assets = ["Liquid BlueChip", "MidCap Stock", "Illiquid SmallCap"]
base_shares = [100000, 200000, 500000]
base_prices = [150.0, 50.0, 20.0]
base_volumes = [1000000, 200000, 15000] # Thin float on small-cap

# Instantiate Engine
engine = FundLiquidityEngine(assets, base_shares, base_prices, base_volumes)

# --- CRITICAL FIX: SLIDERS EXPLICITLY PASSED INTO CODE EXECUTION HERE ---
total_slippage, post_position_values = engine.simulate_liquidation_run(
    redemption_pct=redemption_slider, 
    max_adv_participation=participation_limit, 
    impact_parameter=slippage_severity
)

# --- 3. METRIC RECONCILIATIONS ---
base_nav_per_share = 100.0
total_fund_shares = engine.total_aum / base_nav_per_share
slippage_per_share = total_slippage / total_fund_shares
swing_factor_pct = (total_slippage / engine.total_aum) * 100

swung_nav = base_nav_per_share - slippage_per_share if enable_swing_pricing else base_nav_per_share
unprotected_remaining_nav = base_nav_per_share - (slippage_per_share * (1 / max(0.01, 1 - redemption_slider)))

# KPI Layout Blocks
c1, c2, c3, c4 = st.columns(4)
c1.metric("Initial Portfolio AUM", f"${engine.total_aum:,.2f}")
c2.metric("Redemption Capital Drain", f"${(engine.total_aum * redemption_slider):,.2f}")
c3.metric("Total Market Impact Cost", f"${total_slippage:,.2f}")
c4.metric("Calculated Swing Factor", f"{swing_factor_pct:.4f}%")

st.markdown("---")
chart_col, matrix_col = st.columns(2)

with chart_col:
    st.subheader("Structural Asset Distortion (Before vs After Outflows)")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=assets, y=engine.weights * 100, name='Initial Structure Weight', marker_color='#1f77b4'))
    fig.add_trace(go.Bar(x=assets, y=(post_position_values / np.maximum(1, np.sum(post_position_values))) * 100, name='Post-Run Stressed Weight', marker_color='#ff7f0e'))
    
    fig.update_layout(barmode='group', xaxis_title="Asset Class Pool", yaxis_title="Portfolio Concentration (%)", margin=dict(l=20, r=20, t=20, b=20), height=350)
    st.plotly_chart(fig, use_container_width=True)

with matrix_col:
    st.subheader("Investor Impact Analytics")
    if enable_swing_pricing:
        st.info(f"🟢 **Swing Pricing Active**\n\nRedeeming investors exit at an adjusted NAV of **${swung_nav:,.2f}**, internalizing the liquidity impact costs.")
        st.success(f"**Remaining Investor NAV Protection:** **${base_nav_per_share:,.2f}** (0.0% dilution)")
    else:
        st.warning(f"🔴 **Swing Pricing Disabled**\n\nRedeeming investors exit at a full **${base_nav_per_share:,.2f}** NAV, leaving transaction costs behind.")
        st.error(f"**Diluted Remaining Investor NAV:** **${unprotected_remaining_nav:,.2f}**")
