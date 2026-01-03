#!/usr/bin/env python3
"""
Celery Tasks for Data20 Knowledge Base
Phase 5.1.9: Distributed tool execution tasks
"""

from celery import Task
from celery_app import celery_app
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import database and models
from database import get_db_context
from models import Job as DBJob, JobResult as DBJobResult, JobLog as DBJobLog, JobStatus, ToolStats, SystemMetrics
from redis_client import get_redis

# Import tool runner
from tool_runner import ToolRunner

# Setup paths
tools_dir = Path(__file__).parent.parent / "tools"
output_dir = Path(__file__).parent.parent


class CallbackTask(Task):
    """
    Base task with callbacks for progress tracking
    """

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        print(f"✅ Task {task_id} succeeded")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        print(f"❌ Task {task_id} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        print(f"🔄 Task {task_id} retrying: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="celery_tasks.run_tool_task",
    max_retries=3,
    default_retry_delay=60
)
def run_tool_task(
    self,
    job_id: str,
    tool_name: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a tool as a Celery task

    Args:
        job_id: Job UUID from database
        tool_name: Name of the tool to run
        parameters: Tool parameters

    Returns:
        Dict with execution results
    """

    # Update job status to RUNNING
    with get_db_context() as db:
        job = db.query(DBJob).filter(DBJob.id == job_id).first()
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.celery_task_id = self.request.id

            # Create log
            log = DBJobLog(
                job_id=job_id,
                level="INFO",
                message=f"Task started by Celery worker {self.request.hostname}"
            )
            db.add(log)

    # Publish status update
    redis = get_redis()
    if redis.is_available():
        redis.publish("job_updates", {
            "job_id": job_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "worker": self.request.hostname
        })

    # Run the tool
    runner = ToolRunner(tools_dir, output_dir)

    try:
        # Execute tool asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            runner.run_tool(tool_name, parameters)
        )
        loop.close()

        # Save results to database
        with get_db_context() as db:
            job = db.query(DBJob).filter(DBJob.id == job_id).first()
            if job:
                # Update job
                job.status = JobStatus.COMPLETED if result.status.value == "completed" else JobStatus.FAILED
                job.completed_at = datetime.utcnow()
                job.duration = result.duration
                job.return_code = result.return_code

                # Create result
                db_result = DBJobResult(
                    job_id=job_id,
                    stdout=result.output,
                    stderr=result.error,
                    return_code=result.return_code,
                    output_files=result.output_files,
                    total_size=sum(
                        (output_dir / f).stat().st_size
                        for f in result.output_files
                        if (output_dir / f).exists()
                    )
                )
                db.add(db_result)

                # Create log
                log = DBJobLog(
                    job_id=job_id,
                    level="INFO" if job.status == JobStatus.COMPLETED else "ERROR",
                    message=result.output if job.status == JobStatus.COMPLETED else result.error
                )
                db.add(log)

        # Publish completion
        if redis.is_available():
            redis.publish("job_updates", {
                "job_id": job_id,
                "status": result.status.value,
                "completed_at": datetime.utcnow().isoformat(),
                "output_files": result.output_files,
                "duration": result.duration
            })

            # Cache result
            redis.cache_job_status(job_id, {
                "status": result.status.value,
                "output_files": result.output_files,
                "duration": result.duration
            }, ttl=600)

        return {
            "job_id": job_id,
            "status": result.status.value,
            "output_files": result.output_files,
            "duration": result.duration,
            "return_code": result.return_code
        }

    except Exception as e:
        # Mark job as failed
        with get_db_context() as db:
            job = db.query(DBJob).filter(DBJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()

                # Create error log
                log = DBJobLog(
                    job_id=job_id,
                    level="ERROR",
                    message=f"Task failed: {str(e)}"
                )
                db.add(log)

        # Publish failure
        if redis.is_available():
            redis.publish("job_updates", {
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            })

        # Retry if possible
        raise self.retry(exc=e)


@celery_app.task(name="celery_tasks.cleanup_old_jobs")
def cleanup_old_jobs(max_age_hours: int = 48) -> Dict[str, int]:
    """
    Clean up old completed jobs from database

    Args:
        max_age_hours: Delete jobs older than this many hours

    Returns:
        Dict with cleanup statistics
    """

    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    with get_db_context() as db:
        # Find old completed/failed jobs
        old_jobs = db.query(DBJob).filter(
            DBJob.completed_at < cutoff_time,
            DBJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])
        ).all()

        deleted_count = len(old_jobs)

        # Delete associated results and logs
        for job in old_jobs:
            db.query(DBJobResult).filter(DBJobResult.job_id == job.id).delete()
            db.query(DBJobLog).filter(DBJobLog.job_id == job.id).delete()
            db.delete(job)

    print(f"🧹 Cleaned up {deleted_count} old jobs (older than {max_age_hours}h)")

    return {
        "deleted": deleted_count,
        "cutoff_hours": max_age_hours
    }


@celery_app.task(name="celery_tasks.update_tool_statistics")
def update_tool_statistics() -> Dict[str, Any]:
    """
    Update tool usage statistics

    Returns:
        Dict with statistics
    """

    with get_db_context() as db:
        from sqlalchemy import func

        # Get tool usage stats
        stats = db.query(
            DBJob.tool_name,
            func.count(DBJob.id).label('total_runs'),
            func.count(DBJob.id).filter(DBJob.status == JobStatus.COMPLETED).label('successful_runs'),
            func.avg(DBJob.duration).label('avg_duration')
        ).group_by(DBJob.tool_name).all()

        # Update or create ToolStats records
        for stat in stats:
            tool_stat = db.query(ToolStats).filter(ToolStats.tool_name == stat.tool_name).first()

            if tool_stat:
                tool_stat.total_runs = stat.total_runs
                tool_stat.successful_runs = stat.successful_runs or 0
                tool_stat.failed_runs = stat.total_runs - (stat.successful_runs or 0)
                tool_stat.average_duration = float(stat.avg_duration) if stat.avg_duration else 0.0
                tool_stat.last_run = datetime.utcnow()
            else:
                tool_stat = ToolStats(
                    tool_name=stat.tool_name,
                    total_runs=stat.total_runs,
                    successful_runs=stat.successful_runs or 0,
                    failed_runs=stat.total_runs - (stat.successful_runs or 0),
                    average_duration=float(stat.avg_duration) if stat.avg_duration else 0.0,
                    last_run=datetime.utcnow()
                )
                db.add(tool_stat)

    print(f"📊 Updated statistics for {len(stats)} tools")

    return {
        "tools_updated": len(stats)
    }


@celery_app.task(name="celery_tasks.health_check")
def health_check() -> Dict[str, Any]:
    """
    Health check task for monitoring

    Returns:
        Dict with system health status
    """

    import psutil

    # Check database
    db_healthy = False
    try:
        with get_db_context() as db:
            db.execute("SELECT 1")
        db_healthy = True
    except:
        pass

    # Check Redis
    redis = get_redis()
    redis_healthy = redis.is_available()

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {"healthy": db_healthy},
        "redis": {"healthy": redis_healthy},
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available
        }
    }


# ========================
# Task Utilities
# ========================

def revoke_task(task_id: str, terminate: bool = False) -> bool:
    """
    Revoke (cancel) a running task

    Args:
        task_id: Celery task ID
        terminate: If True, terminate immediately (SIGKILL)

    Returns:
        True if revoked successfully
    """
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        return True
    except Exception as e:
        print(f"❌ Failed to revoke task {task_id}: {e}")
        return False


def get_active_tasks() -> list:
    """
    Get list of active tasks across all workers

    Returns:
        List of active task info dicts
    """
    inspect = celery_app.control.inspect()
    active = inspect.active()

    if not active:
        return []

    all_tasks = []
    for worker, tasks in active.items():
        for task in tasks:
            task["worker"] = worker
            all_tasks.append(task)

    return all_tasks


def get_worker_stats() -> Dict[str, Any]:
    """
    Get statistics from all workers

    Returns:
        Dict with worker stats
    """
    inspect = celery_app.control.inspect()

    return {
        "active": inspect.active(),
        "scheduled": inspect.scheduled(),
        "reserved": inspect.reserved(),
        "stats": inspect.stats(),
    }


if __name__ == "__main__":
    print("Celery Tasks Module")
    print(f"Registered tasks: {list(celery_app.tasks.keys())}")
