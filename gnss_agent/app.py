# -*- coding: utf-8 -*-
"""
GNSS Multimodal Diagnostic Agent — Streamlit Dashboard
Assignment 4: Agents, Tool Use & Multimodal Extraction

Run:  streamlit run app.py
"""
import os
import sys
import json
import time
import base64
import pathlib

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image

# Add parent dir so imports work when running from gnss_agent/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SAMPLES_DIR, OUTPUTS_DIR, GEMINI_API_KEY, OPENROUTER_API_KEY, API_PROVIDER
from agent import GNSSDiagnosticAgent
from extractor import extract_from_image, compare_prompting_strategies
from validator import validate_extraction, compute_extraction_accuracy
from tools import get_tool_schemas
from report_generator import generate_report

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GNSS — Multimodal Diagnostic Agent",
    page_icon="🛰️",
    layout="wide",
)

# ─────────────────────────────────────────────
# Design tokens (matching Assignment 2 & 3)
# ─────────────────────────────────────────────
PLOT_BG = "#0D1B2A"
CARD_BG = "#142A3E"
GRID_COLOR = "#1E3A5F"
TEXT_COLOR = "#E0E7EE"
MUTED = "#6B7B8D"

CYAN = "#00BCD4"
GREEN = "#66BB6A"
AMBER = "#FFB74D"
CORAL = "#FF6B6B"
TEAL = "#009688"
BLUE = "#29B6F6"


def dark_layout(**kwargs):
    base = dict(
        paper_bgcolor=PLOT_BG, plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_COLOR, family="Calibri, sans-serif", size=13),
        legend=dict(bgcolor="rgba(20,42,62,0.85)", bordercolor=GRID_COLOR, borderwidth=1),
        margin=dict(l=60, r=30, t=50, b=50),
    )
    base.update(kwargs)
    return base


def dark_axes(fig):
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR)
    return fig


# ─────────────────────────────────────────────
# Logo helpers
# ─────────────────────────────────────────────
@st.cache_data
def _load_logo_b64(name, ext):
    p = pathlib.Path(__file__).parent / name
    if p.exists():
        mime = "png" if ext == "png" else "jpeg"
        return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    return ""


BEIHANG_LOGO = _load_logo_b64("university logo.png", "png")
RCSSTEAP_LOGO = _load_logo_b64("RCSSTEAP.jpg", "jpg")

