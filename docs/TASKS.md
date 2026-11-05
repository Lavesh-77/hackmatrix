# Tasks

> **Planning basis:** 5.5 working hours from `docs/PROJECT_SPEC.md`; this is the 5–8 hour band, so the plan assigns three tasks per developer. Deliver a runnable candidate for the team's test by 14:15 IST on 5 November 2026. Use the test results and the 13:15 IST twist for focused refinement. Target a tested submission by 17:30 IST; hard cutoff 17:45 IST.

## 1. How to use this file

- Task IDs are permanent and appear in implementation order.
- Branch names and commit messages use the task ID (for example `feature/T-001-causal-features`, `T-001: build causal features`).
- Every task has exactly one owner and a testable completion criterion.
- Dependencies are task IDs. Start the first unblocked task assigned to you; do not edit another owner's files.
- All tasks begin `Not Started`; report blockers and status changes to the Team Lead.

### Status values

| Status | Meaning |
| --- | --- |
| `Not Started` | Defined and assigned, no work yet |
| `In Progress` | The owner is working on it now |
| `Blocked` | Cannot proceed — waiting on a dependency, decision, or external input |
| `In Review` | Pushed to a branch and waiting for the Team Lead |
| `Completed` | Reviewed, merged, and verified in `main` |

At most two `In Progress` tasks per developer at a time.

### Priorities

| Priority | Meaning |
| --- | --- |
| `High` | Critical path for a valid, competitive submission |
| `Medium` | Needed for changed-condition confidence or final polish |
| `Low` | Optional work only after the MVP is integrated |

## 2. Team

| Member | Role | Owns |
| --- | --- | --- |
| Soorya | Team Lead / inference integration | Shared docs, `submission/solution.py`, packaging, integration, portal submission |
| Veer | Developer / model training and validation | `tools/validate_baseline.py`, `tools/train_model.py`, `submission/starter_model.json` |
| Lavesh | Developer / data cleaning and features | `submission/features.py`, `tests/test_features.py` |
| Fourth member | Research/testing (no agent task owner) | May run the final checklist and report issues if available |

## 3. Milestones

| Milestone | Target | Must be true to move on |
| --- | --- | --- |
| M1 — Runnable test candidate | By 14:15 IST | A working `decide` implementation passes a local smoke check and is handed to the team for its test; do not wait for model polish. |
| M2 — Test feedback and twist refinement | Twist audit starts at 13:15 IST; apply candidate-driven changes after the 14:15 IST handoff | Run the team's test, inspect changed data, prioritize failures, make only justified updates, and re-run relevant checks. |
| M3 — Submission ready | By 17:30 IST | Flat ZIP verified against file/runtime rules; smoke, training, and practice checks pass; eligible official source is submitted/nominated using the live portal controls. |
| M4 — Final cutoff | 17:45 IST | No new final upload is assumed after cutoff; the retained selected source is evaluated according to the portal rules. |

## 4. Task board

| ID | Task | Owner | Role | Priority | Depends on | Status | Done when |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-001 | Build causal transaction feature matrix | Lavesh | Data / features | High | None | Completed | `features.matrix` returns the frozen nine-column finite matrix in roster order and respects all time/customer filters. |
| T-002 | Reproduce starter baseline and grouped validation | Veer | Model / validation | High | None | Completed | Baseline checker runs on all three public files and grouped training validation can be repeated without modifying supplied data. |
| T-003 | Add feature edge-case tests | Lavesh | Data / testing | Medium | T-001 | Completed | Standard-library tests cover duplicate rows, cancellations/returns, cutoff dates, unknown IDs, missing values, and empty histories. |
| T-004 | Fit and compare probability/value heads | Veer | Model / training | High | T-001, T-002, T-003 | Completed | Grouped validation compares the candidate with the starter; final JSON parameters are fit on training only and load without pickle/joblib. |
| T-005 | Implement evaluator inference entry point | Soorya | Integration | High | T-001, T-004 | Completed | `solution.py` loads adjacent JSON, calls the feature matrix, and returns the exact valid `decide` contract for test observations. |
| T-006 | Deliver runnable candidate and run team test | Soorya | Integration / release | High | T-002, T-005 | In Progress | A runnable candidate is available by 14:15 IST, passes a local smoke check, and is run against the team's test with results recorded; then run full local checks and one practice upload if checks pass. |
| T-007 | Audit twist data and triage feature-test feedback | Lavesh | Data / features | Medium | T-003 | Not Started | After 13:15 IST, changed inputs are audited in parallel with candidate preparation; after the 14:15 team test, feature findings are addressed and checked without leakage. |
| T-008 | Evaluate and retune for post-twist conditions | Veer | Model / validation | High | T-004, T-006, T-007 | Not Started | Team-test and changed-condition results are evaluated, any justified model update is saved as JSON, and all predictions remain contract-valid. |
| T-009 | Final integration, ZIP verification, and official nomination | Soorya | Integration / release | High | T-006, T-008 | Not Started | Exact flat ZIP passes the checker on smoke/training/practice and is submitted/nominated by 17:30 IST using the current portal's eligible C/automatic-selection controls. |

