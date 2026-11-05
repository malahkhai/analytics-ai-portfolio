"""Pure presentation logic for Maxim's executive narrative report.

No LLM request, no cloud API query, no statistical claims. Historical sample.
"""
from __future__ import annotations

import json
import re
from datetime import date

from src.dashboard_presentation import severity
from src.interview_demo import is_synthetic, evaluate_conversion_rule


def short_summary(row: dict, max_chars: int = 660) -> str:
    """Shorten existing written assessment; never generate new claims."""
    if not row.get("has_ai_investigation") or not row.get("executive_summary"):
        from src.dashboard_presentation import daily_brief
        return daily_brief(row)
    text = re.sub(r"\s+", " ", str(row["executive_summary"])).strip()
    if len(text) <= max_chars:
        return text
    # Keep complete sentences only when available. If first sentence is long,
    # use up to max_chars then visibly mark the excerpt as truncated.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    collected: list[str] = []
    for sentence in sentences:
        candidate = " ".join([*collected, sentence]).strip()
        if len(candidate) > max_chars:
            break
        collected.append(sentence)
    if collected:
        return " ".join(collected) + " [Excerpt — full assessment in appendix]"
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "… [Excerpt]"



def executive_headline(row: dict) -> str:
    """Fact-only investigation headline calculated from detector metrics.

    This deliberately does not use a stale AI dashboard-spec headline: the
    source of truth is the currently selected reporting record.
    """
    from src.dashboard_presentation import severity

    purchase_change = float(row["purchase_rate_change_pct"])
    traffic_change = float(row["session_change_pct"])
    status = severity(row)
    if status in ("red", "yellow") and purchase_change < 0:
        prefix = f"Purchase rate fell {abs(purchase_change):.1f}%"
        if traffic_change > 0:
            return f"{prefix} as traffic rose {traffic_change:.1f}%"
        if traffic_change < 0:
            return f"{prefix} as traffic fell {abs(traffic_change):.1f}%"
        return f"{prefix} with traffic broadly unchanged"
    if status == "red":
        return "A qualifying ecommerce anomaly needs investigation"
    if status == "yellow":
        return "Ecommerce performance needs further review"
    if status == "green":
        return "No qualifying ecommerce anomaly detected"
    return "Ecommerce investigation requires data verification"


def display_action_title(action: str) -> str:
    """Make a common agent-generated analytical phrase executive-readable.

    Underlying recommended-check evidence and purpose are never rewritten.
    """
    clean = str(action or "").strip()
    if "dimension" in clean.lower() and "channel" in clean.lower() and "decomposition" in clean.lower():
        return "Break down performance by traffic channel and device"
    return clean or "Review the supporting evidence"


def parse_json_list(raw: object) -> list[dict]:
    if isinstance(raw, list):
        parsed = raw
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            return []
    else:
        return []
    return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []


def recommended_checks(row: dict) -> list[dict]:
    return parse_json_list(row.get("recommended_checks_json"))


def hypotheses(row: dict) -> list[dict]:
    return parse_json_list(row.get("hypotheses_json"))


ROLE_SIGNALS = (
    (("inventory", "stock", "merchandising", "product availability", "out of stock"), "Inventory & Sales Manager"),
    (("checkout", "payment", "browser", "mobile", "latency", "website", "site speed", "technical"), "Ecommerce Operations Manager"),
    (("tracking", "attribution", "measurement", "tagging", "ga4", "analytics"), "Digital Analytics Lead"),
    (("pricing", "price", "promotion", "discount", "promo code"), "Commercial Operations Manager"),
    (("channel", "acquisition", "traffic", "campaign", "source", "medium", "paid", "audience", "marketing", "dilution"), "Acquisition Manager"),
)


def suggested_owner_role(description: str) -> str:
    """Map an investigation topic to a *fictional job role*, never a person.

    This is a demonstration RACI suggestion, not an actual team assignment.
    """
    topic = str(description or "").lower()
    for needles, role in ROLE_SIGNALS:
        if any(needle in topic for needle in needles):
            return role
    return "Digital Analytics Lead"


def decision(row: dict) -> dict:
    """Proposal for validation; job role illustrative, no invented deadline/ROI."""
    kind = severity(row)
    checks = recommended_checks(row)
    if checks and kind in ("yellow", "red"):
        primary = checks[0]
        action = str(primary.get("action") or "Investigate this performance change")
        why = str(primary.get("purpose") or "Check evidence before taking action.")
    elif kind == "red":
        action, why = "Investigate the triggered anomaly", "Review affected segments and validate the suspected cause."
    elif kind == "yellow":
        action, why = "Review channel and device performance", "This is a watchlist date, not a qualifying anomaly."
    elif kind == "green":
        action, why = "Continue monitoring", "No qualifying alert or watchlist condition was met."
    else:
        action, why = "Verify detection data", "Detection status is not confirmed; don't treat the day as normal."
    return {
        "action": action,
        "why": why,
        "owner": suggested_owner_role(action),
        "owner_is_illustrative": True,
        "impact": "Not estimated",
        "deadline": "Not set",
    }


