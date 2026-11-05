"""Causal transaction features used by the inference model."""

from datetime import datetime, timedelta
import math

import numpy as np


FEATURE_NAMES = (
    "recency",
    "invoice_frequency",
    "recent_value",
    "older_value",
    "basket_value",
    "return_ratio",
    "cadence",
    "tenure",
    "observed_gap",
)

_ROW_FIELDS = 8
_FEATURE_COUNT = len(FEATURE_NAMES)
_DEFAULT_RECENCY = 180.0
_DEFAULT_CADENCE = 90.0


def _parse_datetime(value):
    """Parse an ISO timestamp, returning None for missing or invalid values."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _finite_number(value):
    """Return a finite float for numeric source values, otherwise None."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _prepare_raw_feed(observation):
    """Resolve and normalize staged migrated-feed events into source rows."""
    feed = observation["raw_feed"]
    columns = feed.get("columns", [])
    column_indexes = {name: index for index, name in enumerate(columns)}
    required = ("source", "record_id", "revision", "payload")
    if any(name not in column_indexes for name in required):
        return []

    source_indexes = {name: index for index, name in enumerate(columns)}
    sources = feed.get("sources", {})
    # Select the full replacement with the greatest revision for each logical
    # row. Delivery retries at that revision do not create additional activity.
    latest = {}
    for event in feed.get("events", []):
        try:
            source = event[source_indexes["source"]]
            record_id = event[source_indexes["record_id"]]
            revision = _finite_number(event[source_indexes["revision"]])
            payload = event[source_indexes["payload"]]
        except (IndexError, TypeError):
            continue
        if source not in sources or record_id is None or revision is None:
            continue
        key = (source, record_id)
        current = latest.get(key)
        if current is None or revision > current[0]:
            latest[key] = (revision, payload)

    customer_sources = feed.get("customer_sources", {})
    availability = observation.get("availability", {}).get("sources", {})
    history_start = _parse_datetime(observation.get("history_start"))
    observed_until = _parse_datetime(observation.get("observed_until"))
    snapshot = _parse_datetime(observation.get("snapshot"))
    normalized = []
    seen = set()

    for (source, _record_id), (_revision, payload) in latest.items():
        if not isinstance(payload, (list, tuple)) or len(payload) < _ROW_FIELDS + 1:
            continue
        row = list(payload[:_ROW_FIELDS + 1])
        customer_id = row[6]
        if customer_id is None or customer_sources.get(customer_id) != source:
            continue

        metadata = sources[source]
        quantity_factor = _finite_number(metadata.get("quantity_units_per_item"))
        price_factor = _finite_number(metadata.get("price_units_per_gbp"))
        offset_minutes = _finite_number(metadata.get("clock_offset_minutes"))
        if (
            quantity_factor is None or quantity_factor <= 0
            or price_factor is None or price_factor <= 0
            or offset_minutes is None
        ):
            continue

        quantity = _finite_number(row[3])
        price = _finite_number(row[5])
        transaction_date = _parse_datetime(row[4])
        if quantity is not None:
            row[3] = quantity / quantity_factor
        if price is not None:
            row[5] = price / price_factor
        if transaction_date is None:
            continue
        transaction_date -= timedelta(minutes=offset_minutes)
        row[4] = transaction_date.isoformat()

        # Only complete source intervals support interpreting this history.
        source_availability = availability.get(source, {})
        in_complete_interval = False
        for interval in source_availability.get("complete_intervals", []):
            start = _parse_datetime(interval.get("start"))
            end = _parse_datetime(interval.get("end"))
            if start is not None and end is not None and start <= transaction_date < end:
                in_complete_interval = True
                break
        if not in_complete_interval:
            continue
        if history_start is not None and transaction_date < history_start:
            continue
        if observed_until is not None and transaction_date >= observed_until:
            continue
        if snapshot is not None and transaction_date >= snapshot:
            continue

        # Duplicate identity is the eight restored original source fields;
        # source_row is provenance and does not distinguish duplicate lines.
        identity = tuple(row[:_ROW_FIELDS])
        try:
            if identity in seen:
                continue
            seen.add(identity)
        except TypeError:
            continue
        normalized.append(row)

    return normalized


