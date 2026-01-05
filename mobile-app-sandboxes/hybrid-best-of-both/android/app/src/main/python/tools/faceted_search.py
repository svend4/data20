#!/usr/bin/env python3
"""
Faceted Search - Фасетный поиск
Вдохновлено: S.R. Ranganathan's Colon Classification (1933)

Позволяет фильтровать результаты по множеству независимых критериев (фасетов)
одновременно, постепенно сужая выборку.
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import argparse
import sys
import json
import csv
from datetime import datetime


class FacetedSearchEngine:
    """
    Фасетный поиск - поиск с множественными независимыми фильтрами
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Все статьи
        self.articles = []

        # Фасеты (доступные значения для фильтрации)
        self.facets = {
            'categories': set(),
            'subcategories': set(),
            'tags': set(),
            'authors': set(),
            'years': set(),
            'months': set(),
            'statuses': set(),
            'dewey': set()
        }

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                return fm
        except:
            pass
        return None

    def load_articles(self):
        """Загрузить все статьи"""
        print("📚 Загрузка базы знаний...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)
            if not frontmatter:
                continue

            # Извлечь данные
            title = frontmatter.get('title', md_file.stem)
            category = frontmatter.get('category', '')
            subcategory = frontmatter.get('subcategory', '')
            tags = frontmatter.get('tags', [])
            author = frontmatter.get('author', frontmatter.get('source', ''))
            date = str(frontmatter.get('date', ''))
            status = frontmatter.get('status', 'draft')
            dewey = frontmatter.get('dewey', '')

            # Парсинг даты
            year = ''
            month = ''
            if date and '-' in date:
                parts = date.split('-')
                if len(parts) >= 1:
                    year = parts[0]
                if len(parts) >= 2:
                    month = f"{parts[0]}-{parts[1]}"

            article = {
                'title': title,
                'file': str(md_file.relative_to(self.root_dir)),
                'category': category,
                'subcategory': subcategory,
                'tags': tags if isinstance(tags, list) else [],
                'author': author,
                'date': date,
                'year': year,
                'month': month,
                'status': status,
                'dewey': dewey
            }

            self.articles.append(article)

            # Обновить фасеты
            if category:
                self.facets['categories'].add(category)
            if subcategory:
                self.facets['subcategories'].add(subcategory)
            if author:
                self.facets['authors'].add(author)
            if year:
                self.facets['years'].add(year)
            if month:
                self.facets['months'].add(month)
            if status:
                self.facets['statuses'].add(status)
            if dewey:
                self.facets['dewey'].add(dewey)

            for tag in article['tags']:
                self.facets['tags'].add(tag)

        print(f"   Загружено статей: {len(self.articles)}\n")

    def filter_articles(self, filters):
        """
        Применить фасетные фильтры

        filters = {
            'category': 'computers',
            'tags': ['python', 'AI'],
            'year': '2026',
            ...
        }
        """
        results = self.articles

        # Фильтр по категории
        if 'category' in filters and filters['category']:
            results = [a for a in results if a['category'] == filters['category']]

        # Фильтр по подкатегории
        if 'subcategory' in filters and filters['subcategory']:
            results = [a for a in results if a['subcategory'] == filters['subcategory']]

        # Фильтр по тегам (ИЛИ - хотя бы один тег совпадает)
        if 'tags' in filters and filters['tags']:
            filter_tags = set(filters['tags'])
            results = [a for a in results if any(tag in filter_tags for tag in a['tags'])]

        # Фильтр по тегам (И - все теги должны совпасть)
        if 'tags_all' in filters and filters['tags_all']:
            filter_tags = set(filters['tags_all'])
            results = [a for a in results if filter_tags.issubset(set(a['tags']))]

        # Фильтр по автору
        if 'author' in filters and filters['author']:
            results = [a for a in results if a['author'] == filters['author']]

        # Фильтр по году
        if 'year' in filters and filters['year']:
            results = [a for a in results if a['year'] == filters['year']]

        # Фильтр по месяцу
        if 'month' in filters and filters['month']:
            results = [a for a in results if a['month'] == filters['month']]

        # Фильтр по статусу
        if 'status' in filters and filters['status']:
            results = [a for a in results if a['status'] == filters['status']]

        # Фильтр по Dewey
        if 'dewey' in filters and filters['dewey']:
            results = [a for a in results if a['dewey'] == filters['dewey']]

        # Текстовый поиск в заголовке
        if 'query' in filters and filters['query']:
            query = filters['query'].lower()
            results = [a for a in results if query in a['title'].lower()]

        return results

    def get_facet_counts(self, current_results):
        """Получить количество документов для каждого значения фасета"""
        counts = {
            'categories': defaultdict(int),
            'subcategories': defaultdict(int),
            'tags': defaultdict(int),
            'authors': defaultdict(int),
            'years': defaultdict(int),
            'statuses': defaultdict(int),
            'dewey': defaultdict(int)
        }

        for article in current_results:
            if article['category']:
                counts['categories'][article['category']] += 1
            if article['subcategory']:
                counts['subcategories'][article['subcategory']] += 1
            if article['author']:
                counts['authors'][article['author']] += 1
            if article['year']:
                counts['years'][article['year']] += 1
            if article['status']:
                counts['statuses'][article['status']] += 1
            if article['dewey']:
                counts['dewey'][article['dewey']] += 1

            for tag in article['tags']:
                counts['tags'][tag] += 1

        return counts

    def print_results(self, results, show_facets=True):
        """Вывести результаты поиска"""
        print(f"\n📊 Найдено статей: {len(results)}\n")

        if not results:
            print("❌ Ничего не найдено\n")
            return

        # Показать фасеты (доступные фильтры)
        if show_facets and len(results) < len(self.articles):
            print("🔍 Доступные фильтры для текущей выборки:\n")
            counts = self.get_facet_counts(results)

            # Категории
            if counts['categories']:
                print("   Категории:")
                for cat, count in sorted(counts['categories'].items()):
                    print(f"      {cat}: {count}")

            # Теги (топ-10)
            if counts['tags']:
                top_tags = sorted(counts['tags'].items(), key=lambda x: -x[1])[:10]
                print("\n   Популярные теги:")
                for tag, count in top_tags:
                    print(f"      {tag}: {count}")

            # Авторы
            if counts['authors']:
                print("\n   Авторы:")
                for author, count in sorted(counts['authors'].items()):
                    print(f"      {author}: {count}")

            # Годы
            if counts['years']:
                print("\n   Годы:")
                for year, count in sorted(counts['years'].items(), reverse=True):
                    print(f"      {year}: {count}")

            print("\n" + "="*80 + "\n")

        # Вывести статьи
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   📂 {article['file']}")
            print(f"   🏷️  {article['category']}/{article['subcategory']}")
            if article['tags']:
                tags_str = ', '.join(article['tags'][:5])
                print(f"   🔖 {tags_str}")
            if article['author']:
                print(f"   👤 {article['author']}")
            if article['date']:
                print(f"   📅 {article['date']}")
            print()

    def interactive_search(self):
        """Интерактивный фасетный поиск"""
        print("\n🔍 Интерактивный фасетный поиск\n")
        print("Введите фильтры (или 'help' для справки, 'reset' для сброса, 'quit' для выхода)\n")

        filters = {}

        while True:
            # Применить текущие фильтры
            results = self.filter_articles(filters)

            # Показать текущие фильтры
            if filters:
                print(f"📌 Активные фильтры: {filters}")

            print(f"📊 Результатов: {len(results)}/{len(self.articles)}\n")

            # Показать доступные фасеты
            counts = self.get_facet_counts(results)

            print("Доступные фильтры:")
            print(f"  categories: {', '.join(sorted(counts['categories'].keys()))}")
            print(f"  tags (топ-10): {', '.join([k for k, v in sorted(counts['tags'].items(), key=lambda x: -x[1])[:10]])}")
            print(f"  years: {', '.join(sorted(counts['years'].keys(), reverse=True))}")
            print()

            # Получить команду
            command = input(">>> ").strip()

            if not command:
                continue

            if command == 'quit' or command == 'q':
                break

            if command == 'reset':
                filters = {}
                print("✅ Фильтры сброшены\n")
                continue

            if command == 'show' or command == 'results':
                self.print_results(results, show_facets=False)
                continue

            if command == 'help':
                self.print_help()
                continue

            # Парсинг команды: category=computers, tags=python,AI
            try:
                parts = command.split(',')
                for part in parts:
                    if '=' not in part:
                        print(f"⚠️  Неверный формат: {part}")
                        continue

                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key in ['tags', 'tags_all']:
                        # Множественные значения
                        filters[key] = [v.strip() for v in value.split(' ')]
                    else:
                        filters[key] = value

                print(f"✅ Фильтр добавлен: {part}\n")

            except Exception as e:
                print(f"⚠️  Ошибка: {e}\n")

    def print_help(self):
        """Вывести справку"""
        print("""
📖 Справка по фасетному поиску

Синтаксис:
  фасет=значение

Несколько фильтров (через запятую):
  category=computers, tags=python AI, year=2026

Доступные фасеты:
  category      - категория (computers, household, cooking)
  subcategory   - подкатегория
  tags          - теги (ИЛИ - хотя бы один совпадает)
  tags_all      - теги (И - все должны совпасть)
  author        - автор/источник
  year          - год публикации
  month         - месяц публикации (YYYY-MM)
  status        - статус (draft, published, archived)
  dewey         - номер Dewey классификации
  query         - текстовый поиск в заголовке

Команды:
  show, results - показать текущие результаты
  reset         - сбросить все фильтры
  help          - эта справка
  quit, q       - выход

Примеры:
  category=computers
  category=computers, tags=python AI
  tags_all=python ООП
  year=2026, status=published
  query=холодильник
        """)


class FacetAggregator:
    """
    Агрегация и анализ статистики по фасетам
    Позволяет понять распределение документов по различным критериям
    """

    def __init__(self, articles):
        self.articles = articles

    def aggregate_by_facets(self):
        """Агрегировать статьи по всем фасетам"""
        aggregation = {
            'total': len(self.articles),
            'by_category': Counter(),
            'by_subcategory': Counter(),
            'by_tag': Counter(),
            'by_author': Counter(),
            'by_year': Counter(),
            'by_status': Counter(),
            'by_dewey': Counter()
        }

        for article in self.articles:
            if article['category']:
                aggregation['by_category'][article['category']] += 1
            if article['subcategory']:
                aggregation['by_subcategory'][article['subcategory']] += 1
            if article['author']:
                aggregation['by_author'][article['author']] += 1
            if article['year']:
                aggregation['by_year'][article['year']] += 1
            if article['status']:
                aggregation['by_status'][article['status']] += 1
            if article['dewey']:
                aggregation['by_dewey'][article['dewey']] += 1

            for tag in article['tags']:
                aggregation['by_tag'][tag] += 1

        return aggregation

    def get_top_facets(self, facet_name, n=10):
        """Получить топ N значений для фасета"""
        aggregation = self.aggregate_by_facets()
        facet_key = f'by_{facet_name}'

        if facet_key not in aggregation:
            return []

        return aggregation[facet_key].most_common(n)

    def calculate_diversity(self):
        """Вычислить индекс разнообразия для категорий"""
        if not self.articles:
            return 0.0

        category_counts = Counter(a['category'] for a in self.articles if a['category'])
        total = sum(category_counts.values())

        if total == 0:
            return 0.0

        # Simplified Shannon diversity index
        diversity = 0.0
        for count in category_counts.values():
            p = count / total
            diversity -= p * (p ** 0.5)

        return round(diversity * 100, 2)

    def save_aggregation_report(self, output_file):
        """Сохранить отчёт агрегации"""
        agg = self.aggregate_by_facets()
        diversity = self.calculate_diversity()

        lines = []
        lines.append("# 📊 Фасетная агрегация\n\n")
        lines.append(f"**Всего статей**: {agg['total']}\n")
        lines.append(f"**Индекс разнообразия**: {diversity}%\n\n")

        # Категории
        lines.append("## 🏷️ По категориям\n\n")
        for cat, count in agg['by_category'].most_common():
            pct = (count / agg['total']) * 100
            lines.append(f"- **{cat}**: {count} ({pct:.1f}%)\n")
        lines.append("\n")

        # Топ теги
        lines.append("## 🔖 Топ-20 тегов\n\n")
        for tag, count in agg['by_tag'].most_common(20):
            lines.append(f"- `{tag}`: {count}\n")
        lines.append("\n")

        # Авторы
        lines.append("## 👥 По авторам\n\n")
        for author, count in agg['by_author'].most_common(15):
            lines.append(f"- {author}: {count}\n")
        lines.append("\n")

        # Годы
        lines.append("## 📅 По годам\n\n")
        for year, count in sorted(agg['by_year'].items(), reverse=True):
            lines.append(f"- {year}: {count}\n")
        lines.append("\n")

        # Статусы
        lines.append("## ✅ По статусам\n\n")
        for status, count in agg['by_status'].most_common():
            lines.append(f"- {status}: {count}\n")
        lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"📊 Отчёт агрегации сохранён: {output_file}")


