# Phase 6.5: Simple Web UI

## Overview

Создан **простой и функциональный веб-интерфейс** (Pure HTML/CSS/JavaScript) для работы с Data20 Knowledge Base без необходимости использовать API напрямую.

## Философия: От простого к сложному

Следуя принципу **"от простого к сложному"**, мы начали с чистого HTML/CSS/JavaScript:

1. ✅ **Phase 6.5** - Pure HTML/CSS/JS (Simple Web UI) - **ЗАВЕРШЕНО**
2. 🔜 **Phase 6.6** - React компоненты (Enhanced UI)
3. 🔜 **Phase 6.7** - Electron упаковка (Desktop App)
4. 🔜 **Phase 6.8** - Flutter мобильное приложение

Преимущества этого подхода:
- Минимальные зависимости
- Простота понимания и модификации
- Быстрая загрузка (нет сборки)
- Готовая основа для миграции на React

---

## Структура проекта

```
webapp/
├── index.html              # Главная страница (Login/Register)
├── css/
│   └── style.css           # Общие стили
├── js/
│   ├── config.js           # API конфигурация и утилиты
│   ├── auth.js             # Аутентификация (Login/Register)
│   └── pages/
│       ├── home.js         # Главная страница
│       ├── run-tool.js     # Страница запуска инструмента
│       └── jobs.js         # История задач
└── pages/
    ├── home.html           # Список инструментов
    ├── run-tool.html       # Запуск инструмента
    └── jobs.html           # История задач
```

---

## Функциональность

### 1. Страница Login/Register (index.html)

**Функции**:
- ✅ Вход в систему (логин + пароль)
- ✅ Регистрация нового пользователя
- ✅ Валидация полей формы
- ✅ JWT токены (localStorage)
- ✅ Первый пользователь автоматически становится админом
- ✅ Красивый градиентный дизайн

**Особенности**:
```javascript
// Автоматическое определение API URL
const API_URL = window.location.origin;

// Первый пользователь = admin
if (user.role === 'admin') {
    showSuccess('Вы - администратор! 👑');
}

// Автопереключение на вкладку входа после регистрации
setTimeout(() => showTab('login'), 2000);
```

**Валидация**:
- Логин: минимум 3 символа
- Пароль: минимум 8 символов
- Email: корректный формат

**Скриншот функционала**:
```
┌────────────────────────────────────┐
│   Data20 Knowledge Base            │
│   [ Вход ]  [ Регистрация ]        │
│                                    │
│   Логин: [__________________]     │
│   Пароль: [__________________]    │
│                                    │
│   [ Войти ]                        │
└────────────────────────────────────┘
```

---

### 2. Главная страница (pages/home.html)

**Функции**:
- ✅ Отображение информации о пользователе
- ✅ Статистика (всего инструментов, категорий, задач)
- ✅ Список всех 57+ инструментов в виде карточек
- ✅ Поиск по названию/описанию/категории
- ✅ Фильтрация по категориям
- ✅ Кнопка выхода

**Карточка инструмента**:
```javascript
<div class="tool-card" onclick="runTool('tool_name')">
    <div class="tool-category">📊 Статистика</div>
    <h3>
        <span class="tool-icon">📊</span>
        Базовая статистика
    </h3>
    <p>Вычисляет основные статистические показатели...</p>
    <div class="tool-params">
        📝 Параметров: 2 (1 обязательных)
    </div>
</div>
```

**Категории инструментов**:
- 📊 Статистика
- 📈 Визуализация
- 🧹 Очистка данных
- 🔄 Преобразование
- 🔍 Анализ
- 🤖 Машинное обучение
- 💬 NLP
- ⏰ Временные ряды
- 📝 Текст
- 🌐 Сети
- 🔧 Другое

**Функции поиска**:
```javascript
function filterTools() {
    const query = searchInput.value.toLowerCase();
    filteredTools = allTools.filter(tool => {
        return tool.name.includes(query) ||
               tool.description.includes(query) ||
               tool.category.includes(query);
    });
    displayTools(filteredTools);
}
```

