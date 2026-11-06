"""Signal Investigator | Maxim — executive report experience.

Inspired by the user-provided 'Executive Anomaly Report' layout. The underlying
numbers come exclusively from validated local GA4 reporting data, never from the
visual reference. This application makes no LLM / BigQuery call during a rerun.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard_presentation import (
    CHART_FIELDS,
    fallback_spec,
    severity,
    status_label,
    validate_dashboard_spec,
)
from src.executive_report import (
    alert_reason,
    decision,
    email_brief,
    hypotheses,
    kpi_definitions,
    suggested_owner_role,
    recommended_checks,
    report_window,
    severity_counts,
    short_summary,
    executive_headline, display_action_title,
)
from src.executive_pdf import generate_pdf
from src.financial_evidence import reporting_financial_evidence
from src.email_delivery import (
    EXPECTED_SENDER, compose_sample, validate_recipient, begin_outlook_sign_in,
    complete_outlook_sign_in, send_graph_email,
)
from src.report_filters import (reporting_windows, rows_for_window, selectable_investigations, investigation_option)
from src.ga4_reporting_adapter import build_reporting_rows

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "outputs" / "ga4_executive_reporting.json"
FIXTURES = ROOT / "tests" / "fixtures"
AVATAR = ROOT / "assets" / "maxim-avatar.svg"
# A fixed public avatar from the licensed DiceBear Avataaars style. For a
# self-contained deployment, run scripts/fetch_maxim_avatar.py once and commit
# the resulting SVG alongside AVATAR_LICENSE.md.
AVATAR_URL = "https://api.dicebear.com/10.x/avataaars/svg?seed=MaximSignalInvestigator"

st.set_page_config(
    page_title="Signal Investigator | Maxim",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = r"""
