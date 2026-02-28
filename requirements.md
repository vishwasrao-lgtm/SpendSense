# Requirements Document

## Introduction

SpendSense is a financial transaction monitoring and intervention system designed to help users make better spending decisions in real-time. The system loads transactions from a sample dataset, analyzes them using a dual-check risk engine (behavioral + contextual), and intervenes with explainable alerts before potentially regrettable purchases are completed. The system provides transparency through risk explanations, future impact projections, and a comprehensive dashboard for tracking spending patterns and intervention outcomes.

## Glossary

- **Sample_Dataset**: CSV or JSON file containing pre-defined financial transactions with realistic attributes
- **Data_Loader**: Component that loads transactions from the Sample_Dataset into memory
- **Risk_Engine**: Dual-check system that evaluates transactions using behavioral and contextual detection mechanisms
- **Behavioral_Detector**: Risk detection mechanism that analyzes spending patterns and timing
- **Contextual_Detector**: Risk detection mechanism that analyzes transaction context like recipients, frequency, device, and location
- **Intervention_UI**: User interface component that displays risk alerts and allows user decisions
- **Dashboard**: User interface component that displays transaction history, patterns, and metrics
- **Transaction**: A financial transaction record containing txn_id, user_id, timestamp, amount, category, recipient_status, monthly_budget_remaining, device_id, location, and channel
- **Risk_Flag**: An indicator that a transaction has triggered one or more risk detection rules
- **Intercept_Log**: In-memory historical record of all flagged transactions and user decisions
- **Money_Saved_Counter**: Metric tracking the total amount saved from cancelled transactions

## Requirements

### Requirement 1: Sample Dataset Loading

**User Story:** As a demo presenter, I want to load transactions from a sample dataset, so that I can demonstrate the system's risk detection capabilities with consistent data

#### Acceptance Criteria

1. THE Data_Loader SHALL load transactions from a CSV or JSON file containing fields: txn_id, user_id, timestamp, amount, category, recipient_status, monthly_budget_remaining, device_id, location, and channel
2. WHEN loading the Sample_Dataset, THE Data_Loader SHALL validate that all required fields are present
3. THE Data_Loader SHALL store all loaded transactions in memory for processing
4. WHEN a transaction record is invalid or missing required fields, THE Data_Loader SHALL skip that record and log a warning
5. THE Data_Loader SHALL support both CSV and JSON file formats

### Requirement 2: Behavioral Risk Detection

**User Story:** As a user, I want the system to detect risky spending patterns, so that I can avoid budget-draining purchases

#### Acceptance Criteria

1. WHEN a transaction amount exceeds 50% of the monthly_budget_remaining, THE Behavioral_Detector SHALL flag the transaction as budget drain risk
2. WHEN a transaction occurs between 10 PM and 4 AM, THE Behavioral_Detector SHALL flag the transaction as late-night regret pattern
3. WHEN the Behavioral_Detector flags a transaction, THE Risk_Engine SHALL record the specific behavioral rule that triggered
4. THE Behavioral_Detector SHALL evaluate every transaction in real-time

### Requirement 3: Contextual Risk Detection

**User Story:** As a user, I want the system to detect unusual transaction contexts, so that I can avoid impulsive or fraudulent purchases

#### Acceptance Criteria

1. WHEN a transaction recipient_status is marked as new, THE Contextual_Detector SHALL flag the transaction as new recipient risk
2. WHEN 3 or more transactions occur within a 10-minute window, THE Contextual_Detector SHALL flag subsequent transactions as frequency burst risk
3. WHEN a transaction device_id differs from recent transaction history, THE Contextual_Detector SHALL flag the transaction as device anomaly
4. WHEN a transaction location differs from recent transaction history, THE Contextual_Detector SHALL flag the transaction as location anomaly
5. WHEN the Contextual_Detector flags a transaction, THE Risk_Engine SHALL record the specific contextual rule that triggered

### Requirement 4: Risk Explanation

**User Story:** As a user, I want to understand why a transaction was flagged, so that I can make informed decisions

#### Acceptance Criteria

1. WHEN a transaction is flagged, THE Intervention_UI SHALL display all triggered risk rules with human-readable explanations
2. THE Intervention_UI SHALL display the transaction amount and remaining budget
3. THE Intervention_UI SHALL calculate and display the future value of the transaction amount using compound interest projections
4. WHEN displaying future impact, THE Intervention_UI SHALL show projections for 1 year, 5 years, and 10 years
5. THE Intervention_UI SHALL present risk information before allowing the user to proceed or cancel

