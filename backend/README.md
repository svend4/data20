# 🚀 Data20 Backend API

**Phase 4: Full Backend Integration** - FastAPI сервер для запуска всех 57 инструментов через UI

---

## 📋 Возможности

### ✅ Автоматическое обнаружение инструментов
- Сканирование `tools/` директории
- Извлечение параметров из argparse
- Категоризация инструментов
- Генерация метаданных

### ✅ REST API
- **GET `/api/tools`** - Список всех инструментов
- **GET `/api/tools/{name}`** - Информация об инструменте
- **GET `/api/categories`** - Категории инструментов
- **POST `/api/run`** - Запустить инструмент
- **GET `/api/jobs`** - Список задач
- **GET `/api/jobs/{id}`** - Статус задачи
- **DELETE `/api/jobs/{id}`** - Отменить задачу
- **GET `/api/stats`** - Статистика системы

### ✅ WebSocket Support
- Real-time обновления прогресса
- Live статус выполнения
- Уведомления о завершении

### ✅ Background Tasks
- Асинхронное выполнение
- Очередь задач
- Отмена выполнения
- Логи output/error

---

## 🛠️ Установка

### 1. Установить зависимости

```bash
cd backend
pip install -r requirements.txt
```

### 2. Запустить сервер

```bash
# Из корня проекта
cd backend
python server.py

# Или с uvicorn напрямую
uvicorn server:app --reload --port 8001
```

Сервер запустится на http://localhost:8001

---

## 📚 API Документация

FastAPI автоматически генерирует интерактивную документацию:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI Schema**: http://localhost:8001/openapi.json

---

## 🔧 Компоненты

### 1. `server.py` - FastAPI сервер (350 строк)

Основной API сервер с endpoints:

```python
from fastapi import FastAPI
app = FastAPI(title="Data20 Knowledge Base API")

@app.post("/api/run")
async def run_tool(request: ToolRunRequest):
    """Запустить инструмент"""
    return await runner.run_tool(
        request.tool_name,
        request.parameters
    )
```

**Features**:
- CORS middleware для фронтенда
- Background tasks для длительных операций
- WebSocket endpoint для real-time updates
- Static files serving (опционально)

### 2. `tool_registry.py` - Реестр инструментов (550 строк)

Автоматическое обнаружение и каталогизация инструментов:

```python
registry = ToolRegistry()
registry.scan_tools()  # Находит все .py файлы в tools/

tool = registry.get_tool("build_graph")
# ToolMetadata(
#     name="build_graph",
#     display_name="Build Graph",
#     category=ToolCategory.GRAPH,
#     parameters=[...],
#     output_files=["build_graph.html", "build_graph.json"]
# )
```

**Features**:
- AST parsing для извлечения параметров
- Автоматическая категоризация
- Определение выходных файлов
- UI hints (иконки, цвета)

### 3. `tool_runner.py` - Исполнитель инструментов (300 строк)

Асинхронное выполнение Python инструментов:

```python
runner = ToolRunner()

job = await runner.run_tool(
    "build_graph",
    parameters={"depth": 3},
    progress_callback=lambda p, m: print(f"{p}% - {m}")
)

print(job.status)  # JobStatus.COMPLETED
print(job.output_files)  # ["build_graph.html", ...]
```

**Features**:
- Async subprocess execution
- Progress tracking
- Output capture (stdout/stderr)
- Job cancellation
- Output file detection

---

## 📦 Модели данных

### ToolMetadata

```python
@dataclass
class ToolMetadata:
    name: str
    display_name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    output_files: List[str]
    output_formats: List[str]
    icon: str
    color: str
    complexity: str  # low, medium, high
    estimated_time: int  # seconds
```

### ToolParameter

```python
@dataclass
class ToolParameter:
    name: str
    type: str  # str, int, bool, etc.
    required: bool
    default: Any
    description: str
    choices: Optional[List[Any]]
```

### JobResult

```python
@dataclass
class JobResult:
    job_id: str
    tool_name: str
    status: JobStatus
    output: str
    error: str
    return_code: int
    started_at: datetime
    completed_at: datetime
    duration: float
    output_files: list
    progress: int
```

---

## 🔌 WebSocket Protocol

### Client → Server

**Subscribe to job updates:**
```json
{
    "action": "subscribe",
    "job_id": "uuid-here"
}
```

**Ping:**
```json
{
    "action": "ping"
}
```

### Server → Client

**Progress update:**
```json
{
    "type": "progress",
    "job_id": "uuid-here",
    "tool_name": "build_graph",
    "status": "running",
    "progress": 50,
    "message": "Processing..."
}
```

**Completion:**
```json
{
    "type": "complete",
    "job_id": "uuid-here",
    "status": "completed",
    "output_files": ["build_graph.html", "build_graph.json"],
    "duration": 15.3,
    "error": null
}
```

---

## 🎯 Примеры использования

### Запустить инструмент

```bash
curl -X POST http://localhost:8001/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "build_graph",
    "parameters": {
      "depth": 3,
      "output": "graph.html"
    }
  }'
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "tool_name": "build_graph",
    "status": "pending",
    "message": "Tool build_graph started"
}
```

### Проверить статус

