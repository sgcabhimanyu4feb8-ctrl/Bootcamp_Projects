import re

def update_app_py():
    with open('c:/hack/app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()

    # 1. Update the CTE 'latest' across all queries
    old_cte = r"WITH latest AS \(\s*SELECT MAX\(order_date\) AS today\s*FROM\s*orders_parsed WHERE order_date IS NOT NULL\s*\)"
    new_cte = """WITH latest AS (
    SELECT COALESCE(
        MAX(order_date),
        (%(target_month)s || '-01')::date + INTERVAL '1 month' - INTERVAL '1 day'
    )::date AS today
    FROM   orders_parsed 
    WHERE  order_date IS NOT NULL
      AND  (%(target_month)s::text IS NULL OR TO_CHAR(order_date, 'YYYY-MM') = %(target_month)s)
)"""
    app_content = re.sub(old_cte, new_cte, app_content)

    # 2. Update routes to take 'month' param
    app_content = app_content.replace('from flask import Flask, jsonify, render_template', 'from flask import Flask, jsonify, render_template, request')

    routes_old = """@app.route("/api/summary")
def api_summary():
    rows = run_query(_SUMMARY_SQL)
    return json_response(rows[0] if rows else {})


@app.route("/api/leaderboard")
def api_leaderboard():
    return json_response(run_query(_LEADERBOARD_SQL))


@app.route("/api/destinations")
def api_destinations():
    return json_response(run_query(_DESTINATIONS_SQL))


@app.route("/api/charts")
def api_charts():
    daily   = run_query(_DAILY_CHART_SQL)
    monthly = run_query(_MONTHLY_CHART_SQL)
    return json_response({"daily": daily, "monthly": monthly})"""

    routes_new = """@app.route("/api/summary")
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

    app_content = app_content.replace(routes_old, routes_new)

    with open('c:/hack/app.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("Updated app.py")

def update_index_html():
    with open('c:/hack/templates/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add month selector CSS
    css_old = ".nav-date {\n      font-size: 13px;\n      color: var(--text-2);\n      font-weight: 500;\n    }"
    css_new = """.nav-date {
      font-size: 13px;
      color: var(--text-2);
      font-weight: 500;
    }
    .nav-month-selector {
      padding: 6px 12px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 13px;
      color: var(--text-1);
      background: var(--white);
      outline: none;
    }"""
    html = html.replace(css_old, css_new)

    # 2. Replace nav center
    nav_old = """  <div class="nav-center">
    <span class="nav-date" id="nav-date">—</span>
    <nav class="nav-tabs">
      <button class="nav-tab active" id="tab-dashboard">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
        Dashboard
      </button>
      <button class="nav-tab">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>
        </svg>
        Wallet Summary
      </button>
      <button class="nav-tab">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Download CSV
      </button>
    </nav>
  </div>"""

    nav_new = """  <div class="nav-center">
    <span class="nav-date" id="nav-date">—</span>
    <input type="month" id="month-selector" class="nav-month-selector" />
    <nav class="nav-tabs">
      <button class="nav-tab active" id="tab-dashboard">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
        Dashboard
      </button>
    </nav>
  </div>"""
    html = html.replace(nav_old, nav_new)

    # 3. Replace JS loadDashboard
    js_old = """async function loadDashboard() {
  try {
    const [summary, leaderboard, destinations, charts] = await Promise.all([
      fetch('/api/summary').then(r => r.json()),
      fetch('/api/leaderboard').then(r => r.json()),
      fetch('/api/destinations').then(r => r.json()),
      fetch('/api/charts').then(r => r.json()),
    ]);"""

    js_new = """async function loadDashboard() {
  const m = document.getElementById('month-selector').value;
  const qs = m ? `?month=${m}` : '';
  try {
    const [summary, leaderboard, destinations, charts] = await Promise.all([
      fetch('/api/summary' + qs).then(r => r.json()),
      fetch('/api/leaderboard' + qs).then(r => r.json()),
      fetch('/api/destinations' + qs).then(r => r.json()),
      fetch('/api/charts' + qs).then(r => r.json()),
    ]);"""
    html = html.replace(js_old, js_new)

    js_init_old = "document.addEventListener('DOMContentLoaded', loadDashboard);"
    js_init_new = """document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  document.getElementById('month-selector').addEventListener('change', loadDashboard);
});"""
    html = html.replace(js_init_old, js_init_new)

    with open('c:/hack/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated index.html")

if __name__ == "__main__":
    update_app_py()
    update_index_html()
