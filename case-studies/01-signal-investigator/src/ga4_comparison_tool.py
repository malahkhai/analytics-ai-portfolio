
"""Compare GA4 performance across evaluated dates."""

import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "outputs" / "ga4_diagnostics.json"


def compare_ga4_performance(day: str) -> dict:
    """Rank one date's performance against other evaluated dates.

    Args:
        day: Date to compare, formatted YYYY-MM-DD.

    Returns:
        Rankings and performance comparisons from saved evidence.
    """

    if not isinstance(day, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", day
    ):
        return {"status": "invalid_date"}

    try:
        date.fromisoformat(day)
    except ValueError:
        return {"status": "invalid_date"}

    if not DIAGNOSTICS.exists():
        return {
            "status": "missing_evidence",
            "message": "Diagnostic report not found.",
        }

    with DIAGNOSTICS.open(encoding="utf-8") as file:
        report = json.load(file)

    evaluations = report["evaluations"]

    target = next(
        (row for row in evaluations if row["date"] == day),
        None,
    )

    if target is None:
        return {
            "status": "not_found",
            "date": day,
        }

    # Rank purchase-rate changes: lowest first.
    rate_ranked = sorted(
        (
            row for row in evaluations
            if row["purchase_rate_change_pct"] is not None
        ),
        key=lambda row: row["purchase_rate_change_pct"],
    )

    # Rank session growth: highest first.
    sessions_ranked = sorted(
        evaluations,
        key=lambda row: row["session_change_pct"],
        reverse=True,
    )

    rate_rank = next(
        (
            i for i, row in enumerate(rate_ranked, 1)
            if row["date"] == day
        ),
        None,
    )

    sessions_rank = next(
        i for i, row in enumerate(sessions_ranked, 1)
        if row["date"] == day
    )

    return {
        "status": "ok",
        "date": day,
        "dates_compared": len(evaluations),
        "session_change_pct": target["session_change_pct"],
        "purchase_rate_change_pct": (
            target["purchase_rate_change_pct"]
        ),
        "purchase_rate_decline_rank": rate_rank,
        "session_growth_rank": sessions_rank,
        "largest_purchase_rate_decline": (
            rate_ranked[0]["purchase_rate_change_pct"]
            if rate_ranked else None
        ),
        "largest_session_growth": (
            sessions_ranked[0]["session_change_pct"]
        ),
        "comparison_method": (
            "Rank changes against each date's four "
            "previous matching weekdays."
        ),
        "limitation": (
            "Ranks use existing aggregated diagnostic "
            "evidence, not additional source data. "
            "They do not establish a root cause."
        ),
    }
