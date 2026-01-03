# Multi-stage Dockerfile для Knowledge Base API
# Использование: docker build -t knowledge-base-api .
#               docker run -p 8000:8000 knowledge-base-api

# ============================================================================
# Stage 1: Builder - Генерация всех outputs
# ============================================================================
FROM python:3.10-slim as builder

WORKDIR /app

# Копировать только необходимые файлы
COPY knowledge/ ./knowledge/
COPY tools/ ./tools/
COPY scripts/ ./scripts/
COPY static_site/ ./static_site/

# Установить зависимости для генерации
RUN pip install --no-cache-dir pyyaml

# Генерация outputs (quick mode для скорости)
RUN chmod +x scripts/generate_all.sh && \
    ./scripts/generate_all.sh --quick || true

# Генерация static site
RUN chmod +x static_site/site_generator.py && \
    python3 static_site/site_generator.py

# ============================================================================
# Stage 2: Runtime - FastAPI сервер
# ============================================================================
FROM python:3.10-slim

WORKDIR /app

# Копировать requirements
COPY api/requirements.txt ./api/

# Установить FastAPI зависимости
RUN pip install --no-cache-dir -r api/requirements.txt

# Копировать из builder
COPY --from=builder /app/knowledge/ ./knowledge/
COPY --from=builder /app/tools/ ./tools/
COPY --from=builder /app/*.html ./
COPY --from=builder /app/*.json ./
COPY --from=builder /app/*.csv ./
COPY --from=builder /app/static_site/public/ ./static_site/public/

# Копировать API код
COPY api/ ./api/

# Создать non-root пользователя
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app

USER apiuser

# Expose порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Запуск
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
