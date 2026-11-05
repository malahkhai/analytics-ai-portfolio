-- READ ONLY: inspect ecommerce revenue in one day of the historical public GA4 sample.
-- Validate query bytes and potential charges in BigQuery before running.
-- The *existing* Signal Investigator executive reporting table has NO revenue column.
-- The raw GA4 schema may have this field, but obfuscated values can be NULL/inconsistent.
-- Do not publish revenue KPIs unless the source is populated and reconciled.
SELECT
  COUNT(*) AS purchase_event_count,
  COUNTIF(ecommerce.purchase_revenue_in_usd IS NOT NULL) AS purchase_events_with_revenue_usd,
  ROUND(SUM(ecommerce.purchase_revenue_in_usd), 2) AS summed_purchase_revenue_usd,
  COUNT(DISTINCT NULLIF(ecommerce.transaction_id, '')) AS distinct_nonempty_transaction_ids
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20201207`
WHERE event_name = 'purchase';
