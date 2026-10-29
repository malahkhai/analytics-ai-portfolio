-- Phase 2 exploration: public GA4 obfuscated ecommerce sample dataset.
-- Historical period: 2020-11-01 through 2021-01-31, NOT current analytics data.
-- Execute in Google BigQuery; requires a Google Cloud project with BigQuery enabled.
-- Note: sample data has placeholders / inconsistencies; validate metric behaviour.
-- This query is global daily, not channel/session-attributed.
SELECT
  PARSE_DATE('%Y%m%d', event_date) AS event_day,
  COUNTIF(event_name = 'session_start') AS session_start_events,
  COUNTIF(event_name = 'purchase') AS purchase_events,
  ROUND(SUM(IF(event_name = 'purchase', COALESCE(ecommerce.purchase_revenue, 0), 0)), 2) AS purchase_revenue
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_day
ORDER BY event_day;
