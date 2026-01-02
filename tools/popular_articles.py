#!/usr/bin/env python3
"""
Popular Articles Tracking - Трекинг популярных статей
Определяет самые популярные статьи на основе множества метрик

Вдохновлено: Google Analytics, Wikipedia pageviews
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import subprocess
import json
import math


class PopularityTracker:
    """Трекер популярности статей"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Метрики
        self.articles = {}
        self.popularity_scores = {}

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
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tracker = PopularityTracker(root_dir)
    tracker.analyze_all()
    tracker.generate_report()
    tracker.save_json()


if __name__ == "__main__":
    main()
