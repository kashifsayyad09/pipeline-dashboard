"""
GitHub Actions Analytics Dashboard
Enterprise-grade CI/CD observability platform
Built with Python + Streamlit + Plotly + GitHub REST & GraphQL APIs

Design system: Porcelain & Cobalt
  Background  #EDF1F5  -- porcelain, soft and neutral
  Primary     #0145F2  -- electric cobalt, the "signal" color
  Ink         #0B1B3A  -- near-black navy for headings/text
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

# --------------------------------------------------------------------------------
# CONFIG & CONSTANTS
# --------------------------------------------------------------------------------
load_dotenv()

PAGE_TITLE = "GitHub Actions Analytics"
GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

# -- Porcelain & Cobalt palette ----------------------------------------------
COLORS = {
    "primary":    "#0145F2",   # electric cobalt -- the signal color
    "primary_dk": "#0033B8",   # pressed/hover state of primary
    "secondary":  "#7C3AED",   # violet accent, used sparingly for contrast
    "bg":         "#EDF1F5",   # porcelain background
    "bg_alt":     "#E2E8F1",   # slightly deeper porcelain for stripes/wells
    "card":       "#FFFFFF",   # card surface -- pure white pops off porcelain
    "card2":      "#F7F9FC",   # secondary card surface (nested panels)
    "border":     "#D7DEE9",   # hairline border
    "text":       "#0B1B3A",   # ink -- primary text
    "white":      "#FFFFFF",
    "success":    "#0B9A6B",
    "warning":    "#B5790A",
    "danger":     "#D6304B",
    "muted":      "#5B6B85",   # slate -- secondary text
}

MDASH = "—"  # em-dash — safe to use in f-string expressions (no backslash needed)
PAGES = [
    ("home", "Dashboard"),
    ("folder", "Repositories"),
    ("workflow", "Workflows"),
    ("runs", "Workflow Runs"),
    ("jobs", "Jobs"),
    ("analytics", "Analytics"),
    ("perf", "Performance"),
    ("server", "Self-Hosted Runners"),
    ("cloud", "GitHub Runners"),
    ("artifact", "Artifacts"),
    ("cache", "Cache"),
    ("security", "Security"),
    ("reports", "Reports"),
    ("api", "API Monitor"),
    ("settings", "Settings"),
]

# Minimal inline SVG icon set -- flat, geometric, matches the type-led system
# instead of relying on emoji (which renders inconsistently across OSes and
# fights the chosen palette).
ICONS = {
    "home": '<svg viewBox="0 0 24 24" fill="none"><path d="M4 11.5 12 4l8 7.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10v9a1 1 0 0 0 1 1h3v-6h4v6h3a1 1 0 0 0 1-1v-9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "folder": '<svg viewBox="0 0 24 24" fill="none"><path d="M3 7a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "workflow": '<svg viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="2.3" stroke="currentColor" stroke-width="1.8"/><circle cx="18" cy="6" r="2.3" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="18" r="2.3" stroke="currentColor" stroke-width="1.8"/><path d="M8 7.2 12 16M16 7.2 12 16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "runs": '<svg viewBox="0 0 24 24" fill="none"><path d="M6 4v16l14-8L6 4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "jobs": '<svg viewBox="0 0 24 24" fill="none"><rect x="4" y="6" width="16" height="14" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M8 6V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1M4 11h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "analytics": '<svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "perf": '<svg viewBox="0 0 24 24" fill="none"><path d="M4 19h16M4 19 9 13l3 3 6-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "server": '<svg viewBox="0 0 24 24" fill="none"><rect x="4" y="4" width="16" height="6" rx="1.5" stroke="currentColor" stroke-width="1.8"/><rect x="4" y="14" width="16" height="6" rx="1.5" stroke="currentColor" stroke-width="1.8"/><circle cx="7.5" cy="7" r="0.9" fill="currentColor"/><circle cx="7.5" cy="17" r="0.9" fill="currentColor"/></svg>',
    "cloud": '<svg viewBox="0 0 24 24" fill="none"><path d="M7 18a4 4 0 1 1 .5-7.97A5.5 5.5 0 0 1 18 12.5 3.5 3.5 0 0 1 17.5 18H7Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "artifact": '<svg viewBox="0 0 24 24" fill="none"><path d="M3.5 7.5 12 3l8.5 4.5L12 12 3.5 7.5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M3.5 7.5V16l8.5 4.5L20.5 16V7.5M12 12v8.5" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "cache": '<svg viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="6" rx="8" ry="3" stroke="currentColor" stroke-width="1.8"/><path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" stroke="currentColor" stroke-width="1.8"/></svg>',
    "security": '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3 4.5 6v6c0 4.5 3 7.5 7.5 9 4.5-1.5 7.5-4.5 7.5-9V6L12 3Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "reports": '<svg viewBox="0 0 24 24" fill="none"><path d="M6 3h9l3 3v15a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9 12h6M9 16h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "api": '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3v4M12 17v4M3 12h4M17 12h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.8"/></svg>',
    "settings": '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.8"/><path d="M19.4 13.5a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.04 1.56V20a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.56-1.04H4a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.56-1.1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H10a1.7 1.7 0 0 0 1.04-1.56V4a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1.04 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V10a1.7 1.7 0 0 0 1.56 1.04H20a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1.04Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>',
}

# --------------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="\u26a1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------
# CSS -- design system, layout fixes, full animation language
# --------------------------------------------------------------------------------
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --primary:    {COLORS['primary']};
        --primary-dk: {COLORS['primary_dk']};
        --secondary:  {COLORS['secondary']};
        --bg:         {COLORS['bg']};
        --bg-alt:     {COLORS['bg_alt']};
        --card:       {COLORS['card']};
        --card2:      {COLORS['card2']};
        --border:     {COLORS['border']};
        --text:       {COLORS['text']};
        --success:    {COLORS['success']};
        --warning:    {COLORS['warning']};
        --danger:     {COLORS['danger']};
        --muted:      {COLORS['muted']};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        background-color: var(--bg);
        color: var(--text);
    }}

    h1, h2, h3, h4, .navbar-brand, .kpi-value, .section-header h3 {{
        font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    }}

    @keyframes fadeSlideUp {{
        from {{ opacity: 0; transform: translateY(14px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes pulseDot {{
        0%   {{ box-shadow: 0 0 0 0 rgba(11,154,107,0.55); }}
        70%  {{ box-shadow: 0 0 0 7px rgba(11,154,107,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(11,154,107,0); }}
    }}
    @keyframes pulseDotBlue {{
        0%   {{ box-shadow: 0 0 0 0 rgba(1,69,242,0.45); }}
        70%  {{ box-shadow: 0 0 0 8px rgba(1,69,242,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(1,69,242,0); }}
    }}
    @keyframes shimmer {{
        0%   {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}
    @keyframes growBar {{
        from {{ width: 0%; }}
    }}
    @keyframes railFlow {{
        0%   {{ background-position: 0% 0%; }}
        100% {{ background-position: 0% 200%; }}
    }}
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001ms !important;
        }}
    }}

    .main .block-container {{
        padding: 1.25rem 2.25rem 3rem;
        max-width: 100%;
        background-color: var(--bg);
    }}

    div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
    }}
    div[data-testid="column"] {{
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}

    section[data-testid="stSidebar"] {{
        background: var(--card);
        border-right: 1px solid var(--border);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        gap: 0.35rem;
    }}

    .sidebar-logo {{
        display: flex; align-items: center; gap: 0.6rem;
        padding: 1.1rem 0 0.9rem;
    }}
    .sidebar-logo-mark {{
        width: 34px; height: 34px; border-radius: 9px;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 4px 14px rgba(1,69,242,0.28);
        flex-shrink: 0;
    }}
    .sidebar-logo-mark svg {{ width: 18px; height: 18px; stroke: white; }}
    .sidebar-logo-text {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.05rem; font-weight: 700; color: var(--text);
        line-height: 1.15;
    }}
    .sidebar-logo-sub {{
        font-size: .68rem; color: var(--muted); margin-top: 1px;
        letter-spacing: .02em;
    }}

    .nav-rail {{
        position: relative;
        padding-left: 14px;
        margin: .4rem 0 .6rem;
    }}
    .nav-rail::before {{
        content: '';
        position: absolute; left: 4px; top: 2px; bottom: 2px;
        width: 2px; border-radius: 2px;
        background: linear-gradient(180deg,
            var(--primary) 0%, var(--secondary) 50%, var(--primary) 100%);
        background-size: 100% 200%;
        animation: railFlow 4s linear infinite;
        opacity: .55;
    }}

    .nav-eyebrow {{
        font-size: .64rem; color: var(--muted);
        text-transform: uppercase; letter-spacing: .12em;
        font-weight: 700; margin: 1rem 0 .5rem 2px;
    }}

    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent;
        color: var(--text) !important;
        border: 1px solid transparent;
        border-radius: 9px;
        font-weight: 500;
        font-size: .86rem;
        text-align: left;
        justify-content: flex-start;
        padding: .5rem .7rem;
        transition: background .15s ease, border-color .15s ease, transform .12s ease;
        box-shadow: none;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--bg-alt);
        transform: translateX(2px);
    }}
    section[data-testid="stSidebar"] .stButton > button:active {{
        transform: translateX(2px) scale(0.99);
    }}

    .nav-active button {{
        background: linear-gradient(90deg, rgba(1,69,242,0.10), rgba(1,69,242,0.02)) !important;
        border-color: rgba(1,69,242,0.25) !important;
        color: var(--primary) !important;
        font-weight: 700 !important;
    }}

    .navbar {{
        background: var(--card);
        border: 1px solid var(--border);
        padding: 0.85rem 1.5rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.6rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 1px 2px rgba(11,27,58,0.04);
        animation: fadeSlideUp .45s ease both;
    }}
    .navbar::after {{
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg,
            transparent, var(--primary), var(--secondary), var(--primary), transparent);
        background-size: 200% 100%;
        animation: shimmer 5s linear infinite;
    }}
    .navbar-brand {{
        display: flex; align-items: center; gap: 0.55rem;
        font-size: 1.08rem; font-weight: 700; color: var(--text) !important;
    }}
    .navbar-brand svg {{ width: 22px; height: 22px; }}
    .navbar-right {{
        display: flex; align-items: center; gap: 1.1rem; flex-wrap: wrap;
    }}
    .navbar-stat {{
        font-size: .76rem; font-weight: 600;
        display: flex; align-items: center; gap: .35rem;
    }}

    .kpi-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.15rem 1.3rem;
        position: relative;
        overflow: hidden;
        transition: transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s ease, border-color .2s ease;
        animation: fadeSlideUp .5s cubic-bezier(.2,.8,.2,1) both;
    }}
    .kpi-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 14px 28px -10px rgba(1,69,242,0.18);
        border-color: rgba(1,69,242,0.35);
    }}
    .kpi-card::before {{
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        opacity: 0; transition: opacity .2s ease;
    }}
    .kpi-card:hover::before {{ opacity: 1; }}
    .kpi-icon-wrap {{
        width: 34px; height: 34px; border-radius: 9px;
        background: rgba(1,69,242,0.08);
        display: flex; align-items: center; justify-content: center;
        margin-bottom: .6rem;
    }}
    .kpi-icon-wrap svg {{ width: 17px; height: 17px; stroke: var(--primary); }}
    .kpi-value {{
        font-size: 1.85rem; font-weight: 700; color: var(--text);
        line-height: 1.05; letter-spacing: -.01em;
    }}
    .kpi-label {{
        font-size: .73rem; color: var(--muted); font-weight: 600;
        text-transform: uppercase; letter-spacing: .07em; margin-top: .3rem;
    }}
    .kpi-delta {{
        font-size: .73rem; font-weight: 600; margin-top: .55rem;
        display: inline-flex; align-items: center; gap: .25rem;
        padding: .15rem .5rem; border-radius: 999px;
    }}
    .kpi-delta.up   {{ color: var(--success); background: rgba(11,154,107,0.10); }}
    .kpi-delta.down {{ color: var(--danger);  background: rgba(214,48,75,0.10); }}

    .section-header {{
        display: flex; align-items: center; gap: .6rem;
        margin: 1.75rem 0 1.1rem;
        animation: fadeSlideUp .4s ease both;
    }}
    .section-header .icn {{
        width: 26px; height: 26px; border-radius: 7px;
        background: rgba(1,69,242,0.08);
        display: flex; align-items: center; justify-content: center;
    }}
    .section-header .icn svg {{ width: 14px; height: 14px; stroke: var(--primary); }}
    .section-header h3 {{
        margin: 0; font-size: 1rem; font-weight: 700; color: var(--text);
        letter-spacing: -.005em;
    }}
    .section-header .rule {{
        flex: 1; height: 1px; background: var(--border);
    }}

    .pill {{
        display: inline-flex; align-items: center; gap: .3rem;
        padding: 3px 11px; border-radius: 999px;
        font-size: .71rem; font-weight: 700; letter-spacing: .02em;
        white-space: nowrap;
    }}
    .pill::before {{
        content: ''; width: 6px; height: 6px; border-radius: 50%;
        background: currentColor; flex-shrink: 0;
    }}
    .pill-success  {{ background: rgba(11,154,107,0.10);  color: var(--success); }}
    .pill-failure  {{ background: rgba(214,48,75,0.10);   color: var(--danger);  }}
    .pill-running  {{ background: rgba(1,69,242,0.10);    color: var(--primary); }}
    .pill-running::before {{ animation: pulseDotBlue 1.6s infinite; }}
    .pill-queued   {{ background: rgba(181,121,10,0.10);  color: var(--warning); }}
    .pill-skipped  {{ background: rgba(91,107,133,0.10);  color: var(--muted);   }}
    .pill-canceled {{ background: rgba(91,107,133,0.10);  color: var(--muted);   }}

    .table-wrap {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
        animation: fadeSlideUp .45s ease both;
    }}
    .modern-table {{
        width: 100%; border-collapse: collapse; font-size: .83rem;
    }}
    .modern-table th {{
        background: var(--card2);
        color: var(--muted);
        text-transform: uppercase;
        font-size: .68rem; font-weight: 700; letter-spacing: .07em;
        padding: .7rem .9rem;
        border-bottom: 1px solid var(--border);
        text-align: left; white-space: nowrap;
    }}
    .modern-table td {{
        padding: .65rem .9rem;
        border-bottom: 1px solid var(--bg-alt);
        color: var(--text);
        vertical-align: middle;
    }}
    .modern-table tr:last-child td {{ border-bottom: none; }}
    .modern-table tr {{ transition: background .12s ease; }}
    .modern-table tr:hover td {{ background: rgba(1,69,242,0.035); }}
    .modern-table a {{ color: var(--primary); text-decoration: none; font-weight: 600; }}
    .modern-table a:hover {{ text-decoration: underline; }}

    .chart-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: box-shadow .2s ease, border-color .2s ease;
        animation: fadeSlideUp .5s ease both;
    }}
    .chart-card:hover {{
        box-shadow: 0 10px 24px -12px rgba(11,27,58,0.12);
        border-color: rgba(1,69,242,0.18);
    }}

    .bar-track {{
        width: 100%; height: 7px; border-radius: 999px;
        background: var(--bg-alt); overflow: hidden;
    }}
    .bar-fill {{
        height: 100%; border-radius: 999px;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        animation: growBar 1s cubic-bezier(.2,.8,.2,1) both;
    }}

    .info-box, .warn-box, .error-box {{
        border-radius: 11px; padding: .8rem 1.05rem;
        font-size: .83rem; margin: .6rem 0;
        animation: fadeSlideUp .4s ease both;
        border: 1px solid;
    }}
    .info-box  {{ background: rgba(1,69,242,0.06);   border-color: rgba(1,69,242,0.18);  color: var(--text); }}
    .warn-box  {{ background: rgba(181,121,10,0.07); border-color: rgba(181,121,10,0.2); color: var(--text); }}
    .error-box {{ background: rgba(214,48,75,0.07);  border-color: rgba(214,48,75,0.2);  color: var(--text); }}

    .empty-state {{
        text-align: center; padding: 3.5rem 2rem; color: var(--muted);
        animation: fadeSlideUp .5s ease both;
    }}
    .empty-state .icon-wrap {{
        width: 56px; height: 56px; border-radius: 14px;
        background: rgba(1,69,242,0.07);
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 1rem;
        animation: fadeSlideUp .6s cubic-bezier(.2,.8,.2,1) both;
    }}
    .empty-state .icon-wrap svg {{ width: 26px; height: 26px; stroke: var(--primary); }}
    .empty-state h4 {{ color: var(--text); margin-bottom: .4rem; font-size: 1.1rem; }}

    .live-dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--success); display: inline-block;
        animation: pulseDot 1.8s infinite;
    }}

    .avatar {{
        width: 30px; height: 30px; border-radius: 50%;
        border: 2px solid var(--card);
        box-shadow: 0 0 0 1.5px var(--primary);
    }}

    div[data-testid="stMetric"] {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: .8rem 1.05rem;
        transition: box-shadow .2s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        box-shadow: 0 8px 18px -10px rgba(1,69,242,0.2);
    }}
    div[data-testid="stMetricValue"] {{ color: var(--text) !important; font-weight: 700; }}
    div[data-testid="stMetricLabel"] {{
        color: var(--muted) !important; font-size: .72rem;
        text-transform: uppercase; letter-spacing: .06em;
    }}

    .stSelectbox label, .stTextInput label, .stDateInput label {{
        color: var(--muted) !important; font-size: .72rem !important;
        text-transform: uppercase; letter-spacing: .06em; font-weight: 600;
    }}
    .stSelectbox > div > div, .stTextInput > div > div {{
        background: var(--card) !important;
        border-color: var(--border) !important;
        border-radius: 9px !important;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, var(--primary), var(--primary-dk));
        color: #fff;
        font-weight: 600;
        border: none;
        border-radius: 9px;
        transition: transform .15s ease, box-shadow .15s ease;
        box-shadow: 0 2px 8px rgba(1,69,242,0.22);
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(1,69,242,0.3);
    }}
    .stButton > button:active {{ transform: translateY(0); }}

    .stExpander {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }}

    .stTabs [data-baseweb="tab-list"] {{ gap: .3rem; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        color: var(--muted);
    }}

    code {{
        background: var(--bg-alt) !important;
        color: var(--primary) !important;
        border-radius: 5px;
    }}

    hr {{ border-color: var(--border) !important; }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 3rem;
    }}
    header[data-testid="stHeader"] * {{ visibility: hidden; }}
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarCollapseButton"] *,
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="stExpandSidebarButton"] * {{
        visibility: visible !important;
        opacity: 1 !important;
        display: flex !important;
        color: var(--primary) !important;
    }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    div[data-testid="column"]:nth-child(1) .kpi-card {{ animation-delay: .02s; }}
    div[data-testid="column"]:nth-child(2) .kpi-card {{ animation-delay: .07s; }}
    div[data-testid="column"]:nth-child(3) .kpi-card {{ animation-delay: .12s; }}
    div[data-testid="column"]:nth-child(4) .kpi-card {{ animation-delay: .17s; }}
    div[data-testid="column"]:nth-child(5) .kpi-card {{ animation-delay: .22s; }}

    ::-webkit-scrollbar {{ width: 7px; height: 7px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg-alt); }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--primary); }}
    </style>
    """, unsafe_allow_html=True)


