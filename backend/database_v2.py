"""
Database Configuration with SQLite/PostgreSQL Support
Phase 6.1: Multi-database adapter pattern

Supports both SQLite (serverless) and PostgreSQL (production) databases.
Database type is automatically detected from DATABASE_URL environment variable.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from typing import Generator

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data20.db"  # Default to SQLite
)

# Detect database type
IS_SQLITE = DATABASE_URL.startswith("sqlite")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# Base for models
Base = declarative_base()


def get_engine_config():
    """Get engine configuration based on database type"""
    if IS_SQLITE:
        # SQLite configuration (serverless, file-based)
        return {
            "url": DATABASE_URL,
            "connect_args": {"check_same_thread": False},  # Allow multiple threads
            "poolclass": StaticPool,  # Keep connection alive
            "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        }
    elif IS_POSTGRES:
        # PostgreSQL configuration (production, server-based)
        return {
            "url": DATABASE_URL,
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_pre_ping": True,  # Verify connections before using
            "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        }
    else:
        raise ValueError(f"Unsupported database URL: {DATABASE_URL}")


# Create engine with appropriate configuration
engine = create_engine(**get_engine_config())


# Enable WAL mode for SQLite (better concurrency)
if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
        cursor.execute("PRAGMA foreign_keys=ON")  # Enable foreign keys
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.close()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    Database session dependency for FastAPI

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """
    Initialize database (create tables)

    Call this on application startup
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized ({get_database_type()})")


def check_database_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        return False


def get_database_type() -> str:
    """Get current database type"""
    if IS_SQLITE:
        return "SQLite"
    elif IS_POSTGRES:
        return "PostgreSQL"
    else:
        return "Unknown"


def get_database_info() -> dict:
    """Get database information"""
    info = {
        "type": get_database_type(),
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,  # Hide password
        "is_sqlite": IS_SQLITE,
        "is_postgres": IS_POSTGRES,
        "file_path": DATABASE_URL.replace("sqlite:///", "") if IS_SQLITE else None,
    }

    if IS_POSTGRES:
        info["pool_size"] = engine.pool.size()
        info["checked_out"] = engine.pool.checkedout()

    return info


# Export commonly used items
__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_database",
    "check_database_connection",
    "get_database_type",
    "get_database_info",
    "IS_SQLITE",
    "IS_POSTGRES",
]