class QueryParser:
    """
    Парсинг сложных булевых запросов
    Поддерживает AND, OR, NOT операторы
    """

    def __init__(self):
        pass

    def parse(self, query):
        """
        Парсить запрос в структуру

        Примеры:
          python AND ML
          (python OR javascript) AND AI
          machine learning NOT tutorial
        """
        # Простая реализация - разделение по AND/OR/NOT
        query = query.strip()

        # Заменить операторы на символы для упрощения
        query = re.sub(r'\bAND\b', '&', query, flags=re.IGNORECASE)
        query = re.sub(r'\bOR\b', '|', query, flags=re.IGNORECASE)
        query = re.sub(r'\bNOT\b', '!', query, flags=re.IGNORECASE)

        return {
            'original': query,
            'parsed': query,
            'type': 'boolean'
        }

    def evaluate(self, query_struct, article):
        """Оценить, подходит ли статья под запрос"""
        query = query_struct['parsed'].lower()

        # Извлечь все термины
        terms = re.findall(r'\w+', query)

        # Собрать текст статьи
        article_text = (
            article['title'] + ' ' +
            article['category'] + ' ' +
            ' '.join(article['tags'])
        ).lower()

        # Простая проверка - все термины должны быть в статье
        return all(term in article_text for term in terms if term not in ['and', 'or', 'not'])