# ─────────────────────────────────────────────
# Custom CSS (Dark Navy + Cyan, hover effects)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global dark theme ── */
    .stApp { background-color: #0D1B2A; }

    /* ── Animations ── */
    @keyframes breathe {
        0%, 100% { opacity: 0.75; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.03); }
    }
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 4px rgba(0,188,212,0.15); }
        50% { box-shadow: 0 0 14px rgba(0,188,212,0.45); }
    }
    @keyframes textShimmer {
        0%, 100% { opacity: 0.85; text-shadow: 0 0 0 transparent; }
        50% { opacity: 1; text-shadow: 0 0 8px rgba(0,188,212,0.3); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #142A3E; color: #E0E7EE; border-radius: 6px 6px 0 0;
        padding: 8px 16px; border: 1px solid #1E3A5F;
        transition: all 0.3s ease; animation: glowPulse 3s ease-in-out infinite;
    }
    .stTabs [data-baseweb="tab"]:nth-child(2) { animation-delay: 0.5s; }
    .stTabs [data-baseweb="tab"]:nth-child(3) { animation-delay: 1.0s; }
    .stTabs [data-baseweb="tab"]:nth-child(4) { animation-delay: 1.5s; }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #1A3A5A; border-color: #00BCD4;
        transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,188,212,0.25);
    }
    .stTabs [aria-selected="true"] {
        background-color: #0A2E50; border-bottom: 2px solid #00BCD4;
        box-shadow: 0 0 10px rgba(0,188,212,0.3);
    }

    /* ── Text colors ── */
    h1, h2, h3, .stMarkdown p, .stMarkdown li { color: #E0E7EE; }
    .stMetric label { color: #A0AEBB !important; }
    .stMetric [data-testid="stMetricValue"] { color: #E0E7EE !important; }

    /* ── Expander ── */
    div[data-testid="stExpander"] {
        background-color: #142A3E; border: 1px solid #1E3A5F; border-radius: 8px;
        transition: all 0.3s ease;
    }
    div[data-testid="stExpander"]:hover {
        border-color: #00BCD4; box-shadow: 0 4px 15px rgba(0,188,212,0.15);
    }

    /* ── Card system ── */
    .info-card, .warn-card, .danger-card, .success-card {
        border-radius: 10px; padding: 16px 20px; margin: 8px 0;
        transition: all 0.35s ease; cursor: default;
    }
    .info-card {
        background: linear-gradient(135deg, #142A3E, #1A354C);
        border: 1px solid #1E3A5F; border-left: 4px solid #00BCD4;
    }
    .info-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,188,212,0.25); border-color: #00BCD4; }
    .warn-card {
        background: linear-gradient(135deg, #2A1A0A, #3E250A);
        border: 1px solid #5C3A0A; border-left: 4px solid #FFB74D;
    }
    .warn-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(255,183,77,0.25); border-color: #FFB74D; }
    .danger-card {
        background: linear-gradient(135deg, #2A0A0A, #3E1515);
        border: 1px solid #5C1A1A; border-left: 4px solid #FF6B6B;
    }
    .danger-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(255,107,107,0.25); border-color: #FF6B6B; }
    .success-card {
        background: linear-gradient(135deg, #0A2A15, #0A3E20);
        border: 1px solid #0A5C2A; border-left: 4px solid #66BB6A;
    }
    .success-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(102,187,106,0.25); border-color: #66BB6A; }

    /* ── Metric hover ── */
    div[data-testid="stMetricValue"] { transition: all 0.3s ease; }
    div[data-testid="stMetric-container"]:hover div[data-testid="stMetricValue"] {
        transform: scale(1.08); text-shadow: 0 0 12px rgba(0,188,212,0.4);
    }
    div[data-testid="stMetric-container"] { transition: all 0.3s ease; border-radius: 8px; padding: 4px; }
    div[data-testid="stMetric-container"]:hover { background-color: rgba(20,42,62,0.6); }

    /* ── Plotly chart hover ── */
    div[data-testid="stPlotlyChart"] { transition: all 0.3s ease; border-radius: 8px; }
    div[data-testid="stPlotlyChart"]:hover { box-shadow: 0 4px 20px rgba(0,188,212,0.15); }

    /* ── DataFrame hover ── */
    div[data-testid="stDataFrame"] { transition: all 0.3s ease; }
    div[data-testid="stDataFrame"]:hover { box-shadow: 0 4px 16px rgba(0,188,212,0.15); }

    /* ── Landing page ── */
    .landing-container {
        background: linear-gradient(180deg, #0D1B2A 0%, #142A3E 50%, #0D1B2A 100%);
        border: 1px solid #1E3A5F; border-radius: 16px; padding: 35px 40px;
        text-align: center; margin-bottom: 1.5rem;
    }
    .landing-logos { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .landing-logos img { height: 72px; transition: transform 0.3s ease; }
    .landing-logos img:hover { transform: scale(1.08); }
    .landing-divider { height: 2px; background: linear-gradient(90deg, transparent, #00BCD4, transparent); margin: 18px auto; max-width: 400px; }
    .landing-title { font-size: 24px; font-weight: 700; color: #E0E7EE; margin: 8px 0 4px 0; }
    .landing-subtitle { font-size: 16px; font-weight: 600; color: #00BCD4; margin: 4px 0 8px 0; }
    .landing-info { font-size: 13px; color: #A0AEBB; margin: 2px 0; }
    .member-table { width: 100%; border-collapse: collapse; margin: 12px auto; max-width: 520px; }
    .member-table th { background-color: #0A2E50; color: #00BCD4; padding: 8px 14px; font-size: 13px; border: 1px solid #1E3A5F; }
    .member-table td { color: #E0E7EE; padding: 7px 14px; font-size: 13px; border: 1px solid #1E3A5F; background-color: #142A3E; transition: all 0.3s ease; }
    .member-table tr:hover td { background-color: #1A3A5A; }
    .brief-card {
        background: linear-gradient(135deg, #0A2E50, #142A3E); border: 1px solid #00BCD4;
        border-radius: 10px; padding: 14px 20px; margin: 15px auto 5px auto; max-width: 700px;
        text-align: left; transition: all 0.3s ease;
    }
    .brief-card:hover { box-shadow: 0 6px 20px rgba(0,188,212,0.2); transform: translateY(-2px); }
    .guide-text {
        font-size: 13px; font-weight: 600; margin: 4px 0 0 0; padding: 10px 20px;
        background: linear-gradient(90deg, #0A2E50, #142A3E, #0A2E50);
        background-size: 200% 100%; animation: gradientShift 4s ease infinite;
        border: 1px solid #00BCD4; border-radius: 8px; display: inline-block;
        color: #00BCD4; letter-spacing: 0.3px;
    }
    .guide-text span { color: #FFB74D; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1B2A 0%, #101E30 100%) !important;
    }
    section[data-testid="stSidebar"] * { color: #E0E7EE; }
    section[data-testid="stSidebar"] hr { border-color: #1E3A5F !important; }
    section[data-testid="stSidebar"] h2 { animation: textShimmer 3s ease-in-out infinite; }
    .sidebar-logo { animation: breathe 3.5s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
import config

with st.sidebar:
    if BEIHANG_LOGO:
        st.markdown(
            f'<div style="text-align:center;padding:10px 0 8px 0;">'
            f'<img class="sidebar-logo" src="{BEIHANG_LOGO}" style="height:55px;"/>'
            f'<p style="color:#00BCD4;font-size:10px;margin:6px 0 0 0;letter-spacing:0.5px;">'
            f'GNSS Diagnostic Agent</p></div>',
            unsafe_allow_html=True)
        st.divider()

    st.header("Model & API Controls")

    provider_options = ["ollama", "openrouter", "gemini"]
    provider_index = provider_options.index(API_PROVIDER) if API_PROVIDER in provider_options else 0
    provider = st.selectbox("API Provider", provider_options,
                            index=provider_index,
                            format_func=lambda x: {"ollama": "Ollama (Local \u2014 Free)",
                                                    "openrouter": "OpenRouter (Cloud \u2014 Free Tier)",
                                                    "gemini": "Gemini (Cloud)"}[x])
    config.API_PROVIDER = provider

    if provider == "ollama":
        st.markdown(f'<div class="success-card"><p class="card-title">\u2705 Running Locally</p>'
                    f'<p class="card-text">Vision: <b>{config.OLLAMA_VISION_MODEL}</b><br>'
                    f'Agent: <b>{config.OLLAMA_AGENT_MODEL}</b></p></div>', unsafe_allow_html=True)
        api_key = "ollama"
    elif provider == "openrouter":
        api_key = st.text_input("OpenRouter API Key", value=config.OPENROUTER_API_KEY, type="password")
        if api_key:
            os.environ["OPENROUTER_API_KEY"] = api_key
            config.OPENROUTER_API_KEY = api_key
    else:
        api_key = st.text_input("Gemini API Key", value=config.GEMINI_API_KEY, type="password")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            config.GEMINI_API_KEY = api_key

    st.divider()
    st.header("Tool Schemas")
    for schema in get_tool_schemas():
        with st.expander(f"\U0001f527 {schema['name']}"):
            st.markdown(f'<div class="info-card"><p class="card-text">{schema["description"]}</p></div>',
                        unsafe_allow_html=True)
            st.json(schema["parameters"])

    st.divider()
    st.markdown(
        '<p style="color:#A0AEBB;font-size:12px;text-align:center;">'
        'AI & Advanced Large Models<br>Sessions 9 + 10<br>'
        '<span style="color:#FFB74D;">GNSS in Degraded Environments</span></p>',
        unsafe_allow_html=True)

# ═════════════════════════════════════════════
# Landing Page
# ═════════════════════════════════════════════
_logo_left = f'<img src="{BEIHANG_LOGO}" alt="Beihang University"/>' if BEIHANG_LOGO else ""
_logo_right = f'<img src="{RCSSTEAP_LOGO}" alt="RCSSTEAP"/>' if RCSSTEAP_LOGO else ""

st.markdown(f"""
<div class="landing-container">
    <div class="landing-logos">
        {_logo_left}
        <div style="flex:1;"></div>
        {_logo_right}
    </div>
    <p class="landing-info" style="font-size:14px;color:#E0E7EE;margin:0;">Beihang University (BUAA)</p>
    <p class="landing-info">Regional Centre for Space Science and Technology Education<br>
    in Asia and the Pacific (China) &mdash; RCSSTEAP</p>
    <div class="landing-divider"></div>
    <p class="landing-info">Course: <b style="color:#E0E7EE;">Artificial Intelligence and Advanced Large Models</b> &nbsp;|&nbsp; Spring 2025</p>
    <p class="landing-title">Assignment 4 &mdash; Multimodal Agent Execution</p>
    <p class="landing-subtitle">GNSS Multimodal Diagnostic Agent &mdash; Agents, Tool Use &amp; Structured Extraction</p>
    <p class="landing-info" style="margin-top:6px;">Group 14</p>
    <table class="member-table">
        <tr><th>Name</th><th>Admission Number</th></tr>
        <tr><td>Granny Tlou Molokomme</td><td>LS2525256</td></tr>
        <tr><td>Letsoalo Maile</td><td>LS2525231</td></tr>
        <tr><td>Lemalasia Tevin Muchera</td><td>LS2525229</td></tr>
    </table>
    <div class="brief-card">
        <p style="color:#00BCD4;font-weight:600;margin:0 0 6px 0;">About This Dashboard</p>
        <p style="color:#E0E7EE;font-size:13px;margin:0;line-height:1.6;">
        This interactive dashboard demonstrates a <b style="color:#29B6F6;">multimodal AI agent</b> that
        processes GNSS engineering diagrams (sky plots, DOP tables, signal strength charts) using
        <b style="color:#29B6F6;">vision-based structured extraction</b> and reasons over the data through
        a <b style="color:#29B6F6;">ReAct (Reason + Act) tool-calling loop</b>. The agent identifies
        positioning quality degradation, assesses risk levels, and generates actionable diagnostic
        recommendations for improving GNSS reliability in challenging environments.</p>
    </div>
    <div class="landing-divider"></div>
    <p class="guide-text">Use the <span>sidebar controls</span> to select your API provider and explore the <span>interactive tabs</span> below.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "\U0001f4e5 Input & Extraction",
    "\U0001f916 Agent Execution",
    "\U0001f4ca Diagnostic Report",
    "\U0001f4c8 Evaluation",
])

# Helper: track available images across tabs
if "available_images" not in st.session_state:
    # Auto-detect samples on first load
    sample_files = {
        "sky_plot": os.path.join(SAMPLES_DIR, "sky_plot.png"),
        "dop_table": os.path.join(SAMPLES_DIR, "dop_table.png"),
        "cn0_chart": os.path.join(SAMPLES_DIR, "cn0_chart.png"),
    }
    st.session_state["available_images"] = {k: v for k, v in sample_files.items() if os.path.exists(v)}

available_images = st.session_state["available_images"]

# ═════════════════════════════════════════════
# TAB 1 — Input & Extraction
# ═════════════════════════════════════════════
with tab1:
    st.subheader("GNSS Engineering Diagrams")

    col1, col2 = st.columns([1, 1])
    with col1:
        input_mode = st.radio("Input Source", ["Use Sample Diagrams", "Upload Custom"])

    if input_mode == "Use Sample Diagrams":
        sample_files = {
            "sky_plot": os.path.join(SAMPLES_DIR, "sky_plot.png"),
            "dop_table": os.path.join(SAMPLES_DIR, "dop_table.png"),
            "cn0_chart": os.path.join(SAMPLES_DIR, "cn0_chart.png"),
        }
        all_exist = all(os.path.exists(p) for p in sample_files.values())
        if all_exist:
            st.markdown('<div class="success-card"><p class="card-title">\u2705 Sample diagrams loaded</p>'
                        '<p class="card-text">3 GNSS engineering visuals ready for extraction.</p></div>',
                        unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (dtype, path) in enumerate(sample_files.items()):
                with cols[i]:
                    st.caption(dtype.replace("_", " ").title())
                    st.image(path, width="stretch")
                    available_images[dtype] = path
        else:
            st.markdown('<div class="warn-card"><p class="card-title">\u26a0 Samples not found</p>'
                        '<p class="card-text">Run <code>py generate_samples.py</code> first.</p></div>',
                        unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-card"><p class="card-text">Upload your own GNSS diagrams:</p></div>',
                    unsafe_allow_html=True)
        upload_cols = st.columns(3)
        for i, dtype in enumerate(["sky_plot", "dop_table", "cn0_chart"]):
            with upload_cols[i]:
                uploaded = st.file_uploader(f"Upload {dtype.replace('_',' ').title()}",
                                           type=["png", "jpg", "jpeg"], key=dtype)
                if uploaded:
                    save_path = os.path.join(SAMPLES_DIR, f"custom_{dtype}.png")
                    img = Image.open(uploaded)
                    img.save(save_path)
                    available_images[dtype] = save_path
                    st.image(save_path, width="stretch")

    # ── Single Extraction ──────────────────────────────────────────
    st.divider()
    st.subheader("Multimodal Extraction (Session 10)")

    if available_images:
        ex_col1, ex_col2 = st.columns([1, 2])
        with ex_col1:
            selected_type = st.selectbox("Diagram", list(available_images.keys()),
                                         format_func=lambda x: x.replace("_", " ").title())
            prompting_mode = st.radio("Prompting Strategy", ["few_shot", "zero_shot"],
                                      format_func=lambda x: x.replace("_", " ").title())
        with ex_col2:
            model_name = {"ollama": config.OLLAMA_VISION_MODEL, "openrouter": config.OPENROUTER_MODEL,
                          "gemini": config.GEMINI_MODEL}.get(config.API_PROVIDER, "unknown")
            st.markdown(f'<div class="info-card"><p class="card-text">Provider: <b style="color:#29B6F6;">'
                        f'{config.API_PROVIDER}</b> &nbsp;|&nbsp; Vision model: <b style="color:#29B6F6;">'
                        f'{model_name}</b></p></div>', unsafe_allow_html=True)

            if st.button("\U0001f50d Extract Data", type="primary", width="stretch"):
                if not api_key:
                    st.error("Enter API key in sidebar.")
                else:
                    try:
                        with st.spinner(f"Extracting from {selected_type}..."):
                            result = extract_from_image(available_images[selected_type],
                                                       selected_type, prompting=prompting_mode)
                    except Exception as e:
                        st.error(f"API Error: {e}")
                        st.stop()

                    st.session_state["last_extraction"] = result
                    st.markdown(f'<div class="success-card"><p class="card-title">\u2705 Extraction complete '
                                f'in {result["latency_seconds"]}s</p></div>', unsafe_allow_html=True)
                    st.json(result["extracted_data"])

                    validation = validate_extraction(result["extracted_data"], selected_type)
                    if validation["is_valid"]:
                        st.markdown(f'<div class="success-card"><p class="card-text">'
                                    f'Validation: PASSED | Confidence: {validation["stats"].get("confidence", "N/A")}'
                                    f'</p></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="danger-card"><p class="card-text">'
                                    f'Validation: FAILED \u2014 {", ".join(validation["errors"])}'
                                    f'</p></div>', unsafe_allow_html=True)
                    for w in validation.get("warnings", []):
                        st.markdown(f'<div class="warn-card"><p class="card-text">{w}</p></div>',
                                    unsafe_allow_html=True)

                    gt_path = os.path.join(SAMPLES_DIR, "ground_truth.json")
                    if os.path.exists(gt_path):
                        with open(gt_path) as f:
                            gt = json.load(f)
                        accuracy = compute_extraction_accuracy(result["extracted_data"], gt, selected_type)
                        with st.expander("Accuracy vs Ground Truth"):
                            st.json(accuracy)

    # ── Prompting Comparison ───────────────────────────────────────
    st.divider()
    st.subheader("Prompting Strategy Comparison (Session 10)")
    st.markdown('<div class="info-card"><p class="card-text">Compare <b style="color:#29B6F6;">zero-shot</b> '
                'vs <b style="color:#29B6F6;">few-shot</b> extraction side-by-side. Few-shot includes '
                'domain-specific GNSS examples for improved accuracy.</p></div>', unsafe_allow_html=True)

    if available_images:
        compare_type = st.selectbox("Diagram to compare", list(available_images.keys()),
                                     format_func=lambda x: x.replace("_", " ").title(), key="compare_type")
        if st.button("\u2696\ufe0f Run Comparison", width="stretch"):
            if not api_key:
                st.error("Enter API key in sidebar.")
            else:
                try:
                    with st.spinner("Running zero-shot..."):
                        zero_r = extract_from_image(available_images[compare_type], compare_type, prompting="zero_shot")
                    with st.spinner("Running few-shot..."):
                        few_r = extract_from_image(available_images[compare_type], compare_type, prompting="few_shot")
                except Exception as e:
                    st.error(f"Comparison failed: {e}")
                    st.stop()

                st.session_state["comparison_result"] = {"zero_shot": zero_r, "few_shot": few_r}
                zv = validate_extraction(zero_r["extracted_data"], compare_type)
                fv = validate_extraction(few_r["extracted_data"], compare_type)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p style="color:#CYAN;font-weight:700;font-size:16px;">Zero-Shot</p>',
                                unsafe_allow_html=True)
                    st.caption(f"Latency: {zero_r['latency_seconds']}s")
                    st.json(zero_r["extracted_data"])
                    card = "success-card" if zv["is_valid"] else "danger-card"
                    st.markdown(f'<div class="{card}"><p class="card-text">'
                                f'Valid: {"Yes" if zv["is_valid"] else "No"} | '
                                f'Errors: {len(zv["errors"])} | Warnings: {len(zv["warnings"])}'
                                f'</p></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<p style="color:#66BB6A;font-weight:700;font-size:16px;">Few-Shot</p>',
                                unsafe_allow_html=True)
                    st.caption(f"Latency: {few_r['latency_seconds']}s")
                    st.json(few_r["extracted_data"])
                    card = "success-card" if fv["is_valid"] else "danger-card"
                    st.markdown(f'<div class="{card}"><p class="card-text">'
                                f'Valid: {"Yes" if fv["is_valid"] else "No"} | '
                                f'Errors: {len(fv["errors"])} | Warnings: {len(fv["warnings"])}'
                                f'</p></div>', unsafe_allow_html=True)

                # Comparison chart
                fig_cmp = go.Figure()
                fig_cmp.add_bar(name="Zero-Shot", x=["Latency (s)", "Errors", "Warnings"],
                                y=[zero_r["latency_seconds"], len(zv["errors"]), len(zv["warnings"])],
                                marker_color=CORAL)
                fig_cmp.add_bar(name="Few-Shot", x=["Latency (s)", "Errors", "Warnings"],
                                y=[few_r["latency_seconds"], len(fv["errors"]), len(fv["warnings"])],
                                marker_color=GREEN)
                fig_cmp.update_layout(**dark_layout(title_text="Zero-Shot vs Few-Shot Comparison",
                                                    barmode="group", height=350))
                dark_axes(fig_cmp)
                st.plotly_chart(fig_cmp, width="stretch")

# ═════════════════════════════════════════════
# TAB 2 — Agent Execution
# ═════════════════════════════════════════════
with tab2:
    st.subheader("ReAct Agent Execution (Session 9)")

    st.markdown("""<div class="info-card">
    <p class="card-title">\U0001f916 Agent Workflow</p>
    <p class="card-text">
    1. <b style="color:#29B6F6;">Extract</b> structured data from all GNSS diagrams (multimodal vision)<br>
    2. <b style="color:#FFB74D;">Analyze</b> positioning quality (satellite geometry, DOP, signal strength)<br>
    3. <b style="color:#66BB6A;">Report</b> diagnostic findings with risk assessment and recommendations
    </p></div>""", unsafe_allow_html=True)

    task_input = st.text_area(
        "Diagnostic Task",
        value=("Perform a comprehensive GNSS positioning quality diagnostic for "
               "station BUAA-REF on 2026-04-11. Analyze the satellite geometry, "
               "signal strength, and DOP values to identify any degraded periods "
               "or risk factors. Provide actionable recommendations for improving "
               "positioning reliability in this environment."),
        height=100)

    if st.button("\U0001f680 Run Diagnostic Agent", type="primary", width="stretch"):
        if not api_key:
            st.error("Enter API key in sidebar.")
        elif not available_images:
            st.error("No diagrams. Go to Tab 1 first.")
        else:
            st.markdown(f'<div class="info-card"><p class="card-text">Starting agent with '
                        f'{len(available_images)} diagrams...</p></div>', unsafe_allow_html=True)
            progress = st.progress(0)
            agent = GNSSDiagnosticAgent()
            result = agent.run(task_input, available_images)
            st.session_state["agent_result"] = result
            progress.progress(100)

            # Trace display
            st.subheader("Agent Trace (Thought \u2192 Action \u2192 Observation)")
            for step in result["trace"]:
                tool = step["action"].get("tool", "N/A") if isinstance(step["action"], dict) else "N/A"
                with st.expander(f"Step {step['iteration']}: {tool} ({step['latency_seconds']}s)", expanded=True):
                    st.markdown(f'<div class="info-card"><p class="card-title">\U0001f4ad Thought</p>'
                                f'<p class="card-text">{str(step["thought"])[:500]}</p></div>',
                                unsafe_allow_html=True)
                    if isinstance(step["action"], dict):
                        st.code(json.dumps(step["action"], indent=2), language="json")
                    obs = step.get("observation", "")
                    if isinstance(obs, dict):
                        obs_str = json.dumps(obs, indent=2, default=str)
                        if len(obs_str) > 1500:
                            with st.expander("Full observation"):
                                st.json(obs)
                        else:
                            st.json(obs)
                    else:
                        st.write(obs)

            # Metrics
            metrics = result["metrics"]
            mcols = st.columns(4)
            mcols[0].metric("Iterations", metrics["total_iterations"])
            mcols[1].metric("Total Time", f"{metrics['total_time_seconds']}s")
            mcols[2].metric("Avg Step", f"{metrics['avg_step_time_seconds']}s")
            mcols[3].metric("Success", "\u2705" if metrics["success"] else "\u274c")

# ═════════════════════════════════════════════
# TAB 3 — Diagnostic Report
# ═════════════════════════════════════════════
with tab3:
    st.subheader("GNSS Diagnostic Report")

    if "agent_result" in st.session_state:
        result = st.session_state["agent_result"]
        memory = result.get("memory", {})
        report_data = memory.get("report", {})

        if report_data and "report" in report_data:
            report = report_data["report"]

            # Risk level
            risk = report.get("risk_level", "unknown")
            risk_card = {"low": "success-card", "moderate": "warn-card",
                         "high": "danger-card", "critical": "danger-card"}.get(risk, "info-card")
            st.markdown(f'<div class="{risk_card}"><p class="card-title">Risk Level: {risk.upper()}</p>'
                        f'<p class="card-text">{report.get("executive_summary", "")}</p></div>',
                        unsafe_allow_html=True)

            # Extraction summary metrics
            ext_s = report.get("extraction_summary", {})
            ecols = st.columns(3)
            ecols[0].metric("Diagrams Processed", ext_s.get("total_diagrams_processed", 0))
            ecols[1].metric("Successful", ext_s.get("successful_extractions", 0))
            ecols[2].metric("Success Rate", ext_s.get("extraction_success_rate", "N/A"))

            # Findings
            st.markdown("#### Detailed Findings")
            for f in report.get("detailed_findings", []):
                if "CRITICAL" in str(f):
                    st.markdown(f'<div class="danger-card"><p class="card-text">{f}</p></div>',
                                unsafe_allow_html=True)
                elif "WARNING" in str(f):
                    st.markdown(f'<div class="warn-card"><p class="card-text">{f}</p></div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="info-card"><p class="card-text">{f}</p></div>',
                                unsafe_allow_html=True)

            # Recommendations
            st.markdown("#### Recommendations")
            for r in report.get("recommendations", []):
                st.markdown(f'<div class="success-card"><p class="card-text">\U0001f4a1 {r}</p></div>',
                            unsafe_allow_html=True)

            # Interactive visualizations
            st.markdown("#### Interactive Visualizations")
            viz_c1, viz_c2 = st.columns(2)

            with viz_c1:
                dop_data = memory.get("dop_data")
                if dop_data and isinstance(dop_data, dict) and "epochs" in dop_data:
                    dop_df = pd.DataFrame(dop_data["epochs"])
                    dop_cols = [c for c in ["gdop", "pdop", "hdop", "vdop"] if c in dop_df.columns]
                    if dop_cols and "time" in dop_df.columns:
                        fig_dop = go.Figure()
                        colors = [CYAN, BLUE, GREEN, AMBER]
                        for i, col in enumerate(dop_cols):
                            fig_dop.add_scatter(x=dop_df["time"], y=dop_df[col].astype(float),
                                                mode="lines+markers", name=col.upper(),
                                                line=dict(color=colors[i % len(colors)], width=2),
                                                marker=dict(size=6))
                        fig_dop.add_hline(y=5, line_dash="dash", line_color=AMBER,
                                          annotation_text="Good/Moderate", annotation_font_color=AMBER)
                        fig_dop.update_layout(**dark_layout(title_text="DOP Values Over Time", height=400,
                                                           hovermode="x unified"))
                        dark_axes(fig_dop)
                        st.plotly_chart(fig_dop, width="stretch")

            with viz_c2:
                sat_data = memory.get("satellite_data")
                if sat_data and isinstance(sat_data, dict) and "satellites" in sat_data:
                    sats = sat_data["satellites"]
                    sat_df = pd.DataFrame(sats)
                    if "azimuth_deg" in sat_df.columns and "elevation_deg" in sat_df.columns:
                        sat_df["r"] = 90 - sat_df["elevation_deg"].astype(float)
                        cn0_col = "cn0_dbhz" if "cn0_dbhz" in sat_df.columns else "cn0"
                        sat_df["cn0_val"] = sat_df[cn0_col].astype(float) if cn0_col in sat_df.columns else 35
                        sat_df["quality"] = sat_df["cn0_val"].apply(
                            lambda x: "Strong" if x >= 40 else ("Moderate" if x >= 30 else "Weak"))
                        color_map = {"Strong": GREEN, "Moderate": AMBER, "Weak": CORAL}
                        fig_sky = px.scatter_polar(
                            sat_df, r="r", theta="azimuth_deg", color="quality",
                            color_discrete_map=color_map, hover_name="prn",
                            hover_data={"elevation_deg": True, "cn0_val": True, "r": False},
                            size="cn0_val", size_max=18)
                        fig_sky.update_layout(
                            **dark_layout(title_text="Satellite Sky Plot", height=400),
                            polar=dict(
                                bgcolor=CARD_BG,
                                radialaxis=dict(range=[0, 90], gridcolor=GRID_COLOR, color=TEXT_COLOR,
                                                tickvals=[0,15,30,45,60,75,90],
                                                ticktext=["90\u00b0","75\u00b0","60\u00b0","45\u00b0","30\u00b0","15\u00b0","0\u00b0"]),
                                angularaxis=dict(direction="clockwise", rotation=90, gridcolor=GRID_COLOR,
                                                 color=TEXT_COLOR),
                            ))
                        st.plotly_chart(fig_sky, width="stretch")

            # Save / PDF buttons
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("\U0001f4be Save Report as JSON", width="stretch"):
                    os.makedirs(OUTPUTS_DIR, exist_ok=True)
                    rp = os.path.join(OUTPUTS_DIR, "diagnostic_report.json")
                    with open(rp, "w") as f:
                        json.dump(result, f, indent=2, default=str)
                    st.success(f"Saved: {rp}")
            with sc2:
                if st.button("\U0001f4c4 Generate PDF Report", width="stretch"):
                    with st.spinner("Generating PDF..."):
                        try:
                            pdf_path = generate_report(result)
                            st.success(f"PDF: {pdf_path}")
                            with open(pdf_path, "rb") as pf:
                                st.download_button("\u2b07\ufe0f Download PDF", data=pf.read(),
                                                   file_name="GNSS_Diagnostic_Report.pdf",
                                                   mime="application/pdf")
                        except Exception as e:
                            st.error(f"PDF failed: {e}")
        else:
            st.markdown('<div class="info-card"><p class="card-text">No report yet. '
                        'Run the agent in Tab 2 first.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-card"><p class="card-text">No report yet. '
                    'Run the agent in Tab 2 first.</p></div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════
# TAB 4 — Evaluation
# ═════════════════════════════════════════════
with tab4:
    st.subheader("Evaluation & Metrics")

    if "agent_result" in st.session_state:
        result = st.session_state["agent_result"]
        metrics = result["metrics"]
        memory = result.get("memory", {})

        # Performance metrics
        pcols = st.columns(4)
        pcols[0].metric("Total Iterations", metrics["total_iterations"])
        pcols[1].metric("Total Time", f"{metrics['total_time_seconds']}s")
        pcols[2].metric("Avg Step Time", f"{metrics['avg_step_time_seconds']}s")
        pcols[3].metric("Task Success", "\u2705 Yes" if metrics["success"] else "\u274c No")

        # Tool usage chart — Plotly dark
        tool_calls = metrics.get("tools_called", [])
        if tool_calls:
            tool_counts = {}
            for t in tool_calls:
                tool_counts[t] = tool_counts.get(t, 0) + 1
            fig_tools = go.Figure(go.Bar(
                x=list(tool_counts.keys()), y=list(tool_counts.values()),
                marker_color=[CYAN, AMBER, GREEN, CORAL, BLUE][:len(tool_counts)],
                marker_line=dict(color="white", width=1),
                text=list(tool_counts.values()), textposition="outside",
                textfont=dict(color=TEXT_COLOR)))
            fig_tools.update_layout(**dark_layout(title_text="Tool Usage", height=350, showlegend=False))
            dark_axes(fig_tools)
            st.plotly_chart(fig_tools, width="stretch")

        # Extraction accuracy
        extraction_results = memory.get("extraction_results", [])
        if extraction_results:
            st.markdown("#### Extraction Accuracy")
            for i, ext in enumerate(extraction_results):
                acc = ext.get("accuracy")
                if acc:
                    dtype = ext.get("extracted_data", {}).get("diagram_type", f"Diagram {i+1}")
                    with st.expander(f"Accuracy: {dtype}"):
                        st.json(acc)

        # Latency — Plotly dark
        trace = result.get("trace", [])
        if trace:
            step_labels = [f"Step {s['iteration']}" for s in trace]
            step_lat = [s["latency_seconds"] for s in trace]
            step_tools = [s["action"].get("tool", "N/A") if isinstance(s.get("action"), dict) else "N/A" for s in trace]
            fig_lat = go.Figure(go.Bar(
                x=step_labels, y=step_lat, marker_color=CYAN,
                marker_line=dict(color="white", width=1),
                text=[f"{l}s" for l in step_lat], textposition="outside",
                textfont=dict(color=TEXT_COLOR),
                hovertext=[f"Tool: {t}" for t in step_tools], hoverinfo="text+y"))
            fig_lat.update_layout(**dark_layout(title_text="Latency Per Step", height=350))
            dark_axes(fig_lat)
            st.plotly_chart(fig_lat, width="stretch")

        # ── Failure Analysis ──────────────────────────────────────
        st.markdown("#### Failure Analysis")
        failures = []
        for ext in extraction_results:
            if not ext.get("success"):
                err = ext.get("error", ext.get("validation", {}).get("errors", ["Unknown"]))
                failures.append({"Stage": "Extraction", "Detail": str(err),
                                 "Impact": "Missing data for analysis"})
            val = ext.get("validation", {})
            for w in val.get("warnings", []):
                failures.append({"Stage": "Validation", "Detail": w,
                                 "Impact": "May need human review"})
        for step in trace:
            obs = step.get("observation", {})
            if isinstance(obs, dict) and obs.get("error"):
                failures.append({"Stage": f"Agent Step {step['iteration']}", "Detail": obs["error"],
                                 "Impact": "Tool execution failure"})

        if failures:
            st.dataframe(pd.DataFrame(failures), width="stretch", hide_index=True)
        else:
            st.markdown('<div class="success-card"><p class="card-text">\u2705 No failures detected '
                        '\u2014 clean execution!</p></div>', unsafe_allow_html=True)

        # ── Course Concept Alignment ──────────────────────────────
        st.markdown("#### Course Concept Alignment")
        alignment = pd.DataFrame({
            "Course Concept": [
                "Agent Architecture (Perceive/Reason/Act/Observe)", "Tool Calling with JSON Schemas",
                "ReAct Pattern (Thought/Action/Observation)", "Guardrails & Failure Handling",
                "Multimodal Input Processing", "Structured Extraction to JSON",
                "Few-Shot Prompting for Extraction", "Post-Processing & Validation",
                "Evaluation Metrics", "Failure Mode Awareness",
            ],
            "Session": ["9", "9", "9", "9", "10", "10", "10", "10", "9+10", "9+10"],
            "Implementation": [
                "agent.py \u2014 core ReAct loop with memory",
                "tools.py \u2014 3 tools with full JSON schemas",
                "Agent trace (Tab 2) \u2014 logged at every step",
                "agent.py \u2014 max iterations, confidence thresholds, retry",
                "extractor.py \u2014 Vision API for 3 diagram types",
                "extractor.py + validator.py \u2014 structured JSON output",
                "extractor.py \u2014 GNSS domain examples in prompts",
                "validator.py \u2014 schema, range, type coercion checks",
                "This tab \u2014 iterations, latency, accuracy",
                "Failure analysis section above",
            ]})
        st.dataframe(alignment, width="stretch", hide_index=True)

        with st.expander("Full Agent Trace (JSON)"):
            st.json(result["trace"])

    else:
        st.markdown('<div class="info-card"><p class="card-text">Run the agent first to see metrics.</p></div>',
                    unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    '<p style="color:#6B7B8D;font-size:12px;text-align:center;">'
    'Assignment 4 \u2014 AI & Advanced Large Models | '
    'Multimodal GNSS Diagnostic Agent | '
    'Sessions 9 (Agents) + 10 (Multimodal) | '
    'All sample data synthetic/mock.</p>',
    unsafe_allow_html=True)
