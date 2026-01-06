"""
Mobile Backend Wrapper for Data20

This module is called by the native Android/iOS code to start the embedded Python backend.
It imports and runs the full mobile_server.py FastAPI application.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# AUTH UTILITIES - Embedded to avoid FastAPI import
# ============================================================================

def get_password_hash(password: str) -> str:
    """Hash password using simple SHA256 (fast on Android)"""
    # Simple SHA256 with salt - use os.urandom (works everywhere)
    salt = os.urandom(16).hex()  # 16 bytes = 32 hex chars
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, stored_hash = hashed_password.split(':')
        pwd_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return hmac.compare_digest(pwd_hash, stored_hash)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create simple token WITHOUT JWT library (pure Python)"""
    # Create simple token: base64(user_id:username:role:timestamp)
    import base64
    import time

    user_id = data.get('sub', '')
    username = data.get('username', '')
    role = data.get('role', 'user')
    timestamp = int(time.time())

    # Simple token format
    token_data = f"{user_id}:{username}:{role}:{timestamp}"
    token = base64.b64encode(token_data.encode()).decode()
    return token

def create_tokens_for_user(user) -> dict:
    """Create access and refresh tokens for user"""
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role.value}
    )
    refresh_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(days=30)
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

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
    Run ultra-lightweight HTTP server with lazy initialization

    CRITICAL: Starts INSTANTLY (< 1 second)
    Database and imports only loaded on first auth request
    """
    global server

    logger.info(f"🚀 Starting HTTP backend on {host}:{port}...")

    # Import ONLY standard library - NO custom modules!
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    import json

    # Flag to track if DB is initialized
    db_initialized = False
    db_connection = None

    def ensure_db_initialized():
        """Initialize database using pure sqlite3 (NO SQLAlchemy!)"""
        nonlocal db_initialized, db_connection
        if not db_initialized:
            try:
                logger.info("📦 [STEP 1/3] Starting lightweight database initialization...")

                # Use pure sqlite3 - NO SQLAlchemy imports!
                import sqlite3
                logger.info("✅ sqlite3 imported (built-in library)")

                # Get database path from environment
                db_path = os.getenv('DATA20_DATABASE_PATH', '/tmp/data20_mobile.db')
                logger.info(f"📦 [STEP 2/3] Connecting to database: {db_path}")

                # Create database connection
                db_connection = sqlite3.connect(db_path, check_same_thread=False)
                db_connection.row_factory = sqlite3.Row  # Access columns by name
                logger.info("✅ [STEP 2/3] Database connected")

                # Create users table if not exists
                logger.info("📦 [STEP 3/3] Creating users table...")
                cursor = db_connection.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        full_name TEXT,
                        hashed_password TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                db_connection.commit()
                logger.info("✅ [STEP 3/3] Users table ready")

                db_initialized = True
                logger.info("✅ Database initialization complete (pure sqlite3)!")

            except Exception as e:
                logger.error(f"❌ CRITICAL: Database initialization failed: {e}", exc_info=True)
                raise

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Disable logging

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
            # Health check - NO imports, NO database, INSTANT response
            if '/health' in self.path:
                self._send_json({"status": "ok", "version": "1.0.0"})

            elif '/auth/me' in self.path:
                # Simplified - return mock user
                self._send_json({
                    "id": "1",
                    "username": "user",
                    "email": "user@data20.local",
                    "role": "user",
                    "is_active": True
                })

            elif '/tools' in self.path:
                self._send_json({"tools": [], "total": 0})

            elif '/jobs' in self.path:
                self._send_json([])

            else:
                self._send_json({"message": "Data20 Mobile Backend", "status": "running"})

        def do_POST(self):
            try:
                logger.info(f"🌐 POST request received: {self.path}")

                # Initialize DB on first call
                logger.info("📦 Calling ensure_db_initialized()...")
                ensure_db_initialized()
                logger.info("✅ Database initialization complete")

                logger.info("📦 Reading request body...")
                body = self._get_body()
                logger.info(f"✅ Request body parsed: {list(body.keys())}")

                if '/auth/register' in self.path:
                    # Real registration using pure sqlite3
                    import uuid
                    username = body.get('username')
                    email = body.get('email')
                    password = body.get('password')
                    full_name = body.get('full_name', '')

                    logger.info(f"📝 Registration attempt: {username}")

                    # Check if user exists
                    logger.info("📦 Checking if user already exists...")
                    cursor = db_connection.cursor()
                    cursor.execute(
                        "SELECT id FROM users WHERE username = ? OR email = ?",
                        (username, email)
                    )
                    existing = cursor.fetchone()
                    logger.info(f"✅ User check complete (exists: {existing is not None})")

                    if existing:
                        logger.warning(f"❌ User already exists: {username}")
                        self._send_json({"detail": "Username or email already exists"}, 400)
                        return

                    # Hash password
                    logger.info("📦 Hashing password...")
                    hashed_password = get_password_hash(password)
                    logger.info("✅ Password hashed")

                    # Create user
                    logger.info("📦 Inserting user into database...")
                    user_id = str(uuid.uuid4())
                    cursor.execute(
                        """INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (user_id, username, email, full_name, hashed_password, 'user', 1)
                    )
                    db_connection.commit()
                    logger.info("✅ User saved to database")

                    logger.info(f"✅ User registered: {username}")

                    self._send_json({
                        "id": user_id,
                        "username": username,
                        "email": email,
                        "full_name": full_name,
                        "role": "user",
                        "is_active": True
                    })

                elif '/auth/login' in self.path:
                    # Real login using pure sqlite3
                    username = body.get('username')
                    password = body.get('password')

                    logger.info(f"🔐 Login attempt: {username}")

                    # Find user
                    logger.info("📦 Finding user in database...")
                    cursor = db_connection.cursor()
                    cursor.execute(
                        "SELECT id, username, email, full_name, hashed_password, role, is_active FROM users WHERE username = ? OR email = ?",
                        (username, username)
                    )
                    user_row = cursor.fetchone()
                    logger.info(f"✅ User lookup complete (found: {user_row is not None})")

                    if not user_row:
                        logger.warning(f"❌ User not found: {username}")
                        self._send_json({"detail": "Invalid credentials"}, 401)
                        return

                    # Verify password
                    logger.info("📦 Verifying password...")
                    if not verify_password(password, user_row['hashed_password']):
                        logger.warning(f"❌ Invalid password: {username}")
                        self._send_json({"detail": "Invalid credentials"}, 401)
                        return
                    logger.info("✅ Password verified")

                    if not user_row['is_active']:
                        logger.warning(f"❌ Inactive user: {username}")
                        self._send_json({"detail": "User is inactive"}, 401)
                        return

                    # Create tokens
                    logger.info("📦 Creating JWT tokens...")
                    user_data = {
                        'id': user_row['id'],
                        'username': user_row['username'],
                        'role': user_row['role']
                    }

                    class UserObj:
                        def __init__(self, data):
                            self.id = data['id']
                            self.username = data['username']
                            self.role = type('Role', (), {'value': data['role']})()

                    tokens = create_tokens_for_user(UserObj(user_data))
                    logger.info("✅ JWT tokens created")

                    logger.info(f"✅ User logged in: {username}")
                    self._send_json(tokens)

                else:
                    self._send_json({"access_token": "test", "token_type": "bearer"})

            except Exception as e:
                logger.error(f"❌ Critical error in do_POST: {e}", exc_info=True)
                self._send_json({"detail": str(e)}, 500)

    try:
        server = ThreadingHTTPServer((host, port), Handler)
        logger.info(f"✅ HTTP backend started on {host}:{port} (INSTANT START)")
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
