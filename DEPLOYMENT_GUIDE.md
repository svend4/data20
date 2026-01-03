# 🚀 DEPLOYMENT GUIDE - Полное руководство по деплою

**Версия:** 1.0
**Дата:** 2026-01-03
**Для:** Knowledge Base с 55 инструментами

---

## 📋 СОДЕРЖАНИЕ

1. [Варианты деплоя](#варианты-деплоя)
2. [Вариант A: Static Site (GitHub Pages)](#вариант-a-static-site-github-pages)
3. [Вариант B: Static + API (Гибрид)](#вариант-b-static--api-гибрид)
4. [Вариант C: Full Docker](#вариант-c-full-docker)
5. [Локальная разработка](#локальная-разработка)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 ВАРИАНТЫ ДЕПЛОЯ

| Вариант | Сложность | Стоимость | Скорость | Use Case |
|---------|-----------|-----------|----------|----------|
| **A. Static (GitHub Pages)** | ⭐ | 0₽ | ⚡⚡⚡⚡⚡ | Документация, блоги |
| **B. Static + API** | ⭐⭐⭐ | ~$5/мес | ⚡⚡⚡⚡ | Динамический поиск |
| **C. Full Docker** | ⭐⭐⭐⭐ | ~$10/мес | ⚡⚡⚡ | Enterprise, full control |

---

## 🎯 ВАРИАНТ A: Static Site (GitHub Pages)

**Рекомендуется для старта!** Бесплатно, просто, быстро.

### Пошаговая инструкция

#### Шаг 1: Подготовка

```bash
# 1. Убедиться что в репозитории
cd /path/to/knowledge-base

# 2. Проверить структуру
ls -la scripts/ static_site/ .github/workflows/
```

#### Шаг 2: Локальная генерация (тест)

```bash
# 1. Генерация всех outputs
./scripts/generate_all.sh --quick

# 2. Генерация static site
python3 static_site/site_generator.py

# 3. Просмотр локально
python -m http.server 8000 --directory static_site/public

# 4. Открыть http://localhost:8000
```

**Ожидаемый результат:**
- ✅ `static_site/public/index.html` создан
- ✅ Красивый dashboard с всеми файлами
- ✅ Работающий поиск

#### Шаг 3: Настройка GitHub Pages

```bash
# 1. Commit всех изменений
git add .
git commit -m "Add static site infrastructure"
git push origin main
```

**В GitHub UI:**

1. **Settings** → **Pages**
2. **Source:** GitHub Actions
3. **Save**

#### Шаг 4: Активация GitHub Actions

Файл уже создан: `.github/workflows/build-kb.yml`

```bash
# Проверить что файл существует
cat .github/workflows/build-kb.yml
```

**Автоматический деплой:**
- ✅ При каждом push на `main`
- ✅ Генерация за 2-5 минут
- ✅ Автопубликация на `https://USERNAME.github.io/REPO`

#### Шаг 5: Проверка деплоя

1. **Actions tab** → Дождаться завершения ✅
2. **Открыть URL:** `https://USERNAME.github.io/data20`
3. **Проверить:**
   - ✅ Index page загружается
   - ✅ Поиск работает
   - ✅ Все ссылки кликабельны

---

### ⚙️ Кастомизация для Варианта A

#### Изменить режим генерации

Редактировать `.github/workflows/build-kb.yml`:

```yaml
# Строка 39: изменить --quick на --full
./scripts/generate_all.sh --full  # Все 55 tools (15-20 минут)
```

#### Добавить custom domain

```bash
# 1. Создать файл
echo "kb.yourdomain.com" > static_site/public/CNAME

# 2. В DNS добавить CNAME record
# CNAME kb.yourdomain.com → USERNAME.github.io

# 3. Push
git add static_site/public/CNAME
git commit -m "Add custom domain"
git push
```

#### Настроить расписание обновлений

Добавить в `.github/workflows/build-kb.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Каждый день в полночь
```

---

## 🔥 ВАРИАНТ B: Static + API (Гибрид)

**Для продвинутых фич:** Realtime search, dynamic data

### Архитектура

```
GitHub Pages (static)    Railway/Fly.io (API)
     ↓                          ↓
  index.html  ←── fetch ←── /api/search
  *.html                     /api/graph
  *.json                     /api/stats
```

### Пошаговая инструкция

#### Шаг 1: Деплой Static (как в Варианте A)

Сначала настроить GitHub Pages (см. выше).

#### Шаг 2: Подготовка API

```bash
# 1. Создать requirements для API
cat api/requirements.txt

# 2. Протестировать локально
cd /path/to/knowledge-base
pip install -r api/requirements.txt
python3 api/main.py
```

Откроется на `http://localhost:8000`:
- ✅ `/docs` — Swagger UI
- ✅ `/api/search?q=python`
- ✅ `/api/stats`

#### Шаг 3: Деплой API на Railway

**Railway.app** (рекомендуется, $5/мес):

```bash
# 1. Установить Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Создать проект
railway init

# 4. Создать Procfile
echo "web: uvicorn api.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 5. Deploy
railway up
```

**Получить URL:**
```bash
railway domain
# → https://your-app.railway.app
```

#### Шаг 4: Подключить API к Static Site

Редактировать `static_site/public/index.html`:

```html
<script>
const API_URL = 'https://your-app.railway.app';

async function liveSearch(query) {
    const res = await fetch(`${API_URL}/api/search?q=${query}`);
    const data = await res.json();
    displayResults(data.results);
}
</script>
```

---

### Альтернатива: Fly.io

```bash
# 1. Установить flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch app
flyctl launch
# Выбрать регион, подтвердить

# 4. Deploy
flyctl deploy
```

---

## 🐳 ВАРИАНТ C: Full Docker

**Для production** с полным контролем.

### Пошаговая инструкция

#### Шаг 1: Локальная сборка

```bash
# 1. Build image
docker build -t knowledge-base-api .

# 2. Run container
docker run -p 8000:8000 knowledge-base-api

# 3. Проверить
curl http://localhost:8000/health
```

#### Шаг 2: Docker Compose (полный стек)

```bash
# 1. Запуск всего стека
docker-compose up -d

# 2. Проверка статуса
docker-compose ps

# Сервисы:
# - web (nginx): http://localhost
# - api (FastAPI): http://localhost:8000
```

**Проверка:**
```bash
# Static site
curl http://localhost/

# API
curl http://localhost/api/stats

# Logs
docker-compose logs -f api
```

#### Шаг 3: Деплой на VPS

**На DigitalOcean / Hetzner / AWS EC2:**

```bash
# 1. SSH в сервер
ssh user@your-server.com

# 2. Установить Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone репозитория
git clone https://github.com/YOUR/REPO.git
cd REPO

# 4. Запуск
docker-compose up -d

# 5. Настроить Nginx reverse proxy (опционально)
# или использовать Traefik для auto SSL
```

#### Шаг 4: Auto SSL с Traefik

Создать `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.httpchallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=your@email.com"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  api:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=myresolver"

  web:
    image: nginx:alpine
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`kb.yourdomain.com`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=myresolver"
    volumes:
      - ./static_site/public:/usr/share/nginx/html:ro
```

**Запуск:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Результат:**
- ✅ `https://kb.yourdomain.com` — Static site (auto SSL)
- ✅ `https://api.yourdomain.com` — API (auto SSL)

---

## 💻 ЛОКАЛЬНАЯ РАЗРАБОТКА

### Quick Start

```bash
# 1. Генерация outputs
./scripts/generate_all.sh --quick

# 2. Static site
python3 static_site/site_generator.py
python -m http.server 8000 --directory static_site/public

# 3. API (в другом терминале)
pip install -r api/requirements.txt
python3 api/main.py

# Готово!
# Static: http://localhost:8000
# API: http://localhost:8000 (другой порт, например 8001)
```

### Разработка с live reload

```bash
# API с auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Static - регенерация при изменениях
watch -n 5 python3 static_site/site_generator.py
```

---

## 🐛 TROUBLESHOOTING

### Проблема: GitHub Actions падает с timeout

**Решение:**
```yaml
# В .github/workflows/build-kb.yml изменить:
./scripts/generate_all.sh --quick  # вместо --full
timeout-minutes: 15  # увеличить до 30
```

### Проблема: Docker build слишком долгий

**Решение:** Использовать multi-stage build (уже настроено):
```dockerfile
# Dockerfile уже оптимизирован
# Builder stage: генерация
# Runtime stage: только API
```

### Проблема: Static site не показывает файлы

**Решение:**
```bash
# 1. Проверить что файлы существуют
ls -la *.html *.json *.csv

# 2. Регенерировать
./scripts/generate_all.sh --quick

# 3. Пересоздать site
python3 static_site/site_generator.py
```

### Проблема: API возвращает 500 ошибки

**Решение:**
```bash
# 1. Проверить логи
docker-compose logs api

# 2. Проверить, что tools/ доступны
python3 -c "from search_index import SearchIndexer; print('OK')"

# 3. Пересобрать
docker-compose build --no-cache api
```

---

## 📊 МОНИТОРИНГ И ПОДДЕРЖКА

### Логи

```bash
# GitHub Actions
# В UI: Actions → Workflow run → View logs

# Docker
docker-compose logs -f api
docker-compose logs -f web

# Railway
railway logs
```

### Метрики

**GitHub Pages:**
- Settings → Insights → Traffic

**Railway:**
- Dashboard → Metrics → CPU/Memory/Network

**Docker:**
```bash
docker stats
```

---

## 🎯 РЕКОМЕНДАЦИИ ПО ВЫБОРУ

### Выбирайте **Вариант A (Static)** если:
- ✅ Нужна простая документация/blog
- ✅ Нет бюджета на хостинг
- ✅ Не нужен realtime поиск
- ✅ Обновления редкие (раз в день/неделю)

### Выбирайте **Вариант B (Static + API)** если:
- ✅ Нужен dynamic search
- ✅ Есть бюджет ~$5/мес
- ✅ Нужны realtime обновления
- ✅ Планируется интеграция с другими сервисами

### Выбирайте **Вариант C (Docker)** если:
- ✅ Нужен полный контроль
- ✅ Enterprise use case
- ✅ Есть DevOps команда
- ✅ Требуется кастомная инфраструктура

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [GitHub Pages docs](https://docs.github.com/en/pages)
- [Railway docs](https://docs.railway.app/)
- [Fly.io docs](https://fly.io/docs/)
- [Docker docs](https://docs.docker.com/)
- [FastAPI docs](https://fastapi.tiangolo.com/)

---

## ✅ ЧЕКЛИСТ ДЕПЛОЯ

### Вариант A (Static):
- [ ] Создан `.github/workflows/build-kb.yml`
- [ ] Настроен GitHub Pages (Source: GitHub Actions)
- [ ] Первый push на main
- [ ] Workflow завершился успешно
- [ ] Сайт открывается по URL

### Вариант B (Static + API):
- [ ] Все из Варианта A ✓
- [ ] API протестирован локально
- [ ] Создан аккаунт на Railway/Fly.io
- [ ] API задеплоен
- [ ] URL API добавлен в static site
- [ ] CORS настроен корректно

### Вариант C (Docker):
- [ ] Docker установлен
- [ ] `docker-compose up` работает локально
- [ ] VPS арендован
- [ ] Docker установлен на VPS
- [ ] Репозиторий склонирован на VPS
- [ ] `docker-compose up -d` запущен
- [ ] DNS настроен (опционально)
- [ ] SSL настроен (опционально)

---

**Создано:** 2026-01-03
**Версия:** 1.0
**Поддержка:** См. документацию в `/ARCHITECTURE_ANALYSIS.md`

🎉 **Успешного деплоя!**
