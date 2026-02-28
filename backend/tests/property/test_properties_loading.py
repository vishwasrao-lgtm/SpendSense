"""Property-based tests for data loading (Properties 1–3)."""

import csv
import json
import os
import tempfile

from hypothesis import given, settings, strategies as st

from src.data_loader import DataLoader
from src.models import REQUIRED_FIELDS

# Use safe ASCII text so CSV round-tripping doesn't corrupt data.
_safe_text = st.from_regex(r"[A-Za-z0-9_]{1,15}", fullmatch=True)


def _valid_record_strategy():
    """Strategy producing valid transaction dicts with finite floats and safe text."""
    from datetime import datetime as dt

    return st.fixed_dictionaries({
        "txn_id": st.uuids().map(str),
        "user_id": _safe_text,
        "timestamp": st.datetimes(
            min_value=dt(2020, 1, 1),
            max_value=dt(2027, 12, 31),
        ).map(lambda d: d.isoformat()),
        "amount": st.floats(
            min_value=0.01, max_value=999999,
            allow_nan=False, allow_infinity=False,
        ),
        "category": st.sampled_from(["groceries", "dining", "entertainment", "shopping", "bills"]),
        "recipient_status": st.sampled_from(["new", "existing"]),
        "monthly_budget_remaining": st.floats(
            min_value=0.0, max_value=50000,
            allow_nan=False, allow_infinity=False,
        ),
        "device_id": _safe_text,
        "location": _safe_text,
        "channel": st.sampled_from(["mobile_app", "web", "pos"]),
    })


# Feature: transaction-intervention-system, Property 1: CSV Data Loading Validation
@given(records=st.lists(_valid_record_strategy(), min_size=1, max_size=5))
@settings(max_examples=100)
def test_csv_loading_preserves_all_valid_records(records):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
        path = f.name

    try:
        loader = DataLoader()
        txns = loader.load_from_csv(path)
        assert len(txns) == len(records)
    finally:
        os.unlink(path)


# Feature: transaction-intervention-system, Property 2: JSON Data Loading Validation
@given(records=st.lists(_valid_record_strategy(), min_size=1, max_size=5))
@settings(max_examples=100)
def test_json_loading_preserves_all_valid_records(records):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(records, f)
        path = f.name

    try:
        loader = DataLoader()
        txns = loader.load_from_json(path)
        assert len(txns) == len(records)
    finally:
        os.unlink(path)


# Feature: transaction-intervention-system, Property 3: Invalid Record Handling
# Only timestamp, amount, and category are truly required (others are auto-filled)
_CORE_FIELDS = ["timestamp", "amount", "category"]


@given(
    valid=_valid_record_strategy(),
    missing_field=st.sampled_from(_CORE_FIELDS),
)
@settings(max_examples=100)
def test_invalid_records_are_skipped(valid, missing_field):
    invalid = {k: v for k, v in valid.items() if k != missing_field}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump([valid, invalid], f)
        path = f.name

    try:
        loader = DataLoader()
        txns = loader.load_from_json(path)
        assert len(txns) == 1
    finally:
        os.unlink(path)