def report_window(rows: list[dict]) -> str:
    ordered = sorted(date.fromisoformat(r["investigation_date"]) for r in rows)
    if not ordered:
        return "Unavailable"
    start, end = ordered[0], ordered[-1]
    return f"{start:%d %b} – {end:%d %b %Y}"


def severity_counts(rows: list[dict]) -> dict[str, int]:
    result = {key: 0 for key in ("red", "yellow", "green", "unknown")}
    for row in rows:
        result[severity(row)] += 1
    return result


def alert_reason(row: dict) -> str:
    if severity(row) == "red":
        if is_synthetic(row):
            conditions = evaluate_conversion_rule(row)
            assert conditions["alert_triggered"]
            return (
                "SIMULATED alert only: session count met 150; relative purchase-rate "
                f"decline {abs(row['purchase_rate_change_pct']):.1f}% met 35%; "
                f"modeled purchasing-session gap {row['estimated_purchase_session_gap']:.1f} met 15. "
                "No anomaly was detected in the authentic historical Dec 7 data."
            )
        return "A stored detector alert has been triggered."
    if row.get("alert_status") != "no_qualifying_anomaly":
        return "Detector result is not confirmed; check data readiness."
    sessions = row.get("observed_sessions")
    rate = row.get("purchase_rate_change_pct")
    gap = row.get("estimated_purchase_session_gap")
    failed = []
    if isinstance(sessions, (int, float)) and sessions < 150:
        failed.append("session volume below 150")
    if isinstance(rate, (int, float)) and rate > -35:
        failed.append(f"relative purchase-rate decline {abs(min(rate, 0)):.1f}% < 35%")
    if isinstance(gap, (int, float)) and gap < 15:
        failed.append(f"estimated purchasing-session gap {gap:.1f} < 15")
    return "No alert: " + ("; ".join(failed) if failed else "the detector did not return a qualifying alert") + "."


def kpi_definitions(row: dict) -> list[dict]:
    # No money, orders, ROAS, confidence intervals or revenue-at-risk invented.
    values = [
        ("Sessions", f"{row['observed_sessions']:,}", f"{row['session_change_pct']:+.1f}% vs baseline", "observed_sessions"),
        ("Baseline sessions", f"{row['baseline_sessions']:,.0f}", "4 matching weekdays", "baseline_sessions"),
        ("Purchase-session rate", f"{row['observed_purchase_rate_pct']:.2f}%", f"{row['purchase_rate_change_pct']:+.1f}% relative", "observed_purchase_rate_pct"),
        ("Baseline purchase rate", f"{row['baseline_purchase_rate_pct']:.2f}%", "4 matching weekdays", "baseline_purchase_rate_pct"),
        ("Session growth", f"{row['session_change_pct']:+.1f}%", "relative to baseline", "session_change_pct"),
        ("Estimated session gap", f"{row['estimated_purchase_session_gap']:.1f}", "not confirmed lost sales", "estimated_purchase_session_gap"),
    ]
    return [{"title": a, "value": b, "delta": c, "key": d} for a,b,c,d in values]


def email_brief(row: dict, rows: list[dict]) -> str:
    report_type = "Rule alert" if severity(row) == "red" else "Watchlist" if severity(row) == "yellow" else "Daily review"
    judgment = ("Synthetic authored demo; not Gemini-generated" if is_synthetic(row) else "AI-generated; pending review" if row.get("has_ai_investigation") else "Deterministic only; no AI investigation")
    d = decision(row)
    return (
        f"Subject: Signal Investigator | {report_type} | {row['investigation_date']}\n\n"
        f"Maxim — AI Performance Investigation Analyst\n"
        f"Historical GA4 public ecommerce sample\n"
        + ("SYNTHETIC RED ALERT — interview demonstration, not historical observation\n\n" if is_synthetic(row) else "\n")
        + f"Summary:\n{short_summary(row)}\n\n"
        f"Sessions: {row['observed_sessions']:,} ({row['session_change_pct']:+.1f}% vs baseline)\n"
        f"Purchase-session rate: {row['observed_purchase_rate_pct']:.2f}% "
        f"({row['purchase_rate_change_pct']:+.1f}% relative change)\n"
        f"Alert: {alert_reason(row)}\n\n"
        f"Recommended next step: {d['action']}\nSuggested owner role (illustrative): {d['owner']}\n{d['why']}\n\n"
        f"Review: {judgment}. Cause and financial impact not established.\n"
    )
