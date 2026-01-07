"""
Simplified Mobile Backend - ULTRA MINIMAL version for testing
NO external dependencies - only Python standard library
Just confirms Python environment works without ANY pip packages
"""

import os
import sys
import time

# Simple print-based logging (faster than logging module)
def log_info(message):
    print(f"INFO: {message}", flush=True)

def log_error(message):
    print(f"ERROR: {message}", flush=True, file=sys.stderr)

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

    # Create directories (without pathlib to be faster)
    for path in [upload_dir, logs_dir]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # Set environment variables
    os.environ['DATA20_DATABASE_PATH'] = db_path
    os.environ['DATA20_UPLOAD_PATH'] = upload_dir
    os.environ['DATA20_LOGS_PATH'] = logs_dir
    os.environ['ENVIRONMENT'] = 'mobile'

    log_info("Environment configured:")
    log_info(f"  Database: {db_path}")
    log_info(f"  Uploads: {upload_dir}")
    log_info(f"  Logs: {logs_dir}")


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """
    Run minimal test server (just confirms Python works)

    NOTE: This is an ULTRA-SIMPLIFIED version for testing.
    NO pip dependencies - only Python standard library.
    """
    global is_running

    try:
        log_info(f"Starting ULTRA-MINIMAL mobile backend on {host}:{port}")
        log_info("Python backend initialized successfully!")
        log_info("  This is a test version with ZERO pip dependencies")
        log_info("  Backend is 'running' in demo mode")

        is_running = True

        # Just keep running (no actual server for now)
        # This confirms Python works without crashing
        while is_running:
            time.sleep(1)

        log_info("Backend test completed successfully")

    except Exception as e:
        log_error(f"Failed to start server: {e}")
        # Print traceback manually without importing traceback module
        import sys
        import traceback
        traceback.print_exc()
        raise


def stop_server():
    """
    Stop the test server
    """
    global is_running

    try:
        log_info("Stopping server...")
        is_running = False
        log_info("Server stopped")
    except Exception as e:
        log_error(f"Error stopping server: {e}")


# For testing
if __name__ == "__main__":
    import tempfile
    temp_dir = tempfile.gettempdir()

    setup_environment(
        db_path=os.path.join(temp_dir, "test_data20.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads"),
        logs_dir=os.path.join(temp_dir, "data20_logs")
    )

    run_server(host="127.0.0.1", port=8001)
