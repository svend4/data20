# 🚀 Phase 5 Quick Start Guide

## Что в Phase 5.1 (Database Infrastructure)

Созданы следующие компоненты:

### 1. Database Models (`backend/models.py`)
- ✅ User (аутентификация)
- ✅ Job (задачи выполнения)
- ✅ JobResult (результаты)
- ✅ JobLog (логи)
- ✅ ParameterTemplate (шаблоны)
- ✅ Workflow (многошаговые процессы)
- ✅ ToolStats (статистика инструментов)
- ✅ SystemMetrics (метрики системы)

### 2. Database Connection (`backend/database.py`)
- ✅ SQLAlchemy engine с connection pooling
- ✅ Session factory
- ✅ Dependency injection для FastAPI
- ✅ Context managers
- ✅ Health checks

### 3. Migrations (`backend/alembic/`)
- ✅ Alembic configuration
- ✅ Migration environment
- ✅ Template для migration файлов

### 4. Docker Infrastructure
- ✅ PostgreSQL 15 (port 5432)
- ✅ Redis 7 (port 6379)
- ✅ Celery worker (опционально)
- ✅ Prometheus + Grafana (опционально)

---

## 📋 Quick Start

### Вариант 1: Только база данных (минимальный)

```bash
# 1. Запустить PostgreSQL и Redis
docker-compose -f docker-compose.phase5.yml up -d postgres redis

# 2. Подождать пока запустятся (health checks)
docker-compose -f docker-compose.phase5.yml ps

# 3. Установить Python зависимости
cd backend
pip install -r requirements.txt

# 4. Проверить подключение к БД
python database.py check

# 5. Создать схему БД
python database.py init

# 6. Готово!
```

Теперь PostgreSQL доступен по адресу: `postgresql://data20:data20@localhost:5432/data20_kb`

---

### Вариант 2: Полная конфигурация (с backend и celery)

```bash
# 1. Запустить всё с профилем 'full'
docker-compose -f docker-compose.phase5.yml --profile full up -d

# 2. Проверить статус
docker-compose -f docker-compose.phase5.yml ps

# Должны быть запущены:
# - data20_postgres (PostgreSQL)
# - data20_redis (Redis)
# - data20_backend (Backend API)
# - data20_celery (Celery Worker)

# 3. Проверить логи
docker-compose -f docker-compose.phase5.yml logs -f backend
```

Backend доступен: http://localhost:8001

---

### Вариант 3: С мониторингом (Prometheus + Grafana)

```bash
# 1. Запустить с профилем 'monitoring'
docker-compose -f docker-compose.phase5.yml --profile monitoring up -d

# 2. Откройте dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

---

## 🔧 Работа с базой данных

### Создать migration

```bash
cd backend

# Auto-generate migration из models
alembic revision --autogenerate -m "Add new field to Job"

# Применить migration
alembic upgrade head

# Откатить migration
alembic downgrade -1
```

### Проверить БД

```bash
# Python script
python database.py check

# SQL напрямую
psql postgresql://data20:data20@localhost:5432/data20_kb
```

### Сбросить БД (⚠️ удалит все данные!)

```bash
python database.py reset
```

---

## 📊 Модели данных

### Job (задача выполнения)

```python
from database import get_db_context
from models import Job, JobStatus
from datetime import datetime

with get_db_context() as db:
    # Создать job
    job = Job(
        tool_name="build_graph",
        user_id=user.id,
        parameters={"depth": 3},
        status=JobStatus.PENDING
    )
    db.add(job)
    db.commit()

    # Обновить статус
    job.status = JobStatus.RUNNING
    job.started_at = datetime.utcnow()
    db.commit()

    # Завершить
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    job.duration = (job.completed_at - job.started_at).total_seconds()
    db.commit()
```

### JobResult (результаты)

```python
from models import JobResult

with get_db_context() as db:
    result = JobResult(
        job_id=job.id,
        stdout="Tool output...",
        output_files=["graph.html", "graph.json"],
        total_size=1024567
    )
    db.add(result)