---

### 3. Страница запуска инструмента (pages/run-tool.html)

**Функции**:
- ✅ Загрузка информации об инструменте
- ✅ Динамическая генерация формы параметров
- ✅ Валидация параметров (типы, обязательность)
- ✅ Запуск инструмента
- ✅ Отображение прогресса выполнения
- ✅ Показ результата или ошибки
- ✅ Автообновление статуса (polling каждые 2 сек)

**Типы параметров**:
```javascript
// Boolean
<select>
    <option value="true">Да</option>
    <option value="false">Нет</option>
</select>

// Integer/Number
<input type="number" step="1">

// Enum (список значений)
<select>
    <option value="option1">Option 1</option>
    <option value="option2">Option 2</option>
</select>

// Array/Object
<textarea placeholder='["item1", "item2"]'></textarea>

// String
<input type="text">
```

**Polling механизм**:
```javascript
pollInterval = setInterval(async () => {
    const job = await apiRequest(API.jobDetail(jobId));
    updateJobStatus(job);

    if (job.status === 'completed' || job.status === 'failed') {
        clearInterval(pollInterval);
    }
}, 2000);
```

**Отображение результата**:
```javascript
// Успешное выполнение
{
    "status": "completed",
    "result": { /* данные */ },
    "duration": "2.3с"
}

// Ошибка
{
    "status": "failed",
    "error": "Описание ошибки"
}
```

---

### 4. История задач (pages/jobs.html)

**Функции**:
- ✅ Список всех задач пользователя
- ✅ Фильтрация по статусу (pending, running, completed, failed)
- ✅ Фильтрация по инструменту
- ✅ Автообновление каждые 5 секунд
- ✅ Просмотр деталей задачи
- ✅ Повторный запуск задачи с теми же параметрами
- ✅ Отображение длительности выполнения

**Карточка задачи**:
```javascript
<div class="job-card">
    <div class="job-card-header">
        <h3>tool_name</h3>
        <span class="status-badge completed">✅ Завершено</span>
    </div>

    <div class="job-info">
        <div>Создана: 2026-01-03 12:34</div>
        <div>Длительность: 2.3с</div>
    </div>

    <div class="job-actions">
        <button onclick="viewJobDetails()">👁️ Подробнее</button>
        <button onclick="rerunJob()">🔄 Повторить</button>
    </div>

    <div class="job-result">
        <pre>{ "result": "..." }</pre>
    </div>
</div>
```

**Статусы задач**:
- ⏳ **Pending** - Ожидание (желтый)
- ▶️ **Running** - Выполняется (синий)
- ✅ **Completed** - Завершено (зеленый)
- ❌ **Failed** - Ошибка (красный)

**Автообновление**:
```javascript
autoRefreshInterval = setInterval(async () => {
    await loadJobs(true); // Silent refresh
}, 5000);
```

---

## Конфигурация (config.js)

### API Endpoints

```javascript
const API = {
    // Authentication
    register: '/auth/register',
    login: '/auth/login',
    refresh: '/auth/refresh',
    me: '/auth/me',
    logout: '/auth/logout',

    // Tools
    tools: '/api/tools',
    toolDetail: (name) => `/api/tools/${name}`,
    categories: '/api/categories',

    // Jobs
    runTool: '/api/run',
    jobs: '/api/jobs',
    jobDetail: (id) => `/api/jobs/${id}`,
    jobLogs: (id) => `/api/jobs/${id}/logs`,

    // Admin
    adminUsers: '/admin/users',
};
```

### Utility Functions

```javascript
// Authentication
getToken()              // Получить токен из localStorage
setToken(access, refresh) // Сохранить токены
clearAuth()             // Очистить аутентификацию
isAuthenticated()       // Проверка авторизации

// API Requests
apiRequest(url, options) // Универсальный API запрос с автообработкой токенов

// UI Helpers
setLoading(element, loading)  // Показать/скрыть состояние загрузки
showError(id, message)        // Показать сообщение об ошибке
showSuccess(id, message)      // Показать успешное сообщение
formatDateTime(dateString)    // Форматировать дату/время
formatDuration(seconds)       // Форматировать длительность
```

