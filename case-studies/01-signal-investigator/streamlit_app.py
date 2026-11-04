
"""Signal Investigator — Executive Dashboard."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ga4_reporting_adapter import build_reporting_rows


ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "outputs" / "ga4_executive_reporting.json"
FIXTURES = ROOT / "tests" / "fixtures"


def load_investigations():
    """Load generated investigations or bundled demo evidence."""

    if REPORT.exists():
        return json.loads(REPORT.read_text(encoding="utf-8"))

    # Portable demo fallback for Streamlit Cloud.
    diagnostics = json.loads(
        (FIXTURES / "ga4_diagnostics.json")
        .read_text(encoding="utf-8")
    )
    ai_report = json.loads(
        (
            FIXTURES /
            "ga4_ai_structured_2020-12-07.json"
        ).read_text(encoding="utf-8")
    )

    return build_reporting_rows(diagnostics, ai_report)


st.set_page_config(
    page_title="Signal Investigator",
    page_icon="📊",
    layout="wide",
)

st.title("Signal Investigator")
st.caption(
    "AI-Powered Executive Analytics | "
    "Historical GA4 Public Ecommerce Sample"
)

rows = sorted(
    load_investigations(),
    key=lambda row: row["investigation_date"],
)

dates = [row["investigation_date"] for row in rows]

st.sidebar.header("Investigation Explorer")

selected_date = st.sidebar.selectbox(
    "Select investigation date",
    dates,
    index=len(dates) - 1,
)

st.sidebar.button("Refresh dashboard")

selected = next(
    row for row in rows
    if row["investigation_date"] == selected_date
)

st.subheader(f"Performance Investigation — {selected_date}")

st.caption(
    f"Source: {selected['source']} | "
    f"Scope: {selected['scope']}"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Observed Sessions",
        f"{selected['observed_sessions']:,}",
        f"{selected['session_change_pct']:+.1f}% vs baseline",
    )

with col2:
    st.metric(
        "Purchase Session Rate",
        f"{selected['observed_purchase_rate_pct']:.2f}%",
        (
            f"{selected['purchase_rate_change_pct']:+.1f}% "
            "relative"
        ),
    )

with col3:
    st.metric(
        "Estimated Purchasing-Session Gap",
        f"{selected['estimated_purchase_session_gap']:.1f}",
        help=(
            "Difference from baseline expectation. "
            "Not confirmed lost orders or revenue."
        ),
    )

if selected["alert_status"] == "no_qualifying_anomaly":
    st.info(
        "No qualifying anomaly alert was triggered "
        "for the selected date."
    )
else:
    st.warning(
        f"Detection status: {selected['alert_status']}"
    )

st.divider()

trend = pd.DataFrame(rows)
trend["investigation_date"] = pd.to_datetime(
    trend["investigation_date"]
)

left, right = st.columns(2)

with left:
    st.subheader("Sessions vs Historical Baseline")

    chart_data = trend[
        [
            "investigation_date",
            "observed_sessions",
            "baseline_sessions",
        ]
    ].rename(
        columns={
            "observed_sessions": "Observed",
            "baseline_sessions": "Baseline",
        }
    )

    st.line_chart(
        chart_data,
        x="investigation_date",
        y=["Observed", "Baseline"],
    )

with right:
    st.subheader("Purchase Session Rate (%)")

    rate_data = trend[
        [
            "investigation_date",
            "observed_purchase_rate_pct",
            "baseline_purchase_rate_pct",
        ]
    ].rename(
        columns={
            "observed_purchase_rate_pct": "Observed",
            "baseline_purchase_rate_pct": "Baseline",
        }
    )

    st.line_chart(
        rate_data,
        x="investigation_date",
        y=["Observed", "Baseline"],
    )

st.caption(
    "Baselines use the four previous matching weekdays. "
    "Purchase-session rates represent sessions with purchases, "
    "not total orders."
)

st.divider()
st.subheader("AI Executive Investigation")

if selected["has_ai_investigation"]:

    review = selected["factual_review_status"]

    if review == "pending":
        st.warning("AI-generated findings — factual review pending")
    else:
        st.info(f"Factual review status: {review}")

    st.markdown(selected["executive_summary"])

    if selected["why_no_alert"]:
        with st.expander("Alert Decision Explanation"):
            st.write(selected["why_no_alert"])

    st.subheader("Recommended Analytical Checks")

    checks = json.loads(
        selected["recommended_checks_json"] or "[]"
    )

    for index, check in enumerate(checks, start=1):
        with st.expander(
            f"{index}. {check['action']}"
        ):
            st.write(check["purpose"])
            st.write(
                "Required evidence:",
                ", ".join(check["inputs_needed"]),
            )

    st.subheader("Hypotheses to Validate")

    hypotheses = json.loads(
        selected["hypotheses_json"] or "[]"
    )

    for hypothesis in hypotheses:
        with st.expander(hypothesis["title"]):
            st.write(hypothesis["explanation"])
            st.write(
                "Validation:",
                hypothesis["validation_check"],
            )

else:
    st.info(
        "No AI investigation has been generated for "
        "this date. Verified performance metrics are "
        "still available above."
    )

st.divider()

with st.expander("View All Reporting Records"):
    st.dataframe(
        trend[
            [
                "investigation_date",
                "observed_sessions",
                "session_change_pct",
                "observed_purchase_rate_pct",
                "purchase_rate_change_pct",
                "alert_status",
                "factual_review_status",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

st.caption(
    "Signal Investigator | Historical demonstration dataset | "
    "AI hypotheses are not verified root causes."
)