### Requirement 5: Intervention Countdown

**User Story:** As a user, I want a cooling-off period before completing risky purchases, so that I can reconsider impulsive decisions

#### Acceptance Criteria

1. WHEN a transaction is flagged, THE Intervention_UI SHALL display a 10-second countdown timer
2. WHILE the countdown is active, THE Intervention_UI SHALL disable the "Proceed anyway" button
3. WHEN the countdown reaches zero, THE Intervention_UI SHALL enable the "Proceed anyway" button
4. THE Intervention_UI SHALL allow the "Cancel & Save" button to be clicked at any time during the countdown
5. WHEN the user clicks "Cancel & Save", THE Intervention_UI SHALL immediately cancel the transaction without waiting for countdown completion

### Requirement 6: Transaction Decision Recording

**User Story:** As a user, I want my intervention decisions recorded, so that I can review my spending behavior during the session

#### Acceptance Criteria

1. WHEN a user cancels a flagged transaction, THE Risk_Engine SHALL record the transaction, risk flags, and cancellation decision in the in-memory Intercept_Log
2. WHEN a user proceeds with a flagged transaction, THE Risk_Engine SHALL record the transaction, risk flags, and proceed decision in the in-memory Intercept_Log
3. WHEN a user cancels a transaction, THE Money_Saved_Counter SHALL increment by the transaction amount
4. THE Intercept_Log SHALL store the timestamp of each user decision
5. THE Intercept_Log SHALL store all risk explanations shown to the user

### Requirement 7: Live Transaction Feed

**User Story:** As a user, I want to see all transactions in real-time, so that I can monitor my spending activity

#### Acceptance Criteria

1. THE Dashboard SHALL display all transactions in chronological order with most recent first
2. WHEN a transaction is not flagged, THE Dashboard SHALL display it with a green color indicator
3. WHEN a transaction is flagged and cancelled, THE Dashboard SHALL display it with a red color indicator
4. WHEN a transaction is flagged and proceeded, THE Dashboard SHALL display it with a yellow color indicator
5. THE Dashboard SHALL display transaction details including amount, category, timestamp, and recipient_status
6. THE Dashboard SHALL update the transaction feed in real-time as new transactions are processed

### Requirement 8: Intercept Log Display

**User Story:** As a user, I want to review all flagged transactions and my decisions, so that I can understand my intervention history

#### Acceptance Criteria

1. THE Dashboard SHALL display all flagged transactions from the Intercept_Log
2. WHEN displaying intercept history, THE Dashboard SHALL show the transaction details, risk flags, and user decision
3. THE Dashboard SHALL show the timestamp of each intervention
4. THE Dashboard SHALL allow filtering intercepts by decision type (cancelled or proceeded)
5. THE Dashboard SHALL display risk explanations for each flagged transaction

### Requirement 9: Money Saved Tracking

**User Story:** As a user, I want to see how much money I've saved by cancelling risky transactions, so that I feel motivated to continue using the system

#### Acceptance Criteria

1. THE Dashboard SHALL display the Money_Saved_Counter prominently
2. WHEN the Money_Saved_Counter updates, THE Dashboard SHALL reflect the new total immediately
3. THE Dashboard SHALL display the Money_Saved_Counter as a cumulative total across all cancelled transactions
4. THE Dashboard SHALL format the Money_Saved_Counter as currency with appropriate symbols and decimal places

### Requirement 10: Pattern Visualization

**User Story:** As a user, I want to see visual representations of my spending patterns, so that I can identify areas for improvement

#### Acceptance Criteria

1. THE Dashboard SHALL display a pie chart showing transaction distribution by category
2. THE Dashboard SHALL display a timeline visualization showing transaction frequency over time
3. THE Dashboard SHALL calculate and display an impulsivity score based on override rate and late-night transactions
4. THE Dashboard SHALL display the total number of transactions processed
5. THE Dashboard SHALL display the total number of transactions flagged
6. THE Dashboard SHALL calculate and display the override rate as the percentage of flagged transactions that were proceeded

### Requirement 11: Demo Metrics

**User Story:** As a demo presenter, I want to track key system metrics, so that I can demonstrate effectiveness to judges

#### Acceptance Criteria

1. THE Dashboard SHALL display the total count of transactions processed from the Sample_Dataset
2. THE Dashboard SHALL display the total count of transactions flagged
3. THE Dashboard SHALL display the total amount saved from cancelled transactions
4. THE Dashboard SHALL calculate and display the override rate as a percentage
5. THE Dashboard SHALL update all metrics in real-time as transactions are processed
