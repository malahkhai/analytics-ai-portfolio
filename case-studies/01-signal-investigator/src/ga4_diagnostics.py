
"""Generate explainable GA4 performance diagnostics."""

import json
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

from src.bigquery_reader import fetch_daily_ecommerce
from src.ga4_adapter import adapt_ga4_records
from src.ga4_readiness import find_baseline_ready_days
from src.detect_ga4 import detect_ga4_anomalies


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "ga4_diagnostics.json"


def build_diagnostic_report(rows):
    """Compare GA4 metrics against matching-weekday baselines."""

    ready_days = find_baseline_ready_days(rows)
    alerts = detect_ga4_anomalies(rows)

    lookup = {
        (row["scope"], row["date"]): row
        for row in rows
    }

    evaluations = []

    for item in ready_days:
        day = date.fromisoformat(item["date"])
        scope = item["scope"]
        current = lookup[(scope, day)]

        baseline_dates = [
            day - timedelta(weeks=week)
            for week in (1, 2, 3, 4)
        ]

        history = [
            lookup[(scope, baseline_day)]
            for baseline_day in baseline_dates
        ]

        baseline_sessions = mean(
            row["sessions"] for row in history
        )

        baseline_rate = (
            sum(row["purchasing_sessions"] for row in history)
            / sum(row["sessions"] for row in history)
        )

        current_rate = (
            current["purchasing_sessions"] / current["sessions"]
        )

        session_change = 100 * (
            current["sessions"] / baseline_sessions - 1
        )

        rate_change = (
            100 * (current_rate / baseline_rate - 1)
            if baseline_rate > 0 else None
        )

        purchase_gap = (
            current["sessions"] * baseline_rate
            - current["purchasing_sessions"]
        )

        matching_alerts = [
            alert["anomaly_type"]
            for alert in alerts
            if alert["date"] == day.isoformat()
            and alert["scope"] == scope
        ]

        evaluations.append({
            "date": day.isoformat(),
            "scope": scope,
            "baseline_dates": [
                d.isoformat() for d in baseline_dates
            ],
            "observed_sessions": current["sessions"],
            "baseline_sessions": round(baseline_sessions, 1),
            "session_change_pct": round(session_change, 1),
            "observed_purchase_rate_pct": round(
                current_rate * 100, 2
            ),
            "baseline_purchase_rate_pct": round(
                baseline_rate * 100, 2
            ),
            "purchase_rate_change_pct": (
                round(rate_change, 1)
                if rate_change is not None else None
            ),
            "estimated_purchase_session_gap": round(
                purchase_gap, 1
            ),
            "alert_types": matching_alerts,
            "status": (
                "alert" if matching_alerts
                else "no_qualifying_anomaly"
            ),
        })

    return {
        "project": "Signal Investigator",
        "source": "GA4 public ecommerce sample",
        "records_analyzed": len(rows),
        "dates_evaluated": len(evaluations),
        "qualifying_alerts": len(alerts),
        "evaluations": evaluations,
    }


def main():
    records = fetch_daily_ecommerce()
    rows = adapt_ga4_records(records)

    report = build_diagnostic_report(rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("GA4 diagnostic report created")
    print("Records:", report["records_analyzed"])
    print("Dates evaluated:", report["dates_evaluated"])
    print("Alerts:", report["qualifying_alerts"])

    print("\nLargest purchase-rate declines:")
    ranked = sorted(
        (
            e for e in report["evaluations"]
            if e["purchase_rate_change_pct"] is not None
        ),
        key=lambda e: e["purchase_rate_change_pct"],
    )

    for item in ranked[:3]:
        print(
            f"{item['date']}: "
            f"{item['purchase_rate_change_pct']:+.1f}%"
        )

    print(f"\nEvidence saved: {OUTPUT}")


if __name__ == "__main__":
    main()
