"""
Application Configuration
Phase 6.2: Standalone/Offline Mode Support

Supports three deployment modes:
1. STANDALONE - Full offline mode (SQLite, no Redis, no Celery)
2. DEVELOPMENT - Local development with all services
3. PRODUCTION - Production deployment with PostgreSQL, Redis, Celery
"""

import os
from enum import Enum
from typing import Optional


class DeploymentMode(str, Enum):
    """Deployment mode"""
    STANDALONE = "standalone"  # Offline, no external services
    DEVELOPMENT = "development"  # Local dev with all services
    PRODUCTION = "production"  # Production with all services


class AppConfig:
    """Application configuration"""

    # Deployment mode
    MODE: DeploymentMode = DeploymentMode(
        os.getenv("DEPLOYMENT_MODE", "standalone").lower()
    )

    # ========================
    # Database Configuration
    # ========================

    # Auto-select database based on mode
    if MODE == DeploymentMode.STANDALONE:
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data20.db")
    else:
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://data20:data20@localhost:5432/data20_kb"
        )

    # Database pool settings (PostgreSQL only)
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

    # ========================
    # Redis Configuration
    # ========================

    # Redis enabled only in dev/production
    REDIS_ENABLED = MODE != DeploymentMode.STANDALONE and os.getenv("REDIS_ENABLED", "true").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

    # ========================
    # Celery Configuration
    # ========================

    # Celery enabled only in dev/production
    CELERY_ENABLED = MODE != DeploymentMode.STANDALONE and os.getenv("CELERY_ENABLED", "true").lower() == "true"
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # ========================
    # Authentication Configuration
    # ========================

    SECRET_KEY = os.getenv("SECRET_KEY", "standalone-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ========================
    # Logging Configuration
    # ========================

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "console")  # "console" or "json"
    LOG_DIR = os.getenv("LOG_DIR", None)  # None = stdout only

    # ========================
    # Metrics Configuration
    # ========================

    METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

    # ========================
    # Server Configuration
    # ========================

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))
    WORKERS = int(os.getenv("WORKERS", "1"))
    RELOAD = os.getenv("RELOAD", "false").lower() == "true"

    # ========================
    # CORS Configuration
    # ========================

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # ========================
    # Storage Configuration
    # ========================

    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(100 * 1024 * 1024)))  # 100MB

    @classmethod
    def is_standalone(cls) -> bool:
        """Check if running in standalone mode"""
        return cls.MODE == DeploymentMode.STANDALONE

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.MODE == DeploymentMode.DEVELOPMENT

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.MODE == DeploymentMode.PRODUCTION

    @classmethod
    def get_info(cls) -> dict:
        """Get configuration info"""
        return {
            "mode": cls.MODE.value,
            "database": "SQLite" if "sqlite" in cls.DATABASE_URL else "PostgreSQL",
            "redis_enabled": cls.REDIS_ENABLED,
            "celery_enabled": cls.CELERY_ENABLED,
            "metrics_enabled": cls.METRICS_ENABLED,
            "standalone": cls.is_standalone(),
        }

    @classmethod
    def validate(cls):
        """Validate configuration"""
        issues = []

        # Check SECRET_KEY in production
        if cls.is_production() and cls.SECRET_KEY == "standalone-secret-key-change-in-production":
            issues.append("⚠️  WARNING: Using default SECRET_KEY in production!")

        # Check database in standalone mode
        if cls.is_standalone() and "postgresql" in cls.DATABASE_URL.lower():
            issues.append("⚠️  WARNING: Using PostgreSQL in standalone mode (should use SQLite)")

        # Check Redis in standalone mode
        if cls.is_standalone() and cls.REDIS_ENABLED:
            issues.append("ℹ️  INFO: Redis disabled in standalone mode")
            cls.REDIS_ENABLED = False

        # Check Celery in standalone mode
        if cls.is_standalone() and cls.CELERY_ENABLED:
            issues.append("ℹ️  INFO: Celery disabled in standalone mode")
            cls.CELERY_ENABLED = False

        return issues


# Singleton instance
config = AppConfig()

# Validate on import
validation_issues = config.validate()
if validation_issues:
    for issue in validation_issues:
        print(issue)
