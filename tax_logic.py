"""
Pure tax calculation logic. No Streamlit, no UI - just Python functions.

Keeping this separate means:
- You can test/run it directly, with no browser involved.
- Later, the UI file just calls these functions; it doesn't need to
  know HOW tax is calculated, only WHAT the answer is.
"""


def calculate_new_regime_tax(taxable_income: float) -> float:
    """
    Calculates tax using India's New Regime slabs for FY 2024-25
    (AY 2025-26), as revised in Budget 2024.
    """

    # (upper limit of slab, tax rate for that slab)
    slabs = [
        (300000, 0.00),
        (700000, 0.05),
        (1000000, 0.10),
        (1200000, 0.15),
        (1500000, 0.20),
        (float("inf"), 0.30),
    ]

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


def calculate_old_regime_tax(taxable_income: float) -> float:
    """
    Calculates tax using the Old Regime slabs (FY 2024-25),
    for a taxpayer below 60 years of age.

    Same shape as calculate_new_regime_tax - only the `slabs`
    table differs. That repetition is a hint we could later merge
    these into one function taking a slab table as an argument.
    """

    slabs = [
        (250000, 0.00),
        (500000, 0.05),
        (1000000, 0.20),
        (float("inf"), 0.30),
    ]

    tax = 0.0
    previous_limit = 0

    for limit, rate in slabs:
        if taxable_income > previous_limit:
            slab_income = min(taxable_income, limit) - previous_limit
            tax += slab_income * rate
            previous_limit = limit
        else:
            break

    return round(tax, 2)


# This block only runs when you execute THIS file directly
# (e.g. `python3 tax_logic.py`). It will NOT run when this file
# is imported by app.py or by another script.
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
    option_2 = max(0, rent_paid - (0.10 * basic))  # can't go negative
    option_3 = basic * (0.50 if is_metro else 0.40)

    exemption = min(option_1, option_2, option_3)
    return round(exemption, 2)


# This block only runs when you execute THIS file directly
# (e.g. `python3 tax_logic.py`). It will NOT run when this file
# is imported by app.py or by another script.
def calculate_80c_deduction(invested_amount: float) -> float:
    """
    Section 80C: PF, LIC, ELSS, etc. Old Regime only.
    Capped at ₹1,50,000 regardless of how much you actually invest.
    """
    LIMIT = 150000
    return round(min(invested_amount, LIMIT), 2)


def calculate_80ccd_1b_deduction(nps_invested_amount: float) -> float:
    """
    Section 80CCD(1B): additional NPS investment, ON TOP OF 80C's
    ₹1,50,000 - a separate ₹50,000 bucket. Old Regime only.
    """
    LIMIT = 50000
    return round(min(nps_invested_amount, LIMIT), 2)


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