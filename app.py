"""
Explainable Tax Engine - Step 2
--------------------------------
UI layer only. Actual tax math lives in tax_logic.py

New this step: compare Old vs New Regime side by side.
"""

import streamlit as st
from tax_logic import calculate_new_regime_tax, calculate_old_regime_tax

st.title("Explainable Tax Engine")
st.caption("Step 2: Compare Old Regime vs New Regime")

salary = st.number_input(
    "Enter your annual taxable salary (₹)",
    min_value=0,
    value=1000000,
    step=10000,
)

new_tax = calculate_new_regime_tax(salary)
old_tax = calculate_old_regime_tax(salary)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Old Regime")
    st.metric(label="Tax", value=f"₹{old_tax:,.0f}")

with col2:
    st.subheader("New Regime")
    st.metric(label="Tax", value=f"₹{new_tax:,.0f}")

st.divider()

if old_tax < new_tax:
    saving = new_tax - old_tax
    st.success(f"Choose Old Regime. Tax Saving = ₹{saving:,.0f}")
elif new_tax < old_tax:
    saving = old_tax - new_tax
    st.success(f"Choose New Regime. Tax Saving = ₹{saving:,.0f}")
else:
    st.info("Both regimes result in the same tax.")