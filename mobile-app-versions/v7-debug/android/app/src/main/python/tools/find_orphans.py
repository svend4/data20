#!/usr/bin/env python3
"""
Advanced Orphan Finder - Продвинутый поиск статей-сирот
Функции:
- Orphan classification (новые, старые, критичные)
- Fix suggestions (предложения где добавить ссылки)
- Severity levels (high, medium, low)
- Integration candidates (статьи, которые могут ссылаться)
- Orphan age detection
- Link density analysis
- Category-based analysis
- Automatic fix generation
- JSON export
- Graph visualization data

Вдохновлено: Wikipedia orphan detection, SEO tools, Content auditing tools
"""

from pathlib import Path
import re
import yaml
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter
import math


class OrphanImpactAnalyzer:
    """Анализ влияния сирот на граф знаний"""

    def __init__(self, all_articles, incoming_links, outgoing_links):
        self.all_articles = all_articles
        self.incoming_links = incoming_links
        self.outgoing_links = outgoing_links

    def calculate_lost_pagerank(self, orphan_path):
        """
        Вычислить потерянный PageRank из-за отсутствия входящих ссылок

        PageRank узла зависит от входящих ссылок. Сирота имеет
        только базовый PageRank = (1-d)/N, где d=0.85, N=количество узлов.

        Returns:
            dict: потенциал PageRank если бы были ссылки
        """
        n = len(self.all_articles)
        damping = 0.85

        # Базовый PageRank сироты
        base_pr = (1 - damping) / n

        # Потенциальный PageRank если бы кандидаты ссылались
        potential_pr = base_pr

        # Для упрощения: если бы на сироту ссылались статьи с высоким out-degree,
        # её PR был бы выше
        outgoing_count = len(self.outgoing_links.get(orphan_path, set()))

        # Эвристика: потенциальный PR ~ количество исходящих ссылок
        if outgoing_count > 0:
            potential_pr += (outgoing_count * damping) / (n * 10)

        lost_pr = potential_pr - base_pr

        return {
            'base_pagerank': base_pr,
            'potential_pagerank': potential_pr,
            'lost_pagerank': lost_pr,
            'lost_percentage': (lost_pr / potential_pr * 100) if potential_pr > 0 else 0
        }

    def calculate_connectivity_impact(self, orphan_path):
        """
        Вычислить влияние на связность графа

        Сироты уменьшают связность графа. Метрики:
        - Disconnected component size
        - Average path length increase
        - Betweenness centrality lost

        Returns:
            dict: метрики влияния на связность
        """
        outgoing = self.outgoing_links.get(orphan_path, set())

        # Если сирота ссылается на другие статьи, но на нее никто не ссылается,
        # это односторонняя связь
        one_way_connections = len(outgoing)

        # Потенциальные двусторонние связи (если бы на сироту ссылались обратно)
        potential_bidirectional = 0
        for target in outgoing:
            # Проверить, ссылается ли target обратно
            if orphan_path not in self.outgoing_links.get(target, set()):
                potential_bidirectional += 1

        # Impact score: выше если много односторонних связей
        impact_score = one_way_connections + potential_bidirectional * 2

        return {
            'one_way_connections': one_way_connections,
            'potential_bidirectional': potential_bidirectional,
            'impact_score': impact_score,
            'connectivity_rating': self._rate_connectivity_impact(impact_score)
        }

    def _rate_connectivity_impact(self, score):
        """Оценить влияние на связность"""
        if score >= 10:
            return 'critical'
        elif score >= 5:
            return 'high'
        elif score >= 2:
            return 'medium'
        else:
            return 'low'

    def analyze_cluster_isolation(self, orphans):
        """
        Анализ кластерной изоляции

        Группы сирот в одной категории/теме указывают на
        системную проблему структуры знаний.

        Args:
            orphans: список сирот

        Returns:
            dict: анализ кластеров изолированных сирот
        """
        category_clusters = defaultdict(list)
        tag_clusters = defaultdict(list)

        for orphan in orphans:
            metadata = orphan['metadata']

            # Группировать по категориям
            category = metadata.get('category')
            if category:
                category_clusters[category].append(orphan['path'])

            # Группировать по тегам
            tags = metadata.get('tags', [])
            for tag in tags:
                tag_clusters[tag].append(orphan['path'])

        # Найти кластеры с множественными сиротами
        problem_categories = {cat: paths for cat, paths in category_clusters.items() if len(paths) >= 3}
        problem_tags = {tag: paths for tag, paths in tag_clusters.items() if len(paths) >= 3}

        return {
            'category_clusters': problem_categories,
            'tag_clusters': problem_tags,
            'isolated_categories_count': len(problem_categories),
            'isolated_tags_count': len(problem_tags)
        }

    def calculate_discoverability_score(self, orphan_path):
        """
        Оценить возможность обнаружения сироты

        Discoverability - насколько легко пользователь может найти статью
        через навигацию (без поиска).

        Факторы:
        - Количество исходящих ссылок (чем больше, тем легче найти через них)
        - Наличие в категориях/тегах
        - Глубина в структуре директорий

        Returns:
            int: оценка 0-100 (100 = легко найти)
        """
        metadata = self.all_articles[orphan_path]
        score = 0

        # Исходящие ссылки (0-30 баллов)
        outgoing_count = len(self.outgoing_links.get(orphan_path, set()))
        score += min(30, outgoing_count * 5)

        # Теги (0-25 баллов)
        tags_count = len(metadata.get('tags', []))
        score += min(25, tags_count * 5)

        # Категория (0-20 баллов)
        if metadata.get('category'):
            score += 20

        # Глубина директорий (0-25 баллов, меньше = лучше)
        depth = len(Path(orphan_path).parts) - 2  # -2 для 'knowledge' и filename
        depth_score = max(0, 25 - depth * 5)
        score += depth_score

        return min(100, score)


