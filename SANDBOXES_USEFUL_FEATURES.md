# 🧪 Полезные вещи в песочницах mobile-app-sandboxes

**Дата:** 2026-01-08
**Анализ:** Детальное исследование всех 4 песочниц

---

## 📊 Краткая сводка

| Песочница | Размер | Главная ценность | Статус |
|-----------|--------|------------------|--------|
| **hybrid-best-of-both** | 2.3 MB | 🌟 **ВСЁ в одном!** 22 функции | ✅ Готова |
| **current-324dd58** | 2.2 MB | 📦 Модульная архитектура + 57 tools | ✅ Готова |
| **original-ca458ea** | 215 KB | 🔄 Async функции (run_server_async) | ✅ Референс |
| **build-experiments** | 16 KB | 🧪 Для экспериментов | ⏳ Ждёт |

---

## 🌟 1. HYBRID-BEST-OF-BOTH - ГЛАВНАЯ ЖЕМЧУЖИНА! ⭐⭐⭐

### Что это?
**Гибрид** объединяет ВСЁ лучшее из обеих версий (ca458ea + 324dd58) + 11 новых улучшений.

### 💎 Уникальные возможности:

#### 1.1. Восстановленные async функции (из ca458ea)

```python
def run_server_async(host: str = "127.0.0.1", port: int = 8001):
    """Запуск сервера в фоновом потоке БЕЗ блокировки"""

def stop_server():
    """Корректная остановка с graceful shutdown"""

def initialize_database():
    """Инициализация БД (fallback)"""

def create_mobile_app():
    """Создание FastAPI app (fallback)"""
```

**Зачем нужно:**
- ✅ **run_server_async()** - позволяет запустить backend из MainActivity.kt БЕЗ корутин
- ✅ **stop_server()** - корректно останавливает сервер и освобождает ресурсы
- ✅ Простой native код, меньше boilerplate

**Использование:**
```kotlin
// ПРОСТО! Без корутин!
python!!.getModule("backend_main")
    .callAttr("run_server_async", "127.0.0.1", 8001)

// Остановка
python!!.getModule("backend_main").callAttr("stop_server")
```

---

#### 1.2. Новые health check функции 🆕

```python
def get_server_status() -> dict:
    """Получить статус сервера (running, thread_alive, paths)"""

def wait_for_server_ready(timeout: float = 10.0) -> bool:
    """Дождаться когда сервер готов принимать запросы"""
```

**Зачем нужно:**
- ✅ Мониторинг состояния backend в UI
- ✅ Синхронизация запуска (дождаться готовности перед API calls)
- ✅ Debugging и диагностика

**Использование:**
```kotlin
// Проверить статус
val status = python!!.getModule("backend_main")
    .callAttr("get_server_status")
    .toJava(Map::class.java) as Map<String, Any>

val isRunning = status["running"] as Boolean
statusText.text = if (isRunning) "✅ Running" else "❌ Stopped"

// Дождаться готовности
python!!.getModule("backend_main")
    .callAttr("run_server_async", "127.0.0.1", 8001)

val ready = python!!.getModule("backend_main")
    .callAttr("wait_for_server_ready", 10.0)
    .toBoolean()

if (ready) {
    // Сервер готов, можно делать API запросы
}
```

---

#### 1.3. Graceful Shutdown с таймаутами 🆕

**Что улучшено:**
```python
# Ожидание остановки сервера (до 5 секунд)
wait_time = 0
while server.should_exit and wait_time < 5:
    time.sleep(0.1)
    wait_time += 0.1

# Очистка потока (до 3 секунд)
server_thread.join(timeout=3.0)

if server_thread.is_alive():
    logger.warning("Thread still alive after timeout")
```

**Зачем нужно:**
- ✅ Корректное завершение всех операций
- ✅ Освобождение ресурсов (файлы, сокеты, БД)
- ✅ Избежание зависаний при закрытии app

---

