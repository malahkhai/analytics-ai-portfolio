
"""Prepare GA4 investigations for executive reporting."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def load_json(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def build_reporting_rows(diagnostics, ai_report):
    evaluations = diagnostics["evaluations"]

    if not evaluations:
        raise ValueError("No diagnostic evaluations found.")

    ai_evidence = ai_report["source_evidence"]["evidence"]
    ai_date = ai_evidence["date"]

    # Verify that the AI report refers to genuine
    # evidence in the diagnostic dataset.
    matching = [
        row for row in evaluations
        if row["date"] == ai_date
        and row["scope"] == ai_evidence["scope"]
    ]

    if len(matching) != 1:
        raise ValueError(
            "AI evidence has no unique diagnostic match."
        )

    original = matching[0]

    for field in [
        "observed_sessions",
        "session_change_pct",
        "purchase_rate_change_pct",
        "estimated_purchase_session_gap",
        "status",
    ]:
        if original[field] != ai_evidence[field]:
            raise ValueError(
                f"AI source evidence mismatch: {field}"
            )

    interpretation = ai_report["ai_interpretation"]
    validation = ai_report["validation"]

    rows = []

    for item in evaluations:
        has_ai = (
            item["date"] == ai_date
            and item["scope"] == ai_evidence["scope"]
        )

        row = {
            "investigation_date": item["date"],
            "scope": item["scope"],
            "source": diagnostics["source"],
            "baseline_dates": item["baseline_dates"],
            "observed_sessions": item["observed_sessions"],
            "baseline_sessions": item["baseline_sessions"],
            "session_change_pct": item["session_change_pct"],
            "observed_purchase_rate_pct": (
                item["observed_purchase_rate_pct"]
            ),
            "baseline_purchase_rate_pct": (
                item["baseline_purchase_rate_pct"]
            ),
            "purchase_rate_change_pct": (
                item["purchase_rate_change_pct"]
            ),
            "estimated_purchase_session_gap": (
                item["estimated_purchase_session_gap"]
            ),
            "alert_status": item["status"],
            "alert_types": item["alert_types"],
            "has_ai_investigation": has_ai,
            "executive_summary": (
                interpretation["executive_summary"]
                if has_ai else None
            ),
            "why_no_alert": (
                interpretation["why_no_alert"]
                if has_ai else None
            ),
            "hypotheses_json": (
                json.dumps(interpretation["hypotheses"])
                if has_ai else None
            ),
            "recommended_checks_json": (
                json.dumps(
                    interpretation["recommended_checks"]
                )
                if has_ai else None
            ),
            "factual_review_status": (
                validation["factual_review_status"]
                if has_ai else "not_generated"
            ),
        }

        rows.append(row)

    return rows


def main():
    diagnostics = load_json(
        OUTPUTS / "ga4_diagnostics.json"
    )

    ai_report = load_json(
        OUTPUTS / "ga4_ai_structured_2020-12-07.json"
    )

    rows = build_reporting_rows(
        diagnostics, ai_report
    )

    destination = (
        OUTPUTS / "ga4_executive_reporting.json"
    )

    destination.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("EXECUTIVE REPORTING DATASET")
    print(f"Reporting rows: {len(rows)}")
    print(
        "Rows with AI investigation:",
        sum(r["has_ai_investigation"] for r in rows),
    )

    for row in rows:
        print(
            row["investigation_date"],
            "| sessions:", row["observed_sessions"],
            "| AI:", row["has_ai_investigation"],
            "| review:", row["factual_review_status"],
        )

    print(f"\nSaved: {destination}")


if __name__ == "__main__":
    main()
