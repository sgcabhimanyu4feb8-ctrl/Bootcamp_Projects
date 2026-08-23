-- ================================================================
-- VOYX DASHBOARD — ALL SQL QUERIES (POSTGRESQL)
-- Run each query individually or run as a script in DBeaver
-- Requires: setup_db.sql to have been run first (tables + view)
-- ================================================================


-- ----------------------------------------------------------------
-- Q1 | TODAY'S PERFORMANCE
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
)
SELECT
    latest.today                          AS data_date,
    COUNT(op.order_no)                    AS today_orders,
    ROUND(SUM(op.amount)::numeric, 2)     AS today_revenue
FROM   orders_parsed op
CROSS  JOIN latest
WHERE  op.order_date = latest.today
GROUP  BY latest.today;


-- ----------------------------------------------------------------
-- Q2 | CURRENT MONTH-TO-DATE (MTD)
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
)
SELECT
    TO_CHAR(latest.today, 'Mon YYYY')     AS month_label,
    COUNT(op.order_no)                    AS mtd_orders,
    ROUND(SUM(op.amount)::numeric, 2)     AS mtd_revenue
FROM   orders_parsed op
CROSS  JOIN latest
WHERE  EXTRACT(YEAR  FROM op.order_date) = EXTRACT(YEAR  FROM latest.today)
  AND  EXTRACT(MONTH FROM op.order_date) = EXTRACT(MONTH FROM latest.today)
GROUP  BY latest.today;


-- ----------------------------------------------------------------
-- Q3 | PREVIOUS MONTH — SAME DAY
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
)
SELECT
    COUNT(op.order_no)                    AS prev_same_day_orders,
    ROUND(SUM(op.amount)::numeric, 2)     AS prev_same_day_revenue
FROM   orders_parsed op
CROSS  JOIN latest
WHERE  EXTRACT(YEAR  FROM op.order_date) = EXTRACT(YEAR  FROM latest.today - INTERVAL '1 month')
  AND  EXTRACT(MONTH FROM op.order_date) = EXTRACT(MONTH FROM latest.today - INTERVAL '1 month')
  AND  EXTRACT(DAY   FROM op.order_date) <= EXTRACT(DAY FROM latest.today);


-- ----------------------------------------------------------------
-- Q4 | PREVIOUS FULL MONTH
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
)
SELECT
    TO_CHAR(latest.today - INTERVAL '1 month', 'Mon YYYY') AS month_label,
    COUNT(op.order_no)                                     AS prev_month_orders,
    ROUND(SUM(op.amount)::numeric, 2)                      AS prev_month_revenue
FROM   orders_parsed op
CROSS  JOIN latest
WHERE  EXTRACT(YEAR  FROM op.order_date) = EXTRACT(YEAR  FROM latest.today - INTERVAL '1 month')
  AND  EXTRACT(MONTH FROM op.order_date) = EXTRACT(MONTH FROM latest.today - INTERVAL '1 month')
GROUP  BY latest.today;


-- ----------------------------------------------------------------
-- Q5 | DAILY LEADERBOARD
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
),
sales_reps AS (
    SELECT user_id, TRIM(name) AS name
    FROM   users
    WHERE  user_role = 2
),
today_stats AS (
    SELECT
        op.created_by,
        COUNT(*)        AS day_orders,
        SUM(op.amount)  AS day_revenue
    FROM   orders_parsed op
    CROSS  JOIN latest
    WHERE  op.order_date = latest.today
    GROUP  BY op.created_by
),
mtd_stats AS (
    SELECT
        op.created_by,
        COUNT(*)        AS mtd_orders,
        SUM(op.amount)  AS mtd_revenue
    FROM   orders_parsed op
    CROSS  JOIN latest
    WHERE  EXTRACT(YEAR  FROM op.order_date) = EXTRACT(YEAR  FROM latest.today)
      AND  EXTRACT(MONTH FROM op.order_date) = EXTRACT(MONTH FROM latest.today)
    GROUP  BY op.created_by
),
prev_month_stats AS (
    SELECT
        op.created_by,
        COUNT(*) AS prev_orders
    FROM   orders_parsed op
    CROSS  JOIN latest
    WHERE  EXTRACT(YEAR  FROM op.order_date) = EXTRACT(YEAR  FROM latest.today - INTERVAL '1 month')
      AND  EXTRACT(MONTH FROM op.order_date) = EXTRACT(MONTH FROM latest.today - INTERVAL '1 month')
    GROUP  BY op.created_by
)
SELECT
    ROW_NUMBER() OVER (ORDER BY COALESCE(m.mtd_orders, 0) DESC)  AS rank,
    sr.name                                                      AS sales_rep,
    COALESCE(t.day_orders, 0)                                    AS day_orders,
    ROUND(COALESCE(t.day_revenue, 0)::numeric, 2)                AS day_revenue,
    COALESCE(m.mtd_orders, 0)                                    AS mtd_orders,
    ROUND(COALESCE(m.mtd_revenue, 0)::numeric, 2)                AS mtd_revenue,
    CASE
        WHEN COALESCE(m.mtd_orders, 0) > 0
        THEN ROUND((m.mtd_revenue / m.mtd_orders)::numeric, 2)
        ELSE 0
    END                                                          AS arpu,
    125                                                          AS target,
    ROUND((COALESCE(m.mtd_orders, 0) * 100.0 / 125)::numeric, 0) AS target_pct,
    COALESCE(p.prev_orders, 0)                                   AS prev_month_orders
