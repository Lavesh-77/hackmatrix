# Project Specification — Which customers will buy again?

## Problem statement

A small online retailer has a fixed budget for prioritizing customers and years of messy transaction history. Build a Python solution that predicts each eligible customer's chance of making a qualifying purchase in the next 30 days, estimates their capped purchase value, and selects the required shortlist.

This is an offline predictive ranking task. It does not estimate whether contacting a selected customer causes a purchase.

## Problem analysis

The history includes duplicate lines, returns, cancellations, nonpositive quantities or prices, missing descriptions, and unknown customer IDs. A recent large purchase alone may not identify repeat demand. The system must derive useful customer features without using information from after the observation cutoff, and it must generalize to customer cohorts not seen during training.

## Proposed solution

Train and validate a model using the supplied public training examples. Package its inference code and saved parameters so the evaluation platform can call `decide(observation, state)` on each batch. Cleaning and feature preparation required at inference time must be part of the runnable source; evaluation inputs are supplied by the platform.

## Target users

- **Primary system consumer:** the competition evaluator, which supplies batches and checks the required action schema.
- **Business-context user:** a retailer's customer or marketing analyst who uses the selected shortlist to prioritize outreach.

## User pain points

- The retailer cannot prioritize every eligible customer.
- Transaction records are noisy and include activity that is not a qualifying purchase.
- Recency and a single large purchase can be misleading indicators of future behavior.

## Core MVP features

1. Clean and summarize the supplied transaction history using only information available before `observed_until`.
2. Predict repeat-purchase probability and capped 30-day purchase value for every eligible customer.
3. Select exactly the supplied budget of distinct eligible customer IDs.
4. Return the exact action/state structure required by the evaluator and run within its environment limits.
5. Train and compare models using leakage-aware validation, then check the packaged solution with the supplied local checker.

## Additional features

A small demonstration UI is optional and may be considered only after the model and submission package are tested. It is not required by the competition and is not part of the MVP submission.

## Features excluded from the MVP

- Estimating the causal effect of contacting a customer (uplift modeling).
- A production retailer integration, external data, network services, or an online model gateway.
- Customer-ID memorization as a predictive feature.
- A required UI or dashboard.
- Including datasets, prediction CSVs, notebooks, or serialized pickle/joblib models in the submission.

## User workflow

1. The evaluator passes one observation containing the eligible customer roster, budget, dates, and available raw transactions.
2. The solution uses only the supplied observation, respecting its history and observation cutoffs.
3. The solution returns one probability and value prediction per eligible customer and a shortlist of exactly `budget` IDs.
4. Offline, the team fits/tunes using the public training partition, checks generalization on grouped validation, compares with the public practice partition, and packages the runnable inference source and parameters.

## Functional requirements

