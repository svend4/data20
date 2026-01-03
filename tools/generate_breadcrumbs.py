#!/usr/bin/env python3
"""
Advanced Breadcrumbs Generator - Продвинутый генератор навигационных крошек
Функции:
- Smart path detection (множественные пути к одной статье)
- Context-aware breadcrumbs (разные крошки в зависимости от контекста)
- Schema.org BreadcrumbList (JSON-LD для SEO)
- Multiple trails (альтернативные пути навигации)
- Breadcrumb analytics (популярные пути)
- Hierarchical detection (автоматическое определение иерархии)
- Parent/child relationships (связи между статьями)
- Breadcrumb caching (для производительности)
- Custom breadcrumbs (через frontmatter)
- HTML/Markdown output

Вдохновлено: Schema.org, Google rich snippets, WordPress breadcrumbs, Yoast SEO
"""

from pathlib import Path
import yaml
import re
import json
from collections import defaultdict, Counter
import csv
from datetime import datetime
from typing import List, Dict, Set


class AdvancedBreadcrumbsGenerator:
    """Продвинутый генератор навигационных крошек"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Кэш для производительности
        self.cache = {}
        self.hierarchy = {}
        self.relationships = defaultdict(list)

        # Статистика
        self.breadcrumb_stats = defaultdict(int)

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None

    def build_hierarchy(self):
        """Построить иерархию статей"""
        print("🗂️  Построение иерархии...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, _ = self.extract_frontmatter_and_content(md_file)
            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Сохранить метаданные
            self.hierarchy[article_path] = {
                'title': frontmatter.get('title', md_file.stem),
                'category': frontmatter.get('category'),
                'subcategory': frontmatter.get('subcategory'),
                'parent': frontmatter.get('parent'),  # Явный родитель
                'breadcrumbs': frontmatter.get('breadcrumbs'),  # Кастомные крошки
                'path_parts': list(md_file.relative_to(self.knowledge_dir).parts)
            }

            # Построить отношения parent/child
            parent = frontmatter.get('parent')
            if parent:
                self.relationships[parent].append(article_path)

    def detect_smart_paths(self, article_path):
        """Определить возможные пути к статье"""
        paths = []

        if article_path not in self.hierarchy:
            return paths

        metadata = self.hierarchy[article_path]

        # Путь 1: На основе директорий (filesystem)
        filesystem_path = self.build_filesystem_path(article_path)
        if filesystem_path:
            paths.append({
                'type': 'filesystem',
                'trail': filesystem_path,
                'priority': 10
            })

        # Путь 2: На основе категории/подкатегории
        if metadata['category']:
            category_path = self.build_category_path(article_path)
            if category_path:
                paths.append({
                    'type': 'category',
                    'trail': category_path,
                    'priority': 20
                })

        # Путь 3: На основе явного parent (frontmatter)
        if metadata['parent']:
            parent_path = self.build_parent_path(article_path)
            if parent_path:
                paths.append({
                    'type': 'parent',
                    'trail': parent_path,
                    'priority': 30
                })

        # Путь 4: Кастомные крошки (highest priority)
        if metadata['breadcrumbs']:
            custom_path = self.build_custom_path(article_path)
            if custom_path:
                paths.append({
                    'type': 'custom',
                    'trail': custom_path,
                    'priority': 100
                })

        # Сортировать по приоритету
        paths.sort(key=lambda x: -x['priority'])

        return paths

    def build_filesystem_path(self, article_path):
        """Построить путь на основе файловой системы"""
        trail = []

        file_path = self.root_dir / article_path
        relative_path = file_path.relative_to(self.knowledge_dir)

        # Главная
        trail.append({
            'title': '🏠 Главная',
            'url': '/INDEX.md',
            'position': 1
        })

        # Части пути
        current_path = self.knowledge_dir
        for i, part in enumerate(relative_path.parts[:-1], start=2):
            current_path = current_path / part

            # Название части
            label = part.replace('-', ' ').replace('_', ' ').title()

            # Поиск INDEX.md
            index_file = current_path / "INDEX.md"
            if not index_file.exists():
                # Попробовать index/INDEX.md
                index_file = current_path / "index" / "INDEX.md"

            url = None
            if index_file.exists():
                url = str(index_file.relative_to(self.root_dir))

            trail.append({
                'title': label,
                'url': url,
                'position': i
            })

        # Текущая страница
        metadata = self.hierarchy.get(article_path, {})
        trail.append({
            'title': metadata.get('title', file_path.stem),
            'url': None,  # Текущая страница - без ссылки
            'position': len(trail) + 1
        })

        return trail

    def build_category_path(self, article_path):
        """Построить путь на основе категории"""
        metadata = self.hierarchy.get(article_path)
        if not metadata:
            return None

        trail = []

        # Главная
        trail.append({
            'title': '🏠 Главная',
            'url': '/INDEX.md',
            'position': 1
        })

        # Категория
        if metadata['category']:
            # Найти INDEX для категории
            category_index = self.find_index_by_category(metadata['category'])

            trail.append({
                'title': metadata['category'],
                'url': category_index,
                'position': 2
            })

        # Подкатегория
        if metadata['subcategory']:
            subcategory_index = self.find_index_by_subcategory(
                metadata['category'],
                metadata['subcategory']
            )

            trail.append({
                'title': metadata['subcategory'],
                'url': subcategory_index,
                'position': 3
            })

        # Текущая страница
        trail.append({
            'title': metadata['title'],
            'url': None,
            'position': len(trail) + 1
        })

        return trail

    def build_parent_path(self, article_path):
        """Построить путь на основе явного parent"""
        metadata = self.hierarchy.get(article_path)
        if not metadata or not metadata['parent']:
            return None

        trail = []

        # Рекурсивно собрать путь от корня
        def collect_parents(path, position=1):
            if path not in self.hierarchy:
                return position

            meta = self.hierarchy[path]

            # Если есть parent, сначала обработать его
            if meta['parent']:
                position = collect_parents(meta['parent'], position)

            # Добавить текущий уровень
            trail.append({
                'title': meta['title'],
                'url': path,
                'position': position
            })

            return position + 1

        # Главная
        trail.append({
            'title': '🏠 Главная',
            'url': '/INDEX.md',
            'position': 1
        })

        # Собрать родителей
        collect_parents(metadata['parent'], position=2)

        # Текущая страница
        trail.append({
            'title': metadata['title'],
            'url': None,
            'position': len(trail) + 1
        })

        return trail

    def build_custom_path(self, article_path):
        """Построить кастомный путь из frontmatter"""
        metadata = self.hierarchy.get(article_path)
        if not metadata or not metadata['breadcrumbs']:
            return None

        trail = []
        custom_crumbs = metadata['breadcrumbs']

        # Формат: [{"title": "Home", "url": "/INDEX.md"}, ...]
        if isinstance(custom_crumbs, list):
            for i, crumb in enumerate(custom_crumbs, start=1):
                if isinstance(crumb, dict):
                    trail.append({
                        'title': crumb.get('title', 'Untitled'),
                        'url': crumb.get('url'),
                        'position': i
                    })

        # Текущая страница
        trail.append({
            'title': metadata['title'],
            'url': None,
            'position': len(trail) + 1
        })

        return trail

    def find_index_by_category(self, category):
        """Найти INDEX для категории"""
        for path, meta in self.hierarchy.items():
            if path.endswith('INDEX.md') and category.lower() in path.lower():
                return path
        return None

    def find_index_by_subcategory(self, category, subcategory):
        """Найти INDEX для подкатегории"""
        for path, meta in self.hierarchy.items():
            if path.endswith('INDEX.md'):
                if category.lower() in path.lower() and subcategory.lower() in path.lower():
                    return path
        return None

    def generate_breadcrumbs(self, article_path, output_format='markdown'):
        """Создать навигационные крошки для статьи"""
        # Проверить кэш
        cache_key = f"{article_path}:{output_format}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Определить возможные пути
        paths = self.detect_smart_paths(article_path)

        if not paths:
            return None

        # Использовать путь с наивысшим приоритетом
        primary_path = paths[0]
        trail = primary_path['trail']

        # Статистика
        self.breadcrumb_stats[primary_path['type']] += 1

        # Форматирование
        if output_format == 'markdown':
            result = self.format_markdown(trail)
        elif output_format == 'html':
            result = self.format_html(trail)
        elif output_format == 'json-ld':
            result = self.format_json_ld(trail, article_path)
        else:
            result = None

        # Кэш
        self.cache[cache_key] = result

        return result

    def format_markdown(self, trail):
        """Форматировать в Markdown"""
        crumbs = []

        for item in trail:
            if item['url']:
                crumbs.append(f"[{item['title']}]({item['url']})")
            else:
                crumbs.append(item['title'])

        return " → ".join(crumbs)

    def format_html(self, trail):
        """Форматировать в HTML"""
        html = '<nav class="breadcrumbs" aria-label="breadcrumb">\n'
        html += '  <ol>\n'

        for item in trail:
            html += '    <li>'

            if item['url']:
                html += f'<a href="{item["url"]}">{item["title"]}</a>'
            else:
                html += f'<span aria-current="page">{item["title"]}</span>'

            html += '</li>\n'

        html += '  </ol>\n'
        html += '</nav>'

        return html

    def format_json_ld(self, trail, article_path):
        """Форматировать в JSON-LD (Schema.org BreadcrumbList)"""
        base_url = "https://example.com"  # Настройка

        breadcrumb_list = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": []
        }

        for item in trail:
            if item['url']:
                list_item = {
                    "@type": "ListItem",
                    "position": item['position'],
                    "name": item['title'],
                    "item": f"{base_url}/{item['url']}"
                }
                breadcrumb_list["itemListElement"].append(list_item)

        return json.dumps(breadcrumb_list, ensure_ascii=False, indent=2)

    def add_breadcrumbs_to_file(self, file_path, format='markdown'):
        """Добавить навигационные крошки в файл"""
        article_path = str(file_path.relative_to(self.root_dir))

        frontmatter_str, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return False

        # Создать крошки
        breadcrumbs = self.generate_breadcrumbs(article_path, output_format=format)

        if not breadcrumbs:
            return False

        # Удалить старые крошки (первая строка с → или 🏠)
        lines = content.split('\n')
        if lines and ('🏠' in lines[0] or '→' in lines[0]):
            lines = lines[1:]
            if lines and lines[0].strip() == '':
                lines = lines[1:]
            content = '\n'.join(lines)

        # Добавить новые крошки
        new_content = f"{breadcrumbs}\n\n{content}"

        # Собрать файл
        full_content = f"---\n{frontmatter_str}\n---\n\n{new_content}"

        # Записать
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return True

    def generate_analytics_report(self):
        """Создать отчёт по аналитике крошек"""
        lines = []
        lines.append("# 🍞 Breadcrumbs Analytics\n\n")

        # Статистика по типам
        lines.append("## Статистика по типам путей\n\n")

        total = sum(self.breadcrumb_stats.values())

        for path_type, count in sorted(self.breadcrumb_stats.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"- **{path_type}**: {count} ({pct:.1f}%)\n")

        lines.append(f"\n**Всего**: {total}\n\n")

        # Рекомендации
        lines.append("## Рекомендации\n\n")

        if self.breadcrumb_stats.get('custom', 0) < total * 0.1:
            lines.append("- ⚠️ Рассмотрите добавление кастомных breadcrumbs в frontmatter для важных статей\n")

        if self.breadcrumb_stats.get('parent', 0) > 0:
            lines.append("- ✅ Хорошо: используются явные parent отношения\n")

        output_file = self.root_dir / "BREADCRUMBS_ANALYTICS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Аналитика: {output_file}")

    def process_all(self, output_format='markdown', generate_schema=False):
        """Добавить крошки ко всем статьям"""
        print("🍞 Генерация продвинутых навигационных крошек...\n")

        # Построить иерархию
        self.build_hierarchy()

        count = 0
        schema_data = {}

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            try:
                # Добавить markdown крошки
                if self.add_breadcrumbs_to_file(md_file, format=output_format):
                    count += 1
                    print(f"✅ {article_path}")

                # Сгенерировать Schema.org JSON-LD
                if generate_schema:
                    paths = self.detect_smart_paths(article_path)
                    if paths:
                        trail = paths[0]['trail']
                        schema_data[article_path] = self.format_json_ld(trail, article_path)

            except Exception as e:
                print(f"⚠️  Ошибка {article_path}: {e}")

        print(f"\n✅ Обработано статей: {count}")

        # Сохранить Schema.org данные
        if generate_schema and schema_data:
            output_file = self.root_dir / "breadcrumbs_schema.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Schema.org JSON-LD: {output_file}")

        # Аналитика
        self.generate_analytics_report()


class PathAnalyzer:
    """Анализ путей и иерархий навигации"""

    def __init__(self, generator):
        self.generator = generator
        self.path_stats = Counter()
        self.depth_distribution = Counter()

    def analyze_paths(self):
        """Анализировать все пути"""
        print("📊 Анализ путей навигации...\n")

        for article_path in self.generator.hierarchy.keys():
            paths = self.generator.detect_smart_paths(article_path)

            for path_info in paths:
                self.path_stats[path_info['type']] += 1
                self.depth_distribution[len(path_info['trail'])] += 1

        print(f"   Проанализировано статей: {len(self.generator.hierarchy)}\n")

    def get_depth_statistics(self):
        """Статистика глубины навигации"""
        if not self.depth_distribution:
            return {}

        depths = list(self.depth_distribution.keys())
        total = sum(self.depth_distribution.values())

        return {
            'min_depth': min(depths),
            'max_depth': max(depths),
            'avg_depth': sum(d * c for d, c in self.depth_distribution.items()) / total,
            'distribution': dict(self.depth_distribution)
        }

    def find_deep_paths(self, threshold=5):
        """Найти слишком глубокие пути"""
        deep_paths = []

        for article_path in self.generator.hierarchy.keys():
            paths = self.generator.detect_smart_paths(article_path)

            for path_info in paths:
                if len(path_info['trail']) > threshold:
                    deep_paths.append({
                        'article': article_path,
                        'depth': len(path_info['trail']),
                        'type': path_info['type']
                    })

        return sorted(deep_paths, key=lambda x: -x['depth'])

    def generate_path_report(self):
        """Создать отчёт анализа путей"""
        lines = []
        lines.append("# 📊 Отчёт: Анализ путей навигации\n\n")

        # Статистика глубины
        depth_stats = self.get_depth_statistics()
        if depth_stats:
            lines.append("## Статистика глубины\n\n")
            lines.append(f"- **Минимальная глубина**: {depth_stats['min_depth']}\n")
            lines.append(f"- **Максимальная глубина**: {depth_stats['max_depth']}\n")
            lines.append(f"- **Средняя глубина**: {depth_stats['avg_depth']:.1f}\n\n")

            lines.append("### Распределение по глубине\n\n")
            for depth in sorted(depth_stats['distribution'].keys()):
                count = depth_stats['distribution'][depth]
                lines.append(f"- **Глубина {depth}**: {count} статей\n")
            lines.append("\n")

        # Глубокие пути
        deep = self.find_deep_paths(threshold=5)
        if deep:
            lines.append(f"## Слишком глубокие пути (>{5} уровней)\n\n")
            for item in deep[:15]:
                lines.append(f"- **{item['article']}**: глубина {item['depth']} ({item['type']})\n")
            lines.append("\n")

        return ''.join(lines)


class BreadcrumbOptimizer:
    """Оптимизация навигационных крошек"""

    def __init__(self, generator):
        self.generator = generator
        self.optimizations = []

    def optimize_all(self):
        """Выполнить все оптимизации"""
        print("⚡ Оптимизация breadcrumbs...\n")

        for article_path in self.generator.hierarchy.keys():
            paths = self.generator.detect_smart_paths(article_path)

            if not paths:
                self.optimizations.append({
                    'article': article_path,
                    'issue': 'no_paths',
                    'suggestion': 'Добавить breadcrumbs в frontmatter'
                })
                continue

            # Проверить, есть ли лучший путь
            best_path = paths[0]

            # Слишком длинный путь
            if len(best_path['trail']) > 6:
                self.optimizations.append({
                    'article': article_path,
                    'issue': 'too_deep',
                    'current_depth': len(best_path['trail']),
                    'suggestion': 'Упростить иерархию или использовать parent'
                })

            # Использование filesystem вместо категорий
            if best_path['type'] == 'filesystem':
                category_paths = [p for p in paths if p['type'] == 'category']
                if category_paths:
                    self.optimizations.append({
                        'article': article_path,
                        'issue': 'suboptimal_path',
                        'suggestion': 'Добавить категории в frontmatter для лучшей навигации'
                    })

        print(f"   Найдено оптимизаций: {len(self.optimizations)}\n")

    def get_optimization_summary(self):
        """Получить сводку оптимизаций"""
        issue_counts = Counter(opt['issue'] for opt in self.optimizations)

        return {
            'total': len(self.optimizations),
            'by_issue': dict(issue_counts)
        }

    def generate_optimization_report(self):
        """Создать отчёт оптимизаций"""
        lines = []
        lines.append("# ⚡ Отчёт: Оптимизация breadcrumbs\n\n")

        summary = self.get_optimization_summary()

        lines.append("## Сводка\n\n")
        lines.append(f"- **Всего рекомендаций**: {summary['total']}\n\n")

        for issue, count in summary['by_issue'].items():
            lines.append(f"- **{issue}**: {count}\n")
        lines.append("\n")

        # Топ рекомендации
        lines.append("## Топ рекомендации (15)\n\n")
        for opt in self.optimizations[:15]:
            lines.append(f"### {opt['article']}\n\n")
            lines.append(f"- **Проблема**: {opt['issue']}\n")
            lines.append(f"- **Рекомендация**: {opt['suggestion']}\n\n")

        return ''.join(lines)


class BreadcrumbVisualizer:
    """HTML визуализация навигации"""

    def __init__(self, generator, path_analyzer=None):
        self.generator = generator
        self.path_analyzer = path_analyzer

    def generate_html_navigation(self, output_file='BREADCRUMBS_NAV.html'):
        """Создать HTML навигацию"""
        print("🎨 Создание HTML navigation...\n")

        stats = self._prepare_statistics()
        chart_data = self._prepare_chart_data()

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍞 Breadcrumbs Navigation</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 40px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .stat-label {{
            color: #666;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            color: #667eea;
            font-size: 2.5em;
            font-weight: bold;
        }}

        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}

        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .chart-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        canvas {{
            max-height: 350px;
        }}

        .footer {{
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🍞 Breadcrumbs Navigation</h1>
        <p class="subtitle">Анализ навигационной структуры</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего статей</div>
                <div class="stat-value">{stats['total_articles']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Средняя глубина</div>
                <div class="stat-value">{stats['avg_depth']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Макс. глубина</div>
                <div class="stat-value">{stats['max_depth']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Оптимизаций</div>
                <div class="stat-value">{stats['optimizations']}</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-title">📊 Типы путей</div>
                <canvas id="pathTypesChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">📈 Распределение глубины</div>
                <canvas id="depthDistChart"></canvas>
            </div>
        </div>

        <div class="footer">
            Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Breadcrumbs Navigator v2.0
        </div>
    </div>

    <script>
        // Типы путей
        new Chart(document.getElementById('pathTypesChart'), {{
            type: 'doughnut',
            data: {{
                labels: {chart_data['path_types']['labels']},
                datasets: [{{
                    data: {chart_data['path_types']['values']},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});

        // Распределение глубины
        new Chart(document.getElementById('depthDistChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['depth_dist']['labels']},
                datasets: [{{
                    label: 'Количество статей',
                    data: {chart_data['depth_dist']['values']},
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        output_path = self.generator.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML Navigation: {output_path}\n")

    def _prepare_statistics(self):
        """Подготовить статистику"""
        depth_stats = self.path_analyzer.get_depth_statistics() if self.path_analyzer else {}

        return {
            'total_articles': len(self.generator.hierarchy),
            'avg_depth': f"{depth_stats.get('avg_depth', 0):.1f}",
            'max_depth': depth_stats.get('max_depth', 0),
            'optimizations': 0
        }

    def _prepare_chart_data(self):
        """Подготовить данные для графиков"""
        # Типы путей
        path_types = self.path_analyzer.path_stats if self.path_analyzer else Counter()

        # Глубина
        depth_dist = self.path_analyzer.depth_distribution if self.path_analyzer else Counter()

        return {
            'path_types': {
                'labels': list(path_types.keys()),
                'values': list(path_types.values())
            },
            'depth_dist': {
                'labels': [f"Глубина {d}" for d in sorted(depth_dist.keys())],
                'values': [depth_dist[d] for d in sorted(depth_dist.keys())]
            }
        }


class BreadcrumbValidator:
    """Валидация навигационных крошек"""

    def __init__(self, generator):
        self.generator = generator
        self.validation_results = []

    def validate_all(self):
        """Валидировать все breadcrumbs"""
        print("✅ Валидация breadcrumbs...\n")

        for article_path in self.generator.hierarchy.keys():
            issues = []
            warnings = []

            paths = self.generator.detect_smart_paths(article_path)

            # Нет путей
            if not paths:
                issues.append('Нет путей навигации')

            # Проверить консистентность
            if paths:
                best_path = paths[0]

                # Проверить, все ли URL валидны
                for crumb in best_path['trail']:
                    if crumb['url'] and not crumb['url'].startswith('/'):
                        url_path = self.generator.root_dir / crumb['url']
                        if not url_path.exists():
                            warnings.append(f"Битая ссылка в breadcrumb: {crumb['url']}")

                # Слишком глубоко
                if len(best_path['trail']) > 7:
                    warnings.append(f"Слишком глубокая навигация ({len(best_path['trail'])} уровней)")

                # Проверить титлы
                for crumb in best_path['trail']:
                    if not crumb['title'] or len(crumb['title']) < 2:
                        warnings.append(f"Пустой или слишком короткий title")

            self.validation_results.append({
                'article': article_path,
                'issues': issues,
                'warnings': warnings,
                'status': 'error' if issues else ('warning' if warnings else 'ok')
            })

        errors = len([r for r in self.validation_results if r['status'] == 'error'])
        warnings_count = len([r for r in self.validation_results if r['status'] == 'warning'])

        print(f"   Ошибки: {errors}")
        print(f"   Предупреждения: {warnings_count}\n")

    def generate_validation_report(self):
        """Создать отчёт валидации"""
        lines = []
        lines.append("# ✅ Отчёт: Валидация breadcrumbs\n\n")

        errors = [r for r in self.validation_results if r['status'] == 'error']
        warnings = [r for r in self.validation_results if r['status'] == 'warning']
        ok = [r for r in self.validation_results if r['status'] == 'ok']

        lines.append("## Статистика\n\n")
        lines.append(f"- **Ошибки**: {len(errors)}\n")
        lines.append(f"- **Предупреждения**: {len(warnings)}\n")
        lines.append(f"- **OK**: {len(ok)}\n")
        lines.append(f"- **Всего**: {len(self.validation_results)}\n\n")

        # Ошибки
        if errors:
            lines.append("## ❌ Ошибки\n\n")
            for result in errors[:20]:
                lines.append(f"### {result['article']}\n\n")
                for issue in result['issues']:
                    lines.append(f"- {issue}\n")
                lines.append("\n")

        # Предупреждения
        if warnings:
            lines.append("## ⚠️ Предупреждения (топ-20)\n\n")
            for result in warnings[:20]:
                lines.append(f"### {result['article']}\n\n")
                for warning in result['warnings']:
                    lines.append(f"- {warning}\n")
                lines.append("\n")

        return ''.join(lines)

    def export_to_csv(self, output_file='breadcrumbs_validation.csv'):
        """Экспорт в CSV"""
        csv_path = self.generator.root_dir / output_file

        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Article', 'Status', 'Issues', 'Warnings'])

            for result in self.validation_results:
                writer.writerow([
                    result['article'],
                    result['status'],
                    '; '.join(result['issues']),
                    '; '.join(result['warnings'])
                ])

        print(f"✅ CSV валидация: {csv_path}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='🍞 Advanced Breadcrumbs Generator v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                        # Базовая генерация
  %(prog)s --html                 # HTML навигация
  %(prog)s --analyze              # Анализ путей
  %(prog)s --optimize             # Оптимизация
  %(prog)s --validate             # Валидация
  %(prog)s --csv                  # CSV export
  %(prog)s --all                  # Все функции

Новые возможности v2.0:
  - 📊 Анализ путей и глубины
  - ⚡ Оптимизация с рекомендациями
  - 🎨 HTML dashboard с Chart.js
  - ✅ Валидация консистентности
  - 📈 CSV экспорт
        """
    )

    parser.add_argument('--format', choices=['markdown', 'html'], default='markdown',
                       help='Формат вывода')
    parser.add_argument('--schema', action='store_true',
                       help='Генерировать Schema.org JSON-LD')
    parser.add_argument('--html', action='store_true',
                       help='🎨 HTML navigation dashboard')
    parser.add_argument('--analyze', action='store_true',
                       help='📊 Анализ путей и глубины')
    parser.add_argument('--optimize', action='store_true',
                       help='⚡ Оптимизация breadcrumbs')
    parser.add_argument('--validate', action='store_true',
                       help='✅ Валидация навигации')
    parser.add_argument('--csv', action='store_true',
                       help='📊 CSV export')
    parser.add_argument('--max-depth', type=int, default=5,
                       help='Макс. глубина (default: 5)')
    parser.add_argument('--export-analysis', action='store_true',
                       help='📁 Экспорт отчёта анализа')
    parser.add_argument('--export-optimization', action='store_true',
                       help='⚡ Экспорт отчёта оптимизации')
    parser.add_argument('--export-validation', action='store_true',
                       help='✅ Экспорт отчёта валидации')
    parser.add_argument('--all', action='store_true',
                       help='🔥 Все опции')

    args = parser.parse_args()

    if args.all:
        args.html = args.analyze = args.optimize = args.validate = args.csv = args.schema = True
        args.export_analysis = args.export_optimization = args.export_validation = True

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = AdvancedBreadcrumbsGenerator(root_dir)
    generator.process_all(output_format=args.format, generate_schema=args.schema)

    # Новые функции
    path_analyzer = None
    if args.analyze or args.html or args.all:
        path_analyzer = PathAnalyzer(generator)
        path_analyzer.analyze_paths()
        if args.export_analysis or args.all:
            with open(root_dir / 'BREADCRUMBS_PATH_ANALYSIS.md', 'w', encoding='utf-8') as f:
                f.write(path_analyzer.generate_path_report())
            print(f"✅ Отчёт анализа путей\n")

    if args.optimize or args.all:
        optimizer = BreadcrumbOptimizer(generator)
        optimizer.optimize_all()
        if args.export_optimization or args.all:
            with open(root_dir / 'BREADCRUMBS_OPTIMIZATION.md', 'w', encoding='utf-8') as f:
                f.write(optimizer.generate_optimization_report())
            print(f"✅ Отчёт оптимизации\n")

    if args.validate or args.all:
        validator = BreadcrumbValidator(generator)
        validator.validate_all()
        if args.export_validation or args.all:
            with open(root_dir / 'BREADCRUMBS_VALIDATION.md', 'w', encoding='utf-8') as f:
                f.write(validator.generate_validation_report())
            print(f"✅ Отчёт валидации\n")
        if args.csv or args.all:
            validator.export_to_csv()

    if args.html or args.all:
        visualizer = BreadcrumbVisualizer(generator, path_analyzer)
        visualizer.generate_html_navigation()

    print(f"\n{'='*60}\n📊 Статей: {len(generator.hierarchy)}\n{'='*60}\n")


if __name__ == "__main__":
    main()
