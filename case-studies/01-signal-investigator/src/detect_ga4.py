
"""Detect explainable anomalies in GA4 ecommerce metrics."""

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

from src.bigquery_reader import fetch_daily_ecommerce
from src.ga4_adapter import adapt_ga4_records
from src.ga4_readiness import find_baseline_ready_days


ROOT = Path(__file__).resolve().parents[1]

OUTPUT = ROOT / "outputs" / "ga4_investigations.json"


def detect_ga4_anomalies(
    rows,
    minimum_sessions=150,
    min_expected_purchase_gap=15,
    drop_threshold=0.35,
):
    """Compare dates against four previous matching weekdays."""

    by_scope = defaultdict(dict)

    for row in rows:
        by_scope[row["scope"]][row["date"]] = row

    eligible = find_baseline_ready_days(rows)
    alerts = []

    for item in eligible:
        day = date.fromisoformat(item["date"])
        scope = item["scope"]

        daily = by_scope[scope]
        current = daily[day]

        baseline_dates = [
            day - timedelta(weeks=week)
            for week in (1, 2, 3, 4)
        ]

        historical = [daily[d] for d in baseline_dates]

        prior_sessions = sum(r["sessions"] for r in historical)
        prior_purchases = sum(
            r["purchasing_sessions"] for r in historical
        )

        baseline_sessions = mean(
            r["sessions"] for r in historical
        )

        current_sessions = current["sessions"]
        current_purchases = current["purchasing_sessions"]

        baseline_rate = (
            prior_purchases / prior_sessions
            if prior_sessions > 0 else 0
        )

        current_rate = (
            current_purchases / current_sessions
            if current_sessions > 0 else 0
        )

        common = {
            "date": day.isoformat(),
            "scope": scope,
            "baseline_dates": [
                d.isoformat() for d in baseline_dates
            ],
            "data_source": "GA4 public ecommerce sample",
        }

        # Rule 1: Session purchase-rate decline
        if (
            baseline_rate > 0
            and current_sessions >= minimum_sessions
        ):
            change_pct = 100 * (
                current_rate / baseline_rate - 1
            )

            expected_purchases = (
                current_sessions * baseline_rate
            )

            purchase_gap = (
                expected_purchases - current_purchases
            )

            if (
                change_pct <= -100 * drop_threshold
                and purchase_gap >= min_expected_purchase_gap
            ):
                alerts.append({
                    **common,
                    "anomaly_type": "session_purchase_rate_drop",
                    "severity": (
                        "high" if change_pct < -50
                        else "medium"
                    ),
                    "observed_sessions": current_sessions,
                    "observed_purchasing_sessions": current_purchases,
                    "observed_rate_pct": round(
                        current_rate * 100, 2
                    ),
                    "baseline_rate_pct": round(
                        baseline_rate * 100, 2
                    ),
                    "change_vs_baseline_pct": round(
                        change_pct, 2
                    ),
                    "estimated_purchase_session_shortfall": round(
                        purchase_gap, 1
                    ),
                    "investigation_checks": [
                        "Check checkout and payment completion.",
                        "Validate GA4 purchase event tracking.",
                        "Investigate traffic and device mix changes.",
                    ],
                    "caution": (
                        "Descriptive anomaly only. "
                        "No root cause has been established."
                    ),
                })

        # Rule 2: Traffic decline
        if (
            baseline_sessions >= minimum_sessions
            and current_sessions
            <= baseline_sessions * (1 - drop_threshold)
        ):
            change_pct = 100 * (
                current_sessions / baseline_sessions - 1
            )

            alerts.append({
                **common,
                "anomaly_type": "sessions_drop",
                "severity": (
                    "high" if change_pct < -50
                    else "medium"
                ),
                "observed_sessions": current_sessions,
                "baseline_sessions": round(
                    baseline_sessions, 1
                ),
                "change_vs_baseline_pct": round(
                    change_pct, 2
                ),
                "investigation_checks": [
                    "Check marketing campaign activity.",
                    "Validate GA4 session measurement.",
                    "Investigate traffic source changes.",
                ],
                "caution": (
                    "Descriptive anomaly only. "
                    "Traffic changes may be real or measurement-related."
                ),
            })

    return sorted(
        alerts,
        key=lambda a: (
            a["date"],
            a["scope"],
            a["anomaly_type"],
        ),
    )


def main():
    records = fetch_daily_ecommerce()
    rows = adapt_ga4_records(records)

    eligible = find_baseline_ready_days(rows)
    alerts = detect_ga4_anomalies(rows)

    status = (
        "insufficient_history" if not eligible
        else "alerts_found" if alerts
        else "no_qualifying_anomalies"
    )

    result = {
        "project": "Signal Investigator",
        "source": "GA4 public ecommerce sample",
        "status": status,
        "records_analyzed": len(rows),
        "baseline_ready_dates": len(eligible),
        "alerts_found": len(alerts),
        "alerts": alerts,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(f"Records analyzed: {len(rows)}")
    print(f"Baseline-ready dates: {len(eligible)}")
    print(f"Alerts found: {len(alerts)}")
    print(f"Status: {status}")

    for alert in alerts:
        print(
            f"{alert['date']} | "
            f"{alert['anomaly_type']} | "
            f"{alert['change_vs_baseline_pct']:+.1f}%"
        )

    print(f"Evidence saved: {OUTPUT}")


if __name__ == "__main__":
    main()