- **FR-1 — Causal history:** Use no transaction at or after `observed_until`. The supplied v6 observations have a seven-day gap between `observed_until` and `snapshot`; this unavailable tail is unknown demand, not a zero-purchase period. Respect the supplied `history_start`, snapshot, roster, target window, value cap, and budget.
- **FR-2 — Qualifying purchase:** A line qualifies when `CustomerID` and `InvoiceNo` are present, `InvoiceNo` does not begin with `C` or `c`, and both `Quantity` and `UnitPrice` are greater than zero. Do not infer a customer from a description or invoice coincidence.
- **FR-3 — Targets:** For each customer, repeat is 1 iff any qualifying line occurs in `[snapshot, snapshot + 30 days)`. Value is the sum of positive qualifying `Quantity * UnitPrice`, capped at £2,000 per customer and rounded once to pennies with half-up rounding. No qualifying purchase yields value zero. Returns and cancellations do not subtract from this target, though they may be historical features.
- **FR-4 — Duplicate outcomes:** When forming scored outcomes, count identical rows once only if all eight original fields match: `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, and `Country`. Ignore `source_row` for duplicate detection; different rows sharing an invoice remain distinct.
- **FR-5 — Predictions:** Return exactly one prediction per supplied customer, with exactly `probability` and `value`; values must be finite, probability in `[0,1]`, and value in `[0,2000]`.
- **FR-6 — Selection:** Return exactly `budget` unique IDs from the eligible roster. The supplied budget is authoritative: `max(1, floor(number_of_customers / 5))`.
- **FR-7 — Response contract:** Expose `decide(observation, state)` and return exactly an outer object containing `action` and JSON-compatible `state`. The action contains `predictions` and `selected` with no extra action keys.
- **FR-8 — Training and validation:** Fit only on the supplied training partition. Keep customers/worlds/source groups together in local validation folds. Use customer IDs as join keys only. Practice examples are public comparison data; repeated tuning on them risks overfitting.

## Data and evaluation

The source is UCI Online Retail II (2009–2011), licensed under CC BY 4.0; attribute Daqing Chen and the UCI Machine Learning Repository when attribution is needed. The public-expanded-1 packet contains 75 training cases and 51 separate practice cases, with disjoint customer cohorts. Its transaction columns are `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`, and `source_row`. The supplied roster and budget are authoritative; rows that cannot be joined to an eligible customer cannot be assigned to one by inference.

For each batch, the published 100-point domain score is:

- Probability: `40 * (1 - mean Brier error)`.
- Value: `30 * (1 - mean squared capped-value error / 2000²)`.
- Selection: `30 * selected realized value / oracle budget-sized realized value`, or 30 when oracle value is zero.

Batch scores are averaged weighted by customer count. Invalid/missing predictions or an invalid shortlist score zero for that batch. The supplied starter scored about 80.21 on public practice; this is a reference, not a guaranteed score or a user-set minimum. No numerical score threshold has been set.

## Non-functional requirements

- Use Python 3.12.14 and only the published package versions, Python standard library, supplied helpers, and project-owned code. The grader does not install dependencies.
- Runtime: at most 2 CPUs, 2 GiB memory, 120 seconds per response, 1,200 seconds per run, and 1 MiB per JSON frame. The grader has no direct network access; source/public inputs are read-only and temporary storage is writable.
- The source ZIP may contain only `.py`, `.json`, `.txt`, and `.md` files: at most 100 files, 2 MiB per file, 16 MiB uncompressed total, and 32 MiB uploaded. Put `solution.py` and every imported/read helper or parameter file directly at the ZIP root; do not include an enclosing folder or datasets. Pickle/joblib model files are prohibited even though the corresponding packages are available.
- UI is optional and should not delay the tested submission.

## Hackathon constraints and submission process

- Event date: **5 November 2026**. Deliver at least one runnable candidate for the team's test by **14:15 IST**; use test feedback to guide subsequent refinement. Target uploading a tested submission by **17:30 IST**; the hard final cutoff is **17:45 IST**. The team is budgeting about 5.5 hours for a finished product.
- The packet states four official and four practice uploads per stage, with only one evaluation outstanding at a time. A confirmed compatibility failure releases the attempt while submissions are open; manual withdrawal without such a failure keeps the attempt used.
- The portal view shared during planning showed Initial (C) nomination open, Post-twist (T) nomination closed, and no eligible receipt yet. A retained C source is evaluated in T without another upload. Nomination may use an eligible official/retained validation receipt or automatic best eligible validation.
- The packet's `EVENT_RULES.md` lists stage weights of 20% initial validation, 30% post-twist validation, and 50% private final testing, but also labels its schedule/cohorts as a rehearsal. Follow the live portal for any stage-level scoring rules that differ.
- The final deliverable is a submission-ready source ZIP. Detailed archive preparation and portal upload checks will be handled after the model is ready.

## Success criteria

- The source passes the supplied local checker on smoke, training, and practice data.
- The response schema, customer coverage, value/probability ranges, and exact shortlist budget are valid for every checked case.
- Model choices are supported by leakage-aware validation and comparison against the starter; public practice is not repeatedly tuned as if it were a fresh holdout.
- A runnable candidate is available by 14:15 IST and the team's test is run on it before final refinements.
- A tested submission ZIP is ready by 17:30 IST on 5 November, leaving a 15-minute margin before cutoff.
