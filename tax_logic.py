"""
Pure tax calculation logic. No Streamlit, no UI - just Python functions.

Keeping this separate means:
- You can test/run it directly, with no browser involved.
- Later, the UI file just calls these functions; it doesn't need to
  know HOW tax is calculated, only WHAT the answer is.
"""

# ---------------------------------------------------------------
# Deduction/exemption limits (all in ₹, annual, FY 2024-25 rules).
# Kept as named constants (rather than buried inside functions) so
# they're easy to find, reuse, and eventually override per-year.
# ---------------------------------------------------------------
LIMIT_80C = 150000
LIMIT_80CCD_1B = 50000
LIMIT_80D_NORMAL = 25000
LIMIT_80D_SENIOR_CITIZEN = 50000
LIMIT_80TTA = 10000  # non-seniors: savings account interest only
LIMIT_80TTB_SENIOR = 50000  # seniors: ALL interest (savings + FD + post office etc.)

EMPLOYER_NPS_RATE_PRIVATE = 0.10  # 80CCD(2) cap: 10% of Basic (private-sector employer)
EMPLOYER_NPS_RATE_GOVT = 0.14  # 80CCD(2) cap: 14% of Basic (Central/State Govt employer)

HRA_RENT_THRESHOLD_RATE = 0.10  # rent paid minus 10% of Basic
HRA_METRO_RATE = 0.50
HRA_NON_METRO_RATE = 0.40

# Standard deduction differs by regime (Budget 2024 revision).
STANDARD_DEDUCTION_OLD_REGIME = 50000
STANDARD_DEDUCTION_NEW_REGIME = 75000

# (upper limit of slab, tax rate for that slab)
NEW_REGIME_SLABS = [
    (300000, 0.00),
    (700000, 0.05),
    (1000000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float("inf"), 0.30),
]

# Old Regime slabs vary by the taxpayer's own age - only the basic
# exemption limit changes (rates stay 5%/20%/30%); New Regime slabs
# above are the same for every age group, so there's only one table.
AGE_CATEGORY_BELOW_60 = "below_60"
AGE_CATEGORY_SENIOR = "senior"  # 60 to below 80
AGE_CATEGORY_SUPER_SENIOR = "super_senior"  # 80 and above

