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

OLD_REGIME_SLABS = [
    (250000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]


HEALTH_EDUCATION_CESS_RATE = 0.04  # 4%, same rate for both regimes


def calculate_cess(tax_amount: float, rate: float = HEALTH_EDUCATION_CESS_RATE) -> float:
    """
    Health & Education Cess: a flat 4% surcharge on top of your
    computed tax (not on your income - on the TAX itself).
    Same rate applies to both Old and New Regime.

    Applied AFTER any rebate (e.g. Section 87A) - we haven't built
    rebate yet, so for now this runs directly on slab tax. Once
    rebate is added, this should run on (tax - rebate) instead.
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


def calculate_old_regime_tax(taxable_income: float) -> float:
    """
    Calculates tax using the Old Regime slabs (FY 2024-25),
    for a taxpayer below 60 years of age.
    """
    return calculate_slab_tax(taxable_income, OLD_REGIME_SLABS)


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
    professional_tax: float = 0,
    hra_exemption: float = 0,
    deduction_80c: float = 0,
    deduction_80ccd_1b: float = 0,
    deduction_80ccd_2: float = 0,
    deduction_80g: float = 0,
    deduction_80d: float = 0,
) -> float:
    """
    Combines everything we've built so far into one taxable income number.

    This is a plain aggregator - it doesn't decide WHAT numbers go in
    (that's the caller's job, e.g. passing hra_exemption=0 for New Regime
    since HRA isn't allowed there). It just subtracts what it's given.

    All default to 0 so you can call this for New Regime with just
    gross_salary, standard_deduction, and deduction_80ccd_2 (the one
    deduction New Regime does allow).
    """
    taxable = (
        gross_salary
        - standard_deduction
        - professional_tax
        - hra_exemption
        - deduction_80c
        - deduction_80ccd_1b
        - deduction_80ccd_2
        - deduction_80g
        - deduction_80d
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