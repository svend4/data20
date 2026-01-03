#!/usr/bin/env python3
"""
FastAPI Backend Server for Data20 Knowledge Base
Phase 5.3.1: Structured Logging Integration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session
import asyncio
import json
from datetime import datetime
import os

# Structured logging
from logger import (
    configure_logging, get_logger, LoggingMiddleware,
    log_startup, log_shutdown, log_tool_start, log_tool_success, log_tool_failure
)

from tool_registry import ToolRegistry, ToolCategory
from tool_runner import ToolRunner, JobStatus as RunnerJobStatus
from database import get_db, check_database_connection, init_database, engine
from models import Job as DBJob, JobResult as DBJobResult, JobLog as DBJobLog, JobStatus as DBJobStatus
from redis_client import get_redis, close_redis

# Celery imports
try:
    from celery_tasks import run_tool_task, get_active_tasks, get_worker_stats, revoke_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("⚠️  Celery not available - using fallback execution")

# ========================
# Pydantic Models
# ========================

class ToolRunRequest(BaseModel):
    """Запрос на запуск инструмента"""
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolRunResponse(BaseModel):
    """Ответ на запуск инструмента"""
    job_id: str
    tool_name: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Статус задачи"""
    job_id: str
    tool_name: str
    status: str
    progress: int
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: Optional[float] = None
    output_files: List[str] = []


# ========================
# Logging Configuration
# ========================

# Configure structured logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "console")  # "console" or "json"
LOG_DIR = os.getenv("LOG_DIR", None)

configure_logging(level=LOG_LEVEL, format=LOG_FORMAT, log_dir=LOG_DIR)
logger = get_logger(__name__)

# ========================
# FastAPI App
# ========================

app = FastAPI(
    title="Data20 Knowledge Base API",
    description="Backend API for running 57+ data analysis tools with PostgreSQL + Redis + Celery",
    version="5.3.1"
)

# Logging middleware (first!)
app.add_middleware(LoggingMiddleware)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация
tools_dir = Path(__file__).parent.parent / "tools"
output_dir = Path(__file__).parent.parent
static_dir = Path(__file__).parent.parent / "static_site" / "public"

registry = ToolRegistry(tools_dir)
runner = ToolRunner(tools_dir, output_dir)

# WebSocket connections
active_connections: List[WebSocket] = []


# ========================
# Helper Functions
# ========================

def _convert_runner_status(runner_status: RunnerJobStatus) -> DBJobStatus:
    """Convert tool_runner.JobStatus to models.JobStatus"""
    mapping = {
        RunnerJobStatus.PENDING: DBJobStatus.PENDING,
        RunnerJobStatus.RUNNING: DBJobStatus.RUNNING,
        RunnerJobStatus.COMPLETED: DBJobStatus.COMPLETED,
        RunnerJobStatus.FAILED: DBJobStatus.FAILED,
        RunnerJobStatus.CANCELLED: DBJobStatus.CANCELLED
    }
    return mapping.get(runner_status, DBJobStatus.FAILED)


# ========================
# Lifecycle Events
# ========================

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Starting Data20 Backend API Server...")

    # Проверить подключение к БД
    db_connected = check_database_connection()
    if db_connected:
        logger.info("database_connected")
        # Создать таблицы если их нет
        try:
            init_database()
            logger.info("database_initialized")
        except Exception as e:
            logger.warning("database_init_warning", error=str(e))
    else:
        logger.warning("database_unavailable", message="Running without persistence")

    # Проверить подключение к Redis
    redis = get_redis()
    redis_connected = redis.is_available()
    if redis_connected:
        redis_info = redis.get_info()
        logger.info(
            "redis_connected",
            version=redis_info.get('version'),
            clients=redis_info.get('connected_clients')
        )
    else:
        logger.warning("redis_unavailable", message="Running without cache")

    # Сканировать инструменты
    count = registry.scan_tools()
    logger.info("tools_loaded", count=count)

    # Экспортировать реестр
    registry_file = output_dir / "tool_registry.json"
    registry_data = registry.to_json()
    with open(registry_file, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)
    logger.info("registry_exported", file=str(registry_file))

    # Кэшировать реестр в Redis
    if redis_connected:
        if redis.cache_tool_registry(registry_data, ttl=3600):
            logger.info("registry_cached", ttl_seconds=3600)

    # Log startup summary
    log_startup(
        service="data20_backend",
        version="5.3.1",
        config={
            "database": "Connected" if db_connected else "Disabled",
            "redis": "Connected" if redis_connected else "Disabled",
            "celery": "Available" if CELERY_AVAILABLE else "Disabled",
            "tools_count": count,
            "log_level": LOG_LEVEL,
            "log_format": LOG_FORMAT
        }
    )

    logger.info("🎯 Server ready!", api_docs="http://localhost:8001/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup при остановке"""
    logger.info("👋 Shutting down server...")

    # Отменить все запущенные задачи
    running = runner.get_running_jobs()
    if running:
        logger.info("cancelling_jobs", count=len(running))
        for job in running:
            await runner.cancel_job(job.job_id)

    # Закрыть подключения к БД
    try:
        engine.dispose()
        logger.info("database_closed")
    except Exception as e:
        logger.warning("database_close_failed", error=str(e))

    # Закрыть Redis
    try:
        close_redis()
        logger.info("redis_closed")
    except Exception as e:
        logger.warning("redis_close_failed", error=str(e))

    log_shutdown(service="data20_backend")
    logger.info("✅ Cleanup complete")


# ========================
# API Endpoints
# ========================

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": "Data20 Knowledge Base API",
        "version": "4.0.0",
        "status": "running",
        "total_tools": len(registry.tools),
        "docs": "/docs",
        "registry": "/api/tools"
    }