# --------------------------------------------------------------------------------
# GITHUB API CLIENT  (unchanged -- already production-solid)
# --------------------------------------------------------------------------------
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

    def _get(self, path: str, params: dict = None):
        """GET request with error handling."""
        try:
            url = f"{self.base_url}{path}" if path.startswith("/") else path
            r = requests.get(url, headers=self._headers, params=params, timeout=15)
            if r.status_code == 401:
                st.error("Authentication failed. Check your GitHub token.")
                return None
            if r.status_code == 403:
                reset = r.headers.get("X-RateLimit-Reset", "unknown")
                st.warning(f"Rate limit hit. Resets at: {reset}")
                return None
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            st.error("Request timed out.")
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


# --------------------------------------------------------------------------------
# SESSION STATE HELPERS  (unchanged)
# --------------------------------------------------------------------------------
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
        "auto_auth_attempted": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_client():
    return st.session_state.get("client")


def clear_auth_session():
    """Reset all auth-related session state, forcing the Connect page."""
    st.session_state.token = ""
    st.session_state.client = None
    st.session_state.user = None
    st.session_state.orgs = []
    st.session_state.repos = []
    st.session_state.selected_repo = None
    st.session_state.selected_org = None
    st.session_state.selected_branch = None
    st.session_state.selected_workflow = None


