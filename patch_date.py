import re

def update_app_py():
    with open('c:/hack/app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()

    # 1. Update the CTE 'latest' across all queries
    old_cte = r"""WITH latest AS \(
    SELECT COALESCE\(
        MAX\(order_date\),
        \(%\(target_month\)s \|\| '-01'\)::date \+ INTERVAL '1 month' - INTERVAL '1 day'
    \)::date AS today
    FROM   orders_parsed 
    WHERE  order_date IS NOT NULL
      AND  \(%\(target_month\)s::text IS NULL OR TO_CHAR\(order_date, 'YYYY-MM'\) = %\(target_month\)s\)
\)"""
    
    new_cte = """WITH latest AS (
    SELECT COALESCE(
        %(target_date)s::date,
        (SELECT MAX(order_date) FROM orders_parsed WHERE order_date IS NOT NULL)
    )::date AS today
)"""
    app_content = re.sub(old_cte, new_cte, app_content)

    # 2. Add 'AND order_date <= today' to mtd_s in _SUMMARY_SQL
    app_content = app_content.replace(
        "AND  EXTRACT(MONTH FROM order_date)=EXTRACT(MONTH FROM today)\n    GROUP BY today",
        "AND  EXTRACT(MONTH FROM order_date)=EXTRACT(MONTH FROM today)\n      AND  order_date <= today\n    GROUP BY today"
    )

    # 3. Add 'AND op.order_date <= latest.today' to mtd_stats in _LEADERBOARD_SQL
    app_content = app_content.replace(
        "AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today)\n    GROUP  BY op.created_by",
        "AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today)\n      AND  op.order_date <= latest.today\n    GROUP  BY op.created_by"
    )

    # 4. Add 'AND op.order_date <= latest.today' to monthly_orders in _DESTINATIONS_SQL
    app_content = app_content.replace(
        "AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today)\n)",
        "AND  EXTRACT(MONTH FROM op.order_date)=EXTRACT(MONTH FROM latest.today)\n      AND  op.order_date <= latest.today\n)"
    )

    # 5. Add 'AND op.order_date <= latest.today' to _DAILY_CHART_SQL and _MONTHLY_CHART_SQL
    app_content = app_content.replace(
        "WHERE  op.order_date >= latest.today - INTERVAL '60 days'\n  AND  op.order_date IS NOT NULL",
        "WHERE  op.order_date >= latest.today - INTERVAL '60 days'\n  AND  op.order_date IS NOT NULL\n  AND  op.order_date <= latest.today"
    )
    app_content = app_content.replace(
        "WHERE  op.order_date >= DATE_TRUNC('month', latest.today) - INTERVAL '11 months'\n  AND  op.order_date IS NOT NULL",
        "WHERE  op.order_date >= DATE_TRUNC('month', latest.today) - INTERVAL '11 months'\n  AND  op.order_date IS NOT NULL\n  AND  op.order_date <= latest.today"
    )

    # 6. Change 'month' to 'date' in routes
    routes_old = """@app.route("/api/summary")
def api_summary():
    month = request.args.get('month')
    rows = run_query(_SUMMARY_SQL, {'target_month': month})
    return json_response(rows[0] if rows else {})


@app.route("/api/leaderboard")
def api_leaderboard():
    month = request.args.get('month')
    return json_response(run_query(_LEADERBOARD_SQL, {'target_month': month}))


@app.route("/api/destinations")
def api_destinations():
    month = request.args.get('month')
    return json_response(run_query(_DESTINATIONS_SQL, {'target_month': month}))


@app.route("/api/charts")
def api_charts():
    month = request.args.get('month')
    daily   = run_query(_DAILY_CHART_SQL, {'target_month': month})
    monthly = run_query(_MONTHLY_CHART_SQL, {'target_month': month})
    return json_response({"daily": daily, "monthly": monthly})"""

    routes_new = """@app.route("/api/summary")
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
    return json_response({"daily": daily, "monthly": monthly})"""

    app_content = app_content.replace(routes_old, routes_new)

    with open('c:/hack/app.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("Updated app.py")


def update_index_html():
    with open('c:/hack/templates/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update <input type="month"> to <input type="date">
    html = html.replace(
        '<input type="month" id="month-selector" class="nav-month-selector" />',
        '<input type="date" id="date-selector" class="nav-month-selector" />'
    )

    # 2. Update loadDashboard JS
    js_old = """async function loadDashboard() {
  const m = document.getElementById('month-selector').value;
  const qs = m ? `?month=${m}` : '';
  try {
    const [summary, leaderboard, destinations, charts] = await Promise.all([
      fetch('/api/summary' + qs).then(r => r.json()),
      fetch('/api/leaderboard' + qs).then(r => r.json()),
      fetch('/api/destinations' + qs).then(r => r.json()),
      fetch('/api/charts' + qs).then(r => r.json()),
    ]);"""

    js_new = """async function loadDashboard() {
  const d = document.getElementById('date-selector').value;
  const qs = d ? `?date=${d}` : '';
  try {
    const [summary, leaderboard, destinations, charts] = await Promise.all([
      fetch('/api/summary' + qs).then(r => r.json()),
      fetch('/api/leaderboard' + qs).then(r => r.json()),
      fetch('/api/destinations' + qs).then(r => r.json()),
      fetch('/api/charts' + qs).then(r => r.json()),
    ]);"""
    html = html.replace(js_old, js_new)

    js_init_old = """document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  document.getElementById('month-selector').addEventListener('change', loadDashboard);
});"""
    js_init_new = """document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  document.getElementById('date-selector').addEventListener('change', loadDashboard);
});"""
    html = html.replace(js_init_old, js_init_new)

    with open('c:/hack/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated index.html")

if __name__ == "__main__":
    update_app_py()
    update_index_html()
