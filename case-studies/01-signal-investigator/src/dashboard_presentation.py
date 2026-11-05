"""Pure, offline and deterministic dashboard presentation safeguards.

Never ask the LLM to decide status. Red comes from the detector only; amber
is a separate, explicitly documented follow-up rule—not an anomaly alert.
"""

from __future__ import annotations

from datetime import date
from html import escape
from urllib.parse import urlencode

ALERT_STATUSES = {"qualifying_anomaly", "anomaly_detected", "alert_triggered"}
WATCH_RATE_DROP_PCT = -10.0
WATCH_MIN_GAP = 15.0
MIN_ELIGIBLE_SESSIONS = 150

APPROVED_KPIS = {
    "observed_sessions", "session_change_pct", "observed_purchase_rate_pct",
    "purchase_rate_change_pct", "estimated_purchase_session_gap",
}
CHART_FIELDS = {
    "sessions_vs_baseline": ["observed_sessions", "baseline_sessions"],
    "purchase_rate_vs_baseline": [
        "observed_purchase_rate_pct", "baseline_purchase_rate_pct"
    ],
    "session_change_trend": ["session_change_pct"],
    "purchase_rate_change_trend": ["purchase_rate_change_pct"],
}
SECTION_FIELDS = {
    "executive_summary": "executive_summary",
    "alert_explanation": "why_no_alert",
    "hypotheses": "hypotheses_json",
    "recommended_checks": "recommended_checks_json",
}


def is_alert(row: dict) -> bool:
    """Trust only stored detection evidence, not narrative sentiment."""
    return bool(row.get("alert_types")) or row.get("alert_status") in ALERT_STATUSES


def is_watch(row: dict) -> bool:
    """Flag a *non-alert* follow-up for a material negative rate shift.

    Demo policy: >=150 sessions, >=10% relative purchase-rate decline,
    and >=15 estimated purchasing-session gap. Does not modify anomaly rules.
    """
    if is_alert(row) or row.get("alert_status") != "no_qualifying_anomaly":
        return False
    return (
        isinstance(row.get("observed_sessions"), (int, float))
        and row["observed_sessions"] >= MIN_ELIGIBLE_SESSIONS
        and isinstance(row.get("purchase_rate_change_pct"), (int, float))
        and row["purchase_rate_change_pct"] <= WATCH_RATE_DROP_PCT
        and isinstance(row.get("estimated_purchase_session_gap"), (int, float))
        and row["estimated_purchase_session_gap"] >= WATCH_MIN_GAP
    )


def severity(row: dict) -> str:
    if is_alert(row):
        return "red"
    if row.get("alert_status") != "no_qualifying_anomaly":
        return "unknown"  # Never paint missing/invalid evidence green.
    return "yellow" if is_watch(row) else "green"


def status_label(row: dict) -> str:
    return {
        "red": "Qualifying anomaly detected",
        "yellow": "Watchlist — attention recommended (not an alert)",
        "green": "No qualifying alert or watchlist condition",
        "unknown": "Data readiness or detection status needs review",
    }[severity(row)]


def timeline_icon(row: dict) -> str:
    return {"red": "🔴", "yellow": "🟡", "green": "🟢", "unknown": "⚪"}[severity(row)]


def format_date(day: str) -> str:
    return date.fromisoformat(day).strftime("%d %b")


def timeline_nav_html(rows: list[dict], selected_date: str) -> str:
    """Accessible, scrollable day tiles with direct-link query parameters."""
    items = []
    for row in rows:
        day = row["investigation_date"]
        stamp = date.fromisoformat(day)  # valid date by construction
        kind = severity(row)
        active = day == selected_date
        href = "?" + urlencode({"date": day})
        month = stamp.strftime("%b").upper()
        weekday = stamp.strftime("%a")
        state = "true" if active else "false"
        items.append(
            f'<a class="si-day si-day--{kind} {"si-day--active" if active else ""}" '
            f'href="{escape(href, quote=True)}" aria-current="{ "date" if active else "false" }" '
            f'title="{escape(day + ": " + status_label(row), quote=True)}">'
            f'<span class="si-day-month">{month}</span>'
            f'<span class="si-day-number">{stamp.day:02d}</span>'
            f'<span class="si-day-weekday">{weekday}</span>'
            f'<span class="si-day-dot" aria-label="{escape(kind, quote=True)}"></span>'
            f'</a>'
        )
    return (
        '<nav class="si-timeline" aria-label="Select investigation date">'
        '<div class="si-timeline-track">' + "".join(items) + "</div></nav>"
    )