def auto_authenticate():
    """
    Automatically authenticate using a token already present in
    st.session_state.token (sourced from .env at startup) -- without
    requiring the user to click Connect. Runs at most once per session.
    """
    if st.session_state.get("client") and st.session_state.get("user"):
        return
    if st.session_state.get("auto_auth_attempted"):
        return

    st.session_state.auto_auth_attempted = True

    token = st.session_state.get("token", "")
    if not token:
        return

    base_url = st.session_state.get("base_url", GITHUB_API)

    try:
        client = GitHubClient(token, base_url)
        user = client.get_user()

        if not user or not user.get("login"):
            clear_auth_session()
            return

        orgs = client.get_orgs()

        st.session_state.client = client
        st.session_state.user = user
        st.session_state.orgs = orgs or []

    except Exception:
        clear_auth_session()


# --------------------------------------------------------------------------------
# CACHED DATA FETCHERS  (unchanged -- TTL = 5 minutes)
# --------------------------------------------------------------------------------
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


# --------------------------------------------------------------------------------
# UTILITY FUNCTIONS  (unchanged)
# --------------------------------------------------------------------------------
def parse_iso(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def duration_str(seconds) -> str:
    if not seconds:
        return "\u2014"
    minutes, secs = divmod(int(seconds), 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    if mins:
        return f"{mins}m {secs}s"
    return f"{secs}s"

def run_duration_seconds(run: dict):
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


# --------------------------------------------------------------------------------
# PLOTLY CHART BUILDERS  (re-themed for light Porcelain & Cobalt surface)
# --------------------------------------------------------------------------------
def make_plotly(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="Inter, sans-serif", size=12),
        margin=dict(l=20, r=20, t=35, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"])
    fig.update_yaxes(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"])
    return fig

def pie_status(runs: list):
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
    colors = [label_map.get(l, "#888") for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.62,
        marker=dict(colors=colors, line=dict(color=COLORS["card"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
    ))
    fig.update_layout(
        title=dict(text="Run Status", font=dict(size=13, color=COLORS["text"])),
        showlegend=False,
    )
    return make_plotly(fig)

def daily_runs_chart(df: pd.DataFrame):
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
                                  font=dict(size=13, color=COLORS["text"])))
    return make_plotly(fig)

def duration_trend(df: pd.DataFrame):
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
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=5, color=COLORS["secondary"]),
        name="Duration (min)",
        fill="tozeroy",
        fillcolor="rgba(1,69,242,0.07)",
    ))
    fig.update_layout(
        title=dict(text="Build Duration Trend (minutes)",
                   font=dict(size=13, color=COLORS["text"])),
        xaxis_title="", yaxis_title="Minutes",
    )
    return make_plotly(fig)

def top_failed_workflows(df: pd.DataFrame):
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
                   font=dict(size=13, color=COLORS["text"])),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title="",
    )
    return make_plotly(fig)

