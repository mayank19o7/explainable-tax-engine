# Explainable Tax Engine

*A Python-based tax computation, reconciliation, and explainability
platform.*

------------------------------------------------------------------------

# Vision

Most tax calculators answer:

> "How much tax do I need to pay?"

This project aims to answer:

> "Why is my tax this amount?"

The goal is to build a **tax debugger** rather than a simple calculator.

The system should be able to explain:

-   Why taxable income increased.
-   Why deductions disappeared.
-   Why a particular regime was chosen.
-   Why an amount appears in the ITR.
-   Why the tax liability changed between payroll and filing.

------------------------------------------------------------------------

# Example Problem Statement

Example reconciliation:

  Source               Taxable Income
  ------------------ ----------------
  Employer Payroll         ₹23,72,400
  Filed ITR                ₹28,04,760

Difference:

  Reason                      Impact
  ----------------------- ----------
  Savings Interest          +154,554
  FD Interest                +42,170
  Dividend                    +1,544
  Refund Interest             +2,505
  HRA removed               +143,070
  80C removed               +150,000
  NPS 80CCD(1B) removed      +50,000
  Employer NPS retained     -141,929

The tool should generate such reports automatically.

------------------------------------------------------------------------

# Core Design Principles

## 1. Explainability First

Every number should have:

-   Source
-   Formula
-   Tax section
-   Regime applicability
-   Supporting explanation

Example:

``` text
Refund Interest: ₹2,505

Source:
CPC Refund Record

Section:
Income from Other Sources

Reason:
Interest paid u/s 244A on previous year's refund.
```

------------------------------------------------------------------------

## 2. Source Traceability

Every value must know where it originated.

Possible sources:

-   Form16
-   Form24Q
-   AIS
-   Form26AS
-   Employer Tax Sheet
-   Filed ITR JSON
-   User Input

Example:

``` python
salary = TaxValue(
    amount=2910444,
    source="Form24Q",
    section="Salary",
    confidence="high"
)
```

------------------------------------------------------------------------

## 3. Reconciliation Engine

The most important feature.

Compare:

-   Payroll Tax Sheet
-   Filed ITR
-   AIS
-   TDS Data

Generate difference reports automatically.

------------------------------------------------------------------------

# High Level Architecture

``` text
TaxEngine
│
├── Income
│   ├── Salary
│   ├── House Property
│   ├── Capital Gains
│   └── Other Sources
│
├── Deductions
│   ├── 80C
│   ├── 80CCD1B
│   ├── 80CCD2
│   ├── 80D
│   └── 80G
│
├── Regime Engines
│   ├── Old Regime
│   └── New Regime
│
├── Reconciliation
│
└── Explainability
```

------------------------------------------------------------------------

# Supported Inputs

## Manual Entry

-   Salary
-   Rent Paid
-   HRA Received
-   Investments
-   Other Income

## Imports

### AIS JSON

Extract: - Savings Interest - FD Interest - Dividend - Refund Interest

### Form16

Extract: - Salary - HRA - PF - NPS - TDS

### Employer Tax Sheet

Extract: - Taxable Income - Payroll Tax - HRA Computation

### ITR JSON

Extract: - Final Taxable Income - Regime Used - Claimed Deductions

### Form26AS

Extract: - TDS - TCS - Refunds

------------------------------------------------------------------------

# Income Modules

## Salary

-   Multiple employers
-   Bonus
-   Perquisites
-   RSUs
-   ESOPs

## Other Sources

-   Savings Interest
-   FD Interest
-   Dividend
-   Refund Interest
-   Bond Interest

## House Property

-   Self occupied
-   Let out
-   Interest deduction

## Capital Gains

-   Equity
-   Debt
-   Mutual Funds
-   ESOP sales

------------------------------------------------------------------------

# Deductions Engine

Supported sections:

-   80C
-   80CCD(1B)
-   80CCD(2)
-   80D
-   80G
-   80TTA
-   80TTB
-   24(b)

Each deduction should know:

-   Limit
-   Eligibility
-   Applicable regime

------------------------------------------------------------------------

# Regime Rule Engine

Example:

## Old Regime

Allowed:

-   HRA
-   80C
-   80CCD(1B)
-   80D
-   Professional Tax

## New Regime

Allowed:

-   Standard Deduction
-   Employer NPS 80CCD(2)

Disallowed:

-   HRA
-   80C
-   80CCD(1B)
-   80D

------------------------------------------------------------------------

# HRA Engine

Inputs:

-   Basic Salary
-   HRA Received
-   Rent Paid
-   Metro Flag

Formula:

Least of:

1.  Actual HRA received
2.  Rent paid minus 10% of salary
3.  50% or 40% of salary

------------------------------------------------------------------------

# Explainability Engine

Questions it should answer:

-   Why is my taxable income high?
-   Why was refund interest added?
-   Why is HRA missing?
-   Why was 80C ignored?
-   Why is payroll tax different from ITR tax?

------------------------------------------------------------------------

# Recommendation Engine

Output:

  Particular         Old   New
  ---------------- ----- -----
  Taxable Income         
  Tax Liability          
  Cess                   
  Net Tax                

Recommendation:

``` text
Choose Old Regime.
Tax Saving = ₹7,496
```

------------------------------------------------------------------------

# Scenario Simulator

Examples:

-   What if I invest ₹50,000 in NPS?
-   What if I switch regime?
-   What if I sell mutual funds?
-   What if I receive bonus?

------------------------------------------------------------------------

# Future Features

-   AIS Auto Import
-   PAN based portfolio tracking
-   Tax forecast for next FY
-   Monthly tax projection
-   Tax optimization suggestions
-   PDF Tax Sheet generation

------------------------------------------------------------------------

# Suggested Technology Stack

Backend: - Python - Pandas - Pydantic

API: - FastAPI

UI: - Streamlit initially - React later

Storage: - SQLite initially - PostgreSQL later

------------------------------------------------------------------------

# Development Roadmap

## Phase 1

-   Salary Engine
-   Tax Slab Engine
-   Old/New Regime Support

## Phase 2

-   HRA Engine
-   Deductions Engine

## Phase 3

-   AIS Import
-   Form16 Import
-   ITR Import

## Phase 4

-   Reconciliation Engine
-   Explainability Engine

## Phase 5

-   Dashboard
-   Reports
-   PDF Export

------------------------------------------------------------------------

# Guiding Principle

Do not build:

> A tax calculator.

Build:

> An explainable tax computation and reconciliation engine capable of
> explaining every rupee appearing in an ITR.
