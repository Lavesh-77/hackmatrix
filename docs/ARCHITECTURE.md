# Architecture

> **Status:** Planned for the standalone Applied ML submission. This architecture follows `docs/PROJECT_SPEC.md` and the explicit organizer runtime/submission constraints.

## 1. Technology stack

### Frontend

None in the MVP. The evaluator calls the Python function directly. A Streamlit demonstration dashboard is an optional stretch only after the submission pipeline is working; it is not included in the portal ZIP.

### Backend

No HTTP server or API service. The submission is a Python 3.12.14 module exposing `solution.py:decide(observation, state)`. Offline training and validation use Python with NumPy and scikit-learn from the approved environment. Inference uses the submitted Python source, NumPy, and a JSON parameter file; estimator objects are not serialized.

### Database

None. The evaluator supplies each observation and resets state per case. Public training data is read locally during development; the submission contains only source and model parameters.

### External APIs and services

None. Evaluation has no direct network access. No gateway, credentials, paid services, or third-party data are required.

### Local development tooling

- Python 3.12.14.
- Approved packages: `numpy==2.3.4`, `pandas==2.3.3`, `scipy==1.18.1`, `scikit-learn==1.7.2`, `joblib==1.6.0`, `cloudpickle==3.1.2`, `python-dateutil==3.0.0`, `pytz==2026.6`, `tzdata==2026.6`, `six==1.17.0`, and `threadpoolctl==3.7.0`. Import scikit-learn as `sklearn` and python-dateutil as `dateutil`. The project needs NumPy and scikit-learn; do not install or bundle any additional third-party package.
- Linux/Docker isolated evaluation; 2 CPUs, 2 GiB RAM, no direct network, read-only source/public files, writable temporary storage; 120 seconds per response, 1,200 seconds per run, 1 MiB JSON frame.
- Supplied `Initial-Data/local_check.py`, `training.json.gz`, `practice.json.gz`, `smoke.json.gz`, and scoring/data documentation.
- Standard-library `unittest` for focused feature and contract tests.
- Run checks from the repository root, for example: `python Initial-Data/local_check.py --solution submission/solution.py --data Initial-Data/smoke.json.gz`.
- Do not modify or overwrite the supplied `Initial-Data/` or `Submission-Format/` packets. Training scripts write generated JSON parameters under `submission/`.

## 2. System overview

Offline development fits a compact repeat-probability head and capped-value head on the public training partition, validates them with grouped splits, and exports numeric parameters as JSON. During evaluation, the platform passes an observation to `submission/solution.py`; it builds causal features from the raw transaction rows, loads its adjacent JSON parameters, and returns the exact action/state contract. There is no browser, server, database, or network call.

```text
Public training data ──> tools/train_model.py ──> submission/starter_model.json
                                                      │
Evaluator observation ──> submission/solution.py ──> submission/features.py ──> action JSON
                                                      │
Local checker + practice data ──> score and contract verification
```

## 3. Component responsibilities

| Component | Responsibility | Owner |
| --- | --- | --- |
| `submission/features.py` | Clean/join raw history to the authoritative roster and create causal customer features. | Lavesh |
| `tools/validate_baseline.py` | Reproduce the supplied baseline and establish grouped validation without modifying supplied files. | Veer |
| `tools/train_model.py` | Fit and compare model heads with grouped validation; export JSON coefficients/scales. | Veer |
| `submission/solution.py` | Load parameters relative to `__file__`, invoke feature generation, validate bounds, and form the fixed-budget action. | Soorya |
| `tests/` and supplied local checker | Verify feature edge cases, output contract, and public score. | Assigned per task; Soorya integrates |
| `tools/package_submission.py` | Build and verify a flat, size-limited ZIP from submission files only. | Soorya |

## 4. Project folder structure

```text
docs/                       Shared product, architecture, contract, and task docs
roles/                      Team role instructions
Initial-Data/               Supplied read-only data, starter, checker, and rules
Submission-Format/          Supplied read-only example package
submission/                 Final inference source and JSON parameters
  solution.py
  features.py
  starter_model.json
  README.md                  Optional; included only if useful
tools/                      Offline fitting, validation, and ZIP tooling (not required in ZIP)
  validate_baseline.py
  train_model.py
  package_submission.py
tests/                      Standard-library focused tests (not required in ZIP)
```

The ZIP is assembled from the contents of `submission/`, so its root contains `solution.py`, every imported/read helper and parameter, and optionally `README.md`; it does not contain the `submission/` directory itself. Training data and development tools are never included.

## 5. Data flow

1. Offline fitting reads only the public training partition. Validation folds keep documented source/world groups together; the practice set is used as a limited final public comparison, not repeatedly tuned.
2. The evaluator passes the observation roster, dates, budget, and raw transactions to `decide`; no labels are passed to inference.
3. Feature generation joins only on supplied customer IDs, filters rows to the available history before `observed_until`, and distinguishes positive purchases from returns/cancellations. Exact repeated source rows are de-duplicated for aggregates using the eight original fields, excluding `source_row`.
4. The model predicts repeat probability and unconditional capped purchase value for each roster customer. Its value estimate is formed from repeat probability and a conditional amount estimate; predictions are bounded to the contract ranges.
5. The selector ranks predicted capped value and returns exactly the supplied number of distinct eligible customer IDs.

