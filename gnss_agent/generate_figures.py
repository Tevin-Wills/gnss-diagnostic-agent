"""
Generate publication-quality matplotlib figures for PDF embedding.

Uses scientific visualization best practices:
  - Okabe-Ito colorblind-safe palette
  - Sans-serif fonts (Arial), min 8pt
  - 300 DPI export
  - Clean spines, no chart junk
  - Proper axis labels with units
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

from config import OUTPUTS_DIR, SAMPLES_DIR

# ── Publication style ──────────────────────────────────────────────────
OKABE_ITO = ['#009E73', '#E69F00', '#D55E00', '#56B4E9',
             '#0072B2', '#CC79A7', '#F0E442', '#000000']
DARK_BG = '#0e1117'
CARD_BG = '#1a1a2e'
CYAN = '#00d4aa'
YELLOW = '#ffd700'
RED = '#ff6b6b'
PURPLE = '#c084fc'
WHITE = '#e0e0e0'

def _apply_dark_style():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 9,
        'axes.labelsize': 10,
        'axes.titlesize': 11,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.facecolor': DARK_BG,
        'axes.facecolor': CARD_BG,
        'axes.edgecolor': '#3a3a5a',
        'axes.labelcolor': WHITE,
        'text.color': WHITE,
        'xtick.color': '#a0a0b0',
        'ytick.color': '#a0a0b0',
        'grid.color': '#2a2a4a',
        'grid.alpha': 0.5,
        'savefig.facecolor': DARK_BG,
        'savefig.dpi': 300,
    })


def _load_data():
    with open(os.path.join(OUTPUTS_DIR, 'agent_result.json'), encoding='utf-8') as f:
        return json.load(f)


def generate_sky_plot(result, out_dir):
    """Generate publication-quality polar sky plot."""
    _apply_dark_style()
    sats = result['memory'].get('satellite_data', {}).get('satellites', [])
    if not sats:
        return None

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_facecolor(CARD_BG)

    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rlim(0, 90)
    ax.set_rticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_yticklabels(['90°', '75°', '60°', '45°', '30°', '15°', '0°'],
                        fontsize=7, color='#a0a0b0')
    ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315],
                       labels=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                       fontsize=9, color=WHITE)
    ax.grid(True, alpha=0.3)

    for sat in sats:
        az = np.radians(float(sat.get('azimuth_deg', 0)))
        el = float(sat.get('elevation_deg', 45))
        cn0 = float(sat.get('cn0_dbhz', sat.get('cn0_dbHz', 35)))
        r = 90 - el

        if cn0 >= 40:
            color, marker = CYAN, 'o'
        elif cn0 >= 30:
            color, marker = YELLOW, 's'
        else:
            color, marker = RED, '^'

        ax.scatter(az, r, c=color, s=100, marker=marker, edgecolors='white',
                   linewidths=0.8, zorder=5)
        ax.annotate(sat.get('prn', '?'), (az, r), textcoords='offset points',
                    xytext=(6, 6), fontsize=8, color=color, fontweight='bold')

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=CYAN,
                   markersize=8, label='Strong (C/N0 >= 40)', linestyle='None'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=YELLOW,
                   markersize=8, label='Moderate (30-40)', linestyle='None'),
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor=RED,
                   markersize=8, label='Weak (< 30)', linestyle='None'),
    ]
    ax.legend(handles=legend_elements, loc='lower right',
              bbox_to_anchor=(1.15, -0.08), frameon=True,
              facecolor=CARD_BG, edgecolor='#3a3a5a', labelcolor=WHITE)

    ax.set_title('Satellite Sky Plot — Elevation vs Azimuth\n',
                 fontsize=12, fontweight='bold', color=CYAN, pad=15)

    path = os.path.join(out_dir, 'fig_sky_plot.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)
    return path


def generate_dop_chart(result, out_dir):
    """Generate DOP time series chart."""
    _apply_dark_style()
    epochs = result['memory'].get('dop_data', {}).get('epochs', [])
    if not epochs:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))
    times = [e.get('time', f'T{i}') for i, e in enumerate(epochs)]
    x = np.arange(len(times))

    dop_configs = [
        ('gdop', RED, '-', 'o', 'GDOP'),
        ('pdop', YELLOW, '--', 's', 'PDOP'),
        ('hdop', CYAN, '-.', '^', 'HDOP'),
        ('vdop', '#4ecdc4', ':', 'v', 'VDOP'),
        ('tdop', PURPLE, '--', 'D', 'TDOP'),
    ]

    for key, color, ls, marker, label in dop_configs:
        vals = [float(e.get(key, 0)) for e in epochs]
        ax.plot(x, vals, color=color, linestyle=ls, marker=marker,
                markersize=6, linewidth=1.8, label=label)

    # Threshold zones
    ax.axhspan(0, 5, alpha=0.05, color=CYAN)
    ax.axhspan(5, 10, alpha=0.05, color=YELLOW)
    ax.axhspan(10, max(15, ax.get_ylim()[1]), alpha=0.05, color=RED)
    ax.axhline(5, color=YELLOW, linewidth=0.8, linestyle='--', alpha=0.6)
    ax.axhline(10, color=RED, linewidth=0.8, linestyle='--', alpha=0.6)

    ax.text(len(times) - 0.3, 5.2, 'Good/Moderate', fontsize=7, color=YELLOW, alpha=0.8)
    ax.text(len(times) - 0.3, 10.2, 'Moderate/Poor', fontsize=7, color=RED, alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(times)
    ax.set_xlabel('Time (UTC)')
    ax.set_ylabel('DOP Value')
    ax.set_title('Dilution of Precision Over Time', fontsize=12, fontweight='bold', color=CYAN)
    ax.legend(loc='upper left', frameon=True, facecolor=CARD_BG, edgecolor='#3a3a5a',
              labelcolor=WHITE, ncol=5, fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.2)

    path = os.path.join(out_dir, 'fig_dop_chart.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    return path


def generate_cn0_chart(result, out_dir):
    """Generate C/N0 bar chart."""
    _apply_dark_style()
    signals = result['memory'].get('cn0_data', {}).get('signals', [])
    if not signals:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))
    prns = [s.get('prn', '?') for s in signals]
    cn0s = [float(s.get('cn0_dbhz', s.get('cn0_dbHz', 0))) for s in signals]
    colors = [CYAN if c >= 40 else (YELLOW if c >= 30 else RED) for c in cn0s]

    bars = ax.bar(prns, cn0s, color=colors, edgecolor='white', linewidth=0.5, width=0.6)

    for bar, val in zip(bars, cn0s):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f'{val:.1f}', ha='center', va='bottom', fontsize=7, color=WHITE)

    ax.axhline(40, color=CYAN, linewidth=0.8, linestyle='--', alpha=0.6, label='Strong (>=40)')
    ax.axhline(30, color=YELLOW, linewidth=0.8, linestyle='--', alpha=0.6, label='Moderate (>=30)')
    ax.axhline(20, color=RED, linewidth=0.8, linestyle='--', alpha=0.6, label='Weak (<30)')

    ax.set_xlabel('Satellite PRN')
    ax.set_ylabel('C/N0 (dBHz)')
    ax.set_title('Signal Strength per Satellite', fontsize=12, fontweight='bold', color=CYAN)
    ax.legend(loc='upper right', frameon=True, facecolor=CARD_BG, edgecolor='#3a3a5a',
              labelcolor=WHITE, fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='y', alpha=0.2)

    path = os.path.join(out_dir, 'fig_cn0_chart.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    return path


def generate_agent_timeline(result, out_dir):
    """Generate agent execution timeline (horizontal bar chart)."""
    _apply_dark_style()
    trace = result.get('trace', [])
    if not trace:
        return None

    fig, ax = plt.subplots(figsize=(8, 3.5))

    tool_colors = {
        'extract_diagram_data': CYAN,
        'analyze_positioning_quality': YELLOW,
        'generate_diagnostic_report': RED,
        'TASK_COMPLETE': '#4ecdc4',
        'PARSE_ERROR': '#888888',
    }

    labels = []
    latencies = []
    colors_list = []
    cumulative = 0

    for step in trace:
        tool = step.get('action', {}).get('tool', '?') if isinstance(step.get('action'), dict) else '?'
        lat = step.get('latency_seconds', 0)
        labels.append(f"Step {step['iteration']}\n{tool.split('_')[-1] if '_' in tool else tool}")
        latencies.append(lat)
        colors_list.append(tool_colors.get(tool, '#888888'))

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, latencies, color=colors_list, edgecolor='white', linewidth=0.5, height=0.6)

    for bar, lat in zip(bars, latencies):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f'{lat:.1f}s', va='center', fontsize=8, color=WHITE)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Latency (seconds)')
    ax.set_title('Agent Execution Timeline — ReAct Steps', fontsize=12, fontweight='bold', color=CYAN)
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, axis='x', alpha=0.2)

    # Legend
    unique_tools = {}
    for step in trace:
        tool = step.get('action', {}).get('tool', '?') if isinstance(step.get('action'), dict) else '?'
        if tool not in unique_tools:
            unique_tools[tool] = tool_colors.get(tool, '#888888')
    legend_elements = [mpatches.Patch(facecolor=c, label=t.replace('_', ' ').title())
                       for t, c in unique_tools.items()]
    ax.legend(handles=legend_elements, loc='lower right', frameon=True,
              facecolor=CARD_BG, edgecolor='#3a3a5a', labelcolor=WHITE, fontsize=7)

    path = os.path.join(out_dir, 'fig_timeline.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    return path


def generate_risk_gauge(result, out_dir):
    """Generate a risk assessment gauge chart."""
    _apply_dark_style()
    memory = result.get('memory', {})
    report_data = memory.get('report', {})
    rpt = report_data.get('report', report_data) if isinstance(report_data, dict) else {}
    risk_level = rpt.get('risk_level', 'unknown')
    risk_val = {'low': 20, 'moderate': 50, 'high': 75, 'critical': 95}.get(risk_level, 50)

    fig, ax = plt.subplots(figsize=(5, 3.5), subplot_kw={'aspect': 'equal'})

    # Draw gauge arcs
    theta_start, theta_end = np.pi, 0
    for start_frac, end_frac, color in [
        (0, 0.3, CYAN), (0.3, 0.6, YELLOW), (0.6, 1.0, RED)
    ]:
        t1 = theta_start + (theta_end - theta_start) * start_frac
        t2 = theta_start + (theta_end - theta_start) * end_frac
        theta = np.linspace(t1, t2, 50)
        for r in np.linspace(0.7, 1.0, 15):
            ax.plot(r * np.cos(theta), r * np.sin(theta), color=color, alpha=0.3, linewidth=2)

    # Needle
    needle_angle = theta_start + (theta_end - theta_start) * (risk_val / 100)
    ax.plot([0, 0.65 * np.cos(needle_angle)], [0, 0.65 * np.sin(needle_angle)],
            color='white', linewidth=3, solid_capstyle='round')
    ax.scatter([0], [0], c='white', s=40, zorder=10)

    # Labels
    ax.text(0, -0.2, f'{risk_level.upper()}', ha='center', va='center',
            fontsize=20, fontweight='bold',
            color=RED if risk_val > 60 else (YELLOW if risk_val > 30 else CYAN))
    ax.text(0, -0.38, f'Risk Score: {risk_val}/100', ha='center', va='center',
            fontsize=10, color='#a0a0b0')

    # Zone labels
    ax.text(-0.85, -0.05, 'LOW', ha='center', fontsize=8, color=CYAN, fontweight='bold')
    ax.text(0, 0.85, 'MODERATE', ha='center', fontsize=8, color=YELLOW, fontweight='bold')
    ax.text(0.85, -0.05, 'HIGH', ha='center', fontsize=8, color=RED, fontweight='bold')

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.5, 1.15)
    ax.axis('off')
    ax.set_title('GNSS Positioning Risk Assessment', fontsize=12, fontweight='bold',
                 color=CYAN, pad=5)

    path = os.path.join(out_dir, 'fig_risk_gauge.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    return path


def generate_architecture_diagram(out_dir):
    """Generate system architecture diagram."""
    _apply_dark_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    boxes = [
        # (x, y, w, h, label, color, sublabel)
        (0.5, 3.2, 2.2, 0.9, 'GNSS Diagrams', '#3a5a8a', 'sky_plot.png\ndop_table.png\ncn0_chart.png'),
        (3.8, 3.2, 2.2, 0.9, 'Vision LLM', CYAN, 'llava 7B\nFew-shot prompting\nJSON extraction'),
        (7.1, 3.2, 2.2, 0.9, 'Validator', YELLOW, 'Schema checks\nRange validation\nType coercion'),
        (0.5, 1.3, 2.2, 0.9, 'ReAct Agent', PURPLE, 'llama3.2:3b\nThought/Action/Obs\nTool calling'),
        (3.8, 1.3, 2.2, 0.9, 'Tool Registry', '#E69F00', '3 tools\nJSON schemas\nMemory injection'),
        (7.1, 1.3, 2.2, 0.9, 'Report Gen', RED, 'Risk assessment\nFindings\nPDF / HTML'),
    ]

    for x, y, w, h, label, color, sublabel in boxes:
        rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.1',
                                        facecolor=color, alpha=0.25, edgecolor=color,
                                        linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.18, label, ha='center', va='top',
                fontsize=10, fontweight='bold', color=color)
        ax.text(x + w / 2, y + 0.1, sublabel, ha='center', va='bottom',
                fontsize=7, color='#a0a0b0', linespacing=1.3)

    # Arrows
    arrow_kw = dict(arrowstyle='->', color='#5a5a8a', lw=1.5, connectionstyle='arc3,rad=0')
    for (x1, y1), (x2, y2) in [
        ((2.7, 3.65), (3.8, 3.65)),   # Diagrams -> Vision
        ((6.0, 3.65), (7.1, 3.65)),   # Vision -> Validator
        ((5.5, 3.2), (4.0, 2.2)),     # mid -> Agent (down)
        ((2.7, 1.75), (3.8, 1.75)),   # Agent -> Tools
        ((6.0, 1.75), (7.1, 1.75)),   # Tools -> Report
    ]:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=arrow_kw)

    ax.set_xlim(0, 9.8)
    ax.set_ylim(0.5, 4.5)
    ax.axis('off')
    ax.set_title('System Architecture — GNSS Multimodal Diagnostic Agent',
                 fontsize=13, fontweight='bold', color=CYAN, pad=10)

    # Session labels
    ax.text(4.9, 4.35, 'Session 10: Multimodal Extraction', ha='center',
            fontsize=9, color='#6a6a9a', style='italic')
    ax.text(4.9, 0.75, 'Session 9: Agent & Tool Use', ha='center',
            fontsize=9, color='#6a6a9a', style='italic')

    path = os.path.join(out_dir, 'fig_architecture.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    return path


def generate_extraction_summary(result, out_dir):
    """Generate extraction summary multi-panel figure."""
    _apply_dark_style()
    ext_results = result.get('memory', {}).get('extraction_results', [])
    if not ext_results:
        return None

    fig, axes = plt.subplots(1, 3, figsize=(9, 3))

    for i, (ext, ax) in enumerate(zip(ext_results, axes)):
        dtype = ext.get('extracted_data', {}).get('diagram_type', f'Diagram {i+1}')
        val = ext.get('validation', {})
        is_valid = val.get('is_valid', False)
        confidence = val.get('stats', {}).get('confidence', 0)
        latency = ext.get('latency_seconds', 0)
        method = ext.get('prompting_method', '?')

        # Confidence bar
        bar_color = CYAN if is_valid else RED
        ax.barh([0], [confidence * 100], color=bar_color, alpha=0.7, height=0.3, edgecolor='white')
        ax.barh([0], [100], color='#2a2a4a', height=0.3, zorder=0)

        # Status badge
        status_text = 'PASSED' if is_valid else 'FAILED'
        ax.text(50, 0.5, f'{dtype.replace("_", " ").upper()}',
                ha='center', va='center', fontsize=10, fontweight='bold', color=WHITE)
        ax.text(50, 0.25, f'{status_text} | {confidence*100:.0f}% conf | {latency:.1f}s | {method}',
                ha='center', va='center', fontsize=7, color='#a0a0b0')

        ax.set_xlim(0, 100)
        ax.set_ylim(-0.3, 0.8)
        ax.axis('off')

    fig.suptitle('Extraction Pipeline Summary', fontsize=12, fontweight='bold',
                 color=CYAN, y=1.0)
    fig.tight_layout()

    path = os.path.join(out_dir, 'fig_extraction_summary.png')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    return path


def generate_all_figures():
    """Generate all figures for the PDF report."""
    fig_dir = os.path.join(OUTPUTS_DIR, 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    result = _load_data()
    figures = {}

    generators = [
        ('architecture', generate_architecture_diagram, (fig_dir,)),
        ('sky_plot', generate_sky_plot, (result, fig_dir)),
        ('dop_chart', generate_dop_chart, (result, fig_dir)),
        ('cn0_chart', generate_cn0_chart, (result, fig_dir)),
        ('timeline', generate_agent_timeline, (result, fig_dir)),
        ('risk_gauge', generate_risk_gauge, (result, fig_dir)),
        ('extraction_summary', generate_extraction_summary, (result, fig_dir)),
    ]

    for name, func, args in generators:
        try:
            path = func(*args)
            if path:
                figures[name] = path
                print(f'  {name}: OK')
            else:
                print(f'  {name}: SKIPPED (no data)')
        except Exception as e:
            print(f'  {name}: ERROR - {e}')

    return figures


if __name__ == '__main__':
    print('Generating publication-quality figures...')
    figs = generate_all_figures()
    print(f'\nGenerated {len(figs)} figures')
