#!/usr/bin/env python3
"""
Multi-Page Site Generator v3.0 - Phase 3
Создаёт полноценное многостраничное приложение с PWA features:
- Отдельные страницы для каждого раздела
- PWA support (manifest.json, service worker)
- Advanced search page
- Offline работа
- Улучшенная навигация
"""

from pathlib import Path
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
import re

class MultiPageGenerator:
    """Генератор многостраничного сайта"""

    def __init__(self, root_dir: Path = Path(".")):
        self.root_dir = Path(root_dir)
        self.output_dir = self.root_dir / "static_site" / "public"
        self.assets_dir = self.output_dir / "assets"
        self.pages_dir = self.output_dir / "pages"

        # Создать директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        (self.assets_dir / "css").mkdir(exist_ok=True)
        (self.assets_dir / "js").mkdir(exist_ok=True)
        (self.assets_dir / "icons").mkdir(exist_ok=True)

        # Собрать все файлы
        self.html_files = []
        self.json_files = []
        self.csv_files = []
        self.reports = []
        self.all_files = []

    def scan_outputs(self):
        """Сканировать все сгенерированные файлы"""
        print("📊 Сканирование outputs...")

        self.html_files = sorted(self.root_dir.glob("*.html"))
        self.json_files = sorted([f for f in self.root_dir.glob("*.json")
                                  if not f.name.startswith('.')])
        self.csv_files = sorted(self.root_dir.glob("*.csv"))

        self.reports = sorted(self.root_dir.glob("*REPORT*.md"))
        self.reports += sorted(self.root_dir.glob("*SUMMARY*.md"))
        self.reports += sorted(self.root_dir.glob("COMPLETE_*.md"))
        self.reports = list(set(self.reports))

        self.all_files = self.html_files + self.json_files + self.csv_files + self.reports

        print(f"  HTML: {len(self.html_files)} файлов")
        print(f"  JSON: {len(self.json_files)} файлов")
        print(f"  CSV: {len(self.csv_files)} файлов")
        print(f"  Reports: {len(self.reports)} файлов")

    def categorize_files(self) -> Dict[str, List[Path]]:
        """Категоризация файлов"""
        categories = {
            "visualizations": [],
            "graphs": [],
            "stats": [],
            "reports": [],
            "data": [],
            "tables": [],
        }

        for html in self.html_files:
            name_lower = html.name.lower()
            if any(k in name_lower for k in ['graph', 'network', 'viz']):
                categories["graphs"].append(html)
            elif any(k in name_lower for k in ['stat', 'dashboard', 'metric']):
                categories["stats"].append(html)
            else:
                categories["visualizations"].append(html)

        categories["reports"] = self.reports
        categories["data"] = self.json_files
        categories["tables"] = self.csv_files

        return categories

    def get_navigation_html(self, current_page: str = "") -> str:
        """Общая навигация для всех страниц"""
        nav_items = [
            ("index.html", "🏠 Dashboard", "home"),
            ("pages/explorer.html", "🔍 Data Explorer", "explorer"),
            ("pages/visualizations.html", "📊 Visualizations", "visualizations"),
            ("pages/reports.html", "📄 Reports", "reports"),
            ("pages/graph.html", "🕸️ Graph", "graph"),
            ("pages/search.html", "🔎 Search", "search"),
        ]

        html = '<nav class="main-nav">\n'
        html += '  <div class="nav-brand">\n'
        html += '    <h1>📚 Knowledge Base</h1>\n'
        html += '  </div>\n'
        html += '  <ul class="nav-links">\n'

        for link, label, page_id in nav_items:
            active = ' class="active"' if current_page == page_id else ''
            # Adjust path based on current location
            href = link if current_page == "home" else f"../{link}"
            html += f'    <li><a href="{href}"{active}>{label}</a></li>\n'

        html += '  </ul>\n'
        html += '  <div class="nav-actions">\n'
        html += '    <button onclick="toggleTheme()" class="btn-icon" title="Toggle theme">🌓</button>\n'
        html += '    <button onclick="installPWA()" id="install-btn" class="btn-icon" title="Install App" style="display:none">📲</button>\n'
        html += '  </div>\n'
        html += '</nav>\n'

        return html

    def get_page_template(self, title: str, page_id: str) -> str:
        """Базовый шаблон страницы"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Knowledge Base - {title}">
    <meta name="theme-color" content="#667eea">
    <title>{title} - Knowledge Base</title>

    <!-- PWA Meta -->
    <link rel="manifest" href="../manifest.json">
    <link rel="apple-touch-icon" href="../assets/icons/icon-192.png">

    <!-- Styles -->
    <link rel="stylesheet" href="../assets/css/enhanced.css">
    <link rel="stylesheet" href="../assets/css/multipage.css">
    <link rel="stylesheet" href="../assets/css/tool-runner.css">

    <!-- External Libraries -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
</head>
<body data-page="{page_id}">
    {self.get_navigation_html(page_id)}

    <main class="page-content">
        {{CONTENT}}
    </main>

    <footer class="page-footer">
        <p>🚀 Knowledge Base v4.0 - Multi-Page PWA + Backend API</p>
        <p>Phase 1 + Phase 2 + Phase 3 + Phase 4 | Full Integration</p>
    </footer>

    <!-- Scripts -->
    <script src="../assets/js/enhanced.js"></script>
    <script src="../assets/js/data-explorer.js"></script>
    <script src="../assets/js/dashboard.js"></script>
    <script src="../assets/js/graph-viewer.js"></script>
    <script src="../assets/js/pwa.js"></script>
    <script src="../assets/js/api-client.js"></script>
    <script src="../assets/js/tool-runner.js"></script>
</body>
</html>
"""

    def generate_index(self):
        """Генерация главной страницы (Dashboard)"""
        print("📄 Генерация index.html (Dashboard)...")

        categories = self.categorize_files()

        content = f"""
        <header class="page-header">
            <h1>📚 Knowledge Base Dashboard</h1>
            <p>Централизованный доступ ко всем данным и визуализациям</p>
            <p class="header-meta">Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <!-- Quick Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-number">{len(self.all_files)}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-number">{len(self.html_files)}</div>
                <div class="stat-label">Visualizations</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-number">{len(self.json_files)}</div>
                <div class="stat-label">Data Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-number">{len(self.reports)}</div>
                <div class="stat-label">Reports</div>
            </div>
        </div>

        <!-- Quick Links -->
        <div class="quick-links">
            <h2>Quick Access</h2>
            <div class="links-grid">
                <a href="pages/explorer.html" class="link-card">
                    <div class="link-icon">🔍</div>
                    <h3>Data Explorer</h3>
                    <p>Интерактивный просмотр JSON/CSV</p>
                </a>
                <a href="pages/visualizations.html" class="link-card">
                    <div class="link-icon">📊</div>
                    <h3>Visualizations</h3>
                    <p>Галерея визуализаций ({len(self.html_files)})</p>
                </a>
                <a href="pages/reports.html" class="link-card">
                    <div class="link-icon">📄</div>
                    <h3>Reports</h3>
                    <p>Markdown отчёты ({len(self.reports)})</p>
                </a>
                <a href="pages/graph.html" class="link-card">
                    <div class="link-icon">🕸️</div>
                    <h3>Knowledge Graph</h3>
                    <p>Визуализация связей</p>
                </a>
                <a href="pages/search.html" class="link-card">
                    <div class="link-icon">🔎</div>
                    <h3>Advanced Search</h3>
                    <p>Поиск по всем файлам</p>
                </a>
            </div>
        </div>

        <!-- Mini Dashboard (будет подключен dashboard.js) -->
        <div id="mini-dashboard-placeholder"></div>
        """

        # Использовать home template
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Knowledge Base - Interactive Dashboard">
    <meta name="theme-color" content="#667eea">
    <title>Dashboard - Knowledge Base</title>

    <!-- PWA Meta -->
    <link rel="manifest" href="manifest.json">
    <link rel="apple-touch-icon" href="assets/icons/icon-192.png">

    <!-- Styles -->
    <link rel="stylesheet" href="assets/css/enhanced.css">
    <link rel="stylesheet" href="assets/css/multipage.css">
    <link rel="stylesheet" href="assets/css/tool-runner.css">

    <!-- External Libraries -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
