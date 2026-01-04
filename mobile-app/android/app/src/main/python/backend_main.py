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
    Run simple HTTP server (blocking)

    Called by native code to start the server.
    This function blocks until the server is stopped.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8001)
    """
    global app, server

    try:
        logger.info(f"🚀 Starting ULTRA-SIMPLE HTTP server on {host}:{port}")
        logger.info("📦 Using Python http.server (no FastAPI, no uvicorn)")

        # Use standard library http.server instead of FastAPI
        from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
        import json

        class SimpleHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                """Override to use logger instead of stderr"""
                logger.info(f"HTTP: {format % args}")

            def _send_json(self, data, status=200):
                """Helper to send JSON response"""
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))

            def do_OPTIONS(self):
                """Handle CORS preflight"""
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                self.end_headers()

            def do_GET(self):
                """Handle GET requests"""
                logger.info(f"GET {self.path}")

                if self.path == '/health':
                    self._send_json({"status": "ok", "message": "Ultra-simple backend running"})
                elif self.path == '/':
                    self._send_json({"message": "Data20 Ultra-Simple Backend"})
                elif self.path == '/auth/me':
                    self._send_json({
                        "id": "test-user-1",
                        "username": "admin",
                        "email": "admin@test.com",
                        "full_name": "Test Admin",
                        "role": "admin",
                        "is_active": True
                    })
                else:
                    self._send_json({"error": "Not found"}, 404)

            def do_POST(self):
                """Handle POST requests - SIMPLEST POSSIBLE"""
                logger.info(f"POST {self.path} - INSTANT RESPONSE")

                # DON'T read body - just send response immediately
                # This avoids any threading/blocking issues

                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                    self.end_headers()

                    response = '{"access_token":"test_token_12345","refresh_token":"test_refresh_67890","token_type":"bearer"}'
                    self.wfile.write(response.encode('utf-8'))

                    logger.info(f"POST {self.path} - SUCCESS")

                except Exception as e:
                    logger.error(f"POST {self.path} - ERROR: {e}")
                    import traceback
                    traceback.print_exc()

        # Create and start server (ThreadingHTTPServer for concurrent requests)
        logger.info(f"🔧 Creating ThreadingHTTPServer on {host}:{port}...")
        server = ThreadingHTTPServer((host, port), SimpleHandler)
        logger.info(f"✅ Threaded server created, can handle concurrent requests...")
        logger.info(f"   This allows POST /auth/login and GET /health at the same time!")

        # This blocks until server is stopped
        server.serve_forever()

        logger.info("Server stopped")

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
