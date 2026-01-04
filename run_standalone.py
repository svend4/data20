#!/usr/bin/env python3
"""
Standalone Launcher for Data20 Knowledge Base
Phase 6.2: Offline/Standalone Mode

Runs the application in standalone mode:
- SQLite database (no PostgreSQL server needed)
- No Redis (in-memory caching fallback)
- No Celery (local task execution)
- Complete offline operation

Usage:
    python run_standalone.py

    # Custom port
    python run_standalone.py --port 8080

    # Custom database location
    python run_standalone.py --db ./my_database.db

    # Enable debug mode
    python run_standalone.py --debug
"""

import os
import sys
import argparse
from pathlib import Path

# Set standalone mode BEFORE importing anything else
os.environ["DEPLOYMENT_MODE"] = "standalone"


def setup_standalone_environment(args):
    """Setup environment for standalone mode"""

    # Database configuration
    db_path = Path(args.db).resolve()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Disable external services
    os.environ["REDIS_ENABLED"] = "false"
    os.environ["CELERY_ENABLED"] = "false"

    # Server configuration
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)

    # Logging
    if args.debug:
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["SQL_ECHO"] = "true"
    else:
        os.environ["LOG_LEVEL"] = "INFO"

    # Storage directories
    os.environ["UPLOAD_DIR"] = str(Path("./uploads").resolve())
    os.environ["OUTPUT_DIR"] = str(Path("./output").resolve())

    # Create directories
    Path(os.environ["UPLOAD_DIR"]).mkdir(exist_ok=True)
    Path(os.environ["OUTPUT_DIR"]).mkdir(exist_ok=True)

    print("=" * 60)
    print("🚀 Data20 Knowledge Base - Standalone Mode")
    print("=" * 60)
    print(f"📊 Database: {db_path}")
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"📁 Uploads: {os.environ['UPLOAD_DIR']}")
    print(f"📁 Output: {os.environ['OUTPUT_DIR']}")
    print(f"🔧 Debug: {'Yes' if args.debug else 'No'}")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ SQLite database (no server needed)")
    print("  ✅ Local execution (no Celery)")
    print("  ✅ In-memory cache (no Redis)")
    print("  ✅ JWT authentication")
    print("  ✅ User management")
    print("  ✅ Job ownership")
    print("  ✅ 57+ data analysis tools")
    print()
    print("Offline Mode: All features work without internet connection")
    print("=" * 60)
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Data20 Knowledge Base - Standalone Mode"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to listen on (default: 8001)"
    )
    parser.add_argument(
        "--db",
        default="./data20.db",
        help="SQLite database file path (default: ./data20.db)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logging)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes"
    )

    args = parser.parse_args()

    # Setup environment
    setup_standalone_environment(args)

    # Import and run server
    try:
        import uvicorn

        # Import after environment is set
        from backend.server import app

        # Check if database exists
        db_path = Path(args.db)
        is_new_db = not db_path.exists()

        if is_new_db:
            print(f"📝 Creating new database: {db_path}")
            print("   First user will become admin automatically")
            print()

        # Run server
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="debug" if args.debug else "info"
        )

    except ImportError as e:
        print(f"❌ Error: Missing dependency: {e}")
        print()
        print("Please install standalone requirements:")
        print("  pip install -r requirements-standalone.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