def actor_leaderboard(df: pd.DataFrame):
    if df.empty:
        return go.Figure()
    top = df["Actor"].value_counts().head(10).reset_index()
    top.columns = ["Actor", "Runs"]
    fig = px.bar(top, x="Actor", y="Runs",
                  color_discrete_sequence=[COLORS["secondary"]])
    fig.update_layout(
        title=dict(text="Top Workflow Triggers",
                   font=dict(size=13, color=COLORS["text"])),
        xaxis_title="", yaxis_title="",
    )
    return make_plotly(fig)

def branch_chart(df: pd.DataFrame):
    if df.empty:
        return go.Figure()
    top = df["Branch"].value_counts().head(10).reset_index()
    top.columns = ["Branch", "Runs"]
    fig = px.pie(top, names="Branch", values="Runs", hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_layout(
        title=dict(text="Runs by Branch",
                   font=dict(size=13, color=COLORS["text"])),
    )
    return make_plotly(fig)

def success_rate_gauge(score: float):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number=dict(suffix="%", font=dict(color=COLORS["text"], size=36)),
        delta=dict(reference=80, increasing=dict(color=COLORS["success"]),
                   decreasing=dict(color=COLORS["danger"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=COLORS["muted"]),
            bar=dict(color=COLORS["primary"]),
            bgcolor=COLORS["bg_alt"],
            steps=[
                dict(range=[0, 50],  color="rgba(214,48,75,0.12)"),
                dict(range=[50, 80], color="rgba(181,121,10,0.12)"),
                dict(range=[80, 100],color="rgba(11,154,107,0.12)"),
            ],
            threshold=dict(line=dict(color=COLORS["warning"], width=3), value=80),
        ),
        title=dict(text="Success Rate", font=dict(color=COLORS["muted"], size=12)),
    ))
    fig.update_layout(height=220)
    return make_plotly(fig)

def runtime_dist(df: pd.DataFrame):
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
                   font=dict(size=13, color=COLORS["text"])),
        xaxis_title="Duration (min)", yaxis_title="Count",
    )
    return make_plotly(fig)

def runner_utilization(runners: list):
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
        title=dict(text="Runner Status", font=dict(size=13, color=COLORS["text"])),
        xaxis_title="", yaxis_title="Count",
    )
    return make_plotly(fig)


# --------------------------------------------------------------------------------
# UI COMPONENTS
# --------------------------------------------------------------------------------
def icon(name: str) -> str:
    return ICONS.get(name, "")

def kpi_card(icon_name: str, label: str, value, delta: str = None, delta_up: bool = True):
    delta_html = ""
    if delta:
        cls = "up" if delta_up else "down"
        arrow = "&#8593;" if delta_up else "&#8595;"
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {delta}</div>'
    return f"""
    <div class="kpi-card">
      <div class="kpi-icon-wrap">{icon(icon_name)}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
      {delta_html}
    </div>
    """

def section_header(icon_name: str, title: str):
    st.markdown(
        f'<div class="section-header"><div class="icn">{icon(icon_name)}</div>'
        f'<h3>{title}</h3><div class="rule"></div></div>',
        unsafe_allow_html=True,
    )

