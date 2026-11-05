# Inference Contract

> **Contract version:** 1.0 — agreed for the standalone competition submission. This project has no HTTP API; the evaluator imports a Python function directly.

## 1. Contract metadata

| Field | Value |
| --- | --- |
| Project | Which customers will buy again? |
| Contract version | 1.0 (Python callable) |
| Owner | Team Lead (Soorya) |
| Last updated | 2026-11-05 |
| Consumer | Competition evaluator / `local_check.py` |
| Provider | `submission/solution.py`; integration owner Soorya |

## 2. Base URL and environments

| Environment | Base URL / port | Notes |
| --- | --- | --- |
| Local development | Not applicable | The checker imports the submission file and calls `decide` in-process. |
| Evaluation | Not applicable | The isolated evaluator invokes `decide`; no server is started. |
| Frontend origin / CORS | Not applicable | No browser client or HTTP traffic. |

## 3. Interface version

- **Version:** 1.0.
- **Scheme:** Python function-call contract; there are no URL routes or HTTP methods.
- **Required module/function:** `solution.py:decide(observation, state)`.

## 4. Communication format

| Topic | Decision |
| --- | --- |
| Transport | In-process Python call by the evaluator. |
| Data format | JSON-compatible Python dictionaries, lists, strings, finite numbers, booleans, and `None` where schema permits. |
| Observation naming | Use the exact evaluator keys below; transaction column names preserve the source spelling. |
| Dates and times | ISO-formatted retail timestamps. Source workbook timestamps are local-naive; do not add timezone conversions. |
| Identifiers | Customer IDs, invoice numbers, stock codes, countries, and `source_row` are strings. Customer IDs are join keys only. |
| Missing values | Source transaction missing values are JSON `null` / Python `None`. Do not infer missing customer IDs. |
| Pagination | None; each call contains one complete batch. |
| State | State resets between cases; return an empty object `{}`. |

## 5. Authentication

Not required. The evaluator invokes the module directly; there are no credentials, public/private HTTP routes, or tokens.

## 6. HTTP endpoint index

There are **no HTTP endpoints**. The required callable interface below is the complete integration contract. Do not add an HTTP server or invent routes.

## 7. Callable interface details

### `decide(observation, state)`

**Purpose:** Produce probability/value predictions for every eligible customer and select exactly the batch budget.
**Authentication:** None.
**Owner:** Soorya (inference integration), using feature code owned by Lavesh and JSON model parameters owned by Veer.
**Status:** Agreed.

**Input — `observation`**

| Key | Type | Required | Contract |
| --- | --- | --- | --- |
| `case_id` | string | yes | Opaque case identifier; not a predictive feature. |
| `task` | string | yes | Domain task label; not a predictive feature. |
| `snapshot` | ISO timestamp string | yes | Reference date for the target window. |
| `history_start` | ISO timestamp string | yes | Beginning of available history. |
| `observed_until` | ISO timestamp string | yes | Exclusive upper bound for usable history; no row at or after this date may be used. |
| `target_days` | integer | yes | 30. |
| `customers` | array of strings | yes | Authoritative eligible customer IDs. |
| `budget` | integer | yes | Exact selection count, `max(1, floor(len(customers) / 5))`; use supplied value. |
| `value_cap` | number | yes | 2000. |
| `availability` | object | yes | Evaluator-supplied history availability metadata; do not treat unavailable periods as zero demand. |
| `transactions` | object | yes | Contains `columns` and `rows` as defined below. |
| `preparation_contract` | object | optional | May be present in v6 observations; metadata only unless a documented field is required by the task. |

`transactions.columns` is exactly:

```text
["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate",
 "UnitPrice", "CustomerID", "Country", "source_row"]
```

Each `transactions.rows` entry is a nine-element array in that order. `Quantity` and `UnitPrice` are numbers or null; `InvoiceDate` is an ISO timestamp string or null; missing source values are null; identifiers are strings or null. Source row order is preserved. For exact duplicate checks, compare the first eight original fields and ignore `source_row`.

