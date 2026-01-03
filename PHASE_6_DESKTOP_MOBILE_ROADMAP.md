# Phase 6.3-6.4: Desktop & Mobile Application Roadmap

## Текущее состояние

### ✅ Что уже готово для desktop/mobile

1. **Backend API** (FastAPI)
   - ✅ REST API с 30+ endpoints
   - ✅ JWT authentication
   - ✅ User management
   - ✅ Job execution & tracking
   - ✅ 57+ data analysis tools

2. **Standalone Mode**
   - ✅ SQLite database (no server needed)
   - ✅ Local execution (no Celery)
   - ✅ Offline operation
   - ✅ Portable (USB flash drive)

3. **Security**
   - ✅ JWT tokens
   - ✅ Password hashing (bcrypt)
   - ✅ Role-based access control
   - ✅ Job ownership

4. **Monitoring**
   - ✅ Structured logging
   - ✅ Prometheus metrics
   - ✅ Request tracing

### ❌ Что нужно добавить

1. **Frontend UI** (нет визуального интерфейса)
2. **Desktop wrapper** (для Windows/Mac/Linux приложения)
3. **Mobile app** (для Android/iOS)
4. **Offline sync** (опционально для мобильных устройств)
5. **App packaging & distribution**

---

## Phase 6.3: Desktop Application

### Архитектура

```
┌─────────────────────────────────────────┐
│          Desktop Application            │
│  (Electron/Tauri/PyQt)                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────┐   ┌──────────────┐  │
│  │   Frontend    │   │   Backend    │  │
│  │   (React/     │◄─►│   (FastAPI   │  │
│  │    Vue)       │   │    SQLite)   │  │
│  └───────────────┘   └──────────────┘  │
│         ▲                    ▲          │
│         │                    │          │
│         └────────────────────┘          │
│          http://localhost:8001          │
└─────────────────────────────────────────┘
```

### Опция 1: Electron (Рекомендуется для быстрого старта)

**Преимущества**:
- ✅ Кроссплатформенный (Windows, Mac, Linux)
- ✅ Огромное сообщество и примеры
- ✅ Web технологии (HTML/CSS/JavaScript)
- ✅ Auto-update механизм
- ✅ Много готовых UI библиотек

**Недостатки**:
- ❌ Большой размер (~150-200MB)
- ❌ Больше потребление RAM

**Стек**:
- Electron 28+
- React 18 + TypeScript
- Material-UI или Ant Design
- FastAPI backend (embedded)

**Структура проекта**:
```
data20-desktop/
├── electron/                 # Electron main process
│   ├── main.js              # Entry point
│   ├── preload.js           # Bridge между renderer и main
│   └── backend.js           # Backend process manager
├── src/                     # React frontend
│   ├── components/          # UI components
│   ├── pages/               # Application pages
│   ├── api/                 # API client
│   └── App.tsx              # Main app
├── backend/                 # Python FastAPI (from current project)
│   ├── server.py
│   ├── database_v2.py
│   └── ...
├── package.json             # NPM dependencies
└── electron-builder.yml     # Build configuration
```

**Пример main.js**:
```javascript
const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let backendProcess;

// Start FastAPI backend
function startBackend() {
  const pythonPath = path.join(__dirname, '../backend/venv/bin/python');
  const serverPath = path.join(__dirname, '../run_standalone.py');

  backendProcess = spawn(pythonPath, [serverPath, '--port', '8001']);

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
}

// Create main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Wait for backend to start
  setTimeout(() => {
    mainWindow.loadURL('http://localhost:3000'); // React dev server
    // In production: mainWindow.loadFile('build/index.html');
  }, 2000);
}

app.on('ready', () => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
  app.quit();
});
```

**Сборка**:
```bash
# Development
npm run electron:dev

# Build for all platforms
npm run electron:build

# Build for specific platform
npm run electron:build:win    # Windows
npm run electron:build:mac    # macOS
npm run electron:build:linux  # Linux
```

