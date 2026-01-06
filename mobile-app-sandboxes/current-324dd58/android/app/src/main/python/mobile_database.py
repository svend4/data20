"""
Mobile Database - SQLite configuration for mobile devices

Simplified version without PostgreSQL dependency
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path

from mobile_models import Base

# Get database path from environment (set by native code)
DATABASE_PATH = os.getenv('DATA20_DATABASE_PATH', '/tmp/data20_mobile.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_mobile_database():
    """Initialize mobile database"""
    # Ensure database directory exists
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print(f"✅ Database initialized: {DATABASE_PATH}")

    # Create default admin user if not exists
    from mobile_models import User, UserRole
    from mobile_auth import get_password_hash

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()

        if not admin:
            admin = User(
                username="admin",
                email="admin@data20.local",
                full_name="Administrator",
                hashed_password=get_password_hash("admin"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ Default admin user created (username: admin, password: admin)")
    finally:
        db.close()

def check_database_connection():
    """Check if database is accessible"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