FROM       sales_reps        sr
LEFT JOIN  today_stats       t ON sr.user_id = t.created_by
LEFT JOIN  mtd_stats         m ON sr.user_id = m.created_by
LEFT JOIN  prev_month_stats  p ON sr.user_id = p.created_by
WHERE  COALESCE(m.mtd_orders, 0) > 0
ORDER BY mtd_orders DESC;


-- ----------------------------------------------------------------
-- Q6 | TOP DESTINATIONS (current month)
-- ----------------------------------------------------------------
-- ----------------------------------------------------------------
-- Q6 | TOP DESTINATIONS (current month)
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
),
monthly_orders AS (
    SELECT op.product_id
    FROM   orders_parsed op
    CROSS  JOIN latest
    WHERE  EXTRACT(YEAR  FROM op.order_date) = EXTRACT(YEAR  FROM latest.today)
      AND  EXTRACT(MONTH FROM op.order_date) = EXTRACT(MONTH FROM latest.today)
),
order_with_dest AS (
    -- Fix: Added double quotes around "coverageDestinations"
    SELECT TRIM(SPLIT_PART(p."coverageDestinations", ',', 1)) AS primary_dest
    FROM   monthly_orders mo
    JOIN   products p ON mo.product_id = p.prod_id
    WHERE  p."coverageDestinations" IS NOT NULL
      AND  p."coverageDestinations" <> ''
)
SELECT
    COALESCE(d.destination_name, owd.primary_dest) AS destination_name,
    COUNT(*)                                       AS order_count
FROM       order_with_dest owd
LEFT JOIN  destinations d ON d.destination_id::text = owd.primary_dest
GROUP  BY  COALESCE(d.destination_name, owd.primary_dest)
ORDER  BY  order_count DESC;
LIMIT  10;


-- ----------------------------------------------------------------
-- Q7 | DAILY ORDER COUNT — for Daily Summary line chart
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
)
SELECT
    op.order_date                   AS date,
    TO_CHAR(op.order_date, 'DD/MM') AS date_label,
    COUNT(op.order_no)              AS daily_orders,
    ROUND(SUM(op.amount)::numeric, 2) AS daily_revenue
FROM   orders_parsed op
CROSS  JOIN latest
WHERE  op.order_date >= latest.today - INTERVAL '60 days'
  AND  op.order_date IS NOT NULL
GROUP  BY op.order_date
ORDER  BY op.order_date;


-- ----------------------------------------------------------------
-- Q8 | MONTHLY ORDER COUNT — for Monthly Summary line chart
-- ----------------------------------------------------------------
WITH latest AS (
    SELECT MAX(order_date) AS today
    FROM   orders_parsed
    WHERE  order_date IS NOT NULL
)
SELECT
    TO_CHAR(DATE_TRUNC('month', op.order_date), 'Mon ''YY') AS month_label,
    DATE_TRUNC('month', op.order_date)                      AS month_start,
    COUNT(op.order_no)                                      AS monthly_orders,
    ROUND(SUM(op.amount)::numeric, 2)                       AS monthly_revenue
FROM   orders_parsed op
CROSS  JOIN latest
WHERE  op.order_date >= DATE_TRUNC('month', latest.today) - INTERVAL '11 months'
  AND  op.order_date IS NOT NULL
GROUP  BY DATE_TRUNC('month', op.order_date)
ORDER  BY month_start;