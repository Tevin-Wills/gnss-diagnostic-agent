"""Configuration for the GNSS Multimodal Diagnostic Agent."""
import os
from dotenv import load_dotenv

# Load API keys from .env file (one directory up from gnss_agent/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# ── API Provider ────────────────────────────────────────────────────────────
# Options: "ollama" (local, free), "openrouter" (cloud, free tier), "gemini" (cloud)
API_PROVIDER = os.environ.get("API_PROVIDER", "ollama")

# ── Ollama (Local) ─────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_VISION_MODEL = "llava"           # Vision model for diagram extraction (needs 7B+ for JSON output)
OLLAMA_AGENT_MODEL = "llama3.2:3b"      # Fast text model for agent reasoning

# ── Gemini API ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash-lite"

# ── OpenRouter API ──────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Free vision-capable model for extraction (Google Gemma 3 — vision support)
OPENROUTER_MODEL = "google/gemma-3-27b-it:free"
# Free text model for agent reasoning (NVIDIA — reliable, 262k context)
OPENROUTER_AGENT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
# Fallback agent model if primary fails (Qwen — different provider)
OPENROUTER_AGENT_MODEL_FALLBACK = "qwen/qwen3-next-80b-a3b-instruct:free"

# ── Agent Settings ──────────────────────────────────────────────────────────
MAX_AGENT_ITERATIONS = 8
CONFIDENCE_THRESHOLD = 0.80

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# ── GNSS Domain Constants ──────────────────────────────────────────────────
VALID_RANGES = {
    "elevation_deg": (0, 90),
    "azimuth_deg": (0, 360),
    "cn0_dbhz": (0, 60),
    "gdop": (0, 50),
    "pdop": (0, 50),
    "hdop": (0, 50),
    "vdop": (0, 50),
    "tdop": (0, 50),
}

# DOP quality thresholds (standard interpretation)
DOP_QUALITY = {
    "ideal": (0, 1),
    "excellent": (1, 2),
    "good": (2, 5),
    "moderate": (5, 10),
    "fair": (10, 20),
    "poor": (20, 50),
}

# Minimum satellites for reliable positioning
MIN_SATELLITES = 4
MIN_CN0_STRONG = 35  # dBHz - strong signal threshold
MIN_CN0_WEAK = 20    # dBHz - below this is unusable
