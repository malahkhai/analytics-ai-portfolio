"""Deterministic, explainable v0 anomaly detection (no LLM or paid services needed)."""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "daily_ecommerce_metrics.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "investigations.json"


def load_metrics(path):
    rows = []
    seen = set()
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        expected = {"date", "channel", "sessions", "orders", "revenue_eur"}
        if not expected.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing required columns: {sorted(expected - set(reader.fieldnames or []))}")
        for item in reader:
            day = date.fromisoformat(item["date"])
            channel = item["channel"].strip()
            sessions = int(item["sessions"])
            orders = int(item["orders"])
            revenue = float(item["revenue_eur"])
            if not channel or sessions < 0 or orders < 0 or orders > sessions or revenue < 0:
                raise ValueError(f"Invalid metric row: {item}")
            key = (day, channel)
            if key in seen:
                raise ValueError(f"Duplicate day/channel record: {key}")
            seen.add(key)
            rows.append({"date": day, "channel": channel, "sessions": sessions,
                         "orders": orders, "revenue_eur": revenue})
    return rows


def investigate(rows, minimum_sessions=150, min_expected_orders_gap=15, drop_threshold=0.35):
    """Compare each day with the prior 4 matching weekdays, per channel.

    Baseline data must exist on each of the four dates. Alerts are descriptive;
    hypotheses are not proven causes. No LLM participates at this stage.
    """
    by_channel = defaultdict(dict)
    for row in rows:
        by_channel[row["channel"]][row["date"]] = row
    alerts = []
    for channel, daily in by_channel.items():
        for day in sorted(daily):
            current = daily[day]
            lookback_days = [day - timedelta(days=7 * weeks) for weeks in (1, 2, 3, 4)]
            if not all(d in daily for d in lookback_days):
                continue
            refs = [daily[d] for d in lookback_days]
            if current["sessions"] < minimum_sessions:
                # Not enough current volume for a conversion-rate comparison.
                # Traffic-drop checks below use the historical sessions instead.
                pass
            prior_sessions = sum(r["sessions"] for r in refs)
            prior_orders = sum(r["orders"] for r in refs)
            baseline_sessions = mean(r["sessions"] for r in refs)
            if prior_sessions <= 0:
                continue
            baseline_cr = prior_orders / prior_sessions
            current_cr = current["orders"] / current["sessions"] if current["sessions"] else 0.0
            baseln_aov = sum(r["revenue_eur"] for r in refs) / prior_orders if prior_orders else 0.0
            if baseline_cr > 0 and current["sessions"] >= minimum_sessions:
                drop_pct = 100 * (current_cr / baseline_cr - 1)
                expected_orders = current["sessions"] * baseline_cr
                shortfall = expected_orders - current["orders"]
                if drop_pct <= -100 * drop_threshold and shortfall >= min_expected_orders_gap:
                    alerts.append({
                        "date": day.isoformat(), "channel": channel,
                        "anomaly_type": "conversion_rate_drop",
                        "severity": "high" if drop_pct < -50 else "medium",
                        "observed_sessions": current["sessions"],
                        "observed_orders": current["orders"],
                        "observed_conversion_rate_pct": round(current_cr * 100, 2),
                        "baseline_conversion_rate_pct": round(baseline_cr * 100, 2),
                        "change_vs_baseline_pct": round(drop_pct, 2),
                        "expected_orders": round(expected_orders, 1),
                        "estimated_order_shortfall": round(shortfall, 1),
                        "estimated_revenue_gap_eur": round(shortfall * baseln_aov, 2),
                        "baseline_dates": [d.isoformat() for d in lookback_days],
                        "investigation_checks": [
                            "Validate purchase event and transaction-ID completeness against backend orders.",
                            "Inspect checkout errors, conversion funnel and site changes during incident.",
                            "Compare landing-page and device-level conversion rates by campaign."],
                        "caution": "Statistical alert only. No root cause established; revenue gap is a scenario estimate."
                    })
            if baseline_sessions >= minimum_sessions and current["sessions"] <= baseline_sessions * (1 - drop_threshold):
                decline = 100 * (current["sessions"] / baseline_sessions - 1)
                alerts.append({
                    "date": day.isoformat(), "channel": channel,
                    "anomaly_type": "sessions_drop", "severity": "high" if decline < -50 else "medium",
                    "observed_sessions": current["sessions"],
                    "baseline_sessions": round(baseline_sessions, 1),
                    "change_vs_baseline_pct": round(decline, 2),
                    "baseline_dates": [d.isoformat() for d in lookback_days],
                    "investigation_checks": [
                        "Check campaign schedules, email delivery or paid media spend changes.",
                        "Validate session_start tracking and consent configuration.",
                        "Compare channel attribution and referrer classification over time."],
                    "caution": "Statistical alert only. Traffic reduction might be real or measurement-related."
                })
    return sorted(alerts, key=lambda alert: (alert["date"], alert["channel"], alert["anomaly_type"]))


def run(input_path=DEFAULT_INPUT, output_path=DEFAULT_OUTPUT):
    rows = load_metrics(input_path)
    alerts = investigate(rows)
    result = {"project": "Analytics Investigation Agent", "release": "v0.1-baseline",
              "dataset": "synthetic_demo", "rows_analyzed": len(rows), "alerts": alerts}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect explainable ecommerce anomalies")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.input, args.output)
    print(f"Checked {result['rows_analyzed']} rows; identified {len(result['alerts'])} alerts.")
    for alert in result["alerts"]:
        print(f"  {alert['date']} | {alert['channel']} | {alert['anomaly_type']} | "
              f"{alert['change_vs_baseline_pct']:+.1f}% vs prior matching weekdays")
    print(f"Saved structured evidence: {args.output}")
