"""
Database connection and session management
Phase 5.1.3: PostgreSQL connection pool
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import os


# ========================
# Database Configuration
# ========================

# Read from environment or use defaults
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://data20:data20@localhost:5432/data20_kb"
)

# SQLite fallback for development (if PostgreSQL not available)
SQLITE_URL = "sqlite:///./data20_kb.db"


# ========================
# Engine Configuration
# ========================

def get_engine(url: str = None, echo: bool = False):
    """
    Create SQLAlchemy engine with connection pooling

    Args:
        url: Database URL (defaults to DATABASE_URL env var)
        echo: Echo SQL queries (for debugging)

    Returns:
        SQLAlchemy Engine
    """
    url = url or DATABASE_URL

    # PostgreSQL configuration
    if url.startswith("postgresql"):
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=5,          # Number of connections to keep open
            max_overflow=10,      # Max additional connections
            pool_timeout=30,      # Timeout for getting connection
            pool_recycle=3600,    # Recycle connections after 1 hour
            pool_pre_ping=True,   # Verify connections before using
            echo=echo
        )

    # SQLite configuration (development)
    elif url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},  # Allow multi-threading
            echo=echo
        )

    else:
        raise ValueError(f"Unsupported database URL: {url}")

    return engine


# Create global engine
engine = get_engine()


# ========================
# Session Factory
# ========================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ========================
# Dependency Injection
# ========================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ========================
# Database Initialization
# ========================

def init_database():
    """Initialize database schema"""
    from models import Base

    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database schema created")


def check_database_connection() -> bool:
    """
    Check if database is accessible

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database connection info

    Returns:
        Dict with database info
    """
    return {
        "url": str(engine.url).split("@")[-1],  # Hide password
        "driver": engine.driver,
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
        "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None
    }


# ========================
# Migration Helpers
# ========================

def reset_database():
    """
    DROP and recreate all tables
    ⚠️  WARNING: This will delete all data!
    """
    from models import Base

    print("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating fresh schema...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database reset complete")


# ========================
# Startup/Shutdown
# ========================

async def startup_database():
    """Run on application startup"""
    print("🔌 Connecting to database...")

    if check_database_connection():
        print("✅ Database connected")
        print(f"📊 Database info: {get_database_info()}")
    else:
        print("❌ Database connection failed - using fallback")


async def shutdown_database():
    """Run on application shutdown"""
    print("🔌 Closing database connections...")
    engine.dispose()
    print("✅ Database connections closed")


# ========================
# CLI for testing
# ========================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            init_database()

        elif command == "check":
            if check_database_connection():
                print("✅ Database connection OK")
                print(f"Info: {get_database_info()}")
            else:
                print("❌ Database connection FAILED")
                sys.exit(1)

        elif command == "reset":
            confirm = input("⚠️  This will DELETE ALL DATA. Type 'yes' to confirm: ")
            if confirm.lower() == "yes":
                reset_database()
            else:
                print("Cancelled")

        else:
            print(f"Unknown command: {command}")
            print("Usage: python database.py [init|check|reset]")

    else:
        print("Database module")
        print("Commands:")
        print("  init   - Initialize database schema")
        print("  check  - Check database connection")
        print("  reset  - Reset database (⚠️  deletes all data)")
