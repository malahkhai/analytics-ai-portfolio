# Analytics & AI Agents Portfolio

Practical case studies combining **digital analytics, business intelligence, and applied AI agents** to investigate business performance and support better decisions.

My work brings together experience in digital performance, ecommerce analytics, and stakeholder reporting with hands-on development of AI-assisted analytical workflows. Each project documents the business problem, data and methods, implemented capabilities, results, testing, and limitations.

## Featured case study

### 01 · Signal Investigator — Maxim, AI Analytics Investigation Agent

**Status:** Working case study · Executive reporting interface deployed

**[Explore Maxim's live executive report](https://maxim-signal-investigator.streamlit.app/?window=all&date=2020-12-07)** · **[Read the Signal Investigator case study](case-studies/01-signal-investigator/)**

**Maxim is the AI investigation agent.** It combines explainable Python anomaly detection, Gemini tool-assisted investigation, structured evidence validation, and prioritized analytical recommendations. **Streamlit is Maxim's stakeholder-facing reporting interface**, with paginated PDF export and an email report popup. Outlook delivery requires owner authorization; draft preview remains available.

**Implemented capabilities**

- **Ecommerce data modeling:** Public GA4 sample data transformed in BigQuery with dbt, including sessions, purchase activity, conversion rates, and revenue.
- **Anomaly detection:** Validated daily metrics compared against four previous matching weekdays using explicit, testable thresholds.
- **AI investigation:** Gemini uses bounded analytical tools to evaluate evidence, propose hypotheses, and recommend checks without asserting unverified causes.
- **Financial context:** Recorded revenue versus historical baseline, with separately identified modeled financial exposure for demonstration scenarios.
- **Executive reporting:** A deployed Streamlit interface presenting findings, business implications, recommended actions, and exportable reports.
- **Quality assurance:** 118 automated tests passed in the latest local verification (6 November 2026).

**Case-study evidence:** On 7 December 2020, the historical sample showed a **14.5% relative decline in purchase-session rate** while traffic increased **42.0%**. Recorded sample revenue was **$8,472**, or **22.5% above** its four-Monday benchmark. Maxim classified the conversion change as a watchlist case, rather than a qualifying red alert.

**Data integrity:** This project uses historical, obfuscated public GA4 data. A separate, deliberately modified dataset is used to test the red-alert investigation path; its revenue is **modeled**, not observed, and any shortfall is a scenario comparison—not confirmed lost sales. See the [case-study methodology](case-studies/01-signal-investigator/) for details.

## Other planned case studies

### 02 · Marketing Performance & Budget Allocation Agent

**Status: Planned.** Investigate campaign and channel efficiency and support evidence-grounded budget allocation recommendations.

### 03 · Tracking Quality Assurance Agent

**Status: Planned.** Identify measurement implementation errors, event anomalies, missing parameters, and data-quality issues.

### 04 · Executive Analytics Copilot

**Status: Planned.** Explore controlled, evidence-based business questions over trusted analytical data.

## Core capabilities and tools

- **Analytics & business intelligence:** GA4, SQL, ecommerce analytics, conversion measurement, Looker Studio, Power BI.
- **Data & modeling:** Python, BigQuery, dbt, data validation, metric definitions, reproducible analysis.
- **Applied AI agents:** Gemini function calling, structured responses, evidence-grounded interpretation, human review.
- **Delivery & quality:** Git/GitHub, automated testing, documentation, stakeholder reporting, Streamlit.

## Development principles

1. Start with a clear business question and measurable definitions.
2. Establish reliable analytical evidence before asking an AI agent to interpret it.
3. Separate observed results, modeled scenarios, hypotheses, and proposed business actions.
4. Use public or synthetic data transparently and document limitations.
5. Demonstrate working capabilities and their business relevance without overstating production readiness.

**Career focus:** Senior Manager / Lead — Data, Analytics & AI, connecting analytical leadership, business intelligence, and practical AI agents.