Only `observation` is available to inference. Public training wrappers may contain `targets`, but labels are not part of this input and must never be read from external files during evaluation.

**Input — `state`**

JSON-compatible object. It is reset for every case; this implementation does not need persistent state.

**Success response**

Return exactly an object with top-level keys `action` and `state`; `state` is `{}`. `action` has exactly `predictions` and `selected`:

```json
{
  "action": {
    "predictions": {
      "12345": {"probability": 0.35, "value": 125.20}
    },
    "selected": ["12345"]
  },
  "state": {}
}
```

Contract requirements:

- `predictions` has exactly one key for every supplied customer and no other keys.
- Each prediction has exactly `probability` and `value`; both are finite numbers, not booleans. `probability` is in `[0,1]`; `value` is in `[0,2000]` and estimates expected capped purchase value (zero target when there is no qualifying purchase).
- `selected` contains exactly `budget` unique strings, all members of `customers`.
- There are no additional action keys. The wrapper contains only `action` and `state`.

**Errors and invalid input**

There is no HTTP error response or alternate action schema. The evaluator supplies valid observation records; missing/invalid predictions or an invalid selection score zero for that batch. Do not return an undocumented `error` object or partial action. Feature, response-range, and selection invariants must be tested locally before submission.

## 8. Scoring contract

For each batch, score is:

- Probability: `40 * (1 - mean Brier error)`.
- Value: `30 * (1 - mean squared value error / 2000²)`.
- Selection: `30 * realized value selected / realized value of the oracle budget-sized set`; if oracle value is zero, this component is 30.

Batch scores are averaged weighted by customer count. The outcome window is `[snapshot, snapshot + 30 days)`. A qualifying purchase line requires present `CustomerID` and `InvoiceNo`, invoice not beginning with `C`/`c`, and positive quantity and unit price. Scored duplicate removal uses all eight original transaction fields except `source_row`; returns/cancellations do not subtract from target value. Per-customer value is capped at £2,000 and rounded once to pennies using half-up rounding.

## 9. Database schema

Not applicable. The runtime is stateless per case. The model parameter file is JSON, not a database; no migrations, indexes, or persistent records exist.

## 10. Shared data types

| Type | Fields | Used by |
| --- | --- | --- |
| `Observation` | `case_id`, `task`, `snapshot`, `history_start`, `observed_until`, `target_days`, `customers`, `budget`, `value_cap`, `availability`, `transactions`; optional metadata may be present. | Evaluator input |
| `TransactionRow` | Nine source fields in the exact order listed in §7; missing values are null. | Feature builder |
| `Prediction` | Exactly `probability: finite number [0,1]`, `value: finite number [0,2000]`. | Per-customer output |
| `Action` | Exactly `predictions: {customer_id: Prediction}` and `selected: string[]`. | Evaluator output |
| `DecisionResult` | Exactly `action: Action`, `state: {}`. | `decide` return |

## 11. Integration rules

1. `decide(observation, state)` is the sole evaluator entry point; do not create HTTP endpoints.
2. Match the evaluator fields and output shape exactly; no invented output fields, partial batches, or alternate error shape.
3. Use only transactions before `observed_until` and the supplied customer roster. Do not read labels or bundled datasets at inference.
4. Read model files relative to `__file__`; store numeric model parameters in JSON. Do not use pickle/joblib model files.
5. Keep all source/artifact files at the ZIP root when packaging, and test with the supplied checker on smoke, training, and practice data.
6. No database, CORS, authentication, environment variables, or network access are part of this interface.

## 12. Change log

| Date | Change | Approved by | Affected sides |
| --- | --- | --- | --- |
| 2026-11-05 | Replaced generic HTTP template with evaluator callable contract for the Python-only task. | Team Lead (Soorya) | Feature engineering, model training, inference integration, packaging |
