"""
Simplified Mobile Backend - Minimal version for testing
No heavy dependencies (no pandas, no sqlalchemy, no fastapi)
Just a simple HTTP server to verify Python works
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
database_path = None
upload_path = None
logs_path = None
is_running = False


def setup_environment(db_path: str, upload_dir: str, logs_dir: str):
    """
    Setup environment for mobile backend
    """
    global database_path, upload_path, logs_path

    database_path = db_path
    upload_path = upload_dir
    logs_path = logs_dir

    # Create directories
    for path in [upload_dir, logs_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)

    # Set environment variables
    os.environ['DATA20_DATABASE_PATH'] = db_path
    os.environ['DATA20_UPLOAD_PATH'] = upload_dir
    os.environ['DATA20_LOGS_PATH'] = logs_dir
    os.environ['ENVIRONMENT'] = 'mobile'

    logger.info(f"✅ Environment configured:")
    logger.info(f"   Database: {db_path}")
    logger.info(f"   Uploads: {upload_dir}")
    logger.info(f"   Logs: {logs_dir}")


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """
    Run minimal test server (just confirms Python works)

    NOTE: This is a SIMPLIFIED version for testing.
    Full FastAPI server is too heavy for initial mobile deployment.
    """
    global is_running

    try:
        logger.info(f"🚀 Starting SIMPLIFIED mobile backend on {host}:{port}")
        logger.info("✅ Python backend initialized successfully!")
        logger.info("   This is a test version without FastAPI/heavy dependencies")
        logger.info("   Backend is 'running' in demo mode")

        is_running = True

        # Just keep running (no actual server for now)
        # This confirms Python works without crashing
        import time
        while is_running:
            time.sleep(1)

        logger.info("✅ Backend test completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        raise


def stop_server():
    """
    Stop the test server
    """
    global is_running

    try:
        logger.info("🛑 Stopping server...")
        is_running = False
        logger.info("✅ Server stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping server: {e}")


# For testing
if __name__ == "__main__":
    import tempfile
    temp_dir = tempfile.gettempdir()

    setup_environment(
        db_path=f"{temp_dir}/test_data20.db",
        upload_dir=f"{temp_dir}/data20_uploads",
        logs_dir=f"{temp_dir}/data20_logs"
    )

    run_server(host="127.0.0.1", port=8001)
