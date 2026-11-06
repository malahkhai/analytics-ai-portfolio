"""Revenue evidence add-on for Signal Investigator.

Amounts are observed historical GA4 purchase-event revenue in USD; variance is
against a *descriptive* matching-weekday mean, not a causal or financial forecast.
No Cloud query runs on dashboard render or module import.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

PROJECT = "signal-investigator-analytics"
ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
FIXTURES = ROOT / "tests" / "fixtures"


def validate_financial_record(record: dict, selected_day: str) -> dict:
    if record.get("date") != selected_day:
        raise ValueError("Financial evidence does not match selected date")
    if record.get("source") != "GA4 public ecommerce sample · purchase events":
        raise ValueError("Unknown revenue evidence source")
    for key in ("purchase_events", "purchases_with_revenue", "positive_revenue_events", "distinct_transaction_ids"):
        n = record.get(key)
        if type(n) is not int or n < 0:
            raise ValueError(f"Invalid {key}")
    if record["purchases_with_revenue"] > record["purchase_events"] or record["positive_revenue_events"] > record["purchases_with_revenue"]:
        raise ValueError("Invalid revenue coverage counts")
    if record["distinct_transaction_ids"] > record["purchase_events"]:
        raise ValueError("Invalid transaction identifier count")
    amount = record.get("purchase_revenue_usd")
    if type(amount) not in (float, int) or amount < 0:
        raise ValueError("Invalid purchase revenue")
    baseline = record.get("baseline_revenue_usd")
    if baseline is not None and (type(baseline) not in (float, int) or baseline < 0):
        raise ValueError("Invalid baseline revenue")
    days = record.get("baseline_dates", [])
    if baseline is not None and len(days) != 4:
        raise ValueError("A revenue baseline requires four matching-weekday dates")
    return record


def load_financial_evidence(selected_day: str, outputs: Path = OUTPUTS, fixtures: Path = FIXTURES) -> dict | None:
    """Use checked local evidence, or demo fixture when not generated yet."""
    date.fromisoformat(selected_day)
    filename = f"ga4_financial_evidence_{selected_day}.json"
    for location in (outputs / filename, fixtures / filename):
        if location.is_file():
            return validate_financial_record(json.loads(location.read_text(encoding="utf-8")), selected_day)
    return None



# The financial snapshot comes from the original, *unmodified* historical
# GA4 events. These are the verified same-day daily metrics in that original
# case study. They are NOT a generic way to prove BigQuery source provenance.
# A dashboard row that differs must not inherit the original revenue amount.
ORIGINAL_REVENUE_CASE = {
    "2020-12-07": {
        "observed_sessions": 5461,
        "observed_purchase_rate_pct": 1.67,
        "baseline_purchase_rate_pct": 1.95,
        "purchase_events": 110,
    },
}


def matching_financial_evidence(row: dict, financial: dict | None = None) -> dict | None:
    """Gate historical purchase revenue against its known original reporting row.

    For the static case study, do not reuse raw-source revenue with a modified
    purchasing-session or purchase-events scenario. Returning None means
    'unavailable for this selected report', never zero or lost revenue.
    """
    day = row.get("investigation_date")
    original = ORIGINAL_REVENUE_CASE.get(day)
    if original is None:
        return None  # A different day's revenue was not validated.
    required = ("observed_sessions", "observed_purchase_rate_pct")
    optional = ("baseline_purchase_rate_pct",)
    for metric in (*required, *(name for name in optional if name in row)):
        try:
            value = float(row[metric])
        except (KeyError, TypeError, ValueError):
            return None
        tolerance = 0.011 if metric.endswith("pct") else 0.1
        if abs(value - original[metric]) > tolerance:
            return None
    if financial is None:
        financial = load_financial_evidence(day)
    if not financial or financial.get("date", day) != day:
        return None
    if financial.get("purchase_events", original["purchase_events"]) != original["purchase_events"]:
        return None
    return financial


def financial_context_for_diagnostic(
    evaluation: dict,
    current: dict,
    model_name: str,
) -> dict | None:
    """Provide validated financial context for the December 7 case."""

    day = evaluation["date"]

    if day != "2020-12-07":
        return None

    financial = load_financial_evidence(day)

    if financial is None:
        raise ValueError("Financial evidence is missing")

    baseline = financial["baseline_revenue_usd"]

    if baseline is None or baseline <= 0:
        raise ValueError("Valid revenue baseline required")

    # Original historical GA4 case.
    if model_name == "fct_daily_ecommerce":
        if (
            current["sessions"] != 5461
            or current["purchasing_sessions"] != 91
            or current["purchase_events"] != 110
        ):
            raise ValueError("Original financial evidence does not match data")

        if matching_financial_evidence(
            {**evaluation, "investigation_date": day}, financial
        ) is None:
            raise ValueError("Historical revenue validation failed")

        revenue = financial["purchase_revenue_usd"]
        evidence_type = "recorded"
        assumption = None

    # Modified BigQuery data for the interview.
    elif model_name == "fct_daily_ecommerce_red_demo":
        if current["sessions"] != 5461:
            raise ValueError("Simulation differs from historical traffic")

        purchasing_sessions = current["purchasing_sessions"]

        if not 0 <= purchasing_sessions <= 91:
            raise ValueError("Invalid simulated purchasing-session count")

        revenue = round(
            financial["purchase_revenue_usd"]
            * purchasing_sessions / 91,
            2,
        )

        evidence_type = "modeled"
        assumption = (
            "Historical revenue per purchasing session held constant"
        )

    else:
        return None

    difference = round(revenue - baseline, 2)

    return {
        "evidence_type": evidence_type,
        "revenue_usd": revenue,
        "baseline_revenue_usd": baseline,
        "revenue_difference_usd": difference,
        "revenue_change_pct": round(
            (revenue / baseline - 1) * 100, 1
        ),
        "assumption": assumption,
        "currency": "USD",
    }


def build_financial_record(day: str, baseline_dates: list[str], daily: dict[str, dict]) -> dict:
    """Keep observed dollars distinct from a noncausal baseline comparison."""
    if len(baseline_dates) != 4 or len(set(baseline_dates)) != 4:
        raise ValueError("Requires four distinct baseline dates")
    for value in [day, *baseline_dates]:
        date.fromisoformat(value)
    if any(value not in daily for value in [day, *baseline_dates]):
        raise ValueError("One or more matching-weekday dates have no purchase data")
    current = daily[day]
    base = sum(daily[d]["purchase_revenue_usd"] for d in baseline_dates) / 4
    actual = current["purchase_revenue_usd"]
    record = {
        "date": day,
        "source": "GA4 public ecommerce sample · purchase events",
        "currency": "USD",
        "purchase_events": current["purchase_events"],
        "purchases_with_revenue": current["purchases_with_revenue"],
        "positive_revenue_events": current["positive_revenue_events"],
        "distinct_transaction_ids": current["distinct_transaction_ids"],
        "purchase_revenue_usd": actual,
        "baseline_dates": baseline_dates,
        "baseline_revenue_usd": round(base, 2),
        "revenue_difference_usd": round(actual - base, 2),
        "relative_revenue_change_pct": round((actual / base - 1) * 100, 1) if base else None,
        "status": "observed_revenue_with_descriptive_baseline",
        "limitations": "Obfuscated GA4 sample; purchase-event revenue, not reconciled ledger revenue. Difference from baseline is not attributable lost revenue or a forecast.",
    }
    return validate_financial_record(record, day)


def reporting_financial_evidence(row: dict, financial: dict | None = None) -> dict | None:
    """Prefer financial fields from the validated reporting pipeline.

    Backwards-compatible historical fallback supports the older public
    snapshot. Never use historical raw revenue for a different scenario.
    """
    import math

    fields = (
        "purchase_revenue_usd",
        "baseline_revenue_usd",
        "revenue_difference_usd",
        "revenue_change_pct",
        "revenue_evidence_type",
        "purchase_events_with_revenue",
    )
    # An incomplete reporting record must not silently use stale revenue.
    if any(row.get(field) is not None for field in fields):
        if any(row.get(field) is None for field in fields):
            return None
        kind = row["revenue_evidence_type"]
        if kind not in ("recorded", "modeled"):
            return None
        try:
            values = [float(row[name]) for name in fields[:4]]
            coverage = row["purchase_events_with_revenue"]
        except (TypeError, ValueError, OverflowError):
            return None
        revenue, baseline, difference, percent = values
        if (
            not all(math.isfinite(v) for v in values)
            or revenue < 0 or baseline <= 0
            or type(coverage) is not int or coverage < 0
            or abs((revenue - baseline) - difference) > 0.03
            or abs(100 * difference / baseline - percent) > 0.2
        ):
            return None
        return {
            "purchase_revenue_usd": revenue,
            "baseline_revenue_usd": baseline,
            "revenue_difference_usd": difference,
            "relative_revenue_change_pct": percent,
            "revenue_evidence_type": kind,
            "purchases_with_revenue": coverage,
            "purchase_events": None,  # Not included in reporting rows.
            "distinct_transaction_ids": None,
        }

    # Legacy snapshot only: validated recorded GA4 evidence.
    historical = matching_financial_evidence(row, financial)
    return ({**historical, "revenue_evidence_type": "recorded"}
            if historical is not None else None)


def fetch_from_bigquery(day: str, baseline_dates: list[str], max_mib: int = 64):
    from google.cloud import bigquery
    dates = [day, *baseline_dates]
    suffixes = [date.fromisoformat(d).strftime("%Y%m%d") for d in dates]
    # Quoted date suffixes are validated before interpolation.
    selected = ",".join(f"'{suffix}'" for suffix in suffixes)
    sql = f"""
    SELECT FORMAT_DATE('%Y-%m-%d', PARSE_DATE('%Y%m%d', _TABLE_SUFFIX)) AS day,
      COUNT(*) AS purchase_events,
      COUNTIF(ecommerce.purchase_revenue_in_usd IS NOT NULL) AS purchases_with_revenue,
      COUNTIF(ecommerce.purchase_revenue_in_usd > 0) AS positive_revenue_events,
      COUNT(DISTINCT NULLIF(ecommerce.transaction_id,'')) AS distinct_transaction_ids,
      ROUND(SUM(COALESCE(ecommerce.purchase_revenue_in_usd,0)),2) AS purchase_revenue_usd
    FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    WHERE _TABLE_SUFFIX IN ({selected}) AND event_name='purchase'
    GROUP BY day
    """
    client = bigquery.Client(project=PROJECT)
    dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False), location="US")
    estimated = dry.total_bytes_processed
    print(f"Estimated query scan: {estimated / 1048576:.2f} MiB")
    budget = max_mib * 1048576
    if estimated > budget:
        raise ValueError(f"Refusing query exceeding {max_mib} MiB guard")
    job = client.query(sql, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=budget), location="US")
    results = {str(r.day): {k: r[k] for k in ("purchase_events", "purchases_with_revenue", "positive_revenue_events", "distinct_transaction_ids", "purchase_revenue_usd")} for r in job.result()}
    return build_financial_record(day, baseline_dates, results)


def main():
    parser = argparse.ArgumentParser(description="Optional read-only GA4 revenue evidence collection")
    parser.add_argument("--date", default="2020-12-07")
    parser.add_argument("--fetch", action="store_true", help="Run guarded BigQuery read, not only a preview")
    args = parser.parse_args()
    source = json.loads((OUTPUTS / "ga4_executive_reporting.json").read_text(encoding="utf-8"))
    selected = next((r for r in source if r["investigation_date"] == args.date), None)
    if not selected:
        raise ValueError("Requested day is absent from reporting records")
    if not args.fetch:
        print("Preview only. Selected date:", args.date)
        print("Matching-weekday baseline:", ", ".join(selected["baseline_dates"]))
        print("Run with --fetch for guarded BigQuery query. No data changed.")
        return
    data = fetch_from_bigquery(args.date, selected["baseline_dates"])
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    target = OUTPUTS / f"ga4_financial_evidence_{args.date}.json"
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({k: data[k] for k in ("date", "purchase_revenue_usd", "baseline_revenue_usd", "revenue_difference_usd", "relative_revenue_change_pct")}, indent=2))
    print("Saved:", target)


if __name__ == "__main__":
    main()
