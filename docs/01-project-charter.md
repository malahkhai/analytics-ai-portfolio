# Project charter · AI Analytics Investigation Agent

**Working name:** Signal Investigator
**Project owner:** Analytics & AI portfolio case study
**Status:** Stage 1 · reproducible analytical baseline, not yet an AI agent
**Intended interview narrative:** Demonstrate the bridge between analytics leadership, sound data engineering and reliable agentic AI.

## Business problem
Digital teams spend too much time identifying what changed and collecting evidence across analytics systems before deciding what to investigate. A defensible AI agent should accelerate the investigation **without inventing causes or misrepresenting metrics**.

## First user story
> As an ecommerce analytics manager, I want an automated alert when a channel's conversion rate falls materially below historical behaviour, with numeric evidence and practical next checks, so I can prioritise investigation.

## MVP definition of done
- Historical data can be loaded and checked for valid metrics.
- Baselines use four prior matching weekdays for each channel.
- Deliberately injected conversion-rate and traffic incidents are detected.
- Every alert includes evidence, baseline dates, proposed checks and an uncertainty label.
- Basic unit tests pass.
- The work is documented and reproducible by another analyst.

## Scope boundaries
**In scope for Stage 1:** deterministic detection over synthetic daily ecommerce data; CSV in, JSON out; tests and documentation.
**Out of scope for Stage 1:** real-time operations, attribution, automatic causal diagnosis, LLM, UI, deployment and Fivetran integration. These are future stages.

## Key questions the eventual agent should answer
1. Which KPIs deviated, and by how much?
2. Which channels/dates/segments explain most of the movement?
3. How reliable is the data, and what alternative explanations exist?
4. What checks or actions should the analytics team take next?

## Risks and mitigations
- **False positives:** compare equivalent weekdays and set minimum volume thresholds; later evaluate seasonality and multiple-testing behaviour.
- **Misleading claims:** call the result an anomaly, not a root cause; every hypothesis requires independent validation.
- **GA4 data mismatch:** document difference between UI sessions, BigQuery `session_start` events and transaction source of truth.
- **Reproducibility:** fixed random seed, documented sample incidents and runnable tests.
- **Privacy:** use only synthetic/public data; never commit real customer data, OAuth tokens, or API keys.
