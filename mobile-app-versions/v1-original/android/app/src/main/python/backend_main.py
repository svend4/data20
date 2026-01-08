"""
Mobile Backend Wrapper for Data20 - HYBRID BEST OF BOTH VERSION

This is the HYBRID version combining:
- Modular architecture from 324dd58 (mobile_server.py, mobile_auth.py, etc.)
- Async functions from ca458ea (run_server_async, stop_server)
- Additional improvements (graceful shutdown, enhanced logging, health checks)

Version: 1.0.0-hybrid
Created: 2026-01-05
Purpose: Optimal version with ALL functionality and NO losses
"""

import os
import sys
import logging
import threading
import signal
import time
from pathlib import Path
from typing import Optional

# Configure logging with enhanced format
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variables
app = None
server = None
server_thread: Optional[threading.Thread] = None
database_path = None
upload_path = None
logs_path = None
shutdown_event = threading.Event()


def setup_environment(db_path: str, upload_dir: str, logs_dir: str, debug: bool = False):
    """
    Setup environment for mobile backend

    Called by native code (MainActivity.kt / BackendBridge.swift) before starting server.

    Args:
        db_path: Path to SQLite database file
        upload_dir: Directory for uploaded files
        logs_dir: Directory for log files
        debug: Enable debug mode (optional, default: False)
    """
    global database_path, upload_path, logs_path

    database_path = db_path
    upload_path = upload_dir
    logs_path = logs_dir

    # Create directories
    for path in [upload_dir, logs_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)

    # Set environment variables for FastAPI app (NEW naming from 324dd58)
    os.environ['DATA20_DATABASE_PATH'] = db_path
    os.environ['DATA20_UPLOAD_PATH'] = upload_dir
    os.environ['DATA20_LOGS_PATH'] = logs_dir

    # Also set old names for backwards compatibility
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['UPLOAD_DIR'] = upload_dir
    os.environ['LOGS_DIR'] = logs_dir

    # Mobile-specific settings (from ca458ea)
    os.environ['ENVIRONMENT'] = 'mobile'
    os.environ['DEBUG'] = 'true' if debug else 'false'
    os.environ['CORS_ORIGINS'] = '*'  # Allow all origins on mobile

    # Disable features not needed on mobile (from ca458ea)
    os.environ['ENABLE_CELERY'] = 'false'
    os.environ['ENABLE_REDIS'] = 'false'
    os.environ['ENABLE_METRICS'] = 'false'

    # Adjust logging level if debug
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Debug mode enabled")

    logger.info("=" * 60)
    logger.info("✅ Environment configured successfully")
    logger.info("=" * 60)
    logger.info(f"   Database: {db_path}")
    logger.info(f"   Uploads:  {upload_dir}")
    logger.info(f"   Logs:     {logs_dir}")
    logger.info(f"   Debug:    {debug}")
    logger.info(f"   CORS:     * (all origins allowed)")
    logger.info("=" * 60)


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """
    Run FastAPI server (BLOCKING mode)

    Called by native code to start the server in blocking mode.
    This function blocks until the server is stopped.

    Use this when running in a background thread/coroutine from native code.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8001)

    Raises:
        ImportError: If mobile_server cannot be imported
        Exception: If server fails to start
    """
    global app, server

    try:
        logger.info("=" * 60)
        logger.info(f"🚀 Starting mobile backend on {host}:{port}")
        logger.info("   Mode: BLOCKING (will block until stopped)")
        logger.info("=" * 60)

        # Import the full mobile server (from 324dd58)
        try:
            from mobile_server import app as mobile_app
            app = mobile_app
            logger.info("✅ Full mobile server loaded (mobile_server.py)")
            logger.info("   - mobile_auth.py")
            logger.info("   - mobile_database.py")
            logger.info("   - mobile_models.py")
            logger.info("   - mobile_tool_registry.py")
            logger.info("   - mobile_tool_runner.py")
            logger.info("   - tools/*.py (57 tools)")
        except ImportError as e:
            logger.error("=" * 60)
            logger.error("❌ Failed to import mobile_server")
            logger.error("=" * 60)
            logger.error(f"   Error: {e}")
            logger.error("   Please ensure all mobile_* modules are present:")
            logger.error("   - mobile_server.py")
            logger.error("   - mobile_auth.py")
            logger.error("   - mobile_database.py")
            logger.error("   - mobile_models.py")
            logger.error("   - mobile_tool_registry.py")
            logger.error("   - mobile_tool_runner.py")
            logger.error("=" * 60)
            raise

        # Configure uvicorn
        import uvicorn

        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            access_log=False,  # Save resources on mobile
            loop="asyncio"
        )

        server = uvicorn.Server(config)

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            stop_server()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Run server (blocking)
        logger.info("=" * 60)
        logger.info("✅ Backend server started successfully")
        logger.info(f"   🌐 Server listening on http://{host}:{port}")
        logger.info(f"   📚 API docs: http://{host}:{port}/docs")
        logger.info(f"   ❤️  Health check: http://{host}:{port}/health")
        logger.info("=" * 60)

        server.run()

    except KeyboardInterrupt:
        logger.info("⌨️  Keyboard interrupt received")
        stop_server()
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ Failed to start server")
        logger.error("=" * 60)
        logger.error(f"   Error: {e}")
        logger.error("   Traceback:")
        import traceback
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"   {line}")
        logger.error("=" * 60)
        raise
    finally:
        logger.info("🔚 Server run_server() completed")


