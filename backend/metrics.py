#!/usr/bin/env python3
"""
Prometheus Metrics for Data20 Knowledge Base
Phase 5.3.2: Production-ready monitoring with Prometheus
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info, Summary,
    generate_latest, CONTENT_TYPE_LATEST, REGISTRY
)
from functools import wraps
import time
from typing import Callable
import psutil


# ========================
# HTTP Request Metrics
# ========================

# Counter: Total HTTP requests
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histogram: Request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Counter: HTTP errors
http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'status']
)


# ========================
# Tool Execution Metrics
# ========================

# Counter: Total tool executions
tool_executions_total = Counter(
    'tool_executions_total',
    'Total tool executions',
    ['tool_name', 'status']  # status: completed, failed, cancelled
)

# Histogram: Tool execution duration
tool_execution_duration_seconds = Histogram(
    'tool_execution_duration_seconds',
    'Tool execution duration in seconds',
    ['tool_name'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)  # 1s to 1h
)

# Gauge: Currently running tools
tool_executions_active = Gauge(
    'tool_executions_active',
    'Currently active tool executions',
    ['tool_name']
)


# ========================
# Database Metrics
# ========================

# Counter: Total database queries
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation']  # select, insert, update, delete
)

# Histogram: Query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Counter: Slow queries (> 1s)
db_slow_queries_total = Counter(
    'db_slow_queries_total',
    'Total slow database queries (>1s)',
    ['operation']
)

# Gauge: Database connection pool
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Idle database connections in pool'
)


# ========================
# Celery Task Metrics
# ========================

# Counter: Total Celery tasks
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']  # pending, running, success, failure, retry
)

# Histogram: Task duration
celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

# Gauge: Active tasks
celery_tasks_active = Gauge(
    'celery_tasks_active',
    'Currently active Celery tasks',
    ['task_name']
)

# Gauge: Queue length
celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue']
)

# Counter: Task retries
celery_task_retries_total = Counter(
    'celery_task_retries_total',
    'Total Celery task retries',
    ['task_name']
)


# ========================
# Redis Cache Metrics
# ========================

# Counter: Cache hits
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']  # tool_registry, job_status, etc.
)

# Counter: Cache misses
cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Gauge: Cache size
cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes'
)


# ========================
# System Metrics
# ========================

# Gauge: CPU usage
system_cpu_percent = Gauge(
    'system_cpu_percent',
    'System CPU usage percentage'
)

# Gauge: Memory usage
system_memory_percent = Gauge(
    'system_memory_percent',
    'System memory usage percentage'
)

system_memory_used_bytes = Gauge(
    'system_memory_used_bytes',
    'System memory used in bytes'
)

# Gauge: Disk usage
system_disk_percent = Gauge(
    'system_disk_percent',
    'System disk usage percentage'
)

system_disk_used_bytes = Gauge(
    'system_disk_used_bytes',
    'System disk used in bytes'
)


# ========================
# Application Info
# ========================

# Info: Application version and metadata
app_info = Info(
    'app',
    'Application information'
)


# ========================
# Decorator Helpers
# ========================

def track_request_metrics(method: str, endpoint: str):
    """
    Decorator to track HTTP request metrics

    Usage:
        @track_request_metrics("POST", "/api/run")
        async def run_tool(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                status = "200"  # Assume success

                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                duration = time.time() - start_time
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

                return result

            except Exception as e:
                status = "500"  # Error

                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                raise

        return wrapper
    return decorator


def track_tool_execution(tool_name: str):
    """
    Context manager to track tool execution metrics

    Usage:
        with track_tool_execution("build_graph"):
            result = run_tool(...)
    """
    class ToolExecutionTracker:
        def __enter__(self):
            self.start_time = time.time()
            tool_executions_active.labels(tool_name=tool_name).inc()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            tool_executions_active.labels(tool_name=tool_name).dec()

            if exc_type is None:
                # Success
                tool_executions_total.labels(
                    tool_name=tool_name,
                    status="completed"
                ).inc()

                tool_execution_duration_seconds.labels(
                    tool_name=tool_name
                ).observe(duration)
            else:
                # Failure
                tool_executions_total.labels(
                    tool_name=tool_name,
                    status="failed"
                ).inc()

            return False  # Don't suppress exceptions

    return ToolExecutionTracker()


# ========================
# Metric Update Functions
# ========================

def update_system_metrics():
    """Update system resource metrics"""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    system_cpu_percent.set(cpu_percent)

    # Memory
    memory = psutil.virtual_memory()
    system_memory_percent.set(memory.percent)
    system_memory_used_bytes.set(memory.used)

    # Disk
    disk = psutil.disk_usage('/')
    system_disk_percent.set(disk.percent)
    system_disk_used_bytes.set(disk.used)


def update_db_pool_metrics(engine):
    """
    Update database connection pool metrics

    Args:
        engine: SQLAlchemy engine
    """
    try:
        pool = engine.pool

        # Get pool status
        db_connections_active.set(pool.checkedout())
        db_connections_idle.set(pool.size() - pool.checkedout())

    except Exception as e:
        # Ignore if pool metrics not available
        pass


def update_redis_metrics(redis_client):
    """
    Update Redis cache metrics

    Args:
        redis_client: RedisClient instance
    """
    try:
        if redis_client.is_available():
            info = redis_client.client.info('memory')
            cache_size_bytes.set(info.get('used_memory', 0))
    except Exception:
        pass


def update_celery_metrics():
    """Update Celery task queue metrics"""
    try:
        from celery_tasks import get_active_tasks, celery_app

        # Active tasks
        active_tasks = get_active_tasks()

        # Count by task name
        task_counts = {}
        for task in active_tasks:
            task_name = task.get('name', 'unknown')
            task_counts[task_name] = task_counts.get(task_name, 0) + 1

        # Update gauges
        for task_name, count in task_counts.items():
            celery_tasks_active.labels(task_name=task_name).set(count)

        # Queue lengths
        inspect = celery_app.control.inspect()
        reserved = inspect.reserved()

        if reserved:
            for worker, tasks in reserved.items():
                # Extract queue name from worker tasks
                for task in tasks:
                    queue = task.get('delivery_info', {}).get('routing_key', 'default')
                    celery_queue_length.labels(queue=queue).inc()

    except Exception:
        # Celery not available
        pass


def record_db_query(operation: str, duration: float):
    """
    Record database query metrics

    Args:
        operation: Query type (select, insert, update, delete)
        duration: Query duration in seconds
    """
    db_queries_total.labels(operation=operation).inc()
    db_query_duration_seconds.labels(operation=operation).observe(duration)

    if duration > 1.0:
        db_slow_queries_total.labels(operation=operation).inc()


def record_cache_access(cache_type: str, hit: bool):
    """
    Record cache hit/miss

    Args:
        cache_type: Type of cache (tool_registry, job_status, etc.)
        hit: True if cache hit, False if miss
    """
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()


def record_celery_task(task_name: str, status: str, duration: float = None):
    """
    Record Celery task metrics

    Args:
        task_name: Name of the task
        status: Task status (success, failure, retry)
        duration: Task duration in seconds (optional)
    """
    celery_tasks_total.labels(task_name=task_name, status=status).inc()

    if duration is not None:
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)

    if status == "retry":
        celery_task_retries_total.labels(task_name=task_name).inc()


