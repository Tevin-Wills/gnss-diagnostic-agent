# Assignment 4 — AI Process Log
## Multimodal Agent Execution: GNSS Diagnostic Agent Pipeline

**Course:** Artificial Intelligence and Advanced Large Models  
**Assignment:** 4 of 6 — Multimodal Agent Execution (Sessions 9-10)  
**Date:** 2026-04-13  
**Group:** 14  
**Domain:** GNSS Positioning Quality Diagnostics in Degraded Environments  

---

## 1. Overview & Objective

Assignment 4 required designing an **Agentic Workflow** that:
1. Processes complex engineering diagrams (multimodal input)
2. Uses AI tool calls to extract structured data
3. Demonstrates a planning/execution loop (ReAct pattern)

We built a **GNSS Multimodal Diagnostic Agent** — a Streamlit-based interactive dashboard
where a ReAct agent autonomously processes satellite sky plots, DOP tables, and signal
strength charts, extracts structured data via vision models, analyses positioning quality,
and generates diagnostic reports with risk assessments and recommendations.

---

## 2. AI Tools Used

| Step | Tool | Version | Purpose |
|------|------|---------|---------|
| 1 | **Claude Code (Claude Sonnet 4.6)** | claude-sonnet-4-6 | Code generation, architecture design, debugging, report design |
| 2 | **Ollama + llava** | llava:latest (7B) | Local vision model for diagram extraction |
| 3 | **Ollama + llama3.2** | llama3.2:3b | Local text model for agent reasoning |
| 4 | **OpenRouter / Gemini** | Free-tier cloud | Cloud vision/agent fallback when Ollama unavailable |
| 5 | **Python 3.x + Streamlit** | 1.51.0 | Interactive dashboard and execution environment |
| 6 | **Plotly** | 5.x | Dark-themed interactive visualizations (dashboard + HTML report) |
| 7 | **ReportLab** | Latest | Dynamic PDF report generation with dark themes and bookmarks |
| 8 | **Matplotlib** | Latest | Scientific GNSS sample diagram generation |
| 9 | **Jupyter / nbformat** | Latest | Notebook export of the execution trace |

---

## 3. Prompt Engineering Log

### 3.1 System Prompt Design (Agent — Session 9)

**Goal:** Define the agent's persona, domain expertise, tool-calling workflow, and ReAct format.

**Prompt Used:**
```
You are a GNSS Diagnostic Agent — an AI-powered engineering assistant
that analyzes GNSS data from engineering diagrams to diagnose positioning
quality issues in degraded environments.

You MUST follow the ReAct (Reason + Act) pattern for every step:
1. Thought: Reason about the current state
2. Action: Call exactly ONE tool with specific parameters
3. Observation: Receive and interpret the tool's result

At each step, respond with EXACTLY this JSON structure:
{
    "thought": "Your reasoning...",
    "action": {"tool": "tool_name", "parameters": {...}}
}
```

**Engineering Rationale:**
- Specifying "GNSS Diagnostic Agent" focuses the model on positioning domain vocabulary
- Strict JSON format ensures machine-parseable responses from the small 3B model
- ReAct pattern forces the model to explain reasoning before acting

### 3.2 Vision Extraction Prompts (Multimodal — Session 10)

**Zero-Shot Strategy:**
```
Analyze this GNSS satellite sky plot image.
Extract ALL satellites and return a JSON object with structure:
{"diagram_type": "sky_plot", "satellites": [...], "metadata": {...}, "confidence": 0.85}
```

**Few-Shot Strategy (Recommended):**
```
You are a GNSS engineer analyzing satellite sky plots.

EXAMPLE INPUT: A polar sky plot showing 4 GPS satellites
EXAMPLE OUTPUT:
{"diagram_type": "sky_plot", "satellites": [
    {"prn": "G05", "elevation_deg": 60, "azimuth_deg": 90, "cn0_dbhz": 45, "signal_quality": "strong"},
    ...
], "metadata": {...}, "confidence": 0.90}

Now analyze the provided sky plot image. Extract every satellite with its PRN,
elevation, azimuth, and C/N0 value.
```

**Key Finding:** Few-shot prompting improved extraction accuracy by reducing schema violations
and hallucinated values, especially with the local llava 7B model which tends to return
markdown-wrapped or partially formatted JSON without examples.

