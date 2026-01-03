#!/usr/bin/env python3
"""
Statistics Dashboard - Статистический дашборд
Комплексный обзор всех метрик базы знаний

Вдохновлено: Google Analytics, GitHub Insights
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import subprocess
from datetime import datetime, timedelta
import json
import math


class TrendAnalyzer:
    """
    Анализ трендов роста базы знаний по времени
    Определяет скорость роста, активность, прогнозы
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Данные для анализа
        self.articles_by_month = defaultdict(int)
        self.articles_by_year = defaultdict(int)
        self.commits_by_month = defaultdict(int)
        self.authors_by_month = defaultdict(set)

    def analyze_git_history(self):
        """Анализировать историю git для трендов"""
        try:
            # Получить все коммиты с датами
            result = subprocess.run(
                ['git', 'log', '--format=%ai|%an', '--', 'knowledge/'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                return

            for line in result.stdout.strip().split('\n'):
                if '|' not in line:
                    continue

                date_str, author = line.split('|', 1)
                try:
                    date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                    month_key = date.strftime('%Y-%m')
                    year_key = date.strftime('%Y')

                    self.commits_by_month[month_key] += 1
                    self.authors_by_month[month_key].add(author.strip())
                except:
                    continue
        except:
            pass

    def analyze_article_dates(self):
        """Анализировать даты создания статей"""
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    if fm and 'date' in fm:
                        date_value = fm['date']

                        # Парсинг даты
                        if isinstance(date_value, str):
                            try:
                                date = datetime.strptime(date_value, '%Y-%m-%d')
                            except:
                                continue
                        elif hasattr(date_value, 'strftime'):
                            date = date_value
                        else:
                            continue

                        month_key = date.strftime('%Y-%m')
                        year_key = date.strftime('%Y')

                        self.articles_by_month[month_key] += 1
                        self.articles_by_year[year_key] += 1
            except:
                continue

    def calculate_growth_rate(self):
        """Вычислить скорость роста (статей в месяц)"""
        if not self.articles_by_month:
            return 0

        # Сортировать по месяцам
        sorted_months = sorted(self.articles_by_month.keys())

        if len(sorted_months) < 2:
            return 0

        # Последние 6 месяцев
        recent_months = sorted_months[-6:]
        total_articles = sum(self.articles_by_month[m] for m in recent_months)

        return total_articles / len(recent_months)

    def forecast_growth(self, months_ahead=3):
        """Простой линейный прогноз на N месяцев вперёд"""
        growth_rate = self.calculate_growth_rate()

        if not self.articles_by_month:
            return {}

        sorted_months = sorted(self.articles_by_month.keys())
        last_month = sorted_months[-1] if sorted_months else None

        if not last_month:
            return {}

        # Текущее количество статей
        total_current = sum(self.articles_by_month.values())

        forecast = {}
        for i in range(1, months_ahead + 1):
            projected = total_current + (growth_rate * i)
            forecast[f'+{i}m'] = int(projected)

        return forecast

    def get_activity_heatmap(self):
        """Генерировать heatmap активности по месяцам"""
        if not self.commits_by_month:
            return {}

        heatmap = {}
        for month, count in self.commits_by_month.items():
            heatmap[month] = {
                'commits': count,
                'authors': len(self.authors_by_month.get(month, set())),
                'intensity': 'high' if count > 20 else 'medium' if count > 5 else 'low'
            }

        return heatmap

    def get_trends_summary(self):
        """Получить сводку трендов"""
        self.analyze_git_history()
        self.analyze_article_dates()

        growth_rate = self.calculate_growth_rate()
        forecast = self.forecast_growth()
        heatmap = self.get_activity_heatmap()

        # Топ-3 самых продуктивных месяца
        top_months = sorted(
            self.articles_by_month.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return {
            'growth_rate': round(growth_rate, 2),
            'forecast': forecast,
            'top_months': dict(top_months),
            'total_months': len(self.articles_by_month),
            'articles_by_year': dict(self.articles_by_year),
            'activity_heatmap': heatmap
        }


class CategoryStatistics:
    """
    Детальная статистика по категориям
    Сравнение категорий, рост, активность
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Данные по категориям
        self.category_data = defaultdict(lambda: {
            'count': 0,
            'total_words': 0,
            'total_links': 0,
            'tags': Counter(),
            'articles': []
        })

    def analyze_categories(self):
        """Анализировать все категории"""
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                if not match:
                    continue

                fm = yaml.safe_load(match.group(1))
                article_content = match.group(2)

                if not fm:
                    continue

                category = fm.get('category', 'Без категории')

                # Подсчёт слов
                words = len(re.findall(r'\b[а-яёa-z]+\b', article_content.lower()))

                # Подсчёт ссылок
                links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', article_content))

                # Теги
                tags = fm.get('tags', [])

                # Добавить данные
                self.category_data[category]['count'] += 1
                self.category_data[category]['total_words'] += words
                self.category_data[category]['total_links'] += links

                for tag in tags:
                    self.category_data[category]['tags'][tag] += 1

                self.category_data[category]['articles'].append({
                    'title': fm.get('title', md_file.stem),
                    'words': words,
                    'file': str(md_file.relative_to(self.root_dir))
                })
            except:
                continue

    def compare_categories(self):
        """Сравнить категории между собой"""
        comparisons = []

        for category, data in self.category_data.items():
            avg_words = data['total_words'] / data['count'] if data['count'] > 0 else 0
            avg_links = data['total_links'] / data['count'] if data['count'] > 0 else 0

            top_tags = data['tags'].most_common(5)

            comparisons.append({
                'category': category,
                'count': data['count'],
                'total_words': data['total_words'],
                'avg_words': round(avg_words, 0),
                'avg_links': round(avg_links, 1),
                'top_tags': [tag for tag, count in top_tags],
                'unique_tags': len(data['tags'])
            })

        # Сортировать по количеству статей
        comparisons.sort(key=lambda x: x['count'], reverse=True)

        return comparisons

    def get_category_leaders(self):
        """Получить лидеров по различным метрикам"""
        self.analyze_categories()

        if not self.category_data:
            return {}

        # Самая большая категория
        largest = max(self.category_data.items(), key=lambda x: x[1]['count'])

        # Самая словообильная
        most_words = max(self.category_data.items(), key=lambda x: x[1]['total_words'])

        # Самая связанная (много ссылок)
        most_connected = max(self.category_data.items(), key=lambda x: x[1]['total_links'])

        return {
            'largest_category': {
                'name': largest[0],
                'count': largest[1]['count']
            },
            'most_words': {
                'name': most_words[0],
                'total_words': most_words[1]['total_words']
            },
            'most_connected': {
                'name': most_connected[0],
                'total_links': most_connected[1]['total_links']
            }
        }


class QualityScorer:
    """
    Комплексный scoring качества статей (0-100)
    Критерии: полнота, читаемость, структура, ссылки
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def calculate_quality_score(self, frontmatter, content):
        """
        Вычислить качество статьи (0-100)

        Критерии (100 баллов):
        - Frontmatter полнота (20): title, tags, category, date, source
        - Структура (20): заголовки, TOC, разделы
        - Контент (30): длина, примеры кода, изображения
        - Ссылки (15): внутренние и внешние ссылки
        - Форматирование (15): списки, таблицы, выделения
        """
        score = 0

        # 1. Frontmatter полнота (20 баллов)
        if frontmatter:
            if frontmatter.get('title'):
                score += 5
            if frontmatter.get('tags') and len(frontmatter['tags']) >= 3:
                score += 5
            elif frontmatter.get('tags'):
                score += 2
            if frontmatter.get('category'):
                score += 5
            if frontmatter.get('date'):
                score += 3
            if frontmatter.get('source') or frontmatter.get('sources'):
                score += 2

        # 2. Структура (20 баллов)
        headings = re.findall(r'^#{1,6}\s', content, re.MULTILINE)
        if len(headings) >= 5:
            score += 10
        elif len(headings) >= 3:
            score += 7
        elif len(headings) >= 1:
            score += 4

        # TOC
        if '## ' in content and len(headings) >= 3:
            score += 5

        # Разделы (подзаголовки разного уровня)
        if '### ' in content:
            score += 5

        # 3. Контент (30 баллов)
        word_count = len(re.findall(r'\b[а-яёa-z]+\b', content.lower()))

        # Длина контента
        if word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        elif word_count >= 200:
            score += 5
        elif word_count >= 100:
            score += 2

        # Примеры кода
        code_blocks = len(re.findall(r'```', content)) // 2
        if code_blocks >= 3:
            score += 10
        elif code_blocks >= 1:
            score += 5

        # Изображения
        images = len(re.findall(r'!\[', content))
        if images >= 2:
            score += 5
        elif images >= 1:
            score += 3

        # 4. Ссылки (15 баллов)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        internal_links = [l for l in links if not l[1].startswith('http')]
        external_links = [l for l in links if l[1].startswith('http')]

        if len(internal_links) >= 5:
            score += 8
        elif len(internal_links) >= 3:
            score += 5
        elif len(internal_links) >= 1:
            score += 2

        if len(external_links) >= 3:
            score += 7
        elif len(external_links) >= 1:
            score += 4

        # 5. Форматирование (15 баллов)
        # Списки
        lists = len(re.findall(r'^\s*[-*]\s', content, re.MULTILINE))
        if lists >= 10:
            score += 5
        elif lists >= 5:
            score += 3
        elif lists >= 1:
            score += 1

        # Таблицы
        tables = len([line for line in content.split('\n') if '|' in line and line.strip().startswith('|')])
        if tables >= 5:
            score += 5
        elif tables >= 1:
            score += 3

        # Выделения (bold, italic, inline code)
        bold = len(re.findall(r'\*\*[^*]+\*\*', content))
        code_inline = len(re.findall(r'`[^`]+`', content))

        if bold + code_inline >= 10:
            score += 5
        elif bold + code_inline >= 5:
            score += 3

        return min(score, 100)

    def analyze_all_quality(self):
        """Проанализировать качество всех статей"""
        quality_distribution = {
            'excellent': 0,    # 80-100
            'good': 0,         # 60-79
            'fair': 0,         # 40-59
            'poor': 0,         # 20-39
            'very_poor': 0     # 0-19
        }

        article_scores = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    article_content = match.group(2)
                else:
                    fm = None
                    article_content = content

                score = self.calculate_quality_score(fm, article_content)

                # Классификация
                if score >= 80:
                    quality_distribution['excellent'] += 1
                elif score >= 60:
                    quality_distribution['good'] += 1
                elif score >= 40:
                    quality_distribution['fair'] += 1
                elif score >= 20:
                    quality_distribution['poor'] += 1
                else:
                    quality_distribution['very_poor'] += 1

                article_scores.append({
                    'file': str(md_file.relative_to(self.root_dir)),
                    'title': fm.get('title', md_file.stem) if fm else md_file.stem,
                    'score': score
                })
            except:
                continue

        # Средний балл
        avg_score = sum(a['score'] for a in article_scores) / len(article_scores) if article_scores else 0

        # Топ-10 лучших
        top_quality = sorted(article_scores, key=lambda x: x['score'], reverse=True)[:10]

        # Топ-10 худших (требуют улучшения)
        needs_improvement = sorted(article_scores, key=lambda x: x['score'])[:10]

        return {
            'distribution': quality_distribution,
            'average_score': round(avg_score, 1),
            'top_quality': top_quality,
            'needs_improvement': needs_improvement,
            'total_analyzed': len(article_scores)
        }


class InteractiveDashboard:
    """
    Генератор интерактивного HTML dashboard с графиками
    Responsive design, Chart.js интеграция
    """

    def __init__(self, stats_data):
        self.stats = stats_data

    def generate_html(self, output_file):
        """Генерировать интерактивный HTML dashboard"""
        html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Statistics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .content {{
            padding: 40px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
        }}

        .chart-container {{
            margin-bottom: 40px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .chart-container h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}

        canvas {{
            max-height: 400px;
        }}

        .quality-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin: 5px;
        }}

        .badge-excellent {{ background: #4CAF50; color: white; }}
        .badge-good {{ background: #2196F3; color: white; }}
        .badge-fair {{ background: #FF9800; color: white; }}
        .badge-poor {{ background: #f44336; color: white; }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Statistics Dashboard</h1>
            <p>Комплексный анализ базы знаний • Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>

        <div class="content">
            <!-- Main Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Всего статей</h3>
                    <div class="value">{self.stats.get('articles', {}).get('total', 0)}</div>
                    <div class="label">в базе знаний</div>
                </div>

                <div class="stat-card">
                    <h3>Всего слов</h3>
                    <div class="value">{self.stats.get('content', {}).get('total_words', 0):,}</div>
                    <div class="label">объём контента</div>
                </div>

                <div class="stat-card">
                    <h3>Коммитов</h3>
                    <div class="value">{self.stats.get('activity', {}).get('total_commits', 0)}</div>
                    <div class="label">всего изменений</div>
                </div>

                <div class="stat-card">
                    <h3>Качество</h3>
                    <div class="value">{self.stats.get('quality', {}).get('avg_quality_score', 0)}/5</div>
                    <div class="label">средний балл</div>
                </div>
            </div>
'''

        # Добавить графики если есть данные
        categories = self.stats.get('articles', {}).get('by_category', {})
        if categories:
            html += self._generate_category_chart(categories)

        trends = self.stats.get('trends', {})
        if trends.get('articles_by_year'):
            html += self._generate_trends_chart(trends['articles_by_year'])

        quality_dist = self.stats.get('quality_analysis', {}).get('distribution', {})
        if quality_dist:
            html += self._generate_quality_chart(quality_dist)

        html += '''
        </div>
    </div>
</body>
</html>
'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_category_chart(self, categories):
        """Генерировать график категорий"""
        labels = list(categories.keys())
        data = list(categories.values())

        return f'''
            <div class="chart-container">
                <h2>📚 Распределение по категориям</h2>
                <canvas id="categoryChart"></canvas>
            </div>

            <script>
                new Chart(document.getElementById('categoryChart'), {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels, ensure_ascii=False)},
                        datasets: [{{
                            label: 'Количество статей',
                            data: {json.dumps(data)},
                            backgroundColor: 'rgba(102, 126, 234, 0.7)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 2
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
'''

    def _generate_trends_chart(self, articles_by_year):
        """Генерировать график трендов по годам"""
        years = sorted(articles_by_year.keys())
        counts = [articles_by_year[y] for y in years]

        return f'''
            <div class="chart-container">
                <h2>📈 Рост базы знаний по годам</h2>
                <canvas id="trendsChart"></canvas>
            </div>

            <script>
                new Chart(document.getElementById('trendsChart'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(years)},
                        datasets: [{{
                            label: 'Статей в год',
                            data: {json.dumps(counts)},
                            borderColor: 'rgba(118, 75, 162, 1)',
                            backgroundColor: 'rgba(118, 75, 162, 0.2)',
                            fill: true,
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{ display: true }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true }}
                        }}
                    }}
                }});
            </script>
'''

    def _generate_quality_chart(self, distribution):
        """Генерировать график качества"""
        labels = ['Отлично (80+)', 'Хорошо (60-79)', 'Средне (40-59)', 'Плохо (20-39)', 'Очень плохо (0-19)']
        data = [
            distribution.get('excellent', 0),
            distribution.get('good', 0),
            distribution.get('fair', 0),
            distribution.get('poor', 0),
            distribution.get('very_poor', 0)
        ]

        return f'''
            <div class="chart-container">
                <h2>⭐ Распределение по качеству</h2>
                <canvas id="qualityChart"></canvas>
            </div>

            <script>
                new Chart(document.getElementById('qualityChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: {json.dumps(labels, ensure_ascii=False)},
                        datasets: [{{
                            data: {json.dumps(data)},
                            backgroundColor: [
                                'rgba(76, 175, 80, 0.8)',
                                'rgba(33, 150, 243, 0.8)',
                                'rgba(255, 152, 0, 0.8)',
                                'rgba(244, 67, 54, 0.8)',
                                'rgba(158, 158, 158, 0.8)'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }}
                        }}
                    }}
                }});
            </script>
'''


class StatisticsDashboard:
    """Генератор статистического дашборда"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Статистика
        self.stats = {
            'articles': {},
            'content': {},
            'structure': {},
            'activity': {},
            'quality': {}
        }

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

    def collect_article_stats(self):
        """Собрать статистику по статьям"""
        total_articles = 0
        by_category = defaultdict(int)
        by_difficulty = defaultdict(int)
        all_tags = defaultdict(int)

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            total_articles += 1

            if frontmatter:
                category = frontmatter.get('category', 'Без категории')
                by_category[category] += 1

                difficulty = frontmatter.get('difficulty', 'средний')
                by_difficulty[difficulty] += 1

                tags = frontmatter.get('tags', [])
                for tag in tags:
                    all_tags[tag] += 1

        self.stats['articles'] = {
            'total': total_articles,
            'by_category': dict(by_category),
            'by_difficulty': dict(by_difficulty),
            'tags': dict(sorted(all_tags.items(), key=lambda x: -x[1])[:20])
        }

    def collect_content_stats(self):
        """Собрать статистику по контенту"""
        total_words = 0
        total_chars = 0
        total_lines = 0
        total_headings = 0
        total_links = 0
        total_code_blocks = 0
        total_images = 0
        total_tables = 0

        article_lengths = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            # Подсчёты
            words = len(re.findall(r'\b[а-яёa-z]+\b', content.lower()))
            total_words += words
            article_lengths.append(words)

            total_chars += len(content)
            total_lines += len(content.split('\n'))

            total_headings += len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))
            total_links += len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
            total_code_blocks += len(re.findall(r'```', content)) // 2
            total_images += len(re.findall(r'!\[', content))
            total_tables += len([line for line in content.split('\n') if '|' in line and line.strip().startswith('|')])

        self.stats['content'] = {
            'total_words': total_words,
            'total_chars': total_chars,
            'total_lines': total_lines,
            'avg_article_length': int(total_words / len(article_lengths)) if article_lengths else 0,
            'shortest_article': min(article_lengths) if article_lengths else 0,
            'longest_article': max(article_lengths) if article_lengths else 0,
            'total_headings': total_headings,
            'total_links': total_links,
            'total_code_blocks': total_code_blocks,
            'total_images': total_images,
            'total_tables': total_tables
        }

    def collect_structure_stats(self):
        """Собрать статистику по структуре"""
        # Подсчитать ссылки между статьями
        internal_links = 0
        external_links = 0
        orphaned_articles = 0
        linked_articles = set()

        all_articles = set()

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            all_articles.add(article_path)

            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for text, link in links:
                if link.startswith('http'):
                    external_links += 1
                else:
                    internal_links += 1

                    try:
                        target = (md_file.parent / link.split('#')[0]).resolve()
                        if target.exists() and target.is_relative_to(self.root_dir):
                            target_path = str(target.relative_to(self.root_dir))
                            linked_articles.add(target_path)
                    except:
                        pass

        orphaned_articles = len(all_articles - linked_articles)

        self.stats['structure'] = {
            'internal_links': internal_links,
            'external_links': external_links,
            'total_links': internal_links + external_links,
            'orphaned_articles': orphaned_articles,
            'connectivity_ratio': round(len(linked_articles) / len(all_articles), 2) if all_articles else 0
        }

    def collect_activity_stats(self):
        """Собрать статистику по активности"""
        try:
            # Коммиты за последние 30 дней
            since_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--oneline'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            recent_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

            # Всего коммитов
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            total_commits = int(result.stdout.strip()) if result.stdout.strip() else 0

            # Авторы
            result = subprocess.run(
                ['git', 'log', '--format=%an'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            authors = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()

            self.stats['activity'] = {
                'total_commits': total_commits,
                'recent_commits_30d': recent_commits,
                'total_authors': len(authors),
                'avg_commits_per_day': round(total_commits / 365, 2) if total_commits else 0
            }
        except:
            self.stats['activity'] = {
                'total_commits': 0,
                'recent_commits_30d': 0,
                'total_authors': 0,
                'avg_commits_per_day': 0
            }

    def collect_quality_stats(self):
        """Собрать статистику по качеству"""
        articles_with_tags = 0
        articles_with_sources = 0
        articles_with_toc = 0
        total_quality_score = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            quality_score = 0

            if frontmatter:
                if frontmatter.get('tags'):
                    articles_with_tags += 1
                    quality_score += 1

                if frontmatter.get('source') or frontmatter.get('sources'):
                    articles_with_sources += 1
                    quality_score += 1

            # TOC
            if '## ' in content:
                articles_with_toc += 1
                quality_score += 1

            # Код
            if '```' in content:
                quality_score += 1

            # Ссылки
            if len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)) > 3:
                quality_score += 1

            total_quality_score += quality_score

        total_articles = self.stats['articles']['total']

        self.stats['quality'] = {
            'articles_with_tags': articles_with_tags,
            'articles_with_sources': articles_with_sources,
            'articles_with_structure': articles_with_toc,
            'avg_quality_score': round(total_quality_score / total_articles, 2) if total_articles else 0,
            'completeness_ratio': round(articles_with_tags / total_articles, 2) if total_articles else 0
        }

    def analyze_all(self):
        """Собрать всю статистику"""
        print("📊 Сбор статистики...\n")

        self.collect_article_stats()
        print(f"   ✅ Статистика по статьям")

        self.collect_content_stats()
        print(f"   ✅ Статистика по контенту")

        self.collect_structure_stats()
        print(f"   ✅ Статистика по структуре")

        self.collect_activity_stats()
        print(f"   ✅ Статистика по активности")

        self.collect_quality_stats()
        print(f"   ✅ Статистика по качеству\n")

    def generate_dashboard(self):
        """Создать дашборд"""
        lines = []
        lines.append("# 📊 Statistics Dashboard\n\n")
        lines.append(f"> Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        # Общий обзор
        lines.append("## 📈 Общий обзор\n\n")
        lines.append("| Метрика | Значение |\n")
        lines.append("|---------|----------|\n")
        lines.append(f"| **Всего статей** | {self.stats['articles']['total']} |\n")
        lines.append(f"| **Всего слов** | {self.stats['content']['total_words']:,} |\n")
        lines.append(f"| **Средняя длина статьи** | {self.stats['content']['avg_article_length']} слов |\n")
        lines.append(f"| **Всего ссылок** | {self.stats['structure']['total_links']} |\n")
        lines.append(f"| **Всего коммитов** | {self.stats['activity']['total_commits']} |\n")
        lines.append(f"| **Активных авторов** | {self.stats['activity']['total_authors']} |\n\n")

        # Статьи
        lines.append("## 📚 Статьи\n\n")
        lines.append(f"**Всего**: {self.stats['articles']['total']}\n\n")

        if self.stats['articles']['by_category']:
            lines.append("### По категориям\n\n")
            for category, count in sorted(self.stats['articles']['by_category'].items(), key=lambda x: -x[1]):
                lines.append(f"- **{category}**: {count}\n")
            lines.append("\n")

        if self.stats['articles']['by_difficulty']:
            lines.append("### По сложности\n\n")
            for difficulty, count in sorted(self.stats['articles']['by_difficulty'].items()):
                lines.append(f"- **{difficulty}**: {count}\n")
            lines.append("\n")

        if self.stats['articles']['tags']:
            lines.append("### Популярные теги\n\n")
            for tag, count in list(self.stats['articles']['tags'].items())[:10]:
                lines.append(f"- **{tag}**: {count}\n")
            lines.append("\n")

        # Контент
        lines.append("## 📝 Контент\n\n")
        lines.append("| Метрика | Значение |\n")
        lines.append("|---------|----------|\n")
        lines.append(f"| Всего слов | {self.stats['content']['total_words']:,} |\n")
        lines.append(f"| Всего символов | {self.stats['content']['total_chars']:,} |\n")
        lines.append(f"| Всего строк | {self.stats['content']['total_lines']:,} |\n")
        lines.append(f"| Заголовков | {self.stats['content']['total_headings']} |\n")
        lines.append(f"| Блоков кода | {self.stats['content']['total_code_blocks']} |\n")
        lines.append(f"| Изображений | {self.stats['content']['total_images']} |\n")
        lines.append(f"| Таблиц | {self.stats['content']['total_tables']} |\n")
        lines.append(f"| Самая короткая статья | {self.stats['content']['shortest_article']} слов |\n")
        lines.append(f"| Самая длинная статья | {self.stats['content']['longest_article']} слов |\n\n")

        # Структура
        lines.append("## 🔗 Структура\n\n")
        lines.append("| Метрика | Значение |\n")
        lines.append("|---------|----------|\n")
        lines.append(f"| Внутренних ссылок | {self.stats['structure']['internal_links']} |\n")
        lines.append(f"| Внешних ссылок | {self.stats['structure']['external_links']} |\n")
        lines.append(f"| Статей-сирот | {self.stats['structure']['orphaned_articles']} |\n")
        lines.append(f"| Связанность | {self.stats['structure']['connectivity_ratio'] * 100:.0f}% |\n\n")

        # Активность
        lines.append("## 🚀 Активность\n\n")
        lines.append("| Метрика | Значение |\n")
        lines.append("|---------|----------|\n")
        lines.append(f"| Всего коммитов | {self.stats['activity']['total_commits']} |\n")
        lines.append(f"| Коммитов за 30 дней | {self.stats['activity']['recent_commits_30d']} |\n")
        lines.append(f"| Авторов | {self.stats['activity']['total_authors']} |\n")
        lines.append(f"| Среднее коммитов/день | {self.stats['activity']['avg_commits_per_day']} |\n\n")

        # Качество
        lines.append("## ⭐ Качество\n\n")
        lines.append("| Метрика | Значение |\n")
        lines.append("|---------|----------|\n")
        lines.append(f"| Статей с тегами | {self.stats['quality']['articles_with_tags']} ({self.stats['quality']['completeness_ratio'] * 100:.0f}%) |\n")
        lines.append(f"| Статей с источниками | {self.stats['quality']['articles_with_sources']} |\n")
        lines.append(f"| Статей со структурой | {self.stats['quality']['articles_with_structure']} |\n")
        lines.append(f"| Средний балл качества | {self.stats['quality']['avg_quality_score']}/5 |\n\n")

        # Визуализация прогресса
        total = self.stats['articles']['total']
        progress_bar_length = 50
        filled = int((total / 100) * progress_bar_length) if total < 100 else progress_bar_length

        lines.append("## 📊 Прогресс до 100 статей\n\n")
        lines.append(f"```\n")
        lines.append(f"[{'█' * filled}{'░' * (progress_bar_length - filled)}] {total}/100 ({total}%)\n")
        lines.append(f"```\n\n")

        output_file = self.root_dir / "STATISTICS_DASHBOARD.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Дашборд: {output_file}")

    def save_json(self):
        """Сохранить статистику в JSON"""
        output_file = self.root_dir / "statistics.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON статистика: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Advanced Statistics Dashboard - Продвинутый статистический дашборд',
        epilog='''Примеры использования:
  %(prog)s                           # Базовый markdown отчёт
  %(prog)s --json stats.json        # + JSON экспорт
  %(prog)s --html dashboard.html    # + HTML dashboard с графиками
  %(prog)s --trends                 # + Анализ трендов роста
  %(prog)s --quality                # + Детальный анализ качества
  %(prog)s --categories             # + Сравнение категорий
  %(prog)s --all                    # Все анализы + все форматы экспорта
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--json', metavar='FILE',
                       help='Экспорт статистики в JSON')
    parser.add_argument('--html', metavar='FILE',
                       help='Генерировать интерактивный HTML dashboard')
    parser.add_argument('--trends', action='store_true',
                       help='Анализ трендов роста (статьи по месяцам/годам, прогноз)')
    parser.add_argument('--quality', action='store_true',
                       help='Детальный анализ качества статей (0-100 scoring)')
    parser.add_argument('--categories', action='store_true',
                       help='Сравнение категорий (размер, активность, теги)')
    parser.add_argument('--all', action='store_true',
                       help='Выполнить все анализы + все форматы экспорта')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Базовый дашборд
    dashboard = StatisticsDashboard(root_dir)
    dashboard.analyze_all()

    # Дополнительные анализы
    all_stats = dashboard.stats.copy()

    if args.trends or args.all:
        print("📈 Анализ трендов...\n")
        trend_analyzer = TrendAnalyzer(root_dir)
        trends = trend_analyzer.get_trends_summary()
        all_stats['trends'] = trends

        print(f"   Скорость роста: {trends['growth_rate']} статей/месяц")
        print(f"   Прогноз (+3 месяца): {trends['forecast']}")
        print()

    if args.categories or args.all:
        print("📊 Анализ категорий...\n")
        category_stats = CategoryStatistics(root_dir)
        category_stats.analyze_categories()

        comparisons = category_stats.compare_categories()
        leaders = category_stats.get_category_leaders()

        all_stats['category_analysis'] = {
            'comparisons': comparisons,
            'leaders': leaders
        }

        print(f"   Категорий: {len(comparisons)}")
        if leaders.get('largest_category'):
            print(f"   Самая большая: {leaders['largest_category']['name']} ({leaders['largest_category']['count']} статей)")
        print()

    if args.quality or args.all:
        print("⭐ Анализ качества...\n")
        quality_scorer = QualityScorer(root_dir)
        quality_analysis = quality_scorer.analyze_all_quality()

        all_stats['quality_analysis'] = quality_analysis

        print(f"   Средний балл качества: {quality_analysis['average_score']}/100")
        dist = quality_analysis['distribution']
        print(f"   Отлично (80+): {dist['excellent']}")
        print(f"   Хорошо (60-79): {dist['good']}")
        print(f"   Средне (40-59): {dist['fair']}")
        print(f"   Требуют улучшения: {dist['poor'] + dist['very_poor']}")
        print()

    # Генерация отчётов
    dashboard.generate_dashboard()

    if args.json or args.all:
        json_file = args.json if args.json else root_dir / "statistics.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_stats, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON: {json_file}")

    if args.html or args.all:
        html_file = args.html if args.html else root_dir / "DASHBOARD.html"
        html_generator = InteractiveDashboard(all_stats)
        html_generator.generate_html(html_file)
        print(f"✅ HTML Dashboard: {html_file}")

    print("\n✨ Анализ завершён!")


if __name__ == "__main__":
    main()
