"""
Generate an interactive HTML report for Assignment 4.

Produces a self-contained .html file with:
  - Dark-navy theme matching the Streamlit dashboard exactly
  - Dual institutional logos (Beihang + RCSSTEAP) on title page
  - CSS animations: breathe, glowPulse, gradientShift, textShimmer
  - Reading progress bar at top
  - IntersectionObserver active-section highlighting in sidebar
  - Hover effects: card lift, table row glow, metric scale, sidebar pulse
  - Back-to-top button
  - Section reveal (fade-in-up) on scroll
  - Interactive Plotly charts (zoomable, pannable, hoverable)
  - Collapsible ReAct trace steps
  - Smooth scrolling with nav offset
"""
import base64
import json
import os
from datetime import datetime

from config import OUTPUTS_DIR, SAMPLES_DIR


# ── Image helpers ─────────────────────────────────────────────────────────────

def _img_to_base64(path: str, mime: str = "png") -> str:
    """Convert an image file to a base64 data URI."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{data}"


def _load_agent_result():
    path = os.path.join(OUTPUTS_DIR, "agent_result.json")
    with open(path) as f:
        return json.load(f)


# ── CSS ───────────────────────────────────────────────────────────────────────

def _css(risk_color: str) -> str:
    return f"""
<style>
/* ── Design tokens (match Streamlit dashboard) ── */
:root {{
    --bg:        #0D1B2A;
    --card:      #142A3E;
    --card2:     #0A2E50;
    --grid:      #1E3A5F;
    --cyan:      #00BCD4;
    --green:     #66BB6A;
    --amber:     #FFB74D;
    --coral:     #FF6B6B;
    --blue:      #29B6F6;
    --text:      #E0E7EE;
    --muted:     #A0AEBB;
    --border:    #1E3A5F;
    --risk:      {risk_color};
    --shadow-cyan: rgba(0,188,212,0.25);
    --shadow-coral: rgba(255,107,107,0.25);
    --shadow-amber: rgba(255,183,77,0.25);
}}

/* ── Reset ── */
*, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
    font-family: 'Segoe UI', Calibri, system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6;
    overflow-x: hidden;
}}

