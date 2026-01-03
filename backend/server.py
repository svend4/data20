#!/usr/bin/env python3
"""
FastAPI Backend Server for Data20 Knowledge Base
Phase 5.1.7: Database Integration with PostgreSQL
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

from tool_registry import ToolRegistry, ToolCategory
from tool_runner import ToolRunner, JobStatus as RunnerJobStatus
from database import get_db, check_database_connection, init_database, engine
from models import Job as DBJob, JobResult as DBJobResult, JobLog as DBJobLog, JobStatus as DBJobStatus
from redis_client import get_redis, close_redis

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
# FastAPI App
# ========================

app = FastAPI(
    title="Data20 Knowledge Base API",
    description="Backend API for running 57+ data analysis tools with PostgreSQL persistence",
    version="5.1.7"
)

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
    print("🚀 Starting Data20 Backend API Server...")
    print("=" * 60)

    # Проверить подключение к БД
    db_connected = check_database_connection()
    if db_connected:
        print("✅ Database connected")
        # Создать таблицы если их нет
        try:
            init_database()
            print("✅ Database schema initialized")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")
    else:
        print("⚠️  Database not available (running without persistence)")

    # Проверить подключение к Redis
    redis = get_redis()
    redis_connected = redis.is_available()
    if redis_connected:
        print("✅ Redis connected")
        redis_info = redis.get_info()
        print(f"   Version: {redis_info.get('version')}, Clients: {redis_info.get('connected_clients')}")
    else:
        print("⚠️  Redis not available (running without cache)")

    # Сканировать инструменты
    count = registry.scan_tools()
    print(f"✅ Loaded {count} tools")

    # Экспортировать реестр
    registry_file = output_dir / "tool_registry.json"
    registry_data = registry.to_json()
    with open(registry_file, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Registry exported to {registry_file}")

    # Кэшировать реестр в Redis
    if redis_connected:
        if redis.cache_tool_registry(registry_data, ttl=3600):
            print("✅ Registry cached in Redis (TTL: 1h)")

    print("=" * 60)
    print("🎯 Server ready!")
    print("📚 API Docs: http://localhost:8001/docs")
    print("🔧 Total Tools: {}".format(count))
    print("💾 Database: {}".format("Connected" if db_connected else "Disabled"))
    print("🔥 Redis: {}".format("Connected" if redis_connected else "Disabled"))
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup при остановке"""
    print("\n👋 Shutting down server...")

    # Отменить все запущенные задачи
    running = runner.get_running_jobs()
    for job in running:
        await runner.cancel_job(job.job_id)

    # Закрыть подключения к БД
    try:
        engine.dispose()
        print("✅ Database connections closed")
    except:
        pass

    # Закрыть Redis
    try:
        close_redis()
        print("✅ Redis connection closed")
    except:
        pass

    print("✅ Cleanup complete")


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
    db: Session = Depends(get_db)
):
    """
    Запустить инструмент

    Возвращает job_id для отслеживания прогресса через WebSocket
    """

    # Проверить существование инструмента
    tool = registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")

    # Создать job в БД
    import uuid
    job_id = str(uuid.uuid4())

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
    except Exception as e:
        print(f"⚠️  Failed to save job to database: {e}")
        # Продолжить без БД

    # Запустить в фоне
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
        message=f"Tool {request.tool_name} started"
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
