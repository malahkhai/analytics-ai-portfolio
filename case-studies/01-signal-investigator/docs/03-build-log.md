# Build log

## Stage 1 · starter baseline
**Status:** Code assembled and tested locally. Does not contain an LLM or a live data source.

**Built:**
- Reproducible synthetic ecommerce CSV with labelled incidents.
- Weekday-matched baseline detector and JSON alert output.
- Unit tests for known incidents and stable data.
- Project charter, architecture, metric glossary, evaluation plan and release checklist.

**Next development checkpoint:** Query Google's public GA4 BigQuery sample, inspect what events exist, compare sample metrics with the mock schema, and define the first dbt source/staging model.

**Decision log:**
- Chose analytics investigation over copilot because numeric detection and evidence can be evaluated independently of natural-language quality.
- Chose a deterministic baseline before LLM orchestration to isolate measurement errors from language-model errors.
- Chose reproducible synthetic data first to avoid credentials, costs and privacy complications.
