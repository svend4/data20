#!/usr/bin/env python3
"""
Celery Application for Data20 Knowledge Base
Phase 5.1.9: Distributed task queue with Redis broker
"""

from celery import Celery
import os

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CELERY_BROKER_URL = f"{REDIS_URL}/1"  # Database 1 for broker
CELERY_RESULT_BACKEND = f"{REDIS_URL}/2"  # Database 2 for results

# Create Celery app
celery_app = Celery(
    "data20_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["celery_tasks"]  # Import tasks module
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "celery_tasks.run_tool_task": {"queue": "tools"},
        "celery_tasks.cleanup_old_jobs": {"queue": "maintenance"},
    },

    # Task time limits
    task_time_limit=3600,  # Hard limit: 1 hour
    task_soft_time_limit=3300,  # Soft limit: 55 minutes

    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Worker settings
    worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks

    # Task retry settings
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies

    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-old-jobs-daily": {
            "task": "celery_tasks.cleanup_old_jobs",
            "schedule": 86400.0,  # Every 24 hours
            "args": (48,),  # Delete jobs older than 48 hours
        },
        "update-tool-stats-hourly": {
            "task": "celery_tasks.update_tool_statistics",
            "schedule": 3600.0,  # Every hour
        },
    },

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Task annotations for specific configuration
celery_app.conf.task_annotations = {
    "celery_tasks.run_tool_task": {
        "rate_limit": "10/m",  # Max 10 tool runs per minute
        "time_limit": 3600,
        "soft_time_limit": 3300,
    }
}

# Optional: Configure logging
celery_app.conf.worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"


if __name__ == "__main__":
    celery_app.start()
