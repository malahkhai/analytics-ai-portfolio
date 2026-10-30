# Signal Investigator — dbt Analytics Pipeline

## Overview

This dbt project transforms Google's public GA4 ecommerce sample data into a reusable, tested BigQuery analytics model.

It is part of the Signal Investigator portfolio project, which explores automated analytics anomaly detection and investigation.

## Technology

- Google BigQuery — data warehouse
- dbt 2.0.9 — SQL transformation and data-quality testing
- SQL and YAML — data models and validation rules
- Python — separate investigation engine

## Data Source

Google's public GA4 ecommerce dataset:

`bigquery-public-data.ga4_obfuscated_sample_ecommerce`

Analysis period: December 1–7, 2020.

## Analytics Model

**Model:** `fct_daily_ecommerce`

**BigQuery destination:** `signal-investigator-analytics.signal_investigator_dev.fct_daily_ecommerce`

The model calculates daily sessions, page views, product views, add-to-cart events, checkout events, purchase events, purchasing sessions, and session purchase rate.

Session purchase rate is calculated as:

`Purchasing sessions / Sessions × 100`

## Data-Quality Tests

Eight tests validate the model:

- Six built-in dbt tests for date uniqueness and required values
- One custom test for valid session counts
- One custom test for conversion-rate consistency

## Running the Project

Configure Google Cloud Application Default Credentials and a dbt BigQuery profile named `signal_investigator_dbt`.

From this project directory, run:

```bash
dbt debug
dbt build --select fct_daily_ecommerce
```

To run the tests separately:

```bash
dbt test --select fct_daily_ecommerce
```

## Verified Results

The first complete build succeeded with:

- 1 BigQuery view created
- 8 data-quality tests passed
- 0 failures
- 42.5 seconds total execution time

## Current Limitations

The model uses a fixed historical seven-day dataset. It is not a live GA4 ingestion pipeline.

The Python anomaly-detection engine currently uses a separate synthetic dataset and has not yet been connected to this BigQuery model.

## Next Phase

Connect Python to BigQuery, retrieve validated analytics metrics, and extend Signal Investigator toward evidence-grounded AI-assisted investigation.

For the complete case study, see `../../../docs/08-bigquery-dbt-pipeline.md`.