class AutoLinker:
    """Автоматическое предложение ссылок на основе контента"""

    def __init__(self, all_articles, incoming_links, outgoing_links):
        self.all_articles = all_articles
        self.incoming_links = incoming_links
        self.outgoing_links = outgoing_links

    def extract_keywords(self, content, top_n=10):
        """
        Извлечь ключевые слова из контента

        Простая TF (term frequency) без IDF для скорости.

        Args:
            content: текст статьи
            top_n: количество топ-слов

        Returns:
            list: топ ключевые слова
        """
        if not content:
            return []

        # Удалить markdown разметку
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # ссылки
        text = re.sub(r'#+\s+', '', text)  # заголовки
        text = re.sub(r'[*_`]', '', text)  # форматирование

        # Разбить на слова
        words = re.findall(r'\b[а-яА-Яa-zA-Z]{3,}\b', text.lower())

        # Стоп-слова (базовый список)
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'this', 'that', 'with', 'have', 'from',
            'это', 'для', 'как', 'или', 'что', 'так', 'все', 'еще', 'уже', 'был', 'был', 'было', 'были', 'есть', 'мой', 'твой', 'его', 'её'
        }

        # Подсчитать частоту
        word_freq = Counter(w for w in words if w not in stop_words)

        return [word for word, _ in word_freq.most_common(top_n)]

    def find_content_similarity(self, orphan_path, other_path):
        """
        Вычислить схожесть контента между двумя статьями

        Используем Jaccard similarity на основе ключевых слов.

        Args:
            orphan_path: путь к сироте
            other_path: путь к другой статье

        Returns:
            float: similarity score 0-1
        """
        orphan_metadata = self.all_articles[orphan_path]
        other_metadata = self.all_articles[other_path]

        # Загрузить контент
        try:
            with open(orphan_metadata['file_path'], 'r', encoding='utf-8') as f:
                orphan_content = f.read()
            with open(other_metadata['file_path'], 'r', encoding='utf-8') as f:
                other_content = f.read()
        except:
            return 0.0

        # Извлечь ключевые слова
        orphan_keywords = set(self.extract_keywords(orphan_content, top_n=20))
        other_keywords = set(self.extract_keywords(other_content, top_n=20))

        # Jaccard similarity
        if not orphan_keywords or not other_keywords:
            return 0.0

        intersection = len(orphan_keywords & other_keywords)
        union = len(orphan_keywords | other_keywords)

        return intersection / union if union > 0 else 0.0

    def suggest_contextual_links(self, orphan_path, top_n=5):
        """
        Предложить ссылки на основе контекстуальной схожести

        Находит статьи с похожим контентом, которые должны ссылаться на сироту.

        Args:
            orphan_path: путь к сироте
            top_n: количество предложений

        Returns:
            list: предложения с similarity scores
        """
        suggestions = []

        for article_path in self.all_articles.keys():
            if article_path == orphan_path:
                continue

            # Вычислить схожесть
            similarity = self.find_content_similarity(orphan_path, article_path)

            if similarity > 0.1:  # Порог схожести
                suggestions.append({
                    'article': article_path,
                    'similarity': similarity,
                    'type': 'content_similarity'
                })

        # Сортировать по схожести
        suggestions.sort(key=lambda x: -x['similarity'])

        return suggestions[:top_n]

    def generate_auto_link_text(self, orphan_path, target_path, context='generic'):
        """
        Сгенерировать текст ссылки автоматически

        Args:
            orphan_path: путь к сироте
            target_path: путь к статье, которая будет ссылаться
            context: контекст ('generic', 'related', 'see_also')

        Returns:
            str: markdown код ссылки
        """
        orphan_metadata = self.all_articles[orphan_path]
        orphan_name = Path(orphan_path).stem
        orphan_title = orphan_metadata.get('frontmatter', {}).get('title', orphan_name)

        if context == 'related':
            return f"Смотрите также: [{orphan_title}]({Path(orphan_path).name})"
        elif context == 'see_also':
            return f"См. [{orphan_title}]({Path(orphan_path).name})"
        else:
            return f"[{orphan_title}]({Path(orphan_path).name})"

    def bulk_analyze_opportunities(self, orphans, threshold=0.15):
        """
        Массовый анализ возможностей для автоматического связывания

        Args:
            orphans: список сирот
            threshold: минимальный порог схожести

        Returns:
            dict: статистика возможностей
        """
        total_opportunities = 0
        high_confidence = 0  # similarity > 0.3
        medium_confidence = 0  # similarity > 0.2
        low_confidence = 0  # similarity > threshold

        for orphan in orphans:
            suggestions = self.suggest_contextual_links(orphan['path'])

            for suggestion in suggestions:
                sim = suggestion['similarity']
                if sim >= threshold:
                    total_opportunities += 1

                    if sim > 0.3:
                        high_confidence += 1
                    elif sim > 0.2:
                        medium_confidence += 1
                    else:
                        low_confidence += 1

        return {
            'total_opportunities': total_opportunities,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence
        }


class OrphanClusterAnalyzer:
    """Анализ кластеров сирот"""

    def __init__(self, all_articles):
        self.all_articles = all_articles

    def cluster_by_category(self, orphans):
        """
        Группировать сироты по категориям

        Args:
            orphans: список сирот

        Returns:
            dict: {category: [orphan_paths]}
        """
        clusters = defaultdict(list)

        for orphan in orphans:
            metadata = orphan['metadata']
            category = metadata.get('category', 'uncategorized')
            clusters[category].append(orphan)

        return dict(clusters)

    def cluster_by_age(self, orphans):
        """
        Группировать по возрасту

        Возрастные группы:
        - Fresh (< 7 дней)
        - Recent (7-30 дней)
        - Mature (30-90 дней)
        - Old (90+ дней)

        Args:
            orphans: список сирот

        Returns:
            dict: {age_group: [orphan_paths]}
        """
        clusters = {
            'fresh': [],
            'recent': [],
            'mature': [],
            'old': []
        }

        for orphan in orphans:
            age_days = orphan['metadata']['age_days']

            if age_days < 7:
                clusters['fresh'].append(orphan)
            elif age_days < 30:
                clusters['recent'].append(orphan)
            elif age_days < 90:
                clusters['mature'].append(orphan)
            else:
                clusters['old'].append(orphan)

        return clusters

    def cluster_by_directory(self, orphans):
        """
        Группировать по директориям

        Если в одной директории много сирот, это указывает
        на проблему в структуре.

        Args:
            orphans: список сирот

        Returns:
            dict: {directory: [orphan_paths]}
        """
        clusters = defaultdict(list)

        for orphan in orphans:
            directory = str(Path(orphan['path']).parent)
            clusters[directory].append(orphan)

        return dict(clusters)

    def find_problematic_areas(self, orphans):
        """
        Найти проблемные области (много сирот в одном месте)

        Args:
            orphans: список сирот

        Returns:
            list: проблемные области с метриками
        """
        dir_clusters = self.cluster_by_directory(orphans)
        cat_clusters = self.cluster_by_category(orphans)

        problematic = []

        # Проблемные директории (3+ сирот)
        for directory, cluster_orphans in dir_clusters.items():
            if len(cluster_orphans) >= 3:
                problematic.append({
                    'type': 'directory',
                    'location': directory,
                    'orphan_count': len(cluster_orphans),
                    'severity': 'high' if len(cluster_orphans) >= 5 else 'medium',
                    'orphans': [o['path'] for o in cluster_orphans]
                })

        # Проблемные категории (4+ сирот)
        for category, cluster_orphans in cat_clusters.items():
            if len(cluster_orphans) >= 4:
                problematic.append({
                    'type': 'category',
                    'location': category,
                    'orphan_count': len(cluster_orphans),
                    'severity': 'high' if len(cluster_orphans) >= 7 else 'medium',
                    'orphans': [o['path'] for o in cluster_orphans]
                })

        # Сортировать по количеству сирот
        problematic.sort(key=lambda x: -x['orphan_count'])

        return problematic

    def analyze_orphan_trends(self, orphans):
        """
        Анализ трендов: когда появляются сироты

        Args:
            orphans: список сирот

        Returns:
            dict: статистика трендов
        """
        age_clusters = self.cluster_by_age(orphans)

        # Скорость появления сирот
        fresh_count = len(age_clusters['fresh'])
        recent_count = len(age_clusters['recent'])
        mature_count = len(age_clusters['mature'])
        old_count = len(age_clusters['old'])

        # Тренд: растёт ли число сирот?
        # Если fresh + recent > mature + old, то тренд растущий
        recent_total = fresh_count + recent_count
        old_total = mature_count + old_count

        if recent_total > old_total:
            trend = 'increasing'
            trend_severity = 'warning'
        elif recent_total < old_total * 0.5:
            trend = 'decreasing'
            trend_severity = 'good'
        else:
            trend = 'stable'
            trend_severity = 'neutral'

        return {
            'fresh_count': fresh_count,
            'recent_count': recent_count,
            'mature_count': mature_count,
            'old_count': old_count,
            'trend': trend,
            'trend_severity': trend_severity,
            'orphan_rate': (recent_total / len(self.all_articles) * 100) if self.all_articles else 0
        }


