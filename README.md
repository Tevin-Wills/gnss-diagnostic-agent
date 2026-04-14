# GNSS Multimodal Diagnostic Agent

**Assignment 4 — Multimodal Agent Execution**  
Course: Artificial Intelligence and Advanced Large Models  
Beihang University (BUAA) — RCSSTEAP · Spring 2026 · Group 14

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gnss-diagnostic-agent-jwffrautkwjic2npdw3fzt.streamlit.app/)

---

## Live Demo

| Resource | Link |
|----------|------|
| **Streamlit Dashboard** | [gnss-diagnostic-agent-jwffrautkwjic2npdw3fzt.streamlit.app](https://gnss-diagnostic-agent-jwffrautkwjic2npdw3fzt.streamlit.app/) |
| **GitHub Repository** | [github.com/Tevin-Wills/gnss-diagnostic-agent](https://github.com/Tevin-Wills/gnss-diagnostic-agent) |

---

## Overview

A **ReAct (Reason + Act) agentic pipeline** that autonomously processes GNSS engineering diagrams — satellite sky plots, DOP tables, and signal strength charts — using a vision language model for structured data extraction, then diagnoses positioning quality and generates actionable risk assessments.

Covers two course sessions:
- **Session 9** — Agents, Tool Use, ReAct execution loop
- **Session 10** — Multimodal AI, structured extraction from engineering diagrams

---

## Architecture

```
GNSS Diagrams (PNG)
       │
       ▼
┌─────────────────────┐
│   extractor.py      │  Vision LLM (llava / Gemini / OpenRouter)
│   Few-shot prompts  │  → Structured JSON extraction
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│   validator.py      │  Schema checks, range validation,
│                     │  confidence scoring, auto-repair
└─────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│   agent.py — ReAct Loop                             │
│                                                     │
│  Thought → Action → Observation → Thought → ...    │
│                                                     │
│  Tool 1: extract_diagram_data                       │
│  Tool 2: analyze_positioning_quality                │
│  Tool 3: generate_diagnostic_report                 │
└─────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│   app.py            │  Streamlit dashboard
│   report_generator  │  PDF report (ReportLab)
│   generate_html_    │  Interactive HTML report
│   report.py         │
└─────────────────────┘
```

---

## Features

### Streamlit Dashboard (4 tabs)
| Tab | Description |
|-----|-------------|
| **Input & Extraction** | Upload or use sample GNSS diagrams; zero-shot vs few-shot extraction comparison |
| **Agent Execution** | Run the full ReAct agent loop; live step-by-step trace |
| **Diagnostic Report** | Risk banner, findings, recommendations, interactive Plotly charts |
| **Evaluation** | Accuracy metrics, DOP quality assessment, course concept alignment |

### Agent Capabilities
- Processes **3 diagram types**: satellite sky plots, DOP tables, C/N₀ signal charts
- **4-strategy JSON parser** handles local model output variability (direct → fence → bracket-depth → repair)
- **Deterministic pre-extraction** + LLM reasoning for reliable operation with small models (3B params)
- **Risk classification**: Low / Moderate / High / Critical based on satellite count, DOP values, C/N₀, sky coverage

---

## Project Structure

```
gnss-diagnostic-agent/
├── gnss_agent/
│   ├── app.py                  # Streamlit dashboard (main UI)
│   ├── agent.py                # ReAct agent with tool calling
│   ├── tools.py                # 3 tool schemas + implementations
│   ├── extractor.py            # Vision LLM extraction (few-shot)
│   ├── validator.py            # Schema validation & confidence scoring
│   ├── report_generator.py     # PDF report (ReportLab, Book Antiqua)
│   ├── generate_html_report.py # Interactive HTML report
│   ├── generate_notebook.py    # Jupyter notebook export
│   ├── generate_figures.py     # Matplotlib figure generation
│   ├── generate_samples.py     # GNSS sample diagram generation
│   └── config.py               # API providers, thresholds, paths
├── samples/
│   ├── sky_plot.png            # Sample satellite sky plot
│   ├── dop_table.png           # Sample DOP values table
│   ├── cn0_chart.png           # Sample C/N₀ signal chart
│   └── ground_truth.json       # Ground truth for accuracy evaluation
├── .streamlit/
│   ├── config.toml             # Dark navy theme for Cloud
│   └── secrets.toml.example    # API key template for Cloud deployment
├── streamlit_app.py            # Root entry point for Streamlit Cloud
├── requirements.txt
└── AI_PROCESS_LOG.md           # AI tool usage & prompt engineering log
```

---

## Running Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API keys
Copy `.streamlit/secrets.toml.example` to `.env` in the project root and fill in your keys:
```env
API_PROVIDER=openrouter          # or "ollama" for local inference
OPENROUTER_API_KEY=sk-or-v1-...  # Free tier: https://openrouter.ai/keys
GEMINI_API_KEY=AIza...           # Optional: https://aistudio.google.com/apikey
```

For **local inference** (no API key needed): install [Ollama](https://ollama.com) and pull the models:
```bash
ollama pull llava        # Vision model for diagram extraction
ollama pull llama3.2:3b  # Text model for agent reasoning
```

### 3. Run the dashboard
```bash
cd gnss_agent
streamlit run app.py
```

Dashboard opens at `http://localhost:8501`

### 4. Regenerate submission reports
```bash
cd gnss_agent
python generate_html_report.py   # → outputs/gnss_diagnostic_report.html
python report_generator.py       # → outputs/diagnostic_report.pdf
```

---

## Streamlit Cloud Deployment

1. Fork or clone this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select repo, branch `master`, file `streamlit_app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   API_PROVIDER = "openrouter"
   OPENROUTER_API_KEY = "sk-or-v1-..."
   ```
5. Deploy

> **Note:** Ollama (local inference) is not available on Streamlit Cloud. Use `openrouter` or `gemini` as the API provider.

---

## AI Tools Used

| Tool | Purpose |
|------|---------|
| **Claude Code (Sonnet 4.6)** | Architecture design, code generation, debugging |
| **Ollama + llava:7B** | Local vision model for diagram extraction |
| **Ollama + llama3.2:3b** | Local text model for agent reasoning |
| **OpenRouter / Gemini** | Cloud vision & agent fallback |
| **Streamlit** | Interactive dashboard |
| **Plotly** | Interactive visualizations |
| **ReportLab** | PDF report generation |

---

## Group 14

| Name | Admission Number |
|------|-----------------|
| Granny Tlou Molokomme | LS2525256 |
| Letsoalo Maile | LS2525231 |
| Lemalasia Tevin Muchera | LS2525229 |

*Beihang University (BUAA) — RCSSTEAP · Spring 2026*
