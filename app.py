"""
Explainable Tax Engine
--------------------------------
UI layer only. Actual tax math lives in tax_logic.py

Tabs so far: Regime Comparison, HRA Calculator, and a Full
Computation flow combining everything (salary -> exemptions ->
deductions -> tax, per regime, including 80C/80CCD(1B)/80CCD(2)/80D/80G).
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
    calculate_80tta_ttb_deduction,
    calculate_cess,
    calculate_balance_tax_payable,
    calculate_87a_rebate,
    calculate_surcharge,
    compute_taxable_income,
    STANDARD_DEDUCTION_OLD_REGIME,
    STANDARD_DEDUCTION_NEW_REGIME,
    LIMIT_80C,
    LIMIT_80CCD_1B,
    LIMIT_80D_NORMAL,
    LIMIT_80D_SENIOR_CITIZEN,
    EMPLOYER_NPS_RATE_PRIVATE,
    EMPLOYER_NPS_RATE_GOVT,
    AGE_CATEGORY_BELOW_60,
    AGE_CATEGORY_SENIOR,
    AGE_CATEGORY_SUPER_SENIOR,
)

st.set_page_config(page_title="Explainable Tax Engine", layout="wide")

st.title("Explainable Tax Engine")

tab1, tab2, tab3 = st.tabs(["Regime Comparison", "HRA Calculator", "Full Computation"])

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

    age_label_to_category = {
        "Below 60": AGE_CATEGORY_BELOW_60,
        "Senior Citizen (60-79)": AGE_CATEGORY_SENIOR,
        "Super Senior Citizen (80+)": AGE_CATEGORY_SUPER_SENIOR,
    }
    age_label = st.selectbox(
        "Your age category (affects Old Regime basic exemption limit only - "
        "New Regime slabs are the same for every age)",
        list(age_label_to_category.keys()),
        key="regime_cmp_age",
    )
    age_category = age_label_to_category[age_label]

    new_tax = calculate_new_regime_tax(salary)
    old_tax = calculate_old_regime_tax(salary, age_category=age_category)

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
        hra_received = st.number_input(
            "HRA Received (monthly ₹)", min_value=0, value=58049
        )
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
# Tab 3: Full Computation (everything combined)
# -----------------------------------------------------------
with tab3:
    st.caption(
        "One flow: gross salary → exemptions/deductions → taxable income "
        "→ tax, computed separately per regime, since each regime allows "
        "different things."
    )

    left_col, right_col = st.columns([1, 1])

    with left_col:
        with st.container(border=True):
            st.subheader(
                "🎂 Age Category",
                help=(
                    "Sets your Old Regime basic exemption (₹2.5L below 60 / "
                    "₹3L senior 60-79 / ₹5L super senior 80+) and your 80D "
                    "senior-citizen status. New Regime slabs don't vary by age."
                ),
            )
            full_age_label_to_category = {
                "Below 60": AGE_CATEGORY_BELOW_60,
                "Senior Citizen (60-79)": AGE_CATEGORY_SENIOR,
                "Super Senior Citizen (80+)": AGE_CATEGORY_SUPER_SENIOR,
            }
            full_age_label = st.selectbox(
                "Your age category",
                list(full_age_label_to_category.keys()),
                key="full_age",
            )
            full_age_category = full_age_label_to_category[full_age_label]

        with st.container(border=True):
            st.subheader(
                "💰 Gross Salary", help="Total salary before any exemptions/deductions."
            )
            gross_salary = st.number_input(
                "Gross Salary (₹, annual)", min_value=0, value=2910444, key="full_gross"
            )

        with st.container(border=True):
            st.subheader(
                "🏦 Income from Other Sources",
                help=(
                    "Taxable in BOTH regimes. 80TTA/80TTB below (Old Regime "
                    "only) covers Savings + Deposit interest only: non-seniors "
                    "get 80TTA (savings only, ₹10,000 cap); seniors get 80TTB "
                    "(savings + deposit, ₹50,000 cap) instead."
                ),
            )
            os1, os2 = st.columns(2)
            with os1:
                full_savings_interest = st.number_input(
                    "Interest from Savings Bank (₹, annual)",
                    min_value=0,
                    value=0,
                    key="full_savings_interest",
                )
            with os2:
                full_deposit_interest = st.number_input(
                    "Interest from Deposits - FD/Post Office/NSC etc. (₹, annual)",
                    min_value=0,
                    value=0,
                    key="full_deposit_interest",
                )

            os3, os4 = st.columns(2)
            with os3:
                full_dividend_income = st.number_input(
                    "Dividend - shares & mutual fund units (₹, annual)",
                    min_value=0,
                    value=0,
                    key="full_dividend_income",
                )
            with os4:
                full_other_income_misc = st.number_input(
                    "Others - refund interest, family pension, etc. (₹, annual)",
                    min_value=0,
                    value=0,
                    key="full_other_income_misc",
                )

            other_source_income = (
                full_savings_interest
                + full_deposit_interest
                + full_dividend_income
                + full_other_income_misc
            )

            full_is_senior_for_tta_ttb = full_age_category != AGE_CATEGORY_BELOW_60
            deduction_80tta_ttb = calculate_80tta_ttb_deduction(
                savings_interest=full_savings_interest,
                fd_interest=full_deposit_interest,
                is_senior_citizen=full_is_senior_for_tta_ttb,
            )
            if other_source_income > 0:
                st.metric("Total Other Source Income", f"₹{other_source_income:,.0f}")
                section_used = (
                    "80TTB (senior)"
                    if full_is_senior_for_tta_ttb
                    else "80TTA (non-senior)"
                )
                st.metric(
                    f"Deduction claimed - {section_used}",
                    f"₹{deduction_80tta_ttb:,.0f}",
                )
                if not full_is_senior_for_tta_ttb and full_deposit_interest > 0:
                    st.caption(
                        f"Deposit interest (₹{full_deposit_interest:,.0f}) doesn't "
                        "qualify under 80TTA - only savings bank interest does."
                    )
                if full_dividend_income + full_other_income_misc > 0:
                    st.caption(
                        f"Dividend + Others (₹{full_dividend_income + full_other_income_misc:,.0f}) "
                        "get no 80TTA/80TTB deduction - only savings/deposit interest is eligible."
                    )

        with st.container(border=True):
            st.subheader(
                "🏛️ Professional Tax",
                help="State-level payroll tax, Old Regime only. Typically capped ~₹2,500/year.",
            )
            professional_tax = st.number_input(
                "Professional Tax paid (₹, annual)",
                min_value=0,
                value=2500,
                key="full_pt",
            )

        with st.container(border=True):
            st.subheader(
                "🏠 HRA (Old Regime only)",
                help="Sec 10(13A). Exemption = least of HRA received, rent − 10% of Basic, or 40%/50% of Basic.",
            )
            fc1, fc2 = st.columns(2)
            with fc1:
                full_basic = st.number_input(
                    "Basic Salary (₹, annual)",
                    min_value=0,
                    value=1419288,
                    key="full_basic",
                )
                full_hra_received = st.number_input(
                    "HRA Received (₹, annual)",
                    min_value=0,
                    value=709647,
                    key="full_hra",
                )
            with fc2:
                full_rent_paid = st.number_input(
                    "Rent Paid (₹, annual)", min_value=0, value=285000, key="full_rent"
                )
                full_is_metro = st.checkbox("Metro city", value=False, key="full_metro")

        with st.container(border=True):
            st.subheader(
                "📈 Section 80C / 80CCD(1B) - Investments (Old Regime only)",
                help=(
                    "80C: EPF/VPF, PPF, ELSS, life insurance, tuition fees, home "
                    "loan principal, NSC, SCSS, Sukanya Samriddhi, tax-saving FD/"
                    "bonds - combined cap ₹1,50,000. 80CCD(1B): extra NPS, cap ₹50,000."
                ),
            )
            fc3, fc4 = st.columns(2)
            with fc3:
                full_80c = st.number_input(
                    "80C investments (₹, annual)",
                    min_value=0,
                    value=150000,
                    key="full_80c",
                )
                if full_80c > LIMIT_80C:
                    st.caption(
                        f"Only ₹{LIMIT_80C:,.0f} allowed - the extra "
                        f"₹{full_80c - LIMIT_80C:,.0f} gets no benefit."
                    )
            with fc4:
                full_nps = st.number_input(
                    "80CCD(1B) NPS (₹, annual)",
                    min_value=0,
                    value=50000,
                    key="full_nps",
                )
                if full_nps > LIMIT_80CCD_1B:
                    st.caption(
                        f"Only ₹{LIMIT_80CCD_1B:,.0f} allowed - the extra "
                        f"₹{full_nps - LIMIT_80CCD_1B:,.0f} gets no benefit."
                    )

        with st.container(border=True):
            st.subheader(
                "🏢 Section 80CCD(2) - Employer NPS (allowed in BOTH regimes)",
                help="Employer's NPS contribution. Old Regime: 14% (Govt) / 10% (private) of Basic. New Regime: 14% for everyone.",
            )
            full_is_govt_employee = st.checkbox(
                "I am a Central/State Government employee",
                value=False,
                key="full_is_govt",
            )
            old_regime_nps_rate = (
                EMPLOYER_NPS_RATE_GOVT
                if full_is_govt_employee
                else EMPLOYER_NPS_RATE_PRIVATE
            )
            suggested_employer_nps = round(old_regime_nps_rate * full_basic, 2)
            auto_calc_nps = st.checkbox(
                f"Auto-calculate as {old_regime_nps_rate:.0%} of Basic Salary (recommended)",
                value=False,
                key="full_nps_auto",
            )
            if auto_calc_nps:
                full_employer_nps = suggested_employer_nps
                st.info(
                    f"Auto-set to {old_regime_nps_rate:.0%} of Basic (₹{full_basic:,.0f}) = ₹{full_employer_nps:,.0f}"
                )
            else:
                full_employer_nps = st.number_input(
                    "Employer's NPS contribution (₹, annual)",
                    min_value=0,
                    value=int(suggested_employer_nps),
                    key="full_employer_nps_manual",
                )

        with st.container(border=True):
            st.subheader(
                "🎗️ Section 80G - Donations (Old Regime only)",
                help="Donations to eligible charities. No cap in this simplified 100%-deductible category.",
            )
            full_donation = st.number_input(
                "Donation amount (₹, annual)",
                min_value=0,
                value=550,
                key="full_donation",
            )

        with st.container(border=True):
            st.subheader(
                "🏥 Section 80D - Health Insurance (Old Regime only)",
                help="Self+family cap ₹25,000 (₹50,000 senior). Parents cap ₹25,000 (₹50,000 senior).",
            )
            d1, d2 = st.columns(2)
            with d1:
                full_premium_self = st.number_input(
                    "Self + family premium (₹, annual)",
                    min_value=0,
                    value=0,
                    key="full_premium_self",
                )
                full_self_senior = full_age_category != AGE_CATEGORY_BELOW_60
                st.caption(
                    "Senior citizen limit applies (from Age Category above)."
                    if full_self_senior
                    else "Non-senior limit applies (from Age Category above)."
                )
                limit_self = (
                    LIMIT_80D_SENIOR_CITIZEN if full_self_senior else LIMIT_80D_NORMAL
                )
                if full_premium_self > limit_self:
                    st.caption(
                        f"Only ₹{limit_self:,.0f} allowed - the extra "
                        f"₹{full_premium_self - limit_self:,.0f} gets no benefit."
                    )
            with d2:
                full_premium_parents = st.number_input(
                    "Parents' premium (₹, annual)",
                    min_value=0,
                    value=0,
                    key="full_premium_parents",
                )
                full_parents_senior = st.checkbox(
                    "Parents are senior citizens (60+)",
                    value=False,
                    key="full_parents_senior",
                )
                limit_parents = (
                    LIMIT_80D_SENIOR_CITIZEN
                    if full_parents_senior
                    else LIMIT_80D_NORMAL
                )
                if full_premium_parents > limit_parents:
                    st.caption(
                        f"Only ₹{limit_parents:,.0f} allowed - the extra "
                        f"₹{full_premium_parents - limit_parents:,.0f} gets no benefit."
                    )

        with st.container(border=True):
            st.subheader(
                "💵 Tax Already Paid (TDS / Advance Tax)",
                help=(
                    "Tax already deducted by your employer (Form16) or paid as "
                    "advance tax during the year - typically based on whichever "
                    "regime/declarations you told your employer, which may not "
                    "match your final numbers here (e.g. undeclared Other Source "
                    "income). Used below to show what's still payable, or "
                    "refundable, at ITR filing under each regime."
                ),
            )
            tax_already_paid = st.number_input(
                "Tax Already Paid (₹, annual)",
                min_value=0,
                value=0,
                key="full_tax_paid",
            )

    # Old Regime: everything applies
    hra_exemption = calculate_hra_exemption(
        full_basic, full_hra_received, full_rent_paid, full_is_metro
    )
    deduction_80c = calculate_80c_deduction(full_80c)
    deduction_80ccd_1b = calculate_80ccd_1b_deduction(full_nps)
    deduction_80ccd_2_old = calculate_80ccd_2_deduction(
        full_employer_nps, full_basic, full_is_govt_employee, is_new_regime=False
    )
    deduction_80ccd_2_new = calculate_80ccd_2_deduction(
        full_employer_nps, full_basic, full_is_govt_employee, is_new_regime=True
    )
    deduction_80g = calculate_80g_deduction(full_donation, fully_exempt=True)
    deduction_80d = calculate_80d_deduction(
        full_premium_self, full_premium_parents, full_self_senior, full_parents_senior
    )

    taxable_income_old = compute_taxable_income(
        gross_salary=gross_salary,
        standard_deduction=STANDARD_DEDUCTION_OLD_REGIME,
        other_source_income=other_source_income,
        professional_tax=professional_tax,
        hra_exemption=hra_exemption,
        deduction_80c=deduction_80c,
        deduction_80ccd_1b=deduction_80ccd_1b,
        deduction_80ccd_2=deduction_80ccd_2_old,
        deduction_80g=deduction_80g,
        deduction_80d=deduction_80d,
        deduction_80tta_ttb=deduction_80tta_ttb,
    )
    tax_old = calculate_old_regime_tax(
        taxable_income_old, age_category=full_age_category
    )

    # New Regime: only 80CCD(2) applies; other source income is still
    # taxable but gets no 80TTA/80TTB deduction.
    taxable_income_new = compute_taxable_income(
        gross_salary=gross_salary,
        standard_deduction=STANDARD_DEDUCTION_NEW_REGIME,
        other_source_income=other_source_income,
        deduction_80ccd_2=deduction_80ccd_2_new,
    )
    tax_new = calculate_new_regime_tax(taxable_income_new)

    rebate_old = calculate_87a_rebate(taxable_income_old, tax_old, is_new_regime=False)
    tax_after_rebate_old = tax_old - rebate_old
    rebate_new = calculate_87a_rebate(taxable_income_new, tax_new, is_new_regime=True)
    tax_after_rebate_new = tax_new - rebate_new

    surcharge_old = calculate_surcharge(
        taxable_income_old,
        tax_after_rebate_old,
        is_new_regime=False,
        tax_calculator=lambda income: calculate_old_regime_tax(
            income, age_category=full_age_category
        ),
    )
    surcharge_new = calculate_surcharge(
        taxable_income_new,
        tax_after_rebate_new,
        is_new_regime=True,
        tax_calculator=calculate_new_regime_tax,
    )

    tax_plus_surcharge_old = tax_after_rebate_old + surcharge_old
    tax_plus_surcharge_new = tax_after_rebate_new + surcharge_new
    cess_old = calculate_cess(tax_plus_surcharge_old)
    net_tax_old = tax_plus_surcharge_old + cess_old
    cess_new = calculate_cess(tax_plus_surcharge_new)
    net_tax_new = tax_plus_surcharge_new + cess_new

    balance_old = calculate_balance_tax_payable(net_tax_old, tax_already_paid)
    balance_new = calculate_balance_tax_payable(net_tax_new, tax_already_paid)

    NOT_APPLICABLE = "⛔ Not Applicable"

    def comparison_row(label, old_val, new_val, old_ok=True, new_ok=True):
        """One line item, Old Regime vs New Regime, side by side."""
        rc1, rc2 = st.columns(2)
        rc1.write(
            f"{label}: {'₹{:,.0f}'.format(old_val) if old_ok else NOT_APPLICABLE}"
        )
        rc2.write(
            f"{label}: {'₹{:,.0f}'.format(new_val) if new_ok else NOT_APPLICABLE}"
        )

    with right_col:
        st.subheader("🧾 Regime Comparison")

        with st.container(border=True):
            rc1, rc2 = st.columns(2)
            rc1.markdown("### Old Regime")
            rc2.markdown("### New Regime")

            st.markdown("**💰 Income**")
            comparison_row(
                "Standard Deduction",
                STANDARD_DEDUCTION_OLD_REGIME,
                STANDARD_DEDUCTION_NEW_REGIME,
            )
            if other_source_income > 0:
                comparison_row(
                    "Other Source Income", other_source_income, other_source_income
                )

            st.markdown("**📉 Exemptions & Deductions**")
            comparison_row("Professional Tax", professional_tax, 0, new_ok=False)
            comparison_row("HRA Exemption", hra_exemption, 0, new_ok=False)
            comparison_row("80C Deduction", deduction_80c, 0, new_ok=False)
            comparison_row("80CCD(1B) Deduction", deduction_80ccd_1b, 0, new_ok=False)
            comparison_row(
                "80CCD(2) Deduction", deduction_80ccd_2_old, deduction_80ccd_2_new
            )
            comparison_row("80G Deduction", deduction_80g, 0, new_ok=False)
            comparison_row("80D Deduction", deduction_80d, 0, new_ok=False)
            if other_source_income > 0:
                comparison_row(
                    "80TTA/80TTB Deduction", deduction_80tta_ttb, 0, new_ok=False
                )

            st.markdown("**🧮 Tax**")
            rc1, rc2 = st.columns(2)
            rc1.metric("Taxable Income", f"₹{taxable_income_old:,.0f}")
            rc2.metric("Taxable Income", f"₹{taxable_income_new:,.0f}")
            rc1, rc2 = st.columns(2)
            rc1.metric("Tax Liability", f"₹{tax_old:,.0f}")
            rc2.metric("Tax Liability", f"₹{tax_new:,.0f}")
            if rebate_old > 0 or rebate_new > 0:
                comparison_row("Section 87A Rebate", rebate_old, rebate_new)
            if surcharge_old > 0 or surcharge_new > 0:
                comparison_row("Surcharge", surcharge_old, surcharge_new)
            comparison_row("Cess (4%)", cess_old, cess_new)
            rc1, rc2 = st.columns(2)
            rc1.metric("Net Tax", f"₹{net_tax_old:,.0f}")
            rc2.metric("Net Tax", f"₹{net_tax_new:,.0f}")

            if tax_already_paid > 0:
                st.markdown("**💵 ITR Settlement**")
                comparison_row(
                    "Tax Already Paid (TDS)", tax_already_paid, tax_already_paid
                )
                bc1, bc2 = st.columns(2)
                for col, balance in ((bc1, balance_old), (bc2, balance_new)):
                    if balance > 0:
                        col.error(f"Payable: ₹{balance:,.0f}")
                    elif balance < 0:
                        col.success(f"Refund: ₹{-balance:,.0f}")
                    else:
                        col.info("Settled: ₹0")

            st.divider()
            if net_tax_old < net_tax_new:
                st.success(
                    f"Choose Old Regime. Tax Saving = ₹{net_tax_new - net_tax_old:,.0f}"
                )
            elif net_tax_new < net_tax_old:
                st.success(
                    f"Choose New Regime. Tax Saving = ₹{net_tax_old - net_tax_new:,.0f}"
                )
            else:
                st.info("Both regimes result in the same tax.")

        st.caption(
            "87A Rebate has marginal relief just above ₹5L (Old) / ₹7L (New) taxable income. "
            "Surcharge (income > ₹50L) also has marginal relief per threshold; New Regime caps at 25%, "
            "Old Regime adds a 37% slab above ₹5Cr. 80CCD(2) assumes 14% (Govt) / 10% (private) of Basic "
            "under Old Regime and 14% for everyone under New Regime - some employers use a different base "
            "(e.g. Basic+DA), which can cause a small gap vs your Form16."
        )
