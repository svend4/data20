# 🧪 Phase 9.2 Testing Suite

**Базовая версия**: browser-extension (Phase 9.2 - Hybrid Offline Strategy)
**Создано**: 2026-01-05
**Статус**: 🟡 Planned - Подготовка к тестированию

---

## 🎯 Цели Тестирования

Проверить и верифицировать все компоненты Phase 9.2:
- ✅ Tool Classification System (9.2.1)
- ✅ 35 WASM Tools (9.2.2)
- ✅ Smart Router (9.2.3)
- ✅ Offline Queue (9.2.4)
- ✅ Performance Monitor (9.2.5)

---

## 📋 План Тестирования

### 1. Unit Tests

#### 1.1 Smart Router Tests
**Файл**: `tests/smart-router.test.js`

```javascript
// Тесты для:
- getToolComplexity()
- executeTool() с разными complexity levels
- Cache механизм
- Retry logic
- Timeout handling
- Fallback mechanisms
```

**Покрытие**: Цель 90%+

#### 1.2 Offline Queue Tests
**Файл**: `tests/offline-queue.test.js`

```javascript
// Тесты для:
- addToQueue()
- processQueue()
- Priority sorting
- Retry logic
- Network status handling
- Background sync
```

**Покрытие**: Цель 85%+

#### 1.3 Performance Monitor Tests
**Файл**: `tests/performance-monitor.test.js`

```javascript
// Тесты для:
- recordToolExecution()
- getMetrics()
- Memory sampling
- Export functions
- Reset functionality
```

**Покрытие**: Цель 80%+

#### 1.4 Tool Registry Tests
**Файл**: `tests/tool-registry.test.js`

```javascript
// Тесты для:
- loadTools()
- executeTool() для каждого из 35 tools
- Error handling
- Parameter validation
```

**Покрытие**: Цель 75%+

---

### 2. Integration Tests

#### 2.1 Router + Queue Integration
**Сценарий**: Offline → Queue → Online → Execute

```javascript
// Test flow:
1. Go offline (navigator.onLine = false)
2. Execute complex tool
3. Verify queued
4. Go online
5. Verify auto-execution
6. Check result
```

#### 2.2 Router + Cache Integration
**Сценарий**: Cache hit/miss behavior

```javascript
// Test flow:
1. Execute tool (cache miss)
2. Verify result cached
3. Execute same tool (cache hit)
4. Verify instant return
5. Wait for TTL expiry
6. Execute again (cache miss)
```

#### 2.3 Monitor + Router Integration
**Сценарий**: Metrics recording

```javascript
// Test flow:
1. Execute 10 different tools
2. Check metrics updated
3. Verify routing distribution
4. Check error rates
5. Export metrics
```

---

### 3. E2E Tests (End-to-End)

#### 3.1 User Flow: Tool Execution
```
1. User opens extension
2. Selects tool from list
3. Enters parameters
4. Executes tool
5. Sees results
6. Checks metrics
```

#### 3.2 User Flow: Offline Operations
```
1. User goes offline
2. Executes simple tool (works locally)
3. Executes complex tool (queued)
4. Goes online
5. Sees queue processing
6. Receives notification
```

#### 3.3 User Flow: Queue Management
```
1. User opens Queue tab
2. Sees queued jobs
3. Clears completed
4. Retries failed
5. Triggers manual sync
```

---

### 4. Performance Tests

#### 4.1 Load Time Tests
**Цель**: Измерить время инициализации

```javascript
// Метрики:
- Pyodide load time: < 4s (first), < 100ms (cached)
- Tool registry load: < 500ms
- Smart router init: < 100ms
- Total extension load: < 5s
```

#### 4.2 Execution Speed Tests
**Цель**: Сравнить local vs cloud

```javascript
// Для каждого tool:
- Local execution time
- Cloud execution time (mock)
- Cache hit time (should be ~0ms)
- Speedup ratio
```

#### 4.3 Memory Tests
**Цель**: Проверить потребление памяти

```javascript
// Метрики:
- Initial memory: < 30MB
- After 10 tools: < 50MB
- After 100 tools: < 70MB
- Peak memory: < 100MB
- No memory leaks
```

#### 4.4 Stress Tests
**Цель**: Проверить стабильность под нагрузкой

```javascript
// Сценарии:
- Execute 100 tools sequentially
- Execute 20 tools in parallel
- Queue 50 jobs and process
- Run for 1 hour continuously
```

---

### 5. Browser Compatibility Tests

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 120+ | 🟡 To Test |
| Firefox | 120+ | 🟡 To Test |
| Edge | 120+ | 🟡 To Test |
| Opera | 100+ | 🟡 To Test |