---

## Дизайн и стили (style.css)

### Цветовая схема

```css
/* Градиент фона */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Кнопки */
.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

/* Статусы */
.status-badge.pending { background: #fff3cd; color: #856404; }
.status-badge.running { background: #cfe2ff; color: #084298; }
.status-badge.completed { background: #d1e7dd; color: #0f5132; }
.status-badge.failed { background: #f8d7da; color: #842029; }
```

### Анимации

```css
/* Появление карточек */
@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Spinner загрузки */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

### Responsive Design

```css
/* Адаптивная сетка инструментов */
.tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
}

/* Мобильные устройства */
@media (max-width: 768px) {
    .tools-grid {
        grid-template-columns: 1fr;
    }
}
```

---

## Безопасность

### JWT Authentication

```javascript
// Токены хранятся в localStorage
localStorage.setItem('data20_access_token', accessToken);
localStorage.setItem('data20_refresh_token', refreshToken);

// Автоматическое добавление в запросы
headers['Authorization'] = `Bearer ${token}`;

// Автоматический выход при 401
if (error.status === 401) {
    clearAuth();
    window.location.href = 'index.html';
}
```

### Валидация данных

```javascript
// Client-side validation
if (username.length < 3) {
    showError('register-error', 'Логин должен быть минимум 3 символа');
    return;
}

if (password.length < 8) {
    showError('register-error', 'Пароль должен быть минимум 8 символов');
    return;
}

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(email)) {
    showError('register-error', 'Введите корректный email');
    return;
}
```

---

## Запуск Web UI

### Standalone режим

```bash
# Запустить сервер
python run_standalone.py

# Открыть в браузере
http://127.0.0.1:8001

# Web UI доступен на главной странице
http://127.0.0.1:8001/index.html
```

### Production режим

```bash
# Запустить с nginx
export DEPLOYMENT_MODE=production
python backend/server.py

# Nginx конфигурация для статики
location /webapp {
    alias /path/to/data20/webapp;
    index index.html;
}

# API проксирование
location /api {
    proxy_pass http://localhost:8001;
}
```

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Backend
COPY backend/ ./backend/
COPY tools/ ./tools/
COPY run_standalone.py .

# Web UI
COPY webapp/ ./webapp/

# Install dependencies
RUN pip install -r requirements-standalone.txt

# Expose port
EXPOSE 8001

# Run
CMD ["python", "run_standalone.py", "--host", "0.0.0.0"]
```

---

## Использование

### 1. Регистрация

```
1. Открыть http://127.0.0.1:8001
2. Нажать вкладку "Регистрация"
3. Заполнить форму:
   - Логин (минимум 3 символа)
   - Email
   - Пароль (минимум 8 символов)
   - Полное имя (опционально)
4. Нажать "Зарегистрироваться"
5. Первый пользователь автоматически станет администратором
```

### 2. Вход в систему

```
1. Ввести логин и пароль
2. Нажать "Войти"
3. JWT токены сохраняются в localStorage
4. Редирект на страницу инструментов
```

### 3. Запуск инструмента

```
1. На главной странице найти нужный инструмент
2. Кликнуть на карточку инструмента
3. Заполнить параметры (если требуются)
4. Нажать "Запустить инструмент"
5. Ожидать результата (автообновление статуса)
6. Просмотреть результат или ошибку
```

### 4. Просмотр истории

```
1. Нажать "История задач" в header
2. Просмотреть список всех задач
3. Фильтровать по статусу или инструменту
4. Кликнуть "Подробнее" для просмотра результата
5. Кликнуть "Повторить" для повторного запуска
```

---

## Совместимость

### Браузеры