**Размер приложения**:
- Windows: ~150MB (installer), ~200MB (installed)
- macOS: ~180MB (.dmg), ~220MB (installed)
- Linux: ~140MB (.AppImage), ~190MB (installed)

---

### Опция 2: Tauri (Рекомендуется для production)

**Преимущества**:
- ✅ Легковесный (~15-20MB final app)
- ✅ Быстрый (Rust backend)
- ✅ Безопасный (меньше attack surface)
- ✅ Web технологии для UI

**Недостатки**:
- ❌ Меньше примеров и сообщества
- ❌ Нужно знание Rust (опционально)

**Стек**:
- Tauri 1.5+
- React/Vue/Svelte frontend
- Rust для системных вызовов
- FastAPI backend (embedded)

**Структура**:
```
data20-tauri/
├── src-tauri/               # Tauri backend (Rust)
│   ├── src/
│   │   ├── main.rs          # Entry point
│   │   └── backend.rs       # Backend process manager
│   ├── Cargo.toml           # Rust dependencies
│   └── tauri.conf.json      # Tauri config
├── src/                     # Frontend (React)
│   ├── components/
│   ├── pages/
│   └── App.tsx
└── package.json
```

**Пример main.rs**:
```rust
use tauri::Manager;
use std::process::Command;

#[tauri::command]
fn start_backend() {
    let backend_path = "run_standalone.py";

    Command::new("python")
        .arg(backend_path)
        .arg("--port")
        .arg("8001")
        .spawn()
        .expect("Failed to start backend");
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            start_backend();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Размер приложения**:
- Windows: ~15MB
- macOS: ~18MB
- Linux: ~12MB

---

### Опция 3: PyInstaller + PyQt/PySide

**Преимущества**:
- ✅ Pure Python (знакомый язык)
- ✅ Native GUI
- ✅ Нет веб-технологий

**Недостатки**:
- ❌ Более сложная разработка UI
- ❌ Размер ~100-150MB

**Структура**:
```
data20-pyqt/
├── main.py                  # Entry point
├── ui/
│   ├── main_window.py       # Main window
│   ├── login_dialog.py      # Login UI
│   └── job_list.py          # Job list widget
├── backend/                 # FastAPI (in-process)
│   └── server.py
└── data20.spec              # PyInstaller spec
```

---

## Phase 6.4: Mobile Application

### Архитектура

```
┌─────────────────────────────────────────┐
│      Mobile Application (iOS/Android)   │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────┐   ┌──────────────┐  │
│  │   Frontend    │   │   Backend    │  │
│  │  (React       │◄─►│   (FastAPI   │  │
│  │   Native/     │   │    SQLite)   │  │
│  │   Flutter)    │   │              │  │
│  └───────────────┘   └──────────────┘  │
│                                         │
│  Режимы:                                │
│  1. Embedded backend (offline)          │
│  2. Remote backend (online sync)        │
└─────────────────────────────────────────┘
```

### Опция 1: Flutter (Рекомендуется)

**Преимущества**:
- ✅ Кроссплатформенный (iOS + Android + Web + Desktop)
- ✅ Отличная производительность
- ✅ Красивый UI (Material Design)
- ✅ Hot reload
- ✅ Dart язык (похож на TypeScript)

**Недостатки**:
- ❌ Новый язык (Dart)
- ❌ Нужно обучение

**Стек**:
- Flutter 3.16+
- Dart 3+
- sqflite (SQLite для Flutter)
- http/dio (API client)

**Структура**:
```
data20_mobile/
├── lib/
│   ├── main.dart            # Entry point
│   ├── screens/             # UI screens
│   │   ├── login_screen.dart
│   │   ├── home_screen.dart
│   │   ├── tools_screen.dart
│   │   └── jobs_screen.dart
│   ├── models/              # Data models
│   │   ├── user.dart
│   │   ├── job.dart
│   │   └── tool.dart
│   ├── services/            # Business logic
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   └── database_service.dart
│   └── widgets/             # Reusable widgets
├── android/                 # Android project
├── ios/                     # iOS project
└── pubspec.yaml             # Dependencies
```

**Пример API service**:
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  final String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:8001'});

  Future<List<Tool>> getTools() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/tools'),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['tools'] as List)
          .map((json) => Tool.fromJson(json))
          .toList();
    } else {
      throw Exception('Failed to load tools');
    }
  }

  Future<Job> runTool(String toolName, Map<String, dynamic> params) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/run'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'tool_name': toolName,
        'parameters': params,
      }),
    );

    if (response.statusCode == 200) {
      return Job.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to run tool');
    }
  }
}
```