**Тест для каждого браузера**:
- [ ] Extension loads
- [ ] All tabs work
- [ ] Tools execute
- [ ] Queue works
- [ ] Metrics display
- [ ] Export functions

---

## 🔧 Testing Framework

### Рекомендуемый Stack

```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "jest-webextension-mock": "^3.8.0",
    "@testing-library/dom": "^9.0.0",
    "puppeteer": "^21.0.0",
    "chrome-launcher": "^1.0.0"
  }
}
```

### Структура Тестов

```
sandbox/phase-9.2-testing/
├── tests/
│   ├── unit/
│   │   ├── smart-router.test.js
│   │   ├── offline-queue.test.js
│   │   ├── performance-monitor.test.js
│   │   └── tool-registry.test.js
│   ├── integration/
│   │   ├── router-queue.test.js
│   │   ├── router-cache.test.js
│   │   └── monitor-router.test.js
│   ├── e2e/
│   │   ├── user-flow-execution.test.js
│   │   ├── user-flow-offline.test.js
│   │   └── user-flow-queue.test.js
│   └── performance/
│       ├── load-time.test.js
│       ├── execution-speed.test.js
│       ├── memory.test.js
│       └── stress.test.js
├── mocks/
│   ├── chrome-api.mock.js
│   ├── pyodide.mock.js
│   └── storage.mock.js
└── fixtures/
    ├── sample-tools.json
    ├── sample-metrics.json
    └── sample-queue.json
```

---

## 📊 Test Coverage Goals

| Component | Unit Tests | Integration | E2E | Total |
|-----------|-----------|-------------|-----|-------|
| Smart Router | 90% | 80% | 70% | 85% |
| Offline Queue | 85% | 75% | 70% | 80% |
| Performance Monitor | 80% | 70% | 60% | 75% |
| Tool Registry | 75% | 70% | 60% | 70% |
| **Overall** | **85%** | **75%** | **65%** | **78%** |

---

## 🐛 Known Issues & Bug Tracking

### Issue #1: [Название]
**Приоритет**: 🔴 High / 🟡 Medium / 🟢 Low
**Компонент**: Smart Router / Queue / Monitor / etc.
**Статус**: 🟡 Open / 🔵 In Progress / 🟢 Fixed

**Описание**:
Подробное описание проблемы

**Воспроизведение**:
1. Шаг 1
2. Шаг 2
3. Ожидаемое vs фактическое поведение

**Решение**:
Как исправлено или план исправления

---

## ✅ Testing Checklist

### Pre-Test Setup
- [ ] Sandbox копия создана
- [ ] Jest установлен и настроен
- [ ] Mocks подготовлены
- [ ] Fixtures созданы

### Unit Testing
- [ ] Smart Router tests written (90%)
- [ ] Offline Queue tests written (85%)
- [ ] Performance Monitor tests written (80%)
- [ ] Tool Registry tests written (75%)
- [ ] All unit tests pass

### Integration Testing
- [ ] Router + Queue integration tested
- [ ] Router + Cache integration tested
- [ ] Monitor + Router integration tested
- [ ] All integration tests pass

### E2E Testing
- [ ] Tool execution flow tested
- [ ] Offline operations flow tested
- [ ] Queue management flow tested
- [ ] All E2E tests pass

### Performance Testing
- [ ] Load time benchmarks collected
- [ ] Execution speed measured
- [ ] Memory usage profiled
- [ ] Stress tests completed

### Browser Compatibility
- [ ] Chrome tested
- [ ] Firefox tested
- [ ] Edge tested
- [ ] Opera tested

### Final Verification
- [ ] All tests pass (>95%)
- [ ] Coverage goals met
- [ ] No critical bugs
- [ ] Performance within targets
- [ ] Documentation updated

---

## 📝 Test Results Log

### Test Run #1
**Дата**: YYYY-MM-DD
**Браузер**: Chrome 120
**Результаты**:
- Unit Tests: X/Y passed (Z% coverage)
- Integration Tests: X/Y passed
- E2E Tests: X/Y passed
- Performance: Within/Outside targets

**Выводы**:
...

---

## 🚀 Running Tests

### All Tests
```bash
cd /home/user/data20/sandbox/phase-9.2-testing/
npm test
```

### Unit Tests Only
```bash
npm run test:unit
```

### Integration Tests
```bash
npm run test:integration
```

### E2E Tests
```bash
npm run test:e2e
```

### Coverage Report
```bash
npm run test:coverage
```

### Performance Benchmarks
```bash
npm run test:perf
```

---

**Версия документа**: 1.0
**Последнее обновление**: 2026-01-05
**Ответственный**: TBD
