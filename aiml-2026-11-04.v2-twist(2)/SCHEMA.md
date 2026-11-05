# JSON contract

Observation keys: `case_id` (opaque string), `task`, `snapshot` (ISO timestamp), `history_start`, `observed_until`, `target_days=30`, `customers` (eligible ID strings), `budget` (exact count, `max(1,floor(n/5))`), `value_cap=2000`, `availability` (history availability metadata), and `transactions`.

`transactions.columns` is `[InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country,source_row]`; every row follows this order. Identifiers are strings; missing values are JSON null. Quantity/price are numbers. InvoiceDate is an ISO timestamp. The original Excel timestamps have no timezone; treat arithmetic as local-naive retail time. Line rows retain original source order within timestamp, and source_row is a global row identifier as a string: one plus the sequential data-row index across both worksheets, excluding headers. Customer IDs have no predictive numeric meaning.

Action (no extra action keys):

```json
{"predictions":{"12345":{"probability":0.35,"value":125.20}},"selected":["12345"]}
```

There must be exactly one prediction for every supplied customer and no others, with exactly `probability` and `value`. Probability must be finite in `[0,1]`, expected capped value finite in `[0,2000]`; booleans are rejected. `selected` must contain exactly `budget` unique eligible customer IDs. Selecting someone does not change their true outcome. No partial batches, additional steps or deferred decisions. The outer response must contain `action` and `state`; use an empty object `{}` for state. Keep each JSON request/response below 1 MiB; source/artifacts below 16 MiB.

The labeled public wrapper contains id, cluster_id, targets and observation; legacy scales are optional. Only observation is passed to inference. Source dates can correlate disjoint customers; group local validation by customer and snapshot.
