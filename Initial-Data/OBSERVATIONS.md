# Observation guide — frozen v6 rehearsal

Submit solution.py with decide(observation, state), returning action and state.
Preparation, feature engineering and decisions belong in that runnable pipeline.
You may compare algorithms and use any causal strategy consistent with the action
schema. Source examples and local checks are development aids;
only portal submissions reveal validation performance. Final results stay private
to organizers. See EVENT_RULES.md for limits, schedule and 20/30/50 phase weights.

Predict repeat demand and capped next-30-day value, then select the required number of customers.
The transaction table uses the columns in SCHEMA.md. The 180-day history ends at the snapshot;
the current scheduled extract is complete only up to observed_until, seven days earlier.
The unavailable tail is unknown demand, not a period with zero purchases. Customers,
history_start, snapshot, target_days and budget are authoritative. Distinguish cancellations,
missing customer IDs, repeated rows and valid equal-value purchases. Public examples include
targets for your own local split. The supplied baseline feature code and model are examples;
you may change features, preprocessing and the learning algorithm. The supplied baseline model is fitted only on the public training partition. This remains a historical rehearsal.