## 5. Progress

| Metric | Count |
| --- | --- |
| Total tasks | 9 |
| Not Started | 3 |
| In Progress | 1 |
| Blocked | 0 |
| In Review | 0 |
| Completed | 5 |

## 6. Task detail

### T-001 — Build causal transaction feature matrix

- **Owner:** Lavesh
- **Role:** Data / features
- **Priority:** High
- **Depends on:** None
- **Status:** Completed
- **Files:** `submission/features.py`

**Goal**

Build the frozen feature interface in `docs/ARCHITECTURE.md` from each raw observation.

**Scope**

- Preserve the eligible roster order and join only on supplied customer IDs.
- Use history from `history_start` inclusive to `observed_until` exclusive; use `snapshot` for age calculations.
- De-duplicate exact source rows using the eight original fields, excluding `source_row`.
- Distinguish valid positive purchase lines from returns/cancellations; do not subtract historical returns from positive purchase value.
- Expose `FEATURE_NAMES` and `matrix(observation)` returning a finite `(n_customers, 9)` NumPy matrix in the agreed order.

**Out of scope:** model fitting, reading labels/targets, changing the inference contract, or modifying supplied packet files.

**Acceptance criteria**

- [ ] Feature order and shape match the architecture document.
- [ ] No row at/after `observed_until` or unknown customer affects a customer's features.
- [ ] Output remains finite for empty histories and missing source fields.

### T-002 — Reproduce starter baseline and grouped validation

- **Owner:** Veer
- **Role:** Model / validation
- **Priority:** High
- **Depends on:** None
- **Status:** Completed
- **Files:** `tools/validate_baseline.py`

**Goal**

Establish a reproducible reference and leakage-aware comparison process before changing the model.

**Scope**

- Run the supplied local checker against the supplied starter on smoke, training, and practice files.
- Record component scores and compare with `Initial-Data/baseline_results.json`.
- Create or document grouped folds using the public source/world grouping metadata; do not random-split related examples or tune repeatedly on practice.
- Keep all supplied data and starter files unchanged.

**Acceptance criteria**

- [ ] The commands, scores, and discrepancies from the published baseline are recorded in the task report.
- [ ] The validation procedure is repeatable and groups related source examples together.

### T-003 — Add feature edge-case tests

- **Owner:** Lavesh
- **Role:** Data / testing
- **Priority:** Medium
- **Depends on:** T-001
- **Status:** Completed
- **Files:** `tests/test_features.py`

**Goal**

Prevent cleaning and causal-window regressions before model fitting.

**Acceptance criteria**

- [ ] Standard-library tests cover exact duplicate handling, cancellation/return signals, exclusive `observed_until`, unknown customer IDs, missing fields, and customers with no usable history.
- [ ] Feature outputs preserve every supplied customer and are finite with the exact agreed shape.

### T-004 — Fit and compare probability/value heads

- **Owner:** Veer
- **Role:** Model / training
- **Priority:** High
- **Depends on:** T-001, T-002, T-003
- **Files:** `tools/train_model.py`, `submission/starter_model.json`
- **Status:** Completed

**Goal**

Fit the agreed logistic repeat head and ridge capped-value head, and export portable JSON parameters.

**Acceptance criteria**

- [ ] Fit only on public training examples; evaluate hyperparameters with grouped validation and compare against the starter score.
- [ ] Train final parameters on the allowed training partition and store feature scaling, intercepts, and coefficients in the agreed JSON shape.
- [ ] Candidate predictions are finite and bounded; do not include customer IDs as features or use pickle/joblib serialization.

