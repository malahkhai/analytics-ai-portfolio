
# Investigation 001 — Paid Search Conversion Drop

## 1. Business Problem

On October 13, 2026, paid search experienced a
significant decline in ecommerce conversion rate.

The objective was to identify where performance
deteriorated and determine which hypotheses
deserved further investigation.

## 2. Initial Anomaly

Channel: Paid Search
Date: 2026-10-13

- Sessions: 1,266
- Orders: 25
- Observed conversion rate: 1.97%
- Historical conversion rate: 5.01%
- Relative change: -60.6%

The baseline was calculated using the previous
four matching Tuesdays.

## 3. Initial Hypotheses

H1: Checkout or payment processing issue.
H2: Purchase-event tracking failure.
H3: Lower-quality paid search traffic.
H4: Product availability problems.

These were hypotheses, not established causes.

## 4. Investigation Methodology

A Python-based investigation engine was developed
to compare funnel-stage performance against a
historical baseline.

The analysis included:

1. Product view rate
2. Add-to-cart progression
3. Checkout progression
4. Payment-attempt progression
5. Order completion relative to payment attempts
6. Sessions affected by payment failures

Historical rates were calculated using aggregated
numerators and denominators.

## 5. Key Findings

### Finding 1: Early funnel performance was stable

Product views, add-to-cart activity and checkout
progression showed relatively small changes
against the historical baseline.

### Finding 2: Payment-stage performance deteriorated

Historical orders per payment-attempt session:
77.99%

October 13 orders per payment-attempt session:
30.12%

Change: -47.87 percentage points.

This was the largest decline across the analysed
funnel stages.

### Finding 3: Failed-payment share increased

Historical affected-session share: 3.46%
October 13 affected-session share: 59.04%

The incident showed a substantial increase in
sessions experiencing payment failures.

## 6. Analytical Conclusion

The evidence supports prioritising a payment
processing or checkout-related investigation.

However, the root cause remains unverified.

Additional payment-provider logs, error codes
and backend order records would be required
to confirm the explanation.

Other hypotheses have not been fully excluded.

## 7. Recommended Actions

1. Investigate payment-provider error logs.
2. Check payment failures by payment method.
3. Review recent checkout deployments.
4. Compare GA4 orders against backend records.
5. Validate tracking implementation.
6. Review campaign and audience quality.

## 8. Limitations

- All data is synthetic and created for training.
- Payment failures are measured as affected sessions.
- Order counts are treated as session conversions
  under the simplified dataset assumptions.
- The dataset lacks transaction-level evidence.
- The investigation cannot establish causality.
- The simulated failure spike was deliberately
  introduced for this exercise.

## 9. Technical Components

Data:
data/daily_paid_search_funnel.csv

Anomaly detection:
src/detect.py

Investigation planning:
src/plan_investigation.py

Funnel investigation:
src/investigate_funnel.py

Generated evidence:
outputs/funnel_investigation.md

## 10. Next Development Stage

- Add automated validation tests.
- Extend funnel data to more channels and dates.
- Introduce dbt models for trusted metrics.
- Add AI-assisted investigation workflows.

## Project Status

Rule-based investigation prototype completed.
AI agent integration not yet implemented.
