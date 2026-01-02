#!/usr/bin/env python3
"""
Скрипт для поиска дубликатов и похожей информации
Помогает избежать повторений и найти связи между документами
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import yaml


class DuplicateFinder:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.articles = []

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return None, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except:
            return None, content

    def calculate_similarity(self, text1, text2):
        """
        Простой расчет схожести текстов
        Можно улучшить через cosine similarity или embedding
        """
        # Простой подход: сравнение общих слов
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        # Jaccard similarity
        return len(intersection) / len(union)

    def find_similar_by_tags(self):
        """Найти статьи с похожими тегами"""
        tag_groups = defaultdict(list)

        for article in self.articles:
            tags = article.get('tags', [])
            if tags:
                # Группировать по тегам
                for tag in tags:
                    tag_groups[tag].append(article['file'])

        # Найти группы с более чем 1 статьей
        similar_groups = {tag: files for tag, files in tag_groups.items()
                         if len(files) > 1}

        return similar_groups

    def find_similar_by_title(self):
        """Найти статьи с похожими заголовками"""
        similar = []

        for i, article1 in enumerate(self.articles):
            for article2 in self.articles[i+1:]:
                title1 = article1.get('title', '').lower()
                title2 = article2.get('title', '').lower()

                if not title1 or not title2:
                    continue

                # Простое сравнение слов в заголовке
                words1 = set(title1.split())
                words2 = set(title2.split())

                intersection = words1 & words2

                # Если >50% слов совпадают
                if len(intersection) > len(words1) * 0.5:
                    similar.append({
                        'article1': article1['file'],
                        'article2': article2['file'],
                        'title1': article1.get('title'),
                        'title2': article2.get('title'),
                        'common_words': list(intersection)
                    })

        return similar

    def find_duplicates_by_content(self, threshold=0.7):
        """Найти дубликаты по содержимому"""
        duplicates = []

        for i, article1 in enumerate(self.articles):
            for article2 in self.articles[i+1:]:
                content1 = article1.get('content', '')
                content2 = article2.get('content', '')

                similarity = self.calculate_similarity(content1, content2)

                if similarity > threshold:
                    duplicates.append({
                        'article1': article1['file'],
                        'article2': article2['file'],
                        'similarity': f"{similarity*100:.1f}%"
                    })

        return duplicates

    def scan_articles(self):
        """Сканировать все статьи"""
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter(md_file)

            article = {
                'file': str(md_file.relative_to(self.root_dir)),
                'title': frontmatter.get('title') if frontmatter else None,
                'tags': frontmatter.get('tags', []) if frontmatter else [],
                'content': content
            }

            self.articles.append(article)

    def run(self):
        """Запустить анализ"""
        print("🔍 Поиск дубликатов и похожих статей...\n")

        # Сканировать статьи
        self.scan_articles()
        print(f"📊 Найдено статей: {len(self.articles)}\n")

        # Поиск по тегам
        print("🏷️  Статьи с общими тегами:")
        similar_tags = self.find_similar_by_tags()

        for tag, files in list(similar_tags.items())[:10]:
            print(f"\n   Тег: {tag}")
            for f in files[:5]:
                print(f"     - {f}")
            if len(files) > 5:
                print(f"     ... и еще {len(files) - 5} статей")

        # Поиск по заголовкам
        print("\n\n📝 Статьи с похожими заголовками:")
        similar_titles = self.find_similar_by_title()

        if similar_titles:
            for item in similar_titles[:5]:
                print(f"\n   {item['title1']}")
                print(f"   {item['title2']}")
                print(f"   Общие слова: {', '.join(item['common_words'])}")
        else:
            print("   Не найдено")

        # Поиск дубликатов по содержимому
        print("\n\n🔄 Возможные дубликаты по содержимому (>70% схожести):")
        duplicates = self.find_duplicates_by_content()

        if duplicates:
            for dup in duplicates:
                print(f"\n   {dup['article1']}")
                print(f"   {dup['article2']}")
                print(f"   Схожесть: {dup['similarity']}")
        else:
            print("   Не найдено")

        print("\n✅ Анализ завершен!")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    finder = DuplicateFinder(root_dir)
    finder.run()


if __name__ == "__main__":
    main()
