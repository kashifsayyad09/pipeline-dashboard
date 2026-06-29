"""
GitHub Actions Analytics Dashboard
Enterprise-grade CI/CD observability platform
Built with Python + Streamlit + Plotly + GitHub REST & GraphQL APIs
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
import io

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG & CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

PAGE_TITLE = "GitHub Actions Analytics"
GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

COLORS = {
    "primary":    "#81CAD6",
    "secondary":  "#8A2BE2",
    "bg":         "#011A27",
    "card":       "#0B2435",
    "card2":      "#12344D",
    "text":       "#DFF6FF",
    "white":      "#FFFFFF",
    "success":    "#4ADE80",
    "warning":    "#FACC15",
    "danger":     "#EF4444",
    "muted":      "#6B7280",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": COLORS["text"], "family": "Inter, sans-serif"},
        "xaxis": {"gridcolor": "#12344D", "zerolinecolor": "#12344D"},
        "yaxis": {"gridcolor": "#12344D", "zerolinecolor": "#12344D"},
    }
}

PAGES = [
    ("🏠", "Dashboard"),
    ("📁", "Repositories"),
    ("⚙️", "Workflows"),
    ("🚀", "Workflow Runs"),
    ("📋", "Jobs"),
    ("📊", "Analytics"),
    ("📈", "Performance"),
    ("🖥️", "Self-Hosted Runners"),
    ("☁️", "GitHub Runners"),
    ("📦", "Artifacts"),
    ("📂", "Cache"),
    ("🔐", "Security"),
    ("📄", "Reports"),
    ("📡", "API Monitor"),
    ("⚙️ ", "Settings"),
]

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
        --primary:   {COLORS['primary']};
        --secondary: {COLORS['secondary']};
        --bg:        {COLORS['bg']};
        --card:      {COLORS['card']};
        --card2:     {COLORS['card2']};
        --text:      {COLORS['text']};
        --success:   {COLORS['success']};
        --warning:   {COLORS['warning']};
        --danger:    {COLORS['danger']};
        --muted:     {COLORS['muted']};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
        background-color: var(--bg);
        color: var(--text);
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #011A27 0%, #0B2435 100%);
        border-right: 1px solid #12344D;
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* ── Main area ── */
    .main .block-container {{
        padding: 1rem 2rem;
        max-width: 100%;
        background-color: var(--bg);
    }}

    /* ── Navbar ── */
    .navbar {{
        background: linear-gradient(90deg, #011A27 0%, #0B2435 100%);
        border-bottom: 1px solid #12344D;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.5rem;
    }}
    .navbar-brand {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--primary) !important;
    }}
    .navbar-right {{
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }}

    /* ── KPI Cards ── */
    .kpi-card {{
        background: linear-gradient(135deg, #0B2435 0%, #12344D 100%);
        border: 1px solid rgba(129,202,214,0.15);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(129,202,214,0.15);
        border-color: rgba(129,202,214,0.35);
    }}
    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        border-radius: 16px 16px 0 0;
    }}
    .kpi-icon {{
        font-size: 1.6rem;
        margin-bottom: 0.5rem;
    }}
    .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
        line-height: 1;
    }}
    .kpi-label {{
        font-size: 0.75rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.25rem;
    }}
    .kpi-delta {{
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }}
    .kpi-delta.up   {{ color: var(--success); }}
    .kpi-delta.down {{ color: var(--danger);  }}

    /* ── Section headers ── */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.5rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #12344D;
    }}
    .section-header h3 {{
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ── Status pills ── */
    .pill {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }}
    .pill-success  {{ background: rgba(74,222,128,0.15); color: #4ADE80; border: 1px solid rgba(74,222,128,0.3);  }}
    .pill-failure  {{ background: rgba(239,68,68,0.15);  color: #EF4444; border: 1px solid rgba(239,68,68,0.3);  }}
    .pill-running  {{ background: rgba(129,202,214,0.15);color: #81CAD6; border: 1px solid rgba(129,202,214,0.3);}}
    .pill-queued   {{ background: rgba(250,204,21,0.15); color: #FACC15; border: 1px solid rgba(250,204,21,0.3); }}
    .pill-skipped  {{ background: rgba(107,114,128,0.15);color: #6B7280; border: 1px solid rgba(107,114,128,0.3);}}
    .pill-canceled {{ background: rgba(107,114,128,0.15);color: #6B7280; border: 1px solid rgba(107,114,128,0.3);}}

    /* ── Data table ── */
    .modern-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
    }}
    .modern-table th {{
        background: #0B2435;
        color: var(--muted);
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.08em;
        padding: 0.6rem 0.8rem;
        border-bottom: 1px solid #12344D;
        text-align: left;
        white-space: nowrap;
    }}
    .modern-table td {{
        padding: 0.6rem 0.8rem;
        border-bottom: 1px solid rgba(18,52,77,0.5);
        color: var(--text);
        vertical-align: middle;
    }}
    .modern-table tr:hover td {{
        background: rgba(129,202,214,0.04);
    }}

    /* ── Chart containers ── */
    .chart-card {{
        background: linear-gradient(135deg, #0B2435 0%, #12344D 100%);
        border: 1px solid rgba(129,202,214,0.12);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }}
    .chart-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }}

    /* ── Alert / info box ── */
    .info-box {{
        background: rgba(129,202,214,0.08);
        border: 1px solid rgba(129,202,214,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 0.82rem;
        color: var(--text);
        margin: 0.5rem 0;
    }}
    .warn-box {{
        background: rgba(250,204,21,0.08);
        border: 1px solid rgba(250,204,21,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 0.82rem;
        color: var(--text);
        margin: 0.5rem 0;
    }}
    .error-box {{
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 0.82rem;
        color: var(--text);
        margin: 0.5rem 0;
    }}

    /* ── Empty state ── */
    .empty-state {{
        text-align: center;
        padding: 3rem 2rem;
        color: var(--muted);
    }}
    .empty-state .icon {{ font-size: 2.5rem; margin-bottom: 0.75rem; }}
    .empty-state h4 {{ color: var(--text); margin-bottom: 0.4rem; }}

    /* ── Avatar ── */
    .avatar {{
        width: 28px; height: 28px;
        border-radius: 50%;
        border: 2px solid var(--primary);
    }}

    /* ── Misc overrides ── */
    div[data-testid="stMetric"] {{
        background: linear-gradient(135deg, #0B2435, #12344D);
        border: 1px solid rgba(129,202,214,0.12);
        border-radius: 12px;
        padding: 0.75rem 1rem;
    }}
    div[data-testid="stMetricValue"] {{ color: var(--primary) !important; font-weight: 700; }}
    div[data-testid="stMetricLabel"] {{ color: var(--muted) !important; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; }}

    .stSelectbox label, .stTextInput label, .stDateInput label {{
        color: var(--muted) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary), #5ba8b5);
        color: #011A27;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        transition: opacity 0.15s;
    }}
    .stButton > button:hover {{ opacity: 0.85; }}

    /* Hide default streamlit header */
    header[data-testid="stHeader"] {{ display: none; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: #0B2435; }}
    ::-webkit-scrollbar-thumb {{ background: #12344D; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--primary); }}
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# GITHUB API CLIENT
# ──────────────────────────────────────────────────────────────────────────────
class GitHubClient:
    """Wrapper around GitHub REST + GraphQL APIs with caching and rate-limit handling."""

    def __init__(self, token: str, base_url: str = GITHUB_API):
        self.token = token
        self.base_url = base_url
        self.gql_url = base_url.replace("api.github.com", "api.github.com").rstrip("/") + "/graphql"
        if "api.github.com" not in self.gql_url:
            self.gql_url = base_url.rstrip("/") + "/graphql"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(self, path: str, params: dict = None) -> Optional[dict | list]:
        """GET request with error handling."""
        try:
            url = f"{self.base_url}{path}" if path.startswith("/") else path
            r = requests.get(url, headers=self._headers, params=params, timeout=15)
            if r.status_code == 401:
                st.error("❌ Authentication failed. Check your GitHub token.")
                return None
            if r.status_code == 403:
                reset = r.headers.get("X-RateLimit-Reset", "unknown")
                st.warning(f"⚠️ Rate limit hit. Resets at: {reset}")
                return None
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out.")
            return None
        except Exception as e:
            st.error(f"API error: {e}")
            return None

    def _get_paginated(self, path: str, params: dict = None, max_pages: int = 5) -> list:
        """Fetch all pages (up to max_pages)."""
        params = params or {}
        params.setdefault("per_page", 100)
        results = []
        page = 1
        while page <= max_pages:
            params["page"] = page
            data = self._get(path, params)
            if not data:
                break
            if isinstance(data, dict):
                # workflows, runs, etc. wrap items
                for key in ["workflows", "workflow_runs", "jobs", "artifacts",
                            "runners", "caches", "secrets", "variables"]:
                    if key in data:
                        items = data[key]
                        results.extend(items)
                        if len(items) < params["per_page"]:
                            return results
                        break
                else:
                    results.append(data)
                    break
            elif isinstance(data, list):
                results.extend(data)
                if len(data) < params["per_page"]:
                    break
            page += 1
        return results

    def get_rate_limit(self) -> dict:
        data = self._get("/rate_limit")
        return data.get("rate", {}) if data else {}

    def get_user(self) -> dict:
        return self._get("/user") or {}

    def get_orgs(self) -> list:
        return self._get_paginated("/user/orgs")

    def get_repos(self, org: str = None) -> list:
        if org:
            return self._get_paginated(f"/orgs/{org}/repos",
                                        {"type": "all", "sort": "updated"})
        return self._get_paginated("/user/repos",
                                    {"type": "all", "sort": "updated"})

    def get_workflows(self, owner: str, repo: str) -> list:
        return self._get_paginated(f"/repos/{owner}/{repo}/actions/workflows")

    def get_workflow_runs(self, owner: str, repo: str,
                          workflow_id: str = None,
                          branch: str = None,
                          status: str = None,
                          per_page: int = 50) -> list:
        path = (f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
                if workflow_id else
                f"/repos/{owner}/{repo}/actions/runs")
        params = {"per_page": per_page}
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status
        data = self._get(path, params)
        if not data:
            return []
        return data.get("workflow_runs", [])

    def get_jobs(self, owner: str, repo: str, run_id: int) -> list:
        data = self._get(f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs")
        return data.get("jobs", []) if data else []

    def get_artifacts(self, owner: str, repo: str) -> list:
        return self._get_paginated(f"/repos/{owner}/{repo}/actions/artifacts")

    def get_runners(self, owner: str, repo: str) -> list:
        data = self._get(f"/repos/{owner}/{repo}/actions/runners")
        return data.get("runners", []) if data else []

    def get_org_runners(self, org: str) -> list:
        data = self._get(f"/orgs/{org}/actions/runners")
        return data.get("runners", []) if data else []

    def get_caches(self, owner: str, repo: str) -> list:
        return self._get_paginated(f"/repos/{owner}/{repo}/actions/caches")

    def get_secrets_meta(self, owner: str, repo: str) -> list:
        data = self._get(f"/repos/{owner}/{repo}/actions/secrets")
        return data.get("secrets", []) if data else []

    def get_variables(self, owner: str, repo: str) -> list:
        data = self._get(f"/repos/{owner}/{repo}/actions/variables")
        return data.get("variables", []) if data else []

    def get_workflow_timing(self, owner: str, repo: str, workflow_id: int) -> dict:
        return self._get(f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/timing") or {}

    def get_branches(self, owner: str, repo: str) -> list:
        return self._get_paginated(f"/repos/{owner}/{repo}/branches")

    def graphql(self, query: str, variables: dict = None) -> dict:
        try:
            r = requests.post(
                GITHUB_GRAPHQL,
                headers=self._headers,
                json={"query": query, "variables": variables or {}},
                timeout=20,
            )
            r.raise_for_status()
            return r.json().get("data", {})
        except Exception:
            return {}

    def get_repo_languages(self, owner: str, repo: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}/languages") or {}

    def get_repo_contributors(self, owner: str, repo: str) -> list:
        return self._get_paginated(f"/repos/{owner}/{repo}/contributors")


# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "token": os.getenv("GITHUB_TOKEN", ""),
        "base_url": os.getenv("GITHUB_API_URL", GITHUB_API),
        "client": None,
        "user": None,
        "orgs": [],
        "selected_org": None,
        "repos": [],
        "selected_repo": None,
        "selected_workflow": None,
        "selected_branch": None,
        "page": "Dashboard",
        "last_refresh": None,
        "search_query": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_client() -> Optional[GitHubClient]:
    return st.session_state.get("client")


# ──────────────────────────────────────────────────────────────────────────────
# CACHED DATA FETCHERS  (TTL = 5 minutes)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def cached_runs(token: str, owner: str, repo: str, branch: str = None) -> list:
    c = GitHubClient(token)
    return c.get_workflow_runs(owner, repo, branch=branch, per_page=100)

@st.cache_data(ttl=300, show_spinner=False)
def cached_workflows(token: str, owner: str, repo: str) -> list:
    c = GitHubClient(token)
    return c.get_workflows(owner, repo)

@st.cache_data(ttl=300, show_spinner=False)
def cached_artifacts(token: str, owner: str, repo: str) -> list:
    c = GitHubClient(token)
    return c.get_artifacts(owner, repo)

@st.cache_data(ttl=300, show_spinner=False)
def cached_runners(token: str, owner: str, repo: str) -> list:
    c = GitHubClient(token)
    return c.get_runners(owner, repo)

@st.cache_data(ttl=300, show_spinner=False)
def cached_caches(token: str, owner: str, repo: str) -> list:
    c = GitHubClient(token)
    return c.get_caches(owner, repo)

@st.cache_data(ttl=300, show_spinner=False)
def cached_secrets(token: str, owner: str, repo: str) -> list:
    c = GitHubClient(token)
    return c.get_secrets_meta(owner, repo)

@st.cache_data(ttl=300, show_spinner=False)
def cached_branches(token: str, owner: str, repo: str) -> list:
    c = GitHubClient(token)
    return c.get_branches(owner, repo)

@st.cache_data(ttl=60, show_spinner=False)
def cached_rate_limit(token: str) -> dict:
    c = GitHubClient(token)
    return c.get_rate_limit()


# ──────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────
def parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def duration_str(seconds: Optional[float]) -> str:
    if not seconds:
        return "—"
    minutes, secs = divmod(int(seconds), 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    if mins:
        return f"{mins}m {secs}s"
    return f"{secs}s"

def run_duration_seconds(run: dict) -> Optional[float]:
    started = parse_iso(run.get("run_started_at") or run.get("created_at"))
    completed = parse_iso(run.get("updated_at"))
    if started and completed and completed > started:
        return (completed - started).total_seconds()
    return None

def status_pill(status: str, conclusion: str = None) -> str:
    label = conclusion or status or "unknown"
    css = {
        "success":   "success",
        "completed": "success",
        "failure":   "failure",
        "failed":    "failure",
        "in_progress": "running",
        "queued":    "queued",
        "skipped":   "skipped",
        "cancelled": "canceled",
        "canceled":  "canceled",
    }.get(label.lower(), "skipped")
    return f'<span class="pill pill-{css}">{label}</span>'

def health_score(runs: list) -> float:
    if not runs:
        return 0.0
    completed = [r for r in runs if r.get("conclusion")]
    if not completed:
        return 0.0
    success = sum(1 for r in completed if r.get("conclusion") == "success")
    return round(success / len(completed) * 100, 1)

def health_color(score: float) -> str:
    if score >= 80:
        return COLORS["success"]
    if score >= 50:
        return COLORS["warning"]
    return COLORS["danger"]

def fmt_bytes(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"

def runs_to_df(runs: list) -> pd.DataFrame:
    rows = []
    for r in runs:
        started = parse_iso(r.get("run_started_at") or r.get("created_at"))
        dur = run_duration_seconds(r)
        rows.append({
            "Run ID":    r.get("id"),
            "Workflow":  r.get("name") or r.get("display_title", ""),
            "Branch":    r.get("head_branch", ""),
            "Actor":     r.get("actor", {}).get("login", ""),
            "Status":    r.get("status", ""),
            "Conclusion": r.get("conclusion") or r.get("status", ""),
            "Event":     r.get("event", ""),
            "Started":   started.strftime("%Y-%m-%d %H:%M") if started else "",
            "Duration":  duration_str(dur),
            "_duration_s": dur or 0,
            "_started_dt": started,
            "Commit":    r.get("head_sha", "")[:7],
            "Attempt":   r.get("run_attempt", 1),
            "Run URL":   r.get("html_url", "#"),
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# PLOTLY CHART BUILDERS
# ──────────────────────────────────────────────────────────────────────────────
def make_plotly(fig) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="Inter, sans-serif", size=12),
        margin=dict(l=20, r=20, t=35, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#12344D", zerolinecolor="#12344D")
    fig.update_yaxes(gridcolor="#12344D", zerolinecolor="#12344D")
    return fig

def pie_status(runs: list) -> go.Figure:
    if not runs:
        return go.Figure()
    counts = {}
    for r in runs:
        c = r.get("conclusion") or r.get("status") or "unknown"
        counts[c] = counts.get(c, 0) + 1
    label_map = {
        "success": COLORS["success"],
        "failure": COLORS["danger"],
        "in_progress": COLORS["primary"],
        "queued": COLORS["warning"],
        "skipped": COLORS["muted"],
        "cancelled": COLORS["muted"],
        "canceled": COLORS["muted"],
    }
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [label_map.get(l, "#555") for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.6,
        marker=dict(colors=colors, line=dict(color=COLORS["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
    ))
    fig.update_layout(
        title=dict(text="Run Status", font=dict(size=13, color=COLORS["primary"])),
        showlegend=False,
    )
    return make_plotly(fig)

def daily_runs_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "_started_dt" not in df.columns:
        return go.Figure()
    df2 = df.copy()
    df2 = df2.dropna(subset=["_started_dt"])
    if df2.empty:
        return go.Figure()
    df2["date"] = df2["_started_dt"].apply(lambda x: x.date() if x else None)
    daily = df2.groupby(["date", "Conclusion"]).size().reset_index(name="count")
    color_map = {
        "success": COLORS["success"],
        "failure": COLORS["danger"],
        "in_progress": COLORS["primary"],
        "queued": COLORS["warning"],
        "skipped": COLORS["muted"],
        "cancelled": COLORS["muted"],
        "canceled": COLORS["muted"],
    }
    fig = px.bar(daily, x="date", y="count", color="Conclusion",
                  color_discrete_map=color_map,
                  barmode="stack",
                  labels={"date": "", "count": "Runs"})
    fig.update_layout(title=dict(text="Daily Workflow Runs",
                                  font=dict(size=13, color=COLORS["primary"])))
    return make_plotly(fig)

def duration_trend(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    df2 = df[df["_duration_s"] > 0].copy()
    if df2.empty:
        return go.Figure()
    df2 = df2.dropna(subset=["_started_dt"])
    df2 = df2.sort_values("_started_dt")
    df2["duration_min"] = df2["_duration_s"] / 60
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df2["_started_dt"], y=df2["duration_min"],
        mode="lines+markers",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=5, color=COLORS["secondary"]),
        name="Duration (min)",
        fill="tozeroy",
        fillcolor="rgba(129,202,214,0.08)",
    ))
    fig.update_layout(
        title=dict(text="Build Duration Trend (minutes)",
                   font=dict(size=13, color=COLORS["primary"])),
        xaxis_title="", yaxis_title="Minutes",
    )
    return make_plotly(fig)

def top_failed_workflows(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    failed = df[df["Conclusion"] == "failure"]
    if failed.empty:
        return go.Figure()
    top = failed["Workflow"].value_counts().head(10).reset_index()
    top.columns = ["Workflow", "Failures"]
    fig = px.bar(top, x="Failures", y="Workflow", orientation="h",
                  color_discrete_sequence=[COLORS["danger"]])
    fig.update_layout(
        title=dict(text="Top Failed Workflows",
                   font=dict(size=13, color=COLORS["primary"])),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title="",
    )
    return make_plotly(fig)

def actor_leaderboard(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    top = df["Actor"].value_counts().head(10).reset_index()
    top.columns = ["Actor", "Runs"]
    fig = px.bar(top, x="Actor", y="Runs",
                  color_discrete_sequence=[COLORS["secondary"]])
    fig.update_layout(
        title=dict(text="Top Workflow Triggers",
                   font=dict(size=13, color=COLORS["primary"])),
        xaxis_title="", yaxis_title="",
    )
    return make_plotly(fig)

def branch_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    top = df["Branch"].value_counts().head(10).reset_index()
    top.columns = ["Branch", "Runs"]
    fig = px.pie(top, names="Branch", values="Runs", hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Teal)
    fig.update_layout(
        title=dict(text="Runs by Branch",
                   font=dict(size=13, color=COLORS["primary"])),
    )
    return make_plotly(fig)

def success_rate_gauge(score: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number=dict(suffix="%", font=dict(color=COLORS["primary"], size=36)),
        delta=dict(reference=80, increasing=dict(color=COLORS["success"]),
                   decreasing=dict(color=COLORS["danger"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=COLORS["muted"]),
            bar=dict(color=COLORS["primary"]),
            steps=[
                dict(range=[0, 50],  color="rgba(239,68,68,0.15)"),
                dict(range=[50, 80], color="rgba(250,204,21,0.15)"),
                dict(range=[80, 100],color="rgba(74,222,128,0.15)"),
            ],
            threshold=dict(line=dict(color=COLORS["warning"], width=3), value=80),
        ),
        title=dict(text="Success Rate", font=dict(color=COLORS["muted"], size=12)),
    ))
    fig.update_layout(height=220)
    return make_plotly(fig)

def runtime_dist(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    df2 = df[df["_duration_s"] > 0].copy()
    if df2.empty:
        return go.Figure()
    df2["duration_min"] = df2["_duration_s"] / 60
    fig = px.histogram(df2, x="duration_min", nbins=25,
                        color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(
        title=dict(text="Runtime Distribution",
                   font=dict(size=13, color=COLORS["primary"])),
        xaxis_title="Duration (min)", yaxis_title="Count",
    )
    return make_plotly(fig)

def runner_utilization(runners: list) -> go.Figure:
    if not runners:
        return go.Figure()
    statuses = {"online": 0, "offline": 0}
    for r in runners:
        s = r.get("status", "offline").lower()
        statuses[s] = statuses.get(s, 0) + 1
    fig = go.Figure(go.Bar(
        x=list(statuses.keys()),
        y=list(statuses.values()),
        marker_color=[COLORS["success"], COLORS["danger"]][:len(statuses)],
    ))
    fig.update_layout(
        title=dict(text="Runner Status", font=dict(size=13, color=COLORS["primary"])),
        xaxis_title="", yaxis_title="Count",
    )
    return make_plotly(fig)


# ──────────────────────────────────────────────────────────────────────────────
# UI COMPONENTS
# ──────────────────────────────────────────────────────────────────────────────
def kpi_card(icon: str, label: str, value, delta: str = None, delta_up: bool = True):
    delta_html = ""
    if delta:
        cls = "up" if delta_up else "down"
        arrow = "↑" if delta_up else "↓"
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {delta}</div>'
    return f"""
    <div class="kpi-card">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
      {delta_html}
    </div>
    """

def section_header(icon: str, title: str):
    st.markdown(
        f'<div class="section-header"><span>{icon}</span><h3>{title}</h3></div>',
        unsafe_allow_html=True,
    )

def render_navbar(user: dict, rl: dict):
    remaining = rl.get("remaining", "?")
    limit = rl.get("limit", "?")
    avatar = user.get("avatar_url", "")
    login = user.get("login", "")
    avatar_html = f'<img src="{avatar}" class="avatar" />' if avatar else "👤"
    rl_color = COLORS["success"] if (remaining != "?" and remaining > 500) else COLORS["warning"]
    st.markdown(f"""
    <div class="navbar">
      <div class="navbar-brand">
        <svg height="22" viewBox="0 0 16 16" fill="{COLORS['primary']}" aria-hidden="true">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
          0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01
          1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95
          0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68
          0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15
          0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38
          A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
        </svg>
        GitHub Actions Analytics
      </div>
      <div class="navbar-right">
        <span style="color:{rl_color};font-size:.75rem;font-weight:600;">
          ⚡ {remaining}/{limit} API calls
        </span>
        <span style="font-size:.75rem;color:{COLORS['muted']};">
          🕐 {datetime.now().strftime('%H:%M:%S')}
        </span>
        {avatar_html}
        <span style="font-size:.78rem;font-weight:600;color:{COLORS['primary']};">
          {login}
        </span>
        <span style="width:8px;height:8px;border-radius:50%;background:{COLORS['success']};
              display:inline-block;" title="Connected"></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    client = get_client()
    token = st.session_state.token

    with st.sidebar:
        # Logo
        st.markdown(f"""
        <div style="padding:1rem 0 0.5rem; text-align:center;">
          <div style="font-size:1.3rem;font-weight:800;color:{COLORS['primary']};
                      letter-spacing:.03em;">⚡ GH Analytics</div>
          <div style="font-size:.7rem;color:{COLORS['muted']};margin-top:2px;">
            Enterprise CI/CD Observability
          </div>
        </div>
        <hr style="border-color:#12344D;margin:.75rem 0;" />
        """, unsafe_allow_html=True)

        # Token input
        if not st.session_state.token:
            st.markdown('<div style="font-size:.72rem;color:{};text-transform:uppercase;'
                        'letter-spacing:.06em;margin-bottom:.3rem;">GitHub Token</div>'.format(
                            COLORS["muted"]), unsafe_allow_html=True)
            tok = st.text_input("Token", type="password", label_visibility="collapsed",
                                 placeholder="ghp_... or github_pat_...",
                                 key="token_input")
            be = st.text_input("GitHub Enterprise URL (optional)", placeholder=GITHUB_API,
                                key="be_input", label_visibility="visible")
            if st.button("🔌 Connect", use_container_width=True):
                if tok:
                    st.session_state.token = tok
                    st.session_state.base_url = be or GITHUB_API
                    st.session_state.client = GitHubClient(tok, st.session_state.base_url)
                    with st.spinner("Authenticating…"):
                        user = st.session_state.client.get_user()
                        if user and user.get("login"):
                            st.session_state.user = user
                            orgs = st.session_state.client.get_orgs()
                            st.session_state.orgs = orgs
                            st.success(f"✅ Connected as **{user['login']}**")
                            st.rerun()
                        else:
                            st.error("Authentication failed.")
                            st.session_state.token = ""
            return

        # Connected state
        if client:
            user = st.session_state.user or {}
            if user.get("avatar_url"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(user["avatar_url"], width=36)
                with col2:
                    st.markdown(f"""
                    <div style="font-size:.82rem;font-weight:700;color:{COLORS['text']};">
                      {user.get('login','')}
                    </div>
                    <div style="font-size:.7rem;color:{COLORS['muted']};">
                      {user.get('name','') or user.get('company','')}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('<hr style="border-color:#12344D;margin:.5rem 0;" />',
                        unsafe_allow_html=True)

            # Org selector
            orgs = st.session_state.orgs
            org_names = [o["login"] for o in orgs]
            user_login = user.get("login", "")
            all_contexts = [user_login] + org_names
            selected_ctx = st.selectbox("Organization / User", all_contexts, key="ctx_sel")
            if selected_ctx != user_login:
                st.session_state.selected_org = selected_ctx
            else:
                st.session_state.selected_org = None

            # Repo selector
            if "repos" not in st.session_state or not st.session_state.repos:
                with st.spinner("Loading repos…"):
                    repos = client.get_repos(st.session_state.selected_org)
                    st.session_state.repos = sorted(repos, key=lambda r: r.get("updated_at", ""), reverse=True)
            repos = st.session_state.repos
            repo_names = [r["full_name"] for r in repos]
            if repo_names:
                sel_repo = st.selectbox("Repository", ["— select —"] + repo_names, key="repo_sel")
                st.session_state.selected_repo = sel_repo if sel_repo != "— select —" else None
            else:
                st.info("No repositories found.")
                st.session_state.selected_repo = None

            # Branch selector
            if st.session_state.selected_repo:
                owner, repo_name = st.session_state.selected_repo.split("/", 1)
                branches = cached_branches(token, owner, repo_name)
                branch_names = [b["name"] for b in branches]
                sel_branch = st.selectbox("Branch", ["All"] + branch_names, key="branch_sel")
                st.session_state.selected_branch = None if sel_branch == "All" else sel_branch
            else:
                st.session_state.selected_branch = None

            st.markdown('<hr style="border-color:#12344D;margin:.5rem 0;" />',
                        unsafe_allow_html=True)

            # Navigation
            st.markdown(f'<div style="font-size:.65rem;color:{COLORS["muted"]};'
                        'text-transform:uppercase;letter-spacing:.1em;'
                        'margin-bottom:.4rem;">Navigation</div>', unsafe_allow_html=True)
            for icon, name in PAGES:
                active = st.session_state.page == name
                bg = f"background:rgba(129,202,214,0.12);border-left:3px solid {COLORS['primary']};" if active else ""
                if st.button(f"{icon} {name}", key=f"nav_{name}", use_container_width=True):
                    st.session_state.page = name
                    st.rerun()

            st.markdown('<hr style="border-color:#12344D;margin:.5rem 0;" />',
                        unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.session_state.last_refresh = datetime.now()
                    st.rerun()
            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    for k in ["token","client","user","orgs","repos","selected_repo",
                               "selected_org","selected_branch","selected_workflow"]:
                        st.session_state[k] = None if k != "token" else ""
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# PAGE RENDERERS
# ──────────────────────────────────────────────────────────────────────────────
def page_not_connected():
    st.markdown(f"""
    <div class="empty-state" style="margin-top:4rem;">
      <div class="icon">⚡</div>
      <h4 style="color:{COLORS['primary']};font-size:1.4rem;">GitHub Actions Analytics</h4>
      <p style="color:{COLORS['muted']};max-width:400px;margin:.5rem auto;">
        Connect your GitHub Personal Access Token in the sidebar to start
        monitoring CI/CD pipelines across your repositories.
      </p>
      <div class="info-box" style="max-width:420px;margin:1rem auto;text-align:left;">
        <strong>Required token scopes:</strong><br/>
        <code>repo</code> · <code>workflow</code> · <code>read:org</code> · <code>read:user</code>
      </div>
    </div>
    """, unsafe_allow_html=True)

def page_no_repo():
    st.markdown(f"""
    <div class="empty-state" style="margin-top:3rem;">
      <div class="icon">📁</div>
      <h4>Select a Repository</h4>
      <p style="color:{COLORS['muted']};">
        Choose a repository from the sidebar to view its GitHub Actions analytics.
      </p>
    </div>
    """, unsafe_allow_html=True)

def page_dashboard(client: GitHubClient, owner: str, repo: str):
    token = st.session_state.token
    branch = st.session_state.selected_branch

    with st.spinner("Loading dashboard data…"):
        runs = cached_runs(token, owner, repo, branch)
        workflows = cached_workflows(token, owner, repo)
        artifacts = cached_artifacts(token, owner, repo)
        runners = cached_runners(token, owner, repo)

    df = runs_to_df(runs)
    score = health_score(runs)
    total = len(runs)
    successful = sum(1 for r in runs if r.get("conclusion") == "success")
    failed = sum(1 for r in runs if r.get("conclusion") == "failure")
    in_progress = sum(1 for r in runs if r.get("status") == "in_progress")
    queued = sum(1 for r in runs if r.get("status") == "queued")
    cancelled = sum(1 for r in runs if r.get("conclusion") in ("cancelled","canceled"))
    skipped = sum(1 for r in runs if r.get("conclusion") == "skipped")

    durations = [d for d in [run_duration_seconds(r) for r in runs] if d]
    avg_dur = sum(durations) / len(durations) if durations else 0
    artifact_size = sum(a.get("size_in_bytes", 0) for a in artifacts)
    online_runners = sum(1 for r in runners if r.get("status") == "online")
    offline_runners = len(runners) - online_runners

    # ── KPIs ──
    section_header("🏠", "Overview")
    cols = st.columns(5)
    kpis = [
        ("🗂️", "Total Runs",     total,            None, True),
        ("✅", "Successful",     successful,       f"{score}% rate", score >= 80),
        ("❌", "Failed",         failed,           None, False),
        ("⏳", "In Progress",    in_progress,      None, True),
        ("🏎️", "Avg Duration",   duration_str(avg_dur), None, True),
    ]
    for i, (icon, label, val, delta, up) in enumerate(kpis):
        with cols[i]:
            st.markdown(kpi_card(icon, label, val, delta, up), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    cols2 = st.columns(5)
    kpis2 = [
        ("🔄", "Queued",         queued,           None, True),
        ("⏭️", "Skipped",        skipped,          None, True),
        ("🚫", "Cancelled",      cancelled,        None, False),
        ("📦", "Artifacts",      len(artifacts),   fmt_bytes(artifact_size), True),
        ("🖥️", "Runners Online", f"{online_runners}/{len(runners)}", None, online_runners > 0),
    ]
    for i, (icon, label, val, delta, up) in enumerate(kpis2):
        with cols2[i]:
            st.markdown(kpi_card(icon, label, val, delta, up), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Charts row 1 ──
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(daily_runs_chart(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(pie_status(runs), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(success_rate_gauge(score), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Charts row 2 ──
    c4, c5 = st.columns(2)
    with c4:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(duration_trend(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(top_failed_workflows(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Charts row 3 ──
    c6, c7 = st.columns(2)
    with c6:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(actor_leaderboard(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c7:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(branch_chart(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Recent runs table ──
    section_header("🚀", "Recent Workflow Runs")
    render_runs_table(df.head(20))


def render_runs_table(df: pd.DataFrame):
    if df.empty:
        st.markdown('<div class="empty-state"><div class="icon">🚀</div>'
                    '<h4>No workflow runs found</h4>'
                    '<p>Trigger a workflow or adjust your filters.</p></div>',
                    unsafe_allow_html=True)
        return

    rows_html = ""
    for _, row in df.iterrows():
        pill = status_pill(row["Status"], row["Conclusion"])
        rows_html += f"""
        <tr>
          <td><a href="{row.get('Run URL','#')}" target="_blank"
                 style="color:{COLORS['primary']};text-decoration:none;">
            #{row['Run ID']}</a></td>
          <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            {row['Workflow']}</td>
          <td><span style="color:{COLORS['secondary']};">{row['Branch']}</span></td>
          <td>{row['Actor']}</td>
          <td>{pill}</td>
          <td>{row['Event']}</td>
          <td>{row['Started']}</td>
          <td>{row['Duration']}</td>
          <td style="font-family:monospace;font-size:.7rem;color:{COLORS['muted']};">
            {row['Commit']}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr>
        <th>Run</th><th>Workflow</th><th>Branch</th><th>Actor</th>
        <th>Status</th><th>Event</th><th>Started</th><th>Duration</th><th>Commit</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)


def page_repositories(client: GitHubClient):
    section_header("📁", "Repositories")
    repos = st.session_state.repos
    if not repos:
        page_no_repo()
        return

    search = st.text_input("🔎 Search repositories", placeholder="Filter by name…", key="repo_search")
    if search:
        repos = [r for r in repos if search.lower() in r["full_name"].lower()]

    col_labels = st.columns([3, 1, 1, 1, 1, 1, 1])
    for col, label in zip(col_labels, ["Repository", "Stars", "Forks", "Issues", "Visibility", "Language", "Updated"]):
        col.markdown(f'<div style="font-size:.68rem;color:{COLORS["muted"]};text-transform:uppercase;'
                     f'letter-spacing:.08em;">{label}</div>', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#12344D;margin:.3rem 0 .5rem;"/>', unsafe_allow_html=True)

    for r in repos[:50]:
        c = st.columns([3, 1, 1, 1, 1, 1, 1])
        vis_color = COLORS["primary"] if r.get("private") else COLORS["success"]
        vis_label = "Private" if r.get("private") else "Public"
        upd = parse_iso(r.get("updated_at", ""))
        with c[0]:
            st.markdown(f'<a href="{r.get("html_url","#")}" target="_blank" '
                        f'style="color:{COLORS["primary"]};font-weight:600;font-size:.85rem;">'
                        f'{r["full_name"]}</a>'
                        f'<div style="font-size:.7rem;color:{COLORS["muted"]};">'
                        f'{(r.get("description") or "")[:60]}</div>', unsafe_allow_html=True)
        with c[1]:
            st.markdown(f'<span style="color:{COLORS["warning"]};">⭐ {r.get("stargazers_count",0)}</span>',
                        unsafe_allow_html=True)
        with c[2]:
            st.write(r.get("forks_count", 0))
        with c[3]:
            st.write(r.get("open_issues_count", 0))
        with c[4]:
            st.markdown(f'<span class="pill pill-{"skipped" if r.get("private") else "success"}">'
                        f'{vis_label}</span>', unsafe_allow_html=True)
        with c[5]:
            lang = r.get("language") or "—"
            st.markdown(f'<code style="font-size:.7rem;">{lang}</code>', unsafe_allow_html=True)
        with c[6]:
            st.markdown(f'<span style="font-size:.72rem;color:{COLORS["muted"]};">'
                        f'{upd.strftime("%b %d") if upd else "—"}</span>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color:rgba(18,52,77,0.3);margin:.2rem 0;"/>', unsafe_allow_html=True)


def page_workflows(client: GitHubClient, owner: str, repo: str):
    section_header("⚙️", f"Workflows — {owner}/{repo}")
    token = st.session_state.token
    workflows = cached_workflows(token, owner, repo)

    if not workflows:
        st.markdown('<div class="empty-state"><div class="icon">⚙️</div>'
                    '<h4>No workflows found</h4>'
                    '<p>This repository has no GitHub Actions workflows.</p></div>',
                    unsafe_allow_html=True)
        return

    for wf in workflows:
        state_color = COLORS["success"] if wf.get("state") == "active" else COLORS["muted"]
        with st.expander(f"⚙️ {wf.get('name','Unnamed')} — {wf.get('path','')}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("State", wf.get("state", "—").title())
            c2.metric("ID", wf.get("id", "—"))
            c3.markdown(f'<a href="{wf.get("html_url","#")}" target="_blank" '
                        f'style="color:{COLORS["primary"]};">View on GitHub ↗</a>',
                        unsafe_allow_html=True)


def page_runs(client: GitHubClient, owner: str, repo: str):
    section_header("🚀", f"Workflow Runs — {owner}/{repo}")
    token = st.session_state.token

    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "completed", "in_progress", "queued"], key="run_status_f")
    with col2:
        conclusion_filter = st.selectbox("Conclusion", ["All", "success", "failure", "cancelled", "skipped"], key="run_conc_f")
    with col3:
        search_actor = st.text_input("Filter by actor", key="run_actor_f")

    runs = cached_runs(token, owner, repo, st.session_state.selected_branch)
    if status_filter != "All":
        runs = [r for r in runs if r.get("status") == status_filter]
    if conclusion_filter != "All":
        runs = [r for r in runs if r.get("conclusion") == conclusion_filter]
    if search_actor:
        runs = [r for r in runs if search_actor.lower() in r.get("actor",{}).get("login","").lower()]

    df = runs_to_df(runs)
    st.markdown(f'<div style="font-size:.78rem;color:{COLORS["muted"]};margin-bottom:.5rem;">'
                f'Showing {len(df)} runs</div>', unsafe_allow_html=True)
    render_runs_table(df)


def page_jobs(client: GitHubClient, owner: str, repo: str):
    section_header("📋", f"Jobs — {owner}/{repo}")
    token = st.session_state.token
    runs = cached_runs(token, owner, repo)

    if not runs:
        page_no_repo()
        return

    recent_run = runs[0] if runs else None
    if not recent_run:
        return

    run_id = recent_run["id"]
    st.markdown(f'<div class="info-box">Showing jobs for latest run: '
                f'<strong>#{run_id}</strong> — {recent_run.get("name","")}</div>',
                unsafe_allow_html=True)

    with st.spinner("Loading jobs…"):
        jobs = client.get_jobs(owner, repo, run_id)

    if not jobs:
        st.markdown('<div class="empty-state"><div class="icon">📋</div>'
                    '<h4>No jobs found</h4></div>', unsafe_allow_html=True)
        return

    for job in jobs:
        started = parse_iso(job.get("started_at"))
        completed = parse_iso(job.get("completed_at"))
        dur = (completed - started).total_seconds() if started and completed and completed > started else None
        conclusion = job.get("conclusion") or job.get("status", "")
        pill = status_pill(job.get("status",""), job.get("conclusion"))

        with st.expander(f"{pill} {job.get('name','Job')} — {duration_str(dur)}",
                          expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Runner", job.get("runner_name") or "GitHub-hosted")
            c2.metric("OS", (job.get("runner_group_name") or job.get("labels",[""])[0] or "—"))
            c3.metric("Duration", duration_str(dur))
            c4.metric("Status", conclusion.title() if conclusion else "—")

            steps = job.get("steps", [])
            if steps:
                st.markdown(f'<div class="chart-title" style="margin-top:.5rem;">Steps</div>',
                            unsafe_allow_html=True)
                rows = ""
                for step in steps:
                    s_conc = step.get("conclusion") or step.get("status","")
                    s_pill = status_pill(step.get("status",""), step.get("conclusion"))
                    s_start = parse_iso(step.get("started_at"))
                    s_end   = parse_iso(step.get("completed_at"))
                    s_dur = (s_end - s_start).total_seconds() if s_start and s_end and s_end > s_start else None
                    rows += f"""
                    <tr>
                      <td>{step.get('number','')}</td>
                      <td>{step.get('name','')}</td>
                      <td>{s_pill}</td>
                      <td>{duration_str(s_dur)}</td>
                    </tr>"""
                st.markdown(f"""
                <table class="modern-table" style="font-size:.78rem;">
                  <thead><tr><th>#</th><th>Step</th><th>Status</th><th>Duration</th></tr></thead>
                  <tbody>{rows}</tbody>
                </table>
                """, unsafe_allow_html=True)


def page_analytics(client: GitHubClient, owner: str, repo: str):
    section_header("📊", f"Analytics — {owner}/{repo}")
    token = st.session_state.token
    runs = cached_runs(token, owner, repo, st.session_state.selected_branch)
    df = runs_to_df(runs)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(daily_runs_chart(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(runtime_dist(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(top_failed_workflows(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(actor_leaderboard(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


def page_performance(client: GitHubClient, owner: str, repo: str):
    section_header("📈", f"Performance — {owner}/{repo}")
    token = st.session_state.token
    runs = cached_runs(token, owner, repo, st.session_state.selected_branch)
    df = runs_to_df(runs)

    durations = sorted([d for d in df["_duration_s"].tolist() if d > 0])
    avg = sum(durations) / len(durations) if durations else 0
    median = durations[len(durations)//2] if durations else 0
    p95 = durations[int(len(durations)*0.95)] if len(durations) >= 20 else (durations[-1] if durations else 0)
    fastest = min(durations) if durations else 0
    slowest = max(durations) if durations else 0

    cols = st.columns(5)
    stats = [
        ("⏱️", "Avg Duration",   duration_str(avg)),
        ("📊", "Median",         duration_str(median)),
        ("📈", "P95 Runtime",    duration_str(p95)),
        ("🐇", "Fastest",        duration_str(fastest)),
        ("🐢", "Slowest",        duration_str(slowest)),
    ]
    for i, (icon, label, val) in enumerate(stats):
        with cols[i]:
            st.markdown(kpi_card(icon, label, val), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(duration_trend(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(runtime_dist(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


def page_runners(client: GitHubClient, owner: str, repo: str, self_hosted: bool = True):
    label = "Self-Hosted Runners" if self_hosted else "GitHub-Hosted Runners"
    section_header("🖥️" if self_hosted else "☁️", f"{label} — {owner}/{repo}")
    runners = cached_runners(st.session_state.token, owner, repo)

    if self_hosted:
        runners = [r for r in runners if not any(
            l.get("name","").startswith("ubuntu-") or l.get("name","").startswith("macos-") or l.get("name","").startswith("windows-")
            for l in r.get("labels", [])
        )]
    else:
        runners = [r for r in runners if any(
            l.get("name","").lower() in ["ubuntu-latest","macos-latest","windows-latest"]
            for l in r.get("labels", [])
        )]

    if not runners:
        st.markdown(f'<div class="empty-state"><div class="icon">{"🖥️" if self_hosted else "☁️"}</div>'
                    f'<h4>No {label.lower()} configured</h4>'
                    f'<p>Add runners in your repository settings.</p></div>',
                    unsafe_allow_html=True)
        # Show org runners if available
        org = st.session_state.selected_org
        if org:
            org_runners = client.get_org_runners(org)
            if org_runners:
                st.markdown(f'<div class="info-box">Showing {len(org_runners)} organization runners.</div>',
                            unsafe_allow_html=True)
                runners = org_runners
            else:
                return
        else:
            return

    # Summary KPIs
    online = sum(1 for r in runners if r.get("status") == "online")
    offline = len(runners) - online
    busy = sum(1 for r in runners if r.get("busy"))

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card("🟢", "Online", online), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("🔴", "Offline", offline), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("⚡", "Busy", busy), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    c_chart, c_table = st.columns([1, 2])
    with c_chart:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(runner_utilization(runners), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c_table:
        rows = ""
        for r in runners:
            status = r.get("status", "offline")
            scls = "success" if status == "online" else "failure"
            labels = ", ".join(l.get("name","") for l in r.get("labels",[]))
            busy_s = "⚡ Busy" if r.get("busy") else "💤 Idle"
            rows += f"""
            <tr>
              <td>{r.get('name','')}</td>
              <td><span class="pill pill-{scls}">{status}</span></td>
              <td>{busy_s}</td>
              <td style="font-size:.7rem;color:{COLORS['muted']};">{labels[:40]}</td>
              <td>{r.get('id','')}</td>
            </tr>"""
        st.markdown(f"""
        <div style="overflow-x:auto;">
        <table class="modern-table">
          <thead><tr><th>Runner</th><th>Status</th><th>Activity</th><th>Labels</th><th>ID</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)


def page_artifacts(client: GitHubClient, owner: str, repo: str):
    section_header("📦", f"Artifacts — {owner}/{repo}")
    token = st.session_state.token
    artifacts = cached_artifacts(token, owner, repo)

    if not artifacts:
        st.markdown('<div class="empty-state"><div class="icon">📦</div>'
                    '<h4>No artifacts found</h4>'
                    '<p>Artifacts are generated by your workflows.</p></div>',
                    unsafe_allow_html=True)
        return

    total_size = sum(a.get("size_in_bytes", 0) for a in artifacts)
    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi_card("📦", "Total Artifacts", len(artifacts)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("💾", "Total Storage", fmt_bytes(total_size)), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    rows = ""
    for a in artifacts[:50]:
        created = parse_iso(a.get("created_at",""))
        expires = parse_iso(a.get("expires_at",""))
        expired = a.get("expired", False)
        exp_class = "failure" if expired else "success"
        rows += f"""
        <tr>
          <td><strong>{a.get('name','')}</strong></td>
          <td>{fmt_bytes(a.get('size_in_bytes',0))}</td>
          <td>{created.strftime('%Y-%m-%d') if created else '—'}</td>
          <td>{expires.strftime('%Y-%m-%d') if expires else '—'}</td>
          <td><span class="pill pill-{exp_class}">{'Expired' if expired else 'Active'}</span></td>
          <td>{a.get('id','')}</td>
        </tr>"""
    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr><th>Name</th><th>Size</th><th>Created</th><th>Expires</th><th>Status</th><th>ID</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)


def page_cache(client: GitHubClient, owner: str, repo: str):
    section_header("📂", f"Cache — {owner}/{repo}")
    token = st.session_state.token
    caches = cached_caches(token, owner, repo)

    if not caches:
        st.markdown('<div class="empty-state"><div class="icon">📂</div>'
                    '<h4>No caches found</h4>'
                    '<p>Workflow caches speed up your CI/CD pipelines.</p></div>',
                    unsafe_allow_html=True)
        return

    total_size = sum(c.get("size_in_bytes", 0) for c in caches)
    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi_card("📂", "Cache Entries", len(caches)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("💾", "Total Size", fmt_bytes(total_size)), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    rows = ""
    for c in caches[:50]:
        last_accessed = parse_iso(c.get("last_accessed_at",""))
        created = parse_iso(c.get("created_at",""))
        rows += f"""
        <tr>
          <td><code style="font-size:.75rem;">{c.get('key','')}</code></td>
          <td>{c.get('ref','')}</td>
          <td>{fmt_bytes(c.get('size_in_bytes',0))}</td>
          <td>{created.strftime('%Y-%m-%d') if created else '—'}</td>
          <td>{last_accessed.strftime('%Y-%m-%d') if last_accessed else '—'}</td>
        </tr>"""
    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr><th>Key</th><th>Ref</th><th>Size</th><th>Created</th><th>Last Accessed</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)


def page_security(client: GitHubClient, owner: str, repo: str):
    section_header("🔐", f"Security — {owner}/{repo}")
    token = st.session_state.token
    secrets = cached_secrets(token, owner, repo)
    variables = client.get_variables(owner, repo)

    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi_card("🔑", "Secrets", len(secrets)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("📝", "Variables", len(variables)), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        section_header("🔑", "Repository Secrets")
        if secrets:
            rows = "".join(f"""
            <tr>
              <td>🔒 {s.get('name','')}</td>
              <td style="font-size:.7rem;color:{COLORS['muted']};">
                {parse_iso(s.get('updated_at','')).strftime('%Y-%m-%d') if parse_iso(s.get('updated_at','')) else '—'}
              </td>
            </tr>""" for s in secrets)
            st.markdown(f"""
            <table class="modern-table">
              <thead><tr><th>Secret Name</th><th>Last Updated</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No secrets configured.</div>', unsafe_allow_html=True)

    with col2:
        section_header("📝", "Variables")
        if variables:
            rows = "".join(f"""
            <tr>
              <td>{v.get('name','')}</td>
              <td style="font-family:monospace;font-size:.75rem;">{str(v.get('value',''))[:40]}</td>
            </tr>""" for v in variables)
            st.markdown(f"""
            <table class="modern-table">
              <thead><tr><th>Variable</th><th>Value</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No variables configured.</div>', unsafe_allow_html=True)


def page_reports(client: GitHubClient, owner: str, repo: str):
    section_header("📄", f"Reports — {owner}/{repo}")
    token = st.session_state.token

    st.markdown('<div class="info-box">Generate and export analytics reports for this repository.</div>',
                unsafe_allow_html=True)

    report_type = st.selectbox("Report Type", ["Workflow Runs", "Artifacts", "Performance Summary"])
    col1, col2 = st.columns(2)
    with col1:
        fmt = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])

    if st.button("📥 Generate Report", use_container_width=False):
        with st.spinner("Generating report…"):
            runs = cached_runs(token, owner, repo)
            df = runs_to_df(runs)
            # Drop internal cols
            export_df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")

            if fmt == "CSV":
                data = export_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", data, "gh_actions_report.csv", "text/csv")
            elif fmt == "JSON":
                data = export_df.to_json(orient="records", indent=2).encode("utf-8")
                st.download_button("⬇️ Download JSON", data, "gh_actions_report.json", "application/json")
            elif fmt == "Excel":
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Workflow Runs")
                st.download_button("⬇️ Download Excel", buf.getvalue(),
                                   "gh_actions_report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.success("✅ Report ready for download!")


def page_api_monitor(client: GitHubClient):
    section_header("📡", "GitHub API Monitor")
    token = st.session_state.token
    rl = cached_rate_limit(token)

    if not rl:
        st.markdown('<div class="error-box">Unable to fetch rate limit data.</div>', unsafe_allow_html=True)
        return

    remaining = rl.get("remaining", 0)
    limit = rl.get("limit", 5000)
    used = limit - remaining
    reset_ts = rl.get("reset", 0)
    reset_dt = datetime.fromtimestamp(reset_ts, tz=timezone.utc) if reset_ts else None
    pct_used = used / limit * 100 if limit else 0
    pct_remaining = 100 - pct_used

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi_card("📡", "API Limit", limit), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("✅", "Remaining", remaining, None, pct_remaining > 20), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("📊", "Used", used), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("🕐", "Resets At",
                                   reset_dt.strftime("%H:%M UTC") if reset_dt else "—"),
                          unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Gauge
    bar_color = COLORS["success"] if pct_remaining > 50 else (COLORS["warning"] if pct_remaining > 20 else COLORS["danger"])
    fig = go.Figure(go.Bar(
        x=[used, remaining],
        y=["API Usage", "API Usage"],
        orientation="h",
        marker_color=[COLORS["danger"], COLORS["success"]],
        text=[f"Used: {used}", f"Remaining: {remaining}"],
        textposition="inside",
    ))
    fig.update_layout(
        title=dict(text="API Rate Limit Utilization", font=dict(size=13, color=COLORS["primary"])),
        barmode="stack", xaxis_range=[0, limit],
        height=120, margin=dict(l=20, r=20, t=40, b=20),
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(make_plotly(fig), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    if pct_remaining < 10:
        st.markdown(f'<div class="error-box">⚠️ API rate limit critically low! '
                    f'Resets at {reset_dt.strftime("%H:%M UTC") if reset_dt else "unknown"}.</div>',
                    unsafe_allow_html=True)


def page_settings():
    section_header("⚙️", "Settings")
    user = st.session_state.get("user", {}) or {}
    token = st.session_state.token

    with st.expander("👤 Account", expanded=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            if user.get("avatar_url"):
                st.image(user["avatar_url"], width=60)
        with c2:
            st.markdown(f"""
            **Login:** {user.get('login','—')}  
            **Name:** {user.get('name','—')}  
            **Company:** {user.get('company','—')}  
            **Email:** {user.get('email','—')}  
            """)

    with st.expander("🔌 Connection"):
        st.markdown(f"**API Endpoint:** `{st.session_state.get('base_url', GITHUB_API)}`")
        st.markdown(f"**Token:** `{'*' * 20}{token[-4:] if len(token) >= 4 else '****'}`")
        rl = cached_rate_limit(token)
        if rl:
            st.markdown(f"**Rate Limit:** {rl.get('remaining','?')}/{rl.get('limit','?')} remaining")

    with st.expander("ℹ️ About"):
        st.markdown("""
        **GitHub Actions Analytics Dashboard**  
        Enterprise-grade CI/CD observability platform  
        
        Built with: Python · Streamlit · Plotly · GitHub REST & GraphQL APIs  
        Version: 1.0.0
        """)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────────────────────────────────────
def main():
    init_session()
    inject_css()
    render_sidebar()

    client = get_client()
    token  = st.session_state.token

    # Top navbar
    if client and token:
        user = st.session_state.user or {}
        rl   = cached_rate_limit(token)
        render_navbar(user, rl)

    # No token → landing
    if not token or not client:
        page_not_connected()
        return

    page = st.session_state.page

    # Pages that need repo context
    repo_pages = {"Dashboard", "Workflows", "Workflow Runs", "Jobs", "Analytics",
                  "Performance", "Self-Hosted Runners", "GitHub Runners",
                  "Artifacts", "Cache", "Security", "Reports"}

    owner = repo_name = None
    if page in repo_pages:
        sel = st.session_state.selected_repo
        if not sel:
            page_no_repo()
            return
        owner, repo_name = sel.split("/", 1)

    # Route
    if page == "Dashboard":
        page_dashboard(client, owner, repo_name)
    elif page == "Repositories":
        page_repositories(client)
    elif page == "Workflows":
        page_workflows(client, owner, repo_name)
    elif page == "Workflow Runs":
        page_runs(client, owner, repo_name)
    elif page == "Jobs":
        page_jobs(client, owner, repo_name)
    elif page == "Analytics":
        page_analytics(client, owner, repo_name)
    elif page == "Performance":
        page_performance(client, owner, repo_name)
    elif page == "Self-Hosted Runners":
        page_runners(client, owner, repo_name, self_hosted=True)
    elif page == "GitHub Runners":
        page_runners(client, owner, repo_name, self_hosted=False)
    elif page == "Artifacts":
        page_artifacts(client, owner, repo_name)
    elif page == "Cache":
        page_cache(client, owner, repo_name)
    elif page == "Security":
        page_security(client, owner, repo_name)
    elif page == "Reports":
        page_reports(client, owner, repo_name)
    elif page == "API Monitor":
        page_api_monitor(client)
    elif page == "Settings":
        page_settings()
    else:
        st.info(f"Page **{page}** coming soon.")


if __name__ == "__main__":
    main()
