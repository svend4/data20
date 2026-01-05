"""
Database models for Data20 Knowledge Base
Phase 5.1.1: SQLAlchemy models for persistence
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Enum as SQLEnum, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum


Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    """User roles for permissions"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


# ========================
# User Management
# ========================

class User(Base):
    """User account"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.name} for {self.user_id}>"


# ========================
# Job Management
# ========================

class Job(Base):
    """Tool execution job"""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Nullable до Phase 5.2 (Auth)

    # Tool info
    tool_name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(200))
    category = Column(String(50), index=True)

    # Execution
    parameters = Column(JSON, default={})
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    priority = Column(Integer, default=5)  # 1-10, higher = more important

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    queued_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Results
    return_code = Column(Integer)
    duration = Column(Float)  # seconds
    result = Column(JSON, default=None)  # For mobile: direct result storage
    error = Column(Text, default=None)  # For mobile: direct error storage

    # Celery task info
    celery_task_id = Column(String(255), index=True)
    worker_name = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="jobs")
    result_detail = relationship("JobResult", back_populates="job", uselist=False, cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.tool_name} ({self.status})>"


class JobResult(Base):
    """Job execution results"""
    __tablename__ = "job_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), unique=True, nullable=False)

    # Output
    stdout = Column(Text)
    stderr = Column(Text)

    # Files
    output_files = Column(JSON, default=[])  # List of file paths
    file_metadata = Column(JSON, default={})  # File sizes, types, etc.

    # Metrics
    memory_used = Column(Float)  # MB
    cpu_percent = Column(Float)

    # Storage
    storage_path = Column(String(500))  # Path where files are stored
    total_size = Column(Integer)  # Total size in bytes

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("Job", back_populates="result_detail")

    def __repr__(self):
        return f"<JobResult for {self.job_id}>"


class JobLog(Base):
    """Job execution logs"""
    __tablename__ = "job_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)

    # Log entry
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)

    # Context
    source = Column(String(100))  # worker, api, system
    metadata = Column(JSON, default={})

    # Relationships
    job = relationship("Job", back_populates="logs")

    def __repr__(self):
        return f"<JobLog {self.level}: {self.message[:50]}>"


# ========================
# Templates & Workflows
# ========================

class ParameterTemplate(Base):
    """Saved parameter templates"""
    __tablename__ = "parameter_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    tool_name = Column(String(100), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    parameters = Column(JSON, nullable=False)
    is_public = Column(Boolean, default=False)

    # Usage stats
    use_count = Column(Integer, default=0)
    last_used = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Template {self.name} for {self.tool_name}>"


class Workflow(Base):
    """Multi-step workflows"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Workflow definition (JSON)
    steps = Column(JSON, nullable=False)  # List of steps with dependencies

    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    # Stats
    run_count = Column(Integer, default=0)
    last_run = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow {self.name}>"


class WorkflowRun(Base):
    """Workflow execution instance"""
    __tablename__ = "workflow_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration = Column(Float)

    # Results
    job_ids = Column(JSON, default=[])  # List of job IDs created by this run

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="runs")

    def __repr__(self):
        return f"<WorkflowRun {self.workflow_id} ({self.status})>"


# ========================
# Analytics & Metrics
# ========================

class ToolStats(Base):
    """Aggregated tool usage statistics"""
    __tablename__ = "tool_stats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    tool_name = Column(String(100), nullable=False, unique=True, index=True)

    # Usage
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    # Performance
    avg_duration = Column(Float)
    min_duration = Column(Float)
    max_duration = Column(Float)

    # Recent activity
    last_run = Column(DateTime)
    last_success = Column(DateTime)
    last_failure = Column(DateTime)

    # Popularity
    unique_users = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ToolStats {self.tool_name}: {self.total_runs} runs>"


class SystemMetrics(Base):
    """System-wide metrics snapshots"""
    __tablename__ = "system_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Queue metrics
    pending_jobs = Column(Integer, default=0)
    running_jobs = Column(Integer, default=0)
    completed_jobs_24h = Column(Integer, default=0)
    failed_jobs_24h = Column(Integer, default=0)

    # Performance
    avg_job_duration = Column(Float)
    avg_queue_time = Column(Float)

    # System resources
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)

    # Workers
    active_workers = Column(Integer, default=0)

    def __repr__(self):
        return f"<SystemMetrics at {self.timestamp}>"


# ========================
# Utility functions
# ========================

def init_db(engine):
    """Initialize database schema"""
    Base.metadata.create_all(engine)


def drop_db(engine):
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(engine)