**Backend на Android**:
```dart
// Опция 1: Embedded Python (Chaquopy для Android)
// Запуск FastAPI внутри Android app

// Опция 2: Remote backend
// Подключение к удаленному серверу

// Опция 3: Offline-first
// Local SQLite + sync при наличии сети
```

**Размер приложения**:
- Android: ~20-30MB (без embedded backend)
- Android: ~60-80MB (с embedded Python + FastAPI)
- iOS: ~25-35MB

---

### Опция 2: React Native

**Преимущества**:
- ✅ JavaScript/TypeScript (знакомый язык)
- ✅ Огромное сообщество
- ✅ Много готовых библиотек
- ✅ Hot reload

**Недостатки**:
- ❌ Не такая производительность как Flutter
- ❌ Сложнее с native modules

**Стек**:
- React Native 0.73+
- TypeScript
- React Navigation
- Axios (API client)
- AsyncStorage (local data)

**Структура**:
```
data20-rn/
├── src/
│   ├── screens/             # Screens
│   ├── components/          # Components
│   ├── services/            # API services
│   ├── store/               # State management (Redux/MobX)
│   └── types/               # TypeScript types
├── android/                 # Android project
├── ios/                     # iOS project
└── package.json
```

---

## Сравнение технологий

### Desktop

| Критерий | Electron | Tauri | PyQt |
|----------|----------|-------|------|
| Размер приложения | 150-200MB | 15-20MB | 100-150MB |
| Производительность | Средняя | Отличная | Хорошая |
| Сложность разработки | Легкая | Средняя | Средняя |
| UI технологии | Web (React/Vue) | Web (React/Vue) | Native (Qt) |
| Сообщество | Огромное | Растущее | Большое |
| Кроссплатформенность | ✅ | ✅ | ✅ |
| Auto-update | ✅ | ✅ | ⚠️ |

**Рекомендация**: **Electron** (для быстрого старта) или **Tauri** (для production)

### Mobile

| Критерий | Flutter | React Native | Native |
|----------|---------|--------------|--------|
| Производительность | Отличная | Хорошая | Наилучшая |
| Сложность разработки | Средняя | Легкая | Сложная |
| Язык | Dart | JavaScript/TypeScript | Kotlin/Swift |
| Кроссплатформенность | ✅ iOS/Android/Web/Desktop | ✅ iOS/Android | ❌ |
| Размер приложения | 20-30MB | 25-35MB | 15-20MB |
| Hot reload | ✅ | ✅ | ❌ |
| UI | Material/Cupertino | Native components | Native |

**Рекомендация**: **Flutter** (для лучшей производительности и UI)

---

## Roadmap реализации

### Phase 6.3: Desktop Application (Electron)

**Шаг 1: Setup проект (1-2 дня)**
```bash
# Создать Electron + React проект
npx create-electron-app data20-desktop --template=webpack-typescript

# Добавить зависимости
npm install axios react-router-dom @mui/material
```

**Шаг 2: Интеграция backend (1-2 дня)**
- Embedded FastAPI server
- Backend process manager
- Auto-start при запуске приложения

**Шаг 3: Frontend UI (3-5 дней)**
- Login/Register screens
- Tools list
- Job execution & monitoring
- User management (admin)

