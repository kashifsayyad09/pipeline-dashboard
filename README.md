# ⚡ GitHub Actions Analytics Dashboard

Enterprise-grade CI/CD observability platform built with Python + Streamlit.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your token
cp .env.example .env
# Edit .env and set GITHUB_TOKEN=ghp_...

# 3. Run
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Token Scopes Required

| Scope | Purpose |
|-------|---------|
| `repo` | Read repository data, workflows, runs, artifacts |
| `workflow` | List and inspect workflow runs |
| `read:org` | Read organization and org-level runners |
| `read:user` | Show authenticated user info |

Create a token at: https://github.com/settings/tokens

## GitHub Enterprise

Set `GITHUB_API_URL=https://github.yourcompany.com/api/v3` in your `.env`
or enter it in the sidebar when connecting.

## Features

| Page | What it shows |
|------|--------------|
| 🏠 Dashboard | KPI cards, run trend, success rate gauge, failure breakdown |
| 📁 Repositories | All repos with stars, forks, language, visibility |
| ⚙️ Workflows | Active workflows with state and path |
| 🚀 Workflow Runs | Filterable run table with status pills |
| 📋 Jobs | Step-by-step job breakdown for the latest run |
| 📊 Analytics | Daily runs, runtime distribution, actor leaderboard |
| 📈 Performance | Avg / median / P95 / fastest / slowest durations |
| 🖥️ Self-Hosted Runners | Runner status, labels, busy/idle |
| ☁️ GitHub Runners | Hosted runner status |
| 📦 Artifacts | Artifact list with sizes and expiry |
| 📂 Cache | Workflow cache entries and sizes |
| 🔐 Security | Secrets metadata and variables |
| 📄 Reports | Export runs to CSV / JSON / Excel |
| 📡 API Monitor | Rate limit gauge and reset time |
| ⚙️ Settings | Account info and connection details |

## Architecture

```
app.py
├── GitHubClient        — REST + GraphQL API wrapper with pagination
├── Cached fetchers     — @st.cache_data (5-min TTL) per data type
├── Chart builders      — Plotly figures with unified dark theme
├── UI components       — kpi_card(), section_header(), render_runs_table()
└── Page renderers      — One function per sidebar page
```

All logic lives in a single `app.py` for easy deployment.
Split into modules by extracting `GitHubClient → github_client.py`,
chart builders → `charts.py`, and page functions → `pages/`.