#### 1.4. Enhanced Logging - Улучшенное логирование 🆕

**Формат:**
```python
[2026-01-08 12:30:45] [INFO] [backend_main] ==============================
[2026-01-08 12:30:45] [INFO] [backend_main] ✅ Environment configured
[2026-01-08 12:30:45] [INFO] [backend_main] ==============================
[2026-01-08 12:30:45] [INFO] [backend_main]    Database: /data/data20.db
[2026-01-08 12:30:45] [INFO] [backend_main]    Uploads:  /data/uploads
```

**Зачем нужно:**
- ✅ Легко читать логи
- ✅ Быстро находить проблемы
- ✅ Визуальное разделение секций

---

#### 1.5. Debug Mode - Режим отладки 🆕

```python
def setup_environment(db_path: str, upload_dir: str, logs_dir: str, debug: bool = False):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Debug mode enabled")
    os.environ['DEBUG'] = 'true' if debug else 'false'
```

**Использование:**
```kotlin
// Production
python!!.getModule("backend_main")
    .callAttr("setup_environment", dbPath, uploadPath, logsPath, false)

// Development
python!!.getModule("backend_main")
    .callAttr("setup_environment", dbPath, uploadPath, logsPath, true)
```

---

#### 1.6. CLI Testing Interface - Тестирование из командной строки 🆕

```bash
# Блокирующий режим
python3 backend_main.py

# Async режим
python3 backend_main.py --async

# С debug
python3 backend_main.py --debug

# Другой порт
python3 backend_main.py --port 9000

# Всё вместе
python3 backend_main.py --async --debug --port 9000
```

**Зачем нужно:**
- ✅ Тестирование backend БЕЗ Android emulator
- ✅ Быстрая проверка изменений
- ✅ Debugging на desktop

---

#### 1.7. Signal Handlers - Обработка сигналов 🆕

```python
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, graceful shutdown...")
    stop_server()

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

**Зачем нужно:**
- ✅ Корректное завершение при Ctrl+C
- ✅ Корректное завершение при kill команде
- ✅ Корректное завершение при app shutdown

---

#### 1.8. Backwards Compatibility - Обратная совместимость 🆕

```python
# NEW naming (from 324dd58)
os.environ['DATA20_DATABASE_PATH'] = db_path
os.environ['DATA20_UPLOAD_PATH'] = upload_dir

# OLD naming (from ca458ea) - compatibility
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
os.environ['UPLOAD_DIR'] = upload_dir
```

**Зачем нужно:**
- ✅ Работает с ЛЮБЫМ кодом (старым или новым)
- ✅ Не ломает существующие интеграции
- ✅ Плавная миграция

---

### 📦 Что ещё есть в hybrid:

- ✅ **6 модулей**: mobile_server.py, mobile_auth.py, mobile_database.py, mobile_models.py, mobile_tool_registry.py, mobile_tool_runner.py
- ✅ **57 инструментов** в tools/ (все offline tools)
- ✅ **Thread naming** для отладки
- ✅ **shutdown_event** для координации потоков
- ✅ **Детальный error handling** с traceback

### 📊 Полное сравнение функций:

| Функция | ca458ea | 324dd58 | hybrid |
|---------|---------|---------|--------|
| run_server() | ✅ | ✅ | ✅ |
| run_server_async() | ✅ | ❌ | ✅ |
| stop_server() | ✅ Basic | ❌ | ✅ Enhanced |
| get_server_status() | ❌ | ❌ | ✅ NEW |
| wait_for_server_ready() | ❌ | ❌ | ✅ NEW |
| Модули | ❌ | ✅ 6 | ✅ 6 |
| 57 tools | ❌ | ✅ | ✅ |
| Graceful shutdown | Basic | ❌ | ✅ Enhanced |
| Debug mode | Basic | ❌ | ✅ Enhanced |
| CLI testing | Basic | ❌ | ✅ Full |

**Итого:** 22 функции/улучшения = МАКСИМУМ!

---

## 📦 2. CURRENT-324DD58 - Модульная архитектура

### Что это?
Текущая версия Phase 7.3 с модульной архитектурой и всеми инструментами.

### 💎 Уникальные возможности:

#### 2.1. Модульная архитектура (6 модулей)

```
mobile_server.py       (427 строк) - FastAPI app, endpoints
mobile_auth.py         (157 строк) - JWT authentication
mobile_database.py     (81 строк)  - SQLite, init DB
mobile_models.py       (351 строк) - Pydantic models
mobile_tool_registry.py (489 строк) - Registry of 57 tools
mobile_tool_runner.py  (311 строк) - Tool execution
```

**Преимущества:**
- ✅ Четкое разделение ответственности
- ✅ Легко тестировать каждый модуль отдельно
- ✅ Легко поддерживать и расширять
- ✅ Можно переиспользовать модули

**Использование:**
```python
# Импорт в backend_main.py
from mobile_server import app as mobile_app
from mobile_database import init_mobile_database
from mobile_auth import create_access_token
from mobile_tool_runner import execute_tool
```

---

#### 2.2. Tool Registry - Реестр инструментов

**Файл:** `mobile_tool_registry.py`

**Что делает:**
- 📋 Регистрирует все 57 инструментов
- 🔍 Позволяет искать инструменты по имени
- 📝 Хранит метаданные (описание, параметры)
- ✅ Валидация перед выполнением

**Пример:**
```python
from mobile_tool_registry import TOOL_REGISTRY, get_tool

# Получить инструмент
tool = get_tool("graph_visualizer")
print(tool["name"])          # "graph_visualizer"
print(tool["description"])   # "Create knowledge graph visualization"
print(tool["parameters"])    # ["input_file", "output_format"]

# Выполнить
from mobile_tool_runner import execute_tool
result = execute_tool("graph_visualizer", {"input_file": "data.json"})
```

---

#### 2.3. JWT Authentication - Аутентификация

**Файл:** `mobile_auth.py`

**Возможности:**
- 🔐 Создание JWT tokens
- ✅ Валидация tokens
- 👤 User management
- 🔒 Password hashing (bcrypt)

**API endpoints:**
```
POST /auth/login     - Вход (возвращает access token)
POST /auth/register  - Регистрация
POST /auth/refresh   - Обновление token
GET  /auth/me        - Текущий пользователь
```

---

#### 2.4. SQLite Database - База данных

**Файл:** `mobile_database.py`

**Что делает:**
- 📊 Создает таблицы (users, jobs, tool_executions)
- 🔧 Создает индексы для быстрого поиска
- 👤 Создает default admin user
- 🔄 Migration support

**Таблицы:**
```sql
users            - Пользователи
jobs             - История выполнения задач
tool_executions  - Логи выполнения инструментов
```

---

#### 2.5. Все 57 offline инструментов

**Категории:**
- 📊 Графы и визуализация (12 tools)
- 📝 Обработка текста (15 tools)
- 🔍 Поиск и анализ (10 tools)
- 📁 Работа с файлами (8 tools)
- 🔗 Связи и ссылки (6 tools)
- 📚 Таксономия и классификация (6 tools)

**Примеры:**
```
graph_visualizer.py      - Визуализация графов
knowledge_graph_builder.py - Построение графа знаний
text_analyzer.py         - Анализ текста
pdf_converter.py         - Конвертация PDF
markdown_processor.py    - Обработка Markdown
cross_references.py      - Кросс-ссылки
build_taxonomy.py        - Построение таксономии
```

---

### 📝 Когда использовать current-324dd58:

✅ **Используйте если:**
- Нужна модульная архитектура
- Важна поддерживаемость кода
- Нужны все 57 инструментов
- Не критична async функциональность

❌ **НЕ используйте если:**
- Нужен run_server_async()
- Нужен stop_server()
- Нужны health checks

**Рекомендация:** Используйте **hybrid-best-of-both** вместо этого!

---

## 🔄 3. ORIGINAL-CA458EA - Async функции

### Что это?
Оригинальная версия Phase 7.3 с async функциями.

### 💎 Уникальные возможности:

#### 3.1. run_server_async() - Асинхронный запуск

```python
def run_server_async(host: str = "127.0.0.1", port: int = 8001):
    """
    Run FastAPI server in background thread
    NON-BLOCKING mode - returns immediately
    """
    global server, server_thread

    def run_in_thread():
        import uvicorn
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        server.run()

    server_thread = threading.Thread(target=run_in_thread, daemon=True)
    server_thread.start()
    logger.info(f"✅ Server started in background on {host}:{port}")
