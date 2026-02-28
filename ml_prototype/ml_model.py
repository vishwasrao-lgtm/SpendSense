import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from datetime import datetime

class BehavioralAnomalyDetector:
    def __init__(self, contamination=0.05):
        self.contamination = contamination
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
        discretionary_categories = ['Electronics', 'Clothing', 'Entertainment']
        df['is_discretionary'] = df['category'].apply(lambda x: 1 if x in discretionary_categories else 0)
        
        # Rolling 7-day spend per category (simulated budget depletion)
        # Note: Requires sorting by time
        df = df.sort_values('timestamp')
        df['rolling_7d_spend'] = df.groupby('category')['amount'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        
        return df
        
    def train(self, df):
        """Trains the Isolation Forest model on regular user behavior."""
        df_featured = self._engineer_features(df)
        
        # Define features for the model
        numeric_features = ['amount', 'hour_of_day', 'is_late_night', 'is_discretionary', 'rolling_7d_spend']
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
        print("Model trained successfully.")
        return self
        
    def predict(self, new_transactions_df):
        """Scores new transactions. Returns 1 for anomaly (harmful/impulsive), 0 for normal."""
        if self.model is None:
            raise Exception("Model is not trained yet!")
            
        df_featured = self._engineer_features(new_transactions_df)
        numeric_features = ['amount', 'hour_of_day', 'is_late_night', 'is_discretionary', 'rolling_7d_spend']
        categorical_features = ['category', 'day_of_week']
        
        X = df_featured[numeric_features + categorical_features]
        
        # Isolation Forest returns -1 for outliers, 1 for inliers
        predictions = self.model.predict(X)
        
        # Convert to 1 for anomaly, 0 for normal
        predictions = np.where(predictions == -1, 1, 0)
        
        # Get raw anomaly scores (lower means more anomalous)
        # We invert it so higher score = more anomalous
        scores = -self.model.decision_function(X) 
        
        df_featured['is_anomaly'] = predictions
        df_featured['anomaly_score'] = scores
        
        return df_featured

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
