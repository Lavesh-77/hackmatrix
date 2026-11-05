Migrated retail feed contract (staged-operations-v1)

The action is unchanged: predictions for every eligible customer (probability
in [0,1], value in [0,2000] GBP), and exactly budget distinct selected IDs.
Targets remain positive-purchase repeat and capped 30-day GBP spend from the
real source. Returns do not undo purchases; exact duplicate original first
8 source fields count once. No new or synthetic target outcomes are introduced.

transactions retains the original nine-column schema but rows is empty: it is
not a clean alternative feed. raw_feed.events is a table with raw_feed.columns:
source, record_id, revision, delivery_id, payload. payload uses the original
nine transaction columns, subject to the source units and clock below. Each
(source, record_id) identifies one logical historical source row. Highest
revision is the full replacement; retries repeat that version and must not add
purchases. delivery_id identifies a transport delivery, not a purchase. Event
order is not revision order. Distinct record IDs may still be exact source-field
duplicates. Original source_row is provenance, never a spend feature.

raw_feed.sources explicitly gives quantity_units_per_item, price_units_per_gbp,
and clock_offset_minutes. Divide Quantity and UnitPrice by their unit factors;
subtract the offset from transported InvoiceDate to restore the business clock.
Null source fields remain null. These clocks/units and earlier provisional
versions are simulated transport effects on authentic historical rows, not
claims about UCI's original delivery systems. All business-clock timestamps
(snapshot, history_start, observed_until, coverage boundaries) are naive ISO
retail business time; raw local clocks use the stated fixed offsets, with no
inferred time zone or daylight-saving conversion. raw_feed.received_at is the
business-clock receipt time for every delivery and is strictly before snapshot.

availability.sources gives half-open complete_intervals [start,end) per source;
raw_feed routing assigns each customer to a source via raw_feed.customer_sources.
Gaps outside these intervals are UNKNOWN, never evidence of zero purchases or
inactivity. There may be interior gaps and different source cutoffs. Rows outside
the provided original availability or at/after snapshot are never exposed.
observed_until is only the latest available source boundary; it does not make
all earlier history complete. Excerpt records are partial, unlabelled historical
snapshots, not runnable cases or complete histories. No labelled post practice
or prediction recipe is released.

Scoring: probability = 40*(1-Brier), selection = 30*min(1,selected/oracle),
with selection=30 when oracle value is zero. The post/final value component is
30*exp(-MSE/129614.14440376188), with MSE in GBP squared averaged over all
eligible customers. Its fixed scale is the population MSE of the constant mean
predictor over the 2,904 labels in the 75 already-public initial training cases:
mean=155.47428719008266 GBP, S^2=129614.14440376188 GBP^2. The training gzip SHA256
is 4b4986955160569754d2d903fc9c05dd4c102f1fe40cea7567d4ae661d5b3592.
No post/final outcomes or model benchmark were used to choose this scale.
Components retain maxima 40/30/30; invalid actions earn zero. Identical valid
predictions and selections receive identical grades. Initial scoring is unchanged.