@app.get("/api/tools")
async def get_all_tools():
    """Получить список всех инструментов (с кэшированием)"""

    # Попытаться получить из Redis cache
    redis = get_redis()
    if redis.is_available():
        cached = redis.get_cached_tool_registry()
        if cached:
            return cached

    # Fallback к registry
    registry_data = registry.to_json()

    # Обновить cache
    if redis.is_available():
        redis.cache_tool_registry(registry_data, ttl=3600)

    return registry_data


@app.get("/api/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Получить информацию об инструменте"""
    tool = registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    return {
        "name": tool.name,
        "display_name": tool.display_name,
        "description": tool.description,
        "category": tool.category.value,
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
        "output_formats": tool.output_formats,
        "icon": tool.icon,
        "color": tool.color,
        "tags": tool.tags,
        "complexity": tool.complexity,
        "estimated_time": tool.estimated_time
    }


@app.get("/api/categories")
async def get_categories():
    """Получить список категорий с количеством инструментов"""
    return {
        cat.value: {
            "name": cat.value,
            "count": len(tools),
            "tools": tools
        }
        for cat, tools in registry.categories.items()
        if tools
    }


@app.get("/api/categories/{category}")
async def get_tools_by_category(category: str):
    """Получить инструменты по категории"""
    try:
        cat_enum = ToolCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    tools = registry.get_by_category(cat_enum)

    return {
        "category": category,
        "count": len(tools),
        "tools": [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "icon": t.icon,
                "color": t.color
            }
            for t in tools
        ]
    }


@app.get("/api/search")
async def search_tools(q: str):
    """Поиск инструментов"""
    results = registry.search(q)

    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "category": t.category.value,
                "icon": t.icon
            }
            for t in results
        ]
    }


@app.post("/api/run")
async def run_tool(
    request: ToolRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    use_celery: bool = True
):
    """
    Запустить инструмент через Celery или fallback

    Args:
        use_celery: Use Celery if available (default: True)

    Возвращает job_id для отслеживания прогресса
    """

    # Проверить существование инструмента
    tool = registry.get_tool(request.tool_name)
    if not tool:
        logger.warning("tool_not_found", tool_name=request.tool_name)
        raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")

    # Создать job в БД
    import uuid
    job_id = str(uuid.uuid4())

    logger.info("creating_job", job_id=job_id, tool_name=request.tool_name, parameters=request.parameters)

    db_job = DBJob(
        id=job_id,
        tool_name=request.tool_name,
        parameters=request.parameters,
        status=DBJobStatus.PENDING
    )

    try:
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.debug("job_saved_to_db", job_id=job_id)
    except Exception as e:
        logger.warning("job_save_failed", job_id=job_id, error=str(e))
        # Продолжить без БД

    # Выбрать метод выполнения: Celery или fallback
    if CELERY_AVAILABLE and use_celery:
        # ========================================
        # Celery Execution (Distributed)
        # ========================================
        try:
            # Запустить задачу через Celery
            task = run_tool_task.delay(
                job_id=job_id,
                tool_name=request.tool_name,
                parameters=request.parameters
            )

            # Сохранить Celery task ID
            try:
                db_job_update = db.query(DBJob).filter(DBJob.id == job_id).first()
                if db_job_update:
                    db_job_update.celery_task_id = task.id
                    db_job_update.status = DBJobStatus.QUEUED
                    db.commit()
            except:
                pass

            return ToolRunResponse(
                job_id=job_id,
                tool_name=request.tool_name,
                status="queued",
                message=f"Tool {request.tool_name} queued for execution (Celery task: {task.id})"
            )

        except Exception as e:
            print(f"⚠️  Celery execution failed, falling back to local: {e}")
            # Fallback to local execution

    # ========================================
    # Fallback Execution (Local BackgroundTasks)
    # ========================================
    async def run_in_background():
        result = await runner.run_tool(request.tool_name, request.parameters)

        # Сохранить результат в БД (с новой сессией)
        from database import get_db_context
        try:
            with get_db_context() as bg_db:
                # Обновить job
                db_job_update = bg_db.query(DBJob).filter(DBJob.id == job_id).first()
                if db_job_update:
                    db_job_update.status = _convert_runner_status(result.status)
                    db_job_update.started_at = result.started_at
                    db_job_update.completed_at = result.completed_at
                    db_job_update.duration = result.duration

                    # Создать result
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
                    bg_db.add(db_result)

                    # Создать log entry
                    db_log = DBJobLog(
                        job_id=job_id,
                        level="INFO" if result.status == RunnerJobStatus.COMPLETED else "ERROR",
                        message=result.output if result.status == RunnerJobStatus.COMPLETED else result.error
                    )
                    bg_db.add(db_log)
        except Exception as e:
            print(f"⚠️  Failed to save job result to database: {e}")

        # Опубликовать обновление в Redis pub/sub
        redis = get_redis()
        if redis.is_available():
            redis.publish("job_updates", {
                "job_id": job_id,
                "status": result.status.value,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            })

            # Кэшировать финальный статус
            redis.cache_job_status(job_id, {
                "status": result.status.value,
                "output_files": result.output_files,
                "duration": result.duration
            }, ttl=600)  # 10 минут

    background_tasks.add_task(run_in_background)

    return ToolRunResponse(
        job_id=job_id,
        tool_name=request.tool_name,
        status="pending",
        message=f"Tool {request.tool_name} started (local execution)"
    )


