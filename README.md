# FinOps Dashboard for Cloud Cost Visibility

A beginner-friendly portfolio project that demonstrates cloud-cost visibility, usage thresholds, reporting, and monitoring. It starts with simulated data so it can be run locally without cloud credentials.

> **Data safety / accuracy:** The default dashboard uses generated demo records and labels them as simulated. Its free-tier thresholds and dollar values are examples, not actual AWS/GCP free-tier limits or invoices. A real billing integration must use your provider's billing export/API, verified pricing/quotas, and appropriately scoped read-only credentials. Budget alerts in this project do not stop resources or guarantee that no bill will occur.

## Features

- Responsive FinOps dashboard with spend cards, daily line chart, service donut chart, risk list, budget progress, and recent records.
- Flask REST endpoints backed by SQLite.
- Configurable monthly budget and a weekly CSV report.
- Simple rule engine: **Watch** at 70% and **High** at 90% of each configured usage threshold.
- Prometheus `/metrics` endpoint, `/health` check, optional Grafana + Prometheus stack using Docker Compose.
- Unit tests for the API, budget validation, CSV report, and metrics endpoint.
- Demo mode works without AWS/GCP credentials.

## Technology stack (plain language)

| Technology | What it does here |
|---|---|
| Python | Main language for business logic and risk rules |
| Flask | Serves the website and JSON APIs |
| SQLite | Stores daily service usage and the budget on your computer |
| HTML/CSS/JavaScript | Builds the user interface and interactions |
| Chart.js | Draws spending and service charts |
| Prometheus | Scrapes application metrics from `/metrics` |
| Grafana | Optional dashboard for Prometheus metrics |
| Docker / Docker Compose | Packages and starts the app and optional monitoring services |
| pytest | Runs automated tests |
| Git + GitHub | Version control and portfolio publishing |

## 1. Install the software on Windows

### Required for the simplest run

1. Install **Python 3.11 or 3.12** from <https://www.python.org/downloads/windows/>. During setup, tick **Add python.exe to PATH**.
2. Install **Visual Studio Code** from <https://code.visualstudio.com/>.
3. Install **Git for Windows** from <https://git-scm.com/download/win>.
4. Extract this ZIP to a simple path, e.g. `C:\Projects\finops-cloud-cost-dashboard`.

You do **not** need AWS, GCP, Grafana, or Docker installed to run the basic dashboard. The charts use Chart.js and Google Fonts from CDNs, so internet access improves the appearance; the backend itself is local.

### Check installations

Open VS Code → **File → Open Folder** → choose the extracted `finops-cloud-cost-dashboard` folder. Then choose **Terminal → New Terminal** and run:

```powershell
python --version
python -m pip --version
git --version
```

If `python` is not found, close and reopen VS Code after installing Python, or try `py --version`.

## 2. Run the dashboard (recommended first run)

In the VS Code terminal, make sure you are in the project root (the folder containing `app.py`). Run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, you can skip activation and use the environment's Python directly:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

When Flask starts, open **<http://127.0.0.1:5000>** in Chrome. Keep the terminal running while using the site. Press **Ctrl+C** in that terminal to stop the server.

On first run, `finops.db` is created automatically and filled with simulated 30-day sample data. The database is ignored by Git so your local generated data is not committed.

## 3. Explore the project

- `app.py` — routes, SQLite schema, demo data generation, API, risk rules, CSV export, Prometheus metrics.
- `templates/index.html` — dashboard structure.
- `static/style.css` — responsive design and theme.
- `static/app.js` — API calls, charts, risk table, budget edit, report download.
- `tests/test_app.py` — basic automated tests.
- `prometheus/prometheus.yml` — tells Prometheus to scrape the Flask app.
- `grafana/provisioning/` and `grafana/dashboards/` — Grafana datasource and dashboard configuration.
- `Dockerfile`, `docker-compose.yml` — optional container setup.
- `.env.example` — optional environment variable examples; no secrets belong in Git.

## 4. How the project works

1. On startup, Python creates the SQLite tables if they do not exist and seeds example records only when the usage table is empty.
2. The browser opens `/` and loads the HTML, CSS, and JavaScript.
3. JavaScript calls `/api/dashboard` and `/api/usage`.
4. Flask reads usage records from SQLite and totals the current month's estimated costs.
5. The rule engine compares the latest usage for each service with its configured threshold. It marks usage at 70% as **Watch** and 90% as **High**.
6. The dashboard visualizes those values and lets you edit a monthly budget.
7. `/report/weekly.csv` creates a downloadable CSV report; `/metrics` exposes basic metrics for Prometheus.

**Risk-rule detail:** The demo checks the latest available daily usage record for each service against the illustrative limit. It is a learning example, not a complete cloud billing or quota engine. Real usage must account for each provider's exact quota period, region, SKU, pricing, credits, taxes, and billing delays.

