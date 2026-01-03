#!/usr/bin/env python3
"""
Static Site Generator - Простая альтернатива Hugo
Генерирует статический сайт из всех outputs (HTML/JSON/CSV)
"""

from pathlib import Path
import json
import shutil
from datetime import datetime
from typing import List, Dict
import re

class SiteGenerator:
    """Генератор статического сайта из outputs"""

    def __init__(self, root_dir: Path = Path(".")):
        self.root_dir = Path(root_dir)
        self.output_dir = self.root_dir / "static_site" / "public"
        self.template_dir = self.root_dir / "static_site" / "templates"
        self.assets_dir = self.root_dir / "static_site" / "assets"

        # Создать директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # Собрать все файлы
        self.html_files = []
        self.json_files = []
        self.csv_files = []
        self.reports = []

    def scan_outputs(self):
        """Сканировать все сгенерированные файлы"""
        print("📊 Сканирование outputs...")

        # HTML files
        self.html_files = sorted(self.root_dir.glob("*.html"))
        print(f"  HTML: {len(self.html_files)} файлов")

        # JSON files
        self.json_files = sorted(self.root_dir.glob("*.json"))
        # Исключить некоторые служебные
        self.json_files = [f for f in self.json_files if not f.name.startswith('.')]
        print(f"  JSON: {len(self.json_files)} файлов")

        # CSV files
        self.csv_files = sorted(self.root_dir.glob("*.csv"))
        print(f"  CSV: {len(self.csv_files)} файлов")

        # Markdown reports
        self.reports = sorted(self.root_dir.glob("*REPORT*.md"))
        self.reports += sorted(self.root_dir.glob("*SUMMARY*.md"))
        self.reports += sorted(self.root_dir.glob("COMPLETE_*.md"))
        self.reports = list(set(self.reports))  # Уникальные
        print(f"  Reports: {len(self.reports)} файлов")

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

        # Отчёты
        categories["Отчёты"] = self.reports

        # Данные
        categories["Данные (JSON)"] = self.json_files
        categories["Таблицы (CSV)"] = self.csv_files

        return categories

    def generate_index(self):
        """Генерация главной страницы"""
        print("📄 Генерация index.html...")

        categories = self.categorize_files()

        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Base - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #2c3e50;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }

        header h1 {
            font-size: 3em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        header p {
            color: #7f8c8d;
            font-size: 1.2em;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-number {
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            color: #7f8c8d;
            margin-top: 10px;
            font-size: 0.9em;
        }

        .category {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }

        .category h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
        }

        .category h2::before {
            content: '📊';
            margin-right: 10px;
            font-size: 1.3em;
        }

        .file-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .file-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
            display: block;
        }

        .file-card:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            background: #fff;
        }

        .file-name {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            word-break: break-word;
        }

        .file-meta {
            font-size: 0.85em;
            color: #7f8c8d;
            display: flex;
            justify-content: space-between;
        }

        .file-type {
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            text-transform: uppercase;
        }

        .search-box {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .search-box input {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1.1em;
            transition: border-color 0.3s ease;
        }

        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }

        footer {
            text-align: center;
            color: white;
            margin-top: 50px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Knowledge Base</h1>
            <p>Централизованный доступ ко всем визуализациям и данным</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Сгенерировано: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">""" + str(len(self.html_files)) + """</div>
                <div class="stat-label">HTML Визуализаций</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(self.json_files)) + """</div>
                <div class="stat-label">JSON Datasets</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(self.csv_files)) + """</div>
                <div class="stat-label">CSV Tables</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(self.reports)) + """</div>
                <div class="stat-label">Markdown Reports</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="search" placeholder="🔍 Поиск по файлам..." onkeyup="filterFiles()">
        </div>
"""

        # Генерация категорий
        category_icons = {
            "Визуализации": "📊",
            "Графы и сети": "🕸️",
            "Статистика": "📈",
            "Отчёты": "📄",
            "Данные (JSON)": "💾",
            "Таблицы (CSV)": "📋",
        }

        for cat_name, files in categories.items():
            if not files:
                continue

            icon = category_icons.get(cat_name, "📁")
            html += f"""
        <div class="category" data-category="{cat_name}">
            <h2 style="position: relative;">
                <span style="position: absolute; left: -5px;">{icon}</span>
                <span style="margin-left: 30px;">{cat_name}</span>
                <span style="margin-left: auto; font-size: 0.6em; color: #7f8c8d;">({len(files)})</span>
            </h2>
            <div class="file-grid">
"""

            for file in files:
                file_type = file.suffix[1:].upper()
                file_size = file.stat().st_size
                size_str = self.format_size(file_size)

                # Относительный путь
                rel_path = file.relative_to(self.root_dir)

                html += f"""
                <a href="../{rel_path}" class="file-card" data-filename="{file.name.lower()}">
                    <div class="file-name">{file.stem}</div>
                    <div class="file-meta">
                        <span class="file-type">{file_type}</span>
                        <span>{size_str}</span>
                    </div>
                </a>
"""

            html += """
            </div>
        </div>
"""

        html += """
    </div>

    <footer>
        <p>🚀 Generated by Knowledge Base Static Site Generator</p>
        <p style="margin-top: 10px; font-size: 0.9em;">55 инструментов | 25+ алгоритмов | Production Ready</p>
    </footer>

    <script>
        function filterFiles() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const fileCards = document.querySelectorAll('.file-card');

            fileCards.forEach(card => {
                const filename = card.getAttribute('data-filename');
                if (filename.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

        # Сохранить
        index_path = self.output_dir / "index.html"
        index_path.write_text(html, encoding='utf-8')
        print(f"  ✓ Создан: {index_path}")

    @staticmethod
    def format_size(size: int) -> str:
        """Форматировать размер файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def copy_outputs(self):
        """Копировать все outputs в public/"""
        print("📂 Копирование файлов...")

        # Создать outputs директорию
        outputs_dir = self.output_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        # Копировать все файлы
        all_files = self.html_files + self.json_files + self.csv_files + self.reports
        for file in all_files:
            dest = outputs_dir / file.name
            shutil.copy2(file, dest)

        print(f"  ✓ Скопировано {len(all_files)} файлов")

    def generate(self):
        """Главная функция генерации"""
        print("\n" + "="*60)
        print("  🏗️  STATIC SITE GENERATOR")
        print("="*60 + "\n")

        self.scan_outputs()
        self.generate_index()

        print("\n" + "="*60)
        print("  ✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
        print("="*60)
        print(f"\nОткройте: {self.output_dir / 'index.html'}")
        print(f"  или запустите: python -m http.server 8000 --directory {self.output_dir}")
        print(f"  затем откройте: http://localhost:8000\n")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Static Site Generator для Knowledge Base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s                    # Генерация с настройками по умолчанию
  %(prog)s --root /path/to/kb # Указать другую директорию
        """
    )

    parser.add_argument(
        '--root',
        type=Path,
        default=Path(".").parent,
        help='Корневая директория проекта (по умолчанию: ..)'
    )

    args = parser.parse_args()

    generator = SiteGenerator(root_dir=args.root)
    generator.generate()

if __name__ == "__main__":
    main()
