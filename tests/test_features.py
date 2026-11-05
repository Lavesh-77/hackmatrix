"""Edge-case tests for causal transaction feature generation."""

import unittest

import numpy as np

from submission.features import FEATURE_NAMES, matrix


def make_observation(customers=None, rows=None):
    return {
        "customers": ["A", "B"] if customers is None else customers,
        "snapshot": "2020-02-01T00:00:00",
        "history_start": "2020-01-01T00:00:00",
        "observed_until": "2020-01-25T00:00:00",
        "transactions": {"rows": [] if rows is None else rows},
    }


def transaction(
    invoice="100",
    stock="item",
    description="product",
    quantity=1,
    date="2020-01-20T00:00:00",
    price=10,
    customer="A",
    country="GB",
    source_row="row-1",
):
    return [invoice, stock, description, quantity, date, price, customer, country, source_row]


class FeatureMatrixTests(unittest.TestCase):
    def test_migrated_feed_revisions_units_clock_and_exact_duplicates(self):
        observation = make_observation(customers=["A"])
        observation.update(
            {
                "snapshot": "2020-02-01T00:00:00",
                "history_start": "2020-01-01T00:00:00",
                "observed_until": "2020-01-25T00:00:00",
                "availability": {
                    "sources": {
                        "store": {
                            "complete_intervals": [
                                {"start": "2020-01-01T00:00:00", "end": "2020-01-25T00:00:00"}
                            ]
                        },
                        "other": {
                            "complete_intervals": [
                                {"start": "2020-01-01T00:00:00", "end": "2020-01-25T00:00:00"}
                            ]
                        },
                    }
                },
                "raw_feed": {
                    "columns": ["source", "record_id", "revision", "delivery_id", "payload"],
                    "customer_sources": {"A": "store"},
                    "sources": {
                        "store": {
                            "quantity_units_per_item": 1,
                            "price_units_per_gbp": 100,
                            "clock_offset_minutes": 60,
                        },
                        "other": {
                            "quantity_units_per_item": 1,
                            "price_units_per_gbp": 1,
                            "clock_offset_minutes": 0,
                        },
                    },
                    "events": [
                        # Latest revision replaces the earlier, higher-price version.
                        ["store", "r0", 1, 0, transaction(price=2000, date="2020-01-20T11:00:00")[:8] + ["row-1"]],
                        ["store", "r0", 2, 1, transaction(price=1000, date="2020-01-20T11:00:00")[:8] + ["row-1"]],
                        # A retry of revision 2 is not another line.
                        ["store", "r0", 2, 2, transaction(price=1000, date="2020-01-20T11:00:00")[:8] + ["row-1"]],
                        # A different record ID with identical source fields is deduplicated.
                        ["store", "r1", 1, 3, transaction(price=1000, date="2020-01-20T11:00:00")[:8] + ["row-2"]],
                        # Outside coverage, despite falling inside the broad history dates.
                        ["store", "r2", 1, 4, transaction(invoice="gap", date="2020-01-10T00:00:00")[:8] + ["row-3"]],
                        # Routed to a different source, so this customer row is ignored.
                        ["other", "r3", 1, 5, transaction(invoice="misrouted")[:8] + ["row-4"]],
                    ],
                },
            }
        )
        # Make the sole complete interval exclude the January 10 event.
        observation["availability"]["sources"]["store"]["complete_intervals"] = [
            {"start": "2020-01-15T00:00:00", "end": "2020-01-25T00:00:00"}
        ]

        result = matrix(observation)[0]

        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 10)
        self.assertEqual(result[4], 10)
        self.assertAlmostEqual(result[0], 11 + 14 / 24)  # Restored to 10:00 business time.

    def test_migrated_feed_uses_customer_source_route_and_interval_gaps(self):
        observation = make_observation(customers=["A"])
        observation.update(
            {
                "availability": {"sources": {"store": {"complete_intervals": []}}},
                "raw_feed": {
                    "columns": ["source", "record_id", "revision", "delivery_id", "payload"],
                    "customer_sources": {"A": "store"},
                    "sources": {
                        "store": {
                            "quantity_units_per_item": 1,
                            "price_units_per_gbp": 1,
                            "clock_offset_minutes": 0,
                        }
                    },
                    "events": [
                        ["store", "r0", 1, 0, transaction()],
                    ],
                },
            }
        )

        result = matrix(observation)
        self.assertEqual(result[0, 1], 0)
        self.assertEqual(result[0, 8], 31)  # No complete source coverage in history.
        self.assertTrue(np.isfinite(result).all())

    def test_duplicate_rows_ignore_source_row_but_keep_distinct_lines(self):
        first_line = transaction(quantity=2, source_row="row-1")
        exact_duplicate = transaction(quantity=2, source_row="row-2")
        same_invoice_different_stock = transaction(
            stock="another-item", quantity=1, price=5, source_row="row-3"
        )

        result = matrix(
            make_observation(customers=["A"], rows=[
                first_line,
                exact_duplicate,
                same_invoice_different_stock,
            ])
        )

        self.assertEqual(result.shape, (1, 9))
        self.assertEqual(result[0, 1], 1)  # One distinct invoice.
        self.assertEqual(result[0, 2], 25)  # Exact repeat counted once.
        self.assertEqual(result[0, 4], 25)

    def test_returns_and_cancellations_do_not_reduce_purchase_features(self):
        rows = [
            transaction(invoice="100", quantity=2, price=10),
            transaction(invoice="101", quantity=-1, price=10, source_row="row-2"),
            transaction(invoice="c102", quantity=1, price=50, source_row="row-3"),
        ]

        result = matrix(make_observation(customers=["A"], rows=rows))[0]

        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 20)
        self.assertEqual(result[4], 20)
        self.assertEqual(result[5], 3)  # (10 return + 50 cancellation) / 20.

    def test_history_start_is_inclusive_and_observed_until_is_exclusive(self):
        rows = [
            transaction(invoice="before", date="2020-01-01T00:00:00", source_row="row-1"),
            transaction(invoice="outside-start", date="2019-12-31T23:59:59", source_row="row-2"),
            transaction(invoice="at-cutoff", date="2020-01-25T00:00:00", source_row="row-3"),
        ]

        result = matrix(make_observation(customers=["A"], rows=rows))[0]

        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 0)
        self.assertEqual(result[3], 10)
        self.assertEqual(result[0], 31)

    def test_missing_fields_and_unknown_customers_are_safe(self):
        rows = [
            transaction(description=None, quantity=1, price=5, source_row="valid"),
            transaction(invoice="missing-quantity", quantity=None, source_row="no-quantity"),
            transaction(invoice="missing-price", price=None, source_row="no-price"),
            transaction(invoice=None, source_row="no-invoice"),
            transaction(invoice="missing-date", date=None, source_row="no-date"),
            transaction(invoice="unknown", customer="NOT-ELIGIBLE", source_row="unknown"),
            transaction(invoice="no-customer", customer=None, source_row="no-customer"),
        ]

        result = matrix(make_observation(customers=["B", "A"], rows=rows))

        self.assertEqual(result.shape, (2, 9))
        self.assertEqual(result[0, 1], 0)  # B stays in roster order, with no history.
        self.assertEqual(result[1, 1], 1)  # Missing description is allowed.
        self.assertEqual(result[1, 2], 5)
        self.assertTrue(np.isfinite(result).all())

    def test_empty_history_and_empty_roster_have_valid_shapes_and_defaults(self):
        result = matrix(make_observation(customers=["A", "B"]))

        self.assertEqual(result.shape, (2, 9))
        self.assertEqual(tuple(FEATURE_NAMES), (
            "recency",
            "invoice_frequency",
            "recent_value",
            "older_value",
            "basket_value",
            "return_ratio",
            "cadence",
            "tenure",
            "observed_gap",
        ))
        np.testing.assert_allclose(
            result,
            [
                [180, 0, 0, 0, 0, 0, 90, 180, 7],
                [180, 0, 0, 0, 0, 0, 90, 180, 7],
            ],
        )
        empty_result = matrix(make_observation(customers=[]))
        self.assertEqual(empty_result.shape, (0, 9))
        self.assertTrue(np.isfinite(result).all())


if __name__ == "__main__":
    unittest.main()
