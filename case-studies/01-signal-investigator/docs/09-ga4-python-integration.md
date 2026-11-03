
# Signal Investigator — Python + BigQuery Integration

## Objective

Connect the existing Python investigation engine
to validated ecommerce metrics in Google BigQuery.

## Architecture

GA4 Public Ecommerce Dataset
        |
        v
BigQuery + dbt Transformation
        |
        v
fct_daily_ecommerce
        |
        v
Python BigQuery Client
        |
        v
GA4 Data Adapter
        |
        v
Historical Baseline Validation
        |
        v
Deterministic Anomaly Detection
        |
        v
Structured Diagnostic Evidence
        |
        v
Future: Gemini AI Investigation Agent

## Historical Data

Source: Google GA4 public ecommerce sample.

Period: November 1 – December 7, 2020.

- 37 daily records
- 9 dates with complete matching-weekday baselines
- Four prior matching weekdays used for comparisons

## Detection Rules

1. Session purchase-rate decline of at least 35%
2. Minimum estimated shortfall of 15 purchasing sessions
3. Minimum 150 current sessions for rate detection
4. Session decline of at least 35% against baseline

Thresholds are configurable, not statistically calibrated.

## Actual Investigation Results

The historical GA4 run produced zero qualifying alerts.

December 7, 2020 was the strongest purchase-rate
decline among the eligible dates:

- Sessions: +42.0%
- Session purchase rate: -14.5%
- Estimated purchasing-session shortfall: 15.5

The decline did not meet the 35% alert threshold.

These results describe observed performance changes.
They do not establish the causes.

## Validation

- 8 dbt tests passed
- 29 Python tests passed
- Python successfully retrieved BigQuery metrics
- Adapter validation passed
- Historical readiness validation passed
- Diagnostic JSON evidence generated

## Limitations

- Uses historical, obfuscated public GA4 data
- No live ingestion or scheduling
- Aggregated data lacks channel-level diagnostics
- No confirmed root-cause analysis
- Gemini AI reasoning has not yet been implemented

## Next Phase

Introduce Gemini to generate evidence-grounded
investigation summaries, hypotheses and next steps.
