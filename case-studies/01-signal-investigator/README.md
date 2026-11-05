# Signal Investigator

### AI-assisted ecommerce anomaly investigation · Portfolio case study

**Stack:** Google Analytics 4 public sample · BigQuery · dbt · Python · Gemini · Streamlit
**Status:** Working investigation prototype and interview demonstration. Streamlit Cloud deployment pending.

Signal Investigator helps an analyst answer a business question: **When ecommerce performance changes unexpectedly, what happened, how substantial is it, and what should the relevant business team investigate first?**

It combines auditable Python detection, tool-supported Gemini investigation, and **Maxim**, a stakeholder-facing executive report. It does **not** assert unverified root causes or treat estimated purchasing-session gaps as confirmed lost sales.

<!-- Replace this line once Streamlit is deployed. -->
**Live Maxim dashboard:** Link to be added after deployment.

## The workflow

```text
Google public GA4 ecommerce sample
             ↓
BigQuery + dbt → fct_daily_ecommerce
             ↓
Python BigQuery reader → GA4 adapter → deterministic anomaly detector
             ↓
GA4 diagnostic evidence (JSON)
             ↓
Gemini tool-using investigation + schema-validated structured findings
             ↓
Python executive reporting adapter (JSON)
             ↓
Maxim — Streamlit stakeholder dashboard / PDF / email preview
```

**Local execution:** The investigation scripts are run deliberately by the analyst. There is **no scheduled automation or continuous ingestion** in this case-study deployment.

**Hosted dashboard:** Streamlit reads the committed investigation snapshot in `demo_data/executive_report.json` when local generated output is unavailable. It does not require recruiters to authenticate to BigQuery or Gemini.

## Results: historical evidence vs. interview simulation

The analysis uses a **public, obfuscated GA4 ecommerce sample from 2020**. Daily aggregates cover 37 days in the analysed window; 9 dates had sufficient data for a comparison with four prior matching weekdays.

| Metric — 7 December 2020 | Original historical sample | Modified red-alert demonstration |
| --- | ---: | ---: |
| Sessions | 5,461 | 5,461 |
| Sessions vs. four-Monday baseline | +42.0% | +42.0% |
| Baseline purchasing-session rate | 1.95% | 1.95% |
| Observed purchasing-session rate | 1.67% | 1.03% |
| Relative purchasing-session-rate change | −14.5% | −47.4% |
| Estimated purchasing-session gap | 15.5 | 50.5 |
| Detector outcome | No qualifying red alert; watchlist case | **Red alert: `session_purchase_rate_drop`** |

The red demonstration uses a **separate copy** of the already transformed BigQuery data, `fct_daily_ecommerce_red_demo`, with deliberately modified purchase metrics for 7 December; the original `fct_daily_ecommerce` table remains unchanged. No new dbt run is required when switching the input to the existing Python detector.

The red case satisfies all three configured alert conditions: **at least 150 sessions, at least a 35% relative purchasing-session-rate decline, and at least a 15-session estimated gap**. These are heuristic thresholds, not a statistical-significance test.

Gemini uses two bounded analysis tools (`get_ga4_diagnostic` and `compare_ga4_performance`) and produces an executive narrative, three plausible hypotheses, and three recommended analytical checks. Explanations such as traffic-quality dilution, checkout friction, or inventory availability are **hypotheses**, not verified causes. AI interpretations remain subject to factual review.

## Running the local interview demo

The source code and scripts are versioned on GitHub, but the BigQuery tables and API credentials remain in the owner's Google Cloud environment. Local execution requires an activated Python virtual environment with dependencies installed, Google BigQuery authentication, and an authorized Gemini API key.

From `case-studies/01-signal-investigator/`:

```bash
# Modified BigQuery copy → real red alert → Gemini → Maxim
./scripts/run_demo.sh red

# Original BigQuery source → historical investigation → Maxim
./scripts/run_demo.sh original
```

The script runs the existing diagnostic, tool-using Gemini agent, structured Gemini investigation, executive reporting adapter, then starts Streamlit locally. It does not modify BigQuery data. Use `Ctrl+C` to stop Streamlit before switching scenarios.

For tests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

**Latest local verification (5 November 2026): 110 tests passed.** This is a local test result; it is not a claim of production readiness.

## Online dashboard vs. local workflow

| | Public-facing Streamlit dashboard | Local interview demo |
| --- | --- | --- |
| Data | Version-controlled report snapshot | Selected BigQuery transformed table |
| Gemini calls on page load | No | No; scripts execute before the page opens |
| Dashboard reflects changed data | When an updated snapshot is committed and deployed | After running the scripts again |
| Credentials needed by viewer | No | Local owner credentials required to regenerate reports |
| Intended audience | Recruiters and stakeholders | Technical walkthrough and interview |

Streamlit Community Cloud entrypoint: `case-studies/01-signal-investigator/streamlit_app.py`. The Python dependency file is alongside that entrypoint. Do not commit `.env`, local credentials, or `.streamlit/secrets.toml`.

## Main project files

| Path | Responsibility |
| --- | --- |
| `src/bigquery_reader.py` | Read selected transformed BigQuery table with a query-size safeguard |
| `src/ga4_adapter.py` | Standardize daily GA4 metrics |
| `src/detect_ga4.py` | Deterministic anomaly checks |
| `src/ga4_diagnostics.py` | Generate evidence and baseline comparisons |
| `src/ai_tool_agent.py` | Gemini analysis using bounded tools |
| `src/ai_investigation_structured.py` | Structured investigation with schema validation |
| `src/ga4_reporting_adapter.py` | Combine diagnostics and AI findings for executive reporting |
| `streamlit_app.py` | Maxim dashboard and reporting experience |
| `demo_data/executive_report.json` | Portable, versioned report snapshot for hosted viewing |
| `scripts/run_demo.sh` | One-command local scenario execution |
| `tests/` | Automated unit and integration-style checks |

The repository also preserves the earlier synthetic-channel detection and funnel-investigation exercises as development history. They are not the input to the current GA4 executive report.

## Interpretation and limitations

- **Case-study provenance:** The red incident is a controlled modification of historical transformed data. It must not be presented as an actual event at an operating business.
- **Observed vs. modelled:** Purchasing sessions are not orders. The estimated 50.5-session gap measures departure from the chosen historical benchmark; it is not confirmed lost transactions or revenue.
- **Incomplete diagnostic dimensions:** The current daily model does not support causal attribution by campaign, device, inventory status, payment processor, or checkout step.
- **Evidence quality:** Google's obfuscated public sample can contain inconsistencies. The agent does not establish causal or statistical significance from the aggregate comparison.
- **Human review:** AI hypotheses and recommended actions require analyst validation before operational decisions.
- **Financial impact:** The original GA4 day has historical revenue fields, but the modified red scenario does not yet have a consistent revenue model. Financial-impact comparison is **the next planned enhancement after dashboard deployment**, not a completed feature.
- **Email:** The dashboard supports an email-preview workflow. Live sending from an Outlook account requires separate delegated authorization and is not configured in the public demo.

## Next milestone

1. Deploy Maxim from the committed, static report snapshot to Streamlit Community Cloud.
2. Add the live dashboard link to this README and the portfolio README.
3. Extend the *existing* investigation with verified recorded revenue, a same-weekday revenue baseline, and a carefully qualified financial-impact estimate.

## Data and technical references

- [Google GA4 public ecommerce BigQuery sample](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset)
- [dbt for BigQuery](https://docs.getdbt.com/guides/bigquery)
- [Gemini API function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Streamlit Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
