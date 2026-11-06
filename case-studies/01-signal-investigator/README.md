# Signal Investigator

## Maxim — AI Analytics Investigation Agent

**Status:** Working portfolio case study · Stakeholder interface deployed on Streamlit Community Cloud

[Explore Maxim's live executive report](https://maxim-signal-investigator.streamlit.app/?window=all&date=2020-12-07)

**Stack:** Public GA4 ecommerce sample · BigQuery · dbt · Python · Gemini · Streamlit

### Business question

When ecommerce performance changes unexpectedly, **what changed, what is the potential financial implication, and what should the relevant business team investigate first?**

**Maxim is the AI investigation agent.** Its workflow combines a deterministic detection engine, tool-supported Gemini analysis, structured evidence validation, and business recommendations. **Streamlit is the presentation layer** for Maxim's investigation; PDF export and email preview make the findings easier to share with stakeholders.

## System workflow

```text
Historical GA4 ecommerce events
             ↓
BigQuery + dbt — daily sessions, purchases, purchase-session rate and revenue
             ↓
Python reader + adapter — data validation and consistent metric definitions
             ↓
Python anomaly detector — matching-weekday baseline, threshold checks
             ↓
Validated diagnostic evidence, including revenue comparisons
             ↓
Maxim / Gemini — bounded tool calls, hypotheses and recommended checks
             ↓
Structured AI findings + executive reporting adapter
             ↓
Stakeholder presentation — Streamlit, PDF export, email preview
```

The detection thresholds are **deterministic**, not AI-generated. Gemini receives the measured and modeled evidence and interprets it; it cannot establish root causes or turn a modeled revenue variance into an actual loss. AI findings remain subject to factual review.

## Investigation results

The dataset is Google's **public, obfuscated GA4 ecommerce sample** from 2020. The analysis covers 37 days, with 9 dates eligible for comparison against their four previous matching weekdays.

| 7 December 2020 | Original historical sample | Controlled red-alert scenario |
| --- | ---: | ---: |
| Sessions | 5,461 | 5,461 |
| Session growth vs. baseline | +42.0% | +42.0% |
| Purchase-session rate | 1.67% | 1.03% |
| Relative purchase-rate change | −14.5% | −47.4% |
| Estimated purchasing-session gap | 15.5 | 50.5 |
| Revenue (USD) | **$8,472 recorded** | **$5,213.54 modeled** |
| Four-Monday revenue baseline | $6,918 | $6,918 |
| Revenue vs. baseline | **+$1,554 (+22.5%)** | **−$1,704.46 (−24.6%) modeled** |
| Detector outcome | Yellow watchlist; no qualifying red alert | Red alert: `session_purchase_rate_drop` |

The controlled red scenario uses a **separate copy of the transformed BigQuery data** with deliberately changed purchase metrics. Its revenue is **modeled** by holding the original day's revenue per purchasing session constant; it is **not observed red-scenario revenue**. The modeled $1,704.46 deficit is a comparison against the historical Monday benchmark, **not proven lost sales**.

The red scenario meets the three alert criteria: at least 150 sessions, a relative purchase-rate decline of at least 35%, and an estimated purchasing-session gap of at least 15. The original historical case does not meet the 35% decline threshold. These are defined heuristics, not a test of statistical significance.

## What Maxim produces

- An executive explanation of traffic, purchase efficiency, and financial context.
- A transparent account of why an alert did or did not trigger.
- Three plausible hypotheses and three recommended analytical checks.
- Suggested business owner roles for follow-up, not real assignments.
- A stakeholder-facing investigation report with supporting KPIs, PDF export, and an email draft preview.

The agent uses bounded tools including `get_ga4_diagnostic` and `compare_ga4_performance`; source evidence is checked against the generated report before presentation. The hypotheses—such as traffic-quality dilution, checkout friction, or stock availability—are **not established causes**.

## Published reporting interface

The [live Streamlit report](https://maxim-signal-investigator.streamlit.app/?window=all&date=2020-12-07) shows the **historical yellow-watchlist investigation** from a version-controlled report snapshot (`demo_data/executive_report.json`). Visitors do not need BigQuery or Gemini credentials.

The underlying investigation pipeline can be run separately with authenticated BigQuery and Gemini access. **The hosted viewer does not execute Gemini or refresh BigQuery automatically.** The email popup supports owner-connected Outlook delivery: visitors enter an address and request the report without signing into Microsoft. Live sending requires the owner-only hosting secrets described in [Outlook setup](docs/outlook-sender-setup.md); draft download remains available when the sender is not connected. PDF export produces a compact, paginated document with the complete selected assessment, proposed checks and measured evidence.

## Main components

| Path | Responsibility |
| --- | --- |
| `dbt/signal_investigator_dbt/models/marts/fct_daily_ecommerce.sql` | Daily ecommerce transformation, including purchase revenue |
| `src/bigquery_reader.py` | Read the selected transformed BigQuery source with a query-size safeguard |
| `src/ga4_adapter.py` | Validate and standardize GA4 daily metrics |
| `src/detect_ga4.py` | Deterministic anomaly detection |
| `src/ga4_diagnostics.py` | Baseline comparisons and financial diagnostic evidence |
| `src/ai_tool_agent.py` | Gemini tool-using investigation |
| `src/ai_investigation_structured.py` | Structured investigation and schema validation |
| `src/ga4_reporting_adapter.py` | Evidence-aligned reporting records |
| `streamlit_app.py` | Maxim's stakeholder presentation interface |
| `src/executive_pdf.py` | PDF executive brief |
| `src/email_delivery.py` | Stakeholder email draft preview |
| `demo_data/executive_report.json` | Version-controlled historical report for public viewing |
| `tests/` | Automated validation and regression tests |

**Testing:** 118 tests passed in the latest reported local run on 6 November 2026. This demonstrates local validation, not production readiness.

## Interpretation and limitations

- **Source:** The GA4 sample is historical and obfuscated; it is not evidence of current business performance.
- **Scenario provenance:** The red alert is a controlled modification, not a real historical incident.
- **Revenue evidence:** The yellow case uses recorded GA4 purchase-event revenue; the red case uses an assumption-based model. Neither the purchasing-session gap nor the modeled revenue deficit is proven lost revenue.
- **Analytical limits:** Daily aggregates cannot establish which channel, device, checkout step, or inventory issue caused a change. Rankings and thresholds do not prove statistical significance.
- **Human oversight:** AI-generated interpretations and suggested business actions require review.
- **Deployment:** The public report is a published snapshot; it does not continuously monitor or investigate changing data.

## References

- [Google GA4 public ecommerce BigQuery sample](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset)
- [dbt for BigQuery](https://docs.getdbt.com/guides/bigquery)
- [Gemini API function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
