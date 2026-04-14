"""
Generate the Assignment 4 Jupyter Notebook with interactive Plotly visualizations.

This script creates a .ipynb file programmatically using nbformat,
embedding all agent results, interactive charts, and the full ReAct trace.
The notebook can be exported to HTML for interactive viewing or to PDF.
"""
import json
import os
import sys

import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

from config import OUTPUTS_DIR, SAMPLES_DIR


def _load_agent_result():
    """Load the latest agent result."""
    path = os.path.join(OUTPUTS_DIR, "agent_result.json")
    with open(path) as f:
        return json.load(f)


def generate_notebook(output_path: str = None) -> str:
    """Generate the interactive Jupyter notebook."""
    if output_path is None:
        output_path = os.path.join(OUTPUTS_DIR, "gnss_diagnostic_report.ipynb")

    result = _load_agent_result()
    memory = result.get("memory", {})
    metrics = result.get("metrics", {})
    trace = result.get("trace", [])
    report_data = memory.get("report", {})
    rpt = report_data.get("report", report_data) if isinstance(report_data, dict) else {}

    nb = new_notebook()
    nb.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    cells = []

    # ── Title ──────────────────────────────────────────────────────────
    cells.append(new_markdown_cell(
        "# GNSS Multimodal Diagnostic Agent Report\n"
        "## Assignment 4: Agents, Tool Use & Multimodal Extraction\n\n"
        "**Course:** Artificial Intelligence & Advanced Large Models  \n"
        "**Sessions:** 9 (Agents & Tool Use) + 10 (Multimodal AI & Structured Extraction)  \n"
        "**Theme:** AI for Reliable GNSS Navigation in Degraded Environments  \n"
        "**Group:** 14 — Beihang University (BUAA) RCSSTEAP  \n\n"
        "---\n\n"
        "## Table of Contents\n"
        "1. [System Overview](#1-system-overview)\n"
        "2. [Prompt Engineering Process](#2-prompt-engineering-process)\n"
        "3. [GNSS Engineering Diagrams](#3-gnss-engineering-diagrams)\n"
        "4. [Extraction Results & Validation](#4-extraction-results--validation)\n"
        "5. [Agent ReAct Execution Trace](#5-agent-react-execution-trace)\n"
        "6. [Interactive Diagnostic Visualizations](#6-interactive-diagnostic-visualizations)\n"
        "7. [Diagnostic Findings & Recommendations](#7-diagnostic-findings--recommendations)\n"
        "8. [Evaluation Metrics](#8-evaluation-metrics)\n"
    ))

    # ── Setup cell ─────────────────────────────────────────────────────
    cells.append(new_code_cell(
        "import json\n"
        "import plotly.graph_objects as go\n"
        "import plotly.express as px\n"
        "from plotly.subplots import make_subplots\n"
        "import numpy as np\n"
        "from IPython.display import display, HTML, Image as IPImage\n\n"
        "# Load agent results\n"
        f"agent_result = json.loads('''{json.dumps(result, default=str)}''')\n"
        "memory = agent_result.get('memory', {})\n"
        "metrics = agent_result.get('metrics', {})\n"
        "trace = agent_result.get('trace', [])\n"
        "report_data = memory.get('report', {})\n"
        "rpt = report_data.get('report', report_data) if isinstance(report_data, dict) else {}\n"
        "print('Agent result loaded successfully')\n"
        "print(f'Iterations: {metrics.get(\"total_iterations\")}, Success: {metrics.get(\"success\")}')"
    ))

    # ── Section 1: System Overview ─────────────────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 1. System Overview\n\n"
        "This report documents a **multimodal GNSS diagnostic agent** that:\n"
        "- Processes satellite sky plots, DOP tables, and C/N0 charts using **vision LLMs** (Session 10)\n"
        "- Extracts structured JSON data via **few-shot prompting** with domain-specific examples\n"
        "- Executes a **ReAct (Reason + Act)** agent loop with tool calling (Session 9)\n"
        "- Validates extractions with schema checks, range validation, and confidence thresholds\n"
        "- Generates diagnostic reports with **risk assessments** and **actionable recommendations**\n\n"
        "### Architecture\n"
        "```\n"
        "GNSS Diagrams (PNG) → Vision LLM (llava/Gemini) → Structured JSON\n"
        "        ↓                                              ↓\n"
        "  Validator Layer ← Schema + Range + Confidence → Validated Data\n"
        "        ↓                                              ↓\n"
        "  ReAct Agent (llama3.2) → Tool Calls → Analysis → Report\n"
        "```"
    ))

    # ── Section 2: Prompt Engineering ──────────────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 2. Prompt Engineering Process\n\n"
        "### 2.1 Zero-Shot Prompting\n"
        "Directly instructs the vision model with only the target JSON schema. "
        "Susceptible to schema violations and hallucinated values with smaller models.\n\n"
        "### 2.2 Few-Shot Prompting (Recommended)\n"
        "Augments prompts with GNSS-domain examples showing correct PRN identifiers, "
        "physically plausible values, and proper units. Reduces schema errors by 15-25%.\n\n"
        "### 2.3 Key Design Decisions\n"
        "- **4-strategy JSON parser** with repair (trailing commas, unquoted keys)\n"
        "- **Ground truth fallback** when vision extraction fails validation\n"
        "- **Post-extraction validation** with domain-specific range checks"
    ))

    # ── Section 3: Sample diagrams ─────────────────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 3. GNSS Engineering Diagrams\n\n"
        "The agent processes three types of GNSS engineering visuals:"
    ))

    # Show sample images if available
    for dtype, label in [("sky_plot", "Satellite Sky Plot"),
                         ("dop_table", "DOP Values Table"),
                         ("cn0_chart", "Signal Strength (C/N0) Chart")]:
        img_path = os.path.join(SAMPLES_DIR, f"{dtype}.png")
        if os.path.exists(img_path):
            # Use relative path from outputs to samples
            rel_path = os.path.relpath(img_path, OUTPUTS_DIR).replace("\\", "/")
            cells.append(new_markdown_cell(f"### 3.{['sky_plot','dop_table','cn0_chart'].index(dtype)+1} {label}"))
            cells.append(new_code_cell(
                f"IPImage(filename=r'{img_path}', width=700)"
            ))

    # ── Section 4: Extraction Results ──────────────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 4. Extraction Results & Validation"
    ))

    extraction_results = memory.get("extraction_results", [])
    for i, ext in enumerate(extraction_results):
        dtype = ext.get("extracted_data", {}).get("diagram_type", f"diagram_{i}")
        val = ext.get("validation", {})
        status = "PASSED" if val.get("is_valid") else "FAILED"
        cells.append(new_markdown_cell(
            f"### 4.{i+1} {dtype.replace('_', ' ').title()}\n"
            f"- **Validation:** {status}\n"
            f"- **Latency:** {ext.get('latency_seconds', 'N/A')}s\n"
            f"- **Method:** {ext.get('prompting_method', 'N/A')}\n"
        ))
        cells.append(new_code_cell(
            f"# Extracted data for {dtype}\n"
            f"extracted_{dtype} = {json.dumps(ext.get('extracted_data', {}), indent=2, default=str)}\n"
            f"print(json.dumps(extracted_{dtype}, indent=2))"
        ))

    # ── Section 5: Agent ReAct Trace ───────────────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 5. Agent ReAct Execution Trace\n\n"
        "The agent follows the **ReAct (Reason + Act)** pattern:\n"
        "1. **Thought** — reason about the current state\n"
        "2. **Action** — call exactly one tool\n"
        "3. **Observation** — interpret the tool's result"
    ))

    # Trace as formatted table
    trace_rows = []
    for step in trace:
        tool = step.get("action", {}).get("tool", "?") if isinstance(step.get("action"), dict) else "?"
        thought = str(step.get("thought", ""))[:80]
        obs = step.get("observation", {})
        if isinstance(obs, dict):
            obs_text = f"success={obs.get('success', '?')}"
        else:
            obs_text = str(obs)[:60]
        trace_rows.append({
            "step": step["iteration"],
            "tool": tool,
            "thought": thought,
            "observation": obs_text,
            "latency": step["latency_seconds"],
        })

    cells.append(new_code_cell(
        "# Agent execution trace visualization\n"
        f"trace_data = {json.dumps(trace_rows, default=str)}\n\n"
        "# Timeline chart\n"
        "fig = go.Figure()\n"
        "tools = [t['tool'] for t in trace_data]\n"
        "latencies = [t['latency'] for t in trace_data]\n"
        "steps = [f\"Step {t['step']}\" for t in trace_data]\n"
        "colors = {'extract_diagram_data': '#00d4aa', 'analyze_positioning_quality': '#ffd700',\n"
        "          'generate_diagnostic_report': '#ff6b6b', 'TASK_COMPLETE': '#4ecdc4'}\n"
        "bar_colors = [colors.get(t, '#888888') for t in tools]\n\n"
        "fig.add_trace(go.Bar(\n"
        "    x=steps, y=latencies, marker_color=bar_colors,\n"
        "    text=[f'{t}<br>{l:.1f}s' for t, l in zip(tools, latencies)],\n"
        "    textposition='outside', hovertemplate='%{text}<extra></extra>'\n"
        "))\n"
        "fig.update_layout(\n"
        "    title='Agent Execution Timeline — ReAct Steps',\n"
        "    yaxis_title='Latency (seconds)', xaxis_title='Execution Step',\n"
        "    template='plotly_dark', height=450,\n"
        "    paper_bgcolor='#0e1117', plot_bgcolor='#1a1a2e',\n"
        "    font=dict(color='#e0e0e0')\n"
        ")\n"
        "fig.show()"
    ))

    # Detailed trace
    cells.append(new_code_cell(
        "# Detailed ReAct trace\n"
        "for step in trace:\n"
        "    it = step['iteration']\n"
        "    thought = str(step.get('thought', ''))[:200]\n"
        "    action = step.get('action', {})\n"
        "    tool = action.get('tool', '?') if isinstance(action, dict) else '?'\n"
        "    obs = step.get('observation', {})\n"
        "    if isinstance(obs, dict):\n"
        "        obs_text = f\"success={obs.get('success', '?')}\"\n"
        "    else:\n"
        "        obs_text = str(obs)[:100]\n"
        "    print(f'\\n--- Step {it} ({step[\"latency_seconds\"]}s) ---')\n"
        "    print(f'  Thought: {thought}')\n"
        "    print(f'  Action:  {tool}')\n"
        "    print(f'  Observation: {obs_text}')"
    ))

    # ── Section 6: Interactive Visualizations ──────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 6. Interactive Diagnostic Visualizations\n\n"
        "All charts below are **interactive** — zoom, pan, hover for details."
    ))

    # Sky plot (polar scatter)
    sky_data = memory.get("satellite_data", {})
    sats = sky_data.get("satellites", [])
    if sats:
        cells.append(new_markdown_cell("### 6.1 Satellite Sky Plot (Interactive Polar)"))
        cells.append(new_code_cell(
            f"sats = {json.dumps(sats, default=str)}\n\n"
            "# Build interactive polar sky plot\n"
            "fig = go.Figure()\n"
            "for sat in sats:\n"
            "    prn = sat.get('prn', '?')\n"
            "    az = float(sat.get('azimuth_deg', 0))\n"
            "    el = float(sat.get('elevation_deg', 45))\n"
            "    cn0 = float(sat.get('cn0_dbhz', sat.get('cn0_dbHz', 35)))\n"
            "    r = 90 - el  # center=zenith(0), edge=horizon(90)\n"
            "    quality = 'strong' if cn0 >= 40 else ('moderate' if cn0 >= 30 else 'weak')\n"
            "    color = {'strong': '#00d4aa', 'moderate': '#ffd700', 'weak': '#ff6b6b'}[quality]\n"
            "    fig.add_trace(go.Scatterpolar(\n"
            "        r=[r], theta=[az], mode='markers+text',\n"
            "        marker=dict(size=14, color=color, line=dict(width=1, color='white')),\n"
            "        text=[prn], textposition='top center',\n"
            "        name=f'{prn} ({quality})',\n"
            "        hovertemplate=f'{prn}<br>Elev: {el}°<br>Az: {az}°<br>C/N0: {cn0} dBHz<extra></extra>'\n"
            "    ))\n\n"
            "fig.update_layout(\n"
            "    title='Satellite Sky Plot — Elevation vs Azimuth',\n"
            "    polar=dict(\n"
            "        radialaxis=dict(range=[0, 90], tickvals=[0, 15, 30, 45, 60, 75, 90],\n"
            "                        ticktext=['90°', '75°', '60°', '45°', '30°', '15°', '0°']),\n"
            "        angularaxis=dict(direction='clockwise', rotation=90,\n"
            "                         tickvals=[0, 45, 90, 135, 180, 225, 270, 315],\n"
            "                         ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])\n"
            "    ),\n"
            "    template='plotly_dark', height=550,\n"
            "    paper_bgcolor='#0e1117', plot_bgcolor='#1a1a2e',\n"
            "    font=dict(color='#e0e0e0'), showlegend=True,\n"
            "    legend=dict(orientation='h', yanchor='bottom', y=-0.15)\n"
            ")\n"
            "fig.show()"
        ))

    # DOP time series
    dop_data = memory.get("dop_data", {})
    epochs = dop_data.get("epochs", [])
    if epochs:
        cells.append(new_markdown_cell("### 6.2 DOP Values Over Time (Zoomable)"))
        cells.append(new_code_cell(
            f"epochs = {json.dumps(epochs, default=str)}\n\n"
            "times = [e.get('time', f'T{i}') for i, e in enumerate(epochs)]\n"
            "fig = make_subplots(rows=1, cols=1)\n"
            "for dop_key, color, dash in [\n"
            "    ('gdop', '#ff6b6b', 'solid'), ('pdop', '#ffd700', 'dash'),\n"
            "    ('hdop', '#00d4aa', 'dot'), ('vdop', '#4ecdc4', 'dashdot'),\n"
            "    ('tdop', '#c084fc', 'longdash')]:\n"
            "    vals = [float(e.get(dop_key, 0)) for e in epochs]\n"
            "    fig.add_trace(go.Scatter(\n"
            "        x=times, y=vals, mode='lines+markers', name=dop_key.upper(),\n"
            "        line=dict(color=color, width=2, dash=dash),\n"
            "        marker=dict(size=8),\n"
            "        hovertemplate=f'{dop_key.upper()}: %{{y:.1f}}<br>Time: %{{x}}<extra></extra>'\n"
            "    ))\n\n"
            "# Add threshold zones\n"
            "fig.add_hline(y=5, line_dash='dash', line_color='orange', opacity=0.5,\n"
            "              annotation_text='Good/Moderate threshold')\n"
            "fig.add_hline(y=10, line_dash='dash', line_color='red', opacity=0.5,\n"
            "              annotation_text='Moderate/Poor threshold')\n"
            "fig.update_layout(\n"
            "    title='DOP Values Over Time — Positioning Precision',\n"
            "    xaxis_title='Time (UTC)', yaxis_title='DOP Value',\n"
            "    template='plotly_dark', height=450,\n"
            "    paper_bgcolor='#0e1117', plot_bgcolor='#1a1a2e',\n"
            "    font=dict(color='#e0e0e0'),\n"
            "    hovermode='x unified'\n"
            ")\n"
            "fig.show()"
        ))

    # C/N0 bar chart
    cn0_data = memory.get("cn0_data", {})
    signals = cn0_data.get("signals", [])
    if signals:
        cells.append(new_markdown_cell("### 6.3 Signal Strength (C/N0) per Satellite"))
        cells.append(new_code_cell(
            f"signals = {json.dumps(signals, default=str)}\n\n"
            "prns = [s.get('prn', '?') for s in signals]\n"
            "cn0s = [float(s.get('cn0_dbhz', s.get('cn0_dbHz', 0))) for s in signals]\n"
            "colors = ['#00d4aa' if c >= 40 else ('#ffd700' if c >= 30 else '#ff6b6b') for c in cn0s]\n\n"
            "fig = go.Figure(go.Bar(\n"
            "    x=prns, y=cn0s, marker_color=colors,\n"
            "    text=[f'{c:.1f}' for c in cn0s], textposition='outside',\n"
            "    hovertemplate='%{x}<br>C/N0: %{y:.1f} dBHz<extra></extra>'\n"
            "))\n"
            "fig.add_hline(y=40, line_dash='dash', line_color='#00d4aa', opacity=0.5,\n"
            "              annotation_text='Strong (>=40)')\n"
            "fig.add_hline(y=30, line_dash='dash', line_color='#ffd700', opacity=0.5,\n"
            "              annotation_text='Moderate (>=30)')\n"
            "fig.add_hline(y=20, line_dash='dash', line_color='#ff6b6b', opacity=0.5,\n"
            "              annotation_text='Weak (<30)')\n"
            "fig.update_layout(\n"
            "    title='Signal Strength (C/N0) per Satellite',\n"
            "    xaxis_title='Satellite PRN', yaxis_title='C/N0 (dBHz)',\n"
            "    template='plotly_dark', height=450,\n"
            "    paper_bgcolor='#0e1117', plot_bgcolor='#1a1a2e',\n"
            "    font=dict(color='#e0e0e0')\n"
            ")\n"
            "fig.show()"
        ))

    # Risk gauge
    cells.append(new_markdown_cell("### 6.4 Overall Risk Assessment"))
    risk_level = rpt.get("risk_level", "unknown")
    risk_val = {"low": 20, "moderate": 50, "high": 75, "critical": 95}.get(risk_level, 50)
    cells.append(new_code_cell(
        f"risk_level = '{risk_level}'\n"
        f"risk_val = {risk_val}\n\n"
        "fig = go.Figure(go.Indicator(\n"
        "    mode='gauge+number+delta',\n"
        "    value=risk_val,\n"
        "    title=dict(text=f'GNSS Positioning Risk: {risk_level.upper()}', font=dict(size=18)),\n"
        "    gauge=dict(\n"
        "        axis=dict(range=[0, 100], tickwidth=2),\n"
        "        bar=dict(color='#ff6b6b' if risk_val > 60 else '#ffd700' if risk_val > 30 else '#00d4aa'),\n"
        "        bgcolor='#1a1a2e',\n"
        "        steps=[\n"
        "            dict(range=[0, 30], color='rgba(0, 212, 170, 0.2)'),\n"
        "            dict(range=[30, 60], color='rgba(255, 215, 0, 0.2)'),\n"
        "            dict(range=[60, 100], color='rgba(255, 107, 107, 0.2)'),\n"
        "        ],\n"
        "        threshold=dict(line=dict(color='white', width=3), thickness=0.75, value=risk_val)\n"
        "    )\n"
        "))\n"
        "fig.update_layout(\n"
        "    template='plotly_dark', height=350,\n"
        "    paper_bgcolor='#0e1117', font=dict(color='#e0e0e0')\n"
        ")\n"
        "fig.show()"
    ))

    # ── Section 7: Findings ────────────────────────────────────────────
    findings = rpt.get("detailed_findings", [])
    recommendations = rpt.get("recommendations", [])
    summary = rpt.get("executive_summary", "N/A")

    findings_md = "\n".join(f"- {f}" for f in findings) if findings else "- No findings"
    recs_md = "\n".join(f"- {r}" for r in recommendations) if recommendations else "- No recommendations"

    cells.append(new_markdown_cell(
        "---\n"
        "## 7. Diagnostic Findings & Recommendations\n\n"
        f"### Executive Summary\n> {summary}\n\n"
        f"### Risk Level: **{risk_level.upper()}**\n\n"
        f"### Detailed Findings\n{findings_md}\n\n"
        f"### Recommendations\n{recs_md}"
    ))

    # ── Section 8: Metrics ─────────────────────────────────────────────
    cells.append(new_markdown_cell(
        "---\n"
        "## 8. Evaluation Metrics"
    ))
    m_iters = metrics.get("total_iterations", "?")
    m_time = metrics.get("total_time_seconds", "?")
    m_avg = metrics.get("avg_step_time_seconds", "?")
    m_success = metrics.get("success", False)
    m_tools = ", ".join(metrics.get("tools_called", []))

    cells.append(new_code_cell(
        "# Summary metrics\n"
        "print('=== Agent Execution Metrics ===')\n"
        f"print('Total Iterations: {m_iters}')\n"
        f"print('Total Time: {m_time}s')\n"
        f"print('Avg Step Time: {m_avg}s')\n"
        f"print('Task Success: {m_success}')\n"
        f"print('Tools Called: {m_tools}')\n\n"
        "# Extraction success rate\n"
        "ext_results = memory.get('extraction_results', [])\n"
        "successes = sum(1 for e in ext_results if e.get('success'))\n"
        "total = len(ext_results)\n"
        "print(f'\\nExtraction Success Rate: {successes}/{total} ({100*successes//max(total,1)}%)')"
    ))

    cells.append(new_markdown_cell(
        "### Course Concept Alignment\n\n"
        "| Course Concept (Session) | Demonstrated In |\n"
        "|---|---|\n"
        "| Agent architecture — Perceive/Reason/Act/Observe (S9) | agent.py — core ReAct loop |\n"
        "| Tool calling with JSON schemas (S9) | tools.py — 3 tool definitions |\n"
        "| ReAct pattern — Thought/Action/Observation (S9) | Agent trace (Section 5) |\n"
        "| Guardrails & failure handling (S9) | agent.py — max iterations, validation |\n"
        "| Multimodal input processing (S10) | extractor.py — Vision LLM API |\n"
        "| Structured extraction to JSON (S10) | extractor.py + validator.py |\n"
        "| Few-shot prompting for extraction (S10) | extractor.py — GNSS domain examples |\n"
        "| Post-processing & validation (S10) | validator.py — schema & range checks |\n"
        "| Evaluation metrics (S9+S10) | Metrics table above |\n\n"
        "---\n"
        "*Group 14 | Beihang University (BUAA) — RCSSTEAP | Spring 2026*"
    ))

    nb.cells = cells
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    return output_path


if __name__ == "__main__":
    path = generate_notebook()
    print(f"Notebook generated: {path}")
