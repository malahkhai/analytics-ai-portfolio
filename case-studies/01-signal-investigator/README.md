# Signal Investigator — Analytics Investigation Agent (Portfolio Case Study)

> **Stage 1 of 6 — v0.1 analytical baseline, not yet AI-powered.**

**What it does today:** analyses simulated daily ecommerce metrics and creates transparent, reproducible alerts when a channel's conversion rate or session volume declines markedly versus its four previous matching weekdays. Results include data-backed comparisons, dates and proposed verification checks; no causes are asserted.

**What we will build:** GA4 → BigQuery → dbt → an evaluated detection service → a Gemini tool-calling agent → an interactive evidence-based demo, with Fivetran ingesting campaign spend from Google Sheets into the warehouse in a later stage.

## Try it locally (Python 3.10+; no pip installs needed)

```bash
python -m src.generate_data
python -m src.detect
python -m unittest discover -s tests -v
```

Find the structured output in `outputs/investigations.json`. No accounts, API keys, or billing required.

## Demo incidents (known synthetic ground truth)
- 2026-10-13: Paid search conversion-rate collapse.
- 2026-10-14: Paid search conversion-rate collapse.
- 2026-10-20: Email traffic collapse.

The detector uses a pooled conversion rate from the previous four matching weekdays and a minimum 35% decline threshold; for conversion alerts it requires a minimum 150 current sessions and estimated 15-order deficit. This is a teaching baseline, not a validated production model.

## Project files

| Path | What to read |
| --- | --- |
| `docs/01-project-charter.md` | Business problem, MVP, success criteria |
| `docs/02-architecture.md` | Current/target architecture and cost caveat |
| `docs/03-build-log.md` | Decisions, stage results and what happens next |
| `docs/04-metric-definitions.md` | Reproducible metric/data contract |
| `docs/05-evaluation-plan.md` | Unit tests now; faithfulness and accuracy later |
| `docs/06-publication-checklist.md` | Checklist for a credible public case study |
| `src/generate_data.py` | Reproducible demo-data generator |
| `src/detect.py` | Explanation-first analytical detection |
| `sql/ga4_public_sample_daily_metrics.sql` | Next-stage exploration of a public GA4 dataset |

## Six-stage plan
1. **Define the investigation problem and build a deterministic baseline** (this repository).
2. Query real public GA4 ecommerce sample data; model validated metrics with **dbt**.
3. Add **Fivetran** ingestion of sample campaign spend from Google Sheets and data lineage.
4. Build a bounded **Gemini function-calling agent** over trusted analytic tools.
5. Create a readable UI, human-in-the-loop investigations and a business-style demo.
6. Evaluate, document, deploy, and publish a GitHub/LinkedIn case study.

## Reality checks
- All provided CSV figures are **synthetic**, not a company's observed performance.
- Google's public GA4 dataset covers 2020-11-01 through 2021-01-31 and is obfuscated with documented inconsistencies; it cannot be used as proof of any current ecommerce incident.
- BigQuery Sandbox can query public data at no cost, but **Fivetran BigQuery destination does not support sandbox accounts**. Using Fivetran → BigQuery later may require a billing-enabled project; set budget alerts.
- A detector is not an AI agent. Never describe Stage 1 as an AI system until the tool-calling agent is actually built.

## References
- Google public GA4 ecommerce sample: https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset
- dbt BigQuery quickstart: https://docs.getdbt.com/guides/bigquery?step=1
- Fivetran Sheets connector: https://fivetran.com/docs/connectors/files/google-sheets/google-sheets-setup-guide
- Fivetran BigQuery destination caveat: https://fivetran.com/docs/destinations/bigquery/setup-guide
- Gemini API Python SDK/function calling: https://ai.google.dev/gemini-api/docs/get-started
