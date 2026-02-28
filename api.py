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
processing_index = 0
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
        "processed": processing_index,
        "has_pending": pending_assessment is not None,
    })


@app.route("/api/load-sample", methods=["POST"])
def load_sample():
    """Load the built-in sample dataset."""
    global all_transactions, processing_index, pending_assessment, loaded, risk_engine

    risk_engine = RiskEngine()
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_transactions.json")
    loader = DataLoader()
    all_transactions = loader.load(sample_path)
    processing_index = 0
    pending_assessment = None
    loaded = True

    return jsonify({
        "success": True,
        "total_transactions": len(all_transactions),
        "message": f"Loaded {len(all_transactions)} transactions from sample dataset",
    })


@app.route("/api/load", methods=["POST"])
def load_file():
    """Upload and load a CSV/JSON file."""
    global all_transactions, processing_index, pending_assessment, loaded, risk_engine

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
        processing_index = 0
        pending_assessment = None
        loaded = True

        return jsonify({
            "success": True,
            "total_transactions": len(all_transactions),
            "message": f"Loaded {len(all_transactions)} transactions",
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        os.unlink(tmp_path)


@app.route("/api/process-next", methods=["POST"])
def process_next():
    """Process the next transaction and return assessment if flagged."""
    global processing_index, pending_assessment

    if not loaded:
        return jsonify({"error": "No data loaded"}), 400
    if pending_assessment is not None:
        return jsonify({
            "status": "pending_decision",
            "assessment": _assessment_to_dict(pending_assessment),
        })
    if processing_index >= len(all_transactions):
        return jsonify({"status": "complete", "message": "All transactions processed"})

    txn = all_transactions[processing_index]
    assessment = risk_engine.evaluate_transaction(txn)
    risk_engine.add_transaction(txn)

    if assessment.is_flagged:
        pending_assessment = assessment
        return jsonify({
            "status": "flagged",
            "assessment": _assessment_to_dict(assessment),
        })
    else:
        processing_index += 1
        return jsonify({
            "status": "clean",
            "transaction": _txn_to_dict(txn),
            "processed": processing_index,
            "total": len(all_transactions),
        })


@app.route("/api/process-all", methods=["POST"])
def process_all():
    """Process all remaining unflagged transactions until one is flagged or done."""
    global processing_index, pending_assessment

    if not loaded:
        return jsonify({"error": "No data loaded"}), 400

    processed_count = 0
    while processing_index < len(all_transactions) and pending_assessment is None:
        txn = all_transactions[processing_index]
        assessment = risk_engine.evaluate_transaction(txn)
        risk_engine.add_transaction(txn)

        if assessment.is_flagged:
            pending_assessment = assessment
            return jsonify({
                "status": "flagged",
                "assessment": _assessment_to_dict(assessment),
                "processed": processing_index,
                "total": len(all_transactions),
                "batch_processed": processed_count,
            })
        else:
            processing_index += 1
            processed_count += 1

    return jsonify({
        "status": "complete",
        "processed": processing_index,
        "total": len(all_transactions),
        "batch_processed": processed_count,
    })


@app.route("/api/decide", methods=["POST"])
def decide():
    """Record user decision (cancel or proceed) for the pending flagged transaction."""
    global processing_index, pending_assessment

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
    processing_index += 1
    pending_assessment = None

    return jsonify({
        "success": True,
        "decision": decision,
        "processed": processing_index,
        "total": len(all_transactions),
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
