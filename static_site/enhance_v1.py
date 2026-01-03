#!/usr/bin/env python3
"""
Enhanced Site Generator v1 - Quick Wins
Добавляет улучшения к базовому site_generator.py:
- Расширенный поиск с фильтрами
- Sidebar навигация
- Карточки с preview и метаданными
- Dark mode toggle
- Улучшенная типографика и анимации
"""

from pathlib import Path
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
import re
import hashlib

class EnhancedSiteGenerator:
    """Улучшенный генератор статического сайта"""

    def __init__(self, root_dir: Path = Path(".")):
        self.root_dir = Path(root_dir)
        self.output_dir = self.root_dir / "static_site" / "public"
        self.assets_dir = self.output_dir / "assets"

        # Создать директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        (self.assets_dir / "css").mkdir(exist_ok=True)
        (self.assets_dir / "js").mkdir(exist_ok=True)

        # Собрать все файлы
        self.html_files = []
        self.json_files = []
        self.csv_files = []
        self.reports = []
        self.all_files = []

    def scan_outputs(self):
        """Сканировать все сгенерированные файлы"""
        print("📊 Сканирование outputs...")

        # HTML files
        self.html_files = sorted(self.root_dir.glob("*.html"))
        print(f"  HTML: {len(self.html_files)} файлов")

        # JSON files
        self.json_files = sorted(self.root_dir.glob("*.json"))
        self.json_files = [f for f in self.json_files if not f.name.startswith('.')]
        print(f"  JSON: {len(self.json_files)} файлов")

        # CSV files
        self.csv_files = sorted(self.root_dir.glob("*.csv"))
        print(f"  CSV: {len(self.csv_files)} файлов")

        # Markdown reports
        self.reports = sorted(self.root_dir.glob("*REPORT*.md"))
        self.reports += sorted(self.root_dir.glob("*SUMMARY*.md"))
        self.reports += sorted(self.root_dir.glob("COMPLETE_*.md"))
        self.reports = list(set(self.reports))
        print(f"  Reports: {len(self.reports)} файлов")

        self.all_files = self.html_files + self.json_files + self.csv_files + self.reports

    def extract_file_metadata(self, file: Path) -> Dict:
        """Извлечь метаданные из файла"""
        metadata = {
            "name": file.stem,
            "filename": file.name,
            "type": file.suffix[1:].upper(),
            "size": file.stat().st_size,
            "size_str": self.format_size(file.stat().st_size),
            "modified": datetime.fromtimestamp(file.stat().st_mtime),
            "modified_str": datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
            "path": str(file.relative_to(self.root_dir)),
        }

        # Дополнительные метаданные для JSON
        if file.suffix == '.json':
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata['json_keys'] = len(data.keys()) if isinstance(data, dict) else None
                    metadata['json_items'] = len(data) if isinstance(data, list) else None
                    metadata['preview'] = self.generate_json_preview(data)
            except Exception as e:
                metadata['preview'] = f"Error: {e}"

        # Для CSV
        elif file.suffix == '.csv':
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    metadata['csv_rows'] = len(lines) - 1  # Минус заголовок
                    metadata['csv_columns'] = len(lines[0].split(',')) if lines else 0
            except Exception:
                pass

        return metadata

    def generate_json_preview(self, data, max_lines=5) -> str:
        """Генерировать preview JSON данных"""
        try:
            preview = json.dumps(data, indent=2, ensure_ascii=False)
            lines = preview.split('\n')
            if len(lines) > max_lines:
                lines = lines[:max_lines] + ['  ...']
            return '\n'.join(lines)
        except Exception:
            return str(data)[:200] + '...'

    def categorize_files(self) -> Dict[str, List[Path]]:
        """Категоризация файлов по типу"""
        categories = {
            "Визуализации": [],
            "Графы и сети": [],
            "Статистика": [],
            "Отчёты": [],
            "Данные (JSON)": [],
            "Таблицы (CSV)": [],
        }

        # Категоризация HTML
        for html in self.html_files:
            name_lower = html.name.lower()
            if any(k in name_lower for k in ['graph', 'network', 'viz']):
                categories["Графы и сети"].append(html)
            elif any(k in name_lower for k in ['stat', 'dashboard', 'metric']):
                categories["Статистика"].append(html)
            else:
                categories["Визуализации"].append(html)

        categories["Отчёты"] = self.reports
        categories["Данные (JSON)"] = self.json_files
        categories["Таблицы (CSV)"] = self.csv_files

        return categories

    def generate_enhanced_index(self):
        """Генерация улучшенной главной страницы"""
        print("📄 Генерация enhanced index.html...")

        categories = self.categorize_files()

        # Начало HTML
        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Base - Enhanced Dashboard</title>
    <link rel="stylesheet" href="assets/css/enhanced.css">