def daily_brief(row: dict) -> str:
    """No AI-generated wording for dates without an AI investigation."""
    opening = (
        f"On **{row['investigation_date']}**, ecommerce recorded "
        f"**{row['observed_sessions']:,} sessions** "
        f"(**{row['session_change_pct']:+.1f}%** vs the prior matching-weekday "
        f"baseline). The purchase-session rate was "
        f"**{row['observed_purchase_rate_pct']:.2f}%** "
        f"(**{row['purchase_rate_change_pct']:+.1f}%** relative change). "
    )
    kind = severity(row)
    if kind == "red":
        return opening + (
            "The rule-based detector **triggered an anomaly alert**. "
            "No AI investigation has been generated for this date yet."
        )
    if kind == "yellow":
        return opening + (
            "**Watchlist, not a triggered anomaly:** the rate decline was at least "
            "10%, with an estimated purchasing-session gap of at least 15. "
            "The formal alert threshold wasn't satisfied. Review traffic "
            "quality and conversion behavior before inferring a cause."
        )
    if kind == "unknown":
        return opening + (
            "The record does not have a confirmed qualifying/no-qualifying "
            "status. Data readiness should be checked before interpreting it."
        )
    reasons = []
    if row["observed_sessions"] < MIN_ELIGIBLE_SESSIONS:
        reasons.append("session volume was below 150")
    if row["purchase_rate_change_pct"] > -35:
        reasons.append("purchase-rate decline was below the formal 35% threshold")
    if row["estimated_purchase_session_gap"] < 15:
        reasons.append("estimated purchasing-session gap was below 15")
    return opening + (
        "**No qualifying anomaly or watchlist condition.** "
        + ("For the conversion alert, " + "; ".join(reasons) + ". " if reasons else "")
        + "This does not prove that every aspect of performance is healthy."
    )


def fallback_spec(row: dict) -> dict:
    """Approved chart/metric set when no stored Gemini plan is available."""
    sections = [
        section for section, field in SECTION_FIELDS.items()
        if row.get("has_ai_investigation") and row.get(field)
    ]
    return {
        "headline": "Performance investigation and historical comparison",
        "kpis": [
            "observed_sessions", "session_change_pct",
            "observed_purchase_rate_pct", "purchase_rate_change_pct",
        ],
        "charts": ["sessions_vs_baseline", "purchase_rate_vs_baseline"],
        "sections": sections,
    }


def validate_dashboard_spec(raw: dict, rows: list[dict], selected: dict) -> dict:
    """No executable code, novel chart types, or unsupported metrics allowed."""
    if not isinstance(raw, dict):
        raise ValueError("Dashboard specification must be an object")
    if set(raw) != {"headline", "kpis", "charts", "sections"}:
        raise ValueError("Unknown or missing dashboard fields")
    headline = raw["headline"]
    if not isinstance(headline, str) or not 8 <= len(headline.strip()) <= 120:
        raise ValueError("Invalid headline")
    for name, allowed, maximum, minimum in (
        ("kpis", APPROVED_KPIS, 4, 2),
        ("charts", CHART_FIELDS, 3, 1),
        ("sections", SECTION_FIELDS, 4, 0),
    ):
        values = raw[name]
        if not isinstance(values, list) or not minimum <= len(values) <= maximum:
            raise ValueError(f"Invalid {name} count")
        if any(not isinstance(v, str) or v not in allowed for v in values):
            raise ValueError(f"Unsupported dashboard {name}")
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate dashboard {name}")
    for metric in raw["kpis"]:
        if selected.get(metric) is None:
            raise ValueError(f"Unavailable KPI: {metric}")
    for chart in raw["charts"]:
        for row in rows:
            if any(row.get(col) is None for col in CHART_FIELDS[chart]):
                raise ValueError(f"Unavailable chart: {chart}")
    for section in raw["sections"]:
        if not selected.get("has_ai_investigation") or not selected.get(
            SECTION_FIELDS[section]
        ):
            raise ValueError(f"Unavailable AI section: {section}")
    return raw
