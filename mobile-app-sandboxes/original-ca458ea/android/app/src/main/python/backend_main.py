"""
Mobile Backend Wrapper for Data20

This is a lightweight wrapper around the main FastAPI backend,
optimized for mobile devices (Android/iOS).

Key differences from desktop backend:
- Uses SQLite (no PostgreSQL)
- Runs on localhost only (127.0.0.1)
- No Celery workers (all tasks run synchronously)
- No Redis (no caching)
- Reduced memory footprint
- Mobile-specific file paths
"""

import os
import sys
import logging
import asyncio
import threading
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
app = None
server = None
server_thread = None
database_path = None
upload_path = None
logs_path = None


def setup_environment(db_path: str, upload_dir: str, logs_dir: str):
    """
    Setup environment for mobile backend

    Args:
        db_path: Path to SQLite database file
        upload_dir: Directory for uploaded files
        logs_dir: Directory for log files
    """
    global database_path, upload_path, logs_path

    database_path = db_path
    upload_path = upload_dir
    logs_path = logs_dir

    # Create directories if they don't exist
    for path in [upload_dir, logs_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)

    # Set environment variables for FastAPI app
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['UPLOAD_DIR'] = upload_dir
    os.environ['LOGS_DIR'] = logs_dir

    # Mobile-specific settings
    os.environ['ENVIRONMENT'] = 'mobile'
    os.environ['DEBUG'] = 'false'
    os.environ['CORS_ORIGINS'] = '*'  # Allow all origins on mobile

    # Disable features not needed on mobile
    os.environ['ENABLE_CELERY'] = 'false'
    os.environ['ENABLE_REDIS'] = 'false'
    os.environ['ENABLE_METRICS'] = 'false'

    logger.info(f"Environment configured:")
    logger.info(f"  Database: {db_path}")
    logger.info(f"  Uploads: {upload_dir}")
    logger.info(f"  Logs: {logs_dir}")


def create_mobile_app():
    """
    Create FastAPI application optimized for mobile

    Returns:
        FastAPI application instance
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Create app
    mobile_app = FastAPI(
        title="Data20 Mobile Backend",
        description="Embedded FastAPI backend for mobile app",
        version="1.0.0",
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
        """Health check endpoint"""
        return {
            "status": "ok",
            "environment": "mobile",
            "database": database_path,
            "version": "1.0.0"
        }

    # Root endpoint
    @mobile_app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Data20 Mobile Backend",
            "status": "running",
            "docs": "/docs"
        }

    # Import and include routers from main backend
    try:
        # Try to import main backend routers
        # In production, you would copy the entire backend/ directory
        # to src/main/python/ and import from there

        # For now, create minimal endpoints
        logger.info("Setting up minimal endpoints (TODO: import full backend)")

        # TODO: Import actual routers when backend is available
        # from backend.api.routes import auth, tools, jobs
        # mobile_app.include_router(auth.router, prefix="/auth", tags=["auth"])
        # mobile_app.include_router(tools.router, prefix="/tools", tags=["tools"])
        # mobile_app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

    except ImportError as e:
        logger.warning(f"Could not import backend modules: {e}")
        logger.info("Running with minimal endpoints only")

    return mobile_app


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """
    Run FastAPI server (blocking)

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8001)
    """
    global app, server

    try:
        logger.info(f"Starting mobile backend on {host}:{port}")

        # Create app if not exists
        if app is None:
            app = create_mobile_app()

        # Initialize database
        initialize_database()

        # Run with uvicorn
        import uvicorn

        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            access_log=False,  # Disable access log on mobile to save resources
            loop="asyncio"
        )

        server = uvicorn.Server(config)

        # Run server (blocking)
        logger.info("Backend server started successfully")
        server.run()

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


def run_server_async(host: str = "127.0.0.1", port: int = 8001):
    """
    Run server in background thread (non-blocking)

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    global server_thread

    def run():
        run_server(host, port)

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()

    logger.info(f"Backend started in background thread")


def stop_server():
    """
    Stop the running server
    """
    global server, server_thread

    try:
        if server is not None:
            logger.info("Stopping server...")
            server.should_exit = True
            server = None

        if server_thread is not None:
            server_thread = None

        logger.info("Server stopped")

    except Exception as e:
        logger.error(f"Error stopping server: {e}")


def initialize_database():
    """
    Initialize SQLite database
    """
    try:
        logger.info("Initializing database...")

        # Create database file if it doesn't exist
        db_file = Path(database_path)
        if not db_file.exists():
            db_file.parent.mkdir(parents=True, exist_ok=True)
            db_file.touch()
            logger.info(f"Created new database: {database_path}")

        # TODO: Run migrations when backend is integrated
        # from alembic.config import Config
        # from alembic import command
        # alembic_cfg = Config("alembic.ini")
        # command.upgrade(alembic_cfg, "head")

        logger.info("Database initialized")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


# For testing/debugging
if __name__ == "__main__":
    # Setup test environment
    import tempfile
    temp_dir = tempfile.gettempdir()

    setup_environment(
        db_path=f"{temp_dir}/test_data20.db",
        upload_dir=f"{temp_dir}/uploads",
        logs_dir=f"{temp_dir}/logs"
    )

    # Run server
    run_server(host="127.0.0.1", port=8001)
