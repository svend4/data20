# Deployment Examples: Практические Примеры

## 📋 Содержание

1. [Quick Start - Desktop Embedded](#quick-start-desktop-embedded)
2. [Quick Start - Mobile Cloud](#quick-start-mobile-cloud)
3. [Production Web Deployment](#production-web-deployment)
4. [Сравнение Режимов](#сравнение-режимов)

---

# Quick Start - Desktop Embedded

## 🎯 Цель: Создать единое desktop приложение с embedded backend

### Шаг 1: Подготовка Backend для Упаковки

Создайте spec файл для PyInstaller:

**backend.spec**:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/tool_registry.py', '.'),
        ('backend/tool_runner.py', '.'),
        ('backend/auth.py', '.'),
        ('backend/database.py', '.'),
        ('backend/database_v2.py', '.'),
        ('backend/models.py', '.'),
        ('backend/config.py', '.'),
        ('backend/logger.py', '.'),
        ('backend/metrics.py', '.'),
        ('tools/', 'tools/'),
    ],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'pydantic',
        'jose',
        'passlib',
        'structlog',
        'prometheus_client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'celery',
        'redis',
        'psycopg2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='data20-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### Шаг 2: Сборка Backend

```bash
# Установить PyInstaller
pip install pyinstaller

# Собрать backend
pyinstaller backend.spec

# Результат:
# dist/data20-backend.exe (Windows)
# dist/data20-backend (Linux/Mac)
# Размер: ~40-60 MB
```

### Шаг 3: Интеграция в Electron

**desktop-app/electron/backend-launcher.js**:
```javascript
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');
const { app } = require('electron');

class BackendLauncher {
  constructor() {
    this.process = null;
    this.port = 8001;
    this.host = '127.0.0.1';
    this.baseUrl = `http://${this.host}:${this.port}`;
    this.isReady = false;
  }

  /**
   * Получить путь к backend executable
   */
  getExecutablePath() {
    const isDev = !app.isPackaged;

    if (isDev) {
      // Development: используем Python интерпретатор
      return {
        command: 'python',
        args: ['backend/server.py']
      };
    } else {
      // Production: используем упакованный executable
      const resourcePath = process.resourcesPath;
      const platform = process.platform;

      let exeName = 'data20-backend';
      if (platform === 'win32') exeName += '.exe';

      const exePath = path.join(resourcePath, 'backend', exeName);

      return {
        command: exePath,
        args: []
      };
    }
  }

  /**
   * Запустить backend process
   */
  async start() {
    console.log('🚀 Starting backend...');

    const { command, args } = this.getExecutablePath();

    // Путь к базе данных в user data
    const userDataPath = app.getPath('userData');
    const dbPath = path.join(userDataPath, 'data20.db');

    // Environment variables
    const env = {
      ...process.env,
      DEPLOYMENT_MODE: 'standalone',
      DATABASE_URL: `sqlite:///${dbPath}`,
      HOST: this.host,
      PORT: this.port.toString(),
      LOG_LEVEL: 'INFO'
    };

    console.log(`📦 Backend command: ${command} ${args.join(' ')}`);
    console.log(`📊 Database: ${dbPath}`);

    // Spawn process
    this.process = spawn(command, args, { env });

    // Логирование
    this.process.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    this.process.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });

    this.process.on('error', (error) => {
      console.error('❌ Backend process error:', error);
    });

    this.process.on('exit', (code, signal) => {
      console.log(`⚠️ Backend exited with code ${code}, signal ${signal}`);
      this.isReady = false;
    });

    // Ждём готовность
    await this.waitForReady();

    console.log('✅ Backend is ready!');
    this.isReady = true;

    return true;
  }

  /**
   * Ожидание готовности backend
   */
  async waitForReady(maxAttempts = 30, interval = 1000) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await axios.get(`${this.baseUrl}/health`, {
          timeout: 2000
        });

        if (response.status === 200) {
          return true;
        }
      } catch (error) {
        // Backend ещё не готов, ждём
        await new Promise(resolve => setTimeout(resolve, interval));
      }
    }

    throw new Error('Backend failed to start within timeout');
  }

  /**
   * Остановить backend
   */
  stop() {
    if (this.process) {
      console.log('🛑 Stopping backend...');
      this.process.kill('SIGTERM');

      // Форсированная остановка через 5 секунд
      setTimeout(() => {
        if (this.process && !this.process.killed) {
          console.log('⚠️ Force killing backend...');
          this.process.kill('SIGKILL');
        }
      }, 5000);

      this.process = null;
      this.isReady = false;
    }
  }

  /**
   * Перезапустить backend
   */
  async restart() {
    this.stop();
    await new Promise(resolve => setTimeout(resolve, 2000));
    await this.start();
  }

  /**
   * Проверить статус
   */
  async checkStatus() {
    try {
      const response = await axios.get(`${this.baseUrl}/health`, {
        timeout: 2000
      });
      return response.data;
    } catch (error) {
      return { status: 'offline', error: error.message };
    }
  }

  /**
   * Получить URL backend
   */
  getUrl() {
    return this.baseUrl;
  }
}

