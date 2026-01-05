#!/usr/bin/env python3
"""
Tool Runner - Выполнение Python инструментов с отслеживанием прогресса
Phase 4.3: Асинхронное выполнение инструментов
"""

import subprocess
import asyncio
import time
import json
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(str, Enum):
    """Статус выполнения задачи"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Результат выполнения инструмента"""
    job_id: str
    tool_name: str
    status: JobStatus
    output: str = ""
    error: str = ""
    return_code: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    output_files: list = field(default_factory=list)
    progress: int = 0


class ToolRunner:
    """Менеджер выполнения инструментов"""

    def __init__(self, tools_dir: Path = Path("tools"), output_dir: Path = Path(".")):
        self.tools_dir = Path(tools_dir)
        self.output_dir = Path(output_dir)
        self.jobs: Dict[str, JobResult] = {}
        self.running_processes: Dict[str, subprocess.Popen] = {}

    async def run_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> JobResult:
        """
        Запустить инструмент асинхронно

        Args:
            tool_name: Имя инструмента (без .py)
            parameters: Параметры для инструмента
            progress_callback: Callback для обновления прогресса (progress, message)

        Returns:
            JobResult с результатами выполнения
        """

        # Создать job
        job_id = str(uuid.uuid4())
        job = JobResult(
            job_id=job_id,
            tool_name=tool_name,
            status=JobStatus.PENDING,
            started_at=datetime.now()
        )
        self.jobs[job_id] = job

        # Путь к инструменту
        tool_path = self.tools_dir / f"{tool_name}.py"

        if not tool_path.exists():
            job.status = JobStatus.FAILED
            job.error = f"Tool not found: {tool_path}"
            job.completed_at = datetime.now()
            return job

        # Построить команду
        cmd = ["python3", str(tool_path)]

        # Добавить параметры
        if parameters:
            for key, value in parameters.items():
                if value is not None:
                    if isinstance(value, bool):
                        if value:
                            cmd.append(f"--{key}")
                    else:
                        cmd.extend([f"--{key}", str(value)])

        # Запустить процесс
        try:
            job.status = JobStatus.RUNNING
            if progress_callback:
                progress_callback(10, "Starting tool...")

            # Асинхронное выполнение
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.output_dir
            )

            self.running_processes[job_id] = process

            if progress_callback:
                progress_callback(30, "Tool running...")

            # Ожидать завершения
            stdout, stderr = await process.communicate()

            # Обновить результат
            job.output = stdout.decode('utf-8', errors='replace')
            job.error = stderr.decode('utf-8', errors='replace')
            job.return_code = process.returncode
            job.completed_at = datetime.now()

            if job.started_at:
                job.duration = (job.completed_at - job.started_at).total_seconds()

            if process.returncode == 0:
                job.status = JobStatus.COMPLETED
                job.progress = 100

                if progress_callback:
                    progress_callback(100, "Completed successfully!")

                # Найти выходные файлы
                job.output_files = self._detect_output_files(tool_name)
            else:
                job.status = JobStatus.FAILED
                if progress_callback:
                    progress_callback(100, f"Failed with code {process.returncode}")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()

            if progress_callback:
                progress_callback(100, f"Error: {str(e)}")

        finally:
            if job_id in self.running_processes:
                del self.running_processes[job_id]

        return job

    async def cancel_job(self, job_id: str) -> bool:
        """Отменить выполняющуюся задачу"""

        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]

        if job.status != JobStatus.RUNNING:
            return False

        if job_id in self.running_processes:
            process = self.running_processes[job_id]
            try:
                # Попытаться graceful shutdown
                process.terminate()

                # Ждать 5 секунд
                await asyncio.sleep(5)

                # Если еще работает, kill
                if process.poll() is None:
                    process.kill()

                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()

                if job.started_at:
                    job.duration = (job.completed_at - job.started_at).total_seconds()

                del self.running_processes[job_id]
                return True

            except Exception as e:
                print(f"Error cancelling job {job_id}: {e}")
                return False

        return False

    def get_job(self, job_id: str) -> Optional[JobResult]:
        """Получить информацию о задаче"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> list[JobResult]:
        """Получить все задачи"""
        return list(self.jobs.values())

    def get_running_jobs(self) -> list[JobResult]:
        """Получить запущенные задачи"""
        return [job for job in self.jobs.values() if job.status == JobStatus.RUNNING]

    def _detect_output_files(self, tool_name: str) -> list[str]:
        """Определить файлы, созданные инструментом"""

        output_files = []

        # Возможные расширения
        extensions = ['.html', '.json', '.csv', '.txt', '.md']

        for ext in extensions:
            file_path = self.output_dir / f"{tool_name}{ext}"
            if file_path.exists():
                output_files.append(str(file_path.relative_to(self.output_dir)))

        # Дополнительные паттерны
        patterns = [
            f"{tool_name}_*.html",
            f"{tool_name}_*.json",
            f"*{tool_name}*.html",
        ]

        for pattern in patterns:
            for file_path in self.output_dir.glob(pattern):
                rel_path = str(file_path.relative_to(self.output_dir))
                if rel_path not in output_files:
                    output_files.append(rel_path)

        return output_files

    def clear_old_jobs(self, max_age_hours: int = 24):
        """Удалить старые завершённые задачи"""

        now = datetime.now()
        to_delete = []

        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at:
                    age_hours = (now - job.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_delete.append(job_id)

        for job_id in to_delete:
            del self.jobs[job_id]

        return len(to_delete)

    def get_system_stats(self) -> Dict[str, Any]:
        """Получить статистику системы"""

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.output_dir))

        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "running_jobs": len(self.get_running_jobs()),
            "total_jobs": len(self.jobs)
        }


# Пример использования
async def main():
    runner = ToolRunner()

    # Callback для прогресса
    def on_progress(progress: int, message: str):
        print(f"[{progress}%] {message}")

    # Запустить инструмент
    print("🚀 Запуск инструмента build_graph...")
    result = await runner.run_tool(
        "build_graph",
        parameters={},
        progress_callback=on_progress
    )

    print(f"\n✅ Статус: {result.status}")
    print(f"⏱️  Время: {result.duration:.2f}s")
    print(f"📁 Выходные файлы: {', '.join(result.output_files)}")

    if result.error:
        print(f"❌ Ошибка: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
