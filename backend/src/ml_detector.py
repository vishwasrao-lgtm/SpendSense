"""Machine Learning Anomaly Detection using Isolation Forest and Pandas."""

import logging
import os
import pandas as pd
import numpy as np
import joblib
from typing import List, Optional
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from src.models import RiskFlag, Transaction

logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    """Uses unsupervised machine learning to detect spending anomalies."""

    def __init__(self, contamination: float = 0.08, model_path: str = "model_cache.joblib"):
        self.contamination = contamination
        self.model_path = model_path
        self.model = None
        self.preprocessor = None
        self.high_spend_threshold = 470.0
        self.impulsive_hours = [0, 1, 2, 3, 4, 5, 6]
        self.is_trained = False
        
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates new features based on transaction timestamps and behavior."""
        df = df.copy()
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Late night / high impulse hour flag
        df['is_late_night'] = df['hour_of_day'].apply(lambda x: 1 if x in self.impulsive_hours else 0)
        
        # Target specific discretionary categories
        discretionary_categories = ['shopping', 'entertainment', 'travel', 'dining']
        df['is_discretionary'] = df['category'].str.lower().apply(lambda x: 1 if x in discretionary_categories else 0)
        
        # Rolling 7-day spend per category
        df = df.sort_values('timestamp')
        df['rolling_7d_spend'] = df.groupby('category')['amount'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        
        # FEATURE ENGINEERING: Square the amount to make high purchases stand out more
        df['amount_squared'] = df['amount'] ** 2
        
        # Sort back to original index to preserve order if needed, but we typically merge on txn_id
        return df

    def fit(self, df: pd.DataFrame) -> None:
        """Trains the Isolation Forest model and calculates dynamic rule thresholds."""
        if len(df) < 10:
            logger.warning("Not enough transactions to train ML model (need >= 10).")
            self.is_trained = False
            return

        df_temp = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_temp['timestamp']):
            df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])
        df_temp['hour_of_day'] = df_temp['timestamp'].dt.hour
            
        # Calculate dynamic threshold based on data (simulate impulsive if not available)
        self.high_spend_threshold = df_temp['amount'].quantile(0.95)
        self.impulsive_hours = [23, 0, 1, 2, 3, 4]
            
        df_featured = self._engineer_features(df)
        
        # Define features for the model
        numeric_features = ['amount', 'amount_squared', 'hour_of_day', 'is_late_night', 'is_discretionary', 'rolling_7d_spend']
        categorical_features = ['category', 'day_of_week']
        
        # Create preprocessing pipeline
        numeric_transformer = StandardScaler()
        categorical_transformer = OneHotEncoder(handle_unknown='ignore')
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])
            
        # Create pipeline including Isolation Forest
        self.model = Pipeline(steps=[
            ('preprocessor', self.preprocessor),
            ('classifier', IsolationForest(
                contamination=self.contamination, 
                random_state=42,
                n_estimators=100
            ))
        ])
        
        # Train model
        X = df_featured[numeric_features + categorical_features]
        try:
            self.model.fit(X)
            self.is_trained = True
            logger.info(f"Successfully trained MLAnomalyDetector on {len(df)} transactions.")
        except Exception as e:
            logger.error(f"Failed to train ML model: {e}")
            self.is_trained = False

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scores a batch of transactions using DataFrame context."""
        if not self.is_trained or self.model is None:
            df_result = df.copy()
            df_result['is_anomaly'] = 0
            df_result['anomaly_score'] = 0.0
            return df_result

        df_featured = self._engineer_features(df)
        numeric_features = ['amount', 'amount_squared', 'hour_of_day', 'is_late_night', 'is_discretionary', 'rolling_7d_spend']
        categorical_features = ['category', 'day_of_week']
        
        X = df_featured[numeric_features + categorical_features]
        
        # Predict returns 1 for inliers, -1 for outliers
        predictions = self.model.predict(X)
        predictions = np.where(predictions == -1, 1, 0)
        
        scores = -self.model.decision_function(X)
        
        # Rule-based override inside ML model:
        heuristic_impulsive = (df_featured['is_discretionary'] == 1) & ((df_featured['is_late_night'] == 1) | (df_featured['amount'] > self.high_spend_threshold))
        combined_predictions = np.where(heuristic_impulsive | (predictions == 1), 1, 0)
        
        df_featured['is_anomaly'] = combined_predictions
        df_featured['anomaly_score'] = scores
        
        return df_featured
