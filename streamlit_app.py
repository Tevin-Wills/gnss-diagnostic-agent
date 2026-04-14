"""Root entry point for Streamlit Cloud deployment.

Streamlit Cloud looks for streamlit_app.py in the repo root.
This file ensures outputs/ and samples/ directories exist, then
launches the main dashboard from gnss_agent/app.py.
"""
import os
import sys

# Ensure runtime directories exist
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs", "figures"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "samples"), exist_ok=True)

# Streamlit Cloud injects secrets as environment variables automatically.
# Expose them so python-dotenv / os.environ.get() picks them up in config.py.
try:
    import streamlit as st
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ.setdefault(k, v)
except Exception:
    pass

# Add gnss_agent to path and run the dashboard
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "gnss_agent"))
exec(open(os.path.join(os.path.dirname(__file__), "gnss_agent", "app.py")).read())
