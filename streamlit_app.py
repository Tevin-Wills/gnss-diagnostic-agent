"""Root entry point for Streamlit Cloud deployment.

Uses runpy.run_path() so that __file__ is correctly set inside app.py,
which is required for logo loading (pathlib.Path(__file__).parent) and
for st.markdown(unsafe_allow_html=True) to render HTML properly.
"""
import os
import sys
import runpy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure runtime directories exist (outputs/ is gitignored, created fresh on Cloud)
os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "outputs", "figures"), exist_ok=True)

# Streamlit Cloud injects secrets as environment variables automatically.
# config.py reads os.environ.get(...) which picks them up with no extra work.

# Add gnss_agent/ to sys.path so all relative imports in app.py resolve
gnss_dir = os.path.join(BASE_DIR, "gnss_agent")
if gnss_dir not in sys.path:
    sys.path.insert(0, gnss_dir)

# Run the dashboard — run_path sets __file__ correctly inside app.py
runpy.run_path(os.path.join(gnss_dir, "app.py"), run_name="__main__")
