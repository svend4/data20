#!/usr/bin/env python3
"""
Search Index - Поисковый индекс
Полнотекстовый поиск по базе знаний

Вдохновлено: Elasticsearch, Lucene
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json
import math


class SearchIndexBuilder:
    """Построитель поискового индекса"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Инвертированный индекс
        self.index = defaultdict(lambda: defaultdict(int))

        # Документы
        self.documents = {}

        # IDF (inverse document frequency)
        self.idf = {}

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

    def tokenize(self, text):
        """Токенизация текста"""
        # Удалить markdown
        text = re.sub(r'[#*`\[\]()]', ' ', text)

        # Извлечь слова (русский + английский)
        words = re.findall(r'\b[а-яёa-z]{2,}\b', text.lower())

        return words

    def build_index(self):
        """Построить индекс"""
        print("🔍 Построение поискового индекса...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            tags = frontmatter.get('tags', []) if frontmatter else []

            # Объединить заголовок и контент для индексации
            # Заголовок имеет больший вес
            full_text = f"{title} {title} {title} " + content
            full_text += " " + " ".join(tags)

            # Токенизация
            words = self.tokenize(full_text)

            # Сохранить документ
            self.documents[article_path] = {
                'title': title,
                'tags': tags,
                'word_count': len(words)
            }

            # Построить инвертированный индекс
            word_freq = defaultdict(int)
            for word in words:
                word_freq[word] += 1

            for word, freq in word_freq.items():
                self.index[word][article_path] = freq

        # Вычислить IDF
        total_docs = len(self.documents)

        for word, docs in self.index.items():
            self.idf[word] = math.log(total_docs / len(docs))

        print(f"   Документов проиндексировано: {len(self.documents)}")
        print(f"   Уникальных слов: {len(self.index)}\n")

    def search(self, query, limit=10):
        """Поиск по запросу"""
        # Токенизация запроса
        query_words = self.tokenize(query)

        if not query_words:
            return []

        # Вычислить TF-IDF для каждого документа
        scores = defaultdict(float)

        for word in query_words:
            if word not in self.index:
                continue

            idf = self.idf[word]

            for doc_path, tf in self.index[word].items():
                # TF-IDF
                tf_normalized = tf / self.documents[doc_path]['word_count']
                scores[doc_path] += tf_normalized * idf

        # Сортировать по релевантности
        results = [
            {
                'path': doc_path,
                'title': self.documents[doc_path]['title'],
                'score': score
            }
            for doc_path, score in scores.items()
        ]

        results.sort(key=lambda x: -x['score'])

        return results[:limit]

    def save_index(self):
        """Сохранить индекс в JSON"""
        data = {
            'documents': self.documents,
            'index': {
                word: dict(docs)
                for word, docs in self.index.items()
            },
            'idf': self.idf
        }

        output_file = self.root_dir / "search_index.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Индекс сохранён: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Search Index')
    parser.add_argument('-q', '--query', help='Поисковый запрос')
    parser.add_argument('-n', '--limit', type=int, default=10, help='Количество результатов')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = SearchIndexBuilder(root_dir)
    builder.build_index()
    builder.save_index()

    if args.query:
        print(f"\n🔍 Поиск: '{args.query}'\n")
        results = builder.search(args.query, limit=args.limit)

        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} (score: {result['score']:.2f})")
                print(f"   {result['path']}\n")
        else:
            print("Ничего не найдено")


if __name__ == "__main__":
    main()
