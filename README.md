# Explainable Tax Engine

A Python-based tax computation, reconciliation, and explainability
platform. Goal: not just "how much tax," but "why is my tax this
amount" — full traceability from source to final number.

## Status

🚧 Learning project, in progress. Currently built:

- [x] New Regime slab calculator
- [x] Old Regime slab calculator + side-by-side comparison
- [x] HRA exemption calculator (Section 10(13A))
- [x] 80C deduction (capped)
- [x] 80CCD(1B) NPS deduction (capped)
- [x] Combined taxable income flow (salary → exemptions → deductions → tax)
- [x] 80CCD(2) employer NPS deduction (allowed in both regimes; Old Regime 10% private/14% govt, New Regime 14% for everyone)
- [x] 80G donations (simplified, 100% category)
- [x] 80D (health insurance, self + parents, senior citizen limits)
- [x] Health & Education Cess (4% on tax)
- [x] Section 288A/288B rounding (nearest ₹10, taxable income)
- [x] Section 87A rebate (New Regime up to ₹7L, Old Regime up to ₹5L - zero tax)
- [x] Section 87A marginal relief (just above the threshold)
- [x] Senior Citizen (60-79) / Super Senior Citizen (80+) Old Regime slabs
- [x] Surcharge for high incomes (>₹50L, with marginal relief; Old Regime 10/15/25/37%, New Regime capped at 25%)
- [x] Income from Other Sources - Savings Bank interest, Deposit (FD/PO/NSC) interest, Dividend, Others - all taxed in both regimes
- [x] 80TTA/80TTB deduction on Savings Bank + Deposit interest only (₹10,000 non-senior savings-only / ₹50,000 senior both-interest, Old Regime only)
- [x] Full Computation tab redesigned as a single Old vs New Regime comparison table (section by section, with "Not Applicable" for regime-restricted items) + hover (ⓘ) tooltips on each input section
- [x] ITR Settlement: enter Tax Already Paid (TDS/Advance Tax) and see Balance Payable / Refund per regime - handles the "employer deducted TDS under one regime/declaration, but final filing differs" scenario
- [ ] Form16 / AIS / ITR import
- [ ] Reconciliation engine
- [ ] Explainability report (PDF export)

See `PLAN.md` for the full original design doc and roadmap.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Run logic without the UI

```bash
python3 tax_logic.py
```

## Project structure

```
explainable-tax-engine/
├── app.py            # Streamlit UI - imports functions from tax_logic.py
├── tax_logic.py       # Pure tax calculation logic, no UI code
├── requirements.txt
├── .gitignore
├── README.md
├── PLAN.md            # Original design/vision doc
└── data/
    └── sample/        # Fake/redacted example data only - never real documents
```

## A note on data privacy

This repo intentionally never contains real payslips, Form16, AIS, or
ITR files. Any real personal documents used for local testing/reference
should be kept under a folder matched by `.gitignore` (e.g. `dist/`,
already ignored for Python packaging purposes) so they're never staged
or committed. If you want sample data for testing, create fake or
redacted numbers under `data/sample/`.