```

**Зачем нужно:**
- ✅ Не блокирует main thread
- ✅ Простой вызов из native кода
- ✅ Сервер работает в фоне

---

#### 3.2. stop_server() - Остановка сервера

```python
def stop_server():
    """Stop the running FastAPI server"""
    global server, server_thread

    if server is not None:
        logger.info("🛑 Stopping server...")
        server.should_exit = True

        # Wait for server to stop
        import time
        time.sleep(1)

        server = None
        logger.info("✅ Server stopped")
```

**Зачем нужно:**
- ✅ Корректное завершение при закрытии app
- ✅ Освобождение ресурсов
- ✅ Предотвращение утечек памяти

---

#### 3.3. Environment Variables для mobile

```python
# Mobile-specific settings
os.environ['DEBUG'] = 'true' if debug else 'false'
os.environ['CORS_ORIGINS'] = '*'  # Allow all on mobile

# Disable features not needed on mobile
os.environ['ENABLE_CELERY'] = 'false'
os.environ['ENABLE_REDIS'] = 'false'
os.environ['ENABLE_METRICS'] = 'false'
```

**Зачем нужно:**
- ✅ CORS разрешён для localhost (mobile app)
- ✅ Celery отключен (не нужен на mobile)
- ✅ Redis отключен (не нужен на mobile)
- ✅ Metrics отключены (экономия ресурсов)

---

### 📝 Когда использовать original-ca458ea:

✅ **Используйте если:**
- Изучаете как работает run_server_async()
- Нужен референс для восстановления функций
- Минимальный backend без модулей

❌ **НЕ используйте если:**
- Нужна модульная архитектура
- Нужны 57 инструментов
- Готовите production версию

**Рекомендация:** Используйте как **референс**, код копируйте в hybrid!

---

## 🧪 4. BUILD-EXPERIMENTS - Экспериментальная зона

### Что это?
Директория для экспериментов со сборкой и оптимизациями.

### 💡 Запланированные эксперименты:

#### Experiment 1: Минимальные зависимости
```
Цель: Уменьшить размер APK
План:
- Убрать pandas, numpy
- Оставить только FastAPI, uvicorn, SQLAlchemy
- Попробовать собрать

Ожидаемый размер: ~40-50 MB (вместо 95 MB)
```

#### Experiment 2: Chaquopy оптимизация
```
Цель: Оптимизировать настройки Chaquopy
План:
- Изменить buildPython настройки
- Включить strip mode
- Попробовать собрать

Ожидаемый размер: ~80 MB
```

#### Experiment 3: Только основные tools
```
Цель: Lite версия (как v3-lite)
План:
- Оставить только 12 инструментов
- Минимальные зависимости

Ожидаемый размер: ~45 MB
```

---

### 📝 Как создать новый эксперимент:

```bash
# Создать директорию
mkdir mobile-app-sandboxes/build-experiments/experiment-4-my-test

