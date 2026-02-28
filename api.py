"""SpendSense Flask REST API — wraps the Python risk engine for the Next.js frontend."""

import os
import tempfile
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.data_loader import DataLoader
from src.risk_engine import RiskEngine
from src.ui import InterventionUI

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Global state (in-memory, session-based)
# ---------------------------------------------------------------------------
risk_engine = RiskEngine()
all_transactions = []
pending_assessment = None
loaded = False


def _txn_to_dict(txn):
    """Serialize a Transaction to a JSON-safe dict."""
    return {
        "txn_id": txn.txn_id,
        "user_id": txn.user_id,
        "timestamp": txn.timestamp.isoformat(),
        "amount": txn.amount,
        "category": txn.category,
        "recipient_status": txn.recipient_status,
        "monthly_budget_remaining": txn.monthly_budget_remaining,
        "device_id": txn.device_id,
        "location": txn.location,
        "channel": txn.channel,
        "is_flagged": txn.is_flagged,
        "user_decision": txn.user_decision,
    }


def _flag_to_dict(flag):
    """Serialize a RiskFlag."""
    return {
        "rule_name": flag.rule_name,
        "explanation": flag.explanation,
        "severity": flag.severity,
        "detector_type": flag.detector_type,
    }


def _assessment_to_dict(assessment):
    """Serialize a RiskAssessment."""
    return {
        "transaction": _txn_to_dict(assessment.transaction),
        "risk_flags": [_flag_to_dict(f) for f in assessment.risk_flags],
        "is_flagged": assessment.is_flagged,
        "future_impact": InterventionUI.calculate_future_impact(assessment.transaction.amount),
    }


def _intercept_to_dict(entry):
    """Serialize an InterceptLog entry."""
    return {
        "txn_id": entry.txn_id,
        "transaction": _txn_to_dict(entry.transaction),
        "risk_flags": [_flag_to_dict(f) for f in entry.risk_flags],
        "user_decision": entry.user_decision,
        "decision_timestamp": entry.decision_timestamp.isoformat(),
        "risk_explanations": entry.risk_explanations,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def get_status():
    """Return current processing state."""
    return jsonify({
        "loaded": loaded,
        "total_transactions": len(all_transactions),
        "processed": len(all_transactions),
        "has_pending": pending_assessment is not None,
    })


def _auto_process_all():
    """Process all loaded transactions through the risk engine (no user intervention)."""
    global all_transactions
    for txn in all_transactions:
        assessment = risk_engine.evaluate_transaction(txn)
        risk_engine.add_transaction(txn)
        # Auto-processed flagged transactions: record as "proceeded" in intercept log
        if assessment.is_flagged:
            risk_engine.record_decision(txn, assessment, "proceeded")


@app.route("/api/load-sample", methods=["POST"])
def load_sample():
    """Load and auto-process the built-in sample dataset."""
    global all_transactions, pending_assessment, loaded, risk_engine

    risk_engine = RiskEngine()
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_transactions.json")
    loader = DataLoader()
    all_transactions = loader.load(sample_path)
    pending_assessment = None
    loaded = True

    _auto_process_all()

    return jsonify({
        "success": True,
        "total_transactions": len(all_transactions),
        "message": f"Loaded and processed {len(all_transactions)} transactions",
    })


@app.route("/api/load", methods=["POST"])
def load_file():
    """Upload, load, and auto-process a CSV/JSON file."""
    global all_transactions, pending_assessment, loaded, risk_engine

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    suffix = ".csv" if file.filename.endswith(".csv") else ".json"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        risk_engine = RiskEngine()
        loader = DataLoader()
        all_transactions = loader.load(tmp_path)
        pending_assessment = None
        loaded = True

        _auto_process_all()

        return jsonify({
            "success": True,
            "total_transactions": len(all_transactions),
            "message": f"Loaded and processed {len(all_transactions)} transactions",
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        os.unlink(tmp_path)


@app.route("/api/add-transaction", methods=["POST"])
def add_transaction():
    """Add a single manual transaction, evaluate it, and return risk assessment."""
    global pending_assessment, all_transactions

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Required fields for a manual transaction
    try:
        amount = float(data.get("amount", 0))
        category = str(data.get("category", "shopping"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    from src.models import Transaction

    # Parse optional timestamp
    ts = datetime.now()
    if data.get("timestamp"):
        try:
            ts = datetime.fromisoformat(str(data["timestamp"]))
        except (ValueError, TypeError):
            pass

    txn = Transaction(
        txn_id=f"MANUAL_{len(all_transactions) + 1:05d}",
        user_id=data.get("user_id", "USR_MANUAL"),
        timestamp=ts,
        amount=amount,
        category=category,
        recipient_status=data.get("recipient_status", "new"),
        monthly_budget_remaining=float(data.get("monthly_budget_remaining", max(2000, amount * 3))),
        device_id=data.get("device_id", "WEB_BROWSER"),
        location=data.get("location", "Web App"),
        channel="web",
    )

    assessment = risk_engine.evaluate_transaction(txn)
    risk_engine.add_transaction(txn)
    all_transactions.append(txn)

    if assessment.is_flagged:
        pending_assessment = assessment
        return jsonify({
            "status": "flagged",
            "assessment": _assessment_to_dict(assessment),
        })
    else:
        return jsonify({
            "status": "clean",
            "transaction": _txn_to_dict(txn),
            "message": "Transaction added successfully",
        })


@app.route("/api/decide", methods=["POST"])
def decide():
    """Record user decision (cancel or proceed) for the pending flagged transaction."""
    global pending_assessment

    if pending_assessment is None:
        return jsonify({"error": "No pending assessment"}), 400

    data = request.get_json()
    decision = data.get("decision")
    if decision not in ("cancelled", "proceeded"):
        return jsonify({"error": "Decision must be 'cancelled' or 'proceeded'"}), 400

    risk_engine.record_decision(
        pending_assessment.transaction,
        pending_assessment,
        decision,
    )
    pending_assessment = None

    return jsonify({
        "success": True,
        "decision": decision,
    })


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    """Return all processed transactions."""
    txns = risk_engine.get_all_transactions()
    return jsonify({
        "transactions": [_txn_to_dict(t) for t in txns],
        "total": len(txns),
    })


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Return dashboard metrics."""
    m = risk_engine.get_metrics()
    return jsonify({
        "total_transactions": m.total_transactions,
        "total_flagged": m.total_flagged,
        "money_saved": m.money_saved,
        "override_rate": m.override_rate,
        "impulsivity_score": m.impulsivity_score,
    })


@app.route("/api/intercept-log", methods=["GET"])
def get_intercept_log():
    """Return intercept log, optionally filtered by decision type."""
    decision_filter = request.args.get("filter")
    entries = risk_engine.get_intercept_log(decision_filter)
    return jsonify({
        "intercepts": [_intercept_to_dict(e) for e in entries],
        "total": len(entries),
    })


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
