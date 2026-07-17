"""
Explainable Tax Engine - Step 1
--------------------------------
Goal: enter a salary, see the tax under the New Regime slabs.

This is intentionally tiny. We'll grow it piece by piece.
"""

import streamlit as st
from tax_logic import calculate_new_regime_tax

st.title("Explainable Tax Engine")
st.caption("Step 1: Salary in, tax out (New Regime only)")

salary = st.number_input(
    "Enter your annual taxable salary (₹)",
    min_value=0,
    value=1000000,
    step=10000,
)

tax = calculate_new_regime_tax(salary)

st.metric(label="Tax under New Regime", value=f"₹{tax:,.0f}")