class OrphanVisualizer:
    """Визуализация сирот"""

    def __init__(self, all_articles, orphans, incoming_links, outgoing_links):
        self.all_articles = all_articles
        self.orphans = orphans
        self.incoming_links = incoming_links
        self.outgoing_links = outgoing_links

    def generate_html_report(self):
        """
        Создать интерактивный HTML отчёт

        Включает:
        - Дашборд с статистикой
        - Интерактивный список сирот
        - Фильтры по severity, категории, возрасту
        - Визуализация по категориям

        Returns:
            str: HTML контент
        """
        # Статистика
        total_articles = len(self.all_articles)
        total_orphans = len(self.orphans)
        orphan_percentage = (total_orphans / total_articles * 100) if total_articles > 0 else 0

        # Группировать по severity
        by_severity = defaultdict(int)
        for orphan in self.orphans:
            severity = orphan['classification']['severity']
            by_severity[severity] += 1

        # Группировать по типу
        by_type = defaultdict(int)
        for orphan in self.orphans:
            orphan_type = orphan['classification']['type']
            by_type[orphan_type] += 1

        # JSON для JavaScript
        orphans_json = []
        for orphan in self.orphans:
            orphans_json.append({
                'path': orphan['path'],
                'name': Path(orphan['path']).stem,
                'type': orphan['classification']['type'],
                'severity': orphan['classification']['severity'],
                'age_days': orphan['metadata']['age_days'],
                'category': orphan['metadata'].get('category', 'uncategorized'),
                'content_length': orphan['metadata']['content_length'],
                'candidates_count': len(orphan['candidates'])
            })

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Анализ статей-сирот</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .stat-label {{
            color: #666;
            font-size: 1.1em;
        }}

        .filters {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}

        .filter-group {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}

        .filter-group label {{
            margin-right: 10px;
            font-weight: 600;
        }}

        .filter-group select, .filter-group input {{
            padding: 8px 12px;
            border: 2px solid #667eea;
            border-radius: 5px;
            font-size: 14px;
        }}

        .orphans-list {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .orphan-item {{
            border-left: 4px solid #ccc;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}

        .orphan-item.high {{
            border-left-color: #dc3545;
        }}

        .orphan-item.medium {{
            border-left-color: #ffc107;
        }}

        .orphan-item.low {{
            border-left-color: #28a745;
        }}

        .orphan-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}

        .orphan-meta {{
            color: #666;
            font-size: 0.95em;
            margin-bottom: 5px;
        }}

        .orphan-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
        }}

        .severity-high {{
            background: #dc3545;
            color: white;
        }}

        .severity-medium {{
            background: #ffc107;
            color: #333;
        }}

        .severity-low {{
            background: #28a745;
            color: white;
        }}

        .no-results {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Анализ статей-сирот</h1>

        <div class="dashboard">
            <div class="stat-card">
                <div class="stat-value">{total_articles}</div>
                <div class="stat-label">Всего статей</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_orphans}</div>
                <div class="stat-label">Сирот</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{orphan_percentage:.1f}%</div>
                <div class="stat-label">Процент сирот</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{by_severity.get('high', 0)}</div>
                <div class="stat-label">Критичных</div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label>Severity:</label>
                <select id="filterSeverity">
                    <option value="all">Все</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Тип:</label>
                <select id="filterType">
                    <option value="all">Все</option>
                    <option value="old_orphan">Старые</option>
                    <option value="new">Новые</option>
                    <option value="isolated">Изолированные</option>
                    <option value="completely_isolated">Полностью изолированные</option>
                    <option value="stub">Stubs</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Поиск:</label>
                <input type="text" id="searchInput" placeholder="Название статьи...">
            </div>
        </div>

        <div class="orphans-list" id="orphansList"></div>
    </div>

    <script>
        const orphans = {json.dumps(orphans_json, ensure_ascii=False)};

        function renderOrphans(filtered) {{
            const container = document.getElementById('orphansList');

            if (filtered.length === 0) {{
                container.innerHTML = '<div class="no-results">Нет результатов</div>';
                return;
            }}

            container.innerHTML = filtered.map(orphan => `
                <div class="orphan-item ${{orphan.severity}}">
                    <div class="orphan-title">${{orphan.name}}</div>
                    <div class="orphan-meta">
                        <span class="orphan-badge severity-${{orphan.severity}}">${{orphan.severity.toUpperCase()}}</span>
                        <span class="orphan-badge" style="background: #6c757d; color: white;">${{orphan.type}}</span>
                    </div>
                    <div class="orphan-meta">
                        📂 ${{orphan.path}}
                    </div>
                    <div class="orphan-meta">
                        📅 Возраст: ${{orphan.age_days}} дней |
                        📝 Размер: ${{orphan.content_length}} символов |
                        🔗 Кандидатов: ${{orphan.candidates_count}}
                    </div>
                    ${{orphan.category !== 'uncategorized' ? `<div class="orphan-meta">🏷️ Категория: ${{orphan.category}}</div>` : ''}}
                </div>
            `).join('');
        }}

        function filterOrphans() {{
            const severity = document.getElementById('filterSeverity').value;
            const type = document.getElementById('filterType').value;
            const search = document.getElementById('searchInput').value.toLowerCase();

            const filtered = orphans.filter(orphan => {{
                if (severity !== 'all' && orphan.severity !== severity) return false;
                if (type !== 'all' && orphan.type !== type) return false;
                if (search && !orphan.name.toLowerCase().includes(search)) return false;
                return true;
            }});

            renderOrphans(filtered);
        }}

        // Event listeners
        document.getElementById('filterSeverity').addEventListener('change', filterOrphans);
        document.getElementById('filterType').addEventListener('change', filterOrphans);
        document.getElementById('searchInput').addEventListener('input', filterOrphans);

        // Initial render
        renderOrphans(orphans);
    </script>