**Шаг 4: Packaging (1 день)**
- electron-builder configuration
- Code signing (опционально)
- Auto-update setup

**Шаг 5: Testing & Distribution (2-3 дня)**
- E2E тесты
- Build для всех платформ
- Create installers

**Total**: 8-13 дней

---

### Phase 6.4: Mobile Application (Flutter)

**Шаг 1: Setup проект (1 день)**
```bash
flutter create data20_mobile
```

**Шаг 2: API Client (2-3 дня)**
- HTTP client (dio)
- Authentication service
- API models

**Шаг 3: UI Screens (5-7 дней)**
- Login/Register
- Tools list
- Tool execution
- Job history
- Settings

**Шаг 4: Local storage (2-3 дня)**
- SQLite database
- Offline caching
- Sync mechanism

**Шаг 5: Native integration (2-3 дня)**
- Permissions (storage, network)
- File picker
- Share functionality

**Шаг 6: Testing & Deployment (3-4 дня)**
- Unit tests
- Widget tests
- Build APK/IPA
- Play Store / App Store submission

**Total**: 15-21 день

---

## Что нужно для запуска

### Desktop (Electron)

**Требования**:
```json
{
  "dependencies": {
    "electron": "^28.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "@mui/material": "^5.14.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0",
    "typescript": "^5.0.0",
    "webpack": "^5.88.0"
  }
}
```

**Команды**:
```bash
npm install
npm run start        # Development
npm run build        # Build frontend
npm run electron:build  # Package app
```

### Mobile (Flutter)

**Требования**:
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  sqflite: ^2.3.0
  provider: ^6.1.0
  flutter_secure_storage: ^9.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
```

**Команды**:
```bash
flutter pub get
flutter run          # Development
flutter build apk    # Android release
flutter build ios    # iOS release (macOS only)
```

---

## Следующие шаги

1. **Выбрать технологию**:
   - Desktop: Electron или Tauri?
   - Mobile: Flutter или React Native?

2. **Создать прототип** (MVP):
   - Базовый UI
   - Интеграция с backend
   - Login + 1 tool execution

3. **Расширить функциональность**:
   - Все экраны
   - Offline sync
   - Push notifications (mobile)

4. **Packaging & Distribution**:
   - Code signing
   - Auto-updates
   - App stores

---

## Готовые решения

### Уже готово (можно использовать сразу)

1. **Backend API** - работает ✅
2. **SQLite database** - работает ✅
3. **Standalone mode** - работает ✅
4. **Authentication** - работает ✅
5. **All tools** - работают ✅

### Нужно создать

1. **Frontend UI** (React/Flutter)
2. **Desktop wrapper** (Electron/Tauri)
3. **Mobile app packaging**

**Оценка времени**:
- Desktop MVP: 2-3 недели
- Mobile MVP: 3-4 недели
- Full-featured: 2-3 месяца

---

## Summary

### Desktop Application

**Рекомендуемый стек**:
- **Electron** + React + TypeScript + Material-UI
- **FastAPI backend** (embedded)
- **SQLite** database

**Преимущества**:
- Быстрая разработка
- Знакомые технологии (web)
- Кроссплатформенность

### Mobile Application

**Рекомендуемый стек**:
- **Flutter** + Dart
- **REST API** (FastAPI)
- **SQLite** (local storage)
- **Offline-first** architecture

**Преимущества**:
- Отличная производительность
- Красивый UI
- iOS + Android из одной кодовой базы

### Что уже готово

✅ Backend API полностью готов для desktop/mobile
✅ Standalone mode работает без серверов
✅ SQLite поддержка
✅ Аутентификация и безопасность
✅ Все инструменты анализа данных

### Что нужно добавить

📱 Frontend UI (React для desktop, Flutter для mobile)
📦 Desktop wrapper (Electron/Tauri)
📲 Mobile app packaging
🔄 Offline sync (опционально)

**Система готова для создания desktop и mobile приложений!** 🚀