</head>
<body data-page="home">
    {self.get_navigation_html("home")}

    <main class="page-content">
        {content}
    </main>

    <footer class="page-footer">
        <p>🚀 Knowledge Base v4.0 - Multi-Page PWA + Backend API</p>
        <p>Phase 1 + Phase 2 + Phase 3 + Phase 4 | Full Integration</p>
    </footer>

    <!-- Scripts -->
    <script src="assets/js/enhanced.js"></script>
    <script src="assets/js/data-explorer.js"></script>
    <script src="assets/js/dashboard.js"></script>
    <script src="assets/js/graph-viewer.js"></script>
    <script src="assets/js/pwa.js"></script>
    <script src="assets/js/api-client.js"></script>
    <script src="assets/js/tool-runner.js"></script>
</body>
</html>
"""

        (self.output_dir / "index.html").write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: index.html")

    def generate_explorer_page(self):
        """Генерация страницы Data Explorer"""
        print("📄 Генерация explorer.html...")

        content = f"""
        <header class="page-header">
            <h1>🔍 Data Explorer</h1>
            <p>Интерактивный просмотр и анализ JSON/CSV файлов</p>
        </header>

        <div class="explorer-page">
            <div class="file-browser">
                <h2>Available Data Files</h2>
                <div class="file-list">
