from __future__ import annotations
import csv, io, os, sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, render_template, request, Response

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('FINOPS_DB_PATH', BASE_DIR / 'finops.db'))
app = Flask(__name__, template_folder='templates', static_folder='static')

SERVICES = [
    ('Compute Engine', 'Compute', 0.42, 4.5),
    ('Object Storage', 'Storage', 0.08, 3.8),
    ('Managed Database', 'Database', 0.31, 4.4),
    ('Network Egress', 'Network', 0.16, 3.2),
    ('Monitoring', 'Monitoring', 0.03, 3.5),
]

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS usage_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usage_date TEXT NOT NULL, service TEXT NOT NULL, category TEXT NOT NULL,
            usage_units REAL NOT NULL, estimated_cost REAL NOT NULL,
            free_limit REAL NOT NULL, provider TEXT NOT NULL DEFAULT 'Demo Cloud',
            UNIQUE(usage_date, service, provider))''')
        con.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
        con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES ('monthly_budget','100.00')")
        count = con.execute('SELECT COUNT(*) FROM usage_daily').fetchone()[0]
        if count == 0:
            today = date.today()
            for day_offset in range(29, -1, -1):
                d = today - timedelta(days=day_offset)
                for idx, (service, category, rate, limit) in enumerate(SERVICES):
                    # Deterministic but varied demo data; explicitly labelled as simulated.
                    usage = max(0.5, (2.0 + ((day_offset * 7 + idx * 11) % 17) / 5) * (1 + idx * .12))
                    if service == 'Compute Engine' and day_offset < 5: usage *= 1.5
                    cost = round(usage * rate, 2)
                    con.execute('''INSERT OR IGNORE INTO usage_daily
                        (usage_date,service,category,usage_units,estimated_cost,free_limit,provider)
                        VALUES (?,?,?,?,?,?,?)''', (d.isoformat(), service, category, round(usage, 2), cost, limit, 'Demo Cloud'))

def get_budget():
    with connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key='monthly_budget'").fetchone()
    return float(row['value']) if row else 100.0

def query_rows(where='1=1', args=()):
    with connect() as con:
        return [dict(r) for r in con.execute(f'SELECT * FROM usage_daily WHERE {where} ORDER BY usage_date', args).fetchall()]

def risk_for(row):
    # A configurable educational heuristic, not a provider guarantee.
    ratio = row['usage_units'] / row['free_limit'] if row['free_limit'] else 0
    if ratio >= 0.90: return 'High'
    if ratio >= 0.70: return 'Watch'
    return 'Low'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard')
def dashboard():
    today = date.today()
    start = today.replace(day=1).isoformat()
    rows = query_rows('usage_date >= ?', (start,))
    all_rows = query_rows()
    total = round(sum(r['estimated_cost'] for r in rows), 2)
    budget = get_budget()
    daily = {}
    by_service = {}
    latest_by_service = {}
    for r in rows:
        daily[r['usage_date']] = round(daily.get(r['usage_date'], 0) + r['estimated_cost'], 2)
        by_service[r['service']] = round(by_service.get(r['service'], 0) + r['estimated_cost'], 2)
        latest_by_service[r['service']] = r
    risks = []
    for service, row in latest_by_service.items():
        level = risk_for(row)
        if level != 'Low':
            risks.append({**row, 'risk': level, 'usage_percent': round(row['usage_units'] / row['free_limit'] * 100, 1)})
    last_7 = [r for r in all_rows if r['usage_date'] >= (today - timedelta(days=6)).isoformat()]
    previous_7 = [r for r in all_rows if (today - timedelta(days=13)).isoformat() <= r['usage_date'] < (today - timedelta(days=6)).isoformat()]
    cur7 = sum(r['estimated_cost'] for r in last_7); prev7 = sum(r['estimated_cost'] for r in previous_7)
    trend = round(((cur7 - prev7) / prev7) * 100, 1) if prev7 else 0
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - today.replace(day=1)).days
    forecast = round(total / max(today.day, 1) * days_in_month, 2)
    return jsonify({
        'mode': 'SIMULATED DEMO DATA', 'today': today.isoformat(), 'month_spend': total,
        'budget': budget, 'budget_percent': round(total / budget * 100, 1) if budget else 0,
        'forecast': forecast, 'trend_percent': trend,
        'daily_labels': list(daily.keys()), 'daily_values': list(daily.values()),
        'service_labels': list(by_service.keys()), 'service_values': list(by_service.values()),
        'risks': sorted(risks, key=lambda x: x['usage_units']/x['free_limit'], reverse=True),
        'records': len(rows), 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/usage')
def usage():
    rows = query_rows()
    for r in rows:
        r['risk'] = risk_for(r)
        r['usage_percent'] = round(r['usage_units'] / r['free_limit'] * 100, 1) if r['free_limit'] else 0
    return jsonify(rows)

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        try: budget = float(data.get('monthly_budget', 100))
        except (ValueError, TypeError): return jsonify({'error':'Budget must be a number.'}), 400
        if budget <= 0 or budget > 100000000: return jsonify({'error':'Budget must be greater than zero and reasonable.'}), 400
        with connect() as con:
            con.execute("INSERT INTO settings(key,value) VALUES('monthly_budget',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(budget),))
        return jsonify({'monthly_budget': budget})
    return jsonify({'monthly_budget': get_budget()})

@app.route('/report/weekly.csv')
def weekly_report():
    cutoff = (date.today() - timedelta(days=6)).isoformat()
    rows = query_rows('usage_date >= ?', (cutoff,))
    out = io.StringIO(); writer = csv.writer(out)
    writer.writerow(['Date','Provider','Service','Category','Usage units (demo)','Estimated cost (USD)','Configured free-limit units','Risk'])
    for r in rows: writer.writerow([r['usage_date'],r['provider'],r['service'],r['category'],r['usage_units'],r['estimated_cost'],r['free_limit'],risk_for(r)])
    return Response(out.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=finops-weekly-usage.csv'})

@app.route('/metrics')
def metrics():
    data = dashboard().get_json()
    lines = [
        '# HELP finops_month_to_date_cost_usd Simulated month-to-date cost in USD.',
        '# TYPE finops_month_to_date_cost_usd gauge', f"finops_month_to_date_cost_usd {data['month_spend']}",
        '# HELP finops_monthly_budget_usd Configured monthly budget in USD.',
        '# TYPE finops_monthly_budget_usd gauge', f"finops_monthly_budget_usd {data['budget']}",
        '# HELP finops_budget_utilization_percent Month-to-date budget utilization percent.',
        '# TYPE finops_budget_utilization_percent gauge', f"finops_budget_utilization_percent {data['budget_percent']}",
        '# HELP finops_risk_services Number of services currently flagged Watch or High.',
        '# TYPE finops_risk_services gauge', f"finops_risk_services {len(data['risks'])}",
    ]
    return Response('\n'.join(lines)+'\n', mimetype='text/plain; version=0.0.4; charset=utf-8')

@app.route('/health')
def health(): return jsonify({'status':'ok','database':str(DB_PATH.name),'mode':'demo'})

init_db()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_DEBUG','0') == '1')