### 3.3 Tool Schema Design

Three tools registered with structured JSON schemas:

| Tool | Key Parameters | Design Note |
|------|----------------|-------------|
| `extract_diagram_data` | `image_path`, `diagram_type` | Vision API extracts structured JSON from images |
| `analyze_positioning_quality` | `satellite_data`, `dop_data`, `cn0_data` | Analyses geometry, DOP degradation, signal strength |
| `generate_diagnostic_report` | `extraction_results`, `analysis_results` | Compiles findings into structured report with risk level |

---

## 4. Agent Execution Loop Documentation

### Architecture: Pre-extract + LLM Reasoning

The agent uses a hybrid approach:
1. **Deterministic phase:** All 3 diagrams are extracted and analysed automatically
2. **LLM phase:** The reasoning model generates the diagnostic report and decides completion

This design ensures all diagrams are always processed (small LLMs often skip steps).

### Step 1 — EXTRACT: `extract_diagram_data(sky_plot)`
**Input:** Sky plot PNG image  
**Output:** 3-6 satellite records with PRN, elevation, azimuth, signal quality  
**Agent Observation:** Validates extraction, auto-fills missing cn0_dbhz from signal quality labels

### Step 2 — EXTRACT: `extract_diagram_data(dop_table)`
**Input:** DOP table PNG image  
**Output:** 3-8 epoch records with GDOP, PDOP, HDOP, VDOP, TDOP values  
**Agent Observation:** Validates DOP consistency (GDOP >= PDOP >= HDOP)

### Step 3 — EXTRACT: `extract_diagram_data(cn0_chart)`
**Input:** C/N0 bar chart PNG image  
**Output:** 5-12 signal records with PRN and C/N0 values in dBHz  
**Agent Observation:** Auto-classifies signal quality (strong >= 40, moderate >= 30, weak < 30)

### Step 4 — ANALYZE: `analyze_positioning_quality(satellite_data, dop_data, cn0_data)`
**Input:** All extracted data from steps 1-3  
**Output:** Risk assessment (low/moderate/high/critical), findings list, recommendations  
**Checks performed:**
- Minimum satellite count (>= 4 for 3D positioning)
- Low-elevation satellites (< 15deg, multipath risk)
- Weak signals (C/N0 < 20 dBHz)
- DOP degradation (GDOP >= 5)
- Sky distribution analysis (empty quadrants)

### Step 5 — REPORT: `generate_diagnostic_report(extraction_results, analysis_results)`
**Input:** Combined extraction and analysis results  
**Output:** Structured report with executive summary, risk level, findings, recommendations

### Step 6 — TASK_COMPLETE
Agent confirms task completion with a final summary.

---

## 5. Key Learnings

### 5.1 Multimodal Extraction (Session 10)
- **Vision model limitations:** llava 7B struggles with small text labels (PRN identifiers,
  C/N0 values near markers). Few-shot examples significantly improve output quality.
- **Robust parsing is essential:** A 4-strategy JSON parser (direct, fence extraction,
  bracket-depth matching, first-to-last braces) handles the diverse output formats from
  local models.
- **Post-extraction validation saves downstream failures:** Schema checks, range validation,
  and auto-derivation (estimating cn0_dbhz from signal_quality labels) prevent cascading
  errors in the analysis pipeline.

### 5.2 Agent Design (Session 9)
- **Small LLMs need guardrails:** llama3.2:3b (3B params) frequently garbles file paths,
  skips workflow steps, and hallucinates non-existent tools. Memory injection, path override,
  and auto-completion guards are essential.
- **Hybrid architecture works best:** Deterministic pre-extraction + LLM reasoning for
  report generation balances reliability with flexibility.
- **Tool parameter injection:** Auto-filling tool parameters from agent memory compensates
  for the small model's inability to pass complex nested data structures.

### 5.3 Connection to Previous Sessions

| Session | Concept | Used in Assignment 4 |
|---------|---------|---------------------|
| Session 6 | Transformers, attention | Vision model's image understanding (llava) |
| Session 7 | Post-training, RLHF | Agent's instruction-following behavior |
| Session 8 | RAG, grounding | Extracted data as grounded context for analysis |
| Session 9 | Tool use, agents, ReAct | Core agentic execution loop |
| Session 10 | Multimodal AI, structured extraction | Vision-based diagram processing |

