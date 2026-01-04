# Архитектура и Deployment: Полное Руководство

## 📋 Оглавление

1. [Где находится Backend](#где-находится-backend)
2. [Текущая Архитектура](#текущая-архитектура)
3. [Deployment Сценарии](#deployment-сценарии)
4. [Прогрессия Уровней (От Простого к Сложному)](#прогрессия-уровней)
5. [План Развития Offline Mode](#план-развития-offline-mode)
6. [Технологические Альтернативы](#технологические-альтернативы)

---

# Где находится Backend?

## 🎯 Критически важно понять:

**Backend - это универсальный FastAPI сервер**, который может работать в разных режимах и находиться в разных местах в зависимости от платформы и сценария использования.

### 📱 Mobile App (Flutter)

```
┌─────────────────────────────────────┐
│   Смартфон пользователя             │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  Flutter App                │   │
│   │  (Dart код)                 │   │
│   └─────────────┬───────────────┘   │
│                 │ HTTP/HTTPS        │
│                 │ API requests      │
└─────────────────┼───────────────────┘
                  │
                  │ Internet / Local Network
                  │
                  ▼
┌─────────────────────────────────────┐
│   Сервер (Ваш/Облачный/Локальный)  │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  Backend (FastAPI)          │   │
│   │  • REST API endpoints       │   │
│   │  • JWT authentication       │   │
│   │  • PostgreSQL/SQLite        │   │
│   │  • Tool execution           │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Варианты расположения Backend:**

#### 1. **Production: Облачный сервер** 🌐
```
Mobile App → https://api.yourdomain.com → Cloud Server (AWS/GCP/Azure)
                                           └─ Backend + PostgreSQL + Redis
```

#### 2. **Development: Локальный сервер** 💻
```
Mobile App → http://192.168.1.100:8001 → Ваш компьютер в локальной сети
                                         └─ Backend + PostgreSQL + Redis
```

#### 3. **Embedded: Backend на телефоне** 📱 (Будущее развитие)
```
Mobile App → http://127.0.0.1:8001 → Backend процесс на этом же телефоне
                                     └─ SQLite + in-memory cache
```
**Технология**: Chaquopy (Python в Android) / PythonKit (iOS)

---

### 🖥️ Desktop App (Electron)

```
┌─────────────────────────────────────────────┐
│   Компьютер пользователя                    │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │  Electron App                       │   │
│   │                                     │   │
│   │  ┌──────────────────────────────┐   │   │
│   │  │ React (Renderer Process)     │   │   │
│   │  │ • UI Components              │   │   │
│   │  └────────┬─────────────────────┘   │   │
│   │           │ HTTP                    │   │
│   │           │ API requests            │   │
│   │  ┌────────▼─────────────────────┐   │   │
│   │  │ Main Process (Node.js)       │   │   │
│   │  │ • Window management          │   │   │
│   │  │ • Local backend launcher?    │   │   │
│   │  └──────────────────────────────┘   │   │
│   └─────────────────────────────────────┘   │
│                 │                           │
└─────────────────┼───────────────────────────┘
                  │
                  ▼
      Backend (External или Embedded)
```

**Варианты расположения Backend:**

#### 1. **External Server** 🌐 (Текущий режим)
```
Electron App → http://localhost:8001 → Backend (запущен отдельно)
                                       └─ python backend/server.py
```

#### 2. **Embedded Backend** 📦 (Будущее развитие)
```
Electron App запускает Backend автоматически:

┌─────────────────────────────────────┐
│  Electron Main Process              │
│  1. app.on('ready', () => {         │
│  2.   spawnBackend()  // Python!    │
│  3.   createWindow()                │
│  })                                 │
└─────────────────────────────────────┘
         │
         ├─→ Child Process: python backend/server.py
         │                  (Embedded в приложение)
         │
         └─→ React UI → http://localhost:8001
```

**Технологии**:
- **PyInstaller** - упаковать backend в executable
- **child_process.spawn()** - запустить из Electron
- **Portable**: Всё приложение = 1 установщик (React + Node + Python + SQLite)

---

### 🌐 Web App (React/HTML)

```
┌─────────────────────────────────────┐
│   Браузер пользователя              │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  React App / HTML           │   │
│   │  • JavaScript код           │   │
│   │  • DOM manipulation         │   │
│   └─────────────┬───────────────┘   │
│                 │ HTTP/HTTPS        │
│                 │ fetch() / axios   │
└─────────────────┼───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   Web Server                        │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  Nginx/Apache               │   │
│   │  • Serve static files       │   │
│   │  • Reverse proxy            │   │
│   └─────────────┬───────────────┘   │
│                 │                   │
│   ┌─────────────▼───────────────┐   │
│   │  Backend (FastAPI)          │   │
│   │  • API endpoints            │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Варианты расположения:**

#### 1. **Classic SPA** 🌐
```
Browser → https://yoursite.com/        → Nginx (static React build)
          https://yoursite.com/api/... → FastAPI Backend
```

#### 2. **Localhost Development** 💻
```
Browser → http://localhost:3000  → Vite Dev Server (React)
                                   └─ proxy /api → http://localhost:8001
          http://localhost:8001  → FastAPI Backend
```

---

# Текущая Архитектура

## 🏗️ Компоненты системы

### Backend (FastAPI Server)

**Местоположение**: `/backend/server.py`

```python
# Главный FastAPI application
app = FastAPI(title="Data20 Knowledge Base API")

# Основные компоненты:
├─ REST API Endpoints
│  ├─ /api/tools - список инструментов
│  ├─ /api/run - запуск инструмента
│  ├─ /api/jobs - список задач
│  └─ /api/jobs/{id} - статус задачи
│
├─ Authentication
│  ├─ /auth/register - регистрация
│  ├─ /auth/login - вход (JWT tokens)
│  ├─ /auth/refresh - обновление токена
│  └─ /auth/me - текущий пользователь
│
├─ Database Layer
│  ├─ SQLAlchemy ORM
│  ├─ PostgreSQL (production/development)
│  └─ SQLite (standalone)
│
├─ Task Execution
│  ├─ Celery (distributed, production)
│  └─ Direct (local, standalone)
│
├─ Caching
│  ├─ Redis (production/development)
│  └─ In-memory dict (standalone)
│
└─ Monitoring
   ├─ Prometheus metrics (/metrics)
   ├─ Structured logging (structlog)
   └─ Health checks (/health)
```

### Frontend Apps (3 платформы)

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Web (React)          Desktop (Electron)    Mobile      │
│  ┌──────────┐        ┌──────────┐         ┌──────────┐ │
│  │ webapp-  │        │ desktop- │         │ mobile-  │ │
│  │ react/   │        │ app/     │         │ app/     │ │
│  │          │        │          │         │          │ │
│  │ React    │        │ Electron │         │ Flutter  │ │
│  │ Router   │        │ + React  │         │ Dart     │ │
│  │ Context  │        │ IPC      │         │ Provider │ │
│  └────┬─────┘        └────┬─────┘         └────┬─────┘ │
│       │                   │                    │       │
└───────┼───────────────────┼────────────────────┼───────┘
        │                   │                    │
        └───────────────────┴────────────────────┘
                            │
                    REST API (JSON/HTTP)
                            │
┌───────────────────────────▼───────────────────────────┐
│                   BACKEND LAYER                       │
├───────────────────────────────────────────────────────┤
│  FastAPI Server (Python)                              │
│  • Endpoints: /api/*, /auth/*                        │
│  • JWT Authentication                                │
│  • Tool Registry (57+ tools)                         │
│  • Job Management                                    │
└───────────────────────────┬───────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Database    │    │  Cache       │    │  Queue       │
│              │    │              │    │              │
│ PostgreSQL   │    │  Redis       │    │  Celery      │
│ or SQLite    │    │  or Memory   │    │  or Direct   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

# Deployment Сценарии

## 📦 Scenario 1: Web App (SPA) - Production

**Кто**: Корпоративные пользователи, команды

```
┌─────────────────────────────────────────────────┐
│  Cloud Infrastructure (AWS/GCP/Azure)           │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │  Load Balancer                           │   │
│  │  (nginx/ALB)                             │   │
│  └────────────┬─────────────────────────────┘   │
│               │                                 │
│       ┌───────┴────────┐                        │
│       │                │                        │
│  ┌────▼─────┐    ┌────▼─────┐                   │
│  │ Static   │    │ API      │                   │
│  │ Files    │    │ Server   │                   │
│  │ (S3/CDN) │    │ (EC2)    │                   │
│  │          │    │          │                   │
│  │ React    │    │ FastAPI  │                   │
│  │ Build    │    │ +        │                   │
│  │          │    │ Gunicorn │                   │
│  └──────────┘    └────┬─────┘                   │
│                       │                         │
│              ┌────────┴────────┐                │
│              │                 │                │
│         ┌────▼─────┐     ┌────▼─────┐           │
│         │ Postgres │     │  Redis   │           │
│         │ (RDS)    │     │ (Elasti  │           │
│         │          │     │  Cache)  │           │
│         └──────────┘     └──────────┘           │
└─────────────────────────────────────────────────┘
```

**Конфигурация**:
```bash
# Backend
export DEPLOYMENT_MODE=production
export DATABASE_URL=postgresql://user:pass@rds.amazonaws.com/data20
export REDIS_URL=redis://elasticache.amazonaws.com:6379

# Frontend
VITE_API_URL=https://api.yourdomain.com

# Deploy
docker-compose -f docker-compose.production.yml up
```

**Стоимость**: ~$100-500/мес (зависит от нагрузки)

---

## 💻 Scenario 2: Desktop App - Standalone

**Кто**: Индивидуальные пользователи, оффлайн работа

```
┌─────────────────────────────────────────┐
│  User's Computer (Windows/Mac/Linux)    │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Electron Application             │  │
│  │  (Single .exe/.app/.AppImage)     │  │
│  │                                   │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ React UI                    │  │  │
│  │  │ (localhost:3000)            │  │  │
│  │  └──────────┬──────────────────┘  │  │
│  │             │ HTTP                │  │
│  │  ┌──────────▼──────────────────┐  │  │
│  │  │ Embedded Backend            │  │  │
│  │  │ (Python subprocess)         │  │  │
│  │  │ • FastAPI                   │  │  │
│  │  │ • SQLite (./data20.db)      │  │  │
│  │  │ • No Redis, No Celery       │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Как работает**:
```javascript
// desktop-app/electron/main.js

const { spawn } = require('child_process');

let backendProcess;

function startBackend() {
  // Запускаем Python backend как subprocess
  backendProcess = spawn('python', ['backend/server.py'], {
    env: {
      ...process.env,
      DEPLOYMENT_MODE: 'standalone',
      DATABASE_URL: 'sqlite:///./data20.db'
    }
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
}

app.on('ready', () => {
  startBackend();
  setTimeout(createWindow, 2000); // Ждём запуск backend
});

app.on('quit', () => {
  backendProcess.kill();
});
```

**Упаковка**:
```bash
# Собрать backend в executable
pyinstaller --onefile backend/server.py

# Собрать Electron app с embedded backend
electron-builder build --win --mac --linux
```

**Размер**: ~150-200MB (включая Python runtime)
**Стоимость**: Бесплатно (one-time install)

---

## 📱 Scenario 3: Mobile App - Cloud Backend

**Кто**: Мобильные пользователи, синхронизация

```
┌──────────────────┐         ┌──────────────────┐
│  User's Phone    │         │  Cloud Server    │
│                  │         │                  │
│  ┌────────────┐  │  HTTPS  │  ┌────────────┐  │
│  │ Flutter    │  │────────>│  │  FastAPI   │  │
│  │ App        │  │  JSON   │  │  Backend   │  │
│  │            │  │<────────│  │            │  │
│  └────────────┘  │         │  └──────┬─────┘  │
│                  │         │         │        │
│  ┌────────────┐  │         │  ┌──────▼─────┐  │
│  │ Secure     │  │         │  │ PostgreSQL │  │
│  │ Storage    │  │         │  └────────────┘  │
│  │ (token)    │  │         │                  │
│  └────────────┘  │         └──────────────────┘
└──────────────────┘
```

**Конфигурация**:
```dart
// mobile-app/lib/services/api_service.dart

class ApiService {
  String _baseUrl = 'https://api.yourdomain.com';

  Future<List<Tool>> getTools() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/api/tools'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return parseTools(response.body);
  }
}
```

**Deploy**:
```bash
# Backend - same as web
docker-compose up

# Mobile app
flutter build apk  # Android
flutter build ios  # iOS
```

---

## 📱 Scenario 4: Mobile App - Embedded Backend (Future)

**Кто**: Полностью оффлайн пользователи

```
┌────────────────────────────────────────┐
│  User's Phone (Android/iOS)            │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  Flutter App                     │  │
│  │                                  │  │
│  │  ┌────────────────────────────┐  │  │
│  │  │ Dart UI                    │  │  │
│  │  └──────────┬─────────────────┘  │  │
│  │             │ Platform Channel   │  │
│  │  ┌──────────▼─────────────────┐  │  │
│  │  │ Python Backend             │  │  │
│  │  │ (via Chaquopy/PythonKit)   │  │  │
│  │  │                            │  │  │
│  │  │ • FastAPI                  │  │  │
│  │  │ • SQLite                   │  │  │
│  │  │ • 57+ tools                │  │  │
│  │  └────────────────────────────┘  │  │
│  └──────────────────────────────────┘  │
│                                        │
│  Всё работает БЕЗ интернета! 🔒        │
└────────────────────────────────────────┘
```

**Технологии**:

### Android: Chaquopy
```kotlin
// android/app/build.gradle
plugins {
    id 'com.chaquo.python'
}

python {
    buildPython "/usr/bin/python3"
    pip {
        install "fastapi"
        install "uvicorn"
    }
}
```

```dart
// Flutter side
import 'package:flutter/services.dart';

class BackendService {
  static const platform = MethodChannel('com.data20/backend');

  Future<void> startBackend() async {
    await platform.invokeMethod('startPythonBackend');
  }
}
```

### iOS: PythonKit
```swift
// ios/Runner/AppDelegate.swift
import PythonKit

func startPythonBackend() {
    let sys = Python.import("sys")
    let uvicorn = Python.import("uvicorn")

    uvicorn.run("backend.server:app", host: "127.0.0.1", port: 8001)
}
```

**Размер**: ~80-120MB (включая Python)
**Сложность**: Высокая (нужны native bindings)

---

# Прогрессия Уровней

## 📊 От Простого к Сложному

### Уровень 1: Static Files 📄
**Сложность**: ⭐ (Базовая)

```
HTML файлы → Браузер
```

**Что есть**:
- ✅ Простые HTML/CSS/JS файлы
- ✅ Работает без сервера (file://)
- ✅ Быстрая загрузка

**Что НЕТ**:
- ❌ Нет динамических данных
- ❌ Нет аутентификации
- ❌ Нет сохранения состояния

**Пример**: `/webapp/index.html` (Phase 6.5)

---

### Уровень 2: SPA + External API 🌐
**Сложность**: ⭐⭐ (Средняя)

```
React App → REST API → Database
```

**Что есть**:
- ✅ Динамический UI (React)
- ✅ Клиент-серверная архитектура
- ✅ JWT аутентификация
- ✅ Real-time updates

**Что НЕТ**:
- ❌ Требует интернет/сеть
- ❌ Требует running server
- ❌ Зависимость от backend availability

**Пример**: `/webapp-react/` + `/backend/` (Phase 6.6)

**Deployment**:
```
Frontend → CDN/S3 (статика)
Backend → Cloud server (AWS/GCP)
```

---

### Уровень 3: Desktop App + External Backend 💻
**Сложность**: ⭐⭐⭐ (Средняя+)

```
Electron (React + Node) → REST API → Backend
```

**Что есть**:
- ✅ Native desktop app
- ✅ Кросс-платформенность
- ✅ File system access
- ✅ System integration

**Что НЕТ**:
- ❌ Всё ещё требует running backend
- ❌ Два отдельных процесса

**Пример**: `/desktop-app/` (Phase 6.7)

**Использование**:
```bash
# Terminal 1
python backend/server.py

# Terminal 2
npm run dev  # Electron app
```

---

### Уровень 4: Desktop App + Embedded Backend 📦
**Сложность**: ⭐⭐⭐⭐ (Высокая)

```
Electron → Embedded Python → SQLite
   ↓
Single .exe/.app файл
```

**Что есть**:
- ✅ Единое приложение
- ✅ Автозапуск backend
- ✅ Offline-first
- ✅ Портативность

**Что НЕТ**:
- ❌ Больший размер (~200MB)
- ❌ Сложнее сборка

**Пример**: Будущая версия `/desktop-app/`

**Технологии**:
```bash
# Упаковка backend
pyinstaller --onefile backend/server.py
→ dist/server.exe (50MB)

# Electron builder
electron-builder
→ Data20-Setup.exe (200MB)
  ├─ app.asar (React)
  ├─ server.exe (Backend)
  └─ data20.db (SQLite)
```

**Как запускается**:
```javascript
// electron/main.js
const backendExe = path.join(
  process.resourcesPath,
  'server.exe'
);

const backend = spawn(backendExe, ['--port', '8001']);

// Ждём запуск
await waitForBackend('http://localhost:8001/health');

// Открываем окно
createWindow();
```

---

### Уровень 5: Mobile + Cloud Backend 📱
**Сложность**: ⭐⭐⭐⭐ (Высокая)

```
Flutter (iOS/Android) → HTTPS API → Cloud
```

**Что есть**:
- ✅ Нативные мобильные приложения
- ✅ Синхронизация между устройствами
- ✅ Push notifications
- ✅ Cloud storage

**Что НЕТ**:
- ❌ Требует интернет
- ❌ Зависит от cloud availability

**Пример**: `/mobile-app/` (Phase 6.8)

---

### Уровень 6: Mobile + Embedded Backend 🚀
**Сложность**: ⭐⭐⭐⭐⭐ (Экспертная)

```
Flutter → Python (Chaquopy) → SQLite
   ↓
Полностью offline мобильное приложение
```

**Что есть**:
- ✅ 100% offline работа
- ✅ Все 57+ tools на телефоне
- ✅ Нативная производительность
- ✅ Локальная база данных

**Что НЕТ**:
- ❌ Сложнейшая интеграция
- ❌ Большой размер APK (~100MB)
- ❌ Проблемы с App Store (embedded Python)

**Технологии**:

#### Android (Chaquopy)
```gradle
// android/app/build.gradle
python {
    buildPython "python3.9"
    pip {
        install "fastapi==0.104.1"
        install "uvicorn==0.24.0"
        install "sqlalchemy==2.0.23"
    }
}
```

```kotlin
// MainActivity.kt
import com.chaquo.python.Python

class MainActivity {
    fun startBackend() {
        val py = Python.getInstance()
        val module = py.getModule("backend.server")
        module.callAttr("run_server", 8001)
    }
}
```

```dart
// lib/main.dart
void main() async {
  // Запускаем Python backend
  await BackendService.startEmbeddedBackend();

  // Ждём готовности
  await BackendService.waitForReady();

  // Запускаем UI
  runApp(MyApp());
}
```

#### iOS (PythonKit) - ОЧЕНЬ сложно
```swift
// AppDelegate.swift
import PythonKit

func application(...) {
    // Python для iOS - экспериментально!
    let sys = Python.import("sys")
    // Запуск backend...
}
```

**Проблемы**:
- Apple не любит embedded scripting
- Review процесс сложный
- Альтернатива: **Dart-only backend** (без Python)

---

### Уровень 7: WebAssembly (Будущее) 🔮
**Сложность**: ⭐⭐⭐⭐⭐⭐ (Bleeding edge)

```
Browser → Python в WASM → IndexedDB
   ↓
Backend ВНУТРИ браузера!
```

**Технология**: **Pyodide** (Python compiled to WebAssembly)

```html
<!-- index.html -->
<script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
<script>
async function loadPyodide() {
  let pyodide = await loadPyodide();

  // Установить FastAPI в браузере!
  await pyodide.loadPackage('micropip');
  await pyodide.runPythonAsync(`
    import micropip
    await micropip.install('fastapi')

    from backend.server import app
    # Запуск FastAPI в браузере
  `);
}
</script>
```

**Что это даёт**:
- ✅ Backend КОД в браузере
- ✅ Нет сервера вообще
- ✅ Полностью offline
- ✅ Работает на GitHub Pages

**Проблемы**:
- ❌ Медленно (интерпретатор в WASM)
- ❌ Не все библиотеки поддерживаются
- ❌ Большой размер загрузки (~50MB)
- ❌ Технология молодая

---

## 📊 Сравнительная таблица уровней

| Уровень | Платформа | Backend Location | Offline | Сложность | Размер | Deployment |
|---------|-----------|------------------|---------|-----------|--------|------------|
| 1️⃣ Static | Web | Нет | ✅ | ⭐ | 1MB | File serve |
| 2️⃣ SPA | Web | Cloud | ❌ | ⭐⭐ | 2MB + Server | CDN + Cloud |
| 3️⃣ Desktop Ext | Desktop | External | ❌ | ⭐⭐⭐ | 100MB × 2 | 2 installers |
| 4️⃣ Desktop Emb | Desktop | Embedded | ✅ | ⭐⭐⭐⭐ | 200MB | 1 installer |
| 5️⃣ Mobile Cloud | Mobile | Cloud | ❌ | ⭐⭐⭐⭐ | 20MB + Server | App Store + Cloud |
| 6️⃣ Mobile Emb | Mobile | Embedded | ✅ | ⭐⭐⭐⭐⭐ | 100MB | App Store |
| 7️⃣ WASM | Web | Browser | ✅ | ⭐⭐⭐⭐⭐⭐ | 50MB | Static host |

---

# План Развития Offline Mode

## 🎯 Текущее состояние

**Что уже есть:**
- ✅ Standalone mode для backend (SQLite + no Redis + no Celery)
- ✅ React web app
- ✅ Electron desktop app (external backend)
- ✅ Flutter mobile app (cloud backend)

**Где находимся**: Уровень 2-3 (SPA + Desktop с external backend)

---

## 🗺️ Roadmap: Развитие Offline

### Phase 7.1: Desktop Embedded Backend ⭐⭐⭐⭐

**Цель**: Единое desktop приложение с встроенным backend

**Задачи**:
1. Упаковка Python backend в executable (PyInstaller)
2. Интеграция в Electron build process
3. Автозапуск backend из Main Process
4. Health checks и restart logic
5. Единый installer (InnoSetup/DMG/AppImage)

**Файлы для создания**:
```
desktop-app/
├─ electron/
│  ├─ backend-manager.js      # Управление Python процессом
│  └─ packager.js              # Build script
├─ resources/
│  ├─ backend.exe              # PyInstaller output (Windows)
│  ├─ backend                  # PyInstaller output (Linux)
│  └─ backend.app              # PyInstaller output (macOS)
└─ installers/
   ├─ windows-installer.nsi    # NSIS script
   ├─ mac-dmg-config.json      # DMG builder
   └─ linux-appimage.yml       # AppImage config
```

**backend-manager.js**:
```javascript
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

class BackendManager {
  constructor() {
    this.process = null;
    this.port = 8001;
    this.baseUrl = `http://127.0.0.1:${this.port}`;
  }

  getExecutablePath() {
    const resourcePath = process.resourcesPath;

    if (process.platform === 'win32') {
      return path.join(resourcePath, 'backend', 'backend.exe');
    } else if (process.platform === 'darwin') {
      return path.join(resourcePath, 'backend', 'backend');
    } else {
      return path.join(resourcePath, 'backend', 'backend');
    }
  }

  async start() {
    const exe = this.getExecutablePath();

    this.process = spawn(exe, [
      '--port', this.port.toString(),
      '--host', '127.0.0.1',
      '--db', path.join(app.getPath('userData'), 'data20.db')
    ]);

    this.process.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    this.process.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    // Ждём запуск
    await this.waitForReady();
  }

  async waitForReady(maxAttempts = 30) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await axios.get(`${this.baseUrl}/health`);
        if (response.status === 200) {
          console.log('Backend ready!');
          return true;
        }
      } catch (e) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    throw new Error('Backend failed to start');
  }

  stop() {
    if (this.process) {
      this.process.kill();
    }
  }
}

module.exports = BackendManager;
```

**Build script**:
```bash
#!/bin/bash
# build-embedded.sh

echo "🔨 Building embedded desktop app..."

# 1. Build backend executable
echo "📦 Packaging Python backend..."
cd ../backend
pyinstaller \
  --onefile \
  --name backend \
  --add-data "tool_registry.py:." \
  --hidden-import fastapi \
  --hidden-import uvicorn \
  server.py

# 2. Copy to resources
echo "📋 Copying backend to Electron resources..."
cd ../desktop-app
mkdir -p resources/backend
cp ../backend/dist/backend* resources/backend/

# 3. Build React
echo "⚛️ Building React frontend..."
npm run build:react

# 4. Build Electron
echo "🔌 Building Electron app..."
electron-builder \
  --win \
  --mac \
  --linux \
  --config electron-builder.yml

echo "✅ Done! Installers in dist/"
```

**electron-builder.yml**:
```yaml
appId: com.data20.knowledgebase
productName: Data20 Knowledge Base

directories:
  output: dist
  buildResources: resources

files:
  - build/**/*
  - electron/**/*
  - package.json

extraResources:
  - from: resources/backend
    to: backend
    filter:
      - "**/*"

win:
  target:
    - nsis
    - portable
  icon: resources/icon.ico

mac:
  target:
    - dmg
    - zip
  icon: resources/icon.icns
  category: public.app-category.productivity

linux:
  target:
    - AppImage
    - deb
    - rpm
  icon: resources/icon.png
  category: Office

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
```

**Результат**: Единый installer ~200MB

---

### Phase 7.2: Progressive Web App (PWA) ⭐⭐⭐

**Цель**: Web app работает offline с Service Worker

**Технологии**:
- Service Worker (кеширование)
- IndexedDB (локальная БД)
- Background Sync (отложенные запросы)

**Что это даёт**:
- Offline UI (но без backend логики)
- Кеш данных
- Install на home screen

**Ограничения**:
- ❌ Нет выполнения Python tools offline
- ✅ Просмотр кешированных результатов

**Файлы**:
```
webapp-react/
└─ public/
   ├─ service-worker.js
   └─ manifest.json
```

**service-worker.js**:
```javascript
const CACHE_NAME = 'data20-v1';
const urlsToCache = [
  '/',
  '/static/js/main.js',
  '/static/css/main.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => response || fetch(event.request))
  );
});
```

---

### Phase 7.3: Mobile Embedded Backend (Android) ⭐⭐⭐⭐⭐

**Цель**: Полный Python backend на Android

**Технология**: Chaquopy

**Шаги**:

1. **Настроить Chaquopy**:
```gradle
// android/app/build.gradle
plugins {
    id 'com.android.application'
    id 'com.chaquo.python'  // Добавить
}

android {
    defaultConfig {
        ndk {
            abiFilters "armeabi-v7a", "arm64-v8a", "x86", "x86_64"
        }

        python {
            version "3.9"
            pip {
                install "fastapi==0.104.1"
                install "uvicorn==0.24.0"
                install "sqlalchemy==2.0.23"
                install "python-jose==3.3.0"
            }
        }
    }
}
```

2. **Скопировать Python код**:
```
android/
└─ app/
   └─ src/
      └─ main/
         └─ python/
            └─ backend/
               ├─ __init__.py
               ├─ server.py
               ├─ tool_registry.py
               └─ ... (весь backend)
```

3. **Kotlin bridge**:
```kotlin
// MainActivity.kt
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : FlutterActivity() {
    private lateinit var python: Python
    private var backendThread: Thread? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Инициализация Python
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        python = Python.getInstance()

        // Запуск backend в отдельном потоке
        startBackend()
    }

    private fun startBackend() {
        backendThread = Thread {
            val module = python.getModule("backend.server")

            // Путь к SQLite
            val dbPath = getExternalFilesDir(null)?.absolutePath + "/data20.db"

            // Запуск FastAPI
            module.callAttr("run_server",
                "127.0.0.1",  // host
                8001,          // port
                dbPath         // database
            )
        }
        backendThread?.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        // Остановка backend
        backendThread?.interrupt()
    }
}
```

4. **Flutter integration**:
```dart
// lib/services/embedded_backend.dart
import 'package:flutter/services.dart';

class EmbeddedBackend {
  static const platform = MethodChannel('com.data20/backend');

  static Future<void> start() async {
    try {
      await platform.invokeMethod('startBackend');
      print('✅ Embedded backend started');
    } catch (e) {
      print('❌ Failed to start backend: $e');
    }
  }

  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('http://127.0.0.1:8001/health')
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}

// main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Запуск embedded backend
  await EmbeddedBackend.start();

  // Ждём готовности
  for (int i = 0; i < 30; i++) {
    if (await EmbeddedBackend.checkHealth()) {
      break;
    }
    await Future.delayed(Duration(seconds: 1));
  }

  runApp(MyApp());
}
```

**Результат**:
- APK размер: ~100MB
- 100% offline работа
- Все 57+ tools доступны

**Проблемы**:
- Долгая сборка (~30 мин)
- Сложности с некоторыми библиотеками
- Большой размер

---

### Phase 7.4: Cloud Sync (Hybrid Mode) ⭐⭐⭐⭐

**Цель**: Работа offline + синхронизация когда есть сеть

**Архитектура**:
```
Offline Mode:
Mobile App → Local Backend → SQLite
                              ↓
                         Local Jobs Queue

Online Mode:
Mobile App → Local Backend → SQLite
                              ↓
                         Sync Service
                              ↓
                    Cloud Backend (when online)
                              ↓
                         PostgreSQL
```

**Функции**:
- Работа полностью offline
- Фоновая синхронизация jobs
- Conflict resolution
- Multi-device sync

**Технологии**:
- **Operational Transform** для conflicts
- **WorkManager** (Android) для background sync
- **Background Fetch** (iOS)

---

### Phase 7.5: WASM Backend (Экспериментально) ⭐⭐⭐⭐⭐⭐

**Цель**: Python backend в браузере через WebAssembly

**Технология**: Pyodide

**Proof of Concept**:
```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
</head>
<body>
  <script>
    async function loadBackend() {
      // Загрузка Pyodide
      let pyodide = await loadPyodide();

      // Установка пакетов
      await pyodide.loadPackage(['micropip', 'sqlite3']);

      await pyodide.runPythonAsync(`
        import micropip
        await micropip.install('fastapi')
        await micropip.install('pydantic')

        # Загрузка нашего backend кода
        from js import fetch

        # Простейший API в браузере
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/api/tools")
        def get_tools():
            return [{"name": "statistics", "category": "analysis"}]

        # Запуск не через uvicorn, а через прокси
        print("Backend loaded in browser!")
      `);

      console.log('✅ Python backend running in browser!');
    }

    loadBackend();
  </script>
</body>
</html>
```

**Проблемы**:
- Не все библиотеки работают
- uvicorn не работает (нет asyncio.run)
- Нужен HTTP proxy в JavaScript
- Очень медленно

**Альтернатива**: Переписать tools на JavaScript
```javascript
// tools-js/statistics.js
export function calculateMean(data) {
  return data.reduce((a, b) => a + b) / data.length;
}

export function calculateStdDev(data) {
  const mean = calculateMean(data);
  const variance = data.reduce((sum, x) => sum + Math.pow(x - mean, 2), 0) / data.length;
  return Math.sqrt(variance);
}
```

---

## 📊 Приоритизация развития

### Короткий срок (1-2 месяца)
1. ✅ **Phase 7.1: Desktop Embedded Backend** - самый ценный, средняя сложность
2. ⭐ **Phase 7.2: PWA** - быстро реализовать, улучшает UX

### Средний срок (3-6 месяцев)
3. ⭐ **Phase 7.4: Cloud Sync** - hybrid mode очень полезен
4. 🔬 **Phase 7.3: Android Embedded** - сложно, но powerful

### Долгий срок (6+ месяцев)
5. 🔮 **Phase 7.5: WASM** - экспериментально, низкий приоритет

---

# Технологические Альтернативы

## 🔄 Альтернативные стеки для Backend

### Текущий: Python + FastAPI
```
✅ Быстрая разработка
✅ Богатая экосистема (pandas, numpy, scipy)
✅ Async support
❌ Сложно встроить в mobile
❌ Большой runtime
```

### Альтернатива 1: Dart + Shelf (Backend на Dart)
```dart
// backend_dart/lib/server.dart
import 'package:shelf/shelf.dart';
import 'package:shelf/shelf_io.dart' as io;

void main() async {
  var handler = const Pipeline()
      .addMiddleware(logRequests())
      .addHandler(_echoRequest);

  var server = await io.serve(handler, 'localhost', 8080);
  print('Server running on localhost:${server.port}');
}

Response _echoRequest(Request request) {
  return Response.ok('Request for "${request.url}"');
}
```

**Преимущества**:
- ✅ Единый язык с Flutter
- ✅ Легко встроить в mobile (тот же runtime)
- ✅ Меньший размер
- ❌ Нет pandas/numpy/scipy
- ❌ Меньше библиотек для data analysis

### Альтернатива 2: Rust + Actix (Native performance)
```rust
// backend_rust/src/main.rs
use actix_web::{web, App, HttpServer, Responder};

async fn index() -> impl Responder {
    "Hello world!"
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/", web::get().to(index))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
```

**Преимущества**:
- ✅ Максимальная производительность
- ✅ Маленький бинарник (~5MB)
- ✅ Легко встроить везде (compile to native)
- ❌ Долгая разработка
- ❌ Нужно переписать все 57 tools

### Альтернатива 3: Go + Gin (Баланс)
```go
// backend_go/main.go
package main

import "github.com/gin-gonic/gin"

func main() {
    r := gin.Default()
    r.GET("/api/tools", func(c *gin.Context) {
        c.JSON(200, gin.H{
            "message": "tools list",
        })
    })
    r.Run(":8080")
}
```

**Преимущества**:
- ✅ Быстрая компиляция
- ✅ Static binary (~10MB)
- ✅ Хорошая производительность
- ❌ Меньше ML/Data libraries

---

## 🎯 Рекомендации

### Для разных use cases:

**Enterprise (Cloud deployment)**:
- ✅ Текущий стек: Python + FastAPI + PostgreSQL + Redis
- Масштабируемость, богатая экосистема

**Desktop (Embedded)**:
- ✅ Python + FastAPI + SQLite (PyInstaller)
- Или Go + Gin (smaller binary)

**Mobile (Embedded)**:
- 🔄 Вариант 1: Dart + Shelf (единый язык)
- 🔄 Вариант 2: Python + Chaquopy (текущие tools)
- 🔄 Вариант 3: Rust + FFI (максимальная производительность)

**Web (Offline)**:
- ✅ PWA + Service Worker
- 🔮 JavaScript reimplementation tools
- 🔬 Pyodide (экспериментально)

---

## 📈 Итоговая матрица решений

| Платформа | Режим | Backend Location | Технология | Размер | Offline | Рекомендация |
|-----------|-------|------------------|------------|--------|---------|--------------|
| Web | Production | Cloud | Python+FastAPI | 2MB + Server | ❌ | ⭐⭐⭐⭐⭐ Лучший выбор |
| Web | Offline | Browser | PWA+SW | 2MB | Partial | ⭐⭐⭐ Quick win |
| Desktop | Cloud | External | Python+FastAPI | 100MB × 2 | ❌ | ⭐⭐ Development |
| Desktop | Standalone | Embedded | Python+PyInstaller | 200MB | ✅ | ⭐⭐⭐⭐⭐ Продакшн готов |
| Desktop | Standalone | Embedded | Go+Gin | 50MB | ✅ | ⭐⭐⭐⭐ Альтернатива |
| Mobile | Cloud | Remote | Python+FastAPI | 20MB + Server | ❌ | ⭐⭐⭐⭐ Текущий |
| Mobile | Embedded | Local | Python+Chaquopy | 100MB | ✅ | ⭐⭐⭐ Возможно |
| Mobile | Embedded | Local | Dart+Shelf | 30MB | ✅ | ⭐⭐⭐⭐ Рекомендуется |
| Mobile | Embedded | Local | Rust+FFI | 25MB | ✅ | ⭐⭐⭐⭐⭐ Лучшее качество |

---

## 🚀 Следующие шаги

**Немедленно** (можно сделать сейчас):
1. Desktop Embedded Backend (Phase 7.1)
2. PWA Service Worker (Phase 7.2)

**Скоро** (требует исследования):
3. Dart backend POC
4. Cloud Sync architecture

**Будущее** (долгосрочно):
5. Mobile embedded (Dart или Rust)
6. WASM experiments
