"""
Voyx Dashboard — Flask Backend
Connects to PostgreSQL, runs SQL queries, serves the dashboard UI.

Start: python app.py
Open:  http://localhost:5000
"""

from flask import Flask, jsonify, render_template, request, request, request, Response
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import json
from decimal import Decimal
import datetime

app = Flask(__name__)
CORS(app)

# ─── Database Configuration ────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "aws-1-ap-southeast-2.pooler.supabase.com",
    "port":     6543,
    "dbname":   "postgres",
    "user":     "postgres.slzxowwkgcksqcwnweut",
    "password": "Abhi@1234#56",
    "sslmode":  "require"
}

# ─── Helpers ───────────────────────────────────────────────────────────────────
class CustomEncoder(json.JSONEncoder):
    """Handles Decimal and date types returned by psycopg2."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


def run_query(sql: str, params=None) -> list:
    """Execute SQL and return list of dicts."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def json_response(data):
    return Response(
        json.dumps(data, cls=CustomEncoder),
        mimetype="application/json"
    )


# ─── SQL Definitions ───────────────────────────────────────────────────────────

_SUMMARY_SQL = """
WITH latest AS (
    SELECT COALESCE(
        %(target_date)s::date,
        (SELECT MAX(order_date) FROM orders_parsed WHERE order_date IS NOT NULL)
    )::date AS today
),
today_s AS (
    SELECT COUNT(*) AS orders, ROUND(SUM(amount)::numeric, 2) AS revenue
    FROM   orders_parsed CROSS JOIN latest
    WHERE  order_date = today
),
mtd_s AS (
    SELECT COUNT(*) AS orders, ROUND(SUM(amount)::numeric, 2) AS revenue,
           TO_CHAR(today, 'Mon YYYY') AS label
    FROM   orders_parsed CROSS JOIN latest
    WHERE  EXTRACT(YEAR  FROM order_date)=EXTRACT(YEAR  FROM today)
      AND  EXTRACT(MONTH FROM order_date)=EXTRACT(MONTH FROM today)
      AND  order_date <= today
    GROUP BY today
),
prev_same_s AS (
    SELECT COUNT(*) AS orders, ROUND(SUM(amount)::numeric, 2) AS revenue
    FROM   orders_parsed CROSS JOIN latest
    WHERE  EXTRACT(YEAR  FROM order_date)=EXTRACT(YEAR  FROM today - INTERVAL '1 month')
      AND  EXTRACT(MONTH FROM order_date)=EXTRACT(MONTH FROM today - INTERVAL '1 month')
      AND  EXTRACT(DAY   FROM order_date)<=EXTRACT(DAY FROM today)
),
prev_full_s AS (
    SELECT COUNT(*) AS orders, ROUND(SUM(amount)::numeric, 2) AS revenue,
           TO_CHAR(today - INTERVAL '1 month','Mon YYYY') AS label
    FROM   orders_parsed CROSS JOIN latest
    WHERE  EXTRACT(YEAR  FROM order_date)=EXTRACT(YEAR  FROM today - INTERVAL '1 month')
      AND  EXTRACT(MONTH FROM order_date)=EXTRACT(MONTH FROM today - INTERVAL '1 month')
    GROUP BY today
)
SELECT
    (SELECT today   FROM latest)               AS data_date,
    (SELECT orders  FROM today_s)              AS today_orders,
    (SELECT revenue FROM today_s)              AS today_revenue,
    (SELECT label   FROM mtd_s)                AS mtd_label,
    (SELECT orders  FROM mtd_s)                AS mtd_orders,
    (SELECT revenue FROM mtd_s)                AS mtd_revenue,
    (SELECT orders  FROM prev_same_s)          AS prev_same_orders,
    (SELECT revenue FROM prev_same_s)          AS prev_same_revenue,
    (SELECT label   FROM prev_full_s)          AS prev_full_label,
    (SELECT orders  FROM prev_full_s)          AS prev_full_orders,
    (SELECT revenue FROM prev_full_s)          AS prev_full_revenue;
"""

