#!/usr/bin/env python3
"""
FastAPI Backend Server for Data20 Knowledge Base
Phase 4: Full Backend Integration with WebSocket Support
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import asyncio
import json
from datetime import datetime

from tool_registry import ToolRegistry, ToolCategory
from tool_runner import ToolRunner, JobStatus

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
    description="Backend API for running 57+ data analysis tools",
    version="4.0.0"
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
# Lifecycle Events
# ========================

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    print("🚀 Starting Data20 Backend API Server...")
    print("=" * 60)

    # Сканировать инструменты
    count = registry.scan_tools()
    print(f"✅ Loaded {count} tools")

    # Экспортировать реестр
    registry_file = output_dir / "tool_registry.json"
    with open(registry_file, 'w', encoding='utf-8') as f:
        json.dump(registry.to_json(), f, indent=2, ensure_ascii=False)
    print(f"✅ Registry exported to {registry_file}")

    print("=" * 60)
    print("🎯 Server ready!")
    print("📚 API Docs: http://localhost:8001/docs")
    print("🔧 Total Tools: {}".format(count))
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup при остановке"""
    print("\n👋 Shutting down server...")

    # Отменить все запущенные задачи
    running = runner.get_running_jobs()
    for job in running:
        await runner.cancel_job(job.job_id)

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
    """Получить список всех инструментов"""
    return registry.to_json()


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
async def run_tool(request: ToolRunRequest, background_tasks: BackgroundTasks):
    """
    Запустить инструмент

    Возвращает job_id для отслеживания прогресса через WebSocket
    """

    # Проверить существование инструмента
    tool = registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")

    # Запустить в фоне
    async def run_in_background():
        await runner.run_tool(request.tool_name, request.parameters)

    background_tasks.add_task(run_in_background)

    # Создать временный job для получения ID
    import uuid
    job_id = str(uuid.uuid4())

    return ToolRunResponse(
        job_id=job_id,
        tool_name=request.tool_name,
        status="pending",
        message=f"Tool {request.tool_name} started"
    )


@app.get("/api/jobs")
async def get_all_jobs():
    """Получить все задачи"""
    jobs = runner.get_all_jobs()

    return {
        "total": len(jobs),
        "running": len([j for j in jobs if j.status == JobStatus.RUNNING]),
        "completed": len([j for j in jobs if j.status == JobStatus.COMPLETED]),
        "failed": len([j for j in jobs if j.status == JobStatus.FAILED]),
        "jobs": [
            {
                "job_id": j.job_id,
                "tool_name": j.tool_name,
                "status": j.status.value,
                "progress": j.progress,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "duration": j.duration
            }
            for j in jobs
        ]
    }


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Получить статус задачи"""
    job = runner.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        tool_name=job.tool_name,
        status=job.status.value,
        progress=job.progress,
        output=job.output if job.status == JobStatus.COMPLETED else None,
        error=job.error if job.status == JobStatus.FAILED else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        duration=job.duration,
        output_files=job.output_files
    )


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Отменить задачу"""
    success = await runner.cancel_job(job_id)

    if not success:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job {job_id}")

    return {"message": f"Job {job_id} cancelled"}


@app.get("/api/stats")
async def get_system_stats():
    """Получить статистику системы"""
    stats = runner.get_system_stats()
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
