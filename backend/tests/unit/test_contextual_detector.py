"""Unit tests for ContextualDetector."""

from datetime import datetime, timedelta

import pytest

from src.detectors import ContextualDetector
from tests.helpers import make_transaction


class TestNewRecipient:
    """Tests for new recipient detection."""

    def test_flags_new_recipient(self):
        txn = make_transaction(recipient_status="new")
        flags = ContextualDetector().detect(txn, [])
        assert any(f.rule_name == "new_recipient" for f in flags)

    def test_no_flag_existing_recipient(self):
        txn = make_transaction(recipient_status="existing")
        flags = ContextualDetector().detect(txn, [])
        assert not any(f.rule_name == "new_recipient" for f in flags)


class TestFrequencyBurst:
    """Tests for frequency burst detection."""

    def test_flags_three_in_ten_minutes(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [
            make_transaction(txn_id="T1", timestamp=now - timedelta(minutes=5)),
            make_transaction(txn_id="T2", timestamp=now - timedelta(minutes=3)),
        ]
        txn = make_transaction(txn_id="T3", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert any(f.rule_name == "frequency_burst" for f in flags)

    def test_no_flag_two_in_ten_minutes(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [
            make_transaction(txn_id="T1", timestamp=now - timedelta(minutes=5)),
        ]
        txn = make_transaction(txn_id="T2", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert not any(f.rule_name == "frequency_burst" for f in flags)

    def test_no_flag_outside_ten_minutes(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [
            make_transaction(txn_id="T1", timestamp=now - timedelta(minutes=15)),
            make_transaction(txn_id="T2", timestamp=now - timedelta(minutes=12)),
        ]
        txn = make_transaction(txn_id="T3", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert not any(f.rule_name == "frequency_burst" for f in flags)


class TestDeviceAnomaly:
    """Tests for device anomaly detection."""

    def test_flags_new_device(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [make_transaction(device_id="DEV_A", timestamp=now - timedelta(hours=1))]
        txn = make_transaction(device_id="DEV_UNKNOWN", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert any(f.rule_name == "device_anomaly" for f in flags)

    def test_no_flag_known_device(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [make_transaction(device_id="DEV_A", timestamp=now - timedelta(hours=1))]
        txn = make_transaction(device_id="DEV_A", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert not any(f.rule_name == "device_anomaly" for f in flags)

    def test_no_flag_empty_history(self):
        txn = make_transaction(device_id="DEV_NEW")
        flags = ContextualDetector().detect(txn, [])
        assert not any(f.rule_name == "device_anomaly" for f in flags)


class TestLocationAnomaly:
    """Tests for location anomaly detection."""

    def test_flags_new_location(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [make_transaction(location="New York", timestamp=now - timedelta(hours=1))]
        txn = make_transaction(location="Tokyo", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert any(f.rule_name == "location_anomaly" for f in flags)

    def test_no_flag_known_location(self):
        now = datetime(2026, 2, 28, 12, 0, 0)
        recent = [make_transaction(location="New York", timestamp=now - timedelta(hours=1))]
        txn = make_transaction(location="New York", timestamp=now)
        flags = ContextualDetector().detect(txn, recent)
        assert not any(f.rule_name == "location_anomaly" for f in flags)

    def test_no_flag_empty_history(self):
        txn = make_transaction(location="Mars")
        flags = ContextualDetector().detect(txn, [])
        assert not any(f.rule_name == "location_anomaly" for f in flags)
