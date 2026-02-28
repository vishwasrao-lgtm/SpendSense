# Design Document: SpendSense Transaction Intervention System

## Overview

SpendSense is a real-time financial transaction monitoring and intervention system originally built as a hackathon demo and significantly extended. The system intercepts transactions at the point of purchase, evaluates them through a tri-layer risk engine (Behavioral + Contextual + Machine Learning), and intervenes with explainable alerts before potentially regrettable purchases are finalized.

The system architecture features a decoupled client-server model:
1. **Frontend:** A Next.js (React) web application providing a modern, dynamic dashboard and the real-time "Intervention Modal" friction layer.
2. **Backend:** A Flask REST API written in Python, orchestrating the risk engine. All data is stored in-memory using Python data structures for blisteringly fast access during demonstrations.

Key design principles:
- **Decoupled Architecture:** Clean separation of concerns between the React UI and the Python data-processing engine.
- **In-memory Processing:** All data stored in Python lists and dictionaries (no persistent database needed for the demo lifecycle).
- **Explainability:** Every risk flag includes human-readable "Behavioral Insights" and numeric compound interest projections.
- **Tri-Layer Risk Detection:** 
  1. *Behavioral:* Static rules matching bad habits (budget drain).
  2. *Contextual:* Sliding-window anomalies (frequency bursts, device/location changes).
  3. *Unsupervised ML:* Pandas DataFrame pipelines analyzing cyclical time, rolling averages, and amount-squaring to detect complex deviations from personal baselines.
- **User Agency:** A 5-second cooling-off period forces users to pause and review insights before they are given the choice to proceed.

## Architecture

### System Components

The system consists of five primary components:

1. **Next.js Frontend (`frontend/src/`)**: 
   - `Sidebar`: Data loading controls.
   - `MetricsBar`: Real-time KPI gradients.
   - `TransactionFeed`: Live chronological transaction feed with status badges.
   - `InterventionModal`: The core friction UI that intercepts risky payments.
2. **Flask API (`backend/api.py`)**: REST endpoints linking the frontend to the Python engine.
3. **Data_Loader**: Loads transactions from CSV/JSON sample datasets into memory.
4. **Risk_Engine**: Evaluates payments and logs decisions.
   - **Behavioral_Detector**: Rules like budget thresholds.
   - **Contextual_Detector**: Rules comparing current payment to sliding n-minute windows.
   - **MLAnomalyDetector**: An `IsolationForest` pipeline that batch-scores DataFrames using engineered features (rolling 7-day spend, discretionary tagging, cyclical hour encoding).
5. **Intercept_Log**: The in-memory data store holding all flagged transaction histories and the user's manual "cancel vs. proceed" choices.

### Data Flow

1. User uploads a CSV/JSON file to the React Frontend.
2. Frontend sends file via `POST /api/load` to the Flask API.
3. Flask initializes full transaction set in memory.
4. `RiskEngine` passes full dataset to `MLAnomalyDetector.fit()` to train the IsolationForest baseline dynamically.
5. `RiskEngine` batch-predicts all historical transactions through the ML pipeline, caching the results.
6. For individual live transactions (`POST /api/add-transaction`):
   - The transaction is synchronously checked by Behavioral and Contextual detectors.
   - The cached ML result is appended.
   - If ANY detector flags the transaction, the API returns `status: "flagged"` along with the `RiskAssessment`.
7. React Frontend catches the "flagged" status and mounts `<InterventionModal>`.
8. User is forced to wait 5 seconds while reading the "Behavioral Insights" and dynamically generated tip.
9. User clicks "Cancel" (API: `POST /api/decide`). The server updates the `InterceptLog` and increments the Money Saved KPI, which is then re-fetched by the UI.

### Technology Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, Lucide Icons, Recharts (for data visualization).
- **Backend API**: Python 3.9+, Flask, Flask-CORS.
- **Data Processing & ML**: pandas, numpy, scikit-learn (`IsolationForest`, `ColumnTransformer`), joblib.
- **Testing**: pytest + hypothesis.

## Components and Interfaces

### MLAnomalyDetector (Machine Learning Core)

**Purpose**: Provide dynamic, unsupervised anomaly checking across complex behavioral permutations.

**Interface**:
```python
class MLAnomalyDetector:
    def __init__(self, contamination=0.08, model_path="model_cache.joblib"):
        pass
        
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts hour_of_day, is_late_night, is_discretionary, rolling_7d_spend"""
        pass

    def fit(self, df: pd.DataFrame) -> None:
        """Trains the scikit-learn IsolationForest pipeline on the baseline dataframe."""
        pass

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scores a batch of transactions using DataFrame context, applying heuristics."""
        pass
```

### Risk_Engine

**Purpose**: Orchestrate the three detectors and maintain state.

**Interface**:
```python
class RiskEngine:
    def evaluate_transaction(self, transaction: Transaction) -> RiskAssessment:
        """Evaluate transaction against behavioral, contextual, and cached ML checks"""
        pass
    
    def record_decision(
        self,
        transaction: Transaction,
        risk_assessment: RiskAssessment,
        user_decision: str  # "cancelled" or "proceeded"
    ) -> None:
        pass
    
    def train_ml_model(self, transactions: List[Transaction]) -> None:
        """Convert list to DataFrame, train ML detector, and cache batch predictions"""
        pass
```

### InterventionModal (React Component)

**Purpose**: The point-of-sale friction layer.

**Key Logic**:
- Auto-generates deterministic, context-aware "Smart Spending Tips" (e.g. checking for late night hours or abnormally high spend amounts).
- Enforces a client-side `setInterval` countdown preventing the "Proceed" button from being clicked until the cooling-off period expires.
- Renders the exact "Behavioral Insights" JSON strings output by the Flask backend.

## Data Models (Python Dataclasses)

### Transaction
```python
@dataclass
class Transaction:
    txn_id: str
    user_id: str
    timestamp: datetime
    amount: float
    category: str
    recipient_status: str
    monthly_budget_remaining: float
    device_id: str
    location: str
    channel: str
    is_flagged: bool = False
    user_decision: str = ""
```

### RiskAssessment
```python
@dataclass
class RiskAssessment:
    transaction: Transaction
    risk_flags: List[RiskFlag]
    is_flagged: bool
    timestamp: datetime
```

### RiskFlag
```python
@dataclass
class RiskFlag:
    rule_name: str
    explanation: str
    severity: str
    detector_type: str
```

## Testing Strategy

The backend enforces core properties utilizing **pytest** and **hypothesis** for randomized property generation. 

Key verified properties:
1. **Model Serialization**: Custom Python objects cannot break the Flask JSON encoder (hence the conversion from Pydantic `model_dump` to `dataclasses.asdict`).
2. **Budget Drain Verification**: Hardcoded threshold asserts flagged status triggers instantly when `amount > (0.5 * budget)`.
3. **Contextual Memory**: Rapid successive small transactions (`<10` minutes) MUST trigger the frequency burst logic by iterating through the contextual memory window.
