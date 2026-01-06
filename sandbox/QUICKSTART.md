# 🚀 Sandbox Quick Start Guide

Быстрое руководство по работе в экспериментальной среде.

---

## ⚡ Быстрый Старт

### 1️⃣ Выберите Sandbox

```bash
# Для UI экспериментов (Phase 9.3)
cd /home/user/data20/sandbox/phase-9.3-ui-experiments/

# Для тестирования (Phase 9.2)
cd /home/user/data20/sandbox/phase-9.2-testing/
```

### 2️⃣ Загрузите в Браузер

#### Chrome / Edge
1. Откройте `chrome://extensions/`
2. Включите **Developer mode** (правый верхний угол)
3. Нажмите **Load unpacked**
4. Выберите папку sandbox проекта

#### Firefox
1. Откройте `about:debugging#/runtime/this-firefox`
2. Нажмите **Load Temporary Add-on**
3. Выберите `manifest.json` из папки sandbox

### 3️⃣ Начните Экспериментировать

```bash
# Откройте нужные файлы
nano src/popup/popup.html
nano src/popup/popup.js
nano public/popup.html

# После изменений:
# Chrome: Нажмите "Reload" на странице расширения
# Firefox: Нажмите "Reload" в about:debugging
```

---

## 📁 Структура Sandbox Проектов

### Phase 9.3 UI Experiments
```
sandbox/phase-9.3-ui-experiments/
├── EXPERIMENTS.md           # Журнал экспериментов
├── src/
│   ├── popup/
│   │   ├── popup.html      # UI компоненты
│   │   └── popup.js        # Логика popup
│   ├── background/
│   │   ├── background.js   # Service worker
│   │   └── smart-router.js # Routing logic
│   └── utils/
│       └── storage.js      # Storage utilities
└── public/
    ├── popup.html          # Main popup file
    └── manifest.json       # Extension manifest
```

### Phase 9.2 Testing
```
sandbox/phase-9.2-testing/
├── TESTING.md              # План тестирования
├── tests/
│   ├── unit/              # Unit тесты
│   ├── integration/       # Integration тесты
│   ├── e2e/              # E2E тесты
│   └── performance/      # Performance тесты
├── mocks/                # Mock данные
└── fixtures/             # Test fixtures
```

---

## 🎯 Типичные Сценарии

### Сценарий 1: Добавить Новую Вкладку в UI

```bash
# 1. Открыть popup.html
cd sandbox/phase-9.3-ui-experiments/
nano public/popup.html

# 2. Добавить кнопку таба
# <button class="tab" data-tab="newtab">New Feature</button>

# 3. Добавить контент таба
# <div class="tab-content" id="newtab-tab">
#   <!-- Ваш контент -->
# </div>

# 4. Обновить popup.js для обработки
nano src/popup/popup.js

# 5. Перезагрузить расширение в браузере

# 6. Документировать в EXPERIMENTS.md
nano EXPERIMENTS.md
```

### Сценарий 2: Добавить График Метрик

```bash
# 1. Установить Chart.js (или другую библиотеку)
# Скачать в sandbox или использовать CDN

# 2. Добавить в popup.html
# <canvas id="metrics-chart"></canvas>

# 3. Инициализировать график в popup.js
nano src/popup/popup.js
# const ctx = document.getElementById('metrics-chart');
# const chart = new Chart(ctx, {...});

# 4. Подключить данные из Performance Monitor

# 5. Тестировать и документировать
```

### Сценарий 3: Протестировать Smart Router

```bash
cd sandbox/phase-9.2-testing/

# 1. Создать тестовый файл
mkdir -p tests/unit/
nano tests/unit/smart-router.test.js

# 2. Написать тесты
# describe('SmartRouter', () => {
#   test('routes simple tools locally', async () => {...});
# });

# 3. Запустить тесты
npm test

# 4. Проверить coverage
npm run test:coverage
```

---

## 🔧 Полезные Команды

### Просмотр Логов Расширения

**Chrome**:
```bash
# 1. Откройте расширение (click icon)
# 2. Правый клик на popup → Inspect
# 3. Console tab для логов popup
# 4. chrome://extensions/ → "background page" для service worker
```

