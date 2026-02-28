"""Dashboard: Streamlit + Plotly visualization of transactions and metrics."""

from typing import List

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.models import DashboardMetrics, InterceptLog, Transaction
from src.risk_engine import RiskEngine


class Dashboard:
    """Render comprehensive spending dashboard."""

    def render(self, risk_engine: RiskEngine) -> None:
        """Render the complete dashboard from in-memory data."""
        metrics = risk_engine.get_metrics()
        transactions = risk_engine.get_all_transactions()
        intercepts = risk_engine.get_intercept_log()

        self.render_metrics(metrics)
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs([
            "📋 Transaction Feed",
            "🛡️ Intercept Log",
            "📊 Patterns & Insights",
        ])

        with tab1:
            self.render_transaction_feed(transactions)
        with tab2:
            self.render_intercept_log(intercepts)
        with tab3:
            self.render_visualizations(transactions, metrics)

    # ------------------------------------------------------------------
    # Metrics bar
    # ------------------------------------------------------------------

    def render_metrics(self, metrics: DashboardMetrics) -> None:
        """Display key metrics in a horizontal row."""
        cols = st.columns(5)
        with cols[0]:
            st.metric("Total Transactions", metrics.total_transactions)
        with cols[1]:
            st.metric("Flagged", metrics.total_flagged)
        with cols[2]:
            st.metric("Money Saved", f"${metrics.money_saved:,.2f}")
        with cols[3]:
            st.metric("Override Rate", f"{metrics.override_rate:.1f}%")
        with cols[4]:
            st.metric("Impulsivity Score", f"{metrics.impulsivity_score:.0f}/100")

    # ------------------------------------------------------------------
    # Transaction feed
    # ------------------------------------------------------------------

    def render_transaction_feed(self, transactions: List[Transaction]) -> None:
        """Display transactions chronologically (most recent first) with color coding."""
        if not transactions:
            st.info("No transactions processed yet.")
            return

        st.markdown("### Live Transaction Feed")

        # Sort descending by timestamp
        sorted_txns = sorted(transactions, key=lambda t: t.timestamp, reverse=True)

        for txn in sorted_txns:
            color, icon = self._get_transaction_style(txn)
            with st.container():
                cols = st.columns([0.5, 2, 1, 1, 1, 1])
                with cols[0]:
                    st.markdown(f"### {icon}")
                with cols[1]:
                    st.markdown(f"**{txn.category.title()}** — {txn.recipient_status}")
                with cols[2]:
                    st.markdown(f"**${txn.amount:,.2f}**")
                with cols[3]:
                    st.markdown(txn.timestamp.strftime("%H:%M:%S"))
                with cols[4]:
                    st.markdown(txn.txn_id)
                with cols[5]:
                    st.markdown(f":{color}[●]")

    # ------------------------------------------------------------------
    # Intercept log
    # ------------------------------------------------------------------

    def render_intercept_log(self, intercepts: List[InterceptLog]) -> None:
        """Display all flagged transactions and user decisions."""
        if not intercepts:
            st.info("No transactions have been flagged yet.")
            return

        st.markdown("### Intervention History")

        # Filter controls
        filter_choice = st.selectbox(
            "Filter by decision:",
            ["All", "Cancelled", "Proceeded"],
            key="intercept_filter",
        )

        filtered = intercepts
        if filter_choice == "Cancelled":
            filtered = [e for e in intercepts if e.user_decision == "cancelled"]
        elif filter_choice == "Proceeded":
            filtered = [e for e in intercepts if e.user_decision == "proceeded"]

        for entry in reversed(filtered):  # most recent first
            decision_icon = "❌" if entry.user_decision == "cancelled" else "⚠️"
            with st.expander(
                f"{decision_icon} {entry.txn_id} — ${entry.transaction.amount:,.2f} "
                f"({entry.user_decision.title()})"
            ):
                st.markdown(f"**Timestamp:** {entry.decision_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Category:** {entry.transaction.category.title()}")
                st.markdown(f"**Decision:** {entry.user_decision.title()}")
                st.markdown("**Risk Flags:**")
                for explanation in entry.risk_explanations:
                    st.markdown(f"- {explanation}")

    # ------------------------------------------------------------------
    # Visualizations
    # ------------------------------------------------------------------

    def render_visualizations(
        self,
        transactions: List[Transaction],
        metrics: DashboardMetrics,
    ) -> None:
        """Render pie chart, timeline, and impulsivity gauge."""
        if not transactions:
            st.info("No data to visualize yet.")
            return

        col1, col2 = st.columns(2)

        with col1:
            self._render_category_pie(transactions)
        with col2:
            self._render_timeline(transactions)

        self._render_impulsivity_gauge(metrics.impulsivity_score)

    def _render_category_pie(self, transactions: List[Transaction]) -> None:
        """Pie chart: transaction distribution by category."""
        from collections import Counter

        counts = Counter(t.category for t in transactions)
        fig = px.pie(
            names=list(counts.keys()),
            values=list(counts.values()),
            title="Spending by Category",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    def _render_timeline(self, transactions: List[Transaction]) -> None:
        """Bar chart: transaction count per hour."""
        hourly: dict[int, int] = {}
        for t in transactions:
            h = t.timestamp.hour
            hourly[h] = hourly.get(h, 0) + 1

        hours = sorted(hourly.keys())
        fig = px.bar(
            x=[f"{h:02d}:00" for h in hours],
            y=[hourly[h] for h in hours],
            title="Transaction Frequency Over Time",
            labels={"x": "Hour", "y": "Count"},
            color_discrete_sequence=["#636EFA"],
        )
        fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    def _render_impulsivity_gauge(self, score: float) -> None:
        """Gauge chart for impulsivity score."""
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={"text": "Impulsivity Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#EF553B"},
                    "steps": [
                        {"range": [0, 33], "color": "#2ecc71"},
                        {"range": [33, 66], "color": "#f39c12"},
                        {"range": [66, 100], "color": "#e74c3c"},
                    ],
                },
            )
        )
        fig.update_layout(height=300, margin=dict(t=40, b=20, l=40, r=40))
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Impulsivity calculation (public for testing)
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_impulsivity_score(
        override_rate: float,
        late_night_count: int,
        total_count: int,
    ) -> float:
        """Calculate impulsivity score (0-100).

        0.6 × override_rate + 0.4 × late_night_pct
        """
        late_night_pct = (late_night_count / total_count * 100) if total_count > 0 else 0.0
        score = 0.6 * override_rate + 0.4 * late_night_pct
        return max(0.0, min(100.0, score))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_transaction_style(txn: Transaction):
        """Return (color_name, icon) based on transaction status."""
        if not txn.is_flagged:
            return "green", "🟢"
        if txn.user_decision == "cancelled":
            return "red", "🔴"
        if txn.user_decision == "proceeded":
            return "orange", "🟡"
        # Flagged but no decision yet (pending)
        return "orange", "🟠"