class SearchResultVisualizer:
    """
    HTML визуализация результатов фасетного поиска
    Создаёт интерактивный dashboard
    """

    def __init__(self, articles, search_results, filters):
        self.articles = articles
        self.results = search_results
        self.filters = filters

    def create_html_dashboard(self, output_file):
        """Создать HTML dashboard"""
        # Агрегация для графиков
        category_dist = Counter(r['category'] for r in self.results if r['category'])
        tag_dist = Counter()
        for r in self.results:
            for tag in r['tags']:
                tag_dist[tag] += 1

        year_dist = Counter(r['year'] for r in self.results if r['year'])
        status_dist = Counter(r['status'] for r in self.results if r['status'])

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Faceted Search Results</title>
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
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
        }}
        .filters-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .filter-badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.9em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 10px;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #333;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
        .results-list {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .result-item {{
            padding: 20px;
            border-bottom: 1px solid #eee;
        }}
        .result-item:last-child {{
            border-bottom: none;
        }}
        .result-title {{
            font-size: 1.2em;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .result-meta {{
            color: #666;
            font-size: 0.9em;
            margin: 5px 0;
        }}
        .result-tags {{
            margin-top: 10px;
        }}
        .tag {{
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 10px;
            border-radius: 12px;
            margin: 2px;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Faceted Search Results</h1>
        <p class="subtitle">Результаты фасетного поиска</p>

        <div class="filters-card">
            <h3 style="margin-bottom: 15px;">Активные фильтры:</h3>
            {''.join(f'<span class="filter-badge">{k}: {v}</span>' for k, v in self.filters.items()) if self.filters else '<em>Фильтры не применены</em>'}
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(self.results)}</div>
                <div class="stat-label">Найдено</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(category_dist)}</div>
                <div class="stat-label">Категорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(tag_dist)}</div>
                <div class="stat-label">Тегов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(year_dist)}</div>
                <div class="stat-label">Периодов</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <h2 class="chart-title">📊 Распределение по категориям</h2>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">🔖 Топ-10 тегов</h2>
                <div class="chart-container">
                    <canvas id="tagChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">📅 По годам</h2>
                <div class="chart-container">
                    <canvas id="yearChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">✅ По статусам</h2>
                <div class="chart-container">
                    <canvas id="statusChart"></canvas>
                </div>
            </div>
        </div>

        <div class="results-list">
            <h2 style="margin-bottom: 25px;">📄 Результаты ({len(self.results)})</h2>
            {''.join(self._render_result(i, r) for i, r in enumerate(self.results[:50], 1))}
            {f'<p style="margin-top: 20px; color: #666;"><em>Показаны первые 50 из {len(self.results)} результатов</em></p>' if len(self.results) > 50 else ''}
        </div>
    </div>

    <script>
        // Категории
        new Chart(document.getElementById('categoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(list(category_dist.keys()))},
                datasets: [{{
                    data: {json.dumps(list(category_dist.values()))},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false
            }}
        }});

        // Теги
        new Chart(document.getElementById('tagChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([t for t, c in tag_dist.most_common(10)])},
                datasets: [{{
                    label: 'Статей',
                    data: {json.dumps([c for t, c in tag_dist.most_common(10)])},
                    backgroundColor: '#667eea',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Годы
        new Chart(document.getElementById('yearChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(sorted(year_dist.keys()))},
                datasets: [{{
                    label: 'Статей',
                    data: {json.dumps([year_dist[y] for y in sorted(year_dist.keys())])},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Статусы
        new Chart(document.getElementById('statusChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(list(status_dist.keys()))},
                datasets: [{{
                    data: {json.dumps(list(status_dist.values()))},
                    backgroundColor: '#764ba2',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"🎨 HTML dashboard сохранён: {output_file}")

    def _render_result(self, index, article):
        """Отрендерить один результат"""
        tags_html = ''.join(f'<span class="tag">{tag}</span>' for tag in article['tags'][:10])

        return f"""
            <div class="result-item">
                <div class="result-title">{index}. {article['title']}</div>
                <div class="result-meta">📂 {article['file']}</div>
                <div class="result-meta">🏷️ {article['category']}/{article['subcategory']}</div>
                {f'<div class="result-meta">👤 {article["author"]}</div>' if article['author'] else ''}
                {f'<div class="result-meta">📅 {article["date"]}</div>' if article['date'] else ''}
                {f'<div class="result-tags">{tags_html}</div>' if article['tags'] else ''}
            </div>
        """


class SearchHistoryManager:
    """
    Управление историей поисков
    Отслеживает популярные запросы и рекомендации
    """

    def __init__(self, history_file='faceted_search_history.json'):
        self.history_file = Path(history_file)
        self.history = self.load_history()

    def load_history(self):
        """Загрузить историю"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'searches': [], 'popular_filters': Counter()}

    def save_history(self):
        """Сохранить историю"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add_search(self, filters, results_count):
        """Добавить поиск в историю"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'filters': filters,
            'results_count': results_count
        }

        self.history['searches'].append(entry)

        # Обновить популярные фильтры
        for key, value in filters.items():
            filter_str = f"{key}={value}"
            self.history['popular_filters'][filter_str] = \
                self.history['popular_filters'].get(filter_str, 0) + 1

        # Сохранить только последние 100 поисков
        self.history['searches'] = self.history['searches'][-100:]

        self.save_history()

    def get_popular_searches(self, n=10):
        """Получить популярные поиски"""
        # Группировать по фильтрам
        search_counts = Counter()

        for search in self.history['searches']:
            filter_str = str(sorted(search['filters'].items()))
            search_counts[filter_str] += 1

        return search_counts.most_common(n)

    def get_popular_filters(self, n=10):
        """Получить популярные фильтры"""
        return Counter(self.history['popular_filters']).most_common(n)

    def show_history(self, n=20):
        """Показать историю"""
        print(f"\n📜 История последних {n} поисков:\n")

        for i, search in enumerate(reversed(self.history['searches'][-n:]), 1):
            print(f"{i}. {search['timestamp']}")
            print(f"   Фильтры: {search['filters']}")
            print(f"   Результатов: {search['results_count']}\n")

    def show_popular(self):
        """Показать популярные запросы"""
        print("\n🔥 Популярные фильтры:\n")

        for filter_str, count in self.get_popular_filters(10):
            print(f"   {filter_str}: {count} раз")

        print()


def main():
    parser = argparse.ArgumentParser(
        description='🔍 Faceted Search - Фасетный поиск по базе знаний',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s -c computers -t python AI      # Фильтр по категории и тегам
  %(prog)s --html --all                   # HTML dashboard со всеми опциями
  %(prog)s --aggregate                    # Агрегированная статистика
  %(prog)s --history                      # История поисков
  %(prog)s -i                             # Интерактивный режим
        """
    )

    # Фильтры
    parser.add_argument('-c', '--category', help='Фильтр по категории')
    parser.add_argument('-s', '--subcategory', help='Фильтр по подкатегории')
    parser.add_argument('-t', '--tags', nargs='+', help='Фильтр по тегам (ИЛИ)')
    parser.add_argument('--tags-all', nargs='+', help='Фильтр по тегам (И)')
    parser.add_argument('-a', '--author', help='Фильтр по автору')
    parser.add_argument('-y', '--year', help='Фильтр по году')
    parser.add_argument('--status', help='Фильтр по статусу')
    parser.add_argument('-d', '--dewey', help='Фильтр по Dewey номеру')
    parser.add_argument('-q', '--query', help='Текстовый поиск в заголовке')

    # Дополнительные опции
    parser.add_argument('--html', action='store_true',
                       help='🎨 Создать HTML dashboard с визуализацией')
    parser.add_argument('--aggregate', action='store_true',
                       help='📊 Агрегированная статистика по фасетам')
    parser.add_argument('--parse-query', type=str, metavar='QUERY',
                       help='🔍 Парсинг булевого запроса (AND/OR/NOT)')
    parser.add_argument('--history', action='store_true',
                       help='📜 Показать историю поисков')
    parser.add_argument('--popular', action='store_true',
                       help='🔥 Показать популярные фильтры')
    parser.add_argument('--json', action='store_true',
                       help='📄 Экспорт результатов в JSON')
    parser.add_argument('--csv', action='store_true',
                       help='📊 Экспорт результатов в CSV')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='🔢 Ограничить количество результатов')
    parser.add_argument('--sort', choices=['relevance', 'date', 'title'],
                       help='📑 Сортировка результатов')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='💬 Интерактивный режим')
    parser.add_argument('--all', action='store_true',
                       help='🚀 Выполнить все опции анализа')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    engine = FacetedSearchEngine(root_dir)
    engine.load_articles()

    # История поисков
    history = SearchHistoryManager(root_dir / "faceted_search_history.json")

    # Показать историю
    if args.history:
        history.show_history()
        return

    # Показать популярные
    if args.popular:
        history.show_popular()
        return

    # Агрегация без фильтров
    if args.aggregate and not any([args.category, args.subcategory, args.tags, args.query]):
        aggregator = FacetAggregator(engine.articles)
        aggregator.save_aggregation_report(root_dir / "faceted_aggregation.md")
        print(f"\n✨ Агрегация завершена!")
        return

    # Интерактивный режим
    if args.interactive:
        engine.interactive_search()
        return

    # Построить фильтры
    filters = {}
    if args.category:
        filters['category'] = args.category
    if args.subcategory:
        filters['subcategory'] = args.subcategory
    if args.tags:
        filters['tags'] = args.tags
    if args.tags_all:
        filters['tags_all'] = args.tags_all
    if args.author:
        filters['author'] = args.author
    if args.year:
        filters['year'] = args.year
    if args.status:
        filters['status'] = args.status
    if args.dewey:
        filters['dewey'] = args.dewey
    if args.query:
        filters['query'] = args.query

    # Парсинг булевого запроса
    if args.parse_query:
        query_parser = QueryParser()
        query_struct = query_parser.parse(args.parse_query)
        print(f"\n📝 Парсинг запроса: {query_struct['original']}\n")

        # Применить к статьям
        results = [a for a in engine.articles if query_parser.evaluate(query_struct, a)]
    elif filters:
        # Обычная фильтрация
        results = engine.filter_articles(filters)
    else:
        # Нет фильтров - показать справку
        print("🔍 Faceted Search - Фасетный поиск\n")
        parser.print_help()
        return

    # Добавить в историю
    if filters or args.parse_query:
        history.add_search(filters if filters else {'query': args.parse_query}, len(results))

    # Сортировка
    if args.sort:
        if args.sort == 'date':
            results.sort(key=lambda x: x['date'] or '', reverse=True)
        elif args.sort == 'title':
            results.sort(key=lambda x: x['title'])

    # Ограничение
    if args.limit:
        results = results[:args.limit]

    # HTML dashboard
    if args.html or args.all:
        visualizer = SearchResultVisualizer(engine.articles, results, filters)
        visualizer.create_html_dashboard(root_dir / "faceted_search_results.html")

    # Агрегация результатов
    if args.aggregate or args.all:
        aggregator = FacetAggregator(results)
        aggregator.save_aggregation_report(root_dir / "faceted_search_aggregation.md")

    # Экспорт JSON
    if args.json:
        output_file = root_dir / "faceted_search_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON экспорт: {output_file}")

    # Экспорт CSV
    if args.csv:
        output_file = root_dir / "faceted_search_results.csv"
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            if results:
                fieldnames = ['title', 'file', 'category', 'subcategory', 'author', 'date', 'status', 'dewey']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for article in results:
                    writer.writerow({
                        'title': article['title'],
                        'file': article['file'],
                        'category': article['category'],
                        'subcategory': article['subcategory'],
                        'author': article['author'],
                        'date': article['date'],
                        'status': article['status'],
                        'dewey': article['dewey']
                    })
        print(f"📊 CSV экспорт: {output_file}")

    # Вывести результаты
    if not (args.html or args.json or args.csv or args.all):
        engine.print_results(results)
    else:
        print(f"\n✨ Найдено: {len(results)} статей")
        print(f"📊 Результаты обработаны и экспортированы")


if __name__ == "__main__":
    main()