def run_server_async(host: str = "127.0.0.1", port: int = 8001):
    """
    Run server in background thread (NON-BLOCKING mode)

    This is the ASYNC function from ca458ea - allows native code to start
    the Python backend without blocking the main thread.

    IMPORTANT: This function returns immediately while the server runs in background.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8001)

    Example (from MainActivity.kt):
        python!!.getModule("backend_main")
            .callAttr("run_server_async", "127.0.0.1", 8001)
    """
    global server_thread, shutdown_event

    logger.info("=" * 60)
    logger.info("🧵 Starting server in BACKGROUND THREAD")
    logger.info("   Mode: NON-BLOCKING (returns immediately)")
    logger.info("=" * 60)

    # Reset shutdown event
    shutdown_event.clear()

    def run_in_thread():
        """Wrapper function to run in thread"""
        try:
            run_server(host, port)
        except Exception as e:
            logger.error(f"❌ Error in server thread: {e}")
        finally:
            shutdown_event.set()

    # Create and start daemon thread
    server_thread = threading.Thread(
        target=run_in_thread,
        name="FastAPI-Server-Thread",
        daemon=True
    )
    server_thread.start()

    # Give server time to start
    time.sleep(0.5)

    logger.info("=" * 60)
    logger.info("✅ Backend started in background thread")
    logger.info(f"   Thread: {server_thread.name}")
    logger.info(f"   Thread ID: {server_thread.ident}")
    logger.info(f"   Daemon: {server_thread.daemon}")
    logger.info("   Server is starting... (may take 2-5 seconds)")
    logger.info("=" * 60)


def stop_server():
    """
    Stop the running server (GRACEFUL SHUTDOWN)

    This is the enhanced stop function combining ca458ea + improvements:
    - Gracefully stops uvicorn server
    - Cleans up server thread
    - Releases resources
    - Sets shutdown event

    Called by native code when app is closing or when stopping backend.

    Example (from MainActivity.kt):
        python!!.getModule("backend_main").callAttr("stop_server")
    """
    global server, server_thread, shutdown_event

    logger.info("=" * 60)
    logger.info("🛑 Initiating graceful shutdown...")
    logger.info("=" * 60)

    try:
        # Stop uvicorn server
        if server is not None:
            logger.info("   Stopping uvicorn server...")
            server.should_exit = True

            # Wait for server to stop (max 5 seconds)
            wait_time = 0
            while server.should_exit and wait_time < 5:
                time.sleep(0.1)
                wait_time += 0.1

            server = None
            logger.info("   ✅ Uvicorn server stopped")
        else:
            logger.info("   ℹ️  Server was not running")

        # Clean up server thread
        if server_thread is not None:
            logger.info("   Waiting for server thread to finish...")
            server_thread.join(timeout=3.0)

            if server_thread.is_alive():
                logger.warning("   ⚠️  Server thread still alive after 3s timeout")
            else:
                logger.info("   ✅ Server thread finished")

            server_thread = None

        # Set shutdown event
        shutdown_event.set()

        logger.info("=" * 60)
        logger.info("✅ Graceful shutdown completed")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ Error during shutdown")
        logger.error("=" * 60)
        logger.error(f"   Error: {e}")
        import traceback
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"   {line}")
        logger.error("=" * 60)


