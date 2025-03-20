import subprocess
import os
import sys
import logging
import threading
import time
import webbrowser
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def launch_dashboard(port=8050, open_browser=True):
    """
    Launch the monitoring dashboard in a separate process
    
    Args:
        port (int): Port to run the dashboard on
        open_browser (bool): Whether to automatically open the browser
    """
    try:
        # Get the path to the monitoring dashboard script
        dashboard_path = Path(__file__).parent / "monitoring_dashboard.py"
        
        if not dashboard_path.exists():
            logger.error(f"Dashboard script not found at {dashboard_path}", exc_info=True)
            return False
        
        # Launch the dashboard in a separate process
        logger.info(f"Launching monitoring dashboard on port {port}")
        process = subprocess.Popen(
            [sys.executable, str(dashboard_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for the dashboard to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Dashboard failed to start: {stderr.decode()}", exc_info=True)
            return False
        
        # Open browser if requested
        if open_browser:
            url = f"http://localhost:{port}"
            logger.info(f"Opening dashboard in browser: {url}")
            webbrowser.open(url)
        
        logger.info("Dashboard launched successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error launching dashboard: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    launch_dashboard()
