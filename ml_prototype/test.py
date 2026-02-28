import pandas as pd
from datetime import datetime
from ml_model import BehavioralAnomalyDetector
from intervention import InterventionEngine
import warnings

# Suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning)

# =====================================================================
# EDIT THESE 3 VARIABLES TO TEST YOUR TRANSACTION
# =====================================================================
TIMESTAMP_TO_TEST = "2026-03-01 02:45:00"
CATEGORY_TO_TEST  = "Entertainment"
AMOUNT_TO_TEST    = 5500.00
# =====================================================================

print("\n" + "=" * 50)
print(" Transaction Analysis ".center(50))
print("=" * 50)

# Load Model
detector = BehavioralAnomalyDetector()
if not detector.load():
    print("❌ Error: Could not find loaded model. Run 'python main.py' first.")
    exit()
    
print(f"Analyzing Transaction:")
print(f"  Time     : {TIMESTAMP_TO_TEST}")
print(f"  Category : {CATEGORY_TO_TEST}")
print(f"  Amount   : ₹{AMOUNT_TO_TEST}")

# Format for model
df = pd.DataFrame([{
    'timestamp': pd.to_datetime(TIMESTAMP_TO_TEST),
    'category': CATEGORY_TO_TEST,
    'amount': float(AMOUNT_TO_TEST)
}])

# Predict
scored_data = detector.predict(df)
result = scored_data.iloc[0]
is_anomaly = result['is_anomaly'] == 1

print("\n[ML Results]")
if is_anomaly:
    print("Status             : ⚠️ Impulsive / Anomalous")
else:
    print("Status             : ✅ Normal")
    
print(f"Raw Anomaly Score  : {result['anomaly_score']:.3f}")

# Intervention
if is_anomaly:
    engine = InterventionEngine()
    msg = engine.generate_intervention({
        'category': result['category'],
        'amount': result['amount'],
        'is_late_night': result['is_late_night'],
        'is_anomaly': result['is_anomaly'],
        'high_spend_threshold': detector.high_spend_threshold
    })
    print("\n[Intervention Triggered]")
    print(f"---> {msg}")
    
print("=" * 50 + "\n")
