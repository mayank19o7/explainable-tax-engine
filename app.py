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
    TAX_YEARS,
    DEFAULT_TAX_YEAR,
    get_tax_rules,
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

tab1, tab2 = st.tabs(["HRA Calculator", "Full Computation"])

# -----------------------------------------------------------
# Tab 1: HRA Calculator
# -----------------------------------------------------------
with tab1:
    st.caption("HRA Exemption under Section 10(13A) - applies to Old Regime only")

    column1, column2 = st.columns(2)
    with column1:
        basic = st.number_input("Basic Salary (monthly ₹)", min_value=0, value=116097)
        hra_received = st.number_input(
            "HRA Received (monthly ₹)", min_value=0, value=58049
        )
    with column2:
        rent_paid = st.number_input("Rent Paid (monthly ₹)", min_value=0, value=25000)
        is_metro = st.checkbox("Metro city (Delhi/Mumbai/Kolkata/Chennai)", value=False)

    exemption = calculate_hra_exemption(basic, hra_received, rent_paid, is_metro)

    st.metric(label="HRA Exemption (monthly)", value=f"₹{exemption:,.0f}")

    st.write("**Why this number?** It's the least of:")
    option1 = hra_received
    option2 = max(0, rent_paid - (0.10 * basic))
    option3 = basic * (0.50 if is_metro else 0.40)

    options = {
        "Actual HRA received": option1,
        "Rent paid − 10% of Basic": option2,
        f"{'50' if is_metro else '40'}% of Basic": option3,
    }

    for label, value in options.items():
        won = " ← lowest (this wins)" if round(value, 2) == exemption else ""
        st.write(f"- {label}: ₹{value:,.0f}{won}")

