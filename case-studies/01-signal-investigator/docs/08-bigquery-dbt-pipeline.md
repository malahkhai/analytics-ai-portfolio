
# Signal Investigator — BigQuery & dbt Pipeline

## Objective

Build a reusable, tested ecommerce analytics model
that can eventually supply reliable metrics to the
Signal Investigator analytics investigation engine.

## Technology Stack

- Google BigQuery — cloud data warehouse
- dbt 2.0.9 — SQL transformation and testing
- Google Cloud CLI — authentication and configuration
- VS Code — local development environment
- SQL and YAML — transformation and data-quality rules

## Data Source

Google's public GA4 ecommerce sample dataset:

`bigquery-public-data.ga4_obfuscated_sample_ecommerce`

Analysis period: December 1–7, 2020.

The public sample data is separate from the synthetic
incident data used by the Python investigation engine.

## Data Architecture

GA4 Public Ecommerce Events
        |
        v
BigQuery Source Data
        |
        v
dbt SQL Transformation
        |
        v
fct_daily_ecommerce (BigQuery View)
        |
        v
dbt Data-Quality Tests
        |
        v
Validated Ecommerce Metrics
        |
        v
Future: Python Investigation Engine

## Transformation Model

Model: `fct_daily_ecommerce`

BigQuery destination:
`signal-investigator-analytics.signal_investigator_dev.fct_daily_ecommerce`

The model produces daily metrics including:

- Sessions
- Page views
- Product views
- Add-to-cart events
- Checkout events
- Purchase events
- Purchasing sessions
- Session purchase rate

Purchase rate definition:

Purchasing sessions / Total sessions * 100

## Data-Quality Testing

Eight automated dbt tests were implemented.

Standard tests (6):
- Event date is not null
- Event date is unique
- Session count is not null
- Purchase event count is not null
- Purchasing session count is not null
- Session purchase rate is not null

Custom SQL tests (2):
- Session counts must be nonnegative, and purchasing
  sessions cannot exceed total sessions
- Purchase rate must be consistent with the underlying
  counts and remain between 0% and 100%;
  the test also rejects zero or negative sessions

## Validation Results

Command:

`dbt build --select fct_daily_ecommerce`

Execution result:
- 1 BigQuery view built successfully
- 8 data-quality tests passed
- 0 failures
- Total execution time: 42.5 seconds

The model was also verified in BigQuery against the
seven-day ecommerce reporting exercise.

## Current Limitations

- Uses a historical, fixed seven-day sample.
- The BigQuery view reads its source when queried.
- Tests validate defined rules, not every aspect
  of source completeness or business correctness.
- The Python investigation engine is not yet
  connected to this BigQuery model.
- This is a portfolio prototype, not a deployed
  production pipeline.

## Next Development Phase

1. Connect Python to BigQuery.
2. Retrieve validated ecommerce metrics.
3. Apply anomaly detection to the retrieved data.
4. Generate structured investigation evidence.
5. Introduce AI-assisted investigation with Gemini.
6. Evaluate the agent against known test scenarios.
