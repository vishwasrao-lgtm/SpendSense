"""SpendSense — Real-time financial transaction monitoring & intervention.

Run: streamlit run app.py
"""

import os
import time

import streamlit as st

from src.data_loader import DataLoader
from src.dashboard import Dashboard
from src.risk_engine import RiskEngine
from src.ui import InterventionUI

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SpendSense",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a polished look
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* Dark-ish accent tweaks */
    .stMetric { text-align: center; }
    .stMetric label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem; }
    h1 { color: #636EFA; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

if "risk_engine" not in st.session_state:
    st.session_state["risk_engine"] = RiskEngine()
    st.session_state["loaded"] = False
    st.session_state["processing_index"] = 0
    st.session_state["pending_assessment"] = None
    st.session_state["all_transactions"] = []

risk_engine: RiskEngine = st.session_state["risk_engine"]
intervention = InterventionUI()
dashboard = Dashboard()

# ---------------------------------------------------------------------------
# Sidebar — data loading
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/light-on.png", width=64)
    st.title("SpendSense")
    st.caption("Real-time transaction monitoring & intervention")
    st.markdown("---")

    data_source = st.radio("Data source", ["Sample dataset", "Upload file"], key="data_source")

    if data_source == "Sample dataset":
        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_transactions.json")
        if st.button("Load sample data", disabled=st.session_state["loaded"]):
            loader = DataLoader()
            txns = loader.load(sample_path)
            st.session_state["all_transactions"] = txns
            st.session_state["loaded"] = True
            st.session_state["processing_index"] = 0
            st.rerun()
    else:
        uploaded = st.file_uploader("Upload CSV or JSON", type=["csv", "json"])
        if uploaded and not st.session_state["loaded"]:
            # Write to temp and load
            import tempfile

            suffix = ".csv" if uploaded.name.endswith(".csv") else ".json"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            loader = DataLoader()
            txns = loader.load(tmp_path)
            st.session_state["all_transactions"] = txns
            st.session_state["loaded"] = True
            st.session_state["processing_index"] = 0
            st.rerun()

    if st.session_state["loaded"]:
        total = len(st.session_state["all_transactions"])
        processed = st.session_state["processing_index"]
        st.progress(processed / total if total else 0, text=f"Processed {processed}/{total}")

        if processed < total and st.session_state["pending_assessment"] is None:
            if st.button("▶️ Process next transaction"):
                txn = st.session_state["all_transactions"][processed]
                assessment = risk_engine.evaluate_transaction(txn)
                risk_engine.add_transaction(txn)
                if assessment.is_flagged:
                    st.session_state["pending_assessment"] = assessment
                else:
                    st.session_state["processing_index"] += 1
                st.rerun()

            if st.button("⏩ Auto-process all remaining"):
                st.session_state["auto_process"] = True
                st.rerun()

    st.markdown("---")
    st.caption("Built for HackSprint 2026")

# ---------------------------------------------------------------------------
# Main area — intervention or dashboard
# ---------------------------------------------------------------------------

st.title("💡 SpendSense Dashboard")

# Handle pending intervention
pending = st.session_state.get("pending_assessment")
if pending:
    decision = intervention.display_alert(pending.transaction, pending)
    if decision:
        risk_engine.record_decision(pending.transaction, pending, decision)
        st.session_state["pending_assessment"] = None
        st.session_state["processing_index"] += 1
        # Clear intervention state
        key_prefix = f"intervention_{pending.transaction.txn_id}"
        for k in list(st.session_state.keys()):
            if k.startswith(key_prefix):
                del st.session_state[k]
        st.rerun()
else:
    # Auto-process mode
    if st.session_state.get("auto_process") and st.session_state["loaded"]:
        total = len(st.session_state["all_transactions"])
        idx = st.session_state["processing_index"]
        if idx < total:
            txn = st.session_state["all_transactions"][idx]
            assessment = risk_engine.evaluate_transaction(txn)
            risk_engine.add_transaction(txn)
            if assessment.is_flagged:
                st.session_state["pending_assessment"] = assessment
                st.session_state["auto_process"] = False
            else:
                st.session_state["processing_index"] += 1
            st.rerun()
        else:
            st.session_state["auto_process"] = False

    # Show dashboard
    if st.session_state["loaded"]:
        dashboard.render(risk_engine)
    else:
        st.info("👈 Load a dataset from the sidebar to get started.")
