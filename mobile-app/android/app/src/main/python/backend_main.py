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
        logger.info(f"🚀 Starting MINIMAL test backend on {host}:{port}")

        # Create minimal FastAPI app instead of importing mobile_server
        logger.info("📦 Creating minimal FastAPI test app...")

        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import JSONResponse
            from fastapi.middleware.cors import CORSMiddleware

            test_app = FastAPI(title="Data20 Test Backend")

            # Add CORS middleware
            test_app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

            @test_app.get("/health")
            async def health():
                logger.info("Health check")
                return {"status": "ok", "message": "Test backend is running"}

            @test_app.get("/")
            async def root():
                logger.info("Root endpoint")
                return {"message": "Data20 Test Backend - Minimal Version"}

            # Auth endpoints - accept RAW JSON (no Pydantic validation)
            @test_app.post("/auth/login")
            async def login(request: Request):
                try:
                    body = await request.json()
                    username = body.get("username", "unknown")
                    logger.info(f"✅ Login request: username={username}")
                    return JSONResponse({
                        "access_token": "test_token_12345",
                        "refresh_token": "test_refresh_67890",
                        "token_type": "bearer"
                    })
                except Exception as e:
                    logger.error(f"❌ Login error: {e}")
                    return JSONResponse({"error": str(e)}, status_code=500)

            @test_app.post("/auth/register")
            async def register(request: Request):
                try:
                    body = await request.json()
                    username = body.get("username", "unknown")
                    logger.info(f"✅ Register request: username={username}")
                    return JSONResponse({
                        "access_token": "test_token_12345",
                        "refresh_token": "test_refresh_67890",
                        "token_type": "bearer"
                    })
                except Exception as e:
                    logger.error(f"❌ Register error: {e}")
                    return JSONResponse({"error": str(e)}, status_code=500)

            @test_app.get("/auth/me")
            async def get_current_user(request: Request):
                try:
                    # Log authorization header
                    auth = request.headers.get("authorization", "none")
                    logger.info(f"✅ Get user request: auth={auth[:20]}..." if len(auth) > 20 else f"auth={auth}")
                    return JSONResponse({
                        "id": "test-user-1",
                        "username": "admin",
                        "email": "admin@test.com",
                        "full_name": "Test Admin",
                        "role": "admin",
                        "is_active": True
                    })
                except Exception as e:
                    logger.error(f"❌ Get user error: {e}")
                    return JSONResponse({"error": str(e)}, status_code=500)

            app = test_app
            logger.info("✅ Minimal test app created with CORS and logging")

        except Exception as e:
            logger.error(f"❌ Failed to create FastAPI app: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"FastAPI creation failed: {e}")

        # Import uvicorn
        try:
            logger.info("📦 Importing uvicorn...")
            import uvicorn
            logger.info("✅ uvicorn imported")
        except ImportError as e:
            logger.error(f"❌ Failed to import uvicorn: {e}")
            raise Exception(f"uvicorn not available: {e}")

        # Configure and run
        try:
            logger.info(f"🚀 Starting uvicorn server on {host}:{port}...")

            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info",
                access_log=False,
            )

            server = uvicorn.Server(config)
            logger.info("✅ Server starting (this will block)...")
            server.run()

            logger.info("Server stopped normally")

        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Server failed: {e}")

    except Exception as e:
        logger.error(f"❌ FATAL: {e}")
        logger.error(f"   Type: {type(e).__name__}")
        import traceback
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
