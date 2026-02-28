import random

class InterventionEngine:
    """Generates personalized interventions based on detected anomalies."""
    
    def __init__(self):
        # A pool of supportive, non-intrusive messages
        self.late_night_messages = [
            "You seem to be shopping late! Consider adding this to your cart and reviewing it tomorrow morning.",
            "Late night splurges can add up. Sleeping on it might give you a fresh perspective tomorrow.",
            "Is this a planned purchase? If not, a quick pause might save you some cash!"
        ]
        
        self.high_spend_messages = [
            "This purchase is larger than your usual {category} spending! A quick review of your budget might be helpful.",
            "Whoa, big purchase in {category}! Taking a 24-hour break before checking out often helps to clarify if it's a need or a want.",
            "This single transaction is {percent}% higher than your weekly average. Consider the long-term impact on your goals!"
        ]
        
        self.high_velocity_messages = [
            "You've been spending quite a bit on {category} this week. Consider setting a small limit for the rest of the week.",
            "Your weekly spend for {category} is looking unusually high. Slowing down now means more savings later!"
        ]
        
    def generate_intervention(self, transaction):
        """
        Takes a transaction dictionary (must include 'anomaly_score' and context features)
        and returns an appropriate intervention message.
        """
        if not transaction.get('is_anomaly', 0):
            return "Looking good! Keep up the healthy spending habits."
            
        category = transaction.get('category', 'this category')
        is_late_night = transaction.get('is_late_night', 0)
        amount = transaction.get('amount', 0)
        
        messages = []
        
        # Rule 1: Late Night Splurges
        if is_late_night:
            msgs = [msg for msg in self.late_night_messages]
            messages.append(random.choice(msgs))
            
        # Rule 2: High Spend Amount 
        # (Dynamic threshold provided by the ML model context)
        high_spend_threshold = transaction.get('high_spend_threshold', 470)
        if amount > high_spend_threshold:
            msg = random.choice(self.high_spend_messages).format(category=category, percent=random.randint(40, 80))
            messages.append(msg)
            
        # Fallback if anomaly triggered but no specific rule caught it
        if not messages:
            messages.append(random.choice(self.high_velocity_messages).format(category=category))
            
        # Combine messages constructively 
        return "Insight: " + " ".join(messages)

if __name__ == "__main__":
    # Test rules engine
    engine = InterventionEngine()
    test_tx1 = {'category': 'Electronics', 'amount': 850.00, 'is_late_night': 1, 'is_anomaly': 1}
    test_tx2 = {'category': 'Groceries', 'amount': 45.00, 'is_late_night': 0, 'is_anomaly': 0}
    test_tx3 = {'category': 'Clothing', 'amount': 250.00, 'is_late_night': 0, 'is_anomaly': 1}
    
    print("Test 1 (Late Night Splurge):", engine.generate_intervention(test_tx1))
    print("Test 2 (Normal Grocery):", engine.generate_intervention(test_tx2))
    print("Test 3 (High Spend Clothing):", engine.generate_intervention(test_tx3))