</body>
</html>"""

        return html

    def generate_category_chart_data(self):
        """
        Подготовить данные для графика по категориям

        Returns:
            dict: данные для Chart.js
        """
        category_counts = defaultdict(int)

        for orphan in self.orphans:
            category = orphan['metadata'].get('category', 'uncategorized')
            category_counts[category] += 1

        return {
            'labels': list(category_counts.keys()),
            'data': list(category_counts.values())
        }


class AdvancedOrphanFinder:
    """Продвинутый поиск статей-сирот"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Статистика
        self.all_articles = {}  # path -> metadata
        self.incoming_links = defaultdict(set)  # target -> sources
        self.outgoing_links = defaultdict(set)  # source -> targets

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

    def analyze_article(self, file_path):
        """Проанализировать статью"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        # Базовая информация
        article_path = str(file_path.relative_to(self.root_dir))

        # Дата создания/модификации
        mtime = file_path.stat().st_mtime
        modified_date = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - modified_date).days

        # Размер контента
        content_length = len(content) if content else 0

        # Теги/категории
        tags = []
        category = None
        if frontmatter:
            tags = frontmatter.get('tags', [])
            category = frontmatter.get('category', None)

        # Сохранить метаданные
        self.all_articles[article_path] = {
            'path': article_path,
            'frontmatter': frontmatter,
            'content_length': content_length,
            'modified_date': modified_date,
            'age_days': age_days,
            'tags': tags,
            'category': category,
            'file_path': file_path
        }

        return content

    def build_link_graph(self):
        """Построить граф ссылок"""
        print("🔍 Анализ статей и ссылок...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            # Анализировать статью
            content = self.analyze_article(md_file)
            article_path = str(md_file.relative_to(self.root_dir))

            if not content:
                continue

            # Найти все markdown ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in links:
                # Пропустить внешние ссылки и якоря
                if link.startswith('http') or link.startswith('#'):
                    continue

                # Разрешить относительный путь
                try:
                    target = (md_file.parent / link.split('#')[0]).resolve()
                    target_path = str(target.relative_to(self.root_dir))

                    # Записать связь
                    self.outgoing_links[article_path].add(target_path)
                    self.incoming_links[target_path].add(article_path)
                except:
                    pass

            # Ссылки из frontmatter (related)
            frontmatter = self.all_articles[article_path]['frontmatter']
            if frontmatter and 'related' in frontmatter:
                related = frontmatter['related']
                if isinstance(related, list):
                    for link in related:
                        try:
                            target = (md_file.parent / link).resolve()
                            target_path = str(target.relative_to(self.root_dir))

                            self.outgoing_links[article_path].add(target_path)
                            self.incoming_links[target_path].add(article_path)
                        except:
                            pass

        print(f"   Статей: {len(self.all_articles)}")
        print(f"   Связей: {sum(len(v) for v in self.outgoing_links.values())}\n")

    def classify_orphan(self, article_path):
        """Классифицировать сироту"""
        metadata = self.all_articles[article_path]

        age_days = metadata['age_days']
        content_length = metadata['content_length']
        outgoing_links_count = len(self.outgoing_links.get(article_path, set()))

        # Классификация
        classification = {
            'type': 'unknown',
            'severity': 'medium',
            'reason': []
        }

        # Новая статья (< 7 дней)
        if age_days < 7:
            classification['type'] = 'new'
            classification['severity'] = 'low'
            classification['reason'].append('Новая статья, возможно еще не интегрирована')

        # Старая статья (> 90 дней) без ссылок
        elif age_days > 90:
            classification['type'] = 'old_orphan'
            classification['severity'] = 'high'
            classification['reason'].append('Старая статья без ссылок - требует внимания')

        # Короткая статья
        if content_length < 500:
            classification['type'] = 'stub'
            classification['severity'] = 'low'
            classification['reason'].append('Короткая статья (stub)')

        # Статья со ссылками наружу но без входящих
        if outgoing_links_count > 0:
            classification['type'] = 'isolated'
            classification['severity'] = 'medium'
            classification['reason'].append(f'Ссылается на {outgoing_links_count} статей, но на нее никто не ссылается')

        # Полностью изолированная статья
        if outgoing_links_count == 0:
            classification['type'] = 'completely_isolated'
            classification['severity'] = 'high'
            classification['reason'].append('Полностью изолирована (нет ссылок ни в одну сторону)')

        return classification

    def find_integration_candidates(self, orphan_path, max_candidates=5):
        """Найти статьи, которые могут ссылаться на сироту"""
        orphan_metadata = self.all_articles[orphan_path]
        candidates = []

        orphan_tags = set(orphan_metadata.get('tags', []))
        orphan_category = orphan_metadata.get('category')

        for article_path, metadata in self.all_articles.items():
            if article_path == orphan_path:
                continue

            score = 0
            reasons = []

            # Общие теги
            article_tags = set(metadata.get('tags', []))
            common_tags = orphan_tags & article_tags
            if common_tags:
                score += len(common_tags) * 2
                reasons.append(f"Общие теги: {', '.join(common_tags)}")

            # Та же категория
            if metadata.get('category') == orphan_category and orphan_category:
                score += 3
                reasons.append(f"Та же категория: {orphan_category}")

            # Сирота ссылается на эту статью
            if article_path in self.outgoing_links.get(orphan_path, set()):
                score += 5
                reasons.append("Сирота ссылается на эту статью (можно сделать взаимную ссылку)")

            # Эта статья в той же директории
            if Path(article_path).parent == Path(orphan_path).parent:
                score += 1
                reasons.append("В той же директории")

            # Много исходящих ссылок (hub)
            outgoing_count = len(self.outgoing_links.get(article_path, set()))
            if outgoing_count > 5:
                score += 1
                reasons.append(f"Hub-статья ({outgoing_count} ссылок)")

            if score > 0:
                candidates.append({
                    'path': article_path,
                    'score': score,
                    'reasons': reasons
                })

        # Сортировать по score
        candidates.sort(key=lambda x: -x['score'])

        return candidates[:max_candidates]

    def generate_fix_suggestion(self, orphan_path, candidate):
        """Сгенерировать предложение по исправлению"""
        orphan_name = Path(orphan_path).stem
        candidate_name = Path(candidate['path']).stem

        suggestion = f"В файле `{candidate['path']}` можно добавить ссылку на `{orphan_path}`:\n"
        suggestion += f"```markdown\n"
        suggestion += f"[{orphan_name}]({Path(orphan_path).name})\n"
        suggestion += f"```\n"
        suggestion += f"Причина: {', '.join(candidate['reasons'])}"

        return suggestion

    def find_orphans(self):
        """Найти и классифицировать сирот"""
        # Построить граф
        self.build_link_graph()

        print("🔍 Поиск статей-сирот...\n")

        # Найти сироты
        orphans = []

        for article_path in self.all_articles.keys():
            incoming_count = len(self.incoming_links.get(article_path, set()))

            if incoming_count == 0:
                # Классифицировать
                classification = self.classify_orphan(article_path)

                # Найти кандидатов для интеграции
                candidates = self.find_integration_candidates(article_path)

                orphan_data = {
                    'path': article_path,
                    'metadata': self.all_articles[article_path],
                    'classification': classification,
                    'candidates': candidates
                }

                orphans.append(orphan_data)

        # Статистика
        total = len(self.all_articles)
        linked = total - len(orphans)

        print(f"   Всего статей: {total}")
        print(f"   Со ссылками: {linked}")
        print(f"   Сироты: {len(orphans)}\n")

        # Статистика по типам
        if orphans:
            types = defaultdict(int)
            for orphan in orphans:
                types[orphan['classification']['type']] += 1

            print("   Типы сирот:")
            for orphan_type, count in sorted(types.items(), key=lambda x: -x[1]):
                print(f"      {orphan_type}: {count}")
            print()

        return orphans

    def generate_report(self, orphans):
        """Создать подробный отчёт"""
        lines = []
        lines.append("# 🔍 Продвинутый отчёт: Статьи-сироты\n\n")
        lines.append("> Статьи без входящих ссылок с анализом и предложениями\n\n")

        lines.append(f"**Найдено сирот**: {len(orphans)}\n\n")

        if not orphans:
            lines.append("✅ Нет статей-сирот! Все статьи связаны.\n")
        else:
            # Группировать по severity
            by_severity = defaultdict(list)
            for orphan in orphans:
                severity = orphan['classification']['severity']
                by_severity[severity].append(orphan)

            # High severity
            if 'high' in by_severity:
                lines.append("## 🔴 Критичные сироты (High Severity)\n\n")
                lines.append("Требуют немедленного внимания\n\n")

                for orphan in by_severity['high']:
                    self._add_orphan_section(lines, orphan)

            # Medium severity
            if 'medium' in by_severity:
                lines.append("\n## 🟡 Средний приоритет (Medium Severity)\n\n")

                for orphan in by_severity['medium']:
                    self._add_orphan_section(lines, orphan)

            # Low severity
            if 'low' in by_severity:
                lines.append("\n## 🟢 Низкий приоритет (Low Severity)\n\n")

                for orphan in by_severity['low']:
                    self._add_orphan_section(lines, orphan)

        output_file = self.root_dir / "ORPHANED_ARTICLES_ADVANCED.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def _add_orphan_section(self, lines, orphan):
        """Добавить секцию для одной сироты"""
        path = orphan['path']
        classification = orphan['classification']
        metadata = orphan['metadata']
        candidates = orphan['candidates']

        lines.append(f"### {Path(path).stem}\n\n")
        lines.append(f"- **Путь**: `{path}`\n")
        lines.append(f"- **Тип**: {classification['type']}\n")
        lines.append(f"- **Severity**: {classification['severity']}\n")
        lines.append(f"- **Возраст**: {metadata['age_days']} дней\n")
        lines.append(f"- **Размер**: {metadata['content_length']} символов\n")

        if classification['reason']:
            lines.append(f"- **Причины**:\n")
            for reason in classification['reason']:
                lines.append(f"  - {reason}\n")

        # Кандидаты для интеграции
        if candidates:
            lines.append(f"\n**Предложения по интеграции** (топ-{len(candidates)}):\n\n")

            for i, candidate in enumerate(candidates, 1):
                lines.append(f"{i}. **{Path(candidate['path']).stem}** (score: {candidate['score']})\n")
                lines.append(f"   - Файл: `{candidate['path']}`\n")
                for reason in candidate['reasons']:
                    lines.append(f"   - {reason}\n")
                lines.append("\n")

        lines.append("\n---\n\n")

    def export_json(self, orphans):
        """Экспорт в JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(self.all_articles),
            'total_orphans': len(orphans),
            'orphans': []
        }

        for orphan in orphans:
            # Конвертировать datetime в string
            metadata = orphan['metadata'].copy()
            metadata['modified_date'] = metadata['modified_date'].isoformat()
            metadata.pop('file_path', None)  # Удалить Path object

            # Конвертировать frontmatter (может содержать date объекты)
            frontmatter = metadata.get('frontmatter')
            if frontmatter:
                frontmatter_clean = {}
                for key, value in frontmatter.items():
                    if hasattr(value, 'isoformat'):  # datetime или date
                        frontmatter_clean[key] = value.isoformat()
                    else:
                        frontmatter_clean[key] = value
                metadata['frontmatter'] = frontmatter_clean

            data['orphans'].append({
                'path': orphan['path'],
                'metadata': metadata,
                'classification': orphan['classification'],
                'candidates': orphan['candidates']
            })

        output_file = self.root_dir / "orphans_analysis.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='📊 Продвинутый поиск статей-сирот',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:

  # Базовый отчёт (Markdown)
  %(prog)s

  # Интерактивный HTML отчёт
  %(prog)s --html

  # Анализ влияния сирот (PageRank, connectivity)
  %(prog)s --impact

  # Автоматическое предложение ссылок
  %(prog)s --auto-link

  # Анализ кластеров (проблемные области)
  %(prog)s --clusters

  # Анализ трендов (когда появляются сироты)
  %(prog)s --trends

  # JSON экспорт
  %(prog)s --json

  # Полный анализ (все опции)
  %(prog)s --all

  # Показать топ критичных сирот
  %(prog)s --top-critical 10

