"""
Launcher script for spch2txt Recorder Client.

This script launches the Streamlit app with proper configuration.
PyInstaller will bundle this as the main entry point.
"""

import os
import sys
from pathlib import Path

# Add the current directory to path
if getattr(sys, "frozen", False):
    # Running as compiled executable
    application_path = Path(sys.executable).parent
else:
    # Running as script
    application_path = Path(__file__).parent

os.chdir(application_path)
sys.path.insert(0, str(application_path))

# Import streamlit and run the app
from streamlit.web import cli as stcli

if __name__ == "__main__":
    # Configure Streamlit to run in headless mode
    sys.argv = [
        "streamlit",
        "run",
        str(application_path / "src" / "ui" / "app_new.py"),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.port=8501",
        "--server.address=localhost",
    ]

    sys.exit(stcli.main())