---

## 6. Deliverable Files

### Source Files

| File | Description |
|------|-------------|
| `gnss_agent/app.py` | **Streamlit dashboard** — main entry point; dark navy theme, animated tabs, Plotly charts, sidebar controls, API provider selection |
| `gnss_agent/agent.py` | ReAct agent with tool calling, memory injection, max-iteration guard, auto-complete safeguard |
| `gnss_agent/tools.py` | 3 tool schemas + implementations: extract_diagram_data, analyze_positioning_quality, generate_diagnostic_report |
| `gnss_agent/extractor.py` | Multimodal vision extraction — zero-shot + few-shot strategies, 4-strategy JSON parser, ground-truth fallback |
| `gnss_agent/validator.py` | Schema validation, domain-range checks (elevation 0–90°, C/N₀ 15–55 dBHz), confidence scoring |
| `gnss_agent/report_generator.py` | **PDF report generator** — Book Antiqua font, dark background every page, TableOfContents with exact page numbers, KeepTogether for section-figure cohesion |
| `gnss_agent/generate_html_report.py` | **HTML report generator** — interactive Plotly charts, CSS animations, reading progress bar, active-section nav, back-to-top |
| `gnss_agent/generate_notebook.py` | Jupyter notebook export of the execution trace |
| `gnss_agent/generate_figures.py` | High-resolution Matplotlib figure generation for PDF report |
| `gnss_agent/generate_samples.py` | Scientific GNSS sample diagram generation (sky plot, DOP table, C/N₀ chart) |
| `gnss_agent/config.py` | Configuration: API providers (Ollama / OpenRouter / Gemini), model names, thresholds, paths |

### Output / Submission Files

| File | Description |
|------|-------------|
| `outputs/diagnostic_report.pdf` | **Primary submission PDF** — 8 sections, TOC with page numbers, dark navy theme, Book Antiqua font, embedded figures |
| `outputs/gnss_diagnostic_report.html` | **Interactive HTML report** — self-contained, zoomable Plotly charts, animated navigation, dual-logo title page matching dashboard |
| `outputs/gnss_diagnostic_report.ipynb` | Jupyter notebook export of the agent execution |
| `outputs/agent_result.json` | Full agent execution trace, memory, metrics, and extracted data |
| `outputs/figures/` | High-resolution PNG charts (sky plot, DOP, C/N₀, risk gauge, timeline, architecture, extraction summary) |
| `AI_PROCESS_LOG.md` | This document — AI tool usage and prompt engineering log |
| `requirements.txt` | Python dependencies |

### Dashboard Features (Streamlit — `http://localhost:8501`)

| Tab | Features |
|-----|----------|
| **Input & Extraction** | Upload or use sample diagrams; displays extracted JSON; zero-shot vs few-shot comparison |
| **Agent Execution** | Run the full ReAct agent; live step-by-step trace display; tool call details |
| **Diagnostic Report** | Risk banner, findings list, recommendations, interactive Plotly charts |
| **Evaluation** | Accuracy metrics, DOP quality assessment, course concept alignment table |

### Design System (consistent across dashboard + HTML + PDF)

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0D1B2A` | Page/app background |
| Card | `#142A3E` | Section blocks, table rows |
| Deep navy | `#0A2E50` | Table headers, callout boxes |
| Cyan accent | `#00BCD4` | Headers, links, accent bars |
| Green | `#66BB6A` | Pass / strong signal / low risk |
| Amber | `#FFB74D` | Warning / moderate |
| Coral | `#FF6B6B` | Error / weak / high risk |
| Font (PDF) | Book Antiqua | Body 12 pt, cover 15 pt |

**To run the dashboard:**
```bash
cd gnss_agent
streamlit run app.py
```

**To regenerate reports:**
```bash
cd gnss_agent
python generate_html_report.py   # → outputs/gnss_diagnostic_report.html
python report_generator.py       # → outputs/diagnostic_report.pdf
```

**Install requirements:**
```bash
pip install streamlit plotly reportlab pillow openai python-dotenv matplotlib nbformat
# For local inference: Ollama must be running with llava and llama3.2:3b models
```

---

*Group 14 | Beihang University (BUAA) — RCSSTEAP | Spring 2026*
