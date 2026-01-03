# 🤖 GitHub Actions Workflows

Автоматическая CI/CD для Knowledge Base.

---

## 📋 Доступные Workflows

### 1. `build-kb.yml` — Основной workflow

**Триггеры:**
- ✅ Push на `main`/`master`/`claude/*`
- ✅ Pull Request на `main`/`master`
- ✅ Ручной запуск (workflow_dispatch)

**Что делает:**

#### Job: `build` (всегда запускается)
1. Checkout кода
2. Установка Python 3.10
3. Установка зависимостей (`pyyaml`)
4. Запуск `generate_all.sh --quick` (критичные инструменты)
5. Генерация static site (`site_generator.py`)
6. Upload artifact для Pages

#### Job: `deploy` (только на main/master)
1. Deploy на GitHub Pages
2. Публикация site по URL

#### Job: `validate` (только на Pull Requests)
1. Запуск валидации (`generate_all.sh --validate-only`)
2. Проверка качества без генерации

---

## 🚀 Быстрый старт

### Шаг 1: Настройка GitHub Pages

1. Открыть Settings → Pages
2. Source: **GitHub Actions**
3. Сохранить

### Шаг 2: Push изменений

```bash
git add .
git commit -m "Enable GitHub Actions"
git push origin main
```

### Шаг 3: Дождаться деплоя

1. Открыть **Actions** tab
2. Дождаться завершения workflow (2-5 минут)
3. Открыть сайт по URL: `https://yourname.github.io`

---

## 📊 Пример вывода

### В Actions tab:

```
🚀 Build Knowledge Base
  └─ 🏗️ Build Site
      ├─ ✓ Checkout repository
      ├─ ✓ Set up Python
      ├─ ✓ Install dependencies
      ├─ ✓ Generate outputs (15 tools, 13 success, 2 failed)
      ├─ ✓ Generate static site (69 files)
      └─ ✓ Upload artifact
  └─ 🚀 Deploy to GitHub Pages
      └─ ✓ Deployed to https://yourname.github.io
```

### Build Summary (в workflow run):

```markdown
### 📊 Build Summary

**Generated files:**
- HTML: 10 files
- JSON: 30 files
- CSV: 1 files
- Reports: 28 files

**Site:**
- Index: ✓ static_site/public/index.html
```

---

## ⚙️ Кастомизация

### Изменить режим генерации

Отредактировать `.github/workflows/build-kb.yml`:

```yaml
# Было:
./scripts/generate_all.sh --quick

# Стало (полная генерация всех 55 tools):
./scripts/generate_all.sh --full
```

**⚠️ Внимание:** Full mode займёт 10-20 минут!

### Изменить таймауты

```yaml
- name: 🛠️ Generate all outputs
  run: ./scripts/generate_all.sh --quick
  timeout-minutes: 15  # Изменить здесь
```

### Добавить кастомные шаги

```yaml
- name: 🎨 Custom processing
  run: |
    python3 my_custom_script.py
    echo "Done!"
```

---

## 🔒 Секреты и переменные

Если нужны API ключи или tokens:

### 1. Добавить в Settings → Secrets

```
CUSTOM_API_KEY=your_secret_value
```

### 2. Использовать в workflow

```yaml
- name: Use secret
  env:
    API_KEY: ${{ secrets.CUSTOM_API_KEY }}
  run: |
    python3 script.py
```

---

## 🐛 Отладка

### Если workflow падает:

1. **Открыть Actions → Failed run**
2. **Кликнуть на failed step**
3. **Прочитать логи**

### Частые проблемы:

#### ❌ "Python module not found"

**Решение:** Добавить в `.github/workflows/build-kb.yml`:

```yaml
- name: Install dependencies
  run: |
    pip install pyyaml missing-module
```

#### ❌ "Timeout after 15 minutes"

**Решение:** Увеличить timeout или использовать `--quick` вместо `--full`:

```yaml
timeout-minutes: 30  # Было: 15
```

#### ❌ "Permission denied"

**Решение:** Проверить, что скрипты executable:

```yaml
- name: Make scripts executable
  run: |
    chmod +x scripts/*.sh
    chmod +x static_site/*.py
```

---

## 📈 Оптимизация

### Кэширование Python пакетов

Уже включено:

```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'  # ← Кэширует pip packages
```

### Кэширование generated outputs

```yaml
- name: Cache outputs
  uses: actions/cache@v3
  with:
    path: |
      *.html
      *.json
      *.csv
    key: outputs-${{ github.sha }}
```

---

## 🎯 Best Practices

1. ✅ **Используйте `--quick` для PR** — быстрая валидация
2. ✅ **Используйте `--full` для main** — полная генерация
3. ✅ **Проверяйте логи** — GitHub сохраняет их 90 дней
4. ✅ **Мониторьте время** — оптимизируйте медленные tools
5. ✅ **Используйте artifacts** — скачать generated files

---

## 📦 Download Artifacts

После успешного build можно скачать outputs:

1. **Actions → Workflow run**
2. **Artifacts → github-pages**
3. **Download ZIP** (содержит весь static site)

---

## 🔄 Manual Trigger

### Через UI:

1. **Actions → Build Knowledge Base**
2. **Run workflow → Branch: main**
3. **Run workflow**

### Через CLI (gh):

```bash
gh workflow run build-kb.yml
```

---

## 📊 Мониторинг

### GitHub Actions Usage

**Settings → Billing → Actions**

- **Free plan**: 2,000 минут/месяц
- **Pro plan**: 3,000 минут/месяц

**Текущий workflow:**
- Quick mode: ~3 минуты
- Full mode: ~15 минут

**Рекомендация:** Используйте Quick mode для экономии минут!

---

**Создано:** 2026-01-03
**Версия:** 1.0