@app.get("/api/jobs")
async def get_all_jobs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Получить все задачи (из памяти + БД)"""

    all_jobs = []

    # 1. Получить задачи из памяти (текущие)
    memory_jobs = runner.get_all_jobs()
    for j in memory_jobs:
        all_jobs.append({
            "job_id": j.job_id,
            "tool_name": j.tool_name,
            "status": j.status.value,
            "progress": j.progress,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "duration": j.duration,
            "source": "memory"
        })

    # 2. Получить задачи из БД (исторические)
    try:
        db_jobs = db.query(DBJob)\
            .order_by(DBJob.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        # Исключить те, которые уже в памяти
        memory_job_ids = {j.job_id for j in memory_jobs}

        for j in db_jobs:
            if str(j.id) not in memory_job_ids:
                all_jobs.append({
                    "job_id": str(j.id),
                    "tool_name": j.tool_name,
                    "status": j.status.value,
                    "progress": 100 if j.status == DBJobStatus.COMPLETED else 0,
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "duration": j.duration,
                    "source": "database"
                })
    except Exception as e:
        print(f"⚠️  Failed to fetch jobs from database: {e}")

    # Сортировать по дате создания (новые первые)
    all_jobs.sort(key=lambda x: x.get("started_at") or "", reverse=True)

    return {
        "total": len(all_jobs),
        "running": len([j for j in all_jobs if j["status"] == "running"]),
        "completed": len([j for j in all_jobs if j["status"] == "completed"]),
        "failed": len([j for j in all_jobs if j["status"] == "failed"]),
        "jobs": all_jobs
    }


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Получить статус задачи (из памяти или БД)"""

    # Сначала проверить в памяти (запущенные задачи)
    job = runner.get_job(job_id)

    if job:
        # Задача в памяти (выполняется или недавно завершена)
        return JobStatusResponse(
            job_id=job.job_id,
            tool_name=job.tool_name,
            status=job.status.value,
            progress=job.progress,
            output=job.output if job.status == RunnerJobStatus.COMPLETED else None,
            error=job.error if job.status == RunnerJobStatus.FAILED else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            duration=job.duration,
            output_files=job.output_files
        )

    # Проверить в БД (завершённые задачи)
    try:
        db_job = db.query(DBJob).filter(DBJob.id == job_id).first()

        if db_job:
            # Загрузить result
            db_result = db.query(DBJobResult).filter(DBJobResult.job_id == job_id).first()

            return JobStatusResponse(
                job_id=str(db_job.id),
                tool_name=db_job.tool_name,
                status=db_job.status.value,
                progress=100 if db_job.status == DBJobStatus.COMPLETED else 0,
                output=db_result.stdout if db_result else None,
                error=db_result.stderr if db_result else None,
                started_at=db_job.started_at.isoformat() if db_job.started_at else None,
                completed_at=db_job.completed_at.isoformat() if db_job.completed_at else None,
                duration=db_job.duration,
                output_files=db_result.output_files if db_result else []
            )
    except Exception as e:
        print(f"⚠️  Database query failed: {e}")

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str, db: Session = Depends(get_db)):
    """Получить логи задачи"""
    try:
        logs = db.query(DBJobLog)\
            .filter(DBJobLog.job_id == job_id)\
            .order_by(DBJobLog.timestamp.asc())\
            .all()

        return {
            "job_id": job_id,
            "total": len(logs),
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message
                }
                for log in logs
            ]
        }
    except Exception as e:
        print(f"⚠️  Failed to fetch logs: {e}")
        return {"job_id": job_id, "total": 0, "logs": []}


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Отменить задачу"""
    success = await runner.cancel_job(job_id)

    if not success:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job {job_id}")

    return {"message": f"Job {job_id} cancelled"}


@app.get("/api/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Получить статистику системы + БД + Redis"""
    stats = runner.get_system_stats()

    # Добавить статистику из БД
    try:
        total_jobs_db = db.query(DBJob).count()
        completed_jobs_db = db.query(DBJob).filter(DBJob.status == DBJobStatus.COMPLETED).count()
        failed_jobs_db = db.query(DBJob).filter(DBJob.status == DBJobStatus.FAILED).count()

        # Топ 5 инструментов
        from sqlalchemy import func
        top_tools = db.query(
            DBJob.tool_name,
            func.count(DBJob.id).label('count')
        ).group_by(DBJob.tool_name)\
         .order_by(func.count(DBJob.id).desc())\
         .limit(5)\
         .all()

        stats["database"] = {
            "connected": True,
            "total_jobs": total_jobs_db,
            "completed_jobs": completed_jobs_db,
            "failed_jobs": failed_jobs_db,
            "success_rate": (completed_jobs_db / total_jobs_db * 100) if total_jobs_db > 0 else 0,
            "top_tools": [
                {"name": name, "count": count}
                for name, count in top_tools
            ]
        }
    except Exception as e:
        print(f"⚠️  Failed to fetch database stats: {e}")
        stats["database"] = {
            "connected": False,
            "error": str(e)
        }

    # Добавить статистику Redis
    redis = get_redis()
    stats["redis"] = redis.get_info()

    return stats


