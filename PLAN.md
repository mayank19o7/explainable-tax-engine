# Explainable Tax Engine

*A Python-based tax computation, reconciliation, and explainability
platform.*

------------------------------------------------------------------------

# Table of Contents

1.  [Vision](#vision)
2.  [Guiding Principle](#guiding-principle)
3.  [Example Problem Statement](#example-problem-statement)
4.  [Core Design Principles](#core-design-principles)
5.  [High Level Architecture](#high-level-architecture)
6.  [Engines & Modules](#engines--modules)
    -   [Regime Rule Engine](#regime-rule-engine)
    -   [HRA Engine](#hra-engine)
    -   [Deductions Engine](#deductions-engine)
    -   [Income Modules](#income-modules)
    -   [Reconciliation Engine](#reconciliation-engine)
    -   [Explainability Engine](#explainability-engine)
    -   [Recommendation Engine](#recommendation-engine)
    -   [Scenario Simulator](#scenario-simulator)
    -   [Monthly Salary Structure Engine (Payroll Simulation)](#monthly-salary-structure-engine-payroll-simulation)
7.  [Supported Inputs](#supported-inputs)
8.  [Cross-Cutting Concerns](#cross-cutting-concerns)
    -   [Financial Year Awareness](#financial-year-awareness)
    -   [Privacy-First Constraint](#privacy-first-constraint)
9.  [ITR Filing Assistance / AI Capability](#itr-filing-assistance--ai-capability)
10. [Backlog & Roadmap](#backlog--roadmap)
    -   [Identified Gaps (from real tax document review)](#identified-gaps-from-real-tax-document-review)
    -   [Future Features](#future-features)
    -   [Development Roadmap](#development-roadmap)
11. [Suggested Technology Stack](#suggested-technology-stack)

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

# Guiding Principle

Do not build:

> A tax calculator.

Build:

> An explainable tax computation and reconciliation engine capable of
> explaining every rupee appearing in an ITR.

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

# Engines & Modules

## Regime Rule Engine

Example:

### Old Regime

Allowed:

-   HRA
-   80C
-   80CCD(1B)
-   80D
-   Professional Tax

### New Regime

Allowed:

-   Standard Deduction
-   Employer NPS 80CCD(2)

Disallowed:

-   HRA
-   80C
-   80CCD(1B)
-   80D

------------------------------------------------------------------------

## HRA Engine

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

## Deductions Engine

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

## Income Modules

### Salary

-   Multiple employers
-   Bonus
-   Perquisites
-   RSUs
-   ESOPs

### Other Sources

-   Savings Interest
-   FD Interest
-   Dividend
-   Refund Interest
-   Bond Interest

### House Property

-   Self occupied
-   Let out
-   Interest deduction

### Capital Gains

-   Equity
-   Debt
-   Mutual Funds
-   ESOP sales

------------------------------------------------------------------------

## Reconciliation Engine

(See [Core Design Principles → Reconciliation Engine](#3-reconciliation-engine)
above for the full description.)

Compare Payroll Tax Sheet, Filed ITR, AIS, and TDS Data; generate
difference reports automatically, in the style of the
[Example Problem Statement](#example-problem-statement).

------------------------------------------------------------------------

## Explainability Engine

Questions it should answer:

-   Why is my taxable income high?
-   Why was refund interest added?
-   Why is HRA missing?
-   Why was 80C ignored?
-   Why is payroll tax different from ITR tax?

------------------------------------------------------------------------

## Recommendation Engine

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

## Scenario Simulator

Examples:

-   What if I invest ₹50,000 in NPS?
-   What if I switch regime?
-   What if I sell mutual funds?
-   What if I receive bonus?

------------------------------------------------------------------------

## Monthly Salary Structure Engine (Payroll Simulation)

The app currently takes salary as **flat annual figures** (Basic,
HRA, etc.) computed once for the whole year. Real payroll/tax-sheet
data (see `Salary + Tax Simulator Sheet FY.2024-2025.xlsx`'s `Salary`
worksheet) instead builds these annual figures bottom-up, **month by
month**, which matters because salary structures usually change
mid-year (e.g. an annual increment effective January) — a flat
annual number can't represent that.

### Observed structure (from the real sheet)

-   Two annual "salary structure" blocks: one effective from the
    start of the FY, one from the increment month onward — each
    listing annual Basic / HRA / Special Allowance / Internet
    Allowance / Provident Fund / Food Coupons / NPS / LTA, divided by
    12 to get a monthly rate for that period.
-   A 12-row month-by-month earnings table (Apr → Mar) with columns
    for Basic, HRA, Special Allowance, Internet Allowance, Misc,
    Leave Encashment, Arrears (Basic/HRA/SA), NPS, Gifts — each month
    picks up the monthly rate from whichever structure block is
    active that month, plus one-off items (arrears, leave encashment,
    gifts) that only appear in specific months.
-   A parallel 12-row month-by-month deductions table: Income Tax
    (TDS), Education Cess (computed as **4% of that month's Income
    Tax**, not a flat annual %), Provident Fund, Professional Tax,
    Mediclaim, CSR Contribution.
-   Both tables have a `Total` row summing all 12 months into the
    annual figures the rest of the tax computation actually uses.

### What this means for the app

-   **Inputs**: instead of one "Basic Salary (annual)" field, allow an
    optional "salary structure change" — a set of Basic/HRA/etc.
    values effective from month 1, an optional second set effective
    from a chosen increment month, and the increment month itself.
-   **Computation**: monthly amount = annual/12 for whichever
    structure block is active; annual total = sum of the 12 monthly
    amounts (N₁ months at rate 1 + N₂ months at rate 2, where
    N₁ + N₂ = 12). This is what should actually feed the HRA
    exemption and taxable income calculations, not a single flat
    annual number.
-   **Reconciliation value**: this is likely a major source of the
    gap between the app's simplified annual math and a real payslip's
    cumulative Form16 figure (see the Example Problem Statement at
    the top of this doc) — a flat-annual HRA/Basic calc doesn't match
    a mid-year-incremented payroll calc.
-   **Cess note**: reinforces that Cess should really be calculated
    per-period on tax withheld (TDS), then summed — for the app's
    simplified annual model, computing Cess as 4% of the final annual
    tax figure is an acceptable approximation, but a true monthly
    payroll simulator should compute it month-by-month like the real
    sheet does.
-   This is a bigger feature than a single deduction — it fits
    naturally into the existing **HRA Calculator tab** (`tab2` in
    `app.py`), since HRA exemption is already computed monthly there;
    extending it to support a second "post-increment" Basic/HRA/rent
    block (with an increment month picker) and summing 12 months is a
    natural evolution of that tab, not a new tab/module. The annual
    Full Computation tab would then consume the resulting annual
    Basic/HRA totals instead of a single flat input.
-   **Output**: alongside annual Basic and annual HRA, the tab should
    also surface an annual **Gross Salary** total (sum of all salary
    components across both structure blocks) so it can directly feed
    the Full Computation tab's "Gross Salary" input instead of that
    figure being entered separately/manually.

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

# Cross-Cutting Concerns

These are concerns that cut across every engine/module above rather
than belonging to any single one — get them wrong and every number
downstream is affected.

## Financial Year Awareness

Every number the engine produces today (slab boundaries/rates,
standard deduction, 80C/80CCD(1B)/80D limits, 80CCD(2) rate, rebate
u/s 87A thresholds, cess %) is **year-specific tax law**, currently
hardcoded in `tax_logic.py` for FY 2024-25 only (see the module's own
"FY 2024-25 rules" comment on its constants block). Tax rules change
almost every Union Budget — slab boundaries, rebate thresholds, and
even deduction rates (e.g. the 80CCD(2) 10%→14% change itself) are
routinely revised year to year. Without a concept of "which FY am I
calculating for," the engine can only ever be correct for one single
year and silently wrong for every other year a user might want to
check.

### Planned approach

-   Add an explicit **FY selector** (e.g. "FY 2023-24", "FY 2024-25",
    "FY 2025-26") as a top-level input, likely in the sidebar or at
    the top of the app, since it affects literally everything
    downstream — slabs, every deduction limit, and applicable rates.
-   Turn today's flat module-level constants in `tax_logic.py` into a
    **per-FY rules table** (e.g. a dict keyed by FY string, each
    holding its own slabs, limits, and rates), with functions taking
    an explicit `fy` parameter instead of relying on hardcoded
    globals. This keeps old-year math available for comparison/
    reconciliation against a previously filed return, not just the
    current year.
-   Every UI caption/limit display (already added per earlier steps)
    should reflect the limits **for the selected FY**, not a fixed
    label.
-   This should be tackled before or alongside the
    [Monthly Salary Structure Engine](#monthly-salary-structure-engine-payroll-simulation)
    above, since salary-structure "increment month" dates only make
    sense relative to a specific FY's Apr-Mar calendar.

## Privacy-First Constraint

Any AI/web-search capability must not send raw PII (name, PAN,
Aadhaar, address) to a third-party API/search by default — given real
tax documents were already found in this project's working directory
(see privacy note under [Identified Gaps](#identified-gaps-from-real-tax-document-review)),
any future AI integration needs local-first or redaction-first
handling of sensitive fields before anything leaves the machine. Web
searches should only ever carry generic queries (e.g. "ITR-2 Schedule
CG instructions AY 2025-26"), never the user's actual figures or
identity.

*(This constraint governs the [ITR Filing Assistance / AI Capability](#itr-filing-assistance--ai-capability)
feature below, but is called out here since it's a project-wide rule,
not just a feature detail.)*

------------------------------------------------------------------------

# ITR Filing Assistance / AI Capability

Once the engine can compute a fully explained, source-traced taxable
income and tax liability (Explainability + Reconciliation Engines
above), the goal is a system that helps answer three practical
questions: **which ITR form do I need to file, how do I fill it, and
how do I legally reduce my tax** — using the app's own computed,
traceable numbers as ground truth, plus web search for anything that
depends on current-year rules/portal specifics rather than being
hardcoded.

## 1. Which ITR form to file

-   Based on the user's actual income sources already modeled by the
    engine (Salary only vs. + House Property vs. + Capital Gains vs.
    + Business income, etc. — see Income Modules), determine the
    correct form: ITR-1 (Sahaj), ITR-2, ITR-3, ITR-4 (Sugam), etc.
-   This is mostly rule-based (a decision table: "has Capital Gains ⇒
    not ITR-1," "has Business income ⇒ ITR-3/4," etc.) — the real
    filed ITR-2 already reviewed in this project is a concrete example
    of "why ITR-2, not ITR-1" (it has Capital Gains/Schedule CG,
    Foreign Assets question, etc.) that can seed this rule table.
-   Since ITR form eligibility rules and form numbers can shift by
    year (see [Financial Year Awareness](#financial-year-awareness)),
    a **web search step** should confirm current-year eligibility
    criteria rather than trusting a possibly-stale hardcoded rule,
    especially for edge cases (foreign income, crypto/VDA, multiple
    house properties).

## 2. How to fill it

-   Reuse the ITR Fill Assistance mapping (computed value → exact
    schedule/field) described above, but go further: for each
    schedule/field, **look up current official guidance** (Income Tax
    Department help text, instructions for that AY) via web search,
    so the "how to fill this field" explanation stays accurate even
    as the portal/form changes year to year, instead of being frozen
    documentation that silently goes stale.
-   Output a step-by-step, schedule-by-schedule fill guide the user
    can follow on the actual e-filing portal — still assistance only,
    never auto-submitting anything.

## 3. Tax optimization suggestions

-   Extends the existing [Recommendation Engine](#recommendation-engine) /
    [Scenario Simulator](#scenario-simulator): given the user's actual
    numbers, suggest concrete, legal ways to reduce tax — e.g. "you
    have ₹30,000 of unused 80C room, investing there saves ≈₹9,000,"
    "you'd save more switching to the New Regime this year," "you're
    close to the 87A rebate threshold."
-   These specific suggestions should be backed by the deterministic
    calculators in `tax_logic.py` (so the numbers are always correct),
    with web search used only to pull in anything time-sensitive that
    isn't (yet) encoded as a rule — e.g. a new scheme/deduction
    introduced in the latest Budget, or a rule change the app's
    constants haven't been updated for yet.

## Implementation shape (not yet decided, options to explore)

-   A hybrid: deterministic engine for all *numbers* (never trust an
    LLM/web result for a value that `tax_logic.py` can compute
    directly), with an LLM + web search layer purely for (a) form
    selection reasoning, (b) explaining *how/where* to fill each
    field in current-year plain language, and (c) surfacing
    optimization ideas the deterministic rules haven't been coded for
    yet.
-   Exact tooling (which LLM, which search API, local vs. hosted) is
    an open question — flagged here as a future decision, not a
    commitment yet.

See [Privacy-First Constraint](#privacy-first-constraint) above for
the non-negotiable rule governing this feature.

------------------------------------------------------------------------

# Backlog & Roadmap

## Identified Gaps (from real tax document review)

Cross-checked the current implementation against real personal tax
documents (salary/tax simulator sheet, an old tax-computation
proforma, a filed ITR-2, and a monthly payslip/tax sheet). These are
sections/rules present in those real documents but not yet built,
kept here as a prioritized backlog. Items are removed from this list
once implemented (and checked off in `README.md`).

### Priority order

1.  **Surcharge** for income above ₹50L / ₹1Cr / ₹2Cr / ₹5Cr.
2.  **80TTA / 80TTB** — savings/FD interest deduction (₹10,000
    non-seniors, ₹50,000 seniors).
3.  **House Property income** — Section 24(b) home loan interest
    exemption, self-occupied vs. let-out, loss from house property.
4.  **Income from Other Sources** — Savings/FD/NSC/Post Office
    interest, family pension (with Sec 57(iia) standard deduction).
5.  **80E, 80GG, 80U, 80DD, 80DDB, broader 80G/80GGA/80GGC
    categories** — all present in the real documents, none built.
6.  **Capital Gains module** — the real filed ITR-2 has a Capital
    Gains schedule (incl. 112A LTCG, VDA/crypto); biggest single
    missing income module, already scoped under [Income Modules](#income-modules)
    above.
7.  **Rebate u/s 89(1)** (Form 10E, arrears relief).

### Already resolved from this review

-   **Health & Education Cess (4%)** on tax.
-   **Rebate u/s 87A** — up to ₹12,500 (Old Regime, taxable income
    ≤ ₹5L) / ₹25,000 (New Regime, taxable income ≤ ₹7L), including
    marginal relief just above the threshold.
-   **Senior Citizen (60-79) / Super Senior Citizen (80+) Old Regime
    slabs** — basic exemption limit now varies by age (₹2,50,000 /
    ₹3,00,000 / ₹5,00,000); New Regime slabs stay the same for every
    age, as per law.
-   80CCD(2) employer NPS rate corrected: Old Regime is 14%
    (Govt employer) / 10% (private employer); New Regime is 14% for
    everyone regardless of employer type.
-   80C kept as a single aggregate input (by design), but its caption
    now lists the instruments it covers (EPF/VPF, PPF, ELSS, LIC,
    tuition, housing loan principal, NSC, SCSS, Sukanya Samriddhi,
    tax-saving FD/bonds) for clarity without adding UI complexity.
-   Real tax documents used for this review are kept out of version
    control (in a git-ignored folder), never committed.

## Future Features

-   AIS Auto Import
-   PAN based portfolio tracking
-   Tax forecast for next FY
-   Monthly tax projection
-   Tax optimization suggestions
-   PDF Tax Sheet generation

## Development Roadmap

### Phase 1

-   Salary Engine
-   Tax Slab Engine
-   Old/New Regime Support

### Phase 2

-   HRA Engine
-   Deductions Engine

### Phase 3

-   AIS Import
-   Form16 Import
-   ITR Import

### Phase 4

-   Reconciliation Engine
-   Explainability Engine

### Phase 5

-   Dashboard
-   Reports
-   PDF Export

------------------------------------------------------------------------

# Suggested Technology Stack

Backend: - Python - Pandas - Pydantic

API: - FastAPI

UI: - Streamlit initially - React later

Storage: - SQLite initially - PostgreSQL later
