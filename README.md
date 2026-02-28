# SpendSense: Active Financial Intervention Engine

SpendSense is a real-time behavioral intervention platform designed to help users curb impulsive spending and make smarter financial decisions. It intercepts transactions at the point of purchase, evaluates them using a dual-check Risk Engine (Behavioral + Contextual) powered by Machine Learning, and provides highly personalized, educational friction before a transaction is finalized.

## 🌟 The Problem
The digitalization of payments has eliminated the psychological friction of spending money. One-click checkouts and contactless payments make it effortless to drain budgets on impulsive, late-night, or uncharacteristic purchases. Financial tools today tell you what you *did* yesterday; they do not stop you from what you are about to do *today*.

## 💡 The Solution
SpendSense acts as a "financial cooling-off period." By running real-time heuristic rules and unsupervised Machine Learning models against incoming transactions, it detects abnormal behavior (e.g., late-night shopping binges, unusual device usage, sudden frequency bursts) and pauses the transaction. It then presents a **Behavioral Insight** to the user, explaining exactly *why* the transaction was flagged, and projecting the long-term impact of their spending.

## 🚀 Key Features

### 1. Advanced Risk Engine
- **Unsupervised ML Anomaly Detection:** An `IsolationForest` pipeline built with `scikit-learn` creates dynamic spending baselines. It analyzes full DataFrames of user history, engineering features like 7-day rolling spend limits and cyclical time-of-day behavior to flag out-of-character purchases.
- **Behavioral Detection:** Flags transactions that consume too much of a user's remaining monthly budget or occur during known impulsive windows (e.g., 11 PM to 4 AM).
- **Contextual Detection:** Recognizes rapid "frequency bursts" (successive small transactions), location anomalies, or new recipients.

### 2. Personalized Interventions
When a transaction is caught, SpendSense doesn't just block it—it educates.
- **Dynamic Messaging:** "You seem to be shopping late!" or "Your spending is 65% above your weekly average."
- **Cooling-Off Period:** Forces a countdown timer, preventing snap decisions and giving the logical brain time to catch up.

### 3. Comprehensive Dashboard
- **Live Transaction Feed:** Watch transactions get evaluated in real-time, categorized by clean, cancelled, or proceeded.
- **KPI Metrics:** Tracks total money saved from cancelled transactions, system override rates, and customized user impulsivity scores.

## 🛠 Tech Stack
- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS, Recharts.
- **Backend:** Python 3, Flask, Pandas, Scikit-learn, Numpy, Joblib.

## 🏃‍♂️ Getting Started

### 1. Start the Flask Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python api.py
```
*The API will run on http://localhost:5000*

### 2. Start the Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
*The app will be available at http://localhost:3000*

## 🧪 Demo Data
You can upload the `data/sample_transactions.json` file in the web interface, or simply click "Load Sample Data" to watch the ML engine train itself on the fly and populate the dashboard.