"""

        # JSON files
        content += '                    <div class="file-category">\n'
        content += '                        <h3>💾 JSON Files ({}))</h3>\n'.format(len(self.json_files))
        for json_file in self.json_files[:20]:  # Первые 20
            rel_path = json_file.relative_to(self.root_dir)
            size = self.format_size(json_file.stat().st_size)
            content += f'''
                        <button class="file-item" onclick="dataExplorer.open('../../{rel_path}')">
                            <span class="file-name">{json_file.stem}</span>
                            <span class="file-size">{size}</span>
                        </button>
'''

        content += '                    </div>\n'

        # CSV files
        if self.csv_files:
            content += '                    <div class="file-category">\n'
            content += '                        <h3>📋 CSV Files ({})</h3>\n'.format(len(self.csv_files))
            for csv_file in self.csv_files:
                rel_path = csv_file.relative_to(self.root_dir)
                size = self.format_size(csv_file.stat().st_size)
                content += f'''
                        <button class="file-item" onclick="dataExplorer.open('../../{rel_path}')">
                            <span class="file-name">{csv_file.stem}</span>
                            <span class="file-size">{size}</span>
                        </button>
'''
            content += '                    </div>\n'

        content += """
                </div>
            </div>
        </div>

        <!-- Data Explorer будет создан через data-explorer.js -->
        """

        html = self.get_page_template("Data Explorer", "explorer")
        html = html.replace("{{CONTENT}}", content)

        (self.pages_dir / "explorer.html").write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: pages/explorer.html")

    def generate_visualizations_page(self):
        """Генерация страницы визуализаций"""
        print("📄 Генерация visualizations.html...")

        content = """
        <header class="page-header">
            <h1>📊 Visualizations Gallery</h1>
            <p>Галерея всех HTML визуализаций</p>
        </header>

        <div class="viz-gallery">
"""

        for html_file in self.html_files:
            rel_path = html_file.relative_to(self.root_dir)
            size = self.format_size(html_file.stat().st_size)

            content += f"""
            <div class="viz-card">
                <div class="viz-preview">
                    <iframe src="../../{rel_path}" loading="lazy"></iframe>
                </div>
                <div class="viz-info">
                    <h3>{html_file.stem}</h3>
                    <div class="viz-meta">
                        <span>📏 {size}</span>
                        <a href="../../{rel_path}" target="_blank" class="btn btn-primary">
                            Open Full
                        </a>
                    </div>
                </div>
            </div>
"""

        content += """
        </div>
        """

        html = self.get_page_template("Visualizations", "visualizations")
        html = html.replace("{{CONTENT}}", content)

        (self.pages_dir / "visualizations.html").write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: pages/visualizations.html")

    def generate_reports_page(self):
        """Генерация страницы отчётов"""
        print("📄 Генерация reports.html...")

        content = f"""
        <header class="page-header">
            <h1>📄 Reports</h1>
            <p>Все Markdown отчёты ({len(self.reports)})</p>
        </header>

        <div class="reports-list">
"""

        for report in self.reports:
            rel_path = report.relative_to(self.root_dir)
            size = self.format_size(report.stat().st_size)

            content += f"""
            <div class="report-card">
                <div class="report-icon">📄</div>
                <div class="report-content">
                    <h3>{report.stem.replace('_', ' ')}</h3>
                    <div class="report-meta">
                        <span>📏 {size}</span>
                        <span>📅 {datetime.fromtimestamp(report.stat().st_mtime).strftime('%Y-%m-%d')}</span>
                    </div>
                </div>
                <a href="../../{rel_path}" target="_blank" class="btn btn-secondary">
                    View Report
                </a>
            </div>
"""

        content += """
        </div>
        """

        html = self.get_page_template("Reports", "reports")
        html = html.replace("{{CONTENT}}", content)

        (self.pages_dir / "reports.html").write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: pages/reports.html")

    def generate_graph_page(self):
        """Генерация страницы графа"""
        print("📄 Генерация graph.html...")

        content = """
        <header class="page-header">
            <h1>🕸️ Knowledge Graph</h1>
            <p>Визуализация связей между файлами</p>
        </header>

        <!-- Graph Viewer будет создан через graph-viewer.js -->
        <div id="graph-viewer-placeholder" style="min-height: 600px;"></div>
        """

        html = self.get_page_template("Knowledge Graph", "graph")
        html = html.replace("{{CONTENT}}", content)

        (self.pages_dir / "graph.html").write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: pages/graph.html")

    def generate_search_page(self):
        """Генерация страницы поиска"""
        print("📄 Генерация search.html...")

        content = """
        <header class="page-header">
            <h1>🔎 Advanced Search</h1>
            <p>Поиск по всем файлам с расширенными фильтрами</p>
        </header>

        <div class="search-page">
            <div class="search-container-advanced">
                <input type="text" id="search-input-advanced" placeholder="🔍 Введите поисковый запрос..." class="search-input-large">

                <div class="search-filters-advanced">
                    <select id="type-filter-advanced" class="filter-select">
                        <option value="">Все типы</option>
                        <option value="html">HTML</option>
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                        <option value="md">Markdown</option>
                    </select>

                    <select id="size-filter-advanced" class="filter-select">
                        <option value="">Любой размер</option>
                        <option value="tiny">< 1 KB</option>
                        <option value="small">1-10 KB</option>
                        <option value="medium">10-100 KB</option>
                        <option value="large">100KB - 1MB</option>
                        <option value="huge">> 1 MB</option>
                    </select>

                    <button onclick="performSearch()" class="btn btn-primary">
                        Search
                    </button>
                    <button onclick="resetSearch()" class="btn btn-secondary">
                        Reset
                    </button>
                </div>
            </div>

            <div id="search-results" class="search-results">
                <p class="search-placeholder">Введите запрос для поиска...</p>
            </div>
        </div>

        <script>
        // Загрузить все файлы для поиска
        const allFiles = """ + json.dumps([{
            'name': f.name,
            'stem': f.stem,
            'type': f.suffix[1:],
            'size': f.stat().st_size,
            'path': str(f.relative_to(self.root_dir))
        } for f in self.all_files], ensure_ascii=False) + """;

        function performSearch() {
            const query = document.getElementById('search-input-advanced').value.toLowerCase();
            const typeFilter = document.getElementById('type-filter-advanced').value;
            const sizeFilter = document.getElementById('size-filter-advanced').value;

            if (!query && !typeFilter && !sizeFilter) {
                document.getElementById('search-results').innerHTML = '<p class="search-placeholder">Введите запрос для поиска...</p>';
                return;
            }

            const results = allFiles.filter(file => {
                const matchesQuery = !query || file.stem.toLowerCase().includes(query) || file.name.toLowerCase().includes(query);
                const matchesType = !typeFilter || file.type === typeFilter;
                const matchesSize = !sizeFilter || checkSizeMatch(file.size, sizeFilter);

                return matchesQuery && matchesType && matchesSize;
            });

            displayResults(results);
        }

        function checkSizeMatch(size, filter) {
            const KB = 1024;
            const MB = KB * 1024;

            switch(filter) {
                case 'tiny': return size < KB;
                case 'small': return size >= KB && size < 10 * KB;
                case 'medium': return size >= 10 * KB && size < 100 * KB;
                case 'large': return size >= 100 * KB && size < MB;
                case 'huge': return size >= MB;
                default: return true;
            }
        }

        function displayResults(results) {
            const container = document.getElementById('search-results');

            if (results.length === 0) {
                container.innerHTML = '<p class="search-placeholder">Нет результатов</p>';
                return;
            }

            let html = `<h2>Найдено: ${results.length}</h2><div class="results-grid">`;

            results.forEach(file => {
                const size = formatBytes(file.size);
                html += `
                    <div class="result-card">
                        <div class="result-type ${file.type}">${file.type.toUpperCase()}</div>
                        <h3>${file.stem}</h3>
                        <p class="result-meta">${size}</p>
                        <a href="../../${file.path}" target="_blank" class="btn btn-primary">Open</a>
                    </div>
                `;
            });

            html += '</div>';
            container.innerHTML = html;
        }

        function resetSearch() {
            document.getElementById('search-input-advanced').value = '';
            document.getElementById('type-filter-advanced').value = '';
            document.getElementById('size-filter-advanced').value = '';
            document.getElementById('search-results').innerHTML = '<p class="search-placeholder">Введите запрос для поиска...</p>';
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        // Поиск при Enter
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('search-input-advanced').addEventListener('keyup', (e) => {
                if (e.key === 'Enter') performSearch();
            });
        });
        </script>
        """

        html = self.get_page_template("Advanced Search", "search")
        html = html.replace("{{CONTENT}}", content)

        (self.pages_dir / "search.html").write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: pages/search.html")

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
        print("  🏗️  MULTI-PAGE SITE GENERATOR v3.0 - PHASE 3")
        print("="*70 + "\n")

        self.scan_outputs()

        print("\n📄 Генерация страниц...")
        self.generate_index()
        self.generate_explorer_page()
        self.generate_visualizations_page()
        self.generate_reports_page()
        self.generate_graph_page()
        self.generate_search_page()

        print("\n" + "="*70)
        print("  ✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
        print("="*70)
        print(f"\nСтраницы созданы:")
        print(f"  - index.html (Dashboard)")
        print(f"  - pages/explorer.html (Data Explorer)")
        print(f"  - pages/visualizations.html (Gallery)")
        print(f"  - pages/reports.html (Reports)")
        print(f"  - pages/graph.html (Knowledge Graph)")
        print(f"  - pages/search.html (Advanced Search)")
        print(f"\nЗапустите: python -m http.server 8000 --directory {self.output_dir}")
        print(f"Откройте: http://localhost:8000\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Multi-Page Site Generator v3.0 - Phase 3',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--root',
        type=Path,
        default=Path(".").parent,
        help='Корневая директория проекта (default: ..)'
    )

    args = parser.parse_args()

    generator = MultiPageGenerator(root_dir=args.root)
    generator.generate()


if __name__ == "__main__":
    main()
