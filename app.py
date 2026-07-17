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
    calculate_80c_deduction,
    calculate_80ccd_1b_deduction,
    calculate_80ccd_2_deduction,
    calculate_80g_deduction,
    calculate_80d_deduction,
    compute_taxable_income,
    STANDARD_DEDUCTION_OLD_REGIME,
    STANDARD_DEDUCTION_NEW_REGIME,
)

st.title("Explainable Tax Engine")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Regime Comparison", "HRA Calculator", "Deductions (80C / NPS / 80D)", "Full Computation"]
)

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

# -----------------------------------------------------------
# Tab 3: new - Deductions (80C / 80CCD(1B))
# -----------------------------------------------------------
with tab3:
    st.caption("Old Regime only - New Regime disallows both of these")

    st.subheader("Section 80C")
    st.write("PF, LIC, ELSS, tuition fees, etc. Combined cap: ₹1,50,000")
    invested_80c = st.number_input(
        "Total 80C investments (₹, annual)", min_value=0, value=150000
    )
    deduction_80c = calculate_80c_deduction(invested_80c)
    st.metric(label="80C Deduction Allowed", value=f"₹{deduction_80c:,.0f}")
    if invested_80c > 150000:
        st.caption(
            f"You invested ₹{invested_80c:,.0f}, but only ₹1,50,000 is "
            f"allowed - the extra ₹{invested_80c - 150000:,.0f} gets no benefit."
        )

    st.divider()

    st.subheader("Section 80CCD(1B)")
    st.write("Additional NPS investment, separate from 80C. Cap: ₹50,000")
    invested_nps = st.number_input(
        "NPS investment under 80CCD(1B) (₹, annual)", min_value=0, value=50000
    )
    deduction_nps = calculate_80ccd_1b_deduction(invested_nps)
    st.metric(label="80CCD(1B) Deduction Allowed", value=f"₹{deduction_nps:,.0f}")
    if invested_nps > 50000:
        st.caption(
            f"You invested ₹{invested_nps:,.0f}, but only ₹50,000 is "
            f"allowed - the extra ₹{invested_nps - 50000:,.0f} gets no benefit."
        )

    st.divider()

    st.subheader("Section 80D")
    st.write(
        "Health insurance premiums. Self+family cap ₹25,000 (₹50,000 if "
        "senior citizen). Parents cap ₹25,000 (₹50,000 if senior citizen)."
    )
    d1, d2 = st.columns(2)
    with d1:
        premium_self = st.number_input(
            "Self + family premium (₹, annual)", min_value=0, value=25000
        )
        self_senior = st.checkbox("I am a senior citizen (60+)", value=False)
    with d2:
        premium_parents = st.number_input(
            "Parents' premium (₹, annual)", min_value=0, value=0
        )
        parents_senior = st.checkbox("Parents are senior citizens (60+)", value=False)
    deduction_80d = calculate_80d_deduction(
        premium_self, premium_parents, self_senior, parents_senior
    )
    st.metric(label="80D Deduction Allowed", value=f"₹{deduction_80d:,.0f}")

    st.divider()
    total_deductions = deduction_80c + deduction_nps + deduction_80d
    st.metric(label="Total Deductions (80C + 80CCD(1B) + 80D)", value=f"₹{total_deductions:,.0f}")

