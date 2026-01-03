#!/usr/bin/env python3
"""
FastAPI Backend для Knowledge Base
Предоставляет REST API для доступа к инструментам в реальном времени
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import List, Dict, Optional
import sys
import json

# Добавить tools/ в Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# Создать приложение
app = FastAPI(
    title="Knowledge Base API",
    description="REST API для доступа ко всем 55 инструментам Knowledge Base",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (для фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Корневая директория
ROOT_DIR = Path(__file__).parent.parent

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "name": "Knowledge Base API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "search": "/api/search?q=python",
            "stats": "/api/stats",
            "graph": "/api/graph",
            "files": "/api/files",
            "validate": "/api/validate",
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "knowledge-base-api"}

# ============================================================================
# SEARCH API
# ============================================================================

@app.get("/api/search")
async def search(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, ge=1, le=100, description="Количество результатов")
):
    """
    Поиск по базе знаний (использует search_index.py)

    Пример: /api/search?q=python&limit=5
    """
    try:
        # Импорт search_index
        from search_index import SearchIndexer

        indexer = SearchIndexer(root_dir=ROOT_DIR)

        # Проверить, существует ли индекс
        if not indexer.index_file.exists():
            indexer.build_index()
            indexer.save_index()
        else:
            indexer.load_index()

        # Поиск
        results = indexer.search(q, top_n=limit)

        return {
            "query": q,
            "total": len(results),
            "results": results[:limit]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# ============================================================================
# STATISTICS API
# ============================================================================

@app.get("/api/stats")
async def get_statistics():
    """
    Статистика базы знаний (использует statistics_dashboard.py)

    Возвращает общую статистику по всем статьям
    """
    try:
        # Подсчитать файлы
        knowledge_dir = ROOT_DIR / "knowledge"

        if not knowledge_dir.exists():
            raise HTTPException(status_code=404, detail="Knowledge directory not found")

        # Подсчитать статьи
        md_files = list(knowledge_dir.rglob("*.md"))

        # Подсчитать категории
        categories = set()
        for file in md_files:
            parts = file.relative_to(knowledge_dir).parts
            if len(parts) > 1:
                categories.add(parts[0])

        # Подсчитать размер
        total_size = sum(f.stat().st_size for f in md_files)

        return {
            "total_articles": len(md_files),
            "total_categories": len(categories),
            "categories": sorted(categories),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics error: {str(e)}")

# ============================================================================
# GRAPH API
# ============================================================================

@app.get("/api/graph")
async def get_graph():
    """
    Граф знаний (использует graph_visualizer.py)

    Возвращает JSON с узлами и связями
    """
    try:
        from graph_visualizer import GraphVisualizer

        visualizer = GraphVisualizer(root_dir=ROOT_DIR)
        visualizer.build_graph()

        # Конвертировать в JSON-friendly формат
        nodes = []
        for article_path, data in visualizer.articles.items():
            nodes.append({
                "id": str(article_path),
                "title": data.get('title', 'Untitled'),
                "category": data.get('category', 'Unknown'),
                "tags": data.get('tags', []),
                "links_count": len(data.get('links', [])),
            })

        edges = []
        for source, targets in visualizer.links.items():
            for target in targets:
                edges.append({
                    "source": str(source),
                    "target": str(target),
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph error: {str(e)}")

# ============================================================================
# FILES API
# ============================================================================

@app.get("/api/files")
async def list_files(
    type: Optional[str] = Query(None, description="Тип файла: html, json, csv")
):
    """
    Список всех сгенерированных файлов

    Пример: /api/files?type=html
    """
    try:
        files = []

        # Определить расширения
        if type == "html":
            pattern = "*.html"
        elif type == "json":
            pattern = "*.json"
        elif type == "csv":
            pattern = "*.csv"
        else:
            # Все файлы
            for pattern in ["*.html", "*.json", "*.csv"]:
                files.extend(ROOT_DIR.glob(pattern))

            return {
                "total": len(files),
                "files": [
                    {
                        "name": f.name,
                        "path": str(f.relative_to(ROOT_DIR)),
                        "size": f.stat().st_size,
                        "type": f.suffix[1:],
                    }
                    for f in sorted(files)
                ]
            }

        # Конкретный тип
        files = list(ROOT_DIR.glob(pattern))

        return {
            "type": type,
            "total": len(files),
            "files": [
                {
                    "name": f.name,
                    "path": str(f.relative_to(ROOT_DIR)),
                    "size": f.stat().st_size,
                }
                for f in sorted(files)
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Files error: {str(e)}")

@app.get("/api/files/{filename}")
async def get_file(filename: str):
    """
    Скачать конкретный файл

    Пример: /api/files/knowledge_graph.json
    """
    file_path = ROOT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    # Определить content type
    if filename.endswith('.json'):
        media_type = "application/json"
    elif filename.endswith('.csv'):
        media_type = "text/csv"
    elif filename.endswith('.html'):
        media_type = "text/html"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

# ============================================================================
# VALIDATION API
# ============================================================================

@app.get("/api/validate")
async def validate_knowledge_base():
    """
    Запустить валидацию базы знаний (validate.py)

    Проверяет качество всех статей
    """
    try:
        from validate import KBValidator

        validator = KBValidator(root_dir=ROOT_DIR)
        articles = validator.find_articles()

        issues = []
        for article_path in articles:
            data = validator.load_article(article_path)
            if data:
                article_issues = validator.validate_article(article_path, data)
                if article_issues:
                    issues.extend(article_issues)

        # Группировать по серьёзности
        by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'info')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        return {
            "total_articles": len(articles),
            "total_issues": len(issues),
            "by_severity": {
                severity: len(items)
                for severity, items in by_severity.items()
            },
            "issues": issues[:50],  # Первые 50
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

# ============================================================================
# TAGS API
# ============================================================================

@app.get("/api/tags")
async def get_tags():
    """
    Список всех тегов с весами (weighted_tags.py)
    """
    try:
        # Прочитать JSON если существует
        tags_file = ROOT_DIR / "tag_analytics.json"

        if tags_file.exists():
            with open(tags_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        else:
            # Собрать теги вручную
            from pathlib import Path
            import yaml

            knowledge_dir = ROOT_DIR / "knowledge"
            tags_count = {}

            for md_file in knowledge_dir.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    if content.startswith('---'):
                        yaml_end = content.find('---', 3)
                        if yaml_end != -1:
                            frontmatter = yaml.safe_load(content[3:yaml_end])
                            if isinstance(frontmatter, dict):
                                tags = frontmatter.get('tags', [])
                                for tag in tags:
                                    tags_count[tag] = tags_count.get(tag, 0) + 1
                except:
                    continue

            return {
                "total_tags": len(tags_count),
                "tags": sorted(
                    [{"tag": tag, "count": count} for tag, count in tags_count.items()],
                    key=lambda x: x['count'],
                    reverse=True
                )
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tags error: {str(e)}")

# ============================================================================
# ANALYTICS API
# ============================================================================

@app.get("/api/analytics/summary")
async def analytics_summary():
    """
    Сводная аналитика всей базы знаний
    """
    try:
        knowledge_dir = ROOT_DIR / "knowledge"

        # Базовая статистика
        md_files = list(knowledge_dir.rglob("*.md"))

        # Категории
        categories = {}
        for file in md_files:
            parts = file.relative_to(knowledge_dir).parts
            if len(parts) > 1:
                category = parts[0]
                categories[category] = categories.get(category, 0) + 1

        # Размеры
        total_words = 0
        total_lines = 0

        for file in md_files[:20]:  # Первые 20 для скорости
            try:
                content = file.read_text(encoding='utf-8')
                total_words += len(content.split())
                total_lines += len(content.splitlines())
            except:
                continue

        return {
            "overview": {
                "total_articles": len(md_files),
                "total_categories": len(categories),
                "sample_words": total_words,
                "sample_lines": total_lines,
            },
            "categories": categories,
            "top_categories": sorted(
                categories.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
╔════════════════════════════════════════╗
║  Knowledge Base API                    ║
║  REST API для всех 55 инструментов     ║
╚════════════════════════════════════════╝

Запуск сервера...

📡 API: http://localhost:8000
📚 Docs: http://localhost:8000/docs
📖 ReDoc: http://localhost:8000/redoc

Endpoints:
  GET  /api/search?q=python
  GET  /api/stats
  GET  /api/graph
  GET  /api/files
  GET  /api/validate
  GET  /api/tags
  GET  /api/analytics/summary

Press Ctrl+C to stop
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload при изменениях
        log_level="info"
    )
