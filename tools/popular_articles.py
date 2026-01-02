#!/usr/bin/env python3
"""
Popular Articles Tracking - Трекинг популярных статей
Определяет самые популярные статьи на основе множества метрик

Вдохновлено: Google Analytics, Wikipedia pageviews
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import subprocess
import json
import math
import argparse
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class TrendAnalyzer:
    """Анализатор трендов и прогнозирование"""

    def __init__(self, articles: Dict):
        self.articles = articles

    def calculate_growth_rate(self, article_path: str, window_days: int = 30) -> float:
        """Вычислить темп роста (на основе частоты редактирований)"""
        data = self.articles.get(article_path)
        if not data:
            return 0.0

        edit_count = data.get('edit_count', 0)
        days_since_edit = data.get('days_since_edit', 999)

        if days_since_edit >= window_days:
            return 0.0

        # Простая оценка: редактирований / дней
        recent_edits = edit_count  # В идеале считать только за window_days
        growth = recent_edits / max(1, days_since_edit)

        return growth

    def detect_viral_content(self, min_links: int = 5, max_age_days: int = 60) -> List[Tuple[str, float]]:
        """Обнаружить вирусный контент (много ссылок за короткое время)"""
        viral = []

        for article_path, data in self.articles.items():
            if data['days_since_edit'] <= max_age_days:
                links = data.get('incoming_links', 0)
                if links >= min_links:
                    # Viral coefficient: links / age
                    age = max(1, data['days_since_edit'])
                    viral_score = links / math.sqrt(age)
                    viral.append((article_path, viral_score))

        return sorted(viral, key=lambda x: -x[1])

    def calculate_momentum(self, article_path: str) -> float:
        """Вычислить импульс (velocity × quality)"""
        data = self.articles.get(article_path)
        if not data:
            return 0.0

        # Velocity: edits / age
        age = max(1, data['days_since_edit'])
        velocity = data.get('edit_count', 0) / age

        # Quality boost
        quality = data.get('content_quality', 0)

        momentum = velocity * (1 + quality)
        return momentum

    def predict_trend_direction(self, article_path: str) -> str:
        """Предсказать направление тренда: rising, stable, declining"""
        data = self.articles.get(article_path)
        if not data:
            return 'unknown'

        days_since_edit = data['days_since_edit']
        edit_count = data['edit_count']

        # Rising: недавно обновлено и много редактирований
        if days_since_edit <= 14 and edit_count >= 3:
            return 'rising'

        # Declining: давно не обновлялось
        if days_since_edit > 90:
            return 'declining'

        # Stable: умеренная активность
        return 'stable'


class CategoryPopularityAnalyzer:
    """Анализ популярности по категориям"""

    def __init__(self, articles: Dict, popularity_scores: Dict):
        self.articles = articles
        self.popularity_scores = popularity_scores

    def get_popular_by_category(self) -> Dict[str, List[Tuple[str, float]]]:
        """Топ статей по каждой категории (из тегов)"""
        category_articles = defaultdict(list)

        for article_path, data in self.articles.items():
            tags = data.get('tags', [])
            score = self.popularity_scores.get(article_path, 0.0)

            for tag in tags:
                category_articles[tag].append((article_path, score))

        # Сортировать
        for tag in category_articles:
            category_articles[tag].sort(key=lambda x: -x[1])

        return dict(category_articles)

    def get_category_stats(self) -> Dict[str, Dict]:
        """Статистика по категориям"""
        stats = defaultdict(lambda: {
            'count': 0,
            'total_score': 0.0,
            'avg_score': 0.0,
            'max_score': 0.0
        })

        for article_path, data in self.articles.items():
            tags = data.get('tags', [])
            score = self.popularity_scores.get(article_path, 0.0)

            for tag in tags:
                stats[tag]['count'] += 1
                stats[tag]['total_score'] += score
                stats[tag]['max_score'] = max(stats[tag]['max_score'], score)

        # Вычислить средние
        for tag in stats:
            if stats[tag]['count'] > 0:
                stats[tag]['avg_score'] = stats[tag]['total_score'] / stats[tag]['count']

        return dict(stats)

    def get_dominant_categories(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Найти доминантные категории (по средней популярности)"""
        stats = self.get_category_stats()

        dominant = [
            (tag, data['avg_score'])
            for tag, data in stats.items()
            if data['count'] >= 2  # Минимум 2 статьи
        ]

        return sorted(dominant, key=lambda x: -x[1])[:top_n]


