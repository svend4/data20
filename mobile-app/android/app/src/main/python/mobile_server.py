"""
Mobile Backend Server - Simplified FastAPI backend for Android/iOS

This is a lightweight version of the main backend optimized for mobile devices:
- SQLite instead of PostgreSQL
- No Celery workers (synchronous execution)
- No Redis caching
- No Prometheus metrics
- Minimal dependencies
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
import os
import sys
from datetime import datetime

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import mobile-adapted modules
from mobile_models import Base, User, Job, JobStatus, UserRole
from mobile_auth import (
    get_password_hash, authenticate_user, create_tokens_for_user,
    get_current_user, get_current_active_user
)
from mobile_database import get_db, init_mobile_database, engine
from mobile_tool_registry import ToolRegistry
from mobile_tool_runner import ToolRunner, JobStatus as RunnerJobStatus

# ========================
# Pydantic Models
# ========================

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        orm_mode = True

class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}
    input_file: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    tool_name: str
    status: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ========================
# Application Setup
# ========================

app = FastAPI(
    title="Data20 Mobile Backend",
    description="Embedded FastAPI backend for mobile devices",
    version="1.0.0"
)

# CORS - allow all origins on mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
tool_registry = None
tool_runner = None

# ========================
# Startup/Shutdown
# ========================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global tool_registry, tool_runner

    print("🚀 Starting mobile backend...")

    # Initialize database
    init_mobile_database()

    # Initialize tool registry
    tools_dir = Path(__file__).parent.parent / "tools"
    if not tools_dir.exists():
        tools_dir = Path(__file__).parent / "tools"

    tool_registry = ToolRegistry(tools_dir=tools_dir)
    print(f"✅ Loaded {len(tool_registry.tools)} tools")

    # Initialize tool runner
    upload_dir = os.getenv('DATA20_UPLOAD_PATH', '/tmp/data20/uploads')
    tool_runner = ToolRunner(
        tools_dir=tools_dir,
        output_dir=Path(upload_dir)
    )

    print("✅ Mobile backend started successfully")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    print("🛑 Shutting down mobile backend...")

# ========================
# Health & Status
# ========================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": "mobile",
        "database": os.getenv('DATA20_DATABASE_PATH', 'unknown'),
        "version": "1.0.0",
        "tools_count": len(tool_registry.tools) if tool_registry else 0
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Data20 Mobile Backend",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# ========================
# Authentication
# ========================

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.USER,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get JWT tokens"""
    user = authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")

    tokens = create_tokens_for_user(user)
    return tokens

@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user

# ========================
# Tools
# ========================

@app.get("/tools")
async def get_tools(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available tools"""
    tools = tool_registry.get_all_tools()

    if category:
        tools = [t for t in tools if t.category == category]

    return {
        "tools": [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "category": t.category,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "description": p.description
                    }
                    for p in t.parameters
                ],
                "icon": t.icon,
                "color": t.color
            }
            for t in tools
        ],
        "total": len(tools)
    }

@app.get("/tools/{tool_name}")
async def get_tool(
    tool_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get tool details"""
    tool = tool_registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {
        "name": tool.name,
        "display_name": tool.display_name,
        "description": tool.description,
        "category": tool.category,
        "parameters": [
            {
                "name": p.name,
                "type": p.type,
                "required": p.required,
                "default": p.default,
                "description": p.description,
                "choices": p.choices
            }
            for p in tool.parameters
        ],
        "output_files": tool.output_files,
        "estimated_time": tool.estimated_time,
        "icon": tool.icon,
        "color": tool.color,
        "tags": tool.tags
    }

# ========================
# Job Execution
# ========================

@app.post("/jobs/execute", response_model=JobResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Execute tool (synchronous on mobile)"""

    # Validate tool exists
    tool = tool_registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Create job record
    job = Job(
        tool_name=request.tool_name,
        parameters=request.parameters,
        status=JobStatus.RUNNING,
        user_id=current_user.id
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Execute tool synchronously (no Celery on mobile)
    try:
        result = await tool_runner.run_tool(
            tool_name=request.tool_name,
            parameters=request.parameters
        )

        # Update job with result
        job.status = JobStatus.COMPLETED
        job.result = {
            "output": result.output,
            "output_files": result.output_files,
            "duration": result.duration
        }
        job.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(job)

        return JobResponse(
            job_id=job.id,
            tool_name=job.tool_name,
            status=job.status.value,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            result=job.result
        )

    except Exception as e:
        # Update job with error
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(job)

        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@app.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's jobs"""
    query = db.query(Job).filter(Job.user_id == current_user.id)

    if status:
        query = query.filter(Job.status == status)

    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()

    return [
        JobResponse(
            job_id=job.id,
            tool_name=job.tool_name,
            status=job.status.value,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            result=job.result,
            error=job.error
        )
        for job in jobs
    ]

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get job details"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.id,
        tool_name=job.tool_name,
        status=job.status.value,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        result=job.result,
        error=job.error
    )

# ========================
# Categories
# ========================

@app.get("/categories")
async def get_categories(current_user: User = Depends(get_current_active_user)):
    """Get tool categories"""
    from mobile_tool_registry import ToolCategory

    return {
        "categories": [
            {
                "id": cat.value,
                "name": cat.value.replace('_', ' ').title()
            }
            for cat in ToolCategory
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
