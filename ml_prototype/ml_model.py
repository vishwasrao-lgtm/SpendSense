import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from datetime import datetime
import joblib
import os

class BehavioralAnomalyDetector:
    def __init__(self, contamination=0.05, model_path="model_cache.joblib"):
        self.contamination = contamination
        self.model_path = model_path
        self.model = None
        self.preprocessor = None
        
    def _engineer_features(self, df):
        """Creates new features based on transaction timestamps and behavior."""
        df = df.copy()
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Late night flag (11 PM to 4 AM)
        df['is_late_night'] = df['hour_of_day'].apply(lambda x: 1 if (x >= 23 or x <= 4) else 0)
        
        # Target specific discretionary categories
        discretionary_categories = ['Shopping', 'Entertainment', 'Travel']
        df['is_discretionary'] = df['category'].apply(lambda x: 1 if x in discretionary_categories else 0)
        
        # Rolling 7-day spend per category (simulated budget depletion)
        # Note: Requires sorting by time
        df = df.sort_values('timestamp')
        df['rolling_7d_spend'] = df.groupby('category')['amount'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        
        # FEATURE ENGINEERING: Square the amount to make high purchases stand out more
        df['amount_squared'] = df['amount'] ** 2
        
        return df
        
    def train(self, df):
        """Trains the Isolation Forest model on regular user behavior."""
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
        self.model.fit(X)
        self.save()
        print("Model trained successfully.")
        return self
        
    def predict(self, new_transactions_df):
        """Scores new transactions. Returns 1 for anomaly (harmful/impulsive), 0 for normal."""
        if self.model is None:
            raise Exception("Model is not trained yet!")
            
        df_featured = self._engineer_features(new_transactions_df)
        numeric_features = ['amount', 'amount_squared', 'hour_of_day', 'is_late_night', 'is_discretionary', 'rolling_7d_spend']
        categorical_features = ['category', 'day_of_week']
        
        X = df_featured[numeric_features + categorical_features]
        
        # Isolation Forest returns -1 for outliers, 1 for inliers
        predictions = self.model.predict(X)
        
        # Convert to 1 for anomaly, 0 for normal
        predictions = np.where(predictions == -1, 1, 0)
        
        # Get raw anomaly scores (lower means more anomalous)
        # We invert it so higher score = more anomalous
        scores = -self.model.decision_function(X) 
        
        # APPLY RULE-BASED OVERRIDE
        # The Isolation Forest is unsupervised and can miss standard definitions of impulsive spending.
        # We override based on our data insights:
        # If it's a Discretionary Category AND (it's Late Night OR Very High Amount (>₹470)) -> Flag as Impulsive
        heuristic_impulsive = (df_featured['is_discretionary'] == 1) & ((df_featured['is_late_night'] == 1) | (df_featured['amount'] > 470))
        
        # Combine ML prediction and heuristic prediction using OR
        combined_predictions = np.where(heuristic_impulsive | (predictions == 1), 1, 0)
        
        df_featured['is_anomaly'] = combined_predictions
        df_featured['anomaly_score'] = scores
        
        return df_featured
        
    def save(self):
        """Saves the trained model to disk."""
        if self.model is None:
            raise Exception("No model to save!")
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")
        
    def load(self):
        """Loads a trained model from disk if it exists."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"Model loaded from {self.model_path}")
            return True
        return False

if __name__ == "__main__":
    # Test model locally
    try:
        data = pd.read_csv('synthetic_transactions.csv')
        detector = BehavioralAnomalyDetector(contamination=0.08)
        detector.train(data)
        
        # Predict on same data just to test
        results = detector.predict(data)
        
        anomalies = results[results['is_anomaly'] == 1]
        print(f"Detected {len(anomalies)} anomalies out of {len(data)} transactions.")
        print("\nTop 5 Anomalies:")
        print(anomalies.sort_values('anomaly_score', ascending=False)[['timestamp', 'category', 'amount', 'is_anomaly', 'anomaly_score']].head())
    except FileNotFoundError:
        print("synthetic_transactions.csv not found. Please run data_generator.py first.")
