"""
Mobile Backend Wrapper for Data20

This module is called by the native Android/iOS code to start the embedded Python backend.
It imports and runs the full mobile_server.py FastAPI application.
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
app = None
server = None
database_path = None
upload_path = None
logs_path = None


def setup_environment(db_path: str, upload_dir: str, logs_dir: str):
    """
    Setup environment for mobile backend

    Called by native code (MainActivity.kt / BackendBridge.swift)

    Args:
        db_path: Path to SQLite database file
        upload_dir: Directory for uploaded files
        logs_dir: Directory for log files
    """
    global database_path, upload_path, logs_path

    database_path = db_path
    upload_path = upload_dir
    logs_path = logs_dir

    # Create directories
    for path in [upload_dir, logs_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)

    # Set environment variables for FastAPI app
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
    Run FastAPI server (blocking)

    Called by native code to start the server.
    This function blocks until the server is stopped.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8001)
    """
    global app, server

    try:
        logger.info(f"🚀 Starting mobile backend on {host}:{port}")

        # Import the full mobile server with detailed error reporting
        try:
            logger.info("📦 Step 1: Importing mobile_server module...")
            from mobile_server import app as mobile_app
            app = mobile_app
            logger.info("✅ Step 1 complete: Full mobile server loaded")
        except ImportError as e:
            logger.error(f"❌ ImportError in mobile_server: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error args: {e.args}")
            import sys
            logger.error(f"   Python path: {sys.path}")
            raise Exception(f"Failed to import mobile_server: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error loading mobile_server: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to load mobile_server: {e}")

        # Import uvicorn
        try:
            logger.info("📦 Step 2: Importing uvicorn...")
            import uvicorn
            logger.info("✅ Step 2 complete: uvicorn imported")
        except ImportError as e:
            logger.error(f"❌ Failed to import uvicorn: {e}")
            raise Exception(f"uvicorn not available: {e}")

        # Configure uvicorn
        try:
            logger.info("⚙️ Step 3: Configuring uvicorn...")
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info",
                access_log=False,  # Save resources on mobile
                loop="asyncio"
            )
            logger.info("✅ Step 3 complete: uvicorn configured")
        except Exception as e:
            logger.error(f"❌ Failed to configure uvicorn: {e}")
            raise Exception(f"uvicorn configuration failed: {e}")

        # Create server
        try:
            logger.info("🔧 Step 4: Creating uvicorn server...")
            server = uvicorn.Server(config)
            logger.info("✅ Step 4 complete: Server instance created")
        except Exception as e:
            logger.error(f"❌ Failed to create server: {e}")
            raise Exception(f"Server creation failed: {e}")

        # Run server (blocking)
        try:
            logger.info(f"🚀 Step 5: Starting server on {host}:{port}...")
            logger.info("✅ Backend server starting (this will block)...")
            server.run()
            logger.info("Server stopped normally")
        except Exception as e:
            logger.error(f"❌ Server runtime error: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Server runtime error: {e}")

    except Exception as e:
        logger.error(f"❌ FATAL: Failed to start server: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        logger.error("Full traceback:")
        traceback.print_exc()
        raise


def stop_server():
    """
    Stop the running server

    Called by native code when app is closing.
    """
    global server

    try:
        if server is not None:
            logger.info("🛑 Stopping server...")
            server.should_exit = True
            server = None
            logger.info("✅ Server stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping server: {e}")


# For testing directly with Python
if __name__ == "__main__":
    import tempfile

    # Setup test environment
    temp_dir = tempfile.gettempdir()

    setup_environment(
        db_path=f"{temp_dir}/test_data20.db",
        upload_dir=f"{temp_dir}/data20_uploads",
        logs_dir=f"{temp_dir}/data20_logs"
    )

    # Run server
    run_server(host="127.0.0.1", port=8001)