### T-005 — Implement evaluator inference entry point

- **Owner:** Soorya
- **Role:** Integration
- **Priority:** High
- **Depends on:** T-001, T-004
- **Files:** `submission/solution.py`
- **Status:** Completed

**Goal**

Connect the feature matrix and portable parameters to the evaluator's direct function call.

**Acceptance criteria**

- [ ] `decide(observation, state)` loads its model file relative to `__file__` and returns only `action` and `state`.
- [ ] Every customer receives exactly the two documented numeric predictions; `selected` has exactly the supplied number of unique eligible IDs.
- [ ] Selection is ranked by predicted capped value with the documented deterministic tie-break; state is `{}`.

### T-006 — Deliver runnable candidate and run team test

- **Owner:** Soorya
- **Role:** Integration / release
- **Priority:** High
- **Depends on:** T-002, T-005
- **Files:** `tools/package_submission.py`
- **Status:** In Progress

**Goal**

Give the team a functioning candidate by 14:15 IST so its own test can identify the highest-value fixes before the final submission window.

**Acceptance criteria**

- [ ] A runnable `decide` candidate is available by 14:15 IST and passes the supplied smoke check before handoff.
- [ ] Run the team's test on that candidate and record its results/failures for the refinement tasks; keep team test inputs out of the submission ZIP.
- [ ] Run local checks on training and practice and, after local/team checks pass, make at most one early practice upload; record its receipt/score without repeatedly tuning to practice.
- [ ] Candidate packaging, if used for the team test, keeps `solution.py` at the ZIP root and includes no datasets.

### T-007 — Audit and test post-twist observations

- **Owner:** Lavesh
- **Role:** Data / features
- **Priority:** Medium
- **Depends on:** T-003
- **Status:** Not Started
- **Start condition:** Twist supplement is released at 13:15 IST.

**Goal**

Audit the twist supplement as soon as it is released; then use the team's candidate-test feedback to identify feature defects before final model refinement.

**Acceptance criteria**

- [ ] Changed training/practice files are inspected without using hidden/private labels.
- [ ] Existing observation contract remains respected; any incompatibility is reported before changing shared assumptions.
- [ ] Twist findings are reported while the first candidate is being prepared; feature changes based on the team's test are made after the 14:15 handoff.
- [ ] Feature tests and local checker smoke coverage pass on available changed examples; actionable findings are handed to Veer and Soorya.

### T-008 — Evaluate and retune for post-twist conditions

- **Owner:** Veer
- **Role:** Model / validation
- **Priority:** High
- **Depends on:** T-004, T-006, T-007
- **Status:** Not Started

**Goal**

Use the released changed-condition examples and the team's test results to evaluate robustness and make only evidence-based model updates.

**Acceptance criteria**

- [ ] Compare unchanged and changed-condition metrics using the permitted train/practice split discipline.
- [ ] If a model update is justified, refit and export the same JSON parameter schema; otherwise retain the prior candidate and document why.
- [ ] The updated or retained candidate passes output bounds and fixed-budget selection checks.

### T-009 — Final integration, ZIP verification, and official nomination

- **Owner:** Soorya
- **Role:** Integration / release
- **Priority:** High
- **Depends on:** T-006, T-008
- **Files:** `submission/`, `tools/package_submission.py`
- **Status:** Not Started

**Goal**

Freeze and submit the best eligible source with time for a final smoke check.

**Acceptance criteria**

- [ ] Re-run the local checker on smoke, training, and practice using the exact final source.
- [ ] Verify ZIP root layout, allowed extensions, file counts/sizes, no datasets, and relative artifact loading.
- [ ] Submit/nominate an eligible official C source using the live portal controls by 17:30 IST; T nomination is currently shown closed and retained C source is evaluated in T without another upload.
- [ ] Record receipt/compatibility status, selected automatic/manual nomination mode, remaining attempts, and any blocker before the 17:45 IST cutoff.

## 7. Handoff notes

- 2026-11-05: No HTTP endpoints, database, environment variables, or required UI. The callable contract is in `docs/API_CONTRACT.md`; the nine-column internal feature schema and JSON model schema are in `docs/ARCHITECTURE.md`.
- Do not edit `Initial-Data/` or `Submission-Format/`; treat both as supplied reference packets.
