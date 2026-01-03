#!/usr/bin/env python3
"""
Structured Logging for Data20 Knowledge Base
Phase 5.3.1: Production-ready logging with structlog
"""

import structlog
import logging
import sys
from pathlib import Path
from datetime import datetime
import os


def configure_logging(
    level: str = "INFO",
    format: str = "json",  # "json" or "console"
    log_dir: str = None
):
    """
    Configure structured logging for the application

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" for production, "console" for development)
        log_dir: Directory for log files (None = stdout only)
    """

    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors for both stdlib and structlog
    shared_processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Unicode handling
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    if format == "json":
        # JSON output for production
        processors = shared_processors + [
            # Render as JSON
            structlog.processors.JSONRenderer()
        ]
    else:
        # Pretty console output for development
        processors = shared_processors + [
            # Add color and pretty formatting
            structlog.dev.ConsoleRenderer(colors=True)
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Add file handler if log_dir specified
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_path / "data20.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        logging.root.addHandler(file_handler)


def get_logger(name: str = __name__):
    """
    Get a structured logger

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# ========================
# Request ID Context
# ========================

from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default=None)


def set_request_id(request_id: str):
    """Set request ID for current context"""
    request_id_var.set(request_id)


def get_request_id() -> str:
    """Get request ID from current context"""
    return request_id_var.get()


# ========================
# FastAPI Middleware
# ========================

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request/response logging
    """

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Start timer
        start_time = time.time()

        # Get logger
        logger = get_logger("api")

        # Log request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time

            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                exc_info=True,
            )

            raise


# ========================
# Celery Task Logging
# ========================

def log_task_start(task_id: str, task_name: str, args: tuple, kwargs: dict):
    """Log Celery task start"""
    logger = get_logger("celery")
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task_name,
        args=args,
        kwargs=kwargs,
    )


def log_task_success(task_id: str, task_name: str, result: any, duration: float):
    """Log Celery task success"""
    logger = get_logger("celery")
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task_name,
        duration_seconds=round(duration, 2),
    )


def log_task_failure(task_id: str, task_name: str, error: Exception, duration: float):
    """Log Celery task failure"""
    logger = get_logger("celery")
    logger.error(
        "task_failed",
        task_id=task_id,
        task_name=task_name,
        error=str(error),
        duration_seconds=round(duration, 2),
        exc_info=True,
    )


def log_task_retry(task_id: str, task_name: str, error: Exception, retry_count: int):
    """Log Celery task retry"""
    logger = get_logger("celery")
    logger.warning(
        "task_retry",
        task_id=task_id,
        task_name=task_name,
        error=str(error),
        retry_count=retry_count,
    )


# ========================
# Database Logging
# ========================

def log_db_query(query: str, params: dict, duration: float):
    """Log database query (for slow query logging)"""
    logger = get_logger("database")

    if duration > 1.0:  # Log queries > 1 second
        logger.warning(
            "slow_query",
            query=query[:200],  # Truncate long queries
            params=params,
            duration_seconds=round(duration, 3),
        )
    else:
        logger.debug(
            "query",
            query=query[:100],
            duration_seconds=round(duration, 3),
        )


def log_db_error(query: str, error: Exception):
    """Log database error"""
    logger = get_logger("database")
    logger.error(
        "query_failed",
        query=query[:200],
        error=str(error),
        exc_info=True,
    )


# ========================
# Tool Execution Logging
# ========================

def log_tool_start(job_id: str, tool_name: str, parameters: dict):
    """Log tool execution start"""
    logger = get_logger("tools")
    logger.info(
        "tool_started",
        job_id=job_id,
        tool_name=tool_name,
        parameters=parameters,
    )


def log_tool_success(job_id: str, tool_name: str, duration: float, output_files: list):
    """Log tool execution success"""
    logger = get_logger("tools")
    logger.info(
        "tool_completed",
        job_id=job_id,
        tool_name=tool_name,
        duration_seconds=round(duration, 2),
        output_files=output_files,
        file_count=len(output_files),
    )


def log_tool_failure(job_id: str, tool_name: str, error: str, duration: float):
    """Log tool execution failure"""
    logger = get_logger("tools")
    logger.error(
        "tool_failed",
        job_id=job_id,
        tool_name=tool_name,
        error=error,
        duration_seconds=round(duration, 2) if duration else None,
    )


# ========================
# Security Logging
# ========================

def log_auth_attempt(username: str, success: bool, ip: str, user_agent: str):
    """Log authentication attempt"""
    logger = get_logger("security")

    if success:
        logger.info(
            "auth_success",
            username=username,
            ip=ip,
            user_agent=user_agent,
        )
    else:
        logger.warning(
            "auth_failed",
            username=username,
            ip=ip,
            user_agent=user_agent,
        )


def log_rate_limit(ip: str, endpoint: str, limit: int):
    """Log rate limit violation"""
    logger = get_logger("security")
    logger.warning(
        "rate_limit_exceeded",
        ip=ip,
        endpoint=endpoint,
        limit=limit,
    )


def log_suspicious_activity(description: str, ip: str, details: dict):
    """Log suspicious activity"""
    logger = get_logger("security")
    logger.critical(
        "suspicious_activity",
        description=description,
        ip=ip,
        details=details,
    )


# ========================
# System Logging
# ========================

def log_startup(service: str, version: str, config: dict):
    """Log service startup"""
    logger = get_logger("system")
    logger.info(
        "service_started",
        service=service,
        version=version,
        config=config,
    )


def log_shutdown(service: str):
    """Log service shutdown"""
    logger = get_logger("system")
    logger.info(
        "service_stopped",
        service=service,
    )


def log_health_check(component: str, healthy: bool, details: dict):
    """Log health check result"""
    logger = get_logger("health")

    if healthy:
        logger.debug(
            "health_check_ok",
            component=component,
            details=details,
        )
    else:
        logger.error(
            "health_check_failed",
            component=component,
            details=details,
        )


# ========================
# Usage Examples
# ========================

if __name__ == "__main__":
    # Configure logging (development mode)
    configure_logging(level="DEBUG", format="console")

    # Get logger
    logger = get_logger(__name__)

    # Simple logging
    logger.info("application_started", version="5.3.1")

    # With context
    logger.info(
        "user_action",
        user_id="user-123",
        action="create_job",
        job_id="job-456",
    )

    # With exception
    try:
        1 / 0
    except Exception as e:
        logger.error("calculation_error", error=str(e), exc_info=True)

    # Nested context
    with structlog.contextvars.bound_contextvars(user_id="user-789"):
        logger.info("processing_request")
        logger.info("validation_passed")

    print("\n" + "=" * 60)
    print("Structured logging examples above ☝️")
    print("=" * 60)
