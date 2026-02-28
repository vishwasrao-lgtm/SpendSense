import pandas as pd
from datetime import datetime
from ml_model import BehavioralAnomalyDetector
from intervention import InterventionEngine
import warnings

# Suppress sklearn warnings about feature names since we don't fit the scaler in this script
warnings.filterwarnings("ignore", category=UserWarning)

def test_single_transaction(timestamp, category, amount):
    """
    Tests a single financial transaction against the loaded ML model
    to determine if it is impulsive/anomalous.
    """
    print("\n" + "=" * 50)
    print(" Transaction Analysis ".center(50))
    print("=" * 50)
    
    # 1. Load the pre-trained model cache
    detector = BehavioralAnomalyDetector()
    if not detector.load():
        print("❌ Error: Could not find loaded model. Please run 'python main.py' first to train the model.")
        return
        
    print(f"Analyzing Transaction:")
    print(f"  Time     : {timestamp}")
    print(f"  Category : {category}")
    print(f"  Amount   : ₹{amount}")
    
    # 2. Format as a DataFrame for the model
    data = [{
        'timestamp': pd.to_datetime(timestamp),
        'category': category,
        'amount': float(amount)
    }]
    df = pd.DataFrame(data)
    
    # 3. Predict Anomaly Score
    scored_data = detector.predict(df)
    result = scored_data.iloc[0]
    is_anomaly = result['is_anomaly'] == 1
    
    print("\n[ML Results]")
    if is_anomaly:
        print("Status             : ⚠️ Impulsive / Anomalous")
    else:
        print("Status             : ✅ Normal")
        
    print(f"Raw Anomaly Score  : {result['anomaly_score']:.3f}")
    
    # 4. Generate Intervention message if it is an anomaly
    if is_anomaly:
        engine = InterventionEngine()
        context = {
            'category': result['category'],
            'amount': result['amount'],
            'is_late_night': result['is_late_night'],
            'is_anomaly': result['is_anomaly']
        }
        msg = engine.generate_intervention(context)
        print("\n[Intervention Triggered]")
        print(f"---> {msg}")
        
    print("=" * 50 + "\n")

if __name__ == "__main__":
    # You can change these variables to test different scenarios
    # -------------------------------------------------------------
    
    # Scenario 1: A late night high spend (Likely Impulsive)
    test_single_transaction(
        timestamp="2026-03-01 02:45:00", 
        category="Entertainment", 
        amount=5500.00
    )
    
    # Scenario 2: A regular afternoon grocery trip (Likely Normal)
    test_single_transaction(
        timestamp="2026-03-02 14:30:00", 
        category="Food", 
        amount=350.00
    )