<style>
/* Reference: white executive report cards against soft stone, elegant display titles. */
:root {
  --paper: #f4f5f7; --ink: #171e2d; --muted: #647084;
  --border: #e3e6eb; --navy: #111827; --accent: #be5219;
  --green: #23834e; --yellow: #a36c08; --red: #bd4317;
}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:var(--paper);}
header[data-testid="stHeader"]{background:var(--paper);}
#MainMenu,footer{visibility:hidden;}
.block-container{max-width:1480px;padding:5rem 2.8rem 3.5rem;}
[data-testid="stSidebar"]{display:none;}
[data-testid="stMarkdownContainer"]{overflow-wrap:anywhere;}
h1,h2,h3{letter-spacing:-.02em;color:var(--ink);}
h1,h2{font-family:Georgia,'Times New Roman',serif;}
[data-testid="stDownloadButton"] button{
  background:#fff;border:1px solid #d9dde4;color:var(--ink);border-radius:7px;
  font-weight:650;font-size:.85rem;padding:.35rem .75rem;
}
[data-testid="stDownloadButton"] button:hover{border-color:#75849a;color:#111827;}
.sr-appbar{display:flex;align-items:center;gap:12px;margin:0 0 12px;min-height:38px;}
.sr-icon{width:31px;height:31px;border-radius:7px;display:flex;align-items:center;
  justify-content:center;color:#fff;background:#121a29;font-weight:800;font-size:18px;}
.sr-brand{font-size:.94rem;font-weight:780;color:#202637;line-height:1.15;}
.sr-brand-sub{font-size:.73rem;color:#7b8594;}
.sr-demo{font-size:.7rem;color:#7a8491;background:#ebedf1;border:1px solid #dfe3e9;
  border-radius:99px;padding:6px 10px;display:inline-block;}
/* All controls live inside the same report surface. No scrollable date strip. */
.st-key-sr-report-head{
  background:#fff;border:1px solid #e1e5ea;border-radius:10px;
  padding:19px 20px 14px;margin:2px 0 17px;
  box-shadow:0 1px 2px rgba(15,23,42,.015);
}
.st-key-sr-report-head [data-testid="stWidgetLabel"] p {
  font-size:.7rem!important;font-weight:800!important;letter-spacing:.07em;
  text-transform:uppercase;color:#647084!important;
}
.st-key-sr-report-head [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  min-height:46px;background:#f4f5f7;border:1px solid #edf0f3;border-radius:8px;
}
.st-key-sr-report-head [data-testid="stSelectbox"] div[data-baseweb="select"] {width:100%;}
.sr-meta-static{height:77px;background:#f4f5f7;border-radius:8px;padding:10px 13px;
  display:flex;flex-direction:column;justify-content:center;min-width:0;}
.sr-meta-static .sr-meta-val{font-size:.81rem;line-height:1.4;overflow-wrap:break-word;}
.sr-hero-grid{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(0,1fr);
  align-items:stretch;gap:16px;margin:0 0 16px;}
.sr-hero-grid .sr-card{margin:0;height:100%;min-width:0;}
.sr-hero-grid .sr-decision{margin:0;height:100%;min-width:0;}
.sr-kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:11px;margin:0 0 15px;}
.sr-hyp-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:8px 0 16px;}
.sr-hyp-card{height:100%;display:flex;flex-direction:column;box-sizing:border-box;}
.sr-hyp-footer{margin-top:auto;padding-top:15px;border-top:1px solid #eceff3;}
.sr-role{font-size:.73rem;font-weight:750;color:#25324a;margin-top:4px;}
.sr-table-wrap{background:#fff;border:1px solid var(--border);border-radius:10px;
  padding:7px 18px 5px;overflow-x:auto;margin-bottom:16px;}
.sr-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:.82rem;color:#273143;}
.sr-table th{padding:12px 8px;border-bottom:1px solid #e6e9ee;text-align:left;
  color:#727f90;font-size:.66rem;font-weight:800;letter-spacing:.06em;}
.sr-table td{padding:14px 8px;border-bottom:1px solid #e6e9ee;vertical-align:top;overflow-wrap:anywhere;line-height:1.45;}
.sr-table tr:last-child td{border-bottom:none;}
.sr-priority{color:#a95316;font-size:.75rem;font-weight:800;}
.sr-assignment{color:#697587;font-size:.7rem;}
/* Financial evidence is a separate validated card, not a revenue loss claim. */
.sr-finance{display:grid;grid-template-columns:1fr 1fr 1fr;gap:13px;
  background:#ffffff;border:1px solid #e1e5ea;border-radius:11px;padding:17px 22px;margin:0 0 18px;
  align-items:stretch;box-sizing:border-box;}
.sr-finance-cell{border-right:1px solid #e7eaf0;padding-right:14px;min-width:0;}
.sr-finance-cell:last-of-type{border-right:none;}
.sr-finance-number{font-size:1.42rem;font-weight:800;color:#151d2b;}
.sr-finance-detail{font-size:.78rem;color:#5c6779;line-height:1.5;}
@media(max-width:760px){.sr-finance{grid-template-columns:1fr;}.sr-finance-cell{border-right:none;border-bottom:1px solid #e7eaf0;padding-bottom:10px;}}
/* Report cards */
.sr-card{background:#fff;border:1px solid var(--border);border-radius:11px;padding:19px 22px;margin:0 0 14px;}
.sr-kicker{font-size:.68rem;font-weight:800;color:#747f8e;letter-spacing:.095em;text-transform:uppercase;}
.sr-title{font-family:Georgia,'Times New Roman',serif;font-size:clamp(1.45rem,2.5vw,2.3rem);
  font-weight:750;color:#171d2b;margin:6px 0 11px;line-height:1.18;letter-spacing:-.036em;
  max-width:850px;}
.sr-report-header{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;}
.sr-subtitle{font-size:.81rem;color:#7b8592;margin-top:-6px;}
.sr-status{display:inline-block;border-radius:99px;padding:6px 11px;font-size:.75rem;font-weight:780;white-space:nowrap;}
.sr-status-green{background:#e3f5e9;color:#196c40;}.sr-status-yellow{background:#ffedc7;color:#885b05;}
.sr-status-red{background:#fce2db;color:#9f3718;}.sr-status-unknown{background:#e9edf2;color:#525e70;}
.sr-meta-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:9px;}
.sr-meta{padding:11px 13px;background:#f4f5f7;border-radius:8px;min-width:0;}
.sr-meta--watch{background:#fff0e6;}
.sr-meta-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.07em;color:#758092;font-weight:780;}
.sr-meta-val{font-size:.88rem;font-weight:700;color:#283142;margin-top:4px;}
.sr-note{font-size:.77rem;color:#697587;margin:11px 0 0;}
.sr-block-title{font-family:Georgia,'Times New Roman',serif;color:#1e2430;font-weight:750;
  font-size:1.33rem;margin:1.0rem 0 .62rem;}
.sr-micro{font-size:.72rem;color:#788292;}
.sr-persona{display:flex;align-items:center;gap:10px;margin:2px 0 13px;}
.sr-persona-name{font-weight:790;font-size:.92rem;color:#1b2638;}
.sr-persona-job{font-size:.72rem;color:#6e7c8d;}
.sr-summary-body{font-family:Georgia,'Times New Roman',serif;font-size:1.03rem;line-height:1.58;color:#1a2232;}
.sr-review{font-size:.75rem;color:#7a8493;border-top:1px solid #e8ebef;padding-top:11px;margin-top:13px;}
.sr-decision{background:#111827;color:#fff;border-radius:11px;padding:22px 23px;height:100%;min-height:280px;}
.sr-decision-title{font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;color:#bfc7d7;font-weight:800;}
.sr-decision-action{font-family:Georgia,'Times New Roman',serif;font-size:1.27rem;line-height:1.35;
  color:white;margin:13px 0 16px;font-weight:700;}
.sr-decision-line{display:flex;justify-content:space-between;gap:10px;padding:9px 0;
  border-top:1px solid #3b4352;font-size:.76rem;color:#d7dce5;}
.sr-decision-line strong{color:#fff;font-weight:700;text-align:right;}
.sr-reco-note{font-size:.75rem;color:#aebacc;line-height:1.5;margin-top:9px;}
.sr-kpi{border:1px solid #e1e4e9;background:#fff;border-radius:10px;padding:13px 13px 10px;min-height:174px;min-width:0;box-sizing:border-box;display:flex;flex-direction:column;}
.sr-kpi-watch{border-color:#f2cda9;}.sr-kpi-red{border-color:#e7a29a;}
.sr-kpi-label{font-size:.77rem;color:#464f5e;margin:0 0 5px;min-height:35px;}
.sr-kpi-number{font-size:clamp(1.1rem,2vw,1.5rem);font-weight:820;color:#1d2635;letter-spacing:-.025em;}
.sr-kpi-change{font-size:.73rem;color:#6d7788;min-height:25px;margin-top:3px;}
.sr-kpi-footer{display:flex;justify-content:space-between;align-items:center;margin-top:auto;}
.sr-kpi-tag{font-size:.62rem;border-radius:99px;background:#f1f3f6;color:#647083;padding:3px 7px;}
.sr-kpi-watch .sr-kpi-tag{background:#fff0dc;color:#895b09;}
.sr-spark{width:100%;height:26px;margin-top:3px;}
.sr-signal-wrap{background:#fff;border:1px solid #f0d4c2;border-radius:10px;overflow:hidden;margin:5px 0 12px;}
.sr-signal-wrap.sr-signal-red{border-color:#e8b0ae;}
.sr-signal-wrap.sr-signal-red .sr-signal-band{background:#fff0ee;}
.sr-signal-wrap.sr-signal-red .sr-signal-caption{color:#b42318;}
.sr-signal-band{background:#fff0e5;padding:15px 20px;display:flex;align-items:flex-start;
  justify-content:space-between;gap:10px;}
.sr-signal-title{font-family:Georgia,'Times New Roman',serif;font-size:1.3rem;color:#202537;font-weight:750;margin:5px 0 0;}
.sr-signal-caption{font-size:.75rem;color:#a34e20;font-weight:760;letter-spacing:.07em;text-transform:uppercase;}
.sr-signal-copy{font-size:.84rem;line-height:1.58;color:#384356;}
.sr-signal-body{padding:18px 20px 16px;}
.sr-hyp-card{border:1px solid #e2e5e9;border-radius:9px;padding:17px;background:#fff;min-height:252px;}
.sr-hyp-number{font-size:.69rem;letter-spacing:.05em;color:#6c7585;font-weight:780;}
.sr-hyp-title{font-size:.92rem;font-weight:780;color:#202938;margin:9px 0;line-height:1.35;}
.sr-hyp-detail{font-size:.77rem;color:#535e6e;line-height:1.5;}
.sr-unverified{background:#f2f4f6;border-radius:99px;font-size:.64rem;color:#68778a;padding:4px 7px;}
.sr-quiet{font-size:.82rem;color:#6c798b;line-height:1.6;}
.sr-footer{font-size:.72rem;color:#7c8795;margin:1.2rem 0;}
[data-testid="stDataFrame"]{border-radius:8px;overflow:hidden;}
[data-testid="stExpander"]{background:#fff;border:1px solid #e1e5eb;border-radius:9px;}
@media(max-width:850px){
 .block-container{padding:5rem .9rem 2rem;}.si-day{min-width:83px;flex-basis:83px;}
 .sr-card{padding:15px;}.sr-meta-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
 .sr-hero-grid{grid-template-columns:1fr;}.sr-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr));}
 .sr-hyp-grid{grid-template-columns:1fr;}.sr-report-header{flex-wrap:wrap;}
}
@media(max-width:600px){
 .sr-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
 .sr-kpi{min-height:160px;}.st-key-sr-report-head{padding:15px 12px;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))



def load_rows() -> list[dict]:
    """Load local investigation first, then the deployed report snapshot."""

    snapshot = ROOT / "demo_data" / "executive_report.json"

    if REPORT.exists():
        # Localhost: latest BigQuery + Python + Gemini investigation
        rows = read_json(REPORT)

    elif snapshot.exists():
        # Streamlit Cloud: saved report committed to GitHub
        rows = read_json(snapshot)

    else:
        # Existing fallback for development
        diagnostics = read_json(FIXTURES / "ga4_diagnostics.json")
        ai_report = read_json(
            FIXTURES / "ga4_ai_structured_2020-12-07.json"
        )
        rows = build_reporting_rows(diagnostics, ai_report)

    if not rows:
        raise ValueError("No reporting records available.")

    seen = set()

    for item in rows:
        key = (
            date.fromisoformat(item["investigation_date"]).isoformat(),
            item["scope"],
        )

        if key in seen:
            raise ValueError(f"Duplicate investigation: {key}")

        seen.add(key)

    return sorted(rows, key=lambda r: r["investigation_date"])



def get_layout(rows: list[dict], selected: dict) -> tuple[dict, str]:
    """Apply validated Gemini choices without executing its suggested code."""
    if severity(selected) == "red":
        # Prior saved layout was generated for the historical watchlist. Prefer
        # purchase-rate evidence first for an actual detector-produced red alert.
        spec = fallback_spec(selected)
        spec["charts"] = ["purchase_rate_vs_baseline", "sessions_vs_baseline"]
        return validate_dashboard_spec(spec, rows, selected), "Validated red-alert evidence layout"
    day = selected["investigation_date"]
    paths = [
        ROOT / "outputs" / f"ga4_dashboard_spec_{day}.json",
        FIXTURES / f"ga4_dashboard_spec_{day}.json",
    ]
    for path in paths:
        if not path.exists():
            continue
        try:
            content = read_json(path)
            if content.get("investigation_date") != day:
                raise ValueError("Incorrect layout date")
            return validate_dashboard_spec(content["dashboard_spec"], rows, selected), "Gemini-selected visuals · validated"
        except (KeyError, TypeError, ValueError, OSError) as exc:
            st.warning(f"Saved dashboard selection rejected: {exc}. Using safe defaults.")
            break
    return fallback_spec(selected), "Default evidence layout"


def percent_signed(num: object) -> str:
    return f"{num:+.1f}%" if isinstance(num, (int, float)) else "Unavailable"


def mini_sparkline(rows: list[dict], field: str, hue: str = "#42556f") -> str:
    """Small static vector trends; does not represent statistical significance."""
    import math
    values = [r.get(field) for r in rows]
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        return ""
    lo, hi = min(values), max(values)
    span = max(float(hi - lo), 0.00001)
    pts = " ".join(
        f"{3 + i * 94 / max(len(values)-1,1):.1f},{24 - (float(v)-lo)/span*19:.1f}"
        for i, v in enumerate(values)
    )
    return (
        '<svg class="sr-spark" viewBox="0 0 100 28" aria-hidden="true" '
        'preserveAspectRatio="none">'
        f'<polyline points="{pts}" fill="none" stroke="{hue}" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" /></svg>'
    )


def kpi_html(item: dict, rows: list[dict], selected: dict, priority: set[str]) -> str:
    chart_field = {
        "observed_sessions": "observed_sessions",
        "baseline_sessions": "baseline_sessions",
        "observed_purchase_rate_pct": "observed_purchase_rate_pct",
        "baseline_purchase_rate_pct": "baseline_purchase_rate_pct",
        "session_change_pct": "session_change_pct",
        "estimated_purchase_session_gap": "estimated_purchase_session_gap",
    }[item["key"]]
    focus = item["key"] in priority
    kind = severity(selected)
    caution = kind in ("yellow", "red") and item["key"] in (
        "observed_purchase_rate_pct", "estimated_purchase_session_gap",
    )
    css = ("sr-kpi-red" if kind == "red" else "sr-kpi-watch") if caution else ""
    indicator = ("Alert" if kind == "red" else "Watch") if caution else ("Priority" if focus else "Context")
    return (
        f'<div class="sr-kpi {css}">'
        f'<div class="sr-kpi-label">{escape(item["title"])}</div>'
        f'<div class="sr-kpi-number">{escape(item["value"])}</div>'
        f'<div class="sr-kpi-change">{escape(item["delta"])}</div>'
        + mini_sparkline(rows, chart_field, "#c16a25" if caution else "#42556f")
        + f'<div class="sr-kpi-footer"><span class="sr-kpi-tag">{indicator}</span></div></div>'
    )


def plot_evidence(key: str, rows: list[dict], selected_day: str):
    """Build only approved chart types from real available columns."""
    chart_map = {
        "sessions_vs_baseline": ("Observed sessions against historical baseline", "Sessions",
            {"observed_sessions": "Observed", "baseline_sessions": "Baseline"}),
        "purchase_rate_vs_baseline": ("Purchase-session rate against historical baseline", "Rate (%)",
            {"observed_purchase_rate_pct": "Observed", "baseline_purchase_rate_pct": "Baseline"}),
        "session_change_trend": ("Relative session change by day", "Change (%)",
            {"session_change_pct": "Observed"}),
        "purchase_rate_change_trend": ("Relative purchase-rate change by day", "Change (%)",
            {"purchase_rate_change_pct": "Observed"}),
    }
    if key not in CHART_FIELDS:
        raise ValueError("Unapproved chart requested")
    heading, ylabel, columns = chart_map[key]
    df = pd.DataFrame(rows)
    df["investigation_date"] = pd.to_datetime(df["investigation_date"])
    long_df = df[["investigation_date", *columns]].rename(columns=columns).melt(
        "investigation_date", var_name="Series", value_name="Value"
    )
    domain = list(columns.values())
    colors = ["#182335", "#93a1b4"] if len(domain) > 1 else ["#182335"]
    x = alt.X("investigation_date:T", axis=alt.Axis(title=None, format="%b %d", labelAngle=0, tickCount=6))
    y = alt.Y("Value:Q", title=ylabel, scale=alt.Scale(zero=False))
    base = alt.Chart(long_df).encode(
        x=x, y=y,
        color=alt.Color("Series:N", title=None, scale=alt.Scale(domain=domain, range=colors),
                        legend=alt.Legend(orient="top", symbolType="stroke")),
        tooltip=[alt.Tooltip("investigation_date:T", title="Date", format="%d %b %Y"),
                 "Series:N", alt.Tooltip("Value:Q", title=ylabel, format=",.2f")],
    )
    line = base.mark_line(strokeWidth=2.4, point=False)
    where = long_df[long_df["investigation_date"].dt.strftime("%Y-%m-%d") == selected_day]
    points = alt.Chart(where[where["Series"] == "Observed"]).mark_circle(
        size=95, color="#c05a25", stroke="#fff", strokeWidth=1.4
    ).encode(x=x, y=y)
    st.markdown(f"**{heading}**")
    st.altair_chart((line + points).properties(height=255), width="stretch")


def _email_configuration(key: str) -> str:
    # Streamlit Cloud secrets are optional. An absent file must not break demo mode.
    if os.environ.get(key):
        return os.environ[key]
    try:
        return str(st.secrets.get(key) or "")
    except (FileNotFoundError, KeyError):
        return ""


@st.dialog("Email Maxim's investigation")
def sample_email_dialog(selected: dict, active_rows: list[dict]):
    """Recipient popup. Mail only transmits after Outlook OAuth + click."""
    finance = reporting_financial_evidence(selected)
    subject, body = compose_sample(selected, short_summary(selected, 650), finance)
    st.caption("Case-study report preview · sender requires Outlook authorization")
    recipient = st.text_input("Recipient email", placeholder="stakeholder@example.com", key="maxim_recipient")
    st.text_input("Subject", value=subject, disabled=True)
    st.text_area("Email preview", body, height=270, disabled=True)
    st.download_button("Download email draft", data=f"From: {EXPECTED_SENDER}\nTo: {recipient}\nSubject: {subject}\n\n{body}",
                       file_name=f"maxim-sample-{selected['investigation_date']}.txt", mime="text/plain")
    enabled = _email_configuration("MAXIM_EMAIL_ENABLED") == "1"
    client_id = _email_configuration("MICROSOFT_CLIENT_ID")
    if not enabled or not client_id:
        st.info(
            f"Sending from {EXPECTED_SENDER} is not connected yet. "
            "The popup and draft are ready; enable Microsoft Graph delegated Mail.Send "
            "and authenticate the sender before using live Send."
        )
        return
    if "maxim_oauth_token" not in st.session_state:
        if st.button("Connect Outlook sender", key="maxim_oauth_start"):
            try:
                app, flow = begin_outlook_sign_in(client_id)
                st.session_state["maxim_oauth_app"] = app
                st.session_state["maxim_oauth_flow"] = flow
            except Exception as exc:
                st.error(f"Could not start Outlook sign-in: {exc}")
        flow = st.session_state.get("maxim_oauth_flow")
        if flow:
            st.info(f"Open {flow.get('verification_uri', 'https://microsoft.com/devicelogin')} and enter the code: {flow['user_code']}")
            if st.button("I've completed Microsoft sign-in", key="maxim_oauth_finish"):
                try:
                    with st.spinner("Verifying authorized sender…"):
                        st.session_state["maxim_oauth_token"] = complete_outlook_sign_in(
                            st.session_state["maxim_oauth_app"], flow
                        )
                    st.success(f"Connected to {EXPECTED_SENDER}")
                except Exception as exc:
                    st.error(f"Sign-in was not completed: {exc}")
    if st.session_state.get("maxim_oauth_token"):
        st.success(f"Sending account verified: {EXPECTED_SENDER}")
        try:
            recipient = validate_recipient(recipient)
        except ValueError:
            st.caption("Enter one valid recipient email to enable sending.")
            return
        last_sent = st.session_state.get("maxim_sent_time", 0)
        cooldown = time.monotonic() - last_sent < 30
        if st.button("Send sample email", disabled=cooldown, type="primary", key="maxim_send_sample"):
            try:
                send_graph_email(st.session_state["maxim_oauth_token"], recipient, subject, body)
                st.session_state["maxim_sent_time"] = time.monotonic()
                st.success("Microsoft Graph accepted the email for sending. Check the recipient inbox and Sent Items.")
            except Exception as exc:
                st.error(f"Email was not accepted: {exc}")
        if cooldown:
            st.caption("Test-send cooldown: 30 seconds between messages.")


# The app renders only reporting records generated by the existing BigQuery →
# detector → Gemini → reporting-adapter workflow. No in-app data simulation.
rows = load_rows()
windows = reporting_windows(rows)
window_by_key = {item["key"]: item for item in windows}

# Top toolbar: branding, optional email draft and PDF export. No demo toggle.
navcol, emailcol, pdfcol = st.columns([8.1, 1.4, 1.3], gap="small", vertical_alignment="center")
with navcol:
    st.markdown(
        '<div class="sr-appbar"><div class="sr-icon">⌁</div><div>'
        '<div class="sr-brand">Signal Investigator</div>'
        '<div class="sr-brand-sub">Executive intelligence · Maxim</div>'
        '</div><span class="sr-demo">GA4 case study</span></div>',
        unsafe_allow_html=True,
    )
with emailcol:
    email_slot = st.empty()
with pdfcol:
    pdf_slot = st.empty()

with st.container(key="sr-report-head", border=False):
    heading_slot = st.empty()
    ctrl_a, ctrl_b, ctrl_c, ctrl_d = st.columns([1.15, 1.12, 1, 1], gap="small", vertical_alignment="bottom")
    with ctrl_a:
        window_keys = [w["key"] for w in windows]
        requested_window = st.query_params.get("window", "all")
        default_window = window_keys.index(requested_window) if requested_window in window_keys else 0
        window_key = st.selectbox(
            "Reporting window", window_keys, index=default_window,
            format_func=lambda x: window_by_key[x]["label"],
            key="reporting_window_select",
        )
        st.query_params["window"] = window_key
    active_rows = rows_for_window(rows, window_by_key[window_key])
    available = selectable_investigations(active_rows)
    available_by_date = {r["investigation_date"]: r for r in available}
    with ctrl_b:
        if available:
            dates = list(available_by_date)
            requested_date = st.query_params.get("date", "")
            default_date = dates.index(requested_date) if requested_date in dates else 0
            selected_date = st.selectbox(
                "Investigation date · yellow / red only", dates, index=default_date,
                format_func=lambda d: investigation_option(available_by_date[d]),
                key=f"investigation_date_select_{window_key}",
            )
            st.query_params["date"] = selected_date
        else:
            st.selectbox(
                "Investigation date · yellow / red only",
                ["No watch or alert in this window"], disabled=True,
                key=f"empty_investigations_{window_key}",
            )
            selected_date = None
    with ctrl_c:
        st.markdown(
            '<div class="sr-meta-static"><div class="sr-meta-label">COMPARED WITH</div>'
            '<div class="sr-meta-val">Four previous matching weekdays</div></div>',
            unsafe_allow_html=True,
        )
    with ctrl_d:
        st.markdown(
            '<div class="sr-meta-static"><div class="sr-meta-label">SOURCE</div>'
            '<div class="sr-meta-val">GA4-derived case-study data</div></div>',
            unsafe_allow_html=True,
        )
    note_slot = st.empty()

counts = severity_counts(active_rows)
if selected_date is None:
    with heading_slot:
        st.markdown(
            '<div class="sr-report-header"><div>'
            '<div class="sr-kicker">EXECUTIVE INVESTIGATION REPORT</div>'
            '<div class="sr-title">No outstanding investigations in this window</div>'
            '<div class="sr-subtitle">All evaluated dates in this window are normal</div>'
            '</div><span class="sr-status sr-status-green">No action needed</span></div>',
            unsafe_allow_html=True,
        )
    with note_slot:
        st.caption(
            "No yellow/red investigation dates occur in this selected window. "
            "Change the reporting window to review outstanding signals. "
            "Normal dates remain available in the full source evidence."
        )
    with email_slot:
        st.download_button("Email summary", data="", file_name="no-investigation.txt", disabled=True, width="stretch")
    with pdf_slot:
        st.download_button("Export PDF", data=b"", file_name="no-investigation.pdf", disabled=True, width="stretch")
    st.info("No investigations require attention in this reporting window.")
    st.stop()

selected = available_by_date[selected_date]
status = severity(selected)
spec, spec_source = get_layout(active_rows, selected)
priority_metrics = set(spec["kpis"])
status_title = {"red": "Action needed", "yellow": "Watchlist", "green": "No alert", "unknown": "Verify data"}[status]
selected_label = date.fromisoformat(selected_date).strftime("%d %b %Y")
headline_str = executive_headline(selected)

with heading_slot:
    st.markdown(
        f'<div class="sr-report-header"><div><div class="sr-kicker">EXECUTIVE INVESTIGATION REPORT</div>'
        f'<div class="sr-title">{escape(headline_str)}</div>'
        f'<div class="sr-subtitle">{escape(selected_label)} · Ecommerce conversion investigation</div></div>'
        f'<div style="text-align:right"><span class="sr-status sr-status-{status}">{escape(status_title)}</span>'
        f'<div class="sr-micro" style="margin-top:7px">{counts["red"]} alerts · '
        f'{counts["yellow"]} watch · {counts["green"]} normal</div></div></div>',
        unsafe_allow_html=True,
    )
with note_slot:
    st.caption(
        "GA4 public ecommerce sample–derived case-study data (2020), not live operations. "
        "For interviews, the daily BigQuery metrics may be modified; all presented "
        "detector and Gemini findings come from the selected reporting file. "
        "Revenue may be recorded or modeled; it is not proven lost revenue. Statistical significance is not established."
    )
with email_slot:
    if st.button("Email summary", width="stretch", key="maxim_email_popup"):
        sample_email_dialog(selected, active_rows)
finance = reporting_financial_evidence(selected)
with pdf_slot:
    st.download_button(
        "Export PDF", data=generate_pdf(selected, active_rows, finance),
        file_name=f"signal-investigator-{selected_date}.pdf", mime="application/pdf", width="stretch",
    )

# Same-height, shared-grid hero cards prevent uneven borders on desktop.
avatar_uri = (
    "data:image/svg+xml;base64," + __import__("base64").b64encode(AVATAR.read_bytes()).decode("ascii")
    if AVATAR.is_file() else AVATAR_URL
)
advice = decision(selected)
finance_status = (
    f"{'Modeled' if finance['revenue_evidence_type'] == 'modeled' else 'Recorded'}: "
    f"${finance['revenue_difference_usd']:+,.0f} vs weekday baseline"
    if finance else "Revenue evidence unavailable"
)
review_label = (
    "AI-generated · factual review pending"
    if selected.get("has_ai_investigation") and selected.get("factual_review_status") == "pending"
    else f"AI-generated · review: {selected.get('factual_review_status')}"
    if selected.get("has_ai_investigation")
    else "Rule-based brief · no AI investigation generated for this day"
)
st.markdown(
    '<div class="sr-hero-grid">'
    '<section class="sr-card">'
    '<div class="sr-kicker">MAXIM · EXECUTIVE ASSESSMENT</div>'
    f'<div class="sr-persona"><img src="{escape(avatar_uri, quote=True)}" '
    'width="49" height="49" alt="Maxim AI analyst avatar" '
    'style="border-radius:100%;background:#e8edf4;border:2px solid #e8edf4" />'
    '<div><div class="sr-persona-name">Maxim</div>'
    '<div class="sr-persona-job">AI Performance Investigation Analyst</div></div></div>'
    f'<div class="sr-summary-body">{escape(short_summary(selected, 650))}</div>'
    f'<div class="sr-review">{escape(review_label)} · Potential causes remain unverified</div>'
    '</section>'
    '<section class="sr-decision">'
    '<div class="sr-decision-title">RECOMMENDED NEXT INVESTIGATION</div>'
    f'<div class="sr-decision-action">{escape(display_action_title(advice["action"]))}</div>'
    f'<div class="sr-decision-line"><span>Suggested owner role*</span>'
    f'<strong>{escape(advice["owner"])}</strong></div>'
    f'<div class="sr-decision-line"><span>Revenue comparison</span><strong>{escape(finance_status)}</strong></div>'
    '<div class="sr-decision-line"><span>Finding status</span><strong>Requires validation</strong></div>'
    f'<div class="sr-reco-note">{escape(advice["why"])}</div>'
    '<div class="sr-reco-note">*Illustrative responsibility, not a real assignment.</div>'
    '</section></div>',
    unsafe_allow_html=True,
)

# Revenue now comes from the same reporting record as the Gemini assessment.
if finance:
    is_modeled = finance["revenue_evidence_type"] == "modeled"
    evidence_label = "Modeled" if is_modeled else "Recorded"
    revenue_label = f"${finance['purchase_revenue_usd']:,.2f} USD"
    comparison = f"${finance['revenue_difference_usd']:+,.2f} USD"
    comparison_context = (
        f"{finance['relative_revenue_change_pct']:+.1f}% versus four matching weekdays"
    )
    covered = finance.get("purchases_with_revenue")
    event_count = finance.get("purchase_events")
    coverage = (
        f"{covered} / {event_count}" if event_count is not None
        else f"{covered} covered purchase events" if covered is not None
        else "Unavailable"
    )
    coverage_detail = (
        f"{finance['distinct_transaction_ids']} distinct transaction IDs · sample data"
        if finance.get("distinct_transaction_ids") is not None
        else "Revenue coverage in the selected BigQuery dataset"
    )
    st.markdown(
        f'<div class="sr-block-title">Commercial impact · {evidence_label.lower()} revenue</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sr-finance">'
        f'<div class="sr-finance-cell"><div class="sr-kicker">{evidence_label.upper()} PURCHASE REVENUE</div>'
        f'<div class="sr-finance-number">{escape(revenue_label)}</div>'
        f'<div class="sr-finance-detail">{evidence_label} GA4-derived revenue (USD)</div></div>'
        '<div class="sr-finance-cell"><div class="sr-kicker">REVENUE VS HISTORICAL BASELINE</div>'
        f'<div class="sr-finance-number">{escape(comparison)}</div>'
        f'<div class="sr-finance-detail">{escape(comparison_context)}</div></div>'
        '<div class="sr-finance-cell"><div class="sr-kicker">PURCHASE EVENT COVERAGE</div>'
        f'<div class="sr-finance-number">{escape(coverage)}</div>'
        f'<div class="sr-finance-detail">{escape(coverage_detail)}</div></div>'
        '</div>', unsafe_allow_html=True,
    )
    if is_modeled:
        st.caption(
            "MODELED scenario: assumes historical revenue per purchasing session "
            "remains constant. Negative variance is against the four-Monday "
            "revenue benchmark—not verified lost revenue."
        )
    else:
        st.caption(
            "Recorded purchase-event revenue from the obfuscated historical GA4 "
            "sample. Historical variance is descriptive, not a causal loss estimate."
        )
else:
    st.markdown('<div class="sr-block-title">Commercial impact · evidence status</div>', unsafe_allow_html=True)
    st.info("Validated revenue comparison is not available for the selected investigation.")

# Six cards, ordered and styled to mirror the reference's executive KPI block.
st.markdown('<div class="sr-block-title">Key metrics</div>', unsafe_allow_html=True)
st.caption("Selected date vs four prior matching weekdays · Colors reflect alert/watch policy, not statistical significance")
st.markdown(
    '<div class="sr-kpi-grid">' + ''.join(
        kpi_html(metric, active_rows, selected, priority_metrics)
        for metric in kpi_definitions(selected)
    ) + '</div>',
    unsafe_allow_html=True,
)

# Primary evidence panel, led by the exact rule reason rather than invented cause.
primary_chart = spec["charts"][0]
status_caption = {
    "yellow": "WATCHLIST · FOLLOW UP ADVISED",
    "red": "DETECTOR ANOMALY · ACTION NEEDED",
    "green": "NO QUALIFYING ANOMALY",
    "unknown": "STATUS NEEDS VERIFICATION",
}[status]
st.markdown(
    f'<section class="sr-signal-wrap sr-signal-{status}"><div class="sr-signal-band">'
    '<div><div class="sr-signal-caption">'
    f'{escape(status_caption)} · {escape(selected_label.upper())}'
    '</div><div class="sr-signal-title">'
    f'{escape(headline_str)}</div></div>'
    f'<div><div class="sr-kicker" style="color:#ae571e;text-align:right">EST. PURCHASING-SESSION GAP</div>'
    f'<div style="font-size:1.4rem;font-weight:800;color:#a64e1b;text-align:right">'
    f'{selected["estimated_purchase_session_gap"]:.1f}</div></div>'
    '</div></section>',
    unsafe_allow_html=True,
)
st.caption("Estimated baseline gap is not orders, lost sales or revenue. A negative gap means performance above baseline.")
small_col, big_col = st.columns([1, 2.15], gap="large", vertical_alignment="top")
with small_col:
    st.markdown("**WHAT HAPPENED**")
    st.markdown(
        f"Sessions changed **{percent_signed(selected['session_change_pct'])}** versus "
        f"the four-weekday baseline. The purchase-session rate was "
        f"**{selected['observed_purchase_rate_pct']:.2f}%**, a relative change of "
        f"**{percent_signed(selected['purchase_rate_change_pct'])}**."
    )
    st.markdown("**DETECTOR DECISION**")
    st.write(alert_reason(selected))
    st.markdown("**EVIDENCE QUALITY**")
    st.markdown(
        "Selected GA4-derived aggregate metrics. Channel, device, funnel and financial attribution "
        "have not been verified for this record."
    )
with big_col:
    plot_evidence(primary_chart, active_rows, selected_date)
st.caption(
    "Graph uses the selected case-study daily metrics and each date's average "
    "of four previous matching weekdays. No confidence interval has been estimated."
)

# Page 2 of the reference: ranked hypothesis *cards*, without invented rankings.
st.markdown('<div class="sr-block-title">Why it happened: hypotheses to validate</div>', unsafe_allow_html=True)
st.caption("Maxim proposes plausible checks. These hypotheses are not ranked by probability and none is a verified cause.")
hyp = hypotheses(selected) if selected.get("has_ai_investigation") else []
if hyp:
    hyp_cards = []
    for i, item in enumerate(hyp[:3], 1):
        needed = item.get("data_needed", [])
        if not isinstance(needed, list):
            needed = []
        lead = suggested_owner_role(str(item.get("title", "")))
        hyp_cards.append(
            '<article class="sr-hyp-card">'
            f'<div class="sr-hyp-number">HYPOTHESIS {i} '
            '<span class="sr-unverified" style="float:right">Unverified</span></div>'
            f'<div class="sr-hyp-title">{escape(str(item.get("title", "Hypothesis")))}</div>'
            f'<div class="sr-hyp-detail">{escape(str(item.get("explanation", "")))}</div>'
            '<div class="sr-hyp-number" style="margin-top:12px">EVIDENCE NEEDED</div>'
            f'<div class="sr-hyp-detail">{escape(", ".join(map(str, needed)) or "Not specified")}</div>'
            '<div class="sr-hyp-footer"><div class="sr-hyp-number">SUGGESTED INVESTIGATION LEAD*</div>'
            f'<div class="sr-role">{escape(lead)}</div></div></article>'
        )
    st.markdown('<div class="sr-hyp-grid">' + ''.join(hyp_cards) + '</div>', unsafe_allow_html=True)
    st.caption('*Illustrative job roles; hypotheses are not ranked by confidence or proven causes.')
else:
    st.info("No AI hypotheses exist for this date; only detector evidence is available.")

# Decision-ready action register with illustrative roles and honest limitations.
st.markdown('<div class="sr-block-title" id="recommendations">Recommendations</div>', unsafe_allow_html=True)
st.caption("Proposed investigations, not approved business actions. Roles are illustrative and no owner has accepted an assignment.")
checks = recommended_checks(selected) if selected.get("has_ai_investigation") else []
if checks:
    table_rows = []
    for i, item in enumerate(checks, 1):
        action = str(item.get("action", "Follow-up"))
        role = suggested_owner_role(action)
        table_rows.append(
            '<tr>'
            f'<td><span class="sr-priority">{i:02d} · Investigate</span></td>'
            f'<td><strong>{escape(action)}</strong><div class="sr-quiet">{escape(str(item.get("purpose", "")))}</div></td>'
            f'<td><strong>{escape(role)}</strong><div class="sr-assignment">Suggested role only</div></td>'
            '<td>Not quantified</td><td>Proposed · review required</td></tr>'
        )
    st.markdown(
        '<div class="sr-table-wrap"><table class="sr-table">'
        '<colgroup><col style="width:13%"><col style="width:40%"><col style="width:20%">'
        '<col style="width:12%"><col style="width:15%"></colgroup>'
        '<thead><tr><th>PRIORITY</th><th>ACTION / PURPOSE</th><th>SUGGESTED OWNER*</th>'
        '<th>IMPACT</th><th>STATUS</th></tr></thead><tbody>'
        + ''.join(table_rows) + '</tbody></table></div>',
        unsafe_allow_html=True,
    )
else:
    st.info(f"Suggested monitoring step: {advice['action']}. No AI action register is available.")

# Supporting evidence as on the second page of the reference. We can show
# aggregate measures; absent channel/funnel breakdowns are never fabricated.
st.markdown('<div class="sr-block-title">Where the performance change appears</div>', unsafe_allow_html=True)
st.caption(f"Approved evidence views · {spec_source}.")
supporting_charts = [c for c in spec["charts"] if c != primary_chart]
if not supporting_charts:
    supporting_charts = ["purchase_rate_vs_baseline" if primary_chart != "purchase_rate_vs_baseline" else "sessions_vs_baseline"]
for start in range(0, len(supporting_charts), 2):
    subset = supporting_charts[start:start+2]
    for col, chart_name in zip(st.columns(len(subset), gap="large"), subset):
        with col:
            plot_evidence(chart_name, active_rows, selected_date)
st.markdown(
    '<div class="sr-card"><div class="sr-kicker">SEGMENTATION LIMITATION</div>'
    '<p class="sr-quiet">Channel attribution, device mix and checkout-funnel data are not included in '
    'this aggregated reporting dataset. A channel waterfall or funnel attribution chart will '
    '<strong>only be generated after the corresponding evidence has been collected and validated</strong>.</p></div>',
    unsafe_allow_html=True,
)

# Third-page secondary signals: comparable ranking without pseudo-impact metrics.
st.markdown('<div class="sr-block-title">Other signals in the reporting window</div>', unsafe_allow_html=True)
rate_ranked = sorted(active_rows, key=lambda r: float(r["purchase_rate_change_pct"]))
session_ranked = sorted(active_rows, key=lambda r: float(r["session_change_pct"]), reverse=True)
selected_rate_rank = next(i for i, r in enumerate(rate_ranked, 1) if r["investigation_date"] == selected_date)
selected_sessions_rank = next(i for i, r in enumerate(session_ranked, 1) if r["investigation_date"] == selected_date)
col_a, col_b = st.columns(2, gap="medium")
with col_a:
    st.markdown(
        '<div class="sr-card"><div class="sr-kicker">TRAFFIC MOVEMENT</div>'
        '<div class="sr-block-title" style="margin:.4rem 0">Session growth ranking</div>'
        f'<div style="font-size:1.7rem;font-weight:800">#{selected_sessions_rank} of {len(active_rows)}</div>'
        f'<div class="sr-quiet">{escape(percent_signed(selected["session_change_pct"]))} versus '
        'the selected day’s matching-weekday baseline.</div></div>',
        unsafe_allow_html=True,
    )
with col_b:
    st.markdown(
        '<div class="sr-card"><div class="sr-kicker">PURCHASE PERFORMANCE</div>'
        '<div class="sr-block-title" style="margin:.4rem 0">Rate decline ranking</div>'
        f'<div style="font-size:1.7rem;font-weight:800">#{selected_rate_rank} of {len(active_rows)}</div>'
        f'<div class="sr-quiet">{escape(percent_signed(selected["purchase_rate_change_pct"]))} '
        'relative rate change. Rank is descriptive, not statistical evidence.</div></div>',
        unsafe_allow_html=True,
    )
st.caption(
    f"Window classifications: {counts['red']} red alerts, {counts['yellow']} yellow watchlist dates, "
    f"{counts['green']} normal dates. Dates shown are the nine baseline-ready dates, not an exhaustive full period."
)

with st.expander("Appendix — methodology, source data and detector evidence", expanded=False):
    st.markdown(
        "**Data:** GA4 public sample–derived case-study data, potentially modified "
        "in a separate BigQuery demo table; all-channels-aggregated.  "
        "**Baseline:** four previous matching weekdays for each date.  "
        "**Alert:** defined by the Python detector; yellow is a separate follow-up policy.  "
        "**Interpretation:** GA4 purchasing-session rates, not orders; no causal analysis "
        "or financial impact has been established.  "
        f"**Dashboard chart selection:** {spec_source}."
    )
    st.markdown(f"**Stored detector decision:** `{selected['alert_status']}`")
    st.markdown(f"**Review status:** `{selected['factual_review_status']}`")
    st.dataframe(pd.DataFrame(active_rows)[[
        "investigation_date", "observed_sessions", "baseline_sessions", "session_change_pct",
        "observed_purchase_rate_pct", "baseline_purchase_rate_pct",
        "purchase_rate_change_pct", "alert_status", "factual_review_status",
    ]], width="stretch", hide_index=True)
    st.download_button(
        "Download investigation JSON", data=json.dumps(selected, indent=2),
        file_name=f"signal-investigation-{selected_date}.json", mime="application/json",
    )

st.markdown(
    '<div class="sr-footer">Signal Investigator · Historical public GA4 ecommerce sample · '
    'Maxim is an AI analyst persona, not a human analyst. This historical case study may contain modified demonstration data; it is not a live incident. '
    'Avatar: Avataaars by Pablo Stanley via DiceBear.</div>',
    unsafe_allow_html=True,
)