```bash
curl http://localhost:8001/api/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "tool_name": "build_graph",
    "status": "completed",
    "progress": 100,
    "started_at": "2026-01-03T14:30:00",
    "completed_at": "2026-01-03T14:30:15",
    "duration": 15.3,
    "output_files": ["build_graph.html", "build_graph.json"]
}
```

### Получить все инструменты

```bash
curl http://localhost:8001/api/tools
```

**Response:**
```json
{
    "total_tools": 57,
    "categories": {
        "graph": 8,
        "visualization": 12,
        "analysis": 15,
        ...
    },
    "tools": {
        "build_graph": {
            "name": "build_graph",
            "display_name": "Build Graph",
            "description": "Build knowledge graph from files",
            "category": "graph",
            "parameters": [...],
            "icon": "🕸️",
            "color": "#e74c3c",
            "complexity": "medium",
            "estimated_time": 30
        },
        ...
    }
}
```

---

## ⚙️ Конфигурация

### Environment Variables

```bash
# Server
HOST=0.0.0.0
PORT=8001

# Paths
TOOLS_DIR=../tools
OUTPUT_DIR=..

# Jobs
MAX_CONCURRENT_JOBS=5
JOB_RETENTION_HOURS=24

# CORS
CORS_ORIGINS=["http://localhost:8000", "http://localhost:3000"]
```

### Настройка в коде

```python
# server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Изменить в production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# tool_runner.py
runner = ToolRunner(
    tools_dir=Path("tools"),
    output_dir=Path(".")
)
```

---

## 🧪 Тестирование

### Запустить Tool Registry

```bash
python tool_registry.py
```

**Output:**
```
🔍 Сканирование tools/...
  ✓ build_graph (graph)
  ✓ calculate_pagerank (analysis)
  ...

✅ Найдено 57 инструментов

📊 Статистика по категориям:
graph                  8 инструментов
visualization         12 инструментов
analysis              15 инструментов
...

✅ Реестр экспортирован в tool_registry.json
```

### Тестировать Tool Runner

```bash
python tool_runner.py
```

**Output:**
```
🚀 Запуск инструмента build_graph...
[10%] Starting tool...
[30%] Tool running...
[100%] Completed successfully!

✅ Статус: JobStatus.COMPLETED
⏱️  Время: 15.30s
📁 Выходные файлы: build_graph.html, build_graph.json
```

---

## 📊 Статистика

### Код

| Компонент | Строк | Назначение |
|-----------|-------|------------|
| server.py | 350 | FastAPI сервер + WebSocket |
| tool_registry.py | 550 | Обнаружение и каталогизация |
| tool_runner.py | 300 | Выполнение инструментов |
| **Всего** | **1,200** | Backend код |

### API Endpoints

- **8 REST endpoints** для управления инструментами и задачами
- **1 WebSocket endpoint** для real-time обновлений
- **Auto-generated docs** через FastAPI

### Поддерживаемые операции

- ✅ Запуск любого из 57 инструментов
- ✅ Настройка параметров
- ✅ Отслеживание прогресса
- ✅ Отмена выполнения
- ✅ Просмотр результатов
- ✅ История задач

---

## 🔄 Интеграция с Frontend

Frontend (PWA) автоматически определяет доступность backend:

```javascript
// api-client.js
const apiClient = new APIClient('http://localhost:8001');

// Проверить доступность
const available = await apiClient.checkAvailability();

if (available) {
    // API Mode: Показать кнопку "Run Tools"
    toolRunnerUI.showToolRunner();
} else {
    // Static Mode: Только просмотр
    toolRunnerUI.showStaticMode();
}
```

---

## 🚀 Production Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY tools/ ./tools/

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

```yaml
services:
  backend:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./tools:/app/tools
      - ./output:/app/output
    environment:
      - CORS_ORIGINS=https://your-domain.com
```

### Systemd Service

```ini
[Unit]
Description=Data20 Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/data20
ExecStart=/usr/bin/uvicorn backend.server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверить зависимости
pip list | grep fastapi

# Проверить порт
lsof -i :8001

# Запустить с debug
uvicorn backend.server:app --reload --log-level debug
```

### Frontend не видит backend

```bash
# Проверить CORS настройки
curl -H "Origin: http://localhost:8000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8001/api/tools
```

### Инструмент не запускается

```bash
# Проверить tool registry
python backend/tool_registry.py | grep your_tool

# Запустить инструмент вручную
python tools/your_tool.py --help
```

---

## 📝 TODO

### v4.1 (Future Enhancements)

- [ ] Celery integration для distributed tasks
- [ ] Redis для job queue
- [ ] PostgreSQL для job history
- [ ] Rate limiting
- [ ] Authentication & Authorization
- [ ] File upload для custom data
- [ ] Scheduled jobs (cron-like)
- [ ] Email notifications
- [ ] Prometheus metrics

---

## 🤝 Contributing

Backend разработан как часть Phase 4. См. основной README для деталей.

**Архитектура**:
- FastAPI для REST API
- asyncio для async execution
- WebSocket для real-time
- Pydantic для validation

**Code style**:
- Type hints everywhere
- Docstrings для всех функций
- PEP 8 compliance

---

## 📄 License

Часть проекта Data20 Knowledge Base
