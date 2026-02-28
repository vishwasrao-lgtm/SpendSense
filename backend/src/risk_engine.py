"""RiskEngine: orchestrates risk detection and records decisions in-memory."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from dataclasses import asdict
from src.detectors import BehavioralDetector, ContextualDetector
from src.ml_detector import MLAnomalyDetector
from src.models import InterceptLog, RiskAssessment, Transaction, RiskFlag

logger = logging.getLogger(__name__)


class RiskEngine:
    """Central orchestrator for transaction risk evaluation and decision recording."""

    def __init__(
        self,
        behavioral_detector: Optional[BehavioralDetector] = None,
        contextual_detector: Optional[ContextualDetector] = None,
        ml_detector: Optional[MLAnomalyDetector] = None,
    ):
        self.behavioral_detector = behavioral_detector or BehavioralDetector()
        self.contextual_detector = contextual_detector or ContextualDetector()
        self.ml_detector = ml_detector or MLAnomalyDetector()

        # In-memory stores
        self.transactions: List[Transaction] = []
        self.intercept_log: List[InterceptLog] = []
        self.money_saved: float = 0.0
        
        # Cache for ML predictions keyed by txn_id
        self.ml_predictions = {}

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def evaluate_transaction(self, transaction: Transaction) -> RiskAssessment:
        """Run a transaction through both detectors and return a RiskAssessment."""
        # Behavioural checks (no history needed)
        behavioral_flags = self.behavioral_detector.detect(transaction)

        # Contextual checks (need recent history)
        recent = self.get_recent_transactions(
            user_id=transaction.user_id,
            time_window_minutes=24 * 60,  # 24 hours
        )
        contextual_flags = self.contextual_detector.detect(transaction, recent)

        # ML anomaly check (retrieved from batch-predicted cache)
        ml_flag = self.ml_predictions.get(transaction.txn_id)

        all_flags = behavioral_flags + contextual_flags
        if ml_flag:
            all_flags.append(ml_flag)

        assessment = RiskAssessment(
            transaction=transaction,
            risk_flags=all_flags,
            is_flagged=len(all_flags) > 0,
            timestamp=datetime.now(),
        )

        # Mark the transaction
        transaction.is_flagged = assessment.is_flagged

        return assessment

    def record_decision(
        self,
        transaction: Transaction,
        risk_assessment: RiskAssessment,
        user_decision: str,
    ) -> None:
        """Record a user's decision for a flagged transaction.

        Args:
            transaction: The transaction in question.
            risk_assessment: The assessment that flagged it.
            user_decision: Either "cancelled" or "proceeded".
        """
        transaction.user_decision = user_decision

        entry = InterceptLog(
            txn_id=transaction.txn_id,
            transaction=transaction,
            risk_flags=risk_assessment.risk_flags,
            user_decision=user_decision,
            decision_timestamp=datetime.now(),
            risk_explanations=[f.explanation for f in risk_assessment.risk_flags],
        )
        self.intercept_log.append(entry)

        if user_decision == "cancelled":
            self.money_saved += transaction.amount

        logger.info(
            "Recorded decision '%s' for txn %s (amount $%.2f)",
            user_decision,
            transaction.txn_id,
            transaction.amount,
        )

    def train_ml_model(self, transactions: List[Transaction]) -> None:
        """Train the ML detector using the provided historical transactions."""
        if not transactions:
            return
            
        df = pd.DataFrame([asdict(t) for t in transactions])
        self.ml_detector.fit(df)
        
        # Immediately batch-predict and cache the results
        df_scored = self.ml_detector.predict_batch(df)
        
        for _, row in df_scored.iterrows():
            if row.get('is_anomaly') == 1:
                score = row.get('anomaly_score', 0.0)
                flag = RiskFlag(
                    rule_name="unusual_pattern",
                    explanation="This purchase significantly deviates from your established spending habits.",
                    severity="high",
                    detector_type="behavioral_model"
                )
                self.ml_predictions[row['txn_id']] = flag
            else:
                self.ml_predictions[row['txn_id']] = None

    def add_transaction(self, transaction: Transaction) -> None:
        """Store a transaction in the in-memory list."""
        self.transactions.append(transaction)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_recent_transactions(
        self,
        user_id: str,
        time_window_minutes: int = 10,
    ) -> List[Transaction]:
        """Return transactions for *user_id* within the last *time_window_minutes*."""
        if not self.transactions:
            return []
        # Use the latest transaction timestamp as reference
        latest = max(t.timestamp for t in self.transactions)
        cutoff = latest - timedelta(minutes=time_window_minutes)
        return [
            t
            for t in self.transactions
            if t.user_id == user_id and t.timestamp >= cutoff
        ]

    def get_all_transactions(self) -> List[Transaction]:
        """Return every transaction stored in memory."""
        return list(self.transactions)

    def get_intercept_log(self, decision_filter: Optional[str] = None) -> List[InterceptLog]:
        """Return intercept log entries, optionally filtered by decision type."""
        if decision_filter:
            return [e for e in self.intercept_log if e.user_decision == decision_filter]
        return list(self.intercept_log)

    def get_money_saved(self) -> float:
        """Return total money saved from cancelled transactions."""
        return self.money_saved

    def get_metrics(self):
        """Compute aggregated dashboard metrics."""
        from src.models import DashboardMetrics

        total = len(self.transactions)
        flagged = sum(1 for t in self.transactions if t.is_flagged)
        proceeded = sum(1 for e in self.intercept_log if e.user_decision == "proceeded")
        override_rate = (proceeded / flagged * 100) if flagged > 0 else 0.0

        late_night_count = sum(
            1
            for t in self.transactions
            if t.timestamp.hour >= 22 or t.timestamp.hour < 4
        )

        impulsivity = self._calculate_impulsivity_score(
            override_rate, late_night_count, total
        )

        return DashboardMetrics(
            total_transactions=total,
            total_flagged=flagged,
            money_saved=self.money_saved,
            override_rate=round(override_rate, 1),
            impulsivity_score=round(impulsivity, 1),
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_impulsivity_score(
        override_rate: float,
        late_night_count: int,
        total_count: int,
    ) -> float:
        """Weighted impulsivity score in [0, 100].

        Formula: 0.6 × override_rate + 0.4 × (late_night_pct)
        Both components are percentages [0‑100].
        """
        late_night_pct = (late_night_count / total_count * 100) if total_count > 0 else 0.0
        score = 0.6 * override_rate + 0.4 * late_night_pct
        return max(0.0, min(100.0, score))