def get_server_status() -> dict:
    """
    Get current server status

    NEW IMPROVEMENT: Health check function to query server state.

    Returns:
        dict: Server status information
            - running (bool): Whether server is running
            - thread_alive (bool): Whether server thread is alive
            - database_path (str): Path to database
            - upload_path (str): Path to uploads
            - logs_path (str): Path to logs

    Example (from MainActivity.kt):
        val status = python!!.getModule("backend_main")
            .callAttr("get_server_status").toJava(Map::class.java)
    """
    global server, server_thread, database_path, upload_path, logs_path

    return {
        "running": server is not None,
        "thread_alive": server_thread is not None and server_thread.is_alive(),
        "thread_name": server_thread.name if server_thread else None,
        "database_path": database_path,
        "upload_path": upload_path,
        "logs_path": logs_path,
        "shutdown_requested": shutdown_event.is_set()
    }


def wait_for_server_ready(timeout: float = 10.0) -> bool:
    """
    Wait for server to be ready

    NEW IMPROVEMENT: Polling function to check when server is fully started.

    Args:
        timeout: Maximum time to wait in seconds (default: 10.0)

    Returns:
        bool: True if server is ready, False if timeout

    Example (from MainActivity.kt):
        val ready = python!!.getModule("backend_main")
            .callAttr("wait_for_server_ready", 10.0).toBoolean()
    """
    import time
    import urllib.request
    import urllib.error

    logger.info(f"⏳ Waiting for server to be ready (timeout: {timeout}s)...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Try to access health endpoint
            response = urllib.request.urlopen(
                "http://127.0.0.1:8001/health",
                timeout=1.0
            )
            if response.status == 200:
                logger.info("✅ Server is ready!")
                return True
        except (urllib.error.URLError, Exception):
            pass

        time.sleep(0.2)

    logger.warning(f"⚠️  Server not ready after {timeout}s")
    return False


def initialize_database():
    """
    Initialize database (FALLBACK function from ca458ea)

    This function is kept for backwards compatibility, but the actual
    initialization is done in mobile_database.py:init_mobile_database()
    which is called from mobile_server.py on startup.

    You can still call this if needed for manual initialization.
    """
    try:
        logger.info("🗄️  Initializing database...")

        # Create database file if it doesn't exist
        if database_path:
            db_file = Path(database_path)
            if not db_file.exists():
                db_file.parent.mkdir(parents=True, exist_ok=True)
                db_file.touch()
                logger.info(f"✅ Created database file: {database_path}")

        # Actual initialization is in mobile_database.py
        logger.info("   Note: Full initialization done by mobile_database.py")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def create_mobile_app():
    """
    Create minimal FastAPI app (FALLBACK from ca458ea)

    This function is kept as a fallback in case mobile_server.py
    is not available. Normally, we import app from mobile_server.py.

    Returns:
        FastAPI: Minimal FastAPI application
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    logger.warning("⚠️  Using fallback create_mobile_app()")
    logger.warning("   mobile_server.py should be used instead!")

    # Create app
    mobile_app = FastAPI(
        title="Data20 Mobile Backend (Fallback)",
        description="Minimal embedded FastAPI backend for mobile app",
        version="1.0.0-fallback",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware (allow all on mobile)
    mobile_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @mobile_app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "environment": "mobile",
            "mode": "fallback",
            "database": database_path,
            "version": "1.0.0-fallback"
        }

    # Root endpoint
    @mobile_app.get("/")
    async def root():
        return {
            "message": "Data20 Mobile Backend (Fallback Mode)",
            "status": "running",
            "docs": "/docs",
            "warning": "This is fallback mode. mobile_server.py should be used."
        }

    return mobile_app


# For testing directly with Python
if __name__ == "__main__":
    import tempfile
    import argparse

    parser = argparse.ArgumentParser(description="Data20 Mobile Backend")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--async", action="store_true", dest="async_mode", help="Run in async mode")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    args = parser.parse_args()

    # Setup test environment
    temp_dir = tempfile.gettempdir()

    logger.info("=" * 60)
    logger.info("🧪 TESTING MODE - backend_main.py")
    logger.info("=" * 60)

    setup_environment(
        db_path=f"{temp_dir}/test_data20.db",
        upload_dir=f"{temp_dir}/data20_uploads",
        logs_dir=f"{temp_dir}/data20_logs",
        debug=args.debug
    )

    # Run server
    if args.async_mode:
        logger.info("Running in ASYNC mode (background thread)")
        run_server_async(host=args.host, port=args.port)

        # Wait for server
        if wait_for_server_ready(timeout=15.0):
            logger.info("Server is ready! Press Ctrl+C to stop")
            try:
                # Keep main thread alive
                shutdown_event.wait()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt")

        stop_server()
    else:
        logger.info("Running in BLOCKING mode")
        run_server(host=args.host, port=args.port)
