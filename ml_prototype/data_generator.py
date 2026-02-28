import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Categories and their typical probability weights
CATEGORIES = {
    'Groceries': 0.25,
    'Dining': 0.15,
    'Transport': 0.10,
    'Utilities': 0.05,
    'Entertainment': 0.10,
    'Electronics': 0.05,
    'Clothing': 0.10,
    'Health': 0.05,
    'Other': 0.15
}

def generate_normal_transactions(num_days=90, transactions_per_day_mean=3):
    """Generates standard, healthy financial transactions."""
    start_date = datetime.now() - timedelta(days=num_days)
    data = []
    
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        # Poisson distribution for number of transactions per day
        num_transactions = np.random.poisson(transactions_per_day_mean)
        
        for _ in range(num_transactions):
            # Normal hours: mostly 8 AM to 9 PM
            hour = int(np.random.normal(14, 4))
            hour = max(0, min(23, hour)) # Constrain to 0-23
            
            minute = np.random.randint(0, 60)
            tx_time = current_date.replace(hour=hour, minute=minute)
            
            category = np.random.choice(list(CATEGORIES.keys()), p=list(CATEGORIES.values()))
            
            # Normal amount varies by category
            if category in ['Groceries', 'Utilities']:
                amount = np.random.lognormal(mean=4.0, sigma=0.5) # ~$50-100
            elif category == 'Dining':
                amount = np.random.lognormal(mean=3.0, sigma=0.5) # ~$20-40
            else:
                amount = np.random.lognormal(mean=3.5, sigma=0.8) # Varied
                
            data.append({
                'timestamp': tx_time,
                'category': category,
                'amount': round(amount, 2),
                'is_impulsive': 0 # Ground truth label
            })
            
    return pd.DataFrame(data)

def inject_impulsive_behavior(df, num_events=10):
    """
    Injects impulsive behavior: 
    Large purchases in late night hours (11 PM - 3 AM) mostly in Electronics/Clothing
    """
    impulsive_data = []
    min_date = df['timestamp'].min()
    max_date = df['timestamp'].max()
    
    for _ in range(num_events):
        # Random day
        random_day = min_date + timedelta(days=np.random.randint(0, (max_date - min_date).days))
        
        # Late night hours: 11 PM to 3 AM
        hour = np.random.choice([23, 0, 1, 2, 3])
        minute = np.random.randint(0, 60)
        tx_time = random_day.replace(hour=hour, minute=minute)
        
        # Highly likely to be discretionary categories
        category = np.random.choice(['Electronics', 'Clothing', 'Entertainment'], p=[0.5, 0.4, 0.1])
        
        # Much larger amounts
        amount = np.random.uniform(200, 1500)
        
        impulsive_data.append({
            'timestamp': tx_time,
            'category': category,
            'amount': round(amount, 2),
            'is_impulsive': 1 # Ground truth label
        })
        
    df = pd.concat([df, pd.DataFrame(impulsive_data)], ignore_index=True)
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df

if __name__ == "__main__":
    np.random.seed(42)
    print("Generating standard transaction history...")
    df = generate_normal_transactions(num_days=90)
    print(f"Generated {len(df)} normal transactions.")
    
    print("Injecting impulsive behavior patterns...")
    df = inject_impulsive_behavior(df, num_events=15)
    print(f"Total transactions: {len(df)}")
    
    # Save to CSV
    df.to_csv('synthetic_transactions.csv', index=False)
    print("Saved dataset to synthetic_transactions.csv")
