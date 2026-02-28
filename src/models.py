"""Core data models for SpendSense."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Transaction:
    """A financial transaction record."""

    txn_id: str
    user_id: str
    timestamp: datetime
    amount: float
    category: str
    recipient_status: str  # "new" or "existing"
    monthly_budget_remaining: float
    device_id: str
    location: str
    channel: str  # "mobile_app", "web", "pos"

    # Populated after risk evaluation
    is_flagged: bool = False
    user_decision: str = ""  # "cancelled", "proceeded", or ""


REQUIRED_FIELDS = [
    "txn_id",
    "user_id",
    "timestamp",
    "amount",
    "category",
    "recipient_status",
    "monthly_budget_remaining",
    "device_id",
    "location",
    "channel",
]

VALID_CATEGORIES = [
    "groceries",
    "dining",
    "entertainment",
    "shopping",
    "bills",
    "travel",
    "health",
    "education",
    "utilities",
    "other",
]

VALID_CHANNELS = ["mobile_app", "web", "pos"]


@dataclass
class RiskFlag:
    """An indicator that a detection rule was triggered."""

    rule_name: str
    explanation: str
    severity: str  # "high", "medium", "low"
    detector_type: str  # "behavioral" or "contextual"


@dataclass
class RiskAssessment:
    """Result of evaluating a transaction through the risk engine."""

    transaction: Transaction
    risk_flags: List[RiskFlag] = field(default_factory=list)
    is_flagged: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InterceptLog:
    """Record of a flagged transaction and the user's decision."""

    txn_id: str
    transaction: Transaction
    risk_flags: List[RiskFlag] = field(default_factory=list)
    user_decision: str = ""  # "cancelled" or "proceeded"
    decision_timestamp: datetime = field(default_factory=datetime.now)
    risk_explanations: List[str] = field(default_factory=list)


@dataclass
class DashboardMetrics:
    """Aggregated metrics for the dashboard."""

    total_transactions: int = 0
    total_flagged: int = 0
    money_saved: float = 0.0
    override_rate: float = 0.0
    impulsivity_score: float = 0.0
