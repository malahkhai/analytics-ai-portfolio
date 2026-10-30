
-- Signal Investigator: Session Count Validation
--
-- This test identifies records where:
-- 1. Sessions are negative
-- 2. Purchasing sessions are negative
-- 3. Purchasing sessions exceed total sessions

SELECT
    event_day,
    sessions,
    purchasing_sessions

FROM {{ ref('fct_daily_ecommerce') }}

WHERE
    sessions < 0
    OR purchasing_sessions < 0
    OR purchasing_sessions > sessions