OLD_REGIME_SLABS_BELOW_60 = [
    (250000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

OLD_REGIME_SLABS_SENIOR = [
    (300000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

OLD_REGIME_SLABS_SUPER_SENIOR = [
    (500000, 0.00),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

OLD_REGIME_SLABS_BY_AGE = {
    AGE_CATEGORY_BELOW_60: OLD_REGIME_SLABS_BELOW_60,
    AGE_CATEGORY_SENIOR: OLD_REGIME_SLABS_SENIOR,
    AGE_CATEGORY_SUPER_SENIOR: OLD_REGIME_SLABS_SUPER_SENIOR,
}

# Kept for backward compatibility - the below-60 table, same as before
# age-based slabs were added.
OLD_REGIME_SLABS = OLD_REGIME_SLABS_BELOW_60


HEALTH_EDUCATION_CESS_RATE = 0.04  # 4%, same rate for both regimes


def calculate_cess(tax_amount: float, rate: float = HEALTH_EDUCATION_CESS_RATE) -> float:
    """
    Health & Education Cess: a flat 4% surcharge on top of your
    computed tax (not on your income - on the TAX itself).
    Same rate applies to both Old and New Regime.

    Applied AFTER any rebate (e.g. Section 87A) and any surcharge - so
    the 4% is computed on (tax - rebate + surcharge), not on the raw
    slab tax alone.
    """
    return round(tax_amount * rate, 2)


def round_to_nearest_10(amount: float) -> float:
    """
    Sections 288A and 288B of the Income Tax Act: taxable income must 
    both be rounded to the nearest ₹10 (not just the nearest rupee, 
    which is all we've done so far).

    Two steps, matching the law exactly:
      1. Ignore paise - round to the nearest whole rupee first.
         (This also fixes floating-point noise from earlier float
         subtraction, e.g. 2372394.9999996 instead of a clean
         2372395.0 - without this step, checking the tens digit
         on the noisy value gives the WRONG answer.)
      2. Round that whole-rupee amount to the nearest 10, using
         "round half up" - if the last digit is 5 or more, round UP;
         otherwise round DOWN. Python's built-in round() won't do
         this correctly for .5 cases (it uses "banker's rounding"),
         so we compute it manually.
    """
    whole_rupees = round(amount)  # step 1: ignore paise, fix float noise
    remainder = whole_rupees % 10  # step 2: round to nearest 10
    if remainder >= 5:
        return float(whole_rupees - remainder + 10)
    return float(whole_rupees - remainder)


# Section 87A rebate: below a taxable income threshold, you get a
# rebate that can zero out your tax entirely. Thresholds and rebate
# caps differ by regime.
REBATE_87A_INCOME_LIMIT_OLD_REGIME = 500000
REBATE_87A_MAX_AMOUNT_OLD_REGIME = 12500

REBATE_87A_INCOME_LIMIT_NEW_REGIME = 700000
REBATE_87A_MAX_AMOUNT_NEW_REGIME = 25000


def calculate_87a_rebate(taxable_income: float, tax: float, is_new_regime: bool) -> float:
    """
    Section 87A rebate: if taxable income is at or below the regime's
    threshold, you get a rebate - capped at the regime's max amount,
    but never more than the tax you actually owe (so it can only
    bring your tax down to zero, never negative).

    Marginal relief: just above the threshold, without relief, tax
    would jump sharply the moment income crosses the limit by even ₹1
    (a hard cliff). The law prevents this: if income exceeds the
    threshold only slightly, the rebate is reduced so that the net tax
    payable never exceeds the amount of income above the threshold
    (i.e. crossing the line by ₹1 can cost at most ₹1 more tax, not
    the full slab tax). This tapers off naturally - once the excess
    income is large enough that slab tax on it exceeds the tax itself,
    no relief is given.
    """
    if is_new_regime:
        income_limit = REBATE_87A_INCOME_LIMIT_NEW_REGIME
        max_rebate = REBATE_87A_MAX_AMOUNT_NEW_REGIME
    else:
        income_limit = REBATE_87A_INCOME_LIMIT_OLD_REGIME
        max_rebate = REBATE_87A_MAX_AMOUNT_OLD_REGIME

    if taxable_income <= income_limit:
        return round(min(tax, max_rebate), 2)

    # Marginal relief zone: income is above the threshold. Cap the
    # rebate so net tax (tax - rebate) never exceeds the excess income.
    excess_income = taxable_income - income_limit
    if tax > excess_income:
        return round(tax - excess_income, 2)
    return 0.0


# Surcharge: an extra percentage ON TOP OF the income tax itself (not
# on income) for high earners. Applies above ₹50L taxable income, in
# increasing steps. New Regime dropped the top 37% slab (Budget 2023),
# capping New Regime surcharge at 25% regardless of how high income
# goes; Old Regime still has the 37% top slab beyond ₹5Cr.
# Each entry is (income threshold crossed, surcharge rate that then
# applies to the WHOLE tax amount - not just the portion above the
# threshold), in ascending order.
SURCHARGE_BRACKETS_OLD_REGIME = [
    (5000000, 0.10),
    (10000000, 0.15),
    (20000000, 0.25),
    (50000000, 0.37),
]

SURCHARGE_BRACKETS_NEW_REGIME = [
    (5000000, 0.10),
    (10000000, 0.15),
    (20000000, 0.25),
]


def calculate_surcharge(
    taxable_income: float,
    tax_before_surcharge: float,
    is_new_regime: bool,
    tax_calculator,
) -> float:
    """
    Surcharge on high incomes: taxable income > ₹50L pays an extra %
    of the income tax itself (not of income). The rate is a single
    flat % applied to the ENTIRE tax amount based on which bracket the
    taxable income falls in - it isn't a portion-by-portion slab like
    income tax itself.

    `tax_calculator` is the regime's own slab-tax function (e.g.
    calculate_new_regime_tax, or a partial of calculate_old_regime_tax
    bound to the taxpayer's age_category) - needed here to work out
    "tax at exactly the threshold" for marginal relief below.

    Marginal relief: without it, crossing a threshold by even ₹1 would
    add tens of thousands of rupees of surcharge in one jump (a hard
    cliff, just like Section 87A's cliff). The law prevents this: the
    combined (tax + surcharge) can never exceed (tax + surcharge at
    the threshold, using the bracket BELOW) plus the extra income
    above the threshold - so crossing by ₹1 costs at most ₹1 more.
    """
    brackets = SURCHARGE_BRACKETS_NEW_REGIME if is_new_regime else SURCHARGE_BRACKETS_OLD_REGIME

    applicable_rate = 0.0
    applicable_threshold = None
    previous_rate = 0.0
    for threshold, rate in brackets:
        if taxable_income > threshold:
            previous_rate = applicable_rate
            applicable_rate = rate
            applicable_threshold = threshold
        else:
            break

    if applicable_threshold is None:
        return 0.0  # at or below ₹50L - no surcharge at all

    surcharge = round(tax_before_surcharge * applicable_rate, 2)
    total_with_surcharge = tax_before_surcharge + surcharge

    # Marginal relief: cap total (tax + surcharge) at what it would
    # have been at the threshold (using the bracket BELOW - i.e. the
    # rate that applied just before crossing) plus the excess income.
    tax_at_threshold = tax_calculator(applicable_threshold)
    max_total_with_surcharge = (
        tax_at_threshold * (1 + previous_rate) + (taxable_income - applicable_threshold)
    )

    if total_with_surcharge > max_total_with_surcharge:
        relieved_surcharge = max_total_with_surcharge - tax_before_surcharge
        return round(max(relieved_surcharge, 0.0), 2)

    return surcharge


def calculate_slab_tax(taxable_income: float, slabs: list) -> float:
    """
    Generic progressive slab-tax calculator: walks through `slabs`
    (a list of (upper_limit, rate) tuples, in ascending order) and
    taxes each portion of income at its own bracket's rate.

    Both New Regime and Old Regime use this same logic - only the
    slab table differs, so it lives here once instead of being
    duplicated per regime.
    """
    tax = 0.0
    previous_limit = 0

    for limit, rate in slabs:
        if taxable_income > previous_limit:
            # amount of income that falls INSIDE this slab
            slab_income = min(taxable_income, limit) - previous_limit
            tax += slab_income * rate
            previous_limit = limit
        else:
            break  # no more income to tax, stop looping

    return round(tax, 2)


def calculate_new_regime_tax(taxable_income: float) -> float:
    """
    Calculates tax using India's New Regime slabs for FY 2024-25
    (AY 2025-26), as revised in Budget 2024.
    """
    return calculate_slab_tax(taxable_income, NEW_REGIME_SLABS)


def calculate_old_regime_tax(
    taxable_income: float, age_category: str = AGE_CATEGORY_BELOW_60
) -> float:
    """
    Calculates tax using the Old Regime slabs (FY 2024-25). The basic
    exemption limit depends on the taxpayer's own age - `age_category`
    must be one of AGE_CATEGORY_BELOW_60 (default), AGE_CATEGORY_SENIOR
    (60 to below 80), or AGE_CATEGORY_SUPER_SENIOR (80+). New Regime
    has no such distinction - every age uses NEW_REGIME_SLABS.
    """
    slabs = OLD_REGIME_SLABS_BY_AGE.get(age_category, OLD_REGIME_SLABS_BELOW_60)
    return calculate_slab_tax(taxable_income, slabs)


def calculate_hra_exemption(
    basic: float,
    hra_received: float,
    rent_paid: float,
    is_metro: bool,
) -> float:
    """
    Calculates HRA exemption under Section 10(13A) - Old Regime only.
    (New Regime doesn't allow HRA exemption at all.)

    Exemption = LEAST of:
      1. Actual HRA received
      2. Rent paid minus 10% of basic salary
      3. 50% of basic (metro cities) or 40% of basic (non-metro)

    'is_metro' is a bool (True/False) - a simple on/off switch.
    Metro cities for this rule: Delhi, Mumbai, Kolkata, Chennai.
    """

    option_1 = hra_received
    option_2 = max(0, rent_paid - (HRA_RENT_THRESHOLD_RATE * basic))  # can't go negative
    option_3 = basic * (HRA_METRO_RATE if is_metro else HRA_NON_METRO_RATE)

    exemption = min(option_1, option_2, option_3)
    return round(exemption, 2)


def calculate_80c_deduction(invested_amount: float) -> float:
    """
    Section 80C: PF, LIC, ELSS, etc. Old Regime only.
    Capped at ₹1,50,000 regardless of how much you actually invest.
    """
    return round(min(invested_amount, LIMIT_80C), 2)


def calculate_80ccd_1b_deduction(nps_invested_amount: float) -> float:
    """
    Section 80CCD(1B): additional NPS investment, ON TOP OF 80C's
    ₹1,50,000 - a separate ₹50,000 bucket. Old Regime only.
    """
    return round(min(nps_invested_amount, LIMIT_80CCD_1B), 2)


def compute_taxable_income(
    gross_salary: float,
    standard_deduction: float,
    other_source_income: float = 0,
    professional_tax: float = 0,
    hra_exemption: float = 0,
    deduction_80c: float = 0,
    deduction_80ccd_1b: float = 0,
    deduction_80ccd_2: float = 0,
    deduction_80g: float = 0,
    deduction_80d: float = 0,
    deduction_80tta_ttb: float = 0,
) -> float:
    """
    Combines everything we've built so far into one taxable income number.

    This is a plain aggregator - it doesn't decide WHAT numbers go in
    (that's the caller's job, e.g. passing hra_exemption=0 for New Regime
    since HRA isn't allowed there). It just adds/subtracts what it's given.

    `other_source_income` (e.g. savings/FD interest under "Income from
    Other Sources") is ADDED to gross salary - it's taxable in BOTH
    regimes. `deduction_80tta_ttb` is the deduction claimed against that
    interest income - Old Regime only, so callers should pass 0 for
    New Regime.

    All default to 0 so you can call this for New Regime with just
    gross_salary, standard_deduction, other_source_income (still
    taxable), and deduction_80ccd_2 (the one deduction New Regime
    does allow).
    """
    taxable = (
        gross_salary
        + other_source_income
        - standard_deduction
        - professional_tax
        - hra_exemption
        - deduction_80c
        - deduction_80ccd_1b
        - deduction_80ccd_2
        - deduction_80g
        - deduction_80d
        - deduction_80tta_ttb
    )
    taxable = max(0, taxable)  # taxable income can't go negative
    return round_to_nearest_10(round(taxable, 2))  # Section 288A rounding


def calculate_80ccd_2_deduction(
    employer_nps_contribution: float,
    basic_salary: float,
    is_government_employee: bool = False,
    is_new_regime: bool = False,
) -> float:
    """
    Section 80CCD(2): EMPLOYER's contribution to NPS (not your own).
    Unlike every other deduction so far, this is allowed in BOTH
    Old and New Regime - see the plan doc's Regime Rule Engine section.

    Capped at the LOWER of the actual employer contribution or a
    percentage of Basic Salary:
    - Old Regime: 14% for Central/State Government employers,
      10% for every other (private-sector) employer.
    - New Regime: 14% for EVERYONE, government or private
      (this is the one case where the New Regime cap is more
      generous than the Old Regime cap for private-sector employees).
    """
    if is_new_regime or is_government_employee:
        rate = EMPLOYER_NPS_RATE_GOVT
    else:
        rate = EMPLOYER_NPS_RATE_PRIVATE
    limit = rate * basic_salary
    return round(min(employer_nps_contribution, limit), 2)


def calculate_80d_deduction(
    premium_self_family: float,
    premium_parents: float = 0,
    self_senior_citizen: bool = False,
    parents_senior_citizen: bool = False,
) -> float:
    """
    Section 80D: health insurance premiums. Old Regime only.

    Two separate buckets, each capped on its own (not combined):
      - Self + family: ₹25,000 normally, ₹50,000 if self is a senior citizen (60+).
      - Parents: ₹25,000 normally, ₹50,000 if parents are senior citizens (60+).

    So a taxpayer with senior citizen parents could claim up to
    ₹25,000 (self) + ₹50,000 (senior parents) = ₹75,000 total.
    """
    limit_self = LIMIT_80D_SENIOR_CITIZEN if self_senior_citizen else LIMIT_80D_NORMAL
    limit_parents = LIMIT_80D_SENIOR_CITIZEN if parents_senior_citizen else LIMIT_80D_NORMAL

    deduction_self = min(premium_self_family, limit_self)
    deduction_parents = min(premium_parents, limit_parents)

    return round(deduction_self + deduction_parents, 2)


def calculate_80g_deduction(donation_amount: float, fully_exempt: bool = True) -> float:
    """
    Section 80G: donations. Old Regime only.

    SIMPLIFIED for now: real 80G has multiple categories (50% or 100%
    exempt, with or without a "qualifying limit" based on adjusted
    gross income). We're only handling the simple 100%-exempt,
    no-qualifying-limit case (e.g. PM CARES-style funds) for now.
    `fully_exempt=False` gives a rough 50% category as a placeholder.
    """
    if fully_exempt:
        return round(donation_amount, 2)
    return round(donation_amount * 0.5, 2)


def calculate_80tta_ttb_deduction(
    savings_interest: float,
    fd_interest: float = 0,
    other_interest: float = 0,
    is_senior_citizen: bool = False,
) -> float:
    """
    Sections 80TTA / 80TTB: deduction on interest income from a
    savings/FD account. Old Regime only - New Regime allows neither.

    The two sections are mutually exclusive per taxpayer, based on age:
      - 80TTA (non-seniors): ONLY savings account interest is eligible
        (FD/post office interest is NOT), capped at ₹10,000.
      - 80TTB (seniors, 60+): ALL interest income is eligible - savings,
        FD, post office, etc. - capped at ₹50,000 (and since this is
        more generous, it replaces 80TTA for seniors rather than
        stacking with it).
    """
    if is_senior_citizen:
        total_interest = savings_interest + fd_interest + other_interest
        return round(min(total_interest, LIMIT_80TTB_SENIOR), 2)
    return round(min(savings_interest, LIMIT_80TTA), 2)


# This block only runs when you execute THIS file directly
# (e.g. `python3 tax_logic.py`). It will NOT run when this file
# is imported by app.py or by another script.
if __name__ == "__main__":
    test_salaries = [250000, 700000, 1000000, 1600000, 2804760]
    print("New Regime:")
    for salary in test_salaries:
        tax = calculate_new_regime_tax(salary)
        print(f"  Salary: ₹{salary:,} -> Tax: ₹{tax:,.0f}")

    print("Old Regime:")
    for salary in [2372400]:  # known figure from payslip: expect ₹5,24,220
        tax = calculate_old_regime_tax(salary)
        print(f"  Salary: ₹{salary:,} -> Tax: ₹{tax:,.0f}")

    print("HRA Exemption (Jun-2024 from payslip, expect ₹13,390):")
    exemption = calculate_hra_exemption(
        basic=116097,
        hra_received=58049,
        rent_paid=25000,
        is_metro=False,  # Pune is non-metro for this rule
    )
    print(f"  Exemption: ₹{exemption:,.0f}")

    print("80C Deduction (expect capped at ₹1,50,000):")
    print(f"  Invested ₹1,50,000 -> ₹{calculate_80c_deduction(150000):,.0f}")
    print(f"  Invested ₹2,00,000 -> ₹{calculate_80c_deduction(200000):,.0f}  (over cap)")
    print(f"  Invested ₹1,00,000 -> ₹{calculate_80c_deduction(100000):,.0f}  (under cap)")

    print("80CCD(1B) Deduction (expect capped at ₹50,000):")
    print(f"  Invested ₹50,000 -> ₹{calculate_80ccd_1b_deduction(50000):,.0f}")
    print(f"  Invested ₹80,000 -> ₹{calculate_80ccd_1b_deduction(80000):,.0f}  (over cap)")

    print("Combined Taxable Income (Old Regime, annual figures from payslip):")
    hra_exempt_annual = calculate_hra_exemption(
        basic=1187094, hra_received=593549, rent_paid=250000, is_metro=False
    )
    taxable_old = compute_taxable_income(
        gross_salary=2910444,
        standard_deduction=STANDARD_DEDUCTION_OLD_REGIME,
        professional_tax=2500,
        hra_exemption=hra_exempt_annual,
        deduction_80c=calculate_80c_deduction(150000),
        deduction_80ccd_1b=calculate_80ccd_1b_deduction(50000),
    )
    print(f"  HRA exemption (annual, monthly-summed method): ₹{hra_exempt_annual:,.0f}")
    print(f"  Taxable Income (Old Regime): ₹{taxable_old:,.0f}")
    print(f"  NOTE: payslip's own figure is ₹23,72,400 - it differs because")
    print(f"  the payslip also applies 80G + 80CCD(2), which we haven't built yet,")
    print(f"  and uses the annual-aggregate HRA method, not the monthly-sum method.")

    print("Now WITH 80CCD(2) and 80G added:")
    deduction_80ccd_2 = calculate_80ccd_2_deduction(
        employer_nps_contribution=141928, basic_salary=1187094
    )
    deduction_80g = calculate_80g_deduction(donation_amount=550, fully_exempt=True)
    taxable_old_v2 = compute_taxable_income(
        gross_salary=2910444,
        standard_deduction=STANDARD_DEDUCTION_OLD_REGIME,
        professional_tax=2500,
        hra_exemption=hra_exempt_annual,
        deduction_80c=calculate_80c_deduction(150000),
        deduction_80ccd_1b=calculate_80ccd_1b_deduction(50000),
        deduction_80ccd_2=deduction_80ccd_2,
        deduction_80g=deduction_80g,
    )
    print(f"  80CCD(2) deduction (capped at 10% of Basic): ₹{deduction_80ccd_2:,.0f}")
    print(f"    (payslip's own figure is ₹1,41,928 - higher than our 10% cap;")
    print(f"    likely computed on a different base, e.g. Basic+DA, or a")
    print(f"    different cap %. Good target for the reconciliation engine.)")
    print(f"  80G deduction: ₹{deduction_80g:,.0f}")
    print(f"  Taxable Income (Old Regime, v2): ₹{taxable_old_v2:,.0f}")
    print(f"  Remaining gap vs payslip's ₹23,72,400: ₹{taxable_old_v2 - 2372400:,.0f}")

    print("80D Deduction (health insurance, expect self=25,000 capped, parents=50,000 senior-capped):")
    deduction_80d = calculate_80d_deduction(
        premium_self_family=30000,
        premium_parents=60000,
        self_senior_citizen=False,
        parents_senior_citizen=True,
    )
    print(f"  Self+family premium ₹30,000 (cap ₹25,000) + Parents premium ₹60,000, "
          f"senior citizens (cap ₹50,000) -> Deduction: ₹{deduction_80d:,.0f}")

    print("Health & Education Cess (expect ₹20,969 on ₹5,24,220 tax, from payslip):")
    cess = calculate_cess(524220)
    print(f"  Cess: ₹{cess:,.0f}")
    print(f"  Net Tax (Tax + Cess): ₹{524220 + cess:,.0f}  (payslip: ₹5,45,189)")

    print("Section 288A Rounding (round taxable income to nearest ₹10):")
    for amount in [2372394, 2372395, 2372396]:
        print(f"  ₹{amount:,} -> ₹{round_to_nearest_10(amount):,}")

    print("Section 87A Rebate (expect zero tax at the threshold):")
    income_new = 700000
    tax_new_87a = calculate_new_regime_tax(income_new)
    rebate_new = calculate_87a_rebate(income_new, tax_new_87a, is_new_regime=True)
    print(f"  New Regime, ₹{income_new:,} taxable: tax=₹{tax_new_87a:,.0f}, "
          f"rebate=₹{rebate_new:,.0f}, net=₹{tax_new_87a - rebate_new:,.0f}")

    income_old = 500000
    tax_old_87a = calculate_old_regime_tax(income_old)
    rebate_old = calculate_87a_rebate(income_old, tax_old_87a, is_new_regime=False)
    print(f"  Old Regime, ₹{income_old:,} taxable: tax=₹{tax_old_87a:,.0f}, "
          f"rebate=₹{rebate_old:,.0f}, net=₹{tax_old_87a - rebate_old:,.0f}")

    print("Section 87A Marginal Relief (expect net tax to rise gently just above the threshold):")
    for income_new_mr in [700100, 710000]:
        tax_new_mr = calculate_new_regime_tax(income_new_mr)
        rebate_new_mr = calculate_87a_rebate(income_new_mr, tax_new_mr, is_new_regime=True)
        print(f"  New Regime, ₹{income_new_mr:,} taxable: tax=₹{tax_new_mr:,.0f}, "
              f"rebate=₹{rebate_new_mr:,.0f}, net=₹{tax_new_mr - rebate_new_mr:,.0f}")

    for income_old_mr in [500100, 510000]:
        tax_old_mr = calculate_old_regime_tax(income_old_mr)
        rebate_old_mr = calculate_87a_rebate(income_old_mr, tax_old_mr, is_new_regime=False)
        print(f"  Old Regime, ₹{income_old_mr:,} taxable: tax=₹{tax_old_mr:,.0f}, "
              f"rebate=₹{rebate_old_mr:,.0f}, net=₹{tax_old_mr - rebate_old_mr:,.0f}")

    print("Senior Citizen / Super Senior Citizen Old Regime slabs (expect lower tax for higher age, same income):")
    income_age_test = 900000
    for label, category in [
        ("Below 60", AGE_CATEGORY_BELOW_60),
        ("Senior (60-79)", AGE_CATEGORY_SENIOR),
        ("Super Senior (80+)", AGE_CATEGORY_SUPER_SENIOR),
    ]:
        tax_age = calculate_old_regime_tax(income_age_test, age_category=category)
        print(f"  {label}, ₹{income_age_test:,} taxable: tax=₹{tax_age:,.0f}")

    print("Surcharge (expect surcharge to kick in above ₹50L, capped at 25% for New Regime beyond ₹2Cr):")
    for income_sur, label in [(4900000, "Just below ₹50L"), (5100000, "Just above ₹50L"),
                               (10100000, "Just above ₹1Cr"), (30000000, "₹3Cr (Old: 25%, New: 25%)"),
                               (60000000, "₹6Cr (Old: 37% top slab, New: still capped 25%)")]:
        tax_new_sur = calculate_new_regime_tax(income_sur)
        surcharge_new = calculate_surcharge(income_sur, tax_new_sur, is_new_regime=True,
                                             tax_calculator=calculate_new_regime_tax)
        tax_old_sur = calculate_old_regime_tax(income_sur)
        surcharge_old = calculate_surcharge(income_sur, tax_old_sur, is_new_regime=False,
                                             tax_calculator=calculate_old_regime_tax)
        print(f"  {label} (₹{income_sur:,}): "
              f"New Regime tax=₹{tax_new_sur:,.0f}+surcharge=₹{surcharge_new:,.0f}, "
              f"Old Regime tax=₹{tax_old_sur:,.0f}+surcharge=₹{surcharge_old:,.0f}")

    print("Section 80TTA/80TTB Deduction (expect non-senior capped at ₹10,000 savings-only, senior capped at ₹50,000 all-interest):")
    non_senior_deduction = calculate_80tta_ttb_deduction(
        savings_interest=15000, fd_interest=40000, is_senior_citizen=False
    )
    print(f"  Non-senior, savings=₹15,000 + FD=₹40,000 -> Deduction (80TTA, savings-only): ₹{non_senior_deduction:,.0f}")

    senior_deduction = calculate_80tta_ttb_deduction(
        savings_interest=15000, fd_interest=40000, is_senior_citizen=True
    )
    print(f"  Senior, savings=₹15,000 + FD=₹40,000 -> Deduction (80TTB, capped ₹50,000): ₹{senior_deduction:,.0f}")