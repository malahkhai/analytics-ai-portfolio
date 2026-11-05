"""Offline and reproducible synthetic red-alert scenario for portfolio interviews.

This module never queries or writes BigQuery and never calls Gemini. It derives
its synthetic metrics from a real, unchanged December 7 reference row. The
simulation is NOT a claim about historical ecommerce performance.
"""
from __future__ import annotations

from copy import deepcopy
import json
from math import isclose

from src.dashboard_presentation import severity

DEMO_DATE = "2020-12-07"
DEMO_PURCHASING_SESSIONS = 56
DETECTOR_MIN_SESSIONS = 150
DETECTOR_RATE_DROP_PCT = -35.0
DETECTOR_MIN_SESSION_GAP = 15.0
SIMULATION_LABEL = "SYNTHETIC RED ALERT · INTERVIEW DEMONSTRATION"


def is_synthetic(row: dict) -> bool:
    return row.get("demo_scenario") == "synthetic_red_alert"


def evaluate_conversion_rule(row: dict) -> dict[str, bool]:
    """Evaluate the conversion alert's documented deterministic thresholds."""
    checks = {
        "sessions_met": row["observed_sessions"] >= DETECTOR_MIN_SESSIONS,
        "rate_drop_met": row["purchase_rate_change_pct"] <= DETECTOR_RATE_DROP_PCT,
        "shortfall_met": row["estimated_purchase_session_gap"] >= DETECTOR_MIN_SESSION_GAP,
    }
    return {**checks, "alert_triggered": all(checks.values())}


def make_synthetic_red_alert(historical: dict) -> dict:
    """Create internally consistent synthetic evidence without editing the input.

    Keeps real date, sessions and historical baseline only. Changes the count of
    purchasing sessions to 56. Calculation uses the unrounded synthetic rate;
    published rates are rounded solely for display.
    """
    if historical.get("investigation_date") != DEMO_DATE:
        raise ValueError("The interview demo only supports the Dec 7 fixture")
    if severity(historical) != "yellow":
        raise ValueError("The reference must be the authentic Dec 7 watchlist")
    sessions = historical["observed_sessions"]
    baseline_pct = historical["baseline_purchase_rate_pct"]
    if not isinstance(sessions, int) or sessions <= DEMO_PURCHASING_SESSIONS:
        raise ValueError("Invalid or insufficient reference session count")
    if not isinstance(baseline_pct, (int, float)) or baseline_pct <= 0:
        raise ValueError("Valid positive baseline purchase rate required")

    rate_pct = DEMO_PURCHASING_SESSIONS * 100 / sessions
    relative_pct = (rate_pct / baseline_pct - 1) * 100
    gap = sessions * baseline_pct / 100 - DEMO_PURCHASING_SESSIONS

    record = deepcopy(historical)
    record.update({
        "demo_scenario": "synthetic_red_alert",
        "scenario_label": SIMULATION_LABEL,
        "demo_purchasing_sessions": DEMO_PURCHASING_SESSIONS,
        "observed_purchase_rate_pct": round(rate_pct, 4),
        "purchase_rate_change_pct": round(relative_pct, 1),
        "estimated_purchase_session_gap": round(gap, 1),
        "alert_status": "qualifying_anomaly",
        "alert_types": ["conversion_rate_drop"],
        "has_ai_investigation": True,
        # This is a authored fixture, NOT a Gemini response.
        "analysis_origin": "deterministic_simulation_fixture_not_gemini",
        "factual_review_status": "synthetic_example",
    })
    if not evaluate_conversion_rule(record)["alert_triggered"]:
        raise AssertionError("Synthetic anomaly does not meet all alert thresholds")

    record["executive_summary"] = (
        "SIMULATION ONLY — not a historical GA4 anomaly. Keeping Dec 7 traffic "
        f"at {sessions:,} sessions, this interview replay assumes "
        f"{DEMO_PURCHASING_SESSIONS} purchasing sessions. The resulting rate is "
        f"{rate_pct:.2f}% versus a {baseline_pct:.2f}% baseline "
        f"({relative_pct:.1f}% relative), with a modeled gap of {gap:.1f}. "
        "All three conversion-alert thresholds qualify. Root cause and revenue impact "
        "are unverified; investigate acquisition mix, checkout and inventory."
    )
    record["why_no_alert"] = None
    record["hypotheses_json"] = json.dumps([
        {
            "title": "Acquisition-channel or traffic-quality shift",
            "explanation": "A change in incoming session mix could produce a lower purchase-session rate; this has not been tested.",
            "data_needed": ["Session-level source and medium", "Channel-level purchase sessions", "Campaign composition"],
            "validation_check": "Compare the synthetic-day segmentation pattern with the four matching weekdays, if trustworthy segment evidence is available.",
        },
        {
            "title": "Browser or checkout technical friction",
            "explanation": "Checkout friction is a plausible hypothesis but no platform errors or funnel evidence are included in this simulation.",
            "data_needed": ["Browser and device data", "Checkout progression", "Technical error logs"],
            "validation_check": "Verify whether measured funnel-stage or error rates diverge by platform before assigning a cause.",
        },
        {
            "title": "Inventory or product availability constraint",
            "explanation": "Stock or merchandising changes might influence purchasing, but no inventory data has been examined.",
            "data_needed": ["Product-level availability", "Out-of-stock events", "Cart and checkout stage counts"],
            "validation_check": "Check product availability against sessions and purchasing behavior before attributing the decline to stock.",
        },
    ])
    record["recommended_checks_json"] = json.dumps([
        {
            "action": "Investigate acquisition channels and traffic quality",
            "purpose": "Determine whether the simulated conversion-rate decline would be concentrated in newly acquired, lower-intent cohorts.",
            "inputs_needed": ["Source/medium", "Campaign and sessions", "Purchasing sessions by channel"],
        },
        {
            "action": "Inspect browser-specific checkout health",
            "purpose": "Rule out platform or checkout issues before treating traffic mix as the cause.",
            "inputs_needed": ["Checkout steps by device", "Browser errors", "Payment completion events"],
        },
        {
            "action": "Validate inventory and product availability",
            "purpose": "Check whether product stock or merchandising changes could explain the modeled purchasing decline.",
            "inputs_needed": ["SKU availability", "Stockout timing", "Product-to-purchase progression"],
        },
    ])
    return record


def scenario_rows(historical_rows: list[dict], simulate: bool) -> list[dict]:
    """Return a new report dataset with only the December 7 record replaced."""
    copied = deepcopy(historical_rows)
    if not simulate:
        return copied
    matches = [i for i, row in enumerate(copied) if row.get("investigation_date") == DEMO_DATE]
    if len(matches) != 1:
        raise ValueError("Expected exactly one historical Dec 7 row")
    copied[matches[0]] = make_synthetic_red_alert(copied[matches[0]])
    return copied


def validate_simulated_row(row: dict) -> None:
    if not is_synthetic(row):
        raise ValueError("Not a synthetic scenario")
    sessions = row["observed_sessions"]
    n_purchases = row["demo_purchasing_sessions"]
    baseline = row["baseline_purchase_rate_pct"]
    expected_rate = n_purchases * 100 / sessions
    expected_change = (expected_rate / baseline - 1) * 100
    expected_gap = sessions * baseline / 100 - n_purchases
    assert isclose(row["observed_purchase_rate_pct"], expected_rate, abs_tol=.0001)
    assert isclose(row["purchase_rate_change_pct"], expected_change, abs_tol=.051)
    assert isclose(row["estimated_purchase_session_gap"], expected_gap, abs_tol=.051)
    assert severity(row) == "red"
    assert evaluate_conversion_rule(row)["alert_triggered"]