</head>
<body>
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-header">
            <h2>📚 KB</h2>
            <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
        </div>

        <!-- Quick Stats -->
        <div class="sidebar-section">
            <h3>📊 Статистика</h3>
            <div class="stat-item">
                <span class="label">Всего файлов</span>
                <span class="value">""" + str(len(self.all_files)) + """</span>
            </div>
            <div class="stat-item">
                <span class="label">Обновлено</span>
                <span class="value">""" + datetime.now().strftime('%H:%M') + """</span>
            </div>
            <div class="stat-item">
                <span class="label">Размер</span>
                <span class="value">""" + self.format_size(sum(f.stat().st_size for f in self.all_files)) + """</span>
            </div>
        </div>

        <!-- Quick Navigation -->
        <nav class="sidebar-section">
            <h3>🧭 Навигация</h3>
            <ul class="nav-list">
"""

        # Добавить навигацию по категориям
        category_icons = {
            "Визуализации": "📊",
            "Графы и сети": "🕸️",
            "Статистика": "📈",
            "Отчёты": "📄",
            "Данные (JSON)": "💾",
            "Таблицы (CSV)": "📋",
        }

        for cat_name, files in categories.items():
            if files:
                icon = category_icons.get(cat_name, "📁")
                cat_id = cat_name.replace(" ", "-").replace("(", "").replace(")", "").lower()
                html += f"""
                <li>
                    <a href="#{cat_id}" class="nav-link">
                        <span class="nav-icon">{icon}</span>
                        <span class="nav-label">{cat_name}</span>
                        <span class="nav-count">{len(files)}</span>
                    </a>
                </li>
