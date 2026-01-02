#!/usr/bin/env python3
"""
Генерация детальной статистики по базе знаний
"""

import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import yaml
import json


class StatisticsGenerator:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.stats = {
            'overview': {},
            'categories': {},
            'tags': {},
            'quality': {},
            'growth': {},
            'top_articles': []
        }

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return None, content

            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except:
            return None, ""

    def count_words(self, text):
        """Подсчитать слова"""
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    def analyze_article(self, file_path):
        """Анализ одной статьи"""
        fm, content = self.extract_frontmatter(file_path)

        analysis = {
            'file': str(file_path.relative_to(self.root_dir)),
            'has_metadata': fm is not None,
            'word_count': self.count_words(content),
            'line_count': len(content.split('\n')),
            'headers': len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            'links': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            'code_blocks': len(re.findall(r'```', content)) // 2
        }

        if fm:
            analysis.update({
                'title': fm.get('title'),
                'category': fm.get('category'),
                'subcategory': fm.get('subcategory'),
                'tags': fm.get('tags', []),
                'tag_count': len(fm.get('tags', [])),
                'status': fm.get('status'),
                'date': fm.get('date')
            })

        return analysis

    def generate_overview(self, articles):
        """Общая статистика"""
        total_articles = len(articles)
        total_words = sum(a['word_count'] for a in articles)
        total_tags = sum(a['tag_count'] for a in articles if 'tag_count' in a)

        self.stats['overview'] = {
            'total_articles': total_articles,
            'total_words': total_words,
            'avg_words_per_article': total_words / total_articles if total_articles > 0 else 0,
            'total_tags_used': total_tags,
            'avg_tags_per_article': total_tags / total_articles if total_articles > 0 else 0,
            'with_metadata': sum(1 for a in articles if a['has_metadata']),
            'metadata_coverage': sum(1 for a in articles if a['has_metadata']) / total_articles * 100 if total_articles > 0 else 0
        }

    def generate_category_stats(self, articles):
        """Статистика по категориям"""
        by_category = defaultdict(list)

        for article in articles:
            if 'category' in article:
                by_category[article['category']].append(article)

        for category, cat_articles in by_category.items():
            self.stats['categories'][category] = {
                'count': len(cat_articles),
                'total_words': sum(a['word_count'] for a in cat_articles),
                'avg_words': sum(a['word_count'] for a in cat_articles) / len(cat_articles),
                'subcategories': len(set(a.get('subcategory') for a in cat_articles if a.get('subcategory')))
            }

    def generate_tag_stats(self, articles):
        """Статистика по тегам"""
        all_tags = []
        for article in articles:
            if 'tags' in article:
                all_tags.extend(article['tags'])

        tag_counts = Counter(all_tags)

        self.stats['tags'] = {
            'unique_tags': len(tag_counts),
            'total_tag_uses': len(all_tags),
            'top_tags': [
                {'tag': tag, 'count': count}
                for tag, count in tag_counts.most_common(20)
            ],
            'singleton_tags': sum(1 for count in tag_counts.values() if count == 1)
        }

    def generate_quality_metrics(self, articles):
        """Метрики качества"""
        self.stats['quality'] = {
            'with_good_tags': sum(1 for a in articles if a.get('tag_count', 0) >= 3),
            'with_links': sum(1 for a in articles if a.get('links', 0) > 0),
            'with_code': sum(1 for a in articles if a.get('code_blocks', 0) > 0),
            'with_headers': sum(1 for a in articles if a.get('headers', 0) > 0),
            'short_articles': sum(1 for a in articles if a.get('word_count', 0) < 100),
            'medium_articles': sum(1 for a in articles if 100 <= a.get('word_count', 0) < 500),
            'long_articles': sum(1 for a in articles if a.get('word_count', 0) >= 500)
        }

    def find_top_articles(self, articles):
        """Топовые статьи"""
        # По количеству слов
        by_words = sorted(articles, key=lambda x: x.get('word_count', 0), reverse=True)

        # По количеству ссылок
        by_links = sorted(articles, key=lambda x: x.get('links', 0), reverse=True)

        self.stats['top_articles'] = {
            'longest': [
                {'title': a.get('title', a['file']), 'words': a['word_count']}
                for a in by_words[:10]
            ],
            'most_linked': [
                {'title': a.get('title', a['file']), 'links': a.get('links', 0)}
                for a in by_links[:10] if a.get('links', 0) > 0
            ]
        }

    def print_report(self):
        """Вывести отчет"""
        print("\n" + "="*80)
        print("📊 СТАТИСТИКА БАЗЫ ЗНАНИЙ")
        print("="*80 + "\n")

        # Общая статистика
        print("📈 Общая статистика:")
        o = self.stats['overview']
        print(f"   Всего статей: {o['total_articles']}")
        print(f"   Всего слов: {o['total_words']:,}")
        print(f"   Среднее слов на статью: {o['avg_words_per_article']:.0f}")
        print(f"   Среднее тегов на статью: {o['avg_tags_per_article']:.1f}")
        print(f"   Покрытие метаданными: {o['metadata_coverage']:.1f}%")

        # По категориям
        print("\n📁 По категориям:")
        for cat, data in self.stats['categories'].items():
            print(f"   {cat}:")
            print(f"      Статей: {data['count']}")
            print(f"      Слов: {data['total_words']:,}")
            print(f"      Подкатегорий: {data['subcategories']}")

        # Теги
        print("\n🏷️  Теги:")
        t = self.stats['tags']
        print(f"   Уникальных тегов: {t['unique_tags']}")
        print(f"   Топ-10 тегов:")
        for tag_info in t['top_tags'][:10]:
            print(f"      {tag_info['tag']}: {tag_info['count']}")

        # Качество
        print("\n✅ Качество:")
        q = self.stats['quality']
        print(f"   С хорошими тегами (3+): {q['with_good_tags']}")
        print(f"   Со ссылками: {q['with_links']}")
        print(f"   С примерами кода: {q['with_code']}")
        print(f"   Распределение по размеру:")
        print(f"      Короткие (<100 слов): {q['short_articles']}")
        print(f"      Средние (100-500 слов): {q['medium_articles']}")
        print(f"      Длинные (>500 слов): {q['long_articles']}")

        # Топ статей
        print("\n🏆 Топ статей:")
        print("   Самые длинные:")
        for article in self.stats['top_articles']['longest'][:5]:
            print(f"      {article['title']}: {article['words']} слов")

        print("\n" + "="*80)

    def save_json(self, output_file):
        """Сохранить статистику в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

        print(f"\n📝 Статистика сохранена в: {output_file}")

    def run(self):
        """Запустить генерацию статистики"""
        print("📊 Генерация статистики...\n")

        # Собрать все статьи
        articles = []
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            analysis = self.analyze_article(md_file)
            articles.append(analysis)

        # Генерация разных видов статистики
        self.generate_overview(articles)
        self.generate_category_stats(articles)
        self.generate_tag_stats(articles)
        self.generate_quality_metrics(articles)
        self.find_top_articles(articles)

        # Вывод отчета
        self.print_report()

        # Сохранение в JSON
        output_file = self.root_dir / "statistics.json"
        self.save_json(output_file)


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = StatisticsGenerator(root_dir)
    generator.run()


if __name__ == "__main__":
    main()