# -----------------------------------------------------------
# Tab 4: new - Full Computation (everything combined)
# -----------------------------------------------------------
with tab4:
    st.caption(
        "One flow: gross salary → exemptions/deductions → taxable income "
        "→ tax, computed separately per regime, since each regime allows "
        "different things."
    )

    st.subheader("Gross Salary")
    st.caption("Total salary before any exemptions/deductions. No limit.")
    gross_salary = st.number_input(
        "Gross Salary (₹, annual)", min_value=0, value=2910444, key="full_gross"
    )

    st.subheader("Professional Tax")
    st.caption("State-level tax on your payslip, Old Regime only. Limit: ~₹2,500/year (varies by state).")
    professional_tax = st.number_input(
        "Professional Tax paid (₹, annual)",
        min_value=0, value=2500, key="full_pt",
    )

    st.write("**HRA inputs (Old Regime only)**")
    st.caption("Rent exemption under Sec 10(13A). Limit: least of HRA received, rent − 10% of Basic, or 40%/50% of Basic.")
    fc1, fc2 = st.columns(2)
    with fc1:
        full_basic = st.number_input("Basic Salary (₹, annual)", min_value=0, value=1187094, key="full_basic")
        full_hra_received = st.number_input("HRA Received (₹, annual)", min_value=0, value=593549, key="full_hra")
    with fc2:
        full_rent_paid = st.number_input("Rent Paid (₹, annual)", min_value=0, value=250000, key="full_rent")
        full_is_metro = st.checkbox("Metro city", value=False, key="full_metro")

    st.write("**Investment inputs (Old Regime only)**")
    st.caption("80C: PF/LIC/ELSS/tuition, capped ₹1,50,000. 80CCD(1B): extra NPS, capped ₹50,000.")
    fc3, fc4 = st.columns(2)
    with fc3:
        full_80c = st.number_input("80C investments (₹, annual)", min_value=0, value=150000, key="full_80c")
    with fc4:
        full_nps = st.number_input("80CCD(1B) NPS (₹, annual)", min_value=0, value=50000, key="full_nps")

    st.write("**80CCD(2) - Employer NPS (allowed in BOTH regimes)**")
    st.caption("Employer's own NPS contribution. Limit: 10% of Basic Salary (private sector).")
    suggested_employer_nps = round(0.10 * full_basic, 2)
    auto_calc_nps = st.checkbox(
        "Auto-calculate as 10% of Basic Salary (recommended)",
        value=True,
        key="full_nps_auto",
    )
    if auto_calc_nps:
        full_employer_nps = suggested_employer_nps
        st.info(f"Auto-set to 10% of Basic (₹{full_basic:,.0f}) = ₹{full_employer_nps:,.0f}")
    else:
        full_employer_nps = st.number_input(
            "Employer's NPS contribution (₹, annual)",
            min_value=0,
            value=int(suggested_employer_nps),
            key="full_employer_nps_manual",
        )

    st.write("**80G - Donations (Old Regime only, simplified to 100% category)**")
    st.caption("Donations to eligible charities. Limit: no cap in this simplified 100%-deductible category.")
    full_donation = st.number_input(
        "Donation amount (₹, annual)", min_value=0, value=550, key="full_donation"
    )

    st.write("**80D - Health Insurance (Old Regime only)**")
    st.caption("Self+family cap ₹25,000 (₹50,000 senior). Parents cap ₹25,000 (₹50,000 senior).")
    d1, d2 = st.columns(2)
    with d1:
        full_premium_self = st.number_input(
            "Self + family premium (₹, annual)", min_value=0, value=0, key="full_premium_self"
        )
        full_self_senior = st.checkbox("I am a senior citizen (60+)", value=False, key="full_self_senior")
    with d2:
        full_premium_parents = st.number_input(
            "Parents' premium (₹, annual)", min_value=0, value=0, key="full_premium_parents"
        )
        full_parents_senior = st.checkbox("Parents are senior citizens (60+)", value=False, key="full_parents_senior")

    # --- Old Regime: everything applies ---
    hra_exemption = calculate_hra_exemption(
        full_basic, full_hra_received, full_rent_paid, full_is_metro
    )
    deduction_80c = calculate_80c_deduction(full_80c)
    deduction_80ccd_1b = calculate_80ccd_1b_deduction(full_nps)
    deduction_80ccd_2 = calculate_80ccd_2_deduction(full_employer_nps, full_basic)
    deduction_80g = calculate_80g_deduction(full_donation, fully_exempt=True)
    deduction_80d = calculate_80d_deduction(
        full_premium_self, full_premium_parents, full_self_senior, full_parents_senior
    )

    taxable_income_old = compute_taxable_income(
        gross_salary=gross_salary,
        standard_deduction=STANDARD_DEDUCTION_OLD_REGIME,
        professional_tax=professional_tax,
        hra_exemption=hra_exemption,
        deduction_80c=deduction_80c,
        deduction_80ccd_1b=deduction_80ccd_1b,
        deduction_80ccd_2=deduction_80ccd_2,
        deduction_80g=deduction_80g,
        deduction_80d=deduction_80d,
    )
    tax_old = calculate_old_regime_tax(taxable_income_old)

    # --- New Regime: only 80CCD(2) applies, nothing else ---
    taxable_income_new = compute_taxable_income(
        gross_salary=gross_salary,
        standard_deduction=STANDARD_DEDUCTION_NEW_REGIME,
        deduction_80ccd_2=deduction_80ccd_2,
    )
    tax_new = calculate_new_regime_tax(taxable_income_new)

    st.divider()
    st.subheader("Result")

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("**Old Regime**")
        st.write(f"Standard Deduction: ₹{STANDARD_DEDUCTION_OLD_REGIME:,.0f}")
        st.write(f"Professional Tax: ₹{professional_tax:,.0f}")
        st.write(f"HRA Exemption: ₹{hra_exemption:,.0f}")
        st.write(f"80C Deduction: ₹{deduction_80c:,.0f}")
        st.write(f"80CCD(1B) Deduction: ₹{deduction_80ccd_1b:,.0f}")
        st.write(f"80CCD(2) Deduction: ₹{deduction_80ccd_2:,.0f}")
        st.write(f"80G Deduction: ₹{deduction_80g:,.0f}")
        st.write(f"80D Deduction: ₹{deduction_80d:,.0f}")
        st.metric("Taxable Income", f"₹{taxable_income_old:,.0f}")
        st.metric("Tax", f"₹{tax_old:,.0f}")
    with rc2:
        st.markdown("**New Regime**")
        st.write(f"Standard Deduction: ₹{STANDARD_DEDUCTION_NEW_REGIME:,.0f}")
        st.write(f"80CCD(2) Deduction: ₹{deduction_80ccd_2:,.0f}  (only deduction New Regime allows)")
        st.write("HRA / 80C / 80CCD(1B) / PT / 80G / 80D: not allowed")
        st.metric("Taxable Income", f"₹{taxable_income_new:,.0f}")
        st.metric("Tax", f"₹{tax_new:,.0f}")

    st.divider()
    if tax_old < tax_new:
        st.success(f"Choose Old Regime. Tax Saving = ₹{tax_new - tax_old:,.0f}")
    elif tax_new < tax_old:
        st.success(f"Choose New Regime. Tax Saving = ₹{tax_old - tax_new:,.0f}")
    else:
        st.info("Both regimes result in the same tax.")

    st.caption(
        "Note: 80CCD(2) here is capped at 10% of Basic. Some employers "
        "cap it against a different base (e.g. Basic+DA), which can "
        "cause a small gap vs your actual Form16 - a good example of "
        "why a Reconciliation Engine matters."
    )