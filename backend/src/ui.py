"""InterventionUI: Streamlit-based risk alert display with countdown."""

import time
from typing import Dict

import streamlit as st

from src.models import RiskAssessment, Transaction


ANNUAL_RETURN_RATE = 0.07  # 7% for future-impact projections


class InterventionUI:
    """Render risk alerts and collect user decisions via Streamlit."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display_alert(
        self,
        transaction: Transaction,
        risk_assessment: RiskAssessment,
    ) -> str:
        """Show intervention modal and return 'cancelled' or 'proceeded'.

        This is designed to be called inside a Streamlit rendering loop.
        The method uses st.session_state to track countdown and decision.
        """
        key_prefix = f"intervention_{transaction.txn_id}"

        # Initialise session state for this transaction
        if f"{key_prefix}_decision" not in st.session_state:
            st.session_state[f"{key_prefix}_decision"] = None
            st.session_state[f"{key_prefix}_countdown_start"] = time.time()

        # If decision already made, return it
        if st.session_state[f"{key_prefix}_decision"]:
            return st.session_state[f"{key_prefix}_decision"]

        # --- Render the alert ---
        st.markdown("---")
        st.markdown("### ⚠️ Risk Alert")

        # Transaction details
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Transaction Amount", f"${transaction.amount:,.2f}")
        with col2:
            st.metric("Budget Remaining", f"${transaction.monthly_budget_remaining:,.2f}")

        st.markdown(f"**Category:** {transaction.category.title()}  ·  **Recipient:** {transaction.recipient_status}")

        # Risk flags
        st.markdown("#### 🔍 Why was this flagged?")
        for flag in risk_assessment.risk_flags:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(flag.severity, "⚪")
            st.markdown(f"{severity_icon} **{flag.rule_name.replace('_', ' ').title()}** — {flag.explanation}")

        # Future impact
        st.markdown("#### 💰 Future Impact (if invested instead)")
        projections = self.calculate_future_impact(transaction.amount)
        pcols = st.columns(3)
        for col, (label, value) in zip(pcols, projections.items()):
            with col:
                st.metric(label, f"${value:,.2f}")

        # Countdown logic
        elapsed = time.time() - st.session_state[f"{key_prefix}_countdown_start"]
        remaining = max(0, 10 - int(elapsed))

        # Countdown display
        if remaining > 0:
            st.warning(f"⏳ Cooling-off period: **{remaining}** seconds remaining")

        # Decision buttons
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("❌ Cancel & Save", key=f"{key_prefix}_cancel", type="primary"):
                st.session_state[f"{key_prefix}_decision"] = "cancelled"
                st.rerun()
        with bcol2:
            proceed_disabled = remaining > 0
            if st.button(
                "✅ Proceed anyway",
                key=f"{key_prefix}_proceed",
                disabled=proceed_disabled,
            ):
                st.session_state[f"{key_prefix}_decision"] = "proceeded"
                st.rerun()

        # Auto-refresh while countdown is active
        if remaining > 0:
            time.sleep(1)
            st.rerun()

        return st.session_state.get(f"{key_prefix}_decision", "")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_future_impact(amount: float) -> Dict[str, float]:
        """Calculate compound interest projections for 1, 5, and 10 years.

        Formula: FV = amount × (1 + rate)^years
        """
        return {
            "1 Year": amount * (1 + ANNUAL_RETURN_RATE) ** 1,
            "5 Years": amount * (1 + ANNUAL_RETURN_RATE) ** 5,
            "10 Years": amount * (1 + ANNUAL_RETURN_RATE) ** 10,
        }

    @staticmethod
    def render_countdown(seconds_remaining: int) -> None:
        """Render a visual countdown timer."""
        progress = 1.0 - (seconds_remaining / 10.0)
        st.progress(progress, text=f"⏳ {seconds_remaining}s remaining")
