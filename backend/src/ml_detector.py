"""Machine Learning Anomaly Detection using Isolation Forest."""

import logging
from typing import List, Optional

import numpy as np
from sklearn.ensemble import IsolationForest

from src.models import RiskFlag, Transaction

logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    """Uses unsupervised machine learning to detect spending anomalies."""

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        """Initialize the ML detector.
        
        Args:
            contamination: Expected proportion of outliers (0 to 0.5).
            random_state: Seed for reproducibility.
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
        )
        self.is_trained = False
        self.categories = [
            "groceries", "dining", "entertainment", "shopping", 
            "bills", "travel", "health", "education", "utilities", "other"
        ]

    def _extract_features(self, transaction: Transaction) -> np.ndarray:
        """Convert a Transaction object into a numerical feature vector.
        
        Features:
        1. Amount (normalized by monthly budget if available, otherwise raw)
        2. Hour of day (cyclical: sin, cos)
        3. Day of week
        4. Category (one-hot encoded)
        """
        features = []

        # 1. Amount relative to budget (or raw if budget is 0)
        if transaction.monthly_budget_remaining > 0:
            amt_ratio = transaction.amount / transaction.monthly_budget_remaining
        else:
            amt_ratio = transaction.amount / 1000.0  # fallback normalization
        features.append(amt_ratio)

        # 2. Time features (Cyclical encoding for hour)
        hour = transaction.timestamp.hour
        hour_sin = np.sin(2 * np.pi * hour / 24.0)
        hour_cos = np.cos(2 * np.pi * hour / 24.0)
        features.extend([hour_sin, hour_cos])

        # 3. Day of week (0-6)
        day_of_week = transaction.timestamp.weekday()
        features.append(day_of_week / 6.0)

        # 4. Category one-hot encoding
        cat = transaction.category.lower()
        if cat not in self.categories:
            cat = "other"
            
        for c in self.categories:
            features.append(1.0 if cat == c else 0.0)

        return np.array(features).reshape(1, -1)

    def fit(self, transactions: List[Transaction]) -> None:
        """Train the Isolation Forest on a baseline set of transactions.
        
        Args:
            transactions: Historical transactions to learn from.
        """
        if len(transactions) < 10:
            logger.warning("Not enough transactions to train ML model (need >= 10).")
            self.is_trained = False
            return

        # Extract features for all transactions
        X = np.vstack([self._extract_features(t) for t in transactions])
        
        # Fit the model
        try:
            self.model.fit(X)
            self.is_trained = True
            logger.info("Successfully trained MLAnomalyDetector on %d transactions.", len(transactions))
        except Exception as e:
            logger.error("Failed to train ML model: %s", e)
            self.is_trained = False

    def detect(self, transaction: Transaction) -> Optional[RiskFlag]:
        """Evaluate a single transaction against the trained baseline.
        
        Returns a RiskFlag if anomalous, else None.
        """
        if not self.is_trained:
            return None

        # Predict returns 1 for inliers, -1 for outliers
        X = self._extract_features(transaction)
        prediction = self.model.predict(X)[0]

        if prediction == -1:
            return RiskFlag(
                rule_name="ml_anomaly",
                explanation="This transaction breaks your normal spending patterns based on machine learning analysis.",
                severity="high",
                detector_type="ml",
            )
        
        return None
