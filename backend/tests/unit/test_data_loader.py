"""Unit tests for DataLoader."""

import json
import os
import tempfile

import pytest

from src.data_loader import DataLoader


VALID_RECORD = {
    "txn_id": "T001",
    "user_id": "U01",
    "timestamp": "2026-02-28T10:00:00",
    "amount": 100.0,
    "category": "shopping",
    "recipient_status": "existing",
    "monthly_budget_remaining": 500.0,
    "device_id": "DEV_A",
    "location": "New York",
    "channel": "web",
}


class TestDataLoaderJSON:
    """Tests for JSON loading."""

    def test_load_valid_json(self, tmp_path):
        path = tmp_path / "txns.json"
        path.write_text(json.dumps([VALID_RECORD]))
        loader = DataLoader()
        txns = loader.load_from_json(str(path))
        assert len(txns) == 1
        assert txns[0].txn_id == "T001"
        assert txns[0].amount == 100.0

    def test_load_multiple_records(self, tmp_path):
        records = [{**VALID_RECORD, "txn_id": f"T{i:03d}"} for i in range(10)]
        path = tmp_path / "txns.json"
        path.write_text(json.dumps(records))
        loader = DataLoader()
        txns = loader.load_from_json(str(path))
        assert len(txns) == 10

    def test_skip_invalid_records(self, tmp_path):
        invalid = {"txn_id": "BAD"}  # missing fields
        path = tmp_path / "txns.json"
        path.write_text(json.dumps([VALID_RECORD, invalid]))
        loader = DataLoader()
        txns = loader.load_from_json(str(path))
        assert len(txns) == 1

    def test_file_not_found(self):
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_from_json("nonexistent.json")

    def test_invalid_json_format(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        loader = DataLoader()
        with pytest.raises(ValueError, match="Invalid JSON"):
            loader.load_from_json(str(path))

    def test_empty_dataset_raises(self, tmp_path):
        bad = {"txn_id": "BAD"}
        path = tmp_path / "empty.json"
        path.write_text(json.dumps([bad]))
        loader = DataLoader()
        with pytest.raises(ValueError, match="No valid transactions"):
            loader.load_from_json(str(path))


class TestDataLoaderCSV:
    """Tests for CSV loading."""

    def test_load_valid_csv(self, tmp_path):
        import csv as csv_mod

        path = tmp_path / "txns.csv"
        with open(path, "w", newline="") as f:
            writer = csv_mod.DictWriter(f, fieldnames=VALID_RECORD.keys())
            writer.writeheader()
            writer.writerow(VALID_RECORD)
        loader = DataLoader()
        txns = loader.load_from_csv(str(path))
        assert len(txns) == 1

    def test_csv_file_not_found(self):
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_from_csv("nonexistent.csv")


class TestDataLoaderAutoDetect:
    """Tests for auto format detection."""

    def test_auto_detect_json(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text(json.dumps([VALID_RECORD]))
        loader = DataLoader()
        txns = loader.load(str(path))
        assert len(txns) == 1

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "data.xml"
        path.write_text("<data/>")
        loader = DataLoader()
        with pytest.raises(ValueError, match="Unsupported"):
            loader.load(str(path))


class TestValidation:
    """Tests for field validation."""

    def test_valid_record(self):
        loader = DataLoader()
        assert loader.validate_transaction(VALID_RECORD) is True

    def test_missing_field(self):
        loader = DataLoader()
        incomplete = {k: v for k, v in VALID_RECORD.items() if k != "amount"}
        assert loader.validate_transaction(incomplete) is False

    def test_negative_amount(self):
        loader = DataLoader()
        record = {**VALID_RECORD, "amount": -10}
        assert loader.validate_transaction(record) is False

    def test_invalid_timestamp(self):
        loader = DataLoader()
        record = {**VALID_RECORD, "timestamp": "not-a-date"}
        assert loader.validate_transaction(record) is False