### Frozen feature and parameter interface

`submission/features.py` exposes `FEATURE_NAMES` and `matrix(observation)`. The matrix is a finite NumPy `float64` array with shape `(len(observation["customers"]), 9)` in exactly the roster order. The frozen feature order reuses the supplied baseline contract:

| Zero-based column | Feature | Definition |
| --- | --- | --- |
| 0 | `recency` | Days from `snapshot` to the latest qualifying positive-purchase line; use 180 when none exists. |
| 1 | `invoice_frequency` | Count of distinct invoice numbers containing qualifying positive-purchase lines. |
| 2 | `recent_value` | Sum of qualifying positive line values with age at most 30 days before `snapshot`. |
| 3 | `older_value` | Sum of qualifying positive line values with age greater than 30 days before `snapshot`. |
| 4 | `basket_value` | Total qualifying positive line value divided by `max(1, invoice_frequency)`. |
| 5 | `return_ratio` | Absolute value of historical lines marked by negative quantity or a C/c invoice prefix, divided by `max(1, total qualifying positive value)`. |
| 6 | `cadence` | Mean days between distinct qualifying purchase invoice dates; use 90 when fewer than two dates exist. |
| 7 | `tenure` | Days from the oldest qualifying positive-purchase line to `snapshot`; use 180 when none exists. |
| 8 | `observed_gap` | Days between `observed_until` and `snapshot`. |

The baseline log-transforms zero-based columns 1–4 with `log1p(max(0, x))`; training-fitted means and scales are stored in the JSON model and reused at inference. Invalid/missing dates do not contribute to time-based features. Return/cancellation lines may contribute to `return_ratio` but never to positive purchase totals.

The JSON model contains `feature_names`, `mean` (nine numbers), `scale` (nine positive numbers), `repeat` (`intercept` plus nine `coefficients`), and `value` (`intercept` plus nine `coefficients`). `repeat` is fit as logistic regression. `value` is ridge regression on `log1p` capped purchase amounts among repeat buyers, with larger positive amounts receiving square-root target weights. Inference applies the sigmoid, converts the value head with clipped `expm1`, and multiplies by repeat probability to estimate unconditional capped value. It selects descending predicted value with customer ID ascending as a deterministic tie-break. Both heads are exported as plain JSON numeric parameters, never as a serialized estimator.

## 6. Authentication and authorization

Not required. There is no application server, user account, private API, or external service. The evaluator invokes the submitted function in an isolated runtime.

## 7. Architecture decisions and rationale

| Decision | Alternatives considered | Why we chose it | Date |
| --- | --- | --- | --- |
| Single offline Python submission; no web app or service | Conventional frontend/backend/API deployment | The evaluator invokes a Python function directly; extra infrastructure cannot improve the task score and risks the deadline. | 2026-11-05 |
| Use compact linear model heads: scikit-learn logistic regression for repeat and ridge regression for conditional log amount; combine their outputs for expected capped value and export numeric JSON parameters | Pickle/joblib estimators, large tree ensembles, or fitting during inference | Approved libraries support offline fitting, while JSON parameters are permitted, portable, small, and do not require model deserialization in the isolated runner. The two-part head modestly improves grouped selection capture and value error over the direct value ridge baseline. | 2026-11-05 |
| Keep training and packaging tools outside `submission/`; keep submission files flat inside the ZIP | Bundle datasets/notebooks or zip an enclosing folder | Meets the no-dataset/no-subfolder constraints and keeps the inference artifact small. | 2026-11-05 |
| No database, environment variables, authentication, or external APIs | Local persistence and hosted services | Observations and parameters are supplied directly; none of these services are required. | 2026-11-05 |

## 8. Technical risks and limitations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Leakage from records at/after `observed_until` or from random splits across related examples | Inflated local validation and poor hidden-cohort performance | Enforce the cutoff in feature code and use grouped validation based on the supplied source/world grouping metadata. |
| Seven-day unavailable tail and messy duplicate/return/cancellation rows | Incorrect recency, frequency, or value features | Treat the tail as unknown; test exact deduplication and purchase predicates; preserve returns/cancellations only as historical evidence. |
| Small public sample and repeated practice tuning | Overfit model selection | Keep an untouched grouped training holdout and limit practice comparisons; compare against the starter baseline. |
| Heavy-tailed capped value and narrow time budget | Unstable value predictions or incomplete integration | Deliver a runnable candidate by 14:15 IST for the team's test; use its results to prioritize fixes, bound predictions, compare against the starter, and reserve time for post-twist retesting. |
| JSON artifact/path/ZIP contract errors or runtime overrun | Compatibility failure or lost attempt | Read artifacts relative to `__file__`; test the exact flat ZIP; run the supplied checker on smoke, training, and practice before upload. |

## 9. Environment variables

None. The submission needs no secrets, service URLs, or configurable runtime environment values.