```

### Query примеры

```python
with get_db_context() as db:
    # Найти все задачи пользователя
    user_jobs = db.query(Job).filter(
        Job.user_id == user.id
    ).all()

    # Найти failed jobs
    failed = db.query(Job).filter(
        Job.status == JobStatus.FAILED
    ).order_by(Job.created_at.desc()).limit(10).all()

    # Статистика по инструменту
    stats = db.query(Job).filter(
        Job.tool_name == "build_graph"
    ).count()

    # Join с results
    jobs_with_results = db.query(Job).join(JobResult).filter(
        Job.status == JobStatus.COMPLETED
    ).all()
```

---

## 🔌 Интеграция с FastAPI

### В server.py

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Job, JobStatus

app = FastAPI()

@app.post("/api/run")
async def run_tool(
    request: ToolRunRequest,
    db: Session = Depends(get_db)
):
    # Создать job в БД
    job = Job(
        tool_name=request.tool_name,
        parameters=request.parameters,
        status=JobStatus.PENDING
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Запустить асинхронно
    await runner.run_tool_async(job.id, ...)

    return {"job_id": str(job.id)}


@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "progress": calculate_progress(job),
        ...
    }
```

---

## 🐳 Docker команды

```bash
# Запустить
docker-compose -f docker-compose.phase5.yml up -d

# Остановить
docker-compose -f docker-compose.phase5.yml down

# Остановить + удалить volumes (⚠️ потеря данных!)
docker-compose -f docker-compose.phase5.yml down -v

# Посмотреть логи
docker-compose -f docker-compose.phase5.yml logs -f postgres
docker-compose -f docker-compose.phase5.yml logs -f redis

# Зайти в контейнер
docker exec -it data20_postgres psql -U data20 -d data20_kb

# Backup БД
docker exec data20_postgres pg_dump -U data20 data20_kb > backup.sql

# Restore БД
cat backup.sql | docker exec -i data20_postgres psql -U data20 data20_kb
```

---

## 📦 Environment Variables

Создайте `.env` файл:

```bash
# Database
DATABASE_URL=postgresql://data20:data20@localhost:5432/data20_kb

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Development
DEBUG=true
LOG_LEVEL=info
```

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest backend/tests/

# With coverage
pytest --cov=backend backend/tests/
```

---

## 📝 Следующие шаги

После Phase 5.1 (Database):

1. **Phase 5.2: Authentication**
   - JWT tokens
   - User registration/login
   - Permissions

2. **Phase 5.3: Monitoring**
   - Structured logging
   - Prometheus metrics
   - Grafana dashboards

3. **Phase 5.4: UX Improvements**
   - History viewer
   - Result management
   - Templates

---

## ⚠️ Troubleshooting

### PostgreSQL не запускается

```bash
# Проверить логи
docker-compose -f docker-compose.phase5.yml logs postgres

# Проверить порт
lsof -i :5432

# Удалить volume и пересоздать
docker-compose -f docker-compose.phase5.yml down -v
docker-compose -f docker-compose.phase5.yml up -d postgres
```

### Alembic ошибки

```bash
# Проверить current revision
alembic current

# Посмотреть history
alembic history

# Downgrade и upgrade заново
alembic downgrade base
alembic upgrade head
```

### Connection pool errors

```python
# В database.py увеличить pool size
engine = create_engine(
    url,
    pool_size=10,  # было 5
    max_overflow=20  # было 10
)
```

---

## 📚 Resources

- **SQLAlchemy docs**: https://docs.sqlalchemy.org/
- **Alembic docs**: https://alembic.sqlalchemy.org/
- **PostgreSQL docs**: https://www.postgresql.org/docs/
- **Redis docs**: https://redis.io/docs/

---

## ✅ Checklist Phase 5.1

- [x] Models created (`backend/models.py`)
- [x] Database connection (`backend/database.py`)
- [x] Alembic setup (`backend/alembic/`)
- [x] Docker compose (`docker-compose.phase5.yml`)
- [x] Requirements updated
- [ ] Backend integration (Phase 5.1.7)
- [ ] Celery integration (Phase 5.1.9)
- [ ] Testing (Phase 5.5)

**Status**: ✅ 60% complete (infrastructure ready)
