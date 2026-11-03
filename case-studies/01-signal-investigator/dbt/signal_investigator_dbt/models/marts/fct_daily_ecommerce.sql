
-- Signal Investigator
-- Daily Ecommerce Performance Model
-- Source: Google GA4 public ecommerce dataset
-- Period: November 1 - December 7, 2020

{{ config(materialized='view') }}

WITH raw_events AS (

    SELECT
        PARSE_DATE('%Y%m%d', event_date) AS event_day,
        event_name,
        user_pseudo_id,

        (
            SELECT ep.value.int_value
            FROM UNNEST(event_params) AS ep
            WHERE ep.key = 'ga_session_id'
            LIMIT 1
        ) AS ga_session_id

    FROM
        `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

    WHERE
        _TABLE_SUFFIX BETWEEN '20201101' AND '20201207'

),

session_events AS (

    SELECT
        event_day,
        event_name,

        CASE
            WHEN user_pseudo_id IS NOT NULL
                 AND ga_session_id IS NOT NULL

            THEN CONCAT(
                user_pseudo_id,
                '.',
                CAST(ga_session_id AS STRING)
            )
        END AS session_key

    FROM raw_events

)

SELECT
    event_day,

    COUNT(DISTINCT session_key) AS sessions,

    COUNTIF(event_name = 'page_view')
        AS page_view_events,

    COUNTIF(event_name = 'view_item')
        AS view_item_events,

    COUNTIF(event_name = 'add_to_cart')
        AS add_to_cart_events,

    COUNTIF(event_name = 'begin_checkout')
        AS begin_checkout_events,

    COUNTIF(event_name = 'purchase')
        AS purchase_events,

    COUNT(DISTINCT IF(
        event_name = 'purchase',
        session_key,
        NULL
    )) AS purchasing_sessions,

    ROUND(
        SAFE_DIVIDE(
            COUNT(DISTINCT IF(
                event_name = 'purchase',
                session_key,
                NULL
            )),
            COUNT(DISTINCT session_key)
        ) * 100,
        2
    ) AS session_purchase_rate_pct

FROM session_events

GROUP BY event_day
