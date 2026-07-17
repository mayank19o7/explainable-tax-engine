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
- [x] 80CCD(2) employer NPS deduction (allowed in both regimes)
- [x] 80G donations (simplified, 100% category)
- [x] 80D (health insurance, self + parents, senior citizen limits)
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
ITR files. `.gitignore` blocks common tax-document file types by
default. If you want sample data for testing, create fake or redacted
numbers under `data/sample/`.