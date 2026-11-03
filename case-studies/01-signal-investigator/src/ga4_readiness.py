
"""Check whether GA4 data has sufficient anomaly baselines."""

from collections import defaultdict
from datetime import timedelta

from src.bigquery_reader import fetch_daily_ecommerce
from src.ga4_adapter import adapt_ga4_records


def find_baseline_ready_days(rows):
    """Find dates with four prior matching weekdays."""

    dates_by_scope = defaultdict(set)

    for row in rows:
        dates_by_scope[row["scope"]].add(row["date"])

    ready_days = []

    for scope, available_dates in dates_by_scope.items():
        for day in sorted(available_dates):

            previous_dates = [
                day - timedelta(weeks=week)
                for week in (1, 2, 3, 4)
            ]

            if all(
                previous_day in available_dates
                for previous_day in previous_dates
            ):
                ready_days.append({
                    "date": day.isoformat(),
                    "scope": scope,
                })

    return ready_days


def main():
    # Retrieve and validate warehouse metrics.
    records = fetch_daily_ecommerce()
    rows = adapt_ga4_records(records)

    # Check historical coverage.
    ready_days = find_baseline_ready_days(rows)

    print(f"Validated GA4 records: {len(rows)}")
    print(f"Baseline-ready dates: {len(ready_days)}")

    if not ready_days:
        print("Status: insufficient_history")
        print(
            "Detection skipped: four previous matching "
            "weekdays are required."
        )
        return

    print("Status: baseline_ready")
    print(
        "Historical coverage is sufficient for these dates. "
        "GA4 anomaly detection is not yet implemented."
    )


if __name__ == "__main__":
    main()
