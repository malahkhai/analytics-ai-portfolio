
-- Signal Investigator: Purchase Rate Accuracy
--
-- Fails when:
-- 1. Total sessions are zero or negative
-- 2. The purchase rate is outside 0-100%
-- 3. The reported purchase rate differs
--    from the rate calculated from session counts

WITH rate_checks AS (

    SELECT
        event_day,
        sessions,
        purchasing_sessions,
        session_purchase_rate_pct,

        ROUND(
            SAFE_DIVIDE(
                purchasing_sessions,
                sessions
            ) * 100,
            2
        ) AS expected_purchase_rate_pct

    FROM {{ ref('fct_daily_ecommerce') }}

)

SELECT *
FROM rate_checks

WHERE
    sessions <= 0

    OR session_purchase_rate_pct < 0

    OR session_purchase_rate_pct > 100

    OR session_purchase_rate_pct
       IS DISTINCT FROM expected_purchase_rate_pct