_LEADERBOARD_SQL = """
WITH latest AS (
    SELECT COALESCE(
        %(target_date)s::date,
        (SELECT MAX(order_date) FROM orders_parsed WHERE order_date IS NOT NULL)
    )::date AS today
),
sales_reps AS (
    SELECT user_id, TRIM(name) AS name FROM users WHERE user_role = 2
),
today_stats AS (
    SELECT op.created_by,
           COUNT(*)       AS day_orders,
           SUM(op.amount) AS day_revenue
    FROM   orders_parsed op CROSS JOIN latest
    WHERE  op.order_date = latest.today
    GROUP  BY op.created_by
),
mtd_stats AS (
    SELECT op.created_by,
           COUNT(*)       AS mtd_orders,
           SUM(op.amount) AS mtd_revenue
    FROM   orders_parsed op CROSS JOIN latest
    WHERE  EXTRACT(YEAR  FROM op.order_date)=EXTRACT(YEAR  FROM latest.today)
      AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today)
      AND  op.order_date <= latest.today
    GROUP  BY op.created_by
),
prev_stats AS (
    SELECT op.created_by, COUNT(*) AS prev_orders
    FROM   orders_parsed op CROSS JOIN latest
    WHERE  EXTRACT(YEAR  FROM op.order_date)=EXTRACT(YEAR  FROM latest.today - INTERVAL '1 month')
      AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today - INTERVAL '1 month')
    GROUP  BY op.created_by
)
SELECT
    ROW_NUMBER() OVER (ORDER BY COALESCE(m.mtd_orders,0) DESC)  AS rank,
    sr.name                                                      AS sales_rep,
    COALESCE(t.day_orders,  0)                                   AS day_orders,
    ROUND(COALESCE(t.day_revenue, 0)::numeric, 2)                         AS day_revenue,
    COALESCE(m.mtd_orders,  0)                                   AS mtd_orders,
    ROUND(COALESCE(m.mtd_revenue, 0)::numeric, 2)                         AS mtd_revenue,
    CASE WHEN COALESCE(m.mtd_orders,0)>0
         THEN ROUND((m.mtd_revenue / m.mtd_orders)::numeric, 2) ELSE 0
    END                                                          AS arpu,
    125                                                          AS target,
    ROUND(COALESCE(m.mtd_orders,0)*100.0/125, 0)               AS target_pct,
    COALESCE(p.prev_orders, 0)                                   AS prev_month_orders
FROM      sales_reps      sr
LEFT JOIN today_stats  t  ON sr.user_id = t.created_by
LEFT JOIN mtd_stats    m  ON sr.user_id = m.created_by
LEFT JOIN prev_stats   p  ON sr.user_id = p.created_by
WHERE COALESCE(m.mtd_orders,0) > 0
ORDER BY mtd_orders DESC;
"""

_DESTINATIONS_SQL = """
WITH latest AS (
    SELECT COALESCE(
        %(target_date)s::date,
        (SELECT MAX(order_date) FROM orders_parsed WHERE order_date IS NOT NULL)
    )::date AS today
),
monthly_orders AS (
    SELECT op.product_id
    FROM   orders_parsed op CROSS JOIN latest
    WHERE  EXTRACT(YEAR  FROM op.order_date)=EXTRACT(YEAR  FROM latest.today)
      AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today)
      AND  op.order_date <= latest.today
),
order_with_dest AS (
    SELECT TRIM(SPLIT_PART(p."coverageDestinations",',',1)) AS primary_dest
    FROM   monthly_orders mo
    JOIN   products p ON mo.product_id = p.prod_id
    WHERE  p."coverageDestinations" IS NOT NULL
      AND  p."coverageDestinations" <> ''
)
SELECT
    COALESCE(d.destination_name, owd.primary_dest) AS destination_name,
    COUNT(*)                                        AS order_count
FROM      order_with_dest owd
LEFT JOIN destinations d ON d.destination_id = owd.primary_dest
GROUP BY  COALESCE(d.destination_name, owd.primary_dest)
ORDER BY  order_count DESC
LIMIT  10;
"""

_DAILY_CHART_SQL = """
WITH latest AS (
    SELECT COALESCE(
        %(target_date)s::date,
        (SELECT MAX(order_date) FROM orders_parsed WHERE order_date IS NOT NULL)
    )::date AS today
)
SELECT
    op.order_date                        AS date,
    TO_CHAR(op.order_date,'DD/MM')       AS date_label,
    COUNT(op.order_no)                   AS daily_orders,
    ROUND(SUM(op.amount)::numeric, 2)             AS daily_revenue
FROM   orders_parsed op CROSS JOIN latest
WHERE  op.order_date >= latest.today - INTERVAL '60 days'
  AND  op.order_date IS NOT NULL
  AND  op.order_date <= latest.today
  AND  op.order_date <= latest.today
  AND  op.order_date <= latest.today
GROUP  BY op.order_date
ORDER  BY op.order_date;
"""

_MONTHLY_CHART_SQL = """
WITH latest AS (
    SELECT COALESCE(
        %(target_date)s::date,
        (SELECT MAX(order_date) FROM orders_parsed WHERE order_date IS NOT NULL)
    )::date AS today
)
SELECT
    TO_CHAR(DATE_TRUNC('month', op.order_date), 'Mon ''YY') AS month_label,
    DATE_TRUNC('month', op.order_date)                       AS month_start,
    COUNT(op.order_no)                                       AS monthly_orders,
    ROUND(SUM(op.amount)::numeric, 2)                                 AS monthly_revenue
FROM   orders_parsed op CROSS JOIN latest
WHERE  op.order_date >= DATE_TRUNC('month', latest.today) - INTERVAL '11 months'
  AND  op.order_date IS NOT NULL
  AND  op.order_date <= latest.today
  AND  op.order_date <= latest.today
  AND  op.order_date <= latest.today
GROUP  BY DATE_TRUNC('month', op.order_date)
ORDER  BY month_start;
"""

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    date = request.args.get('date')
    rows = run_query(_SUMMARY_SQL, {'target_date': date})
    return json_response(rows[0] if rows else {})


@app.route("/api/leaderboard")
def api_leaderboard():
    date = request.args.get('date')
    return json_response(run_query(_LEADERBOARD_SQL, {'target_date': date}))


@app.route("/api/destinations")
def api_destinations():
    date = request.args.get('date')
    return json_response(run_query(_DESTINATIONS_SQL, {'target_date': date}))


@app.route("/api/charts")
def api_charts():
    date = request.args.get('date')
    daily   = run_query(_DAILY_CHART_SQL, {'target_date': date})
    monthly = run_query(_MONTHLY_CHART_SQL, {'target_date': date})
    return json_response({"daily": daily, "monthly": monthly})


# ─── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Voyx Dashboard running at http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
