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
    # PyInstaller creates a _internal folder with all bundled files
    application_path = Path(sys.executable).parent
    bundle_dir = application_path / "_internal"
    app_file = bundle_dir / "src" / "ui" / "app_new.py"
else:
    # Running as script
    application_path = Path(__file__).parent
    bundle_dir = application_path
    app_file = application_path / "src" / "ui" / "app_new.py"

# Set working directory and add to path
os.chdir(application_path)
sys.path.insert(0, str(bundle_dir))
sys.path.insert(0, str(application_path))

# Import streamlit and run the app
from streamlit.web import cli as stcli

if __name__ == "__main__":
    # Configure Streamlit to run in headless mode
    sys.argv = [
        "streamlit",
        "run",
        str(app_file),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.port=8501",
        "--server.address=localhost",
        "--global.developmentMode=false",
    ]

    # sys.exit(stcli.main())
    print(stcli.main())