module.exports = BackendLauncher;
```

### Шаг 4: Обновление Main Process

**desktop-app/electron/main.js**:
```javascript
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const BackendLauncher = require('./backend-launcher');

let mainWindow = null;
let backendLauncher = null;

const isDev = !app.isPackaged;

/**
 * Создать главное окно
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false, // Показываем после загрузки
  });

  // Загрузка UI
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  // Показать когда готово
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Создать меню приложения
 */
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Restart Backend',
          click: async () => {
            await backendLauncher.restart();
          }
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            // Show about dialog
          }
        },
        {
          label: 'Backend Status',
          click: async () => {
            const status = await backendLauncher.checkStatus();
            console.log('Backend status:', status);
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Инициализация приложения
 */
app.on('ready', async () => {
  try {
    // 1. Запуск backend
    console.log('🚀 Starting Data20 Knowledge Base...');

    backendLauncher = new BackendLauncher();
    await backendLauncher.start();

    // 2. Создание UI
    createWindow();
    createMenu();

    console.log('✅ Application ready!');

  } catch (error) {
    console.error('❌ Failed to start application:', error);
    app.quit();
  }
});

/**
 * Все окна закрыты
 */
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * Активация (macOS)
 */
app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

/**
 * Завершение приложения
 */
app.on('before-quit', () => {
  console.log('🛑 Shutting down...');
  if (backendLauncher) {
    backendLauncher.stop();
  }
});

/**
 * IPC Handlers
 */
ipcMain.handle('get-backend-url', () => {
  return backendLauncher ? backendLauncher.getUrl() : null;
});

ipcMain.handle('check-backend-status', async () => {
  return backendLauncher ? await backendLauncher.checkStatus() : null;
});

ipcMain.handle('restart-backend', async () => {
  if (backendLauncher) {
    await backendLauncher.restart();
    return { success: true };
  }
  return { success: false, error: 'Backend not initialized' };
});
```

### Шаг 5: Конфигурация Builder

**desktop-app/electron-builder.yml**:
```yaml
appId: com.data20.knowledgebase
productName: Data20 Knowledge Base
copyright: Copyright © 2024

directories:
  output: dist
  buildResources: resources

files:
  - build/**/*
  - electron/**/*
  - node_modules/**/*
  - package.json

# Включить backend executable
extraResources:
  - from: ../dist/
    to: backend
    filter:
      - data20-backend*

# Windows
win:
  target:
    - target: nsis
      arch:
        - x64
    - target: portable
      arch:
        - x64
  icon: resources/icons/icon.ico
  artifactName: ${productName}-${version}-${arch}.${ext}

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: always
  createStartMenuShortcut: true
  menuCategory: true
  displayLanguageSelector: false

# macOS
mac:
  target:
    - target: dmg
      arch:
        - x64
        - arm64
    - target: zip
      arch:
        - x64
        - arm64
  icon: resources/icons/icon.icns
  category: public.app-category.productivity
  hardenedRuntime: true
  gatekeeperAssess: false
  entitlements: resources/entitlements.mac.plist
  entitlementsInherit: resources/entitlements.mac.plist

dmg:
  contents:
    - x: 130
      y: 220
    - x: 410
      y: 220
      type: link
      path: /Applications
  title: ${productName} ${version}
  icon: resources/icons/icon.icns

# Linux
linux:
  target:
    - target: AppImage
      arch:
        - x64
    - target: deb
      arch:
        - x64
    - target: rpm
      arch:
        - x64
  icon: resources/icons/
  category: Office
  synopsis: Knowledge Base Management System
  description: Data20 Knowledge Base - Advanced data analysis and management tool

appImage:
  license: MIT

deb:
  depends:
    - gconf2
    - gconf-service
    - libnotify4
    - libappindicator1
    - libxtst6
    - libnss3

# Сжатие
compression: maximum
```

### Шаг 6: Build Script

**desktop-app/build-all.sh**:
```bash
#!/bin/bash

set -e

echo "======================================"
echo "  Building Data20 Desktop App"
echo "======================================"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Сборка Backend
echo ""
echo -e "${YELLOW}📦 Step 1: Building Python Backend${NC}"
echo "--------------------------------------"

cd ..
if [ -f backend.spec ]; then
    pyinstaller backend.spec
    echo -e "${GREEN}✅ Backend built successfully${NC}"
else
    echo -e "${RED}❌ backend.spec not found${NC}"
    exit 1
fi

# 2. Сборка React Frontend
echo ""
echo -e "${YELLOW}⚛️  Step 2: Building React Frontend${NC}"
echo "--------------------------------------"

cd desktop-app

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build React
npm run build:react

echo -e "${GREEN}✅ React built successfully${NC}"

# 3. Сборка Electron
echo ""
echo -e "${YELLOW}🔌 Step 3: Building Electron App${NC}"
echo "--------------------------------------"

# Определить платформу
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PLATFORM="win"
else
    echo -e "${RED}❌ Unsupported platform: $OSTYPE${NC}"
    exit 1
fi

# Build для текущей платформы или для всех
if [ "$1" == "all" ]; then
    echo "Building for all platforms..."
    electron-builder -mwl
elif [ "$1" == "mac" ]; then
    electron-builder --mac
elif [ "$1" == "win" ]; then
    electron-builder --win
elif [ "$1" == "linux" ]; then
    electron-builder --linux
else
    echo "Building for current platform: $PLATFORM"
    electron-builder --$PLATFORM
fi

echo ""
echo -e "${GREEN}✅ Build completed!${NC}"
echo ""
echo "======================================"
echo "  📦 Artifacts:"
echo "======================================"
ls -lh dist/*.{exe,dmg,AppImage,deb,rpm} 2>/dev/null || echo "No installers found"
echo ""
echo -e "${GREEN}🎉 All done!${NC}"
```

### Шаг 7: Сборка

```bash
# Дать права на выполнение
chmod +x build-all.sh

# Собрать для текущей платформы
./build-all.sh

# Собрать для всех платформ
./build-all.sh all

# Собрать для конкретной платформы
./build-all.sh win
./build-all.sh mac
./build-all.sh linux
```

### Результат

```
dist/
├── Data20-Setup-1.0.0.exe           # Windows installer (NSIS)
├── Data20-1.0.0-portable.exe        # Windows portable
├── Data20-1.0.0.dmg                 # macOS installer
├── Data20-1.0.0-arm64.dmg          # macOS ARM
├── Data20-1.0.0.AppImage           # Linux portable
├── data20_1.0.0_amd64.deb          # Debian/Ubuntu
└── data20-1.0.0.x86_64.rpm         # RedHat/Fedora
```

**Размеры**:
- Windows: ~180-220 MB
- macOS: ~170-200 MB
- Linux: ~160-190 MB

---

# Quick Start - Mobile Cloud

## 📱 Развертывание Mobile App с Cloud Backend

### Вариант 1: Backend на облачном сервере

#### Шаг 1: Развернуть Backend на облаке

**Используя Heroku**:
```bash
# Установить Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Логин
heroku login

# Создать приложение
heroku create data20-api

# Добавить PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Добавить Redis
heroku addons:create heroku-redis:hobby-dev

# Deploy
git push heroku main

# Получить URL
heroku info
# https://data20-api.herokuapp.com
```

**Используя Railway**:
```bash
# Install Railway CLI
npm install -g railway

# Login
railway login

# Init project
railway init

# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis

# Deploy
railway up

# Get URL
railway domain
# https://data20-api-production.up.railway.app
```

**Используя DigitalOcean App Platform**:
```yaml
# .do/app.yaml
name: data20-api
services:
  - name: backend
    github:
      repo: your-username/data20
      branch: main
    source_dir: /backend
    run_command: uvicorn server:app --host 0.0.0.0 --port 8080
    envs:
      - key: DEPLOYMENT_MODE
        value: production
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
    http_port: 8080

databases:
  - name: db
    engine: PG
    version: "14"
```

```bash
# Deploy
doctl apps create --spec .do/app.yaml
```

#### Шаг 2: Настроить Flutter App

**mobile-app/lib/config/api_config.dart**:
```dart
class ApiConfig {
  // Production URL (из вашего облачного провайдера)
  static const String productionUrl = 'https://data20-api.herokuapp.com';

  // Development URL (локальный сервер)
  static const String developmentUrl = 'http://192.168.1.100:8001';

  // Текущий режим
  static const bool isProduction = bool.fromEnvironment('PRODUCTION', defaultValue: false);

  // Получить base URL
  static String get baseUrl => isProduction ? productionUrl : developmentUrl;
}
```

**mobile-app/lib/services/api_service.dart**:
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/api_config.dart';

class ApiService {
  late String _baseUrl;
  String? _accessToken;

  ApiService() {
    _baseUrl = ApiConfig.baseUrl;
    print('📡 API Service initialized with URL: $_baseUrl');
  }

  // Изменить URL во время runtime (для настроек)
  void setBaseUrl(String url) {
    _baseUrl = url;
    print('📡 API URL changed to: $_baseUrl');
  }

  // Остальные методы...
  Future<List<Tool>> getTools() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/api/tools'),
      headers: _getHeaders(),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body) as List;
      return data.map((json) => Tool.fromJson(json)).toList();
    } else {
      throw ApiException('Failed to load tools', response.statusCode);
    }
  }

  Map<String, String> _getHeaders() {
    final headers = {
      'Content-Type': 'application/json',
    };

    if (_accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }

    return headers;
  }
}
```

#### Шаг 3: Build Flutter App

**Android**:
```bash
# Development build (localhost)
flutter build apk --debug

# Production build (cloud backend)
flutter build apk --release --dart-define=PRODUCTION=true

# Результат:
# build/app/outputs/flutter-apk/app-release.apk
```

**iOS**:
```bash
# Development
flutter build ios --debug

# Production
flutter build ios --release --dart-define=PRODUCTION=true

# Открыть в Xcode
open ios/Runner.xcworkspace
# Archive → Distribute to App Store
```

#### Шаг 4: Опциональные настройки

**Экран настроек для смены backend URL**:

**mobile-app/lib/screens/settings_screen.dart**:
```dart
class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final url = prefs.getString('backend_url') ?? ApiConfig.baseUrl;
    _urlController.text = url;
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();

    // Проверить валидность URL
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      _showError('URL must start with http:// or https://');
      return;
    }

    // Проверить доступность backend
    try {
      final apiService = context.read<ApiService>();
      apiService.setBaseUrl(url);

      // Тест запрос
      await apiService.getTools();

      // Сохранить
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('backend_url', url);

      _showSuccess('Backend URL updated successfully!');
    } catch (e) {
      _showError('Failed to connect to backend: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                labelText: 'Backend URL',
                hintText: 'https://api.yourserver.com',
                helperText: 'Enter the URL of your backend server',
              ),
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _saveUrl,
              child: Text('Save'),
            ),
            SizedBox(height: 16),
            Text(
              'Default URLs:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            ListTile(
              title: Text('Production'),
              subtitle: Text(ApiConfig.productionUrl),
              trailing: IconButton(
                icon: Icon(Icons.content_copy),
                onPressed: () {
                  _urlController.text = ApiConfig.productionUrl;
                },
              ),
            ),
            ListTile(
              title: Text('Development'),
              subtitle: Text(ApiConfig.developmentUrl),
              trailing: IconButton(
                icon: Icon(Icons.content_copy),
                onPressed: () {
                  _urlController.text = ApiConfig.developmentUrl;
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

# Production Web Deployment

## 🌐 Развертывание Web приложения на Production

### Архитектура

```
┌──────────────┐      HTTPS      ┌──────────────┐
│   Browser    │ ──────────────> │   Cloudflare │
└──────────────┘                  │   CDN        │
                                  └──────┬───────┘
                                         │
                                  ┌──────▼───────┐
                                  │    Nginx     │
                                  │ Load Balancer│
                                  └──────┬───────┘
                                         │
                         ┌───────────────┴────────────────┐
                         │                                │
                  ┌──────▼──────┐                 ┌───────▼──────┐
                  │   Static    │                 │   API        │
                  │   Files     │                 │   Server     │
                  │   (React)   │                 │   (FastAPI)  │
                  │             │                 │              │
                  │   S3/CDN    │                 │   EC2/Cloud  │
                  └─────────────┘                 └───────┬──────┘
                                                          │
                                                  ┌───────┴──────┐
                                                  │              │
                                           ┌──────▼─────┐ ┌──────▼──────┐
                                           │ PostgreSQL │ │   Redis     │
                                           │    RDS     │ │ ElastiCache │
                                           └────────────┘ └─────────────┘
```

### Опция 1: AWS Deployment

#### Backend на EC2:

**1. Создать EC2 instance**:
```bash
# Выбрать:
# - Ubuntu 22.04 LTS
# - t3.medium (2 vCPU, 4GB RAM)
# - 20GB SSD
```

**2. Настроить сервер**:
```bash
# SSH в instance
ssh -i key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# Установить зависимости
sudo apt update
sudo apt install -y python3-pip python3-venv nginx postgresql-client redis-tools

# Клонировать репозиторий
git clone https://github.com/yourusername/data20.git
cd data20

# Создать venv
python3 -m venv venv
source venv/bin/activate

# Установить requirements
pip install -r backend/requirements.txt
pip install gunicorn

# Настроить environment
cat > .env << EOF
DEPLOYMENT_MODE=production
DATABASE_URL=postgresql://user:password@rds-endpoint:5432/data20
REDIS_URL=redis://elasticache-endpoint:6379
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Запустить с Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:app \
  --bind 0.0.0.0:8001 \
  --access-logfile /var/log/gunicorn-access.log \
  --error-logfile /var/log/gunicorn-error.log \
  --daemon
```

**3. Настроить Nginx**:
```nginx
# /etc/nginx/sites-available/data20

upstream backend {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # API endpoints
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /auth/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Metrics (защищённые)
    location /metrics {
        allow 10.0.0.0/8;  # VPC only
        deny all;
        proxy_pass http://backend;
    }
}
```

```bash
# Активировать конфигурацию
sudo ln -s /etc/nginx/sites-available/data20 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Получить SSL сертификаты
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

#### Frontend на S3 + CloudFront:

**1. Build React app**:
```bash
cd webapp-react

# Production build
VITE_API_URL=https://api.yourdomain.com npm run build

# Результат в build/
```

**2. Создать S3 bucket**:
```bash
aws s3 mb s3://data20-frontend
```

**3. Upload files**:
```bash
aws s3 sync build/ s3://data20-frontend/ --acl public-read
```

**4. Настроить CloudFront**:
```json
{
  "Origins": [{
    "Id": "S3-data20-frontend",
    "DomainName": "data20-frontend.s3.amazonaws.com",
    "S3OriginConfig": {
      "OriginAccessIdentity": ""
    }
  }],
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-data20-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "Compress": true
  },
  "CustomErrorResponses": [{
    "ErrorCode": 404,
    "ResponsePagePath": "/index.html",
    "ResponseCode": 200
  }]
}
```

**5. DNS настройки**:
```
# Route 53
yourdomain.com          → CloudFront Distribution
api.yourdomain.com      → EC2 Elastic IP
```

---

### Опция 2: Docker + Docker Compose (Универсальный)

**docker-compose.production.yml**:
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: data20-postgres
    environment:
      POSTGRES_USER: data20
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: data20
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: data20-redis
    networks:
      - backend

  # Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: data20-backend
    environment:
      DEPLOYMENT_MODE: production
      DATABASE_URL: postgresql://data20:${DB_PASSWORD}@postgres:5432/data20
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - backend
      - frontend

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: data20-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./webapp-react/build:/usr/share/nginx/html:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - backend
    networks:
      - frontend

  # Certbot для SSL
  certbot:
    image: certbot/certbot
    container_name: data20-certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

networks:
  backend:
  frontend:

volumes:
  postgres_data:
```

**Запуск**:
```bash
# Создать .env файл
cat > .env << EOF
DB_PASSWORD=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Запустить
docker-compose -f docker-compose.production.yml up -d

# Логи
docker-compose -f docker-compose.production.yml logs -f

# Остановить
docker-compose -f docker-compose.production.yml down
```

---

# Сравнение Режимов

## Таблица решений для разных сценариев

| Сценарий | Решение | Backend Location | Сложность | Стоимость/мес |
|----------|---------|------------------|-----------|---------------|
| **Индивидуальный Desktop** | Electron Embedded | Local (embedded) | ⭐⭐⭐⭐ | $0 |
| **Командная разработка** | Web (localhost) | Local (manual) | ⭐⭐ | $0 |
| **Малый бизнес (5-20 юзеров)** | Docker Compose | VPS (DigitalOcean) | ⭐⭐⭐ | $15-40 |
| **Средний бизнес (20-100)** | Kubernetes | Cloud (managed) | ⭐⭐⭐⭐⭐ | $100-300 |
| **Enterprise (100+)** | Multi-region K8s | AWS/GCP multi-zone | ⭐⭐⭐⭐⭐⭐ | $500+ |
| **Mobile индивидуально** | Flutter + Cloud free tier | Heroku/Railway | ⭐⭐⭐ | $0-10 |
| **Mobile team** | Flutter + Cloud | AWS/GCP | ⭐⭐⭐⭐ | $50-150 |

## Рекомендации по выбору

**Выбирайте Desktop Embedded если**:
- ✅ Один пользователь
- ✅ Нужен полный offline режим
- ✅ Важна приватность данных
- ✅ Не хотите платить за хостинг

**Выбирайте Web (Cloud) если**:
- ✅ Команда пользователей
- ✅ Нужна синхронизация между устройствами
- ✅ Важна доступность из любого места
- ✅ Готовы платить за хостинг

**Выбирайте Mobile + Cloud если**:
- ✅ Работа в поле/в дороге
- ✅ Нужна синхронизация
- ✅ Push уведомления важны
- ✅ Готовы к App Store review

**Выбирайте Hybrid (будущее) если**:
- ✅ Нужна работа offline и online
- ✅ Multi-device sync
- ✅ Максимальная гибкость
- ✅ Готовы к сложной архитектуре
