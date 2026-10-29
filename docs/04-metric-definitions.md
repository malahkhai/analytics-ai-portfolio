# Metric glossary and data contract

| Field | Type | Grain / definition |
| --- | --- | --- |
| `date` | ISO date | Reporting day (one record per date x channel). |
| `channel` | String | Simplified first-party channel label in synthetic data. Not GA4's default channel group. |
| `sessions` | Nonnegative integer | Simulated sessions. Not directly interchangeable with GA4 `session_start` counts. |
| `orders` | Integer | Simulated completed ecommerce orders, with 0 ≤ orders ≤ sessions for this simplified exercise. |
| `revenue_eur` | Nonnegative decimal | Simulated gross purchase revenue in EUR. |
| `conversion_rate` | Ratio | `orders / sessions` when `sessions > 0`. |
| `baseline_conversion_rate` | Ratio | Pooled orders / pooled sessions from four previous matching weekdays. |
| `expected_orders` | Estimate | Current sessions × baseline conversion rate. |
| `estimated_order_shortfall` | Estimate | Expected orders − observed orders; an estimate, NOT observed lost sales. |
| `estimated_revenue_gap_eur` | Estimate | Estimated order shortfall × historical weighted AOV; illustrative, not recoverable revenue. |

## Assumptions
Simple one-order-per-session model, no refunds or tax adjustments, fixed currency, no consent effects. Production GA4 requires additional considerations such as purchase event duplicates, event timestamp time zone, session attribution and currency normalisation.
