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


# This block only runs when you execute THIS file directly
# (e.g. `python3 tax_logic.py`). It will NOT run when this file
# is imported by app.py or by another script.
if __name__ == "__main__":
    test_salaries = [250000, 700000, 1000000, 1600000, 2804760]
    print("New Regime:")
    for salary in test_salaries:
        tax = calculate_new_regime_tax(salary)
        print(f"  Salary: ₹{salary:,} -> Tax: ₹{tax:,.0f}")