@app.post("/api/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Удалить старые завершённые задачи"""
    deleted = runner.clear_old_jobs(max_age_hours)
    return {"message": f"Deleted {deleted} old jobs"}


# ========================
# Celery Management Endpoints
# ========================

@app.get("/api/celery/workers")
async def get_celery_workers():
    """Получить информацию о Celery workers"""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery not available")

    try:
        stats = get_worker_stats()
        return {
            "available": True,
            "workers": stats
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@app.get("/api/celery/tasks")
async def get_celery_tasks():
    """Получить список активных Celery задач"""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery not available")

    try:
        tasks = get_active_tasks()
        return {
            "total": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {e}")


@app.delete("/api/celery/tasks/{task_id}")
async def cancel_celery_task(task_id: str, terminate: bool = False):
    """Отменить Celery задачу"""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery not available")

    success = revoke_task(task_id, terminate=terminate)

    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to revoke task {task_id}")

    return {"message": f"Task {task_id} revoked"}


# ========================
# WebSocket для Real-time Updates
# ========================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для real-time обновлений

    Клиент отправляет:
    {
        "action": "subscribe",
        "job_id": "..."
    }

    Сервер отправляет:
    {
        "type": "progress",
        "job_id": "...",
        "progress": 50,
        "message": "..."
    }
    """

    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Получить сообщение от клиента
            data = await websocket.receive_json()

            action = data.get("action")

            if action == "subscribe":
                job_id = data.get("job_id")

                # Начать отправку обновлений для этой задачи
                while True:
                    job = runner.get_job(job_id)

                    if job:
                        await websocket.send_json({
                            "type": "progress",
                            "job_id": job.job_id,
                            "tool_name": job.tool_name,
                            "status": job.status.value,
                            "progress": job.progress,
                            "message": f"Status: {job.status.value}"
                        })

                        # Если завершено, отправить финальное сообщение
                        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                            await websocket.send_json({
                                "type": "complete",
                                "job_id": job.job_id,
                                "status": job.status.value,
                                "output_files": job.output_files,
                                "duration": job.duration,
                                "error": job.error if job.status == JobStatus.FAILED else None
                            })
                            break

                    await asyncio.sleep(1)

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("WebSocket client disconnected")


async def broadcast_message(message: dict):
    """Отправить сообщение всем подключенным клиентам"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass


# ========================
# Static Files (для локального использования)
# ========================

if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="static")


# ========================
# Main
# ========================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Data20 Knowledge Base - Backend API Server             ║
    ║  Phase 4: Full Integration with 57+ Tools               ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
