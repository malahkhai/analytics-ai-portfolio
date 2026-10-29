# Funnel Investigation — 2026-10-13

## Funnel performance

| Stage | Baseline | Incident | Change (pp) |
|---|---:|---:|---:|
| Product view / session | 74.70% | 74.49% | -0.21 |
| Add to cart / product view | 24.08% | 23.86% | -0.22 |
| Checkout / cart | 49.44% | 49.78% | +0.34 |
| Payment attempt / checkout | 72.27% | 74.11% | +1.83 |
| Orders / payment-attempt sessions | 77.99% | 30.12% | -47.87 |

## Biggest deterioration
**Orders / payment-attempt sessions**
- Historical: 77.99%
- Incident: 30.12%
- Change: -47.87 percentage points

## Payment failure cross-check
- Historical affected-session share: 3.46%
- Incident affected-session share: 59.04%

## Investigation conclusion
Payment-stage performance deteriorated sharply.
Elevated payment failures support the payment-issue hypothesis.
Root cause remains unverified. Payment logs, error codes and backend order data are needed.

## Limitations
Synthetic dataset. Stage metrics represent sessions, except orders. The demo assumes at most one order per session. Real funnel reporting should use consistent session-based or user-based metrics.