/* ── Animations ── */
@keyframes breathe {{
    0%, 100% {{ opacity: 0.75; transform: scale(1); }}
    50%       {{ opacity: 1;    transform: scale(1.03); }}
}}
@keyframes glowPulse {{
    0%, 100% {{ box-shadow: 0 0 4px rgba(0,188,212,0.15); }}
    50%       {{ box-shadow: 0 0 14px rgba(0,188,212,0.45); }}
}}
@keyframes textShimmer {{
    0%, 100% {{ opacity: 0.85; text-shadow: none; }}
    50%       {{ opacity: 1; text-shadow: 0 0 8px rgba(0,188,212,0.35); }}
}}
@keyframes gradientShift {{
    0%   {{ background-position: 0% 50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes slideInLeft {{
    from {{ opacity: 0; transform: translateX(-20px); }}
    to   {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes progressGrow {{
    from {{ width: 0; }}
}}
@keyframes spinPulse {{
    0%, 100% {{ transform: rotate(0deg) scale(1); }}
    50%       {{ transform: rotate(180deg) scale(1.1); }}
}}

/* ── Reading progress bar ── */
#progress-bar {{
    position: fixed; top: 0; left: 0; height: 3px; width: 0;
    background: linear-gradient(90deg, var(--cyan), var(--blue));
    z-index: 9999; transition: width 0.1s linear;
    box-shadow: 0 0 8px var(--cyan);
}}

/* ── Sidebar ── */
.sidebar {{
    position: fixed; left: 0; top: 0; width: 260px; height: 100vh;
    background: linear-gradient(180deg, #0D1B2A 0%, #101E30 100%);
    border-right: 1px solid var(--border);
    padding: 0 0 20px; overflow-y: auto; z-index: 100;
    scrollbar-width: thin; scrollbar-color: var(--border) transparent;
}}
.sidebar::-webkit-scrollbar {{ width: 4px; }}
.sidebar::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}

.sidebar-logo-wrap {{
    text-align: center; padding: 18px 0 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 10px;
}}
.sidebar-logo {{
    height: 52px;
    animation: breathe 3.5s ease-in-out infinite;
}}
.sidebar-logo-caption {{
    color: var(--cyan); font-size: 10px; margin-top: 6px;
    letter-spacing: 0.5px; text-transform: uppercase;
    animation: textShimmer 3s ease-in-out infinite;
}}

.sidebar nav {{ padding: 0 12px; }}
.sidebar .nav-section {{
    font-size: 10px; color: var(--muted); text-transform: uppercase;
    letter-spacing: 1.5px; padding: 14px 10px 4px; font-weight: 600;
}}
.sidebar a {{
    display: block; color: var(--muted); text-decoration: none;
    padding: 8px 12px; border-radius: 7px; margin-bottom: 2px;
    font-size: 13px; transition: all 0.25s ease;
    border-left: 3px solid transparent;
    animation: glowPulse 4s ease-in-out infinite;
}}
.sidebar a:nth-child(2) {{ animation-delay: 0.3s; }}
.sidebar a:nth-child(3) {{ animation-delay: 0.6s; }}
.sidebar a:nth-child(4) {{ animation-delay: 0.9s; }}
.sidebar a:hover {{
    background: var(--card); color: var(--cyan);
    border-left-color: var(--cyan);
    transform: translateX(3px);
    box-shadow: 0 3px 12px var(--shadow-cyan);
}}
.sidebar a.active {{
    background: var(--card2); color: var(--cyan);
    border-left-color: var(--cyan);
    box-shadow: 0 0 10px rgba(0,188,212,0.2);
}}
.sidebar a.sub {{ padding-left: 28px; font-size: 12px; }}

.sidebar-footer {{
    padding: 12px 16px; margin-top: 10px;
    border-top: 1px solid var(--border);
    font-size: 11px; color: var(--muted); text-align: center;
    line-height: 1.8;
}}
.sidebar-footer span {{ color: var(--amber); }}

/* ── Main content ── */
.main {{ margin-left: 280px; padding: 0 30px 60px; }}

/* ── Title / Landing page ── */
.landing-container {{
    background: linear-gradient(180deg, #0D1B2A 0%, #142A3E 50%, #0D1B2A 100%);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 36px 40px; text-align: center; margin: 28px 0 32px;
    position: relative; overflow: hidden;
    animation: fadeInUp 0.7s ease both;
}}
.landing-container::before {{
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(0,188,212,0.08) 0%, transparent 70%);
    pointer-events: none;
}}
.landing-logos {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 18px;
}}
.landing-logos img {{
    height: 72px; transition: transform 0.3s ease, filter 0.3s ease;
    filter: drop-shadow(0 2px 6px rgba(0,188,212,0.2));
}}
.landing-logos img:hover {{
    transform: scale(1.1);
    filter: drop-shadow(0 4px 12px rgba(0,188,212,0.45));
}}
.landing-divider {{
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    margin: 16px auto; max-width: 420px; border-radius: 2px;
}}
.landing-institution {{
    font-size: 15px; color: var(--text); font-weight: 600; margin: 0 0 2px;
}}
.landing-dept {{
    font-size: 12px; color: var(--muted); margin: 0 0 4px;
}}
.landing-course {{
    font-size: 12px; color: var(--muted); margin: 6px 0 0;
}}
.landing-title {{
    font-size: 26px; font-weight: 700; color: var(--text);
    margin: 10px 0 4px;
    animation: textShimmer 4s ease-in-out infinite;
}}
.landing-subtitle {{
    font-size: 16px; font-weight: 600; color: var(--cyan); margin: 4px 0 8px;
}}
.landing-group {{ font-size: 13px; color: var(--muted); margin: 4px 0 10px; }}
.member-table {{
    width: 100%; border-collapse: collapse;
    margin: 10px auto 16px; max-width: 540px;
}}
.member-table th {{
    background: var(--card2); color: var(--cyan);
    padding: 9px 16px; font-size: 13px;
    border: 1px solid var(--border); font-weight: 600;
}}
.member-table td {{
    color: var(--text); padding: 8px 16px; font-size: 13px;
    border: 1px solid var(--border); background: var(--card);
    transition: background 0.25s ease;
}}
.member-table tr:hover td {{ background: #1A3A5A; }}
.brief-card {{
    background: linear-gradient(135deg, #0A2E50, #142A3E);
    border: 1px solid var(--cyan); border-radius: 10px;
    padding: 14px 20px; margin: 14px auto 8px; max-width: 720px;
    text-align: left; transition: all 0.3s ease;
}}
.brief-card:hover {{
    box-shadow: 0 6px 20px var(--shadow-cyan); transform: translateY(-2px);
}}
.brief-card-title {{ color: var(--cyan); font-weight: 600; margin-bottom: 6px; font-size: 14px; }}
.brief-card p {{ color: var(--text); font-size: 13px; line-height: 1.7; }}
.guide-text {{
    display: inline-block; font-size: 13px; font-weight: 600;
    padding: 10px 22px; border: 1px solid var(--cyan); border-radius: 8px;
    background: linear-gradient(90deg, #0A2E50, #142A3E, #0A2E50);
    background-size: 200% 100%;
    animation: gradientShift 4s ease infinite;
    color: var(--cyan); letter-spacing: 0.3px; margin-top: 10px;
}}
.guide-text span {{ color: var(--amber); }}

/* ── Section headers ── */
.section-header {{
    display: flex; align-items: center; gap: 12px;
    margin: 36px 0 16px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}}
.section-header .accent-bar {{
    width: 4px; height: 28px; border-radius: 2px;
    background: var(--cyan); flex-shrink: 0;
    box-shadow: 0 0 8px var(--shadow-cyan);
}}
.section-header h2 {{
    font-size: 20px; color: var(--text); font-weight: 600;
    animation: textShimmer 5s ease-in-out infinite;
}}
h3 {{ font-size: 15px; color: var(--cyan); margin: 18px 0 10px; font-weight: 600; }}

/* ── Scroll-reveal sections ── */
.reveal {{
    opacity: 0; transform: translateY(22px);
    transition: opacity 0.55s ease, transform 0.55s ease;
}}
.reveal.visible {{ opacity: 1; transform: translateY(0); }}

/* ── Project link rows ── */
#links .card a:hover {{
    background: #1A3A5A !important;
}}

/* ── Cards ── */
.card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin: 14px 0;
    transition: all 0.3s ease;
}}
.card:hover {{
    border-color: var(--cyan);
    box-shadow: 0 6px 22px var(--shadow-cyan);
    transform: translateY(-2px);
}}
.info-card {{
    background: linear-gradient(135deg, #142A3E, #1A354C);
    border: 1px solid var(--border); border-left: 4px solid var(--cyan);
    border-radius: 10px; padding: 16px 20px; margin: 10px 0;
    transition: all 0.3s ease;
}}
.info-card:hover {{
    transform: translateY(-3px); box-shadow: 0 6px 20px var(--shadow-cyan); border-color: var(--cyan);
}}
.warn-card {{
    background: linear-gradient(135deg, #2A1A0A, #3E250A);
    border: 1px solid #5C3A0A; border-left: 4px solid var(--amber);
    border-radius: 10px; padding: 16px 20px; margin: 10px 0;
    transition: all 0.3s ease;
}}
.warn-card:hover {{
    transform: translateY(-3px); box-shadow: 0 6px 20px var(--shadow-amber); border-color: var(--amber);
}}
.danger-card {{
    background: linear-gradient(135deg, #2A0A0A, #3E1515);
    border: 1px solid #5C1A1A; border-left: 4px solid var(--coral);
    border-radius: 10px; padding: 16px 20px; margin: 10px 0;
    transition: all 0.3s ease;
}}
.danger-card:hover {{
    transform: translateY(-3px); box-shadow: 0 6px 20px var(--shadow-coral); border-color: var(--coral);
}}
.success-card {{
    background: linear-gradient(135deg, #0A2A15, #0A3E20);
    border: 1px solid #0A5C2A; border-left: 4px solid var(--green);
    border-radius: 10px; padding: 16px 20px; margin: 10px 0;
    transition: all 0.3s ease;
}}
.success-card:hover {{
    transform: translateY(-3px); box-shadow: 0 6px 20px rgba(102,187,106,0.25); border-color: var(--green);
}}

/* ── Risk banner ── */
.risk-banner {{
    background: linear-gradient(135deg, #142A3E, #0A2E50);
    border-left: 4px solid var(--risk);
    border: 1px solid var(--border); border-left-width: 4px;
    padding: 20px 24px; border-radius: 10px; margin: 20px 0;
    transition: all 0.3s ease;
    box-shadow: 0 0 12px rgba(0,0,0,0.3);
}}
.risk-banner:hover {{ box-shadow: 0 6px 24px rgba(0,0,0,0.5), 0 0 16px var(--shadow-cyan); }}
.risk-label {{
    color: var(--risk); font-size: 22px; font-weight: 700;
    text-shadow: 0 0 10px currentColor;
    animation: textShimmer 3s ease-in-out infinite;
}}

/* ── Metrics grid ── */
.metrics-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px; margin: 20px 0;
}}
.metric-card {{
    background: var(--card2); border: 1px solid var(--border);
    border-radius: 10px; padding: 18px 14px; text-align: center;
    transition: all 0.3s ease; cursor: default;
    animation: glowPulse 4s ease-in-out infinite;
}}
.metric-card:nth-child(2) {{ animation-delay: 1s; }}
.metric-card:nth-child(3) {{ animation-delay: 2s; }}
.metric-card:nth-child(4) {{ animation-delay: 3s; }}
.metric-card:hover {{
    transform: translateY(-4px) scale(1.03);
    border-color: var(--cyan);
    box-shadow: 0 8px 24px var(--shadow-cyan);
}}
.metric-card .value {{
    font-size: 30px; font-weight: 700; color: var(--cyan);
    transition: all 0.3s ease;
}}
.metric-card:hover .value {{
    transform: scale(1.1);
    text-shadow: 0 0 12px rgba(0,188,212,0.5);
}}
.metric-card .label {{
    font-size: 11px; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px;
}}

/* ── Tables ── */
.table-wrap {{ overflow-x: auto; border-radius: 8px; margin: 14px 0; }}
table {{ width: 100%; border-collapse: collapse; }}
thead tr {{ position: sticky; top: 0; z-index: 2; }}
th {{
    background: var(--card2); color: var(--cyan);
    padding: 11px 16px; text-align: left; font-size: 12.5px;
    text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;
    border-bottom: 2px solid var(--border);
}}
td {{
    padding: 10px 16px; border-bottom: 1px solid var(--border);
    font-size: 13px; transition: background 0.2s ease;
}}
tbody tr:hover td {{ background: rgba(0,188,212,0.07); }}
.pass {{ color: var(--green); font-weight: 700; }}
.fail {{ color: var(--coral); font-weight: 700; }}

/* ── Diagrams ── */
.diagram-wrap {{
    border-radius: 10px; overflow: hidden; margin: 12px 0;
    border: 1px solid var(--border); transition: all 0.3s ease;
    cursor: zoom-in;
}}
.diagram-wrap:hover {{
    box-shadow: 0 8px 28px rgba(0,0,0,0.5), 0 0 0 1px var(--cyan);
    transform: scale(1.005);
}}
img.diagram {{ max-width: 100%; height: auto; display: block; }}

/* ── Agent trace steps ── */
.trace-step {{ margin: 8px 0; }}
.trace-step summary {{
    cursor: pointer; padding: 13px 16px; background: var(--card2);
    border-radius: 8px; border: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px;
    list-style: none; transition: all 0.25s ease;
}}
.trace-step summary:hover {{
    background: #1A3A5A; border-color: var(--cyan);
    box-shadow: 0 4px 14px var(--shadow-cyan);
}}
.trace-step[open] summary {{
    border-radius: 8px 8px 0 0;
    background: #1A3A5A; border-color: var(--cyan);
}}
.trace-step summary::-webkit-details-marker {{ display: none; }}
.trace-step summary::before {{
    content: '▶'; font-size: 10px; color: var(--muted);
    transition: transform 0.25s ease; flex-shrink: 0;
}}
.trace-step[open] summary::before {{ transform: rotate(90deg); color: var(--cyan); }}
.step-num {{
    font-weight: 700; color: var(--text); min-width: 58px;
    font-size: 13px;
}}
.tool-badge {{
    display: inline-flex; align-items: center;
    padding: 3px 11px; border-radius: 20px;
    font-size: 11.5px; font-weight: 700; color: #000;
    letter-spacing: 0.2px;
}}
.step-thought {{
    flex: 1; font-size: 12px; color: var(--muted);
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
    max-width: 360px;
}}
.latency {{ margin-left: auto; color: var(--muted); font-size: 12px; flex-shrink: 0; }}
.trace-detail {{
    padding: 16px 20px; background: var(--card);
    border: 1px solid var(--cyan); border-top: none;
    border-radius: 0 0 8px 8px;
}}
.trace-detail .field {{ margin: 7px 0; font-size: 13px; }}
.trace-detail .field strong {{ color: var(--cyan); }}
.trace-detail pre {{
    background: #0A1520; border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px; margin-top: 6px;
    font-size: 11.5px; color: #a0e0a0; overflow-x: auto;
    white-space: pre-wrap; word-break: break-word;
}}

/* ── Findings ── */
.finding-ok   {{ color: var(--green); }}
.finding-warn {{ color: var(--amber); }}
.finding-error {{ color: var(--coral); }}
ul.findings {{ list-style: none; padding: 0; }}
ul.findings li {{
    padding: 9px 14px; margin: 5px 0;
    background: var(--card2); border-radius: 7px;
    border: 1px solid var(--border);
    transition: all 0.25s ease;
    display: flex; align-items: flex-start; gap: 8px;
}}
ul.findings li:hover {{
    transform: translateX(4px);
    border-color: currentColor;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}}
ul.findings li::before {{ content: '◆'; font-size: 10px; margin-top: 3px; flex-shrink: 0; }}
ul.recs {{ padding-left: 0; list-style: none; }}
ul.recs li {{
    padding: 8px 14px; margin: 5px 0;
    background: var(--card2); border-radius: 7px;
    border: 1px solid var(--border); font-size: 13px;
    transition: all 0.25s ease; display: flex; gap: 8px;
}}
ul.recs li::before {{ content: '→'; color: var(--cyan); font-weight: 700; flex-shrink: 0; }}
ul.recs li:hover {{ background: #1A3A5A; transform: translateX(4px); }}

/* ── Chart containers ── */
.chart-container {{
    margin: 22px 0; border-radius: 10px; overflow: visible;
    border: 1px solid var(--border); transition: all 0.3s ease;
    background: var(--card); padding: 4px 4px 8px;
}}
.chart-container:hover {{
    border-color: var(--cyan);
    box-shadow: 0 6px 22px var(--shadow-cyan);
}}
.chart-label {{
    font-size: 12px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: 1px;
    padding: 10px 14px 0; margin-bottom: -4px;
}}

/* ── Back-to-top ── */
#back-to-top {{
    position: fixed; bottom: 30px; right: 28px;
    width: 44px; height: 44px; border-radius: 50%;
    background: var(--card2); border: 2px solid var(--cyan);
    color: var(--cyan); font-size: 20px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; opacity: 0; visibility: hidden;
    transition: all 0.3s ease; z-index: 500;
    box-shadow: 0 0 14px var(--shadow-cyan);
    text-decoration: none;
}}
#back-to-top.visible {{ opacity: 1; visibility: visible; }}
#back-to-top:hover {{
    background: var(--cyan); color: #000;
    transform: scale(1.15) translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,188,212,0.5);
}}

/* ── Prompt code blocks ── */
.prompt-block {{
    background: #0A1520; border: 1px solid var(--border);
    border-radius: 8px; padding: 14px 18px; margin: 10px 0;
    font-family: 'Cascadia Code', 'Fira Code', 'Courier New', monospace;
    font-size: 12px; color: #a0e0a0; line-height: 1.7;
    overflow-x: auto; transition: all 0.25s ease;
}}
.prompt-block:hover {{ border-color: var(--cyan); }}
.prompt-label {{
    font-size: 11px; color: var(--cyan); font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 6px;
}}

/* ── Responsive ── */
@media (max-width: 900px) {{
    .sidebar {{ display: none; }}
    .main {{ margin-left: 0; padding: 0 16px 40px; }}
    .landing-logos img {{ height: 52px; }}
    .landing-title {{ font-size: 20px; }}
    .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 480px) {{
    .landing-container {{ padding: 24px 18px; }}
    .metrics-grid {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
"""


# ── JavaScript ────────────────────────────────────────────────────────────────

SCRIPTS = """
<script>
// ── Reading progress bar ──────────────────────────────────────────────
var bar = document.getElementById('progress-bar');
window.addEventListener('scroll', function() {
    var scrollTop = window.scrollY || document.documentElement.scrollTop;
    var docH = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (scrollTop / docH * 100) + '%';

    // Back-to-top visibility
    var btn = document.getElementById('back-to-top');
    if (scrollTop > 300) { btn.classList.add('visible'); }
    else { btn.classList.remove('visible'); }
});

// ── Back to top ───────────────────────────────────────────────────────
document.getElementById('back-to-top').addEventListener('click', function(e) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Scroll reveal ─────────────────────────────────────────────────────
var revealObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
document.querySelectorAll('.reveal').forEach(function(el) {
    revealObserver.observe(el);
});

// ── Active sidebar section (IntersectionObserver) ─────────────────────
var sections = document.querySelectorAll('section[id]');
var navLinks = document.querySelectorAll('.sidebar a[href^="#"]');
var activeObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
        if (entry.isIntersecting) {
            navLinks.forEach(function(l) { l.classList.remove('active'); });
            var active = document.querySelector('.sidebar a[href="#' + entry.target.id + '"]');
            if (active) { active.classList.add('active'); }
        }
    });
}, { threshold: 0.25, rootMargin: '-60px 0px -50% 0px' });
sections.forEach(function(s) { activeObserver.observe(s); });

// ── Smooth scroll offset for fixed sidebar ────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(function(a) {
    a.addEventListener('click', function(e) {
        var target = document.querySelector(this.getAttribute('href'));
        if (!target) return;
        e.preventDefault();
        var top = target.getBoundingClientRect().top + window.scrollY - 24;
        window.scrollTo({ top: top, behavior: 'smooth' });
    });
});

// ── Image zoom toggle ─────────────────────────────────────────────────
document.querySelectorAll('.diagram-wrap').forEach(function(wrap) {
    wrap.addEventListener('click', function() {
        this.style.position = this.style.position === 'relative' ? '' : 'relative';
        var img = this.querySelector('img');
        if (img.style.maxWidth === '100%' || img.style.maxWidth === '') {
            img.style.maxWidth = 'none';
            img.style.cursor = 'zoom-out';
            wrap.style.cursor = 'zoom-out';
            wrap.style.overflowX = 'auto';
        } else {
            img.style.maxWidth = '100%';
            img.style.cursor = 'zoom-in';
            wrap.style.cursor = 'zoom-in';
            wrap.style.overflowX = 'hidden';
        }
    });
});
</script>
"""


# ── Main generator ────────────────────────────────────────────────────────────

def generate_html_report(output_path: str = None) -> str:
    """Generate the interactive HTML report."""
    if output_path is None:
        output_path = os.path.join(OUTPUTS_DIR, "gnss_diagnostic_report.html")

    result = _load_agent_result()
    memory = result.get("memory", {})
    metrics = result.get("metrics", {})
    trace = result.get("trace", [])
    report_data = memory.get("report", {})
    rpt = report_data.get("report", report_data) if isinstance(report_data, dict) else {}

    # Data for charts
    sky_data  = memory.get("satellite_data", {})
    sats      = sky_data.get("satellites", [])
    dop_data  = memory.get("dop_data", {})
    epochs    = dop_data.get("epochs", [])
    cn0_data  = memory.get("cn0_data", {})
    signals   = cn0_data.get("signals", [])

    # Embed images
    agent_dir  = os.path.dirname(os.path.abspath(__file__))
    beihang_b64 = _img_to_base64(os.path.join(agent_dir, "university logo.png"), "png")
    rcssteap_b64 = _img_to_base64(os.path.join(agent_dir, "RCSSTEAP.jpg"), "jpeg")
    sky_img     = _img_to_base64(os.path.join(SAMPLES_DIR, "sky_plot.png"), "png")
    dop_img     = _img_to_base64(os.path.join(SAMPLES_DIR, "dop_table.png"), "png")
    cn0_img     = _img_to_base64(os.path.join(SAMPLES_DIR, "cn0_chart.png"), "png")

    # Logo HTML
    logo_left  = f'<img src="{beihang_b64}"  alt="Beihang University"/>'  if beihang_b64  else ""
    logo_right = f'<img src="{rcssteap_b64}" alt="RCSSTEAP"/>' if rcssteap_b64 else ""

    # Sidebar logo
    sidebar_logo_html = ""
    if beihang_b64:
        sidebar_logo_html = f"""
        <div class="sidebar-logo-wrap">
            <img class="sidebar-logo" src="{beihang_b64}" alt="Beihang University"/>
            <div class="sidebar-logo-caption">GNSS Diagnostic Agent</div>
        </div>"""

    # Risk
    risk_level = rpt.get("risk_level", "unknown")
    risk_color = {"low": "#66BB6A", "moderate": "#FFB74D", "high": "#FF6B6B", "critical": "#FF0000"}.get(risk_level, "#A0AEBB")
    summary    = rpt.get("executive_summary", "N/A")

    # ── Build trace HTML ──────────────────────────────────────────────────────
    trace_html = ""
    for step in trace:
        it      = step.get("iteration", "?")
        thought = str(step.get("thought", ""))[:280]
        action  = step.get("action", {})
        tool    = action.get("tool", "?") if isinstance(action, dict) else "?"
        obs     = step.get("observation", {})
        obs_text = f"success={obs.get('success', '?')}" if isinstance(obs, dict) else str(obs)[:300]
        latency  = step.get("latency_seconds", 0)
        args_json = json.dumps(action.get("args", {}), indent=2, default=str)[:500] if isinstance(action, dict) else ""

        tool_color = {
            "extract_diagram_data":         "#00BCD4",
            "analyze_positioning_quality":  "#FFB74D",
            "generate_diagnostic_report":   "#FF6B6B",
            "TASK_COMPLETE":                "#66BB6A",
        }.get(tool, "#6B7B8D")

        trace_html += f"""
        <details class="trace-step">
            <summary>
                <span class="step-num">Step {it}</span>
                <span class="tool-badge" style="background:{tool_color}">{tool}</span>
                <span class="step-thought">{thought[:120]}</span>
                <span class="latency">⏱ {latency:.1f}s</span>
            </summary>
            <div class="trace-detail">
                <div class="field"><strong>Thought:</strong> {thought}</div>
                <div class="field"><strong>Action:</strong> {tool}</div>
                {"<div class='prompt-label'>Args</div><pre>" + args_json + "</pre>" if args_json else ""}
                <div class="field"><strong>Observation:</strong> {obs_text}</div>
            </div>
        </details>"""

    # ── Findings ──────────────────────────────────────────────────────────────
    findings = rpt.get("detailed_findings", [])
    findings_html = ""
    for f in findings:
        cls = "finding-error" if "CRITICAL" in str(f) else ("finding-warn" if "WARNING" in str(f) else "finding-ok")
        findings_html += f'<li class="{cls}">{f}</li>'

    recs = rpt.get("recommendations", [])
    recs_html = "".join(f"<li>{r}</li>" for r in recs)

    # ── Extraction table ──────────────────────────────────────────────────────
    ext_results = memory.get("extraction_results", [])
    ext_rows = ""
    for ext in ext_results:
        dtype   = ext.get("extracted_data", {}).get("diagram_type", "?")
        val     = ext.get("validation", {})
        status  = "PASSED" if val.get("is_valid") else "FAILED"
        cls     = "pass" if val.get("is_valid") else "fail"
        latency = ext.get("latency_seconds", "?")
        method  = ext.get("prompting_method", "?")
        conf    = ext.get("extracted_data", {}).get("confidence_score", "—")
        ext_rows += f"""
        <tr>
            <td>{dtype.replace('_',' ').title()}</td>
            <td class="{cls}">{status}</td>
            <td>{latency}s</td>
            <td>{method}</td>
            <td>{conf}</td>
        </tr>"""

    # ── HTML assembly ─────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GNSS Diagnostic Report — Assignment 4</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js" charset="utf-8"></script>
{_css(risk_color)}
</head>
<body>

<!-- Reading progress bar -->
<div id="progress-bar"></div>

<!-- Back to top -->
<a id="back-to-top" href="#" title="Back to top">↑</a>

<!-- Sidebar Navigation -->
<aside class="sidebar">
    {sidebar_logo_html}
    <nav>
        <div class="nav-section">Contents</div>
        <a href="#title">Title Page</a>
        <a href="#links">Project Links</a>
        <a href="#overview">Overview</a>
        <a href="#prompts">Prompt Engineering</a>
        <a href="#prompts-zero" class="sub">Zero-Shot</a>
        <a href="#prompts-few" class="sub">Few-Shot</a>
        <a href="#diagrams">GNSS Diagrams</a>
        <a href="#extraction">Extraction Results</a>
        <a href="#trace">Agent ReAct Trace</a>
        <a href="#charts">Interactive Charts</a>
        <a href="#charts-sky" class="sub">Sky Plot</a>
        <a href="#charts-dop" class="sub">DOP Values</a>
        <a href="#charts-cn0" class="sub">Signal Strength</a>
        <a href="#charts-risk" class="sub">Risk Gauge</a>
        <a href="#findings">Findings</a>
        <a href="#metrics">Evaluation</a>
    </nav>
    <div class="sidebar-footer">
        AI &amp; Advanced Large Models<br/>
        Sessions 9 + 10<br/>
        <span>GNSS in Degraded Environments</span>
    </div>
</aside>

<div class="main">

<!-- ═══════════════════════════════════════════════════════════════
     TITLE PAGE (matches Streamlit dashboard landing)
══════════════════════════════════════════════════════════════════ -->
<section id="title">
<div class="landing-container">
    <div class="landing-logos">
        {logo_left}
        <div style="flex:1"></div>
        {logo_right}
    </div>
    <p class="landing-institution">Beihang University (BUAA)</p>
    <p class="landing-dept">Regional Centre for Space Science and Technology Education<br/>
    in Asia and the Pacific (China) — RCSSTEAP</p>
    <div class="landing-divider"></div>
    <p class="landing-course">Course: <strong>Artificial Intelligence and Advanced Large Models</strong> &nbsp;|&nbsp; Spring 2026</p>
    <p class="landing-title">Assignment 4 — Multimodal Agent Execution</p>
    <p class="landing-subtitle">GNSS Multimodal Diagnostic Agent — Agents, Tool Use &amp; Structured Extraction</p>
    <p class="landing-group">Group 14</p>
    <table class="member-table">
        <tr><th>Name</th><th>Admission Number</th></tr>
        <tr><td>Granny Tlou Molokomme</td><td>LS2525256</td></tr>
        <tr><td>Letsoalo Maile</td><td>LS2525231</td></tr>
        <tr><td>Lemalasia Tevin Muchera</td><td>LS2525229</td></tr>
    </table>
    <div class="brief-card">
        <div class="brief-card-title">About This Report</div>
        <p>This interactive report documents a <strong>multimodal AI agent</strong> that processes GNSS
        engineering diagrams (sky plots, DOP tables, signal strength charts) using
        <strong>vision-based structured extraction</strong> and reasons over the data through a
        <strong>ReAct (Reason + Act) tool-calling loop</strong>. The agent identifies positioning quality
        degradation, assesses risk levels, and generates actionable diagnostic recommendations for
        improving GNSS reliability in challenging environments.</p>
    </div>
    <div class="landing-divider"></div>
    <span class="guide-text">Use the <span>sidebar</span> to navigate · Hover elements for <span>interactive effects</span> · Charts are <span>zoomable &amp; pannable</span></span>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     PROJECT LINKS
══════════════════════════════════════════════════════════════════ -->
<section id="links" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:#29B6F6;"></div>
    <h2 style="color:#29B6F6;">Project Links</h2>
</div>
<div class="card" style="padding:0;overflow:hidden;">
    <a href="https://github.com/Tevin-Wills/gnss-diagnostic-agent" target="_blank" rel="noopener"
       style="display:flex;align-items:center;gap:18px;padding:18px 24px;text-decoration:none;
              border-bottom:1px solid #1E3A5F;transition:background 0.25s;">
        <span style="font-size:2rem;line-height:1;">&#128279;</span>
        <div>
            <div style="font-size:0.78rem;color:#A0AEBB;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;">GitHub Repository</div>
            <div style="font-size:1.05rem;color:#29B6F6;font-weight:600;">
                github.com/Tevin-Wills/gnss-diagnostic-agent
            </div>
            <div style="font-size:0.82rem;color:#A0AEBB;margin-top:3px;">
                Source code, agent pipeline, report generators, GNSS sample data
            </div>
        </div>
    </a>
    <a href="https://gnss-diagnostic-agent.streamlit.app" target="_blank" rel="noopener"
       style="display:flex;align-items:center;gap:18px;padding:18px 24px;text-decoration:none;
              transition:background 0.25s;">
        <span style="font-size:2rem;line-height:1;">&#128640;</span>
        <div>
            <div style="font-size:0.78rem;color:#A0AEBB;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;">Live Streamlit Dashboard</div>
            <div style="font-size:1.05rem;color:#00BCD4;font-weight:600;">
                gnss-diagnostic-agent.streamlit.app
            </div>
            <div style="font-size:0.82rem;color:#A0AEBB;margin-top:3px;">
                Interactive agent execution, real-time extraction, diagnostic visualizations
            </div>
        </div>
    </a>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     SYSTEM OVERVIEW
══════════════════════════════════════════════════════════════════ -->
<section id="overview" class="reveal">
<div class="section-header">
    <div class="accent-bar"></div>
    <h2>System Overview</h2>
</div>
<div class="card">
    <p>This report documents a <strong>multimodal GNSS diagnostic agent</strong> combining
    vision-based structured extraction (Session 10) with agentic tool-calling workflows (Session 9).
    The system processes satellite sky plots, DOP tables, and signal strength charts through a
    ReAct execution loop, producing automated diagnostic reports with risk assessments.</p>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="value">{metrics.get('total_iterations', '?')}</div>
            <div class="label">Iterations</div>
        </div>
        <div class="metric-card">
            <div class="value">{metrics.get('total_time_seconds', '?')}s</div>
            <div class="label">Total Time</div>
        </div>
        <div class="metric-card">
            <div class="value">{'✓' if metrics.get('success') else '✗'}</div>
            <div class="label">Task Success</div>
        </div>
        <div class="metric-card">
            <div class="value">{len(ext_results)}</div>
            <div class="label">Diagrams Processed</div>
        </div>
    </div>
</div>

<div class="info-card">
    <h3 style="margin-top:0">Architecture Components</h3>
    <ul style="list-style:none;padding:0">
        <li style="padding:5px 0;color:var(--text)"><strong style="color:var(--cyan)">extractor.py</strong> — Vision-based structured extraction via llava/Gemini with few-shot prompts</li>
        <li style="padding:5px 0;color:var(--text)"><strong style="color:var(--cyan)">validator.py</strong> — Schema checks, range validation, type coercion, confidence thresholds</li>
        <li style="padding:5px 0;color:var(--text)"><strong style="color:var(--cyan)">agent.py</strong> — ReAct Thought/Action/Observation loop with 3 registered tool schemas</li>
        <li style="padding:5px 0;color:var(--text)"><strong style="color:var(--cyan)">tools.py</strong> — Tool definitions (extract_diagram_data, analyze_positioning_quality, generate_diagnostic_report)</li>
        <li style="padding:5px 0;color:var(--text)"><strong style="color:var(--cyan)">app.py</strong> — Streamlit dashboard with interactive Plotly charts and report export</li>
    </ul>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     PROMPT ENGINEERING
══════════════════════════════════════════════════════════════════ -->
<section id="prompts" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:var(--blue)"></div>
    <h2>Prompt Engineering Process</h2>
</div>

<div id="prompts-zero" class="warn-card">
    <h3 style="color:var(--amber);margin-top:0">Zero-Shot Prompting</h3>
    <p>Directly instructs the vision model with only the target JSON schema. Susceptible to schema
    violations and hallucinated values with smaller models (llava 7B).</p>
    <div class="prompt-label" style="margin-top:12px">Example Prompt Structure</div>
    <div class="prompt-block">Extract satellite data from this GNSS sky plot image.
Return valid JSON matching this schema:
{{"diagram_type": "sky_plot", "satellites": [{{"prn": "...", "elevation_deg": 0, ...}}]}}</div>
</div>

<div id="prompts-few" class="success-card">
    <h3 style="color:var(--green);margin-top:0">Few-Shot Prompting (Recommended)</h3>
    <p>Augments prompts with GNSS-domain examples showing correct PRN identifiers, physically
    plausible elevation/azimuth values, proper C/N0 units (dBHz), and signal quality
    classifications. Reduces schema errors by 15–25%.</p>
    <div class="prompt-label" style="margin-top:12px">Few-Shot Example Structure</div>
    <div class="prompt-block">Example input → Example output (with real GNSS values):
  PRN: "G01", elevation_deg: 42.5, azimuth_deg: 185.3,
  cn0_dbhz: 38.2, signal_quality: "good"
Use these as reference when extracting from the provided image.</div>
</div>

<div class="card">
    <h3 style="margin-top:0">Key Design Decisions</h3>
    <div class="table-wrap">
    <table>
        <thead><tr><th>Strategy</th><th>Zero-Shot</th><th>Few-Shot (Used)</th></tr></thead>
        <tbody>
            <tr><td>JSON Compliance</td><td style="color:var(--coral)">Frequent violations</td><td style="color:var(--green)">Consistent structure</td></tr>
            <tr><td>Extraction Accuracy</td><td>Baseline</td><td style="color:var(--green)">+15–25% improvement</td></tr>
            <tr><td>Hallucination Rate</td><td style="color:var(--coral)">Higher (small models)</td><td style="color:var(--green)">Significantly reduced</td></tr>
            <tr><td>Best For</td><td>Large models (GPT-4V+)</td><td>Small/local models (llava)</td></tr>
        </tbody>
    </table>
    </div>
    <ul style="list-style:none;padding:0;margin-top:14px">
        <li style="padding:5px 0"><strong style="color:var(--cyan)">4-strategy JSON parser</strong> — repair trailing commas, unquoted keys</li>
        <li style="padding:5px 0"><strong style="color:var(--cyan)">Ground truth fallback</strong> — automatic fallback when vision extraction fails validation</li>
        <li style="padding:5px 0"><strong style="color:var(--cyan)">Post-extraction validation</strong> — domain-specific range checks (elevation 0–90°, C/N0 15–55 dBHz)</li>
        <li style="padding:5px 0"><strong style="color:var(--cyan)">Robust type coercion</strong> — string-to-float, list-to-dict for LLM outputs</li>
    </ul>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     GNSS DIAGRAMS
══════════════════════════════════════════════════════════════════ -->
<section id="diagrams" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:var(--blue)"></div>
    <h2>GNSS Engineering Diagrams</h2>
</div>
<p style="color:var(--muted);margin-bottom:16px">Click any diagram to zoom. These are the source images processed by the vision extraction pipeline.</p>

<div class="card">
    <h3>Satellite Sky Plot</h3>
    <p style="color:var(--muted);font-size:13px;margin-bottom:10px">Polar projection of satellite positions. Outer ring = horizon (0°), center = zenith (90°). Colour encodes signal quality.</p>
    {'<div class="diagram-wrap"><img class="diagram" src="' + sky_img + '" alt="Sky Plot"/></div>' if sky_img else '<p style="color:var(--muted)">Image not available</p>'}
</div>

<div class="card">
    <h3>DOP Values Table</h3>
    <p style="color:var(--muted);font-size:13px;margin-bottom:10px">Dilution of Precision metrics (GDOP/PDOP/HDOP/VDOP/TDOP). Lower is better; PDOP &gt; 5 indicates degraded positioning.</p>
    {'<div class="diagram-wrap"><img class="diagram" src="' + dop_img + '" alt="DOP Table"/></div>' if dop_img else '<p style="color:var(--muted)">Image not available</p>'}
</div>

<div class="card">
    <h3>Signal Strength (C/N₀) Chart</h3>
    <p style="color:var(--muted);font-size:13px;margin-bottom:10px">Carrier-to-noise density ratio per satellite. &gt;40 dBHz = strong, 30–40 = moderate, &lt;30 = weak/unreliable.</p>
    {'<div class="diagram-wrap"><img class="diagram" src="' + cn0_img + '" alt="C/N0 Chart"/></div>' if cn0_img else '<p style="color:var(--muted)">Image not available</p>'}
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     EXTRACTION RESULTS
══════════════════════════════════════════════════════════════════ -->
<section id="extraction" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:var(--amber)"></div>
    <h2>Extraction Results &amp; Validation</h2>
</div>
<div class="card">
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>Diagram</th>
                <th>Validation</th>
                <th>Latency</th>
                <th>Method</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>{ext_rows}</tbody>
    </table>
    </div>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     AGENT ReAct TRACE
══════════════════════════════════════════════════════════════════ -->
<section id="trace" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:var(--coral)"></div>
    <h2>Agent ReAct Execution Trace</h2>
</div>
<p style="color:var(--muted);margin-bottom:14px">Each step shows Thought → Action → Observation. Click to expand details. Tool badge colours indicate: <span style="color:#00BCD4">extract</span> · <span style="color:#FFB74D">analyze</span> · <span style="color:#FF6B6B">report</span> · <span style="color:#66BB6A">complete</span>.</p>
{trace_html}
</section>

<!-- ═══════════════════════════════════════════════════════════════
     INTERACTIVE CHARTS
══════════════════════════════════════════════════════════════════ -->
<section id="charts">
<div class="section-header">
    <div class="accent-bar" style="background:var(--cyan)"></div>
    <h2>Interactive Diagnostic Visualizations</h2>
</div>
<p style="color:var(--muted);margin-bottom:16px">All charts are interactive — zoom, pan, and hover for exact values. Double-click to reset the view.</p>

<div id="charts-sky" class="chart-container">
    <div class="chart-label">Satellite Sky Plot</div>
    <div id="skyPlot" style="min-height:580px;width:100%"></div>
</div>

<div id="charts-dop" class="chart-container">
    <div class="chart-label">DOP Values Over Time</div>
    <div id="dopChart" style="min-height:480px;width:100%"></div>
</div>

<div id="charts-cn0" class="chart-container">
    <div class="chart-label">Signal Strength (C/N₀) per Satellite</div>
    <div id="cn0Chart" style="min-height:480px;width:100%"></div>
</div>

<div id="charts-risk" class="chart-container">
    <div class="chart-label">Overall Risk Assessment</div>
    <div id="riskGauge" style="min-height:380px;width:100%"></div>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     FINDINGS & RECOMMENDATIONS
══════════════════════════════════════════════════════════════════ -->
<section id="findings" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:var(--risk)"></div>
    <h2>Diagnostic Findings &amp; Recommendations</h2>
</div>

<div class="risk-banner">
    <div class="risk-label">Risk Level: {risk_level.upper()}</div>
    <p style="margin-top:10px;font-size:14px">{summary}</p>
</div>

<div class="card">
    <h3>Detailed Findings</h3>
    <ul class="findings">{findings_html}</ul>
</div>

<div class="card">
    <h3>Recommendations</h3>
    <ul class="recs">{recs_html}</ul>
</div>
</section>

<!-- ═══════════════════════════════════════════════════════════════
     EVALUATION METRICS
══════════════════════════════════════════════════════════════════ -->
<section id="metrics" class="reveal">
<div class="section-header">
    <div class="accent-bar" style="background:var(--green)"></div>
    <h2>Evaluation Metrics &amp; Course Alignment</h2>
</div>

<div class="card">
    <div class="table-wrap">
    <table>
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
            <tr><td>Total Iterations</td><td>{metrics.get('total_iterations', '?')}</td></tr>
            <tr><td>Total Time</td><td>{metrics.get('total_time_seconds', '?')}s</td></tr>
            <tr><td>Avg Step Time</td><td>{metrics.get('avg_step_time_seconds', '?')}s</td></tr>
            <tr><td>Task Success</td><td class="{'pass' if metrics.get('success') else 'fail'}">{'Yes' if metrics.get('success') else 'No'}</td></tr>
            <tr><td>Tools Called</td><td>{', '.join(metrics.get('tools_called', []))}</td></tr>
        </tbody>
    </table>
    </div>
</div>

<div class="card">
    <h3>Course Concept Alignment (Sessions 9 &amp; 10)</h3>
    <div class="table-wrap">
    <table>
        <thead><tr><th>Course Concept</th><th>Session</th><th>Demonstrated In</th></tr></thead>
        <tbody>
            <tr><td>Agent architecture &amp; design patterns</td><td>S9</td><td>agent.py — core ReAct loop</td></tr>
            <tr><td>Tool calling with JSON schemas</td><td>S9</td><td>tools.py — 3 tool definitions</td></tr>
            <tr><td>ReAct (Reason + Act) pattern</td><td>S9</td><td>Agent trace above</td></tr>
            <tr><td>Guardrails &amp; failure handling</td><td>S9</td><td>agent.py — max iterations, validation</td></tr>
            <tr><td>Multimodal input processing</td><td>S10</td><td>extractor.py — Vision LLM API</td></tr>
            <tr><td>Structured extraction to JSON</td><td>S10</td><td>extractor.py + validator.py</td></tr>
            <tr><td>Few-shot prompting strategy</td><td>S10</td><td>extractor.py — domain examples</td></tr>
            <tr><td>Post-processing &amp; validation</td><td>S10</td><td>validator.py — schema &amp; range checks</td></tr>
        </tbody>
    </table>
    </div>
</div>

<div style="text-align:center;color:var(--muted);margin-top:36px;padding-bottom:20px;font-size:13px">
    Group 14 &nbsp;|&nbsp; Beihang University (BUAA) — RCSSTEAP &nbsp;|&nbsp; Spring 2026<br/>
    <span style="color:var(--cyan);font-size:11px">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
</div>
</section>

</div><!-- /main -->

<!-- ═══════════════════════════════════════════════════════════════
     PLOTLY CHARTS  (deferred until DOM + Plotly both ready)
══════════════════════════════════════════════════════════════════ -->
<script>
function renderCharts() {{
var PLOT_BG  = '#0D1B2A';
var CARD_BG  = '#142A3E';
var GRID_CLR = '#1E3A5F';
var TEXT_CLR = '#E0E7EE';
var MUTED    = '#6B7B8D';

// ── Sky Plot (Polar) ──────────────────────────────────────────────
var sats = {json.dumps(sats, default=str)};
var skyTraces = sats.map(function(sat) {{
    var cn0 = parseFloat(sat.cn0_dbhz || sat.cn0_dbHz || 35);
    var el  = parseFloat(sat.elevation_deg || 45);
    var az  = parseFloat(sat.azimuth_deg || 0);
    var quality = cn0 >= 40 ? 'strong' : (cn0 >= 30 ? 'moderate' : 'weak');
    var color   = {{strong:'#66BB6A', moderate:'#FFB74D', weak:'#FF6B6B'}}[quality];
    return {{
        type: 'scatterpolar', r: [90 - el], theta: [az],
        mode: 'markers+text', text: [sat.prn || '?'], textposition: 'top center',
        marker: {{size: 15, color: color, line: {{width: 1.5, color: 'rgba(255,255,255,0.4)'}},
                  opacity: 0.9}},
        name: (sat.prn || '?') + ' (' + quality + ')',
        hovertemplate: '<b>' + (sat.prn||'?') + '</b><br>Elevation: ' + el + '°<br>Azimuth: ' + az + '°<br>C/N₀: ' + cn0 + ' dBHz<br>Quality: ' + quality + '<extra></extra>'
    }};
}});
Plotly.newPlot('skyPlot', skyTraces, {{
    polar: {{
        bgcolor: CARD_BG,
        radialaxis: {{
            range: [0, 90], tickvals: [0,15,30,45,60,75,90],
            ticktext: ['90°','75°','60°','45°','30°','15°','0°'],
            gridcolor: GRID_CLR, linecolor: GRID_CLR, tickfont: {{color: TEXT_CLR, size: 11}}
        }},
        angularaxis: {{
            direction: 'clockwise', rotation: 90,
            tickvals: [0,45,90,135,180,225,270,315],
            ticktext: ['N','NE','E','SE','S','SW','W','NW'],
            gridcolor: GRID_CLR, linecolor: GRID_CLR, tickfont: {{color: TEXT_CLR, size: 12}}
        }}
    }},
    title: {{text: 'Satellite Sky Plot — Elevation vs Azimuth', font: {{color: TEXT_CLR, size: 15}}}},
    paper_bgcolor: PLOT_BG, font: {{color: TEXT_CLR, family: 'Segoe UI, sans-serif'}},
    height: 560, showlegend: true,
    legend: {{orientation: 'h', y: -0.18, bgcolor: 'rgba(20,42,62,0.85)',
              bordercolor: GRID_CLR, borderwidth: 1, font: {{size: 11}}}},
    margin: {{l: 40, r: 40, t: 60, b: 60}}
}}, {{responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['lasso2d','select2d']}});

// ── DOP Chart ─────────────────────────────────────────────────────
var epochs = {json.dumps(epochs, default=str)};
var times = epochs.map(function(e, i) {{ return e.time || ('T+' + i); }});
var dopDefs = [
    ['gdop','#FF6B6B','solid'],
    ['pdop','#FFB74D','dash'],
    ['hdop','#00BCD4','dot'],
    ['vdop','#66BB6A','dashdot'],
    ['tdop','#29B6F6','longdash']
];
var dopTraces = dopDefs.map(function(d) {{
    return {{
        x: times,
        y: epochs.map(function(e) {{ return parseFloat(e[d[0]] || 0) || null; }}),
        mode: 'lines+markers', name: d[0].toUpperCase(),
        line: {{color: d[1], width: 2.5, dash: d[2]}},
        marker: {{size: 8, symbol: 'circle', line: {{width: 1, color: PLOT_BG}}}},
        hovertemplate: '<b>' + d[0].toUpperCase() + '</b>: %{{y:.2f}}<br>Time: %{{x}}<extra></extra>'
    }};
}});
Plotly.newPlot('dopChart', dopTraces, {{
    title: {{text: 'DOP Values Over Time — Positioning Precision', font: {{color: TEXT_CLR, size: 15}}}},
    xaxis: {{title: {{text: 'Time (UTC)', font: {{color: MUTED}}}}, gridcolor: GRID_CLR,
             zerolinecolor: GRID_CLR, tickfont: {{color: TEXT_CLR}}}},
    yaxis: {{title: {{text: 'DOP Value', font: {{color: MUTED}}}}, gridcolor: GRID_CLR,
             zerolinecolor: GRID_CLR, tickfont: {{color: TEXT_CLR}}}},
    paper_bgcolor: PLOT_BG, plot_bgcolor: CARD_BG,
    font: {{color: TEXT_CLR, family: 'Segoe UI, sans-serif'}},
    height: 460, hovermode: 'x unified',
    legend: {{bgcolor: 'rgba(20,42,62,0.85)', bordercolor: GRID_CLR, borderwidth: 1}},
    shapes: [
        {{type:'line', y0:5,  y1:5,  x0:0, x1:1, xref:'paper', line:{{color:'#FFB74D', width:1.5, dash:'dash'}}}},
        {{type:'line', y0:10, y1:10, x0:0, x1:1, xref:'paper', line:{{color:'#FF6B6B', width:1.5, dash:'dash'}}}}
    ],
    annotations: [
        {{x:1, xref:'paper', y:5,  yref:'y', text:'PDOP threshold (5)', showarrow:false, font:{{color:'#FFB74D', size:11}}, xanchor:'right'}},
        {{x:1, xref:'paper', y:10, yref:'y', text:'Poor (10)',          showarrow:false, font:{{color:'#FF6B6B', size:11}}, xanchor:'right'}}
    ],
    margin: {{l: 60, r: 30, t: 60, b: 60}}
}}, {{responsive: true}});

// ── C/N0 Bar Chart ────────────────────────────────────────────────
var signals = {json.dumps(signals, default=str)};
var prns  = signals.map(function(s) {{ return s.prn || '?'; }});
var cn0s  = signals.map(function(s) {{ return parseFloat(s.cn0_dbhz || s.cn0_dbHz || 0); }});
var bColors = cn0s.map(function(c) {{ return c >= 40 ? '#66BB6A' : (c >= 30 ? '#FFB74D' : '#FF6B6B'); }});
Plotly.newPlot('cn0Chart', [{{
    type: 'bar', x: prns, y: cn0s,
    marker: {{color: bColors, line: {{color: PLOT_BG, width: 1}}, opacity: 0.9}},
    text: cn0s.map(function(c) {{ return c.toFixed(1); }}), textposition: 'outside',
    textfont: {{color: TEXT_CLR, size: 11}},
    hovertemplate: '<b>%{{x}}</b><br>C/N₀: %{{y:.1f}} dBHz<extra></extra>'
}}], {{
    title: {{text: 'Signal Strength (C/N₀) per Satellite', font: {{color: TEXT_CLR, size: 15}}}},
    xaxis: {{title: {{text: 'Satellite PRN', font: {{color: MUTED}}}}, gridcolor: GRID_CLR,
             tickfont: {{color: TEXT_CLR}}}},
    yaxis: {{title: {{text: 'C/N₀ (dBHz)', font: {{color: MUTED}}}}, gridcolor: GRID_CLR,
             zerolinecolor: GRID_CLR, tickfont: {{color: TEXT_CLR}}, range: [0, Math.max(...cn0s, 55) + 5]}},
    paper_bgcolor: PLOT_BG, plot_bgcolor: CARD_BG,
    font: {{color: TEXT_CLR, family: 'Segoe UI, sans-serif'}},
    height: 460,
    shapes: [
        {{type:'line', y0:40, y1:40, x0:-0.5, x1:prns.length-0.5, line:{{color:'#66BB6A', width:1.5, dash:'dash'}}}},
        {{type:'line', y0:30, y1:30, x0:-0.5, x1:prns.length-0.5, line:{{color:'#FFB74D', width:1.5, dash:'dash'}}}},
        {{type:'line', y0:20, y1:20, x0:-0.5, x1:prns.length-0.5, line:{{color:'#FF6B6B', width:1.5, dash:'dash'}}}}
    ],
    annotations: [
        {{x:prns.length, y:40, text:'Strong (≥40)', showarrow:false, font:{{color:'#66BB6A', size:11}}, xanchor:'right'}},
        {{x:prns.length, y:30, text:'Moderate (30)', showarrow:false, font:{{color:'#FFB74D', size:11}}, xanchor:'right'}},
        {{x:prns.length, y:20, text:'Weak (20)', showarrow:false, font:{{color:'#FF6B6B', size:11}}, xanchor:'right'}}
    ],
    margin: {{l: 60, r: 30, t: 60, b: 60}}
}}, {{responsive: true}});

// ── Risk Gauge ────────────────────────────────────────────────────
var riskVal = {{"low": 20, "moderate": 50, "high": 75, "critical": 95}}['{risk_level}'] || 50;
var gaugeColor = riskVal > 60 ? '#FF6B6B' : (riskVal > 30 ? '#FFB74D' : '#66BB6A');
Plotly.newPlot('riskGauge', [{{
    type: 'indicator', mode: 'gauge+number+delta',
    value: riskVal,
    delta: {{reference: 50, increasing: {{color: '#FF6B6B'}}, decreasing: {{color: '#66BB6A'}}}},
    title: {{text: 'GNSS Positioning Risk: <b>{risk_level.upper()}</b>', font: {{size: 17, color: TEXT_CLR}}}},
    number: {{suffix: '%', font: {{color: gaugeColor, size: 40}}}},
    gauge: {{
        axis: {{range: [0, 100], tickcolor: TEXT_CLR, tickfont: {{color: TEXT_CLR, size: 12}}}},
        bar: {{color: gaugeColor, thickness: 0.3}},
        bgcolor: CARD_BG,
        bordercolor: GRID_CLR, borderwidth: 2,
        steps: [
            {{range: [0,  30], color: 'rgba(102,187,106,0.18)'}},
            {{range: [30, 60], color: 'rgba(255,183,77,0.18)'}},
            {{range: [60,100], color: 'rgba(255,107,107,0.18)'}}
        ],
        threshold: {{line: {{color: 'white', width: 3}}, thickness: 0.75, value: riskVal}}
    }}
}}], {{
    paper_bgcolor: PLOT_BG,
    font: {{color: TEXT_CLR, family: 'Segoe UI, sans-serif'}},
    height: 380, margin: {{l: 40, r: 40, t: 60, b: 30}}
}}, {{responsive: true}});
}} // end renderCharts

// Wait for Plotly to be available, then render
(function waitForPlotly() {{
    if (typeof Plotly !== 'undefined') {{
        renderCharts();
    }} else {{
        setTimeout(waitForPlotly, 100);
    }}
}})();
</script>

{SCRIPTS}
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


if __name__ == "__main__":
    path = generate_html_report()
    print(f"HTML report generated: {path}")
