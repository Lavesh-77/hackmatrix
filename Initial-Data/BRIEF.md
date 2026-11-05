# Applied ML: repeat demand and customer value

A small online retailer has a fixed customer shortlist budget. Use its messy transaction history to estimate, for each eligible customer, (1) the probability of a qualifying purchase in the next 30 days and (2) expected capped purchase value in pounds. Select 20% of the eligible customers in each batch, rounded down, with a minimum of 1. The observation supplies this exact count as budget = max(1, number_of_customers // 5). Return exactly that many distinct eligible customer IDs in selected. This is an offline predictive ranking task; historical outcomes do not establish that contacting someone causes a purchase.

You have six working hours. Audit the data, build causal customer features, train and validate a model, and submit your inference code plus fitted artifacts. The supplied model is a modest, genuinely trained recency/frequency baseline. Any algorithm is allowed. Features, cleaning, calibration, heavy-tail treatment and temporal validation are substantive choices. Customer ID is a join key; memorizing it cannot generalize to disjoint customer cohorts.

## Data and targets

The source is the full UCI Online Retail II workbook (2009–2011). Public training snapshots are in 2010; practice snapshots are in 2011, with different customers. Each observation contains up to 180 days of raw line items for the supplied customers, including duplicates, cancellations, returns, nonpositive prices and missing descriptions. Unknown-customer rows cannot be joined to an eligible customer. Do not infer a customer from a description or invoice coincidence.

A row counts as a purchase only if `CustomerID` and `InvoiceNo` are present, `InvoiceNo` does not begin with either `C` or `c`, and both `Quantity` and `UnitPrice` are greater than zero. When calculating the actual outcomes used for scoring, identical rows are counted only once. Rows are identical only when all eight original fields match: `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID` and `Country`. Ignore `source_row` when checking for duplicates; it only records the row's position in the source data. Different rows sharing an invoice number remain separate. For each customer in `[snapshot,snapshot+30 days)`, repeat=1 iff any qualifying line exists; purchase value is the sum of positive qualifying `Quantity*UnitPrice`, capped at £2,000 per customer and rounded once to pennies with half-up rounding. Returns/cancellations are useful historical evidence but do not subtract from this positive-purchase target. The cap is a fixed public business rule, chosen before heldout evaluation.

History is strictly before observed_until. The supplied customer roster and budget are authoritative. Public training and practice files contain separate labelled examples; fit only on training and evaluate on practice. Official validation and final roles have disjoint customer cohorts. Public and private snapshot dates can overlap within the historical workbook. The supplied starter model is fitted only on the public training partition.

## The 100-point rubric

For batch mean Brier error `B`, mean squared capped-value error `E`, and selected realized value `R`:

* Probability: `40 * (1 - B)`.
* Value: `30 * (1 - E / 2000^2)`.
* Selection: `30 * R / O`, where `O` is the realized value of the best budget-sized customer set. If `O=0`, this component is 30.

The fixed loss normalizers in `scoring.json` are squared target ranges 1 and 2000². They are independent of labels. Affine bounded Brier and squared-value losses are proper: in expectation they reward the true repeat probability and conditional expected capped value. Evaluate models on the published score as well as raw errors. Because the range cap must bound every value loss, value-error marks vary less than selection marks for typical customers. Finite-sample calibration and discrimination both affect Brier error. The final score is the customer-count-weighted average of batch scores; losses and capture are calculated within each batch before averaging. A perfect label/value oracle with optimal selection reaches 100; an honest probabilistic predictor faces irreducible uncertainty. Invalid/missing predictions or an invalid shortlist score 0 for the entire batch. Ties in your selection may be broken however you choose.

## Files and use

`training.json.gz` and `practice.json.gz` contain observations and public `targets` (`CustomerID: [repeat,value]`). Private labels are never present in evaluation observations. `scoring.json` publishes the scoring scales. Each gzip expands to a JSON list of cases.

From this directory run `python train.py` to refit the NumPy linear baseline on your selected public training split, then `python local_check.py --solution starter.py`. Rename `starter.py` to `solution.py` for submission and include `features.py` and `starter_model.json`. The supplied model file already works. Your `solution.py:decide(observation,state)` returns `{"action": {"predictions": ..., "selected": [...]}, "state": {}}`. One call per case; state resets between cases. See SCHEMA.md. Train your model offline and include its saved parameters with your source. Before making predictions, your submitted `solution.py`, together with any included helper files, must clean the supplied raw transaction history and prepare the features your model needs. Use only the supplied observations during prediction. Do not submit a separately cleaned dataset. Returns and cancellations may still be used as historical features, even though they do not count as purchases in the target. The official runner uses the common isolated runtime and common lifecycle rules. Public packets do not include a hidden-case generator or evaluator.

The public checker imports your code on the machine where you run it. Run it only on your own trusted code. It is a convenience for practice formulas, not a security boundary.


## Current data version

Use OBSERVATIONS.md for the v6 data layout and interpretation rules. The action schema and domain outcome score remain unchanged. Implement your own runnable preparation and decisions.

## Expanded training and practice (public-expanded-1)

`training.json.gz` contains 75 ordinary development examples; `practice.json.gz` contains 51 different ordinary examples. See DEVELOPMENT.md for source-group counts, commands, smoke tests and baseline results. Use training for fitting/tuning and practice for comparison after tuning. Practice is public; repeatedly tuning on it makes it development data. Portal practice uses these same practice worlds. Official scoring and private cohorts are unchanged.
