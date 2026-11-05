# Analytics & AI Agents Portfolio


**[Explore the Live Maxim AI Dashboard](https://maxim-signal-investigator.streamlit.app/?window=all&date=2020-12-07)**

Practical case studies connecting **digital analytics, business intelligence, analytics engineering, and applied AI** to business decisions.

My work combines digital performance and ecommerce analytics with hands-on development of data products. Each case study documents the business question, data model, working implementation, evaluation, and limitations—not just a dashboard screenshot.

## Case studies

### 01 · Signal Investigator — AI-assisted ecommerce anomaly investigation

**Status: Working case study; Streamlit publication in progress.**

Signal Investigator examines changes in ecommerce performance, applies explicit anomaly rules, and lets a Gemini agent investigate verified evidence using constrained analytical tools. **Maxim**, the stakeholder dashboard, presents the finding, supporting KPIs, hypotheses, recommended checks, and a PDF / email-preview experience.

**Implemented:**
- GA4 public ecommerce sample transformed in BigQuery with dbt
- Python data adaptation, validation, weekday-baseline comparisons, and anomaly detection
- Gemini tool-using and structured AI investigations with schema checks
- Executive reporting adapter and Streamlit dashboard (Maxim)
- One-command local interview demonstration against two selectable BigQuery tables
- 110 passing automated tests in the latest local verification (5 November 2026)

**Interview demonstration:** The authentic historical sample produces a yellow watchlist for 7 December 2020; a **separately modified copy** of the transformed daily metrics produces a red alert. The red case is a deliberate simulation, not a claim about real historical trading performance. The same Python detection and Gemini investigation path is used in both cases.

[Explore the Signal Investigator case study](case-studies/01-signal-investigator/)

*Maxim live dashboard URL: to be added after deployment.*

### 02 · Marketing Performance & Budget Allocation Agent

**Status: Planned.** Explore channel and campaign performance, budget allocation, and evidence-grounded optimization recommendations.

### 03 · Tracking Quality Assurance Agent

**Status: Planned.** Detect implementation errors, unexpected event changes, and data quality problems in digital measurement.

### 04 · Executive Analytics Copilot

**Status: Planned.** Explore controlled, evidence-based business questions over trusted analytics datasets.

## Technical focus

**Analytics:** GA4, SQL, digital measurement, ecommerce performance, conversion metrics, Power BI, Looker Studio.
**Data engineering:** Python, BigQuery, dbt, source validation and data contracts.
**Applied AI:** Gemini function calling, structured responses, evidence validation and human review.
**Engineering practices:** Git, automated tests, reproducible analytical workflows, documented limitations and stakeholder-facing reporting.

## Development principles

1. Start with a concrete business question and explicitly defined metrics.
2. Establish a deterministic analytical baseline before asking an LLM to interpret findings.
3. Separate observed evidence from hypotheses, modelled gaps, and proposed actions.
4. Use public or synthetic case-study data; never imply a simulated event is a real customer incident.
5. Document what is implemented, what is manual, and what remains planned.

**Career focus:** Senior Manager / Lead roles at the intersection of Data, Analytics & AI.
