"""Shared test helpers and factory functions."""

from datetime import datetime
from typing import Optional

from src.models import Transaction


def make_transaction(
    txn_id: str = "TXN_TEST",
    user_id: str = "USR_TEST",
    timestamp: Optional[datetime] = None,
    amount: float = 50.0,
    category: str = "shopping",
    recipient_status: str = "existing",
    monthly_budget_remaining: float = 1000.0,
    device_id: str = "DEV_A",
    location: str = "New York",
    channel: str = "mobile_app",
) -> Transaction:
    """Create a Transaction with sensible defaults for testing."""
    return Transaction(
        txn_id=txn_id,
        user_id=user_id,
        timestamp=timestamp or datetime(2026, 2, 28, 12, 0, 0),
        amount=amount,
        category=category,
        recipient_status=recipient_status,
        monthly_budget_remaining=monthly_budget_remaining,
        device_id=device_id,
        location=location,
        channel=channel,
    )