# ========================
# Initialization
# ========================

def init_metrics(app_version: str, environment: str = "production"):
    """
    Initialize application metrics

    Args:
        app_version: Application version
        environment: Environment (development, staging, production)
    """
    app_info.info({
        'version': app_version,
        'environment': environment,
        'name': 'data20_backend'
    })


# ========================
# Export Metrics
# ========================

def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format

    Returns:
        Metrics in Prometheus text format
    """
    # Update system metrics before export
    update_system_metrics()

    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Get content type for metrics"""
    return CONTENT_TYPE_LATEST


# ========================
# Testing
# ========================

if __name__ == "__main__":
    print("📊 Prometheus Metrics Module")
    print("=" * 60)

    # Initialize
    init_metrics(app_version="5.3.2", environment="development")

    # Simulate some metrics
    http_requests_total.labels(method="GET", endpoint="/api/tools", status="200").inc()
    http_requests_total.labels(method="POST", endpoint="/api/run", status="200").inc()
    http_request_duration_seconds.labels(method="GET", endpoint="/api/tools").observe(0.05)

    tool_executions_total.labels(tool_name="build_graph", status="completed").inc()
    tool_execution_duration_seconds.labels(tool_name="build_graph").observe(2.5)

    update_system_metrics()

    # Export metrics
    print("\n📈 Sample Metrics Output:")
    print("-" * 60)
    metrics = get_metrics().decode('utf-8')

    # Show only first 20 lines
    lines = metrics.split('\n')[:20]
    for line in lines:
        if line and not line.startswith('#'):
            print(line)

    print("...")
    print(f"\n✅ Total metrics: {len([l for l in metrics.split('\\n') if l and not l.startswith('#')])} lines")
    print("=" * 60)