## 5. API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Dashboard page |
| `GET /health` | Simple health check |
| `GET /api/dashboard` | KPI and chart data |
| `GET /api/usage` | Usage records with risk labels |
| `GET /api/settings` | Current budget setting |
| `POST /api/settings` | Update budget, JSON body such as `{"monthly_budget":150}` |
| `GET /report/weekly.csv` | Download weekly CSV |
| `GET /metrics` | Prometheus text metrics |

Try these in your browser while the app runs: <http://127.0.0.1:5000/health>, <http://127.0.0.1:5000/api/dashboard>, and <http://127.0.0.1:5000/metrics>.

## 6. Run tests

With the virtual environment active:

```powershell
pytest -q
```

Expected result: all included tests pass. Tests use a temporary database so they do not overwrite your normal demo database.

## 7. Optional: run with Docker, Prometheus and Grafana

Install Docker Desktop from <https://www.docker.com/products/docker-desktop/> and start it. In the project root:

```powershell
docker compose up --build -d
```

Open:

- App: <http://localhost:5000>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> (demo credentials: username `admin`, password `changeme-now`)

Change the Grafana password before using it beyond a local demo. Do not expose these demo credentials to the internet.

To inspect services/logs:

```powershell
docker compose ps
docker compose logs -f app
docker compose logs -f prometheus
docker compose logs -f grafana
```

To stop containers without deleting stored data:

```powershell
docker compose down
```

To stop and delete the named demo data volumes too (destructive):

```powershell
docker compose down -v
```

### If Docker cannot download images / OAuth token error

This is usually a Docker Hub/network/DNS/proxy/TLS problem, not a Python dashboard bug. First run the non-Docker steps above. For the optional stack, restart Docker Desktop, check internet/VPN/proxy and system date/time, then test:

```powershell
docker pull python:3.12-slim
docker pull prom/prometheus:v3.5.0
docker pull grafana/grafana:11.6.0
```

If a pull fails, fix Docker Hub connectivity before retrying Compose. You can still use the Flask dashboard locally without Prometheus or Grafana.

### If port 5000 or 3000 is already in use

Close the other app using that port, or change the left side of a Compose port mapping. For example, use `5001:5000` for the Flask app and then open `http://localhost:5001`. If changing the Grafana host port, use `3001:3000` and open `http://localhost:3001`.

## 8. AWS / GCP integration: next development stage

This starter intentionally runs in demo mode; it does **not** claim to fetch live AWS or GCP billing data yet. A safe real integration should be added only after confirming the target provider and the correct billing source:

- **AWS:** AWS Cost Explorer is accessed through the AWS SDK/API and usually requires billing permissions plus an enabled/eligible Cost Explorer setup. Use a dedicated least-privilege IAM identity, never root credentials, and keep credentials out of source control.
- **GCP:** Cloud Billing reports and costs are commonly exported to BigQuery for analysis. Set up a billing export, grant a service account only the required read permissions, then query the export using the BigQuery client. Billing exports may be delayed and are not the same as a real-time meter.
- Keep provider adapters separate from the dashboard and normalize records to `usage_date`, `service`, `category`, `usage_units`, `estimated_cost`, `free_limit`, and `provider`.
- Verify current provider quotas/pricing from official sources. Free-tier eligibility and limits can change and differ by account, region, service, and date.
- Add alert delivery only after the rule engine is tested; provider-native budget alerts are a useful independent safeguard.

No access keys, service-account JSON files, account IDs, or billing exports should be committed to GitHub. `.env` is ignored by Git; secrets should be stored in an appropriate secret manager for any deployed version.

## 9. Publish to GitHub

1. Create a repository at <https://github.com/new>, e.g. `finops-cloud-cost-dashboard`.
2. Choose Public only if you are comfortable sharing the code. Do not upload secrets, billing exports, the local database, or personal data.
3. In VS Code terminal, from the project root run:

```powershell
git init
git add .
git status
git commit -m "Build FinOps cloud cost visibility dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/finops-cloud-cost-dashboard.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username and use the repository URL GitHub gives you. If Git asks you to configure identity, run:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Then repeat the commit. GitHub may open a browser for authentication. Review `git status` before `git add .`; `.gitignore` excludes `.env`, virtual environments, and `finops.db`.

## 10. Add screenshots to the repository

1. Start the dashboard and open `http://127.0.0.1:5000`.
2. Press **Win + Shift + S** and capture the overview, risk monitor, and usage table.
3. Save images in a new `screenshots/` folder as `dashboard-overview.png`, `risk-monitor.png`, and `usage-report.png`.
4. Add the screenshots to the README under a `## Screenshots` heading, for example:

```markdown
![Dashboard overview](screenshots/dashboard-overview.png)
![Risk monitor](screenshots/risk-monitor.png)
![Usage records](screenshots/usage-report.png)
```

5. Publish the screenshots:

```powershell
git add README.md screenshots/
git commit -m "Add dashboard screenshots"
git push
```