"""

        html += """
            </ul>
        </nav>

        <!-- Theme Toggle -->
        <div class="sidebar-section">
            <button class="theme-toggle" onclick="toggleTheme()">
                <span class="theme-icon">🌓</span>
                <span class="theme-label">Тема</span>
            </button>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
        <!-- Header -->
        <header class="page-header">
            <div class="header-content">
                <h1>📚 Knowledge Base Dashboard</h1>
                <p>Централизованный доступ ко всем визуализациям и данным</p>
                <p class="header-meta">Сгенерировано: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            </div>
        </header>

        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-number">""" + str(len(self.html_files)) + """</div>
                <div class="stat-label">HTML Визуализаций</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-number">""" + str(len(self.json_files)) + """</div>
                <div class="stat-label">JSON Datasets</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📋</div>
                <div class="stat-number">""" + str(len(self.csv_files)) + """</div>
                <div class="stat-label">CSV Tables</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-number">""" + str(len(self.reports)) + """</div>
                <div class="stat-label">Markdown Reports</div>
            </div>
        </div>

        <!-- Advanced Search -->
        <div class="search-container">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="🔍 Поиск по файлам..." onkeyup="filterFiles()">
            </div>

            <div class="filters">
                <select id="type-filter" onchange="filterFiles()">
                    <option value="">Все типы</option>
                    <option value="html">HTML</option>
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                    <option value="md">Markdown</option>
                </select>

                <select id="category-filter" onchange="filterFiles()">
                    <option value="">Все категории</option>
                    <option value="viz">Визуализации</option>
                    <option value="graph">Графы</option>
                    <option value="stats">Статистика</option>
                    <option value="reports">Отчёты</option>
                    <option value="data">Данные</option>
                    <option value="tables">Таблицы</option>
                </select>

                <select id="size-filter" onchange="filterFiles()">
                    <option value="">Любой размер</option>
                    <option value="tiny">< 1 KB</option>
                    <option value="small">1-10 KB</option>
                    <option value="medium">10-100 KB</option>
                    <option value="large">100KB - 1MB</option>
                    <option value="huge">> 1 MB</option>
                </select>

                <button class="reset-btn" onclick="resetFilters()">Сбросить</button>
            </div>
        </div>
"""

        # Генерация категорий с улучшенными карточками
        for cat_name, files in categories.items():
            if not files:
                continue

            icon = category_icons.get(cat_name, "📁")
            cat_id = cat_name.replace(" ", "-").replace("(", "").replace(")", "").lower()

            # Определить data-category для фильтрации
            cat_filter_id = ""
            if "Визуализации" in cat_name:
                cat_filter_id = "viz"
            elif "Граф" in cat_name:
                cat_filter_id = "graph"
            elif "Статистика" in cat_name:
                cat_filter_id = "stats"
            elif "Отчёт" in cat_name:
                cat_filter_id = "reports"
            elif "JSON" in cat_name:
                cat_filter_id = "data"
            elif "CSV" in cat_name:
                cat_filter_id = "tables"

            html += f"""
        <section class="category-section" id="{cat_id}">
            <h2 class="category-title">
                <span class="category-icon">{icon}</span>
                <span class="category-name">{cat_name}</span>
                <span class="category-count">({len(files)})</span>
            </h2>

            <div class="file-grid">
"""

            for file in files:
                metadata = self.extract_file_metadata(file)

                # Определить размер для фильтра
                size_class = self.get_size_class(metadata['size'])

                html += f"""
                <div class="file-card enhanced"
                     data-filename="{file.name.lower()}"
                     data-type="{file.suffix[1:].lower()}"
                     data-category="{cat_filter_id}"
                     data-size="{size_class}">

                    <!-- Card Header -->
                    <div class="card-header">
                        <span class="file-type-badge {file.suffix[1:].lower()}">{metadata['type']}</span>
                        <span class="file-size">{metadata['size_str']}</span>
                    </div>

                    <!-- Card Title -->
                    <h3 class="card-title">{metadata['name']}</h3>

                    <!-- Card Meta -->
                    <div class="card-meta">
"""

                # Добавить специфичные метаданные
                if file.suffix == '.json' and 'json_keys' in metadata:
                    if metadata['json_keys']:
                        html += f"""
                        <span class="meta-item">🔑 {metadata['json_keys']} ключей</span>
"""
                    if metadata['json_items']:
                        html += f"""
                        <span class="meta-item">📊 {metadata['json_items']} записей</span>
"""

                elif file.suffix == '.csv' and 'csv_rows' in metadata:
                    html += f"""
                        <span class="meta-item">📋 {metadata['csv_rows']} строк</span>
                        <span class="meta-item">🔢 {metadata['csv_columns']} колонок</span>
"""

                html += f"""
                        <span class="meta-item">📅 {metadata['modified_str']}</span>
                    </div>

                    <!-- Preview (для JSON) -->
"""
                if file.suffix == '.json' and 'preview' in metadata:
                    html += f"""
                    <div class="card-preview">
                        <pre><code>{metadata['preview']}</code></pre>
                    </div>
"""

                html += f"""
                    <!-- Card Actions -->
                    <div class="card-actions">
                        <a href="../{metadata['path']}" class="btn btn-primary" target="_blank">
                            👁️ Открыть
                        </a>
                        <button class="btn btn-secondary" onclick="copyPath('{metadata['path']}')">
                            📋 Путь
                        </button>
                    </div>
                </div>
"""

            html += """
            </div>
        </section>
"""

        # Footer и скрипты
        html += """
    </main>

    <footer class="page-footer">
        <p>🚀 Generated by Enhanced Knowledge Base Static Site Generator v1.0</p>
        <p>55 инструментов | 25+ алгоритмов | Production Ready</p>
    </footer>

    <script src="assets/js/enhanced.js"></script>
</body>
</html>
"""

        # Сохранить
        index_path = self.output_dir / "index.html"
        index_path.write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: {index_path}")

    def generate_css(self):
        """Генерация улучшенных стилей"""
        print("🎨 Генерация enhanced.css...")

        css = """/* Enhanced Dashboard CSS v1.0 */

/* CSS Variables */
:root {
    /* Light theme */
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #e9ecef;
    --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

    --text-primary: #2c3e50;
    --text-secondary: #7f8c8d;
    --text-tertiary: #95a5a6;

    --border-color: #e0e0e0;
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-md: 0 4px 15px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.15);

    --accent-primary: #667eea;
    --accent-secondary: #764ba2;
    --accent-success: #27ae60;
    --accent-warning: #f39c12;
    --accent-danger: #e74c3c;

    --sidebar-width: 280px;
    --header-height: 200px;

    --transition-speed: 0.3s;
    --border-radius: 12px;
}

/* Dark theme */
[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-tertiary: #0f3460;
    --bg-gradient: linear-gradient(135deg, #0f3443 0%, #34e89e 100%);

    --text-primary: #ecf0f1;
    --text-secondary: #bdc3c7;
    --text-tertiary: #95a5a6;

    --border-color: #2c3e50;
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 15px rgba(0,0,0,0.5);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.7);

    --accent-primary: #34e89e;
    --accent-secondary: #0f3443;
}

/* Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-gradient);
    color: var(--text-primary);
    min-height: 100vh;
    line-height: 1.6;
}

/* Smooth transitions */
body.theme-transitioning,
body.theme-transitioning * {
    transition: background-color var(--transition-speed) ease,
                color var(--transition-speed) ease,
                border-color var(--transition-speed) ease !important;
}

/* Sidebar */
.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: var(--sidebar-width);
    height: 100vh;
    background: var(--bg-primary);
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    overflow-y: auto;
    z-index: 1000;
    transition: transform var(--transition-speed) ease;
}

.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sidebar-header h2 {
    font-size: 1.5em;
    background: var(--bg-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sidebar-toggle {
    display: none;
    background: none;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
    color: var(--text-primary);
}

.sidebar-section {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
}

.sidebar-section h3 {
    font-size: 0.9em;
    text-transform: uppercase;
    color: var(--text-tertiary);
    margin-bottom: 15px;
    letter-spacing: 0.5px;
}

.stat-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    font-size: 0.9em;
}

.stat-item .label {
    color: var(--text-secondary);
}

.stat-item .value {
    font-weight: 600;
    color: var(--accent-primary);
}

.nav-list {
    list-style: none;
}

.nav-link {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    text-decoration: none;
    color: var(--text-primary);
    border-radius: 8px;
    transition: all var(--transition-speed) ease;
    margin-bottom: 5px;
}

.nav-link:hover {
    background: var(--bg-secondary);
    transform: translateX(5px);
}

.nav-icon {
    margin-right: 10px;
    font-size: 1.2em;
}

.nav-label {
    flex: 1;
}

.nav-count {
    background: var(--accent-primary);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}

.theme-toggle {
    width: 100%;
    padding: 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1em;
    color: var(--text-primary);
    transition: all var(--transition-speed) ease;
}

.theme-toggle:hover {
    background: var(--accent-primary);
    color: white;
    border-color: var(--accent-primary);
}

/* Main Content */
.main-content {
    margin-left: var(--sidebar-width);
    padding: 30px;
    min-height: 100vh;
}

/* Header */
.page-header {
    background: var(--bg-primary);
    border-radius: var(--border-radius);
    padding: 40px;
    margin-bottom: 30px;
    box-shadow: var(--shadow-lg);
    text-align: center;
}

.page-header h1 {
    font-size: 3em;
    background: var(--bg-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
    font-weight: 800;
}

.page-header p {
    color: var(--text-secondary);
    font-size: 1.2em;
}

.header-meta {
    font-size: 0.9em !important;
    margin-top: 10px;
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: var(--bg-primary);
    border-radius: var(--border-radius);
    padding: 30px;
    box-shadow: var(--shadow-md);
    text-align: center;
    transition: transform var(--transition-speed) ease;
}

.stat-card:hover {
    transform: translateY(-5px);
}

.stat-icon {
    font-size: 3em;
    margin-bottom: 10px;
}

.stat-number {
    font-size: 3em;
    font-weight: bold;
    background: var(--bg-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-label {
    color: var(--text-secondary);
    margin-top: 10px;
    font-size: 0.9em;
}

/* Search Container */
.search-container {
    background: var(--bg-primary);
    border-radius: var(--border-radius);
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: var(--shadow-md);
}

.search-box input {
    width: 100%;
    padding: 15px 20px;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    font-size: 1.1em;
    background: var(--bg-primary);
    color: var(--text-primary);
    transition: border-color var(--transition-speed) ease;
}

.search-box input:focus {
    outline: none;
    border-color: var(--accent-primary);
}

.filters {
    display: flex;
    gap: 15px;
    margin-top: 15px;
    flex-wrap: wrap;
}

.filters select {
    flex: 1;
    min-width: 150px;
    padding: 10px 15px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-primary);
    color: var(--text-primary);
    cursor: pointer;
    font-size: 0.95em;
}

.reset-btn {
    padding: 10px 20px;
    background: var(--accent-primary);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.95em;
    transition: all var(--transition-speed) ease;
}

.reset-btn:hover {
    background: var(--accent-secondary);
    transform: translateY(-2px);
}

/* Category Section */
.category-section {
    margin-bottom: 40px;
}

.category-title {
    color: var(--text-primary);
    margin-bottom: 20px;
    padding: 15px 20px;
    background: var(--bg-primary);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-sm);
    display: flex;
    align-items: center;
    gap: 15px;
}

.category-icon {
    font-size: 1.5em;
}

.category-name {
    flex: 1;
    font-size: 1.5em;
}

.category-count {
    font-size: 0.7em;
    color: var(--text-tertiary);
}

/* File Grid */
.file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
}

/* Enhanced File Cards */
.file-card.enhanced {
    background: var(--bg-primary);
    border-radius: var(--border-radius);
    padding: 20px;
    box-shadow: var(--shadow-md);
    transition: all var(--transition-speed) ease;
    animation: fadeInUp 0.4s ease-out;
    animation-fill-mode: both;
    border: 1px solid var(--border-color);
}

.file-card.enhanced:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.file-type-badge {
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 0.75em;
    font-weight: 600;
    text-transform: uppercase;
    background: var(--accent-primary);
    color: white;
}

.file-type-badge.json { background: #f093fb; }
.file-type-badge.html { background: #667eea; }
.file-type-badge.csv { background: #4facfe; }
.file-type-badge.md { background: #43e97b; }

.file-size {
    font-size: 0.85em;
    color: var(--text-tertiary);
}

.card-title {
    font-size: 1.2em;
    color: var(--text-primary);
    margin-bottom: 12px;
    word-break: break-word;
}

.card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 15px;
}

.meta-item {
    font-size: 0.85em;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    padding: 4px 10px;
    border-radius: 6px;
}

.card-preview {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    max-height: 150px;
    overflow: auto;
}

.card-preview pre {
    margin: 0;
    font-size: 0.85em;
    color: var(--text-secondary);
}

.card-preview code {
    font-family: 'Fira Code', 'Monaco', monospace;
}

.card-actions {
    display: flex;
    gap: 10px;
}

.btn {
    flex: 1;
    padding: 10px 15px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9em;
    text-decoration: none;
    text-align: center;
    transition: all var(--transition-speed) ease;
}

.btn-primary {
    background: var(--accent-primary);
    color: white;
}

.btn-primary:hover {
    background: var(--accent-secondary);
    transform: translateY(-2px);
}

.btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: var(--bg-tertiary);
}

/* Footer */
.page-footer {
    text-align: center;
    color: white;
    margin-top: 50px;
    padding: 30px;
}

.page-footer p {
    margin: 5px 0;
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Stagger animation */
.file-card:nth-child(1) { animation-delay: 0.05s; }
.file-card:nth-child(2) { animation-delay: 0.1s; }
.file-card:nth-child(3) { animation-delay: 0.15s; }
.file-card:nth-child(4) { animation-delay: 0.2s; }
.file-card:nth-child(5) { animation-delay: 0.25s; }
.file-card:nth-child(6) { animation-delay: 0.3s; }

/* Responsive */
@media (max-width: 1024px) {
    .file-grid {
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    }
}

@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
    }

    .sidebar.open {
        transform: translateX(0);
    }

    .sidebar-toggle {
        display: block;
    }

    .main-content {
        margin-left: 0;
    }

    .page-header h1 {
        font-size: 2em;
    }

    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .file-grid {
        grid-template-columns: 1fr;
    }

    .filters {
        flex-direction: column;
    }

    .filters select {
        width: 100%;
    }
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--accent-primary);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-secondary);
}
"""

        css_path = self.assets_dir / "css" / "enhanced.css"
        css_path.write_text(css, encoding='utf-8')
        print(f"  ✓ Создан: {css_path}")

    def generate_js(self):
        """Генерация JavaScript для интерактивности"""
        print("⚡ Генерация enhanced.js...")

        js = """// Enhanced Dashboard JavaScript v1.0

// Theme Management
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Add transition class
    document.body.classList.add('theme-transitioning');
    setTimeout(() => {
        document.body.classList.remove('theme-transitioning');
    }, 300);
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

// Sidebar Toggle (mobile)
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// Advanced Filtering
function filterFiles() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const typeFilter = document.getElementById('type-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const sizeFilter = document.getElementById('size-filter').value;

    const fileCards = document.querySelectorAll('.file-card.enhanced');

    let visibleCount = 0;

    fileCards.forEach(card => {
        const filename = card.getAttribute('data-filename');
        const cardType = card.getAttribute('data-type');
        const cardCategory = card.getAttribute('data-category');
        const cardSize = card.getAttribute('data-size');

        // Check all criteria
        const matchesSearch = filename.includes(searchTerm);
        const matchesType = !typeFilter || cardType === typeFilter;
        const matchesCategory = !categoryFilter || cardCategory === categoryFilter;
        const matchesSize = !sizeFilter || cardSize === sizeFilter;

        const isVisible = matchesSearch && matchesType && matchesCategory && matchesSize;

        if (isVisible) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Update visibility stats
    console.log(`Showing ${visibleCount} of ${fileCards.length} files`);
}

function resetFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('type-filter').value = '';
    document.getElementById('category-filter').value = '';
    document.getElementById('size-filter').value = '';

    filterFiles();
}

// Copy path to clipboard
async function copyPath(path) {
    try {
        await navigator.clipboard.writeText(path);
        showNotification('Путь скопирован: ' + path);
    } catch (err) {
        console.error('Failed to copy:', err);
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = path;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('Путь скопирован: ' + path);
    }
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: var(--accent-primary);
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Smooth scroll for navigation links
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link[href^="#"]');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Close sidebar on mobile
                if (window.innerWidth <= 768) {
                    const sidebar = document.querySelector('.sidebar');
                    sidebar.classList.remove('open');
                }
            }
        });
    });
});

// Add slide animations to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
"""

        js_path = self.assets_dir / "js" / "enhanced.js"
        js_path.write_text(js, encoding='utf-8')
        print(f"  ✓ Создан: {js_path}")

    def get_size_class(self, size: int) -> str:
        """Определить класс размера для фильтрации"""
        if size < 1024:  # < 1 KB
            return "tiny"
        elif size < 10 * 1024:  # 1-10 KB
            return "small"
        elif size < 100 * 1024:  # 10-100 KB
            return "medium"
        elif size < 1024 * 1024:  # 100KB - 1MB
            return "large"
        else:  # > 1 MB
            return "huge"

    @staticmethod
    def format_size(size: int) -> str:
        """Форматировать размер файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def generate(self):
        """Главная функция генерации"""
        print("\n" + "="*70)
        print("  🎨  ENHANCED SITE GENERATOR v1.0 - QUICK WINS")
        print("="*70 + "\n")

        self.scan_outputs()
        self.generate_enhanced_index()
        self.generate_css()
        self.generate_js()

        print("\n" + "="*70)
        print("  ✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
        print("="*70)
        print(f"\nОткройте: {self.output_dir / 'index.html'}")
        print(f"  или запустите: python -m http.server 8000 --directory {self.output_dir}")
        print(f"  затем откройте: http://localhost:8000\n")
        print("Улучшения v1.0:")
        print("  ✓ Расширенный поиск с фильтрами")
        print("  ✓ Sidebar навигация")
        print("  ✓ Карточки с preview и метаданными")
        print("  ✓ Dark mode toggle")
        print("  ✓ Улучшенная типографика и анимации\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced Site Generator v1.0 для Knowledge Base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s                    # Генерация с настройками по умолчанию
  %(prog)s --root /path/to/kb # Указать другую директорию

Улучшения v1.0 (Quick Wins):
  - Расширенный поиск с фильтрами (тип, категория, размер)
  - Sidebar навигация с быстрым доступом
  - Карточки с preview и метаданными
  - Dark/Light mode toggle
  - Улучшенная типографика и плавные анимации
        """
    )

    parser.add_argument(
        '--root',
        type=Path,
        default=Path(".").parent,
        help='Корневая директория проекта (по умолчанию: ..)'
    )

    args = parser.parse_args()

    generator = EnhancedSiteGenerator(root_dir=args.root)
    generator.generate()


if __name__ == "__main__":
    main()
