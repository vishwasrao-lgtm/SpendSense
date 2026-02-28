import pandas as pd

from ml_model import BehavioralAnomalyDetector
from intervention import InterventionEngine
import os

def run_demo():
    print("=" * 60)
    print(" Behavioral Intervention System for Financial Decisions ".center(60))
    print("=" * 60)
    
    # 1. Load Data
    train_dataset_path = 'training50k.csv'
    test_dataset_path = 'testcase10k.csv'
    
    print(f"\n[1] Loading training financial data from {train_dataset_path}...")
    df_train = pd.read_csv(train_dataset_path)
    df_train['timestamp'] = pd.to_datetime(df_train['timestamp'])
    print(f"    Loaded training dataset with {len(df_train)} transactions.")
    
    print(f"\n    Loading testing financial data from {test_dataset_path}...")
    df_test = pd.read_csv(test_dataset_path)
    df_test['timestamp'] = pd.to_datetime(df_test['timestamp'])
    print(f"    Loaded testing dataset with {len(df_test)} transactions.")

    # 2. Train Model
    print("\n[2] Training Behavioral Anomaly Detection Model on training data...")
    detector = BehavioralAnomalyDetector(contamination=0.08)
    detector.train(df_train)
    
    # 3. Predict & Generate Interventions
    print("\n[3] Scoring Transactions & Generating Interventions on test data...")
    # Predict anomalies on the separate test set
    scored_data = detector.predict(df_test)
    
    anomalies = scored_data[scored_data['is_anomaly'] == 1].copy()
    print(f"    Detected {len(anomalies)} anomalous spending patterns.")
    
    engine = InterventionEngine()
    
    print("\n" + "=" * 60)
    print(" Dashboard: Overall Spending Insights ".center(60))
    print("=" * 60)
    
    # Calculate basic ML insights from the test dataset
    categories = df_test['category'].unique()
    total_spend = df_test['amount'].sum()
    num_days = (df_test['timestamp'].max() - df_test['timestamp'].min()).days
    if num_days == 0: num_days = 1 # prevent division by zero
    
    daily_avg = total_spend / num_days
    weekly_avg = daily_avg * 7
    
    print(f"Categories Tracked : {', '.join(categories)}")
    print(f"Average Daily Spend: ₹{daily_avg:.2f}")
    print(f"Average Weekly Spend: ₹{weekly_avg:.2f}")
    
    print("\n" + "=" * 60)
    print(" Top 5 Impulsive Spending Alerts Dashboard ".center(60))
    print("=" * 60)
    
    top_anomalies = anomalies.sort_values('anomaly_score', ascending=False).head(5)
    
    for i, (_, row) in enumerate(top_anomalies.iterrows(), 1):
        print(f"\n[{i}] Alert - {row['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        print(f"    Category:   {row['category']}")
        print(f"    Amount:     ₹{row['amount']:.2f}")
        
        # Prepare context for the engine
        context = {
            'category': row['category'],
            'amount': row['amount'],
            'is_late_night': row['is_late_night'],
            'is_anomaly': row['is_anomaly']
        }
        
        intervention_msg = engine.generate_intervention(context)
        print(f"    ---> {intervention_msg}")
        
    print("\n" + "=" * 60)
    print("Demo completed successfully.")

if __name__ == "__main__":
    run_demo()
