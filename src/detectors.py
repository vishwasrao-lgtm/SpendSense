"""Behavioral and Contextual risk detectors."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from src.models import RiskFlag, Transaction

logger = logging.getLogger(__name__)


# ======================================================================
# Behavioral Detector
# ======================================================================

class BehavioralDetector:
    """Detect risky spending patterns and timing."""

    def detect(self, transaction: Transaction) -> List[RiskFlag]:
        """Evaluate a transaction for behavioural risk patterns.

        Returns a list of triggered RiskFlag objects (may be empty).
        """
        flags: List[RiskFlag] = []

        budget_flag = self.check_budget_drain(transaction)
        if budget_flag:
            flags.append(budget_flag)

        night_flag = self.check_late_night_pattern(transaction)
        if night_flag:
            flags.append(night_flag)

        return flags

    def check_budget_drain(self, transaction: Transaction) -> Optional[RiskFlag]:
        """Flag if amount > 50% of monthly_budget_remaining."""
        if transaction.monthly_budget_remaining <= 0:
            return RiskFlag(
                rule_name="budget_drain",
                explanation=(
                    f"This ${transaction.amount:.2f} purchase will push you further "
                    f"over budget (remaining: ${transaction.monthly_budget_remaining:.2f})."
                ),
                severity="high",
                detector_type="behavioral",
            )

        if transaction.amount > 0.5 * transaction.monthly_budget_remaining:
            pct = (transaction.amount / transaction.monthly_budget_remaining) * 100
            return RiskFlag(
                rule_name="budget_drain",
                explanation=(
                    f"This ${transaction.amount:.2f} purchase uses {pct:.0f}% of your "
                    f"remaining monthly budget (${transaction.monthly_budget_remaining:.2f})."
                ),
                severity="high",
                detector_type="behavioral",
            )

        return None

    def check_late_night_pattern(self, transaction: Transaction) -> Optional[RiskFlag]:
        """Flag if transaction occurs between 10 PM and 4 AM."""
        hour = transaction.timestamp.hour
        if hour >= 22 or hour < 4:
            return RiskFlag(
                rule_name="late_night_regret",
                explanation=(
                    f"Late-night purchase detected at {transaction.timestamp.strftime('%I:%M %p')}. "
                    "Purchases made between 10 PM and 4 AM are more likely to be regretted."
                ),
                severity="medium",
                detector_type="behavioral",
            )
        return None


# ======================================================================
# Contextual Detector
# ======================================================================

class ContextualDetector:
    """Detect unusual transaction contexts."""

    def detect(
        self,
        transaction: Transaction,
        recent_transactions: List[Transaction],
    ) -> List[RiskFlag]:
        """Evaluate a transaction for contextual anomalies.

        Args:
            transaction: The transaction being evaluated.
            recent_transactions: Previous transactions for this user.

        Returns:
            List of triggered RiskFlag objects.
        """
        flags: List[RiskFlag] = []

        new_recip = self.check_new_recipient(transaction)
        if new_recip:
            flags.append(new_recip)

        freq = self.check_frequency_burst(transaction, recent_transactions)
        if freq:
            flags.append(freq)

        device = self.check_device_anomaly(transaction, recent_transactions)
        if device:
            flags.append(device)

        location = self.check_location_anomaly(transaction, recent_transactions)
        if location:
            flags.append(location)

        return flags

    def check_new_recipient(self, transaction: Transaction) -> Optional[RiskFlag]:
        """Flag if recipient_status is 'new'."""
        if transaction.recipient_status == "new":
            return RiskFlag(
                rule_name="new_recipient",
                explanation="This is your first transaction with this recipient. Please verify before proceeding.",
                severity="medium",
                detector_type="contextual",
            )
        return None

    def check_frequency_burst(
        self,
        transaction: Transaction,
        recent_transactions: List[Transaction],
    ) -> Optional[RiskFlag]:
        """Flag if 3+ transactions within a 10-minute window."""
        window_start = transaction.timestamp - timedelta(minutes=10)
        txns_in_window = [
            t for t in recent_transactions
            if t.user_id == transaction.user_id and window_start <= t.timestamp <= transaction.timestamp
        ]
        if len(txns_in_window) >= 2:  # 2 prior + current = 3 total
            return RiskFlag(
                rule_name="frequency_burst",
                explanation=(
                    f"{len(txns_in_window) + 1} transactions detected in the last 10 minutes. "
                    "Rapid spending may indicate impulsive behavior."
                ),
                severity="medium",
                detector_type="contextual",
            )
        return None

    def check_device_anomaly(
        self,
        transaction: Transaction,
        recent_transactions: List[Transaction],
    ) -> Optional[RiskFlag]:
        """Flag if device_id is not in recent 24-hour history."""
        if not recent_transactions:
            return None

        window_start = transaction.timestamp - timedelta(hours=24)
        recent_devices = {
            t.device_id
            for t in recent_transactions
            if t.user_id == transaction.user_id and t.timestamp >= window_start
        }

        if recent_devices and transaction.device_id not in recent_devices:
            return RiskFlag(
                rule_name="device_anomaly",
                explanation=(
                    f"Transaction from unrecognised device '{transaction.device_id}'. "
                    "Recent transactions used different devices."
                ),
                severity="high",
                detector_type="contextual",
            )
        return None

    def check_location_anomaly(
        self,
        transaction: Transaction,
        recent_transactions: List[Transaction],
    ) -> Optional[RiskFlag]:
        """Flag if location differs from recent 24-hour history."""
        if not recent_transactions:
            return None

        window_start = transaction.timestamp - timedelta(hours=24)
        recent_locations = {
            t.location
            for t in recent_transactions
            if t.user_id == transaction.user_id and t.timestamp >= window_start
        }

        if recent_locations and transaction.location not in recent_locations:
            return RiskFlag(
                rule_name="location_anomaly",
                explanation=(
                    f"Transaction from unusual location '{transaction.location}'. "
                    "Recent transactions were from different locations."
                ),
                severity="high",
                detector_type="contextual",
            )
        return None
