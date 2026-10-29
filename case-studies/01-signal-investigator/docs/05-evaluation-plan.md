# Evaluation plan

## Stage 1 quality gates
1. **Detection recall on known injected incidents:** target 3 / 3 labelled incidents (two conversion-rate, one sessions incident).
2. **Quiet-period false alerts:** zero alerts on a constant healthy synthetic series.
3. **Evidence traceability:** 100% of alerts include dates, observed values and baseline comparisons.
4. **Causal discipline:** reports say "checks" / "hypotheses," never confirmed cause.

These simple tests are **not enough** to claim production-ready anomaly detection. A realistic benchmark needs more patterns (holidays, weekday shifts, consent changes, channel mix, missing data, bot traffic, seasonality, returning visitors) and precision/recall evaluation.

## Future LLM quality gates
- Numeric faithfulness: amounts reported by the agent agree with read-only tool results.
- Tool correctness: agent chooses the right time grain, channel and metric.
- Abstention: agent distinguishes missing data from zero performance.
- Grounding: cited metric observations and uncertainty in every investigation.
- Actionability: subject-matter reviewer rates suggested follow-up checks.
- Cost, latency and reliability logged for repeatable scenarios.
