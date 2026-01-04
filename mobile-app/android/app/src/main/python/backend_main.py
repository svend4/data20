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
    Run lightweight HTTP server with real authentication

    Uses ThreadingHTTPServer instead of uvicorn for Android compatibility
    """
    global server

    logger.info(f"🚀 Starting HTTP backend on {host}:{port}...")

    # Import dependencies
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    import json
    from urllib.parse import urlparse, parse_qs

    # Import mobile modules for real functionality
    from mobile_database import get_db, init_mobile_database, SessionLocal
    from mobile_models import User, UserRole
    from mobile_auth import get_password_hash, authenticate_user, create_tokens_for_user

    # Initialize database
    init_mobile_database()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Disable default logging

        def _send_json(self, data, status=200):
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def _get_body(self):
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode())
            return {}

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', '*')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()

        def do_GET(self):
            if '/health' in self.path:
                self._send_json({"status": "ok", "version": "1.0.0"})

            elif '/auth/me' in self.path:
                # Simplified - return default user for now
                self._send_json({
                    "id": "1",
                    "username": "admin",
                    "email": "admin@data20.local",
                    "role": "admin",
                    "is_active": True
                })

            elif '/tools' in self.path:
                self._send_json({"tools": [], "total": 0})

            elif '/jobs' in self.path:
                self._send_json([])

            else:
                self._send_json({"message": "Data20 Mobile Backend", "status": "running"})

        def do_POST(self):
            db = SessionLocal()
            try:
                body = self._get_body()

                if '/auth/register' in self.path:
                    # Real registration
                    username = body.get('username')
                    email = body.get('email')
                    password = body.get('password')
                    full_name = body.get('full_name')

                    # Check if user exists
                    existing = db.query(User).filter(
                        (User.username == username) | (User.email == email)
                    ).first()

                    if existing:
                        self._send_json({"detail": "Username or email already exists"}, 400)
                        return

                    # Create user
                    user = User(
                        username=username,
                        email=email,
                        full_name=full_name,
                        hashed_password=get_password_hash(password),
                        role=UserRole.USER,
                        is_active=True
                    )

                    db.add(user)
                    db.commit()
                    db.refresh(user)

                    self._send_json({
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role.value,
                        "is_active": user.is_active
                    })

                elif '/auth/login' in self.path:
                    # Real login
                    username = body.get('username')
                    password = body.get('password')

                    user = authenticate_user(db, username, password)

                    if not user:
                        self._send_json({"detail": "Invalid credentials"}, 401)
                        return

                    if not user.is_active:
                        self._send_json({"detail": "User is inactive"}, 401)
                        return

                    tokens = create_tokens_for_user(user)
                    self._send_json(tokens)

                else:
                    self._send_json({"access_token": "test", "token_type": "bearer"})

            except Exception as e:
                logger.error(f"Error handling POST: {e}")
                self._send_json({"detail": str(e)}, 500)
            finally:
                db.close()

    try:
        server = ThreadingHTTPServer((host, port), Handler)
        logger.info(f"✅ HTTP backend started on {host}:{port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start HTTP server: {e}")
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