class TimeSeriesPopularityAnalyzer:
    """Анализ популярности во времени"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.knowledge_dir = root_dir / "knowledge"

    def get_edit_timeline(self, file_path: Path, months: int = 6) -> List[Tuple[str, int]]:
        """Получить временную шкалу редактирований"""
        try:
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')

            result = subprocess.run(
                ['git', 'log', '--pretty=format:%ad', '--date=short', f'--since={cutoff_str}', '--', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                dates = result.stdout.strip().split('\n')

                # Группировать по месяцам
                monthly_counts = Counter()
                for date_str in dates:
                    if date_str:
                        # YYYY-MM
                        month_key = date_str[:7]
                        monthly_counts[month_key] += 1

                # Сортировать
                timeline = sorted(monthly_counts.items())
                return timeline

        except:
            pass

        return []

    def detect_activity_spikes(self, file_path: Path) -> List[str]:
        """Обнаружить всплески активности"""
        timeline = self.get_edit_timeline(file_path, months=12)

        if len(timeline) < 3:
            return []

        spikes = []
        counts = [count for _, count in timeline]

        if counts:
            avg = sum(counts) / len(counts)
            threshold = avg * 2  # Всплеск = 2× выше среднего

            for month, count in timeline:
                if count >= threshold:
                    spikes.append(month)

        return spikes

    def calculate_consistency_score(self, file_path: Path, months: int = 6) -> float:
        """Оценить консистентность обновлений (0.0-1.0)"""
        timeline = self.get_edit_timeline(file_path, months=months)

        if not timeline:
            return 0.0

        # Количество месяцев с обновлениями
        active_months = len(timeline)

        # Консистентность = active_months / total_months
        consistency = active_months / months

        return min(consistency, 1.0)


class EngagementScorer:
    """Оценка вовлечённости на основе различных сигналов"""

    def __init__(self, articles: Dict):
        self.articles = articles

    def calculate_engagement_score(self, article_path: str) -> float:
        """Комплексная оценка вовлечённости"""
        data = self.articles.get(article_path)
        if not data:
            return 0.0

        score = 0.0

        # 1. Ссылки (сильный сигнал)
        links = data.get('incoming_links', 0)
        score += links * 3.0

        # 2. Редактирования (активность)
        edits = data.get('edit_count', 0)
        score += math.sqrt(edits) * 2.0

        # 3. Свежесть
        days = data.get('days_since_edit', 999)
        recency_bonus = max(0, (90 - days) / 90) * 2.0
        score += recency_bonus

        # 4. Качество
        quality = data.get('content_quality', 0)
        score += quality * 1.5

        # 5. Размер (более длинные статьи = больше усилий)
        length = data.get('length', 0)
        length_score = min(math.log(1 + length / 1000), 2.0)
        score += length_score

        return score

    def get_engagement_distribution(self) -> Dict[str, int]:
        """Распределение по уровням вовлечённости"""
        distribution = {
            'very_high': 0,   # >15
            'high': 0,        # 10-15
            'medium': 0,      # 5-10
            'low': 0,         # 1-5
            'very_low': 0     # <1
        }

        for article_path in self.articles:
            score = self.calculate_engagement_score(article_path)

            if score > 15:
                distribution['very_high'] += 1
            elif score > 10:
                distribution['high'] += 1
            elif score > 5:
                distribution['medium'] += 1
            elif score > 1:
                distribution['low'] += 1
            else:
                distribution['very_low'] += 1

        return distribution


class PopularityTracker:
    """Трекер популярности статей"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Метрики
        self.articles = {}
        self.popularity_scores = {}

        # Анализаторы
        self.trend_analyzer = None
        self.category_analyzer = None
        self.timeseries_analyzer = None
        self.engagement_scorer = None

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

    def count_incoming_links(self, target_path):
        """Подсчитать входящие ссылки"""
        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            # Ссылки в контенте
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for text, link in links:
                if link.startswith('http'):
                    continue

                try:
                    resolved = (md_file.parent / link.split('#')[0]).resolve()
                    if resolved.exists() and resolved.is_relative_to(self.root_dir):
                        resolved_path = str(resolved.relative_to(self.root_dir))
                        if resolved_path == target_path:
                            count += 1
                except:
                    pass

        return count

    def get_edit_count(self, file_path):
        """Получить количество редактирований из git"""
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '--', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except:
            pass

        return 0

    def get_recent_activity(self, file_path):
        """Получить недавнюю активность (дней с последнего изменения)"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%ad', '--date=short', '--', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                from datetime import datetime
                last_edit = datetime.strptime(result.stdout.strip(), '%Y-%m-%d')
                days_ago = (datetime.now() - last_edit).days
                return days_ago
        except:
            pass

        return 999  # Очень старая статья

    def calculate_content_quality(self, content):
        """Оценить качество контента"""
        if not content:
            return 0.0

        score = 0.0

        # Длина контента
        length = len(content)
        if length > 3000:
            score += 1.0
        elif length > 1000:
            score += 0.5
        elif length > 500:
            score += 0.25

        # Наличие заголовков
        headings = len(re.findall(r'^#{2,6}\s', content, re.MULTILINE))
        score += min(headings * 0.1, 1.0)

        # Наличие списков
        lists = len(re.findall(r'^\s*[-*]\s', content, re.MULTILINE))
        score += min(lists * 0.05, 0.5)

        # Наличие кода
        code_blocks = len(re.findall(r'```', content))
        score += min(code_blocks * 0.1, 0.5)

        # Наличие ссылок
        links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        score += min(links * 0.05, 1.0)

        return score

    def analyze_all(self):
        """Анализировать все статьи"""
        print("⭐ Анализ популярности статей...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Собрать метрики
            incoming_links = self.count_incoming_links(article_path)
            edit_count = self.get_edit_count(md_file)
            days_since_edit = self.get_recent_activity(md_file)
            content_quality = self.calculate_content_quality(content)

            self.articles[article_path] = {
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'tags': frontmatter.get('tags', []) if frontmatter else [],
                'incoming_links': incoming_links,
                'edit_count': edit_count,
                'days_since_edit': days_since_edit,
                'content_quality': content_quality,
                'length': len(content)
            }

            # Вычислить общий балл популярности
            popularity = self.calculate_popularity(
                incoming_links, edit_count, days_since_edit, content_quality
            )

            self.popularity_scores[article_path] = popularity

        print(f"   Статей проанализировано: {len(self.articles)}\n")

        # Инициализировать анализаторы
        self.trend_analyzer = TrendAnalyzer(self.articles)
        self.category_analyzer = CategoryPopularityAnalyzer(self.articles, self.popularity_scores)
        self.timeseries_analyzer = TimeSeriesPopularityAnalyzer(self.root_dir)
        self.engagement_scorer = EngagementScorer(self.articles)

    def calculate_popularity(self, incoming_links, edit_count, days_since_edit, content_quality):
        """Вычислить общий балл популярности"""
        # Нормализовать метрики
        link_score = math.log(1 + incoming_links) * 2.0
        edit_score = math.log(1 + edit_count) * 1.5

        # Штраф за давность (экспоненциальное затухание)
        recency_score = math.exp(-days_since_edit / 30) * 2.0

        quality_score = content_quality * 1.0

        # Итоговый балл
        total = link_score + edit_score + recency_score + quality_score

        return total

    def get_top_articles(self, limit=10):
        """Получить топ статей"""
        sorted_articles = sorted(
            self.popularity_scores.items(),
            key=lambda x: -x[1]
        )

        return sorted_articles[:limit]

    def get_trending_articles(self, limit=10):
        """Получить трендовые статьи (недавно активные)"""
        trending = []

        for article_path, data in self.articles.items():
            if data['days_since_edit'] <= 30:  # Обновлено в последние 30 дней
                score = data['edit_count'] * (1.0 / (1 + data['days_since_edit']))
                trending.append((article_path, score))

        trending.sort(key=lambda x: -x[1])
        return trending[:limit]

    def get_hidden_gems(self, limit=10):
        """Получить скрытые жемчужины (качественные, но мало ссылок)"""
        gems = []

        for article_path, data in self.articles.items():
            if data['content_quality'] > 2.0 and data['incoming_links'] < 3:
                gems.append((article_path, data['content_quality']))

        gems.sort(key=lambda x: -x[1])
        return gems[:limit]

    def run_trend_analysis(self):
        """Провести анализ трендов"""
        if not self.trend_analyzer:
            print("⚠️  Сначала выполните analyze_all()")
            return

        print("\n📈 Анализ трендов\n")

        # Вирусный контент
        viral = self.trend_analyzer.detect_viral_content(min_links=2, max_age_days=60)
        if viral:
            print(f"🔥 Вирусный контент (топ-5):")
            for article_path, viral_score in viral[:5]:
                title = self.articles[article_path]['title']
                print(f"   • {title} (viral score: {viral_score:.2f})")

        # Направления трендов
        print(f"\n🎯 Направления трендов:")
        trend_counts = Counter()

        for article_path in self.articles:
            direction = self.trend_analyzer.predict_trend_direction(article_path)
            trend_counts[direction] += 1

        for direction, count in trend_counts.most_common():
            print(f"   {direction}: {count} статей")

    def run_category_analysis(self):
        """Провести анализ по категориям"""
        if not self.category_analyzer:
            print("⚠️  Сначала выполните analyze_all()")
            return

        print("\n🏷️  Анализ по категориям\n")

        # Доминантные категории
        dominant = self.category_analyzer.get_dominant_categories(top_n=5)
        if dominant:
            print("Топ-5 категорий (по средней популярности):")
            for tag, avg_score in dominant:
                print(f"   • {tag}: {avg_score:.2f}")

        # Статистика
        print(f"\nСтатистика по категориям:")
        stats = self.category_analyzer.get_category_stats()
        for tag, data in sorted(stats.items(), key=lambda x: -x[1]['count'])[:10]:
            print(f"   • {tag}: {data['count']} статей, макс балл: {data['max_score']:.2f}")

    def run_engagement_analysis(self):
        """Провести анализ вовлечённости"""
        if not self.engagement_scorer:
            print("⚠️  Сначала выполните analyze_all()")
            return

        print("\n💬 Анализ вовлечённости\n")

        distribution = self.engagement_scorer.get_engagement_distribution()

        print("Распределение по уровням вовлечённости:")
        print(f"   Очень высокая (>15): {distribution['very_high']}")
        print(f"   Высокая (10-15):     {distribution['high']}")
        print(f"   Средняя (5-10):      {distribution['medium']}")
        print(f"   Низкая (1-5):        {distribution['low']}")
        print(f"   Очень низкая (<1):   {distribution['very_low']}")

        # Топ по вовлечённости
        engagement_scores = [
            (article_path, self.engagement_scorer.calculate_engagement_score(article_path))
            for article_path in self.articles
        ]
        engagement_scores.sort(key=lambda x: -x[1])

        print(f"\nТоп-5 по вовлечённости:")
        for article_path, score in engagement_scores[:5]:
            title = self.articles[article_path]['title']
            print(f"   • {title} ({score:.2f})")

    def export_html(self, output_file: str = "popular_articles.html"):
        """Экспортировать в HTML с визуализацией"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='ru'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("  <title>Популярные статьи</title>")
        html.append("  <style>")
        html.append("    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; background: #f5f5f5; }")
        html.append("    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }")
        html.append("    h1 { color: #333; border-bottom: 3px solid #FF9800; padding-bottom: 10px; }")
        html.append("    h2 { color: #555; margin-top: 30px; }")
        html.append("    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }")
        html.append("    .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }")
        html.append("    .stat-value { font-size: 32px; font-weight: bold; }")
        html.append("    .stat-label { font-size: 14px; opacity: 0.9; }")
        html.append("    .article-card { margin: 15px 0; padding: 20px; background: #fafafa; border-radius: 8px; border-left: 4px solid #FF9800; }")
        html.append("    .article-title { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }")
        html.append("    .article-meta { display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px; }")
        html.append("    .meta-item { font-size: 14px; color: #666; }")
        html.append("    .badge { display: inline-block; background: #FF9800; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-left: 5px; }")
        html.append("    .trend-badge { background: #4CAF50; }")
        html.append("    .gem-badge { background: #9C27B0; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("  <div class='container'>")
        html.append("    <h1>⭐ Популярные статьи</h1>")

        # Статистика
        total_articles = len(self.articles)
        avg_score = sum(self.popularity_scores.values()) / len(self.popularity_scores) if self.popularity_scores else 0

        html.append("    <div class='stats'>")
        html.append(f"      <div class='stat-card'><div class='stat-value'>{total_articles}</div><div class='stat-label'>Всего статей</div></div>")
        html.append(f"      <div class='stat-card'><div class='stat-value'>{avg_score:.1f}</div><div class='stat-label'>Средний балл</div></div>")

        # Топ статьи
        html.append("    </div>")
        html.append("    <h2>Топ-20 самых популярных</h2>")

        top_articles = self.get_top_articles(20)

        for i, (article_path, score) in enumerate(top_articles, 1):
            data = self.articles[article_path]

            html.append(f"    <div class='article-card'>")
            html.append(f"      <div class='article-title'>#{i} {data['title']} <span class='badge'>{score:.1f}</span></div>")
            html.append(f"      <div class='article-meta'>")
            html.append(f"        <div class='meta-item'>📎 Ссылок: {data['incoming_links']}</div>")
            html.append(f"        <div class='meta-item'>✏️ Редактирований: {data['edit_count']}</div>")
            html.append(f"        <div class='meta-item'>📅 Обновлено: {data['days_since_edit']} дн. назад</div>")
            html.append(f"        <div class='meta-item'>⭐ Качество: {data['content_quality']:.1f}</div>")
            html.append(f"      </div>")
            html.append(f"    </div>")

        # Трендовые
        trending = self.get_trending_articles(10)
        if trending:
            html.append("    <h2>🔥 Трендовые статьи</h2>")
            for article_path, _ in trending:
                data = self.articles[article_path]
                html.append(f"    <div class='article-card'>")
                html.append(f"      <div class='article-title'>{data['title']} <span class='badge trend-badge'>Trending</span></div>")
                html.append(f"      <div class='meta-item'>Обновлено {data['days_since_edit']} дней назад</div>")
                html.append(f"    </div>")

        # Скрытые жемчужины
        gems = self.get_hidden_gems(10)
        if gems:
            html.append("    <h2>💎 Скрытые жемчужины</h2>")
            for article_path, quality in gems:
                data = self.articles[article_path]
                html.append(f"    <div class='article-card'>")
                html.append(f"      <div class='article-title'>{data['title']} <span class='badge gem-badge'>Gem</span></div>")
                html.append(f"      <div class='meta-item'>Качество: {quality:.1f}, Ссылок: {data['incoming_links']}</div>")
                html.append(f"    </div>")

        html.append("  </div>")
        html.append("</body>")
        html.append("</html>")

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))

        print(f"\n✅ HTML экспорт: {output_path}")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# ⭐ Популярные статьи\n\n")
        lines.append("> Определение популярности на основе множества метрик\n\n")

        # Методология
        lines.append("## Методология\n\n")
        lines.append("Популярность рассчитывается на основе:\n\n")
        lines.append("- **Входящие ссылки** (вес: 2.0) — сколько других статей ссылаются на эту\n")
        lines.append("- **История редактирований** (вес: 1.5) — как часто обновляется\n")
        lines.append("- **Свежесть** (вес: 2.0) — когда последний раз обновлялась\n")
        lines.append("- **Качество контента** (вес: 1.0) — длина, структура, ссылки\n\n")

        # Топ статей
        lines.append("## Топ-10 самых популярных\n\n")

        top_articles = self.get_top_articles(10)

        for i, (article_path, score) in enumerate(top_articles, 1):
            data = self.articles[article_path]

            lines.append(f"### {i}. {data['title']}\n\n")
            lines.append(f"- **Файл**: [{article_path}]({article_path})\n")
            lines.append(f"- **Балл популярности**: {score:.2f}\n")
            lines.append(f"- **Входящих ссылок**: {data['incoming_links']}\n")
            lines.append(f"- **Редактирований**: {data['edit_count']}\n")
            lines.append(f"- **Обновлено**: {data['days_since_edit']} дней назад\n")
            lines.append(f"- **Качество контента**: {data['content_quality']:.2f}\n")
            lines.append(f"- **Размер**: {data['length']} символов\n\n")

        # Трендовые статьи
        trending = self.get_trending_articles(10)

        if trending:
            lines.append("\n## 🔥 Трендовые статьи\n\n")
            lines.append("> Активно обновляются в последнее время\n\n")

            for i, (article_path, trend_score) in enumerate(trending, 1):
                data = self.articles[article_path]

                lines.append(f"{i}. **{data['title']}**\n")
                lines.append(f"   - [{article_path}]({article_path})\n")
                lines.append(f"   - Обновлено {data['days_since_edit']} дней назад\n")
                lines.append(f"   - Редактирований: {data['edit_count']}\n\n")

        # Скрытые жемчужины
        gems = self.get_hidden_gems(10)

        if gems:
            lines.append("\n## 💎 Скрытые жемчужины\n\n")
            lines.append("> Качественные статьи, которые заслуживают большего внимания\n\n")

            for i, (article_path, quality) in enumerate(gems, 1):
                data = self.articles[article_path]

                lines.append(f"{i}. **{data['title']}**\n")
                lines.append(f"   - [{article_path}]({article_path})\n")
                lines.append(f"   - Качество: {quality:.2f}\n")
                lines.append(f"   - Входящих ссылок: {data['incoming_links']}\n\n")

        output_file = self.root_dir / "POPULAR_ARTICLES.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить данные в JSON"""
        data = {
            'articles': {
                article_path: {
                    **article_data,
                    'tags': list(article_data['tags']),
                    'popularity_score': self.popularity_scores[article_path]
                }
                for article_path, article_data in self.articles.items()
            },
            'rankings': {
                'top': [
                    {'article': article, 'score': score}
                    for article, score in self.get_top_articles(20)
                ],
                'trending': [
                    {'article': article, 'score': score}
                    for article, score in self.get_trending_articles(20)
                ],
                'hidden_gems': [
                    {'article': article, 'quality': quality}
                    for article, quality in self.get_hidden_gems(20)
                ]
            }
        }

        output_file = self.root_dir / "popular_articles.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='⭐ Popular Articles Tracking - Трекинг популярных статей',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                      # Полный анализ и отчёты
  %(prog)s --trending           # Анализ трендов
  %(prog)s --category           # Анализ по категориям
  %(prog)s --engagement         # Анализ вовлечённости
  %(prog)s --html report.html   # Экспорт в HTML
  %(prog)s --all                # Всё: анализ + отчёты + экспорты
        """
    )

    parser.add_argument(
        '--trending',
        action='store_true',
        help='Провести анализ трендов и вирусного контента'
    )

    parser.add_argument(
        '--category',
        action='store_true',
        help='Провести анализ по категориям/тегам'
    )

    parser.add_argument(
        '--engagement',
        action='store_true',
        help='Провести анализ вовлечённости'
    )

    parser.add_argument(
        '--html',
        metavar='FILE',
        nargs='?',
        const='popular_articles.html',
        help='Экспортировать в HTML (по умолчанию: popular_articles.html)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Выполнить все анализы и экспорты'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Не создавать markdown отчёт'
    )

    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Не создавать JSON файл'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tracker = PopularityTracker(root_dir)

    # Анализ всех статей
    tracker.analyze_all()

    # Режим --all
    if args.all:
        tracker.run_trend_analysis()
        tracker.run_category_analysis()
        tracker.run_engagement_analysis()
        if not args.no_report:
            tracker.generate_report()
        if not args.no_json:
            tracker.save_json()
        tracker.export_html(args.html or 'popular_articles.html')
        return

    # Отдельные анализы
    if args.trending:
        tracker.run_trend_analysis()

    if args.category:
        tracker.run_category_analysis()

    if args.engagement:
        tracker.run_engagement_analysis()

    # HTML экспорт
    if args.html:
        tracker.export_html(args.html)

    # Действия по умолчанию (если не указаны специфичные флаги)
    if not any([args.trending, args.category, args.engagement, args.html]):
        if not args.no_report:
            tracker.generate_report()
        if not args.no_json:
            tracker.save_json()


if __name__ == "__main__":
    main()