def _raw_feed_observed_gaps(observation):
    """Return each customer's gap from the end of known source coverage."""
    feed = observation["raw_feed"]
    snapshot = _parse_datetime(observation.get("snapshot"))
    history_start = _parse_datetime(observation.get("history_start"))
    observed_until = _parse_datetime(observation.get("observed_until"))
    if snapshot is None or history_start is None:
        return {}

    sources = observation.get("availability", {}).get("sources", {})
    customer_sources = feed.get("customer_sources", {})
    gaps = {}
    for customer_id in observation["customers"]:
        source = customer_sources.get(customer_id)
        intervals = sources.get(source, {}).get("complete_intervals", [])
        coverage_ends = []
        for interval in intervals:
            end = _parse_datetime(interval.get("end"))
            if end is None:
                continue
            end = min(end, snapshot)
            if observed_until is not None:
                end = min(end, observed_until)
            if end > history_start:
                coverage_ends.append(end)
        latest_end = max(coverage_ends) if coverage_ends else history_start
        gaps[customer_id] = (snapshot - latest_end).total_seconds() / 86400.0
    return gaps


def matrix(observation):
    """Build the frozen nine-column feature matrix in roster order.

    Only exact duplicate transaction rows (the first eight source fields) are
    removed. Rows must have a customer in the supplied roster and a valid date
    in the available history interval to affect any feature.
    """
    customers = observation["customers"]
    snapshot = datetime.fromisoformat(observation["snapshot"])
    history_start = datetime.fromisoformat(observation["history_start"])
    observed_until = datetime.fromisoformat(observation["observed_until"])

    grouped = {customer_id: [] for customer_id in customers}
    seen_rows = set()

    rows = (
        _prepare_raw_feed(observation)
        if "raw_feed" in observation
        else observation["transactions"]["rows"]
    )
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < _ROW_FIELDS + 1:
            continue

        # source_row is intentionally excluded from duplicate identity.
        original_fields = tuple(row[:_ROW_FIELDS])
        try:
            if original_fields in seen_rows:
                continue
            seen_rows.add(original_fields)
        except TypeError:
            # Source fields are scalar by contract. Ignore malformed rows
            # rather than letting an unhashable value disrupt the whole batch.
            continue

        customer_id = row[6]
        if customer_id not in grouped:
            continue

        transaction_date = _parse_datetime(row[4])
        if transaction_date is None:
            continue
        try:
            if not history_start <= transaction_date < observed_until:
                continue
        except TypeError:
            # The source contract uses local-naive timestamps. Incompatible
            # or timezone-aware malformed dates cannot safely pass the filter.
            continue

        grouped[customer_id].append((row, transaction_date))

    rows_by_customer = []
    observed_gap = (snapshot - observed_until).total_seconds() / 86400.0
    customer_gaps = (
        _raw_feed_observed_gaps(observation)
        if "raw_feed" in observation
        else {}
    )
    for customer_id in customers:
        invoice_values = {}
        invoice_ages = {}
        recent_value = 0.0
        older_value = 0.0
        return_value = 0.0

        for row, transaction_date in grouped[customer_id]:
            invoice_no = row[0]
            quantity = _finite_number(row[3])
            unit_price = _finite_number(row[5])
            if quantity is None or unit_price is None:
                continue

            amount = quantity * unit_price
            if not math.isfinite(amount):
                continue

            is_cancellation = str(invoice_no).upper().startswith("C")
            if quantity < 0 or is_cancellation:
                return_value += abs(amount)
                continue

            # Positive purchases require a present invoice and positive
            # quantity and unit price. Returns never reduce purchase totals.
            if not isinstance(invoice_no, str) or quantity <= 0 or unit_price <= 0:
                continue

            age = (snapshot - transaction_date).total_seconds() / 86400.0
            invoice_values[invoice_no] = invoice_values.get(invoice_no, 0.0) + amount
            # The smallest age is the latest positive line date for an invoice.
            invoice_ages[invoice_no] = min(age, invoice_ages.get(invoice_no, math.inf))
            if age <= 30.0:
                recent_value += amount
            else:
                older_value += amount

        total_value = sum(invoice_values.values())
        ages = sorted(invoice_ages.values())
        gaps = [later - earlier for earlier, later in zip(ages, ages[1:])]
        cadence = sum(gaps) / len(gaps) if gaps else _DEFAULT_CADENCE

        rows_by_customer.append(
            [
                min(ages) if ages else _DEFAULT_RECENCY,
                len(invoice_values),
                recent_value,
                older_value,
                total_value / max(1, len(invoice_values)),
                return_value / max(1.0, total_value),
                cadence,
                max(ages) if ages else _DEFAULT_RECENCY,
                customer_gaps.get(customer_id, observed_gap),
            ]
        )

    if not rows_by_customer:
        return np.empty((0, _FEATURE_COUNT), dtype=np.float64)

    result = np.asarray(rows_by_customer, dtype=np.float64).reshape(
        len(customers), _FEATURE_COUNT
    )
    if not np.isfinite(result).all():
        raise ValueError("Invalid causal features")
    return result