def render_navbar(user: dict, rl: dict):
    remaining = rl.get("remaining", "?")
    limit = rl.get("limit", "?")
    avatar = user.get("avatar_url", "")
    login = user.get("login", "")
    avatar_html = f'<img src="{avatar}" class="avatar" />' if avatar else ""
    try:
        pct = remaining / limit if limit not in ("?", 0, None) else 1
    except Exception:
        pct = 1
    rl_color = COLORS["success"] if pct > 0.3 else (COLORS["warning"] if pct > 0.1 else COLORS["danger"])

    st.markdown(f"""
    <div class="navbar">
      <div class="navbar-brand">
        <svg viewBox="0 0 16 16" fill="{COLORS['primary']}" aria-hidden="true">
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
        <span class="navbar-stat" style="color:{rl_color};">
          {icon('api')} {remaining}/{limit} API calls
        </span>
        <span class="navbar-stat" style="color:{COLORS['muted']};">
          {datetime.now().strftime('%H:%M:%S')}
        </span>
        {avatar_html}
        <span style="font-size:.82rem;font-weight:700;color:{COLORS['text']};">
          {login}
        </span>
        <span class="live-dot" title="Connected"></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    client = get_client()
    token = st.session_state.token

    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-logo">
          <div class="sidebar-logo-mark">
            <svg viewBox="0 0 24 24" fill="none"><path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z"
              stroke="white" stroke-width="1.8" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <div class="sidebar-logo-text">GH Analytics</div>
            <div class="sidebar-logo-sub">CI/CD Observability</div>
          </div>
        </div>
        <hr style="margin:.2rem 0 .75rem;" />
        """, unsafe_allow_html=True)

        # Token input
        if not st.session_state.token:
            st.markdown(f'<div style="font-size:.72rem;color:{COLORS["muted"]};'
                        'text-transform:uppercase;letter-spacing:.06em;'
                        'font-weight:600;margin-bottom:.3rem;">GitHub Token</div>',
                        unsafe_allow_html=True)
            tok = st.text_input("Token", type="password", label_visibility="collapsed",
                                 placeholder="ghp_... or github_pat_...",
                                 key="token_input")
            be = st.text_input("GitHub Enterprise URL (optional)", placeholder=GITHUB_API,
                                key="be_input", label_visibility="visible")
            if st.button("Connect", use_container_width=True):
                if tok:
                    st.session_state.token = tok
                    st.session_state.base_url = be or GITHUB_API
                    st.session_state.client = GitHubClient(tok, st.session_state.base_url)
                    with st.spinner("Authenticating..."):
                        user = st.session_state.client.get_user()
                        if user and user.get("login"):
                            st.session_state.user = user
                            orgs = st.session_state.client.get_orgs()
                            st.session_state.orgs = orgs
                            st.session_state.auto_auth_attempted = True
                            st.success(f"Connected as {user['login']}")
                            st.rerun()
                        else:
                            st.error("Authentication failed.")
                            clear_auth_session()
            return

        # Connected state
        if client:
            user = st.session_state.user or {}
            if user.get("avatar_url"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(user["avatar_url"], width=38)
                with col2:
                    st.markdown(f"""
                    <div style="font-size:.84rem;font-weight:700;color:{COLORS['text']};">
                      {user.get('login','')}
                    </div>
                    <div style="font-size:.7rem;color:{COLORS['muted']};">
                      {user.get('name','') or user.get('company','')}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('<hr style="margin:.6rem 0;" />', unsafe_allow_html=True)

            orgs = st.session_state.orgs
            org_names = [o["login"] for o in orgs]
            user_login = user.get("login", "")
            all_contexts = [user_login] + org_names
            selected_ctx = st.selectbox("Organization / User", all_contexts, key="ctx_sel")
            st.session_state.selected_org = None if selected_ctx == user_login else selected_ctx

            if "repos" not in st.session_state or not st.session_state.repos:
                with st.spinner("Loading repos..."):
                    repos = client.get_repos(st.session_state.selected_org)
                    st.session_state.repos = sorted(repos, key=lambda r: r.get("updated_at", ""), reverse=True)
            repos = st.session_state.repos
            repo_names = [r["full_name"] for r in repos]
            if repo_names:
                sel_repo = st.selectbox("Repository", ["\u2014 select \u2014"] + repo_names, key="repo_sel")
                st.session_state.selected_repo = sel_repo if sel_repo != "\u2014 select \u2014" else None
            else:
                st.info("No repositories found.")
                st.session_state.selected_repo = None

            if st.session_state.selected_repo:
                owner, repo_name = st.session_state.selected_repo.split("/", 1)
                branches = cached_branches(token, owner, repo_name)
                branch_names = [b["name"] for b in branches]
                sel_branch = st.selectbox("Branch", ["All"] + branch_names, key="branch_sel")
                st.session_state.selected_branch = None if sel_branch == "All" else sel_branch
            else:
                st.session_state.selected_branch = None

            st.markdown('<div class="nav-eyebrow">Navigation</div>', unsafe_allow_html=True)
            st.markdown('<div class="nav-rail">', unsafe_allow_html=True)
            for icon_name, name in PAGES:
                active = st.session_state.page == name
                wrap_class = "nav-active" if active else ""
                st.markdown(f'<div class="{wrap_class}">', unsafe_allow_html=True)
                if st.button(name, key=f"nav_{name}", use_container_width=True):
                    st.session_state.page = name
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<hr style="margin:.6rem 0;" />', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.session_state.last_refresh = datetime.now()
                    st.rerun()
            with col2:
                if st.button("Logout", use_container_width=True):
                    clear_auth_session()
                    st.session_state.auto_auth_attempted = True
                    st.rerun()


# --------------------------------------------------------------------------------
# PAGE RENDERERS
# --------------------------------------------------------------------------------
def page_not_connected():
    st.markdown(f"""
    <div class="empty-state" style="margin-top:4rem;">
      <div class="icon-wrap">{icon('home')}</div>
      <h4>GitHub Actions Analytics</h4>
      <p style="color:{COLORS['muted']};max-width:420px;margin:.5rem auto;">
        Connect your GitHub Personal Access Token in the sidebar to start
        monitoring CI/CD pipelines across your repositories.
      </p>
      <div class="info-box" style="max-width:420px;margin:1rem auto;text-align:left;">
        <strong>Required token scopes:</strong><br/>
        <code>repo</code> &middot; <code>workflow</code> &middot; <code>read:org</code> &middot; <code>read:user</code>
      </div>
    </div>
    """, unsafe_allow_html=True)


def page_no_repo():
    client = get_client()
    repos = st.session_state.get("repos", [])

    st.markdown(f"""
    <div class="empty-state" style="margin-top:2rem;">
      <div class="icon-wrap">{icon('folder')}</div>
      <h4>Select a Repository</h4>
      <p style="color:{COLORS['muted']};">
        Choose a repository below, or use the sidebar.
      </p>
    </div>
    """, unsafe_allow_html=True)

    if client and not repos:
        with st.spinner("Loading repositories..."):
            fetched = client.get_repos(st.session_state.get("selected_org"))
            st.session_state.repos = sorted(
                fetched, key=lambda r: r.get("updated_at", ""), reverse=True
            )
            repos = st.session_state.repos

    if repos:
        repo_names = [r["full_name"] for r in repos]
        c1, c2 = st.columns([3, 1])
        with c1:
            choice = st.selectbox(
                "Repository", ["\u2014 select \u2014"] + repo_names,
                key="inline_repo_sel", label_visibility="collapsed",
            )
        with c2:
            go = st.button("Open \u2192", use_container_width=True)
        if go and choice != "\u2014 select \u2014":
            st.session_state.selected_repo = choice
            st.rerun()
    else:
        st.markdown(
            f'<div class="warn-box" style="max-width:420px;margin:1rem auto;text-align:left;">'
            f'No repositories found for this account/organization. '
            f'Check that your token has <code>repo</code> scope.</div>',
            unsafe_allow_html=True,
        )


def page_dashboard(client, owner: str, repo: str):
    token = st.session_state.token
    branch = st.session_state.selected_branch

    with st.spinner("Loading dashboard data..."):
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

    section_header("home", "Overview")
    cols = st.columns(5)
    kpis = [
        ("runs",     "Total Runs",     total,            None, True),
        ("workflow", "Successful",     successful,       f"{score}% rate", score >= 80),
        ("security", "Failed",         failed,           None, False),
        ("perf",     "In Progress",    in_progress,      None, True),
        ("analytics","Avg Duration",   duration_str(avg_dur), None, True),
    ]
    for i, (icn, label, val, delta, up) in enumerate(kpis):
        with cols[i]:
            st.markdown(kpi_card(icn, label, val, delta, up), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    cols2 = st.columns(5)
    kpis2 = [
        ("jobs",     "Queued",         queued,           None, True),
        ("reports",  "Skipped",        skipped,          None, True),
        ("api",      "Cancelled",      cancelled,        None, False),
        ("artifact", "Artifacts",      len(artifacts),   fmt_bytes(artifact_size), True),
        ("server",   "Runners Online", f"{online_runners}/{len(runners)}", None, online_runners > 0),
    ]
    for i, (icn, label, val, delta, up) in enumerate(kpis2):
        with cols2[i]:
            st.markdown(kpi_card(icn, label, val, delta, up), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

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

    c4, c5 = st.columns(2)
    with c4:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(duration_trend(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(top_failed_workflows(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    c6, c7 = st.columns(2)
    with c6:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(actor_leaderboard(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c7:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(branch_chart(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    section_header("runs", "Recent Workflow Runs")
    render_runs_table(df.head(20))


def render_runs_table(df: pd.DataFrame):
    if df.empty:
        st.markdown(f'<div class="empty-state"><div class="icon-wrap">{icon("runs")}</div>'
                    '<h4>No workflow runs found</h4>'
                    '<p>Trigger a workflow or adjust your filters.</p></div>',
                    unsafe_allow_html=True)
        return

    rows_html = ""
    for _, row in df.iterrows():
        pill = status_pill(row["Status"], row["Conclusion"])
        rows_html += f"""
        <tr>
          <td><a href="{row.get('Run URL','#')}" target="_blank">#{row['Run ID']}</a></td>
          <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            {row['Workflow']}</td>
          <td><span style="color:{COLORS['secondary']};font-weight:600;">{row['Branch']}</span></td>
          <td>{row['Actor']}</td>
          <td>{pill}</td>
          <td>{row['Event']}</td>
          <td>{row['Started']}</td>
          <td>{row['Duration']}</td>
          <td style="font-family:monospace;font-size:.72rem;color:{COLORS['muted']};">
            {row['Commit']}</td>
        </tr>"""

    st.markdown(f"""
    <div class="table-wrap">
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr>
        <th>Run</th><th>Workflow</th><th>Branch</th><th>Actor</th>
        <th>Status</th><th>Event</th><th>Started</th><th>Duration</th><th>Commit</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    </div>
    """, unsafe_allow_html=True)


def page_repositories(client):
    section_header("folder", "Repositories")
    repos = st.session_state.repos
    if not repos:
        page_no_repo()
        return

    search = st.text_input("Search repositories", placeholder="Filter by name...", key="repo_search")
    if search:
        repos = [r for r in repos if search.lower() in r["full_name"].lower()]

    rows_html = ""
    for r in repos[:50]:
        vis_label = "Private" if r.get("private") else "Public"
        vis_pill_cls = "skipped" if r.get("private") else "success"
        upd = parse_iso(r.get("updated_at", ""))
        lang = r.get("language") or "\u2014"
        desc = (r.get("description") or "")[:70]
        rows_html += f"""
        <tr>
          <td style="min-width:240px;">
            <a href="{r.get('html_url','#')}" target="_blank" style="font-size:.86rem;">
              {r['full_name']}</a>
            <div style="font-size:.72rem;color:{COLORS['muted']};margin-top:2px;">{desc}</div>
          </td>
          <td><span style="color:{COLORS['warning']};font-weight:600;">\u2605 {r.get('stargazers_count',0)}</span></td>
          <td>{r.get('forks_count', 0)}</td>
          <td>{r.get('open_issues_count', 0)}</td>
          <td><span class="pill pill-{vis_pill_cls}">{vis_label}</span></td>
          <td><code style="font-size:.72rem;">{lang}</code></td>
          <td style="font-size:.74rem;color:{COLORS['muted']};white-space:nowrap;">
            {upd.strftime('%b %d, %Y') if upd else MDASH}</td>
        </tr>"""

    st.markdown(f"""
    <div class="table-wrap">
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr>
        <th>Repository</th><th>Stars</th><th>Forks</th><th>Issues</th>
        <th>Visibility</th><th>Language</th><th>Updated</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    </div>
    """, unsafe_allow_html=True)


def page_workflows(client, owner: str, repo: str):
    section_header("workflow", f"Workflows \u2014 {owner}/{repo}")
    token = st.session_state.token
    workflows = cached_workflows(token, owner, repo)

    if not workflows:
        st.markdown(f'<div class="empty-state"><div class="icon-wrap">{icon("workflow")}</div>'
                    '<h4>No workflows found</h4>'
                    '<p>This repository has no GitHub Actions workflows.</p></div>',
                    unsafe_allow_html=True)
        return

    for wf in workflows:
        state = wf.get("state", "\u2014")
        with st.expander(f"{wf.get('name','Unnamed')} \u2014 {wf.get('path','')}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("State", state.title())
            c2.metric("ID", wf.get("id", "\u2014"))
            c3.markdown(f'<a href="{wf.get("html_url","#")}" target="_blank" '
                        f'style="color:{COLORS["primary"]};font-weight:600;">View on GitHub \u2197</a>',
                        unsafe_allow_html=True)


def page_runs(client, owner: str, repo: str):
    section_header("runs", f"Workflow Runs \u2014 {owner}/{repo}")
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
    st.markdown(f'<div style="font-size:.8rem;color:{COLORS["muted"]};margin-bottom:.6rem;">'
                f'Showing {len(df)} runs</div>', unsafe_allow_html=True)
    render_runs_table(df)


def page_jobs(client, owner: str, repo: str):
    section_header("jobs", f"Jobs \u2014 {owner}/{repo}")
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
                f'<strong>#{run_id}</strong> \u2014 {recent_run.get("name","")}</div>',
                unsafe_allow_html=True)

    with st.spinner("Loading jobs..."):
        jobs = client.get_jobs(owner, repo, run_id)

    if not jobs:
        st.markdown(f'<div class="empty-state"><div class="icon-wrap">{icon("jobs")}</div>'
                    '<h4>No jobs found</h4></div>', unsafe_allow_html=True)
        return

    for job in jobs:
        started = parse_iso(job.get("started_at"))
        completed = parse_iso(job.get("completed_at"))
        dur = (completed - started).total_seconds() if started and completed and completed > started else None
        conclusion = job.get("conclusion") or job.get("status", "")
        pill = status_pill(job.get("status",""), job.get("conclusion"))

        with st.expander(f"{job.get('name','Job')} \u2014 {duration_str(dur)}", expanded=False):
            st.markdown(pill, unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Runner", job.get("runner_name") or "GitHub-hosted")
            c2.metric("OS", (job.get("runner_group_name") or job.get("labels",[""])[0] or "\u2014"))
            c3.metric("Duration", duration_str(dur))
            c4.metric("Status", conclusion.title() if conclusion else "\u2014")

            steps = job.get("steps", [])
            if steps:
                rows = ""
                for step in steps:
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
                <div class="table-wrap" style="margin-top:.6rem;">
                <table class="modern-table" style="font-size:.78rem;">
                  <thead><tr><th>#</th><th>Step</th><th>Status</th><th>Duration</th></tr></thead>
                  <tbody>{rows}</tbody>
                </table>
                </div>
                """, unsafe_allow_html=True)


def page_analytics(client, owner: str, repo: str):
    section_header("analytics", f"Analytics \u2014 {owner}/{repo}")
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


def page_performance(client, owner: str, repo: str):
    section_header("perf", f"Performance \u2014 {owner}/{repo}")
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
        ("perf",      "Avg Duration", duration_str(avg)),
        ("analytics", "Median",       duration_str(median)),
        ("api",       "P95 Runtime",  duration_str(p95)),
        ("runs",      "Fastest",      duration_str(fastest)),
        ("workflow",  "Slowest",      duration_str(slowest)),
    ]
    for i, (icn, label, val) in enumerate(stats):
        with cols[i]:
            st.markdown(kpi_card(icn, label, val), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(duration_trend(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(runtime_dist(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


def page_runners(client, owner: str, repo: str, self_hosted: bool = True):
    label = "Self-Hosted Runners" if self_hosted else "GitHub-Hosted Runners"
    icn = "server" if self_hosted else "cloud"
    section_header(icn, f"{label} \u2014 {owner}/{repo}")
    runners = cached_runners(st.session_state.token, owner, repo)

    if self_hosted:
        runners = [r for r in runners if not any(
            l.get("name","").startswith(("ubuntu-","macos-","windows-"))
            for l in r.get("labels", [])
        )]
    else:
        runners = [r for r in runners if any(
            l.get("name","").lower() in ["ubuntu-latest","macos-latest","windows-latest"]
            for l in r.get("labels", [])
        )]

    if not runners:
        st.markdown(f'<div class="empty-state"><div class="icon-wrap">{icon(icn)}</div>'
                    f'<h4>No {label.lower()} configured</h4>'
                    f'<p>Add runners in your repository settings.</p></div>',
                    unsafe_allow_html=True)
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

    online = sum(1 for r in runners if r.get("status") == "online")
    offline = len(runners) - online
    busy = sum(1 for r in runners if r.get("busy"))

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card("server", "Online", online), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("api", "Offline", offline), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("perf", "Busy", busy), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

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
            busy_s = "Busy" if r.get("busy") else "Idle"
            rows += f"""
            <tr>
              <td>{r.get('name','')}</td>
              <td><span class="pill pill-{scls}">{status}</span></td>
              <td>{busy_s}</td>
              <td style="font-size:.72rem;color:{COLORS['muted']};">{labels[:40]}</td>
              <td>{r.get('id','')}</td>
            </tr>"""
        st.markdown(f"""
        <div class="table-wrap">
        <div style="overflow-x:auto;">
        <table class="modern-table">
          <thead><tr><th>Runner</th><th>Status</th><th>Activity</th><th>Labels</th><th>ID</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        </div>
        </div>
        """, unsafe_allow_html=True)


def page_artifacts(client, owner: str, repo: str):
    section_header("artifact", f"Artifacts \u2014 {owner}/{repo}")
    token = st.session_state.token
    artifacts = cached_artifacts(token, owner, repo)

    if not artifacts:
        st.markdown(f'<div class="empty-state"><div class="icon-wrap">{icon("artifact")}</div>'
                    '<h4>No artifacts found</h4>'
                    '<p>Artifacts are generated by your workflows.</p></div>',
                    unsafe_allow_html=True)
        return

    total_size = sum(a.get("size_in_bytes", 0) for a in artifacts)
    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi_card("artifact", "Total Artifacts", len(artifacts)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("cache", "Total Storage", fmt_bytes(total_size)), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
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
          <td>{created.strftime('%Y-%m-%d') if created else MDASH}</td>
          <td>{expires.strftime('%Y-%m-%d') if expires else MDASH}</td>
          <td><span class="pill pill-{exp_class}">{'Expired' if expired else 'Active'}</span></td>
          <td>{a.get('id','')}</td>
        </tr>"""
    st.markdown(f"""
    <div class="table-wrap">
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr><th>Name</th><th>Size</th><th>Created</th><th>Expires</th><th>Status</th><th>ID</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    </div>
    """, unsafe_allow_html=True)


def page_cache(client, owner: str, repo: str):
    section_header("cache", f"Cache \u2014 {owner}/{repo}")
    token = st.session_state.token
    caches = cached_caches(token, owner, repo)

    if not caches:
        st.markdown(f'<div class="empty-state"><div class="icon-wrap">{icon("cache")}</div>'
                    '<h4>No caches found</h4>'
                    '<p>Workflow caches speed up your CI/CD pipelines.</p></div>',
                    unsafe_allow_html=True)
        return

    total_size = sum(c.get("size_in_bytes", 0) for c in caches)
    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi_card("cache", "Cache Entries", len(caches)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("artifact", "Total Size", fmt_bytes(total_size)), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    rows = ""
    for c in caches[:50]:
        last_accessed = parse_iso(c.get("last_accessed_at",""))
        created = parse_iso(c.get("created_at",""))
        rows += f"""
        <tr>
          <td><code style="font-size:.75rem;">{c.get('key','')}</code></td>
          <td>{c.get('ref','')}</td>
          <td>{fmt_bytes(c.get('size_in_bytes',0))}</td>
          <td>{created.strftime('%Y-%m-%d') if created else MDASH}</td>
          <td>{last_accessed.strftime('%Y-%m-%d') if last_accessed else MDASH}</td>
        </tr>"""
    st.markdown(f"""
    <div class="table-wrap">
    <div style="overflow-x:auto;">
    <table class="modern-table">
      <thead><tr><th>Key</th><th>Ref</th><th>Size</th><th>Created</th><th>Last Accessed</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    </div>
    """, unsafe_allow_html=True)


def page_security(client, owner: str, repo: str):
    section_header("security", f"Security \u2014 {owner}/{repo}")
    token = st.session_state.token
    secrets = cached_secrets(token, owner, repo)
    variables = client.get_variables(owner, repo)

    c1, c2 = st.columns(2)
    with c1: st.markdown(kpi_card("security", "Secrets", len(secrets)), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("settings", "Variables", len(variables)), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        section_header("security", "Repository Secrets")
        if secrets:
            rows = "".join(f"""
            <tr>
              <td>{s.get('name','')}</td>
              <td style="font-size:.72rem;color:{COLORS['muted']};">
                {parse_iso(s.get('updated_at','')).strftime('%Y-%m-%d') if parse_iso(s.get('updated_at','')) else MDASH}
              </td>
            </tr>""" for s in secrets)
            st.markdown(f"""
            <div class="table-wrap">
            <table class="modern-table">
              <thead><tr><th>Secret Name</th><th>Last Updated</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No secrets configured.</div>', unsafe_allow_html=True)

    with col2:
        section_header("settings", "Variables")
        if variables:
            rows = "".join(f"""
            <tr>
              <td>{v.get('name','')}</td>
              <td style="font-family:monospace;font-size:.75rem;">{str(v.get('value',''))[:40]}</td>
            </tr>""" for v in variables)
            st.markdown(f"""
            <div class="table-wrap">
            <table class="modern-table">
              <thead><tr><th>Variable</th><th>Value</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No variables configured.</div>', unsafe_allow_html=True)


def page_reports(client, owner: str, repo: str):
    section_header("reports", f"Reports \u2014 {owner}/{repo}")
    token = st.session_state.token

    st.markdown('<div class="info-box">Generate and export analytics reports for this repository.</div>',
                unsafe_allow_html=True)

    report_type = st.selectbox("Report Type", ["Workflow Runs", "Artifacts", "Performance Summary"])
    col1, col2 = st.columns(2)
    with col1:
        fmt = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])

    if st.button("Generate Report", use_container_width=False):
        with st.spinner("Generating report..."):
            runs = cached_runs(token, owner, repo)
            df = runs_to_df(runs)
            export_df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")

            if fmt == "CSV":
                data = export_df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", data, "gh_actions_report.csv", "text/csv")
            elif fmt == "JSON":
                data = export_df.to_json(orient="records", indent=2).encode("utf-8")
                st.download_button("Download JSON", data, "gh_actions_report.json", "application/json")
            elif fmt == "Excel":
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Workflow Runs")
                st.download_button("Download Excel", buf.getvalue(),
                                   "gh_actions_report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.success("Report ready for download!")


def page_api_monitor(client):
    section_header("api", "GitHub API Monitor")
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
    with c1: st.markdown(kpi_card("api", "API Limit", limit), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("workflow", "Remaining", remaining, None, pct_remaining > 20), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("analytics", "Used", used), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("perf", "Resets At",
                                   reset_dt.strftime("%H:%M UTC") if reset_dt else "\u2014"),
                          unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    fill_color = COLORS["success"] if pct_remaining > 50 else (COLORS["warning"] if pct_remaining > 20 else COLORS["danger"])
    st.markdown(f"""
    <div class="chart-card">
      <div style="font-size:.85rem;font-weight:700;color:{COLORS['text']};margin-bottom:.7rem;">
        API Rate Limit Utilization
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:{pct_used:.1f}%;background:linear-gradient(90deg,{fill_color},{COLORS['primary']});"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:.5rem;font-size:.78rem;color:{COLORS['muted']};">
        <span>{used} used</span><span>{remaining} remaining of {limit}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    fig = go.Figure(go.Bar(
        x=[used, remaining],
        y=["API Usage", "API Usage"],
        orientation="h",
        marker_color=[COLORS["danger"], COLORS["success"]],
        text=[f"Used: {used}", f"Remaining: {remaining}"],
        textposition="inside",
    ))
    fig.update_layout(
        title=dict(text="Usage Breakdown", font=dict(size=13, color=COLORS["text"])),
        barmode="stack", xaxis_range=[0, limit],
        height=120, margin=dict(l=20, r=20, t=40, b=20),
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(make_plotly(fig), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    if pct_remaining < 10:
        st.markdown(f'<div class="error-box">API rate limit critically low! '
                    f'Resets at {reset_dt.strftime("%H:%M UTC") if reset_dt else "unknown"}.</div>',
                    unsafe_allow_html=True)


def page_settings():
    section_header("settings", "Settings")
    user = st.session_state.get("user", {}) or {}
    token = st.session_state.token

    with st.expander("Account", expanded=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            if user.get("avatar_url"):
                st.image(user["avatar_url"], width=60)
        with c2:
            st.markdown(f"""
            **Login:** {user.get('login', MDASH)}  
            **Name:** {user.get('name', MDASH)}  
            **Company:** {user.get('company', MDASH)}  
            **Email:** {user.get('email', MDASH)}  
            """)

    with st.expander("Connection"):
        st.markdown(f"**API Endpoint:** `{st.session_state.get('base_url', GITHUB_API)}`")
        st.markdown(f"**Token:** `{'*' * 20}{token[-4:] if len(token) >= 4 else '****'}`")
        rl = cached_rate_limit(token)
        if rl:
            st.markdown(f"**Rate Limit:** {rl.get('remaining','?')}/{rl.get('limit','?')} remaining")

    with st.expander("About"):
        st.markdown("""
        **GitHub Actions Analytics Dashboard**  
        Enterprise-grade CI/CD observability platform  

        Built with: Python &middot; Streamlit &middot; Plotly &middot; GitHub REST & GraphQL APIs  
        Version: 2.0.0 -- Porcelain & Cobalt
        """)


# --------------------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------------------
def main():
    init_session()
    inject_css()
    auto_authenticate()
    render_sidebar()

    client = get_client()
    token  = st.session_state.token

    if client and token:
        user = st.session_state.user or {}
        rl   = cached_rate_limit(token)
        render_navbar(user, rl)

    if not token or not client:
        page_not_connected()
        return

    page = st.session_state.page

    repo_pages = {
        "Dashboard", "Workflows", "Workflow Runs", "Jobs", "Analytics",
        "Performance", "Self-Hosted Runners", "GitHub Runners",
        "Artifacts", "Cache", "Security", "Reports"
    }

    owner = repo_name = None
    if page in repo_pages:
        sel = st.session_state.selected_repo
        if not sel:
            page_no_repo()
            return
        owner, repo_name = sel.split("/", 1)

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
