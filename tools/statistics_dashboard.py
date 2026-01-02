#!/usr/bin/env python3
"""
Statistics Dashboard - Статистический дашборд
Комплексный обзор всех метрик базы знаний

Вдохновлено: Google Analytics, GitHub Insights
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import subprocess
from datetime import datetime, timedelta
import json


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
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    dashboard = StatisticsDashboard(root_dir)
    dashboard.analyze_all()
    dashboard.generate_dashboard()
    dashboard.save_json()


if __name__ == "__main__":
    main()