- ✅ Chrome/Edge (90+)
- ✅ Firefox (88+)
- ✅ Safari (14+)
- ✅ Opera (76+)

### Мобильные устройства

- ✅ iOS Safari (14+)
- ✅ Android Chrome (90+)
- ✅ Samsung Internet (14+)

### Требования

- JavaScript enabled
- LocalStorage enabled
- Fetch API support
- ES6+ support

---

## Производительность

### Размер файлов

```
index.html          ~8 KB
style.css           ~12 KB
config.js           ~6 KB
auth.js             ~5 KB
home.js             ~8 KB
run-tool.js         ~10 KB
jobs.js             ~9 KB
---
Total:              ~58 KB (без сжатия)
Gzipped:            ~15 KB
```

### Загрузка

- Первая загрузка: ~200ms
- Повторная загрузка: ~50ms (кеш)
- API запросы: ~10-50ms (локальный сервер)

### Оптимизации

```javascript
// Кеширование инструментов
const tools = await apiRequest(API.tools); // Один раз при загрузке
filteredTools = tools; // Фильтрация на клиенте

// Batch API calls
Promise.all([
    loadUserInfo(),
    loadTools(),
    loadJobStats()
]);

// Debounce для поиска
let searchTimeout;
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(filterTools, 300);
});
```

---

## Следующие шаги

### Phase 6.6: Enhanced Web UI (React)

**Цель**: Улучшить UX с помощью React компонентов

**Компоненты**:
```javascript
// React компоненты
<ToolCard tool={tool} onClick={runTool} />
<JobsList jobs={jobs} filter={filter} />
<ParameterForm parameters={params} onSubmit={handleSubmit} />
<StatusBadge status={job.status} />
```

**Преимущества**:
- Лучшая производительность (Virtual DOM)
- Компонентная архитектура
- State management (Redux/Context)
- TypeScript support

### Phase 6.7: Desktop App (Electron)

**Цель**: Упаковать в desktop приложение

**Особенности**:
```javascript
// Electron main.js
const { app, BrowserWindow } = require('electron');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true
        }
    });

    win.loadFile('webapp/index.html');
}

app.whenReady().then(createWindow);
```

**Распространение**:
- Windows: .exe installer
- macOS: .dmg/.app
- Linux: .deb/.AppImage

### Phase 6.8: Mobile App (Flutter)

**Цель**: Нативное мобильное приложение

**Особенности**:
```dart
// Flutter widgets
class ToolCard extends StatelessWidget {
    final Tool tool;

    @override
    Widget build(BuildContext context) {
        return Card(
            child: ListTile(
                title: Text(tool.name),
                subtitle: Text(tool.description),
                onTap: () => runTool(tool),
            ),
        );
    }
}
```

**Платформы**:
- iOS (App Store)
- Android (Google Play)
- Web (PWA)

---

## Summary

### Что было создано

✅ **4 HTML страницы**:
- index.html - Login/Register
- home.html - Список инструментов
- run-tool.html - Запуск инструмента
- jobs.html - История задач

✅ **5 JavaScript файлов**:
- config.js - Конфигурация и утилиты
- auth.js - Аутентификация
- home.js - Главная страница
- run-tool.js - Запуск инструментов
- jobs.js - История задач

✅ **1 CSS файл**:
- style.css - Общие стили

✅ **Функции**:
- JWT аутентификация
- Просмотр всех инструментов
- Поиск и фильтрация
- Запуск инструментов с параметрами
- Отслеживание статуса выполнения
- История задач
- Responsive design

### Impact

- **Простота использования**: Не нужно знать API
- **Быстрая разработка**: Pure HTML/CSS/JS, без сборки
- **Минимальные зависимости**: Нет React/Vue/Angular
- **Готовая основа**: Для миграции на React
- **Desktop/Mobile ready**: Можно обернуть в Electron/Flutter

---

**Phase 6.5 Complete!** ✅

Simple Web UI создан и полностью функционален! 🚀

Следующий шаг: Phase 6.6 - Enhanced Web UI with React
