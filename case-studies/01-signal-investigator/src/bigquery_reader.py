
"""Retrieve validated ecommerce metrics from BigQuery."""

import os

from google.cloud import bigquery

PROJECT_ID = "signal-investigator-analytics"
DATASET_ID = "signal_investigator_dev"

# Choose which BigQuery data enters the anomaly detector.
MODEL_NAME = os.getenv(
    "SIGNAL_GA4_MODEL",
    "fct_daily_ecommerce",
)

ALLOWED_MODELS = {
    "fct_daily_ecommerce",
    "fct_daily_ecommerce_red_demo",
}

if MODEL_NAME not in ALLOWED_MODELS:
    raise ValueError(
        f"Unsupported BigQuery source: {MODEL_NAME}"
    )


MAX_BYTES = 1024 ** 3  # 1 GiB


def fetch_daily_ecommerce():
    """Fetch daily ecommerce metrics as Python dictionaries."""

    client = bigquery.Client(
        project=PROJECT_ID,
        location="US",
    )

    query = f"""
        SELECT
            event_day,
            sessions,
            purchase_events,
            purchasing_sessions,
            session_purchase_rate_pct
        FROM `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`
        ORDER BY event_day
    """

    # Check estimated processing before running the query.
    estimate = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
        ),
    )

    estimated_bytes = estimate.total_bytes_processed or 0

    print(
        f"Estimated processing: "
        f"{estimated_bytes / 1024**2:.2f} MiB"
    )

    if estimated_bytes > MAX_BYTES:
        raise RuntimeError(
            "Query blocked: estimated processing exceeds 1 GiB."
        )

    # Execute with a server-side processing limit.
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            maximum_bytes_billed=MAX_BYTES,
        ),
    )

    records = []

    for row in job.result():
        records.append({
            "event_day": row.event_day.isoformat(),
            "sessions": int(row.sessions),
            "purchase_events": int(row.purchase_events),
            "purchasing_sessions": int(row.purchasing_sessions),
            "session_purchase_rate_pct": float(
                row.session_purchase_rate_pct
            ),
        })

    return records


def main():
    records = fetch_daily_ecommerce()

    print(f"\nRetrieved {len(records)} daily records.\n")

    for record in records:
        print(
            f"{record['event_day']} | "
            f"Sessions: {record['sessions']:,} | "
            f"Purchasing sessions: "
            f"{record['purchasing_sessions']:,} | "
            f"Purchase rate: "
            f"{record['session_purchase_rate_pct']}%"
        )


if __name__ == "__main__":
    main()