# Скопировать базу
cp -r mobile-app-sandboxes/hybrid-best-of-both/* \
      mobile-app-sandboxes/build-experiments/experiment-4-my-test/

# Внести изменения
cd mobile-app-sandboxes/build-experiments/experiment-4-my-test
# ... ваши изменения ...

# Попробовать собрать
flutter build apk --release

# Документировать результат
echo "## Результат
Что получилось / не получилось
" > README.md
```

---

## 🎯 РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ

### Для production сборки:
✅ **Используйте: hybrid-best-of-both**
- Все функции БЕЗ потерь
- 22 функции (максимум)
- Готова к сборке APK

### Для изучения модульной архитектуры:
✅ **Используйте: current-324dd58**
- Чистая модульная структура
- 6 модулей + 57 tools
- Хорошая документация

### Для изучения async функций:
✅ **Используйте: original-ca458ea**
- Простой run_server_async()
- Простой stop_server()
- Минимальный код

### Для экспериментов:
✅ **Используйте: build-experiments**
- Безопасная зона для тестов
- Не трогает production код
- Можно ломать и пересоздавать

---

## 📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА

| Критерий | hybrid | current | original | experiments |
|----------|--------|---------|----------|-------------|
| **Функциональность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⚙️ |
| **Готовность к сборке** | ✅ 100% | ✅ 100% | ❌ 30% | ⏳ TBD |
| **Модули** | ✅ 6 | ✅ 6 | ❌ 0 | - |
| **Инструменты** | ✅ 57 | ✅ 57 | ❌ 0 | - |
| **Async функции** | ✅ | ❌ | ✅ | - |
| **Health checks** | ✅ | ❌ | ❌ | - |
| **Debug mode** | ✅ Enhanced | ❌ | ✅ Basic | - |
| **Graceful shutdown** | ✅ Enhanced | ❌ | ✅ Basic | - |
| **CLI testing** | ✅ | ❌ | ✅ Basic | - |
| **Размер на диске** | 2.3 MB | 2.2 MB | 215 KB | 16 KB |
| **Документация** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 💡 КАК ИСПОЛЬЗОВАТЬ ПОЛЕЗНЫЕ ВЕЩИ

### Сценарий 1: Взять async функции для v5-full

```bash
# Скопировать из hybrid в v5-full
cp mobile-app-sandboxes/hybrid-best-of-both/android/app/src/main/python/backend_main.py \
   mobile-app-versions/v5-full/android/app/src/main/python/

# Теперь v5-full тоже имеет все 22 функции!
```

### Сценарий 2: Использовать модули отдельно

```bash
# Скопировать только mobile_auth.py
cp mobile-app-sandboxes/current-324dd58/android/app/src/main/python/mobile_auth.py \
   your-project/backend/

# Использовать в своём проекте
from mobile_auth import create_access_token, verify_token
```

### Сценарий 3: Тестировать backend на desktop

```bash
cd mobile-app-sandboxes/hybrid-best-of-both/android/app/src/main/python

# Запустить с debug
python3 backend_main.py --debug --async

# Открыть в браузере
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/docs  # Swagger UI
```

---

## 🎯 ИТОГИ

### Самое полезное:

1. **🌟 hybrid-best-of-both** - ИСПОЛЬЗУЙТЕ ЭТО!
   - 22 функции
   - Готова к production
   - Максимальная функциональность

2. **📦 current-324dd58** - Для изучения архитектуры
   - Модульная структура
   - 57 инструментов
   - Хорошо документирована

3. **🔄 original-ca458ea** - Для референса
   - Async функции
   - Простой код
   - Минимализм

4. **🧪 build-experiments** - Для экспериментов
   - Безопасная зона
   - Можно ломать
   - Не влияет на production

### Рекомендация:

✅ **Для следующей сборки используйте hybrid-best-of-both!**
- Она содержит ВСЁ лучшее из всех версий
- Готова к сборке APK
- Максимальная функциональность
- Отличная документация

---

**Создано:** 2026-01-08
**Анализ:** Детальное исследование всех 4 песочниц
**Вывод:** hybrid-best-of-both = ЗОЛОТОЙ СТАНДАРТ 🏆
