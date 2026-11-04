
"""Validate and optionally upload executive investigations to BigQuery."""

import argparse
import json
from datetime import date
from pathlib import Path

from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "ga4_executive_reporting.json"

PROJECT = "signal-investigator-analytics"
DATASET = "signal_investigator_dev"
TABLE = f"{PROJECT}.{DATASET}.executive_investigations"


SCHEMA = [
    bigquery.SchemaField("investigation_date", "DATE"),
    bigquery.SchemaField("scope", "STRING"),
    bigquery.SchemaField("source", "STRING"),
    bigquery.SchemaField(
        "baseline_dates", "DATE", mode="REPEATED"
    ),
    bigquery.SchemaField("observed_sessions", "INTEGER"),
    bigquery.SchemaField("baseline_sessions", "FLOAT"),
    bigquery.SchemaField("session_change_pct", "FLOAT"),
    bigquery.SchemaField(
        "observed_purchase_rate_pct", "FLOAT"
    ),
    bigquery.SchemaField(
        "baseline_purchase_rate_pct", "FLOAT"
    ),
    bigquery.SchemaField(
        "purchase_rate_change_pct", "FLOAT"
    ),
    bigquery.SchemaField(
        "estimated_purchase_session_gap", "FLOAT"
    ),
    bigquery.SchemaField("alert_status", "STRING"),
    bigquery.SchemaField(
        "alert_types", "STRING", mode="REPEATED"
    ),
    bigquery.SchemaField(
        "has_ai_investigation", "BOOLEAN"
    ),
    bigquery.SchemaField("executive_summary", "STRING"),
    bigquery.SchemaField("why_no_alert", "STRING"),
    bigquery.SchemaField("hypotheses_json", "STRING"),
    bigquery.SchemaField(
        "recommended_checks_json", "STRING"
    ),
    bigquery.SchemaField(
        "factual_review_status", "STRING"
    ),
]


def validate_rows(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Reporting dataset must contain rows.")

    expected_fields = {field.name for field in SCHEMA}
    seen = set()

    for row in rows:
        if set(row) != expected_fields:
            raise ValueError(
                "Reporting fields do not match BigQuery schema."
            )

        date.fromisoformat(row["investigation_date"])

        for baseline_day in row["baseline_dates"]:
            date.fromisoformat(baseline_day)

        key = (row["investigation_date"], row["scope"])

        if key in seen:
            raise ValueError(
                f"Duplicate investigation: {key}"
            )

        seen.add(key)

        if row["has_ai_investigation"]:
            if not row["executive_summary"]:
                raise ValueError(
                    "AI investigation lacks executive summary."
                )
            if row["factual_review_status"] == "not_generated":
                raise ValueError(
                    "AI investigation has invalid review status."
                )
        else:
            if row["executive_summary"] is not None:
                raise ValueError(
                    "AI summary exists without investigation."
                )
            if row["factual_review_status"] != "not_generated":
                raise ValueError(
                    "Non-AI row has incorrect review status."
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Explicitly upload validated rows to BigQuery.",
    )
    args = parser.parse_args()

    rows = json.loads(SOURCE.read_text(encoding="utf-8"))
    validate_rows(rows)

    print("\nBIGQUERY EXECUTIVE REPORTING")
    print(f"Destination: {TABLE}")
    print(f"Schema columns: {len(SCHEMA)}")
    print(f"Validated rows: {len(rows)}")
    print(
        "Rows with AI:",
        sum(row["has_ai_investigation"] for row in rows),
    )
    print(
        "Pending factual reviews:",
        sum(
            row["factual_review_status"] == "pending"
            for row in rows
        ),
    )

    if not args.upload:
        print("\nVALIDATION ONLY — No BigQuery upload.")
        return

    client = bigquery.Client(project=PROJECT)
    dataset = client.get_dataset(f"{PROJECT}.{DATASET}")

    config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        write_disposition=bigquery.WriteDisposition.WRITE_EMPTY,
    )

    job = client.load_table_from_json(
        rows,
        TABLE,
        job_config=config,
        location=dataset.location,
    )

    job.result()

    destination = client.get_table(TABLE)
    print(f"\nUploaded rows: {destination.num_rows}")
    print(f"BigQuery table: {TABLE}")


if __name__ == "__main__":
    main()