# -----------------------------------------------------------
# Tab 2: Full Computation (everything combined)
# -----------------------------------------------------------
with tab2:
    st.caption(
        "One flow: gross salary → exemptions/deductions → taxable income "
        "→ tax, computed separately per regime, since each regime allows "
        "different things."
    )

    left_col, right_col = st.columns([1, 1])

    with left_col:
        with st.container(border=True):
            column1, column2 = st.columns(2)
            with column1:
                st.subheader(
                    "📅 Tax Year",
                    help=(
                        "Which year's rules to calculate under. New Regime slabs "
                        "and its 87A rebate threshold change almost every Budget - "
                        "Old Regime slabs and all deduction limits (80C, 80D, etc.) "
                        "haven't changed across these years."
                    ),
                )
                full_fiscal_year = st.selectbox(
                    "Financial Year",
                    TAX_YEARS,
                    index=TAX_YEARS.index(DEFAULT_TAX_YEAR),
                    key="full_fiscal_year",
                    format_func=lambda fy: f"{fy} ({get_tax_rules(fy)['ay_label']})",
                )
                full_tax_rules = get_tax_rules(full_fiscal_year)
            with column2:
                st.subheader(
                    "🎂 Age Category",
                    help=(
                        "Sets your Old Regime basic exemption (₹2.5L below 60 / "
                        "₹3L senior 60-79 / ₹5L super senior 80+) and your 80D senior-citizen status."
                        "New Regime slabs don't vary by age."
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
                "💳 Allowances u/s 11 (Earlier 10)",
                help=(
                    "Total of other eligible exempt allowances under Section 11. Do not include HRA. "
                    "Like LTA, Transport, Children Education, etc."
                ),
            )
            allowances_u_s_11 = st.number_input(
                "Allowances u/s 11 (₹, annual)",
                min_value=0,
                value=0,
                key="full_allowances_u_s_11",
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
        standard_deduction=full_tax_rules["standard_deduction_old"],
        allowances_u_s_11=allowances_u_s_11,
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
        allowances_u_s_11=allowances_u_s_11,
        standard_deduction=full_tax_rules["standard_deduction_new"],
        other_source_income=other_source_income,
        deduction_80ccd_2=deduction_80ccd_2_new,
    )
    tax_new = calculate_new_regime_tax(taxable_income_new, fiscal_year=full_fiscal_year)

    rebate_old = calculate_87a_rebate(
        taxable_income_old, tax_old, is_new_regime=False, fiscal_year=full_fiscal_year
    )
    tax_after_rebate_old = tax_old - rebate_old
    rebate_new = calculate_87a_rebate(
        taxable_income_new, tax_new, is_new_regime=True, fiscal_year=full_fiscal_year
    )
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
        tax_calculator=lambda income: calculate_new_regime_tax(
            income, fiscal_year=full_fiscal_year
        ),
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

    def comparison_row(
        label, old_val, new_val, old_ok=True, new_ok=True, emphasize=False
    ):
        """
        One line item, Old Regime vs New Regime, side by side.

        Every row - whether it's a small deduction line or a big total
        like Net Tax Payable - goes through this SAME function, so
        everything uses identical column widths, fonts, and padding.
        `emphasize=True` just bumps size/weight for key totals; it
        never switches to a different widget type (e.g. st.metric),
        which is what caused the misalignment before - metric cards
        have their own built-in padding/font that doesn't match plain
        text rows, so mixing the two made rows drift out of line.
        """
        label_col, old_col, new_col = st.columns([2, 1, 1])

        font_size = "1.05rem" if emphasize else "0.9rem"
        weight = "700" if emphasize else "400"
        bg = (
            "background-color:rgba(120,120,120,0.08); border-radius:4px;"
            if emphasize
            else ""
        )

        label_col.markdown(
            f"<div style='font-size:{font_size}; font-weight:{weight}; "
            f"padding:6px 4px; {bg}'>{label}</div>",
            unsafe_allow_html=True,
        )
        for col, val, ok in ((old_col, old_val, old_ok), (new_col, new_val, new_ok)):
            text = f"₹{val:,.0f}" if ok else NOT_APPLICABLE
            col.markdown(
                f"<div style='text-align:center; font-size:{font_size}; "
                f"font-weight:{weight}; padding:6px 4px; {bg}'>{text}</div>",
                unsafe_allow_html=True,
            )

    def section_header(text):
        """
        Small-caps section label with an underline, used to visually
        group rows without needing a heavy st.divider() between every
        single section - dividers are reserved for the few places that
        mark a genuine phase change (inputs done -> now computing tax;
        tax done -> here's the final number).
        """
        st.markdown(
            f"<div style='font-size:0.8rem; font-weight:700; text-transform:uppercase; "
            f"letter-spacing:0.05em; color:rgba(120,120,120,0.9); margin-top:16px; "
            f"margin-bottom:4px; border-bottom:1px solid rgba(120,120,120,0.25); "
            f"padding-bottom:4px;'>{text}</div>",
            unsafe_allow_html=True,
        )

    with right_col:
        st.subheader("🧾 Regime Comparison")

        with st.container(border=True):
            header_label, header_old, header_new = st.columns([1.5, 1, 1])
            header_old.markdown(
                "<div style='text-align:center;'><h4>Old Regime</h4></div>",
                unsafe_allow_html=True,
            )
            header_new.markdown(
                "<div style='text-align:center;'><h4>New Regime</h4></div>",
                unsafe_allow_html=True,
            )

            section_header("💰 Income")
            comparison_row(
                "Standard Deduction",
                full_tax_rules["standard_deduction_old"],
                full_tax_rules["standard_deduction_new"],
            )
            if other_source_income > 0:
                comparison_row(
                    "Other Source Income", other_source_income, other_source_income
                )

            section_header("📉 Exemptions & Deductions")
            comparison_row("Professional Tax", professional_tax, 0, new_ok=False)
            comparison_row("HRA Exemption", hra_exemption, 0, new_ok=False)
            comparison_row("Allowances u/s 11", allowances_u_s_11, allowances_u_s_11)
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

            section_header("🧮 Taxable Income & Tax")
            comparison_row(
                "Taxable Income", taxable_income_old, taxable_income_new, emphasize=True
            )
            comparison_row("Tax Liability", tax_old, tax_new, emphasize=True)

            if (
                rebate_old > 0
                or rebate_new > 0
                or surcharge_old > 0
                or surcharge_new > 0
            ):
                section_header("➖ Rebate, Surcharge & Cess")
            else:
                section_header("➖ Cess")
            if rebate_old > 0 or rebate_new > 0:
                comparison_row("Section 87A Rebate", rebate_old, rebate_new)
            if surcharge_old > 0 or surcharge_new > 0:
                comparison_row("Surcharge", surcharge_old, surcharge_new)
            comparison_row("Cess (4%)", cess_old, cess_new)

            comparison_row("Net Tax Payable", net_tax_old, net_tax_new, emphasize=True)

            if tax_already_paid > 0:
                section_header("💵 ITR Settlement")
                comparison_row(
                    "Tax Already Paid (TDS)", tax_already_paid, tax_already_paid
                )
                balance_label_col, bc1, bc2 = st.columns([2, 1, 1])

                def balance_box(balance):
                    rounded = round(
                        balance
                    )  # avoid float noise (-0.2) misreading as Refund
                    if rounded > 0:
                        status, amount = "Payable", rounded
                        bg, fg = "rgba(239,68,68,0.15)", "#f87171"
                    elif rounded < 0:
                        status, amount = "Refund", -rounded
                        bg, fg = "rgba(34,197,94,0.15)", "#4ade80"
                    else:
                        status, amount = "Settled", 0
                        bg, fg = "rgba(59,130,246,0.15)", "#60a5fa"
                    return (
                        f"<div style='background-color:{bg}; color:{fg}; "
                        f"border-radius:8px; padding:8px 6px; text-align:center; "
                        f"line-height:1.3;'>"
                        f"<div style='font-size:0.75rem; opacity:0.85;'>{status}</div>"
                        f"<div style='font-size:1rem; font-weight:700;'>₹{amount:,.0f}</div>"
                        f"</div>"
                    )

                bc1.markdown(balance_box(balance_old), unsafe_allow_html=True)
                bc2.markdown(balance_box(balance_new), unsafe_allow_html=True)

            section_header("")
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
            "87A Rebate has marginal relief just above ₹5L (Old) / ₹12L (New) taxable income. "
            "Surcharge (income > ₹50L) also has marginal relief per threshold; New Regime caps at 25%, "
            "Old Regime adds a 37% slab above ₹5Cr. 80CCD(2) assumes 14% (Govt) / 10% (private) of Basic "
            "under Old Regime and 14% for everyone under New Regime - some employers use a different base "
            "(e.g. Basic+DA), which can cause a small gap vs your Form16."
        )
