import pandas as pd
from data_generator import generate_normal_transactions, inject_impulsive_behavior
from ml_model import BehavioralAnomalyDetector
from intervention import InterventionEngine
import os

def run_demo():
    print("=" * 60)
    print(" Behavioral Intervention System for Financial Decisions ".center(60))
    print("=" * 60)
    
    # 1. Generate Data
    if not os.path.exists('synthetic_transactions.csv'):
        print("\n[1] Generating synthetic financial data...")
        df = generate_normal_transactions(num_days=60)
        df = inject_impulsive_behavior(df, num_events=12)
        df.to_csv('synthetic_transactions.csv', index=False)
        print(f"    Created dataset with {len(df)} transactions.")
    else:
        print("\n[1] Loading existing synthetic financial data...")
        df = pd.read_csv('synthetic_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        print(f"    Loaded dataset with {len(df)} transactions.")

    # 2. Train or Load Model
    print("\n[2] Loading/Training Behavioral Anomaly Detection Model...")
    detector = BehavioralAnomalyDetector(contamination=0.08)
    
    if detector.load():
        print("    Using cached model instance.")
    else:
        print("    Training new model instance...")
        detector.train(df)
    
    # 3. Predict & Generate Interventions
    print("\n[3] Scoring Transactions & Generating Interventions...")
    # For demo purposes, we rescore the entire dataset. In reality, this would be new streaming data.
    scored_data = detector.predict(df)
    
    anomalies = scored_data[scored_data['is_anomaly'] == 1].copy()
    print(f"    Detected {len(anomalies)} anomalous spending patterns.")
    
    engine = InterventionEngine()
    
    print("\n" + "=" * 60)
    print(" Top 5 Impulsive Spending Alerts Dashboard ".center(60))
    print("=" * 60)
    
    top_anomalies = anomalies.sort_values('anomaly_score', ascending=False).head(5)
    
    for i, (_, row) in enumerate(top_anomalies.iterrows(), 1):
        print(f"\n[{i}] Alert - {row['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        print(f"    Category:   {row['category']}")
        print(f"    Amount:     ${row['amount']:.2f}")
        
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
