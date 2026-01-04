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

# JWT settings
SECRET_KEY = "mobile-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def _hash_password_pbkdf2(password: str, salt: bytes = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256"""
    if salt is None:
        salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + pwd_hash.hex()

def _verify_password_pbkdf2(plain_password: str, stored_hash: str) -> bool:
    """Verify password against PBKDF2 hash"""
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(pwd_hash, expected_hash)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2"""
    try:
        logger.info("🔐 Hashing password with PBKDF2...")
        result = _hash_password_pbkdf2(password)
        logger.info("✅ Password hash created successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Password hashing failed: {e}", exc_info=True)
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return _verify_password_pbkdf2(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    try:
        logger.info("📦 Importing jwt library...")
        import jwt  # Import only when needed
        logger.info("✅ jwt library imported")

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})

        logger.info("📦 Encoding JWT token...")
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info("✅ JWT token encoded")
        return token
    except Exception as e:
        logger.error(f"❌ JWT token encoding failed: {e}", exc_info=True)
        raise

def create_tokens_for_user(user) -> dict:
    """Create access and refresh tokens for user"""
    try:
        logger.info("🔑 Creating access token...")
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role.value}
        )
        logger.info("✅ Access token created")

        logger.info("🔑 Creating refresh token...")
        refresh_token = create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=timedelta(days=30)
        )
        logger.info("✅ Refresh token created")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"❌ Token creation failed: {e}", exc_info=True)
        raise

def authenticate_user_simple(db, User_model, username: str, password: str):
    """Authenticate user WITHOUT FastAPI dependencies"""
    # Try username or email
    user = db.query(User_model).filter(
        (User_model.username == username) | (User_model.email == username)
    ).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user

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
    _SessionLocal = None
    _User = None
    _UserRole = None

    def ensure_db_initialized():
        """Initialize database only when first needed"""
        nonlocal db_initialized, _SessionLocal, _User, _UserRole
        if not db_initialized:
            try:
                logger.info("📦 [STEP 1/5] Starting database initialization...")

                # Step 1: Import mobile_database
                logger.info("📦 [STEP 2/5] Importing mobile_database module...")
                from mobile_database import init_mobile_database, SessionLocal
                logger.info("✅ [STEP 2/5] mobile_database imported successfully")

                # Step 2: Import mobile_models
                logger.info("📦 [STEP 3/5] Importing mobile_models module...")
                from mobile_models import User, UserRole
                logger.info("✅ [STEP 3/5] mobile_models imported successfully")

                # Step 3: Initialize database
                logger.info("📦 [STEP 4/5] Calling init_mobile_database()...")
                init_mobile_database()
                logger.info("✅ [STEP 4/5] Database initialized successfully")

                # Step 4: Cache the imports
                logger.info("📦 [STEP 5/5] Caching imports...")
                _SessionLocal = SessionLocal
                _User = User
                _UserRole = UserRole

                db_initialized = True
                logger.info("✅ [STEP 5/5] All initialization complete!")

            except Exception as e:
                logger.error(f"❌ CRITICAL: Database initialization failed at step: {e}", exc_info=True)
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

                # Initialize DB and cache imports on first call
                logger.info("📦 Calling ensure_db_initialized()...")
                ensure_db_initialized()
                logger.info("✅ Database initialization complete")

                # Use cached imports
                logger.info("📦 Creating database session...")
                db = _SessionLocal()
                logger.info("✅ Database session created")

                try:
                    logger.info("📦 Reading request body...")
                    body = self._get_body()
                    logger.info(f"✅ Request body parsed: {list(body.keys())}")

                    if '/auth/register' in self.path:
                        # Real registration
                        username = body.get('username')
                        email = body.get('email')
                        password = body.get('password')
                        full_name = body.get('full_name')

                        logger.info(f"📝 Registration attempt: {username}")

                        # Check if user exists
                        logger.info("📦 Checking if user already exists...")
                        existing = db.query(_User).filter(
                            (_User.username == username) | (_User.email == email)
                        ).first()
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
                        logger.info("📦 Creating user object...")
                        user = _User(
                            username=username,
                            email=email,
                            full_name=full_name,
                            hashed_password=hashed_password,
                            role=_UserRole.USER,
                            is_active=True
                        )
                        logger.info("✅ User object created")

                        logger.info("📦 Saving user to database...")
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        logger.info("✅ User saved to database")

                        logger.info(f"✅ User registered: {username}")

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

                        logger.info(f"🔐 Login attempt: {username}")

                        logger.info("📦 Authenticating user...")
                        user = authenticate_user_simple(db, _User, username, password)
                        logger.info(f"✅ Authentication complete (success: {user is not None})")

                        if not user:
                            logger.warning(f"❌ Invalid credentials: {username}")
                            self._send_json({"detail": "Invalid credentials"}, 401)
                            return

                        if not user.is_active:
                            logger.warning(f"❌ Inactive user: {username}")
                            self._send_json({"detail": "User is inactive"}, 401)
                            return

                        logger.info("📦 Creating JWT tokens...")
                        tokens = create_tokens_for_user(user)
                        logger.info("✅ JWT tokens created")

                        logger.info(f"✅ User logged in: {username}")
                        self._send_json(tokens)

                    else:
                        self._send_json({"access_token": "test", "token_type": "bearer"})

                except Exception as e:
                    logger.error(f"❌ Error in POST handler: {e}", exc_info=True)
                    self._send_json({"detail": str(e)}, 500)
                finally:
                    db.close()

            except Exception as e:
                logger.error(f"❌ Critical error in do_POST: {e}", exc_info=True)
                self._send_json({"detail": "Internal server error"}, 500)

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