Take real screenshots from your running app; do not represent demo values as live provider billing data.

## 11. LinkedIn project entry

**Project title:** FinOps Dashboard for Cloud Cost Visibility | Python, Flask, SQLite, Prometheus & Grafana

**Description:** Built a responsive FinOps dashboard to visualize cloud-cost estimates, service-level usage, budget utilization, and configurable free-tier risk thresholds. Developed a Python/Flask API backed by SQLite, added weekly CSV reporting and Prometheus metrics, and prepared an optional Grafana monitoring stack with Docker Compose. Used clearly labelled simulated data for local development and documented the path toward secure AWS/GCP billing integrations.

**Skills:** Python, Flask, SQLite, REST API, HTML, CSS, JavaScript, Chart.js, Docker, Docker Compose, Prometheus, Grafana, Git, GitHub, Cloud Cost Monitoring, FinOps.

**Add project link:** Paste your GitHub repository URL. Add screenshots or a short screen recording of the dashboard. Be transparent that the current data is simulated unless you have independently implemented and verified a live billing integration.

Suggested LinkedIn post:

> 🚀 I built a FinOps Dashboard for Cloud Cost Visibility as a hands-on cloud/DevOps learning project.
>
> The dashboard visualizes estimated spending, budget utilization, service breakdowns, and usage-threshold alerts. I used Python, Flask, SQLite, Chart.js, and prepared optional Prometheus + Grafana monitoring with Docker Compose.
>
> I also added a CSV report, API endpoints, health checks, and automated tests. The current version uses simulated data, with secure AWS/GCP billing integration as a future enhancement.
>
> GitHub: [paste your repository link]
>
> #FinOps #DevOps #Python #CloudComputing #AWS #GCP #Grafana #Prometheus #PortfolioProject

## 12. Interview explanation (simple words)

### 30-second version

“My project is a FinOps Dashboard for Cloud Cost Visibility. Its purpose is to help developers see estimated cloud spending and identify services that are approaching configured usage thresholds. I built the dashboard with Python and Flask, stored daily records in SQLite, used Chart.js for visualization, and exposed metrics for Prometheus and Grafana. The current version uses simulated data, so the next step is to connect it securely to AWS Cost Explorer or GCP Billing export.”

### How it works, in story form

“Imagine I start a small application in the cloud. A few virtual machines, storage buckets, and databases are running, and I want to understand whether my usage is growing. The Python application reads daily usage records from its database and calculates estimated spending. A small rule engine compares the latest usage with the example thresholds and marks services as Low, Watch, or High. The web dashboard makes this information easy to understand using charts and summary cards. I can set a monthly budget and download a weekly CSV report. Prometheus can collect the application's monitoring metrics, and Grafana can show those metrics separately. This helps me practise cost visibility before connecting a real cloud billing source.”

### Common interview questions

**Why did you build it?** To learn cloud cost visibility, usage monitoring, threshold-based alert logic, APIs, and observability in one practical project.

**Why SQLite?** It is simple, file-based, and good for a local prototype. A production multi-user system might use PostgreSQL or another managed database.

**Why Flask?** It is lightweight and makes it easy to expose routes and JSON endpoints in Python.

**What is FinOps?** A practice that brings engineering, finance, and business teams together to understand cloud spending and make informed cost decisions.

**What does Prometheus do?** It periodically scrapes numeric metrics from endpoints such as `/metrics` and stores time-series data.

**What does Grafana do?** It visualizes data from sources such as Prometheus in dashboards.

**Does this guarantee there will be no cloud bill?** No. It is a visibility and learning tool. The demo values are simulated, and even live billing APIs can be delayed. Provider-side budget alerts, quota controls, and safe resource management should be used as additional safeguards.

**What would you improve next?** Add an authenticated AWS Cost Explorer adapter or GCP BigQuery billing-export adapter, validate provider-specific free-tier rules, schedule ingestion, add email/Slack alerts, secure the app, and deploy it with monitoring and tests.

## 13. Troubleshooting

- **Dashboard won't open:** confirm the terminal still shows Flask running; use `http://127.0.0.1:5000`.
- **`ModuleNotFoundError: flask`:** activate `.venv` and run `pip install -r requirements.txt`.
- **Charts are blank:** check internet access for Chart.js CDN and inspect browser DevTools → Console.
- **Port already in use:** stop the other app or set `PORT=5001` before running Python.
- **Old sample data:** stop Flask, delete `finops.db`, and restart. This deletes local demo records and recreates them.
- **Grafana has no data:** check `docker compose ps`, visit Prometheus targets at `http://localhost:9090/targets`, and confirm the `finops-dashboard` target is UP.
- **Docker image pull error:** use the non-Docker Python run path first, then troubleshoot Docker Hub connectivity using the pull commands above.

## License

MIT — see `LICENSE`. This is an educational starter project, not a financial product or provider billing guarantee.