**Firefox**:
```bash
# 1. about:debugging#/runtime/this-firefox
# 2. Нажмите "Inspect" под расширением
# 3. Console tab для логов
```

### Сброс Состояния

```javascript
// В консоли расширения:

// Очистить IndexedDB
indexedDB.deleteDatabase('data20-extension');

// Очистить Chrome Storage
chrome.storage.local.clear();

// Перезагрузить расширение
chrome.runtime.reload();
```

### Проверка Производительности

```javascript
// В консоли popup:

// Замерить время выполнения
console.time('tool-execution');
await executeTool('calculate_reading_time', {text: '...'});
console.timeEnd('tool-execution');

// Проверить память
console.log(performance.memory);
```

---

## 📊 Мониторинг Экспериментов

### Что Отслеживать

1. **Производительность**
   - Время загрузки popup
   - Время выполнения инструментов
   - Использование памяти

2. **UX Метрики**
   - Количество кликов для задачи
   - Время выполнения типичного flow
   - Визуальная ясность

3. **Ошибки**
   - JavaScript errors в console
   - Failed network requests
   - Storage errors

### Инструменты

- **Chrome DevTools**: Performance, Memory, Network tabs
- **Firefox DevTools**: Performance, Memory, Storage tabs
- **Lighthouse**: PWA и performance аудит
- **Console logs**: Детальное логирование

---

## ⚠️ Важные Правила

### ✅ МОЖНО (DO)
- Экспериментировать с любыми идеями
- Ломать код в sandbox (это для этого!)
- Пробовать новые библиотеки
- Создавать радикальные изменения
- Делать множество вариантов

### ❌ НЕЛЬЗЯ (DON'T)
- Изменять основной `browser-extension/` напрямую
- Коммитить sandbox код без ревью
- Удалять успешные эксперименты
- Использовать sandbox для production

---

## 🔄 Цикл Эксперимента

```
1. ИДЕЯ
   ↓
2. ПРОТОТИП в sandbox
   ↓
3. ТЕСТИРОВАНИЕ
   ↓
4. ДОКУМЕНТИРОВАНИЕ в EXPERIMENTS.md
   ↓
5. РЕВЬЮ
   ↓
6a. SUCCESS → Интеграция в production
   или
6b. FAIL → Архивировать и учиться
```

---

## 📚 Дополнительные Ресурсы

### Документация
- [Chrome Extension APIs](https://developer.chrome.com/docs/extensions/)
- [Firefox Extension APIs](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
- [WebAssembly](https://webassembly.org/)
- [Pyodide](https://pyodide.org/)

### Инструменты
- [Chrome DevTools](https://developers.google.com/web/tools/chrome-devtools)
- [web-ext](https://github.com/mozilla/web-ext) - Firefox extension CLI
- [Extension Reloader](https://chrome.google.com/webstore/detail/extensions-reloader/) - Auto-reload

### Библиотеки UI
- [Chart.js](https://www.chartjs.org/) - Графики
- [Lit](https://lit.dev/) - Web components
- [Tailwind CSS](https://tailwindcss.com/) - Utility CSS

---

## 💡 Советы

### Быстрая Итерация
- Используйте hot reload (web-ext для Firefox)
- Держите DevTools открытыми
- Тестируйте в одном браузере сначала

### Отладка
- Используйте `console.log()` обильно
- Breakpoints в DevTools
- Network tab для API calls
- Storage tab для IndexedDB

### Производительность
- Проверяйте Memory tab регулярно
- Используйте Performance recording
- Benchmark перед и после изменений

---

## 🆘 Частые Проблемы

### Расширение не загружается
```bash
# Проверьте manifest.json на ошибки
# Проверьте paths в manifest
# Посмотрите console errors на странице расширения
```

### Service Worker не работает
```bash
# Проверьте background.js на syntax errors
# Откройте service worker DevTools
# Проверьте Chrome://serviceworker-internals/
```

### IndexedDB ошибки
```bash
# Очистить базу: indexedDB.deleteDatabase('data20-extension')
# Проверить DB_VERSION в storage.js
# Посмотреть Application → Storage → IndexedDB в DevTools
```

---

**Создано**: 2026-01-05
**Версия**: 1.0
**Поддержка**: См. README.md в корне sandbox