Вдохновлено: Wikipedia orphan detection, SEO tools, Content auditing tools
        '''
    )

    parser.add_argument('--html', action='store_true',
                        help='Создать интерактивный HTML отчёт')
    parser.add_argument('--impact', action='store_true',
                        help='Анализ влияния сирот (PageRank, connectivity)')
    parser.add_argument('--auto-link', action='store_true',
                        help='Автоматическое предложение ссылок на основе контента')
    parser.add_argument('--clusters', action='store_true',
                        help='Анализ кластеров (проблемные области)')
    parser.add_argument('--trends', action='store_true',
                        help='Анализ трендов появления сирот')
    parser.add_argument('--json', action='store_true',
                        help='Экспорт в JSON')
    parser.add_argument('--top-critical', type=int, metavar='N',
                        help='Показать топ N критичных сирот')
    parser.add_argument('--all', action='store_true',
                        help='Выполнить полный анализ (все опции)')

    args = parser.parse_args()

    # --all включает все опции
    if args.all:
        args.html = True
        args.impact = True
        args.auto_link = True
        args.clusters = True
        args.trends = True
        args.json = True
        if not args.top_critical:
            args.top_critical = 10

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    finder = AdvancedOrphanFinder(root_dir)
    orphans = finder.find_orphans()
    finder.generate_report(orphans)

    # JSON экспорт
    if args.json:
        finder.export_json(orphans)

    # Анализ влияния
    if args.impact:
        print("\n📈 Анализ влияния сирот...\n")

        impact_analyzer = OrphanImpactAnalyzer(
            finder.all_articles,
            finder.incoming_links,
            finder.outgoing_links
        )

        # Анализ кластерной изоляции
        cluster_isolation = impact_analyzer.analyze_cluster_isolation(orphans)

        print(f"   Проблемные категории: {cluster_isolation['isolated_categories_count']}")
        print(f"   Проблемные теги: {cluster_isolation['isolated_tags_count']}\n")

        # Топ сирот по влиянию
        orphans_with_impact = []
        for orphan in orphans:
            pagerank_impact = impact_analyzer.calculate_lost_pagerank(orphan['path'])
            connectivity_impact = impact_analyzer.calculate_connectivity_impact(orphan['path'])
            discoverability = impact_analyzer.calculate_discoverability_score(orphan['path'])

            orphans_with_impact.append({
                'path': orphan['path'],
                'pagerank_impact': pagerank_impact,
                'connectivity_impact': connectivity_impact,
                'discoverability': discoverability
            })

        # Сохранить отчёт
        impact_report = []
        impact_report.append("# 📈 Анализ влияния сирот\n\n")

        impact_report.append("## Кластерная изоляция\n\n")
        if cluster_isolation['category_clusters']:
            impact_report.append("### Проблемные категории (3+ сирот)\n\n")
            for category, paths in cluster_isolation['category_clusters'].items():
                impact_report.append(f"**{category}**: {len(paths)} сирот\n\n")
                for path in paths[:5]:
                    impact_report.append(f"- `{path}`\n")
                impact_report.append("\n")

        impact_report.append("\n## Топ-10 сирот по connectivity impact\n\n")
        sorted_by_connectivity = sorted(
            orphans_with_impact,
            key=lambda x: -x['connectivity_impact']['impact_score']
        )

        for orphan_impact in sorted_by_connectivity[:10]:
            path = orphan_impact['path']
            conn = orphan_impact['connectivity_impact']

            impact_report.append(f"### {Path(path).stem}\n\n")
            impact_report.append(f"- **Путь**: `{path}`\n")
            impact_report.append(f"- **Impact score**: {conn['impact_score']}\n")
            impact_report.append(f"- **Connectivity rating**: {conn['connectivity_rating']}\n")
            impact_report.append(f"- **Односторонних связей**: {conn['one_way_connections']}\n")
            impact_report.append(f"- **Потенциальных двусторонних**: {conn['potential_bidirectional']}\n\n")

        impact_report.append("\n## Топ-10 сирот по discoverability (легко найти)\n\n")
        sorted_by_discoverability = sorted(
            orphans_with_impact,
            key=lambda x: -x['discoverability']
        )

        for orphan_impact in sorted_by_discoverability[:10]:
            path = orphan_impact['path']
            disc = orphan_impact['discoverability']

            impact_report.append(f"1. **{Path(path).stem}**: {disc}/100\n")

        output_file = root_dir / "ORPHAN_IMPACT_ANALYSIS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(impact_report)

        print(f"✅ Анализ влияния: {output_file}")

    # Автоматическое связывание
    if args.auto_link:
        print("\n🔗 Автоматическое предложение ссылок...\n")

        auto_linker = AutoLinker(
            finder.all_articles,
            finder.incoming_links,
            finder.outgoing_links
        )

        # Массовый анализ
        opportunities = auto_linker.bulk_analyze_opportunities(orphans)

        print(f"   Всего возможностей: {opportunities['total_opportunities']}")
        print(f"   Высокая уверенность (>0.3): {opportunities['high_confidence']}")
        print(f"   Средняя уверенность (>0.2): {opportunities['medium_confidence']}")
        print(f"   Низкая уверенность (>0.15): {opportunities['low_confidence']}\n")

        # Сохранить топ предложений
        auto_link_report = []
        auto_link_report.append("# 🔗 Автоматическое предложение ссылок\n\n")
        auto_link_report.append(f"**Всего возможностей**: {opportunities['total_opportunities']}\n\n")

        auto_link_report.append("## Топ-10 сирот для автоматического связывания\n\n")

        # Для каждой сироты найти лучшие предложения
        orphans_with_suggestions = []
        for orphan in orphans[:20]:  # Ограничиться топ-20 для скорости
            suggestions = auto_linker.suggest_contextual_links(orphan['path'])
            if suggestions:
                orphans_with_suggestions.append({
                    'path': orphan['path'],
                    'best_similarity': suggestions[0]['similarity'],
                    'suggestions': suggestions
                })

        # Сортировать по лучшей схожести
        orphans_with_suggestions.sort(key=lambda x: -x['best_similarity'])

        for orphan_sugg in orphans_with_suggestions[:10]:
            path = orphan_sugg['path']
            suggestions = orphan_sugg['suggestions']

            auto_link_report.append(f"### {Path(path).stem}\n\n")
            auto_link_report.append(f"**Путь**: `{path}`\n\n")
            auto_link_report.append("**Предложения**:\n\n")

            for i, sugg in enumerate(suggestions, 1):
                auto_link_report.append(f"{i}. **{Path(sugg['article']).stem}** (similarity: {sugg['similarity']:.3f})\n")
                auto_link_report.append(f"   - Файл: `{sugg['article']}`\n")

                # Сгенерировать код ссылки
                link_code = auto_linker.generate_auto_link_text(path, sugg['article'], context='see_also')
                auto_link_report.append(f"   - Код ссылки: `{link_code}`\n")

            auto_link_report.append("\n")

        output_file = root_dir / "AUTO_LINK_SUGGESTIONS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(auto_link_report)

        print(f"✅ Предложения по связыванию: {output_file}")

    # Анализ кластеров
    if args.clusters:
        print("\n🗂️  Анализ кластеров сирот...\n")

        cluster_analyzer = OrphanClusterAnalyzer(finder.all_articles)

        problematic_areas = cluster_analyzer.find_problematic_areas(orphans)

        print(f"   Проблемных областей: {len(problematic_areas)}\n")

        # Сохранить отчёт
        cluster_report = []
        cluster_report.append("# 🗂️  Анализ кластеров сирот\n\n")
        cluster_report.append("> Группы сирот указывают на системные проблемы\n\n")

        cluster_report.append(f"**Проблемных областей**: {len(problematic_areas)}\n\n")

        if problematic_areas:
            cluster_report.append("## Проблемные области\n\n")

            for area in problematic_areas:
                severity_emoji = '🔴' if area['severity'] == 'high' else '🟡'

                cluster_report.append(f"### {severity_emoji} {area['location']}\n\n")
                cluster_report.append(f"- **Тип**: {area['type']}\n")
                cluster_report.append(f"- **Сирот**: {area['orphan_count']}\n")
                cluster_report.append(f"- **Severity**: {area['severity']}\n\n")

                cluster_report.append("**Список сирот**:\n\n")
                for orphan_path in area['orphans'][:10]:
                    cluster_report.append(f"- `{orphan_path}`\n")

                if area['orphan_count'] > 10:
                    cluster_report.append(f"\n... и ещё {area['orphan_count'] - 10} сирот\n")

                cluster_report.append("\n---\n\n")

        output_file = root_dir / "ORPHAN_CLUSTERS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(cluster_report)

        print(f"✅ Анализ кластеров: {output_file}")

    # Анализ трендов
    if args.trends:
        print("\n📊 Анализ трендов появления сирот...\n")

        cluster_analyzer = OrphanClusterAnalyzer(finder.all_articles)
        trends = cluster_analyzer.analyze_orphan_trends(orphans)

        print(f"   Тренд: {trends['trend']} ({trends['trend_severity']})")
        print(f"   Скорость появления: {trends['orphan_rate']:.2f}% новых сирот\n")

        # Сохранить отчёт
        trends_report = []
        trends_report.append("# 📊 Анализ трендов сирот\n\n")

        trends_report.append("## Возрастное распределение\n\n")
        trends_report.append(f"- **Fresh (< 7 дней)**: {trends['fresh_count']}\n")
        trends_report.append(f"- **Recent (7-30 дней)**: {trends['recent_count']}\n")
        trends_report.append(f"- **Mature (30-90 дней)**: {trends['mature_count']}\n")
        trends_report.append(f"- **Old (90+ дней)**: {trends['old_count']}\n\n")

        trends_report.append("## Тренд\n\n")
        trend_emoji = {
            'increasing': '📈',
            'decreasing': '📉',
            'stable': '➡️'
        }.get(trends['trend'], '❓')

        trends_report.append(f"{trend_emoji} **Тренд**: {trends['trend']}\n\n")
        trends_report.append(f"**Severity**: {trends['trend_severity']}\n\n")
        trends_report.append(f"**Скорость появления**: {trends['orphan_rate']:.2f}% новых/недавних сирот\n\n")

        if trends['trend'] == 'increasing':
            trends_report.append("⚠️  **Внимание**: Число сирот растёт! Рекомендуется усилить связывание новых статей.\n")
        elif trends['trend'] == 'decreasing':
            trends_report.append("✅ **Хорошо**: Число сирот уменьшается. Продолжайте в том же духе!\n")

        output_file = root_dir / "ORPHAN_TRENDS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(trends_report)

        print(f"✅ Анализ трендов: {output_file}")

    # Топ критичных
    if args.top_critical:
        n = args.top_critical

        print(f"\n🔴 Топ-{n} критичных сирот:\n")

        # Фильтровать критичные
        critical = [o for o in orphans if o['classification']['severity'] == 'high']

        if not critical:
            print("   Нет критичных сирот! ✅")
        else:
            for i, orphan in enumerate(critical[:n], 1):
                path = orphan['path']
                classification = orphan['classification']
                metadata = orphan['metadata']

                print(f"{i}. **{Path(path).stem}**")
                print(f"   Путь: {path}")
                print(f"   Тип: {classification['type']}")
                print(f"   Возраст: {metadata['age_days']} дней")
                print(f"   Кандидатов: {len(orphan['candidates'])}")
                if classification['reason']:
                    print(f"   Причины: {', '.join(classification['reason'])}")
                print()

    # HTML визуализация
    if args.html:
        print("\n🎨 Создание интерактивного HTML отчёта...\n")

        visualizer = OrphanVisualizer(
            finder.all_articles,
            orphans,
            finder.incoming_links,
            finder.outgoing_links
        )

        html_content = visualizer.generate_html_report()

        output_file = root_dir / "orphans_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML отчёт: {output_file}")
        print(f"   Откройте {output_file} в браузере")

    print("\n✨ Анализ завершён!")


if __name__ == "__main__":
    main()
