"""
Explainable Tax Engine - Step 3
--------------------------------
UI layer only. Actual tax math lives in tax_logic.py

New this step: HRA exemption calculator, with a breakdown of
which of the three formula options actually won (the "explain"
part of the plan).
"""

import streamlit as st
from tax_logic import (
    calculate_new_regime_tax,
    calculate_old_regime_tax,
    calculate_hra_exemption,
)

st.title("Explainable Tax Engine")

tab1, tab2 = st.tabs(["Regime Comparison", "HRA Calculator"])

# -----------------------------------------------------------
# Tab 1: same as Step 2
# -----------------------------------------------------------
with tab1:
    st.caption("Compare Old Regime vs New Regime")

    salary = st.number_input(
        "Enter your annual taxable salary (₹)",
        min_value=0,
        value=1000000,
        step=10000,
        key="salary_input",
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
        st.success(f"Choose Old Regime. Tax Saving = ₹{new_tax - old_tax:,.0f}")
    elif new_tax < old_tax:
        st.success(f"Choose New Regime. Tax Saving = ₹{old_tax - new_tax:,.0f}")
    else:
        st.info("Both regimes result in the same tax.")

# -----------------------------------------------------------
# Tab 2: new - HRA Calculator
# -----------------------------------------------------------
with tab2:
    st.caption("HRA Exemption under Section 10(13A) - applies to Old Regime only")

    c1, c2 = st.columns(2)
    with c1:
        basic = st.number_input("Basic Salary (monthly ₹)", min_value=0, value=116097)
        hra_received = st.number_input("HRA Received (monthly ₹)", min_value=0, value=58049)
    with c2:
        rent_paid = st.number_input("Rent Paid (monthly ₹)", min_value=0, value=25000)
        is_metro = st.checkbox("Metro city (Delhi/Mumbai/Kolkata/Chennai)", value=False)

    exemption = calculate_hra_exemption(basic, hra_received, rent_paid, is_metro)

    st.metric(label="HRA Exemption (monthly)", value=f"₹{exemption:,.0f}")

    st.write("**Why this number?** It's the least of:")
    option_1 = hra_received
    option_2 = max(0, rent_paid - (0.10 * basic))
    option_3 = basic * (0.50 if is_metro else 0.40)

    options = {
        "Actual HRA received": option_1,
        "Rent paid − 10% of Basic": option_2,
        f"{'50' if is_metro else '40'}% of Basic": option_3,
    }

    for label, value in options.items():
        won = " ← lowest (this wins)" if round(value, 2) == exemption else ""
        st.write(f"- {label}: ₹{value:,.0f}{won}")