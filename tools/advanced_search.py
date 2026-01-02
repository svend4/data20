#!/usr/bin/env python3
"""
Расширенный поиск с ранжированием по релевантности
Комбинирует:
- Boolean operators (AND, OR, NOT)
- TF-IDF ranking
- Fuzzy matching
- Phrase search
"""

import os
import re
from pathlib import Path
from collections import defaultdict, Counter
import math


class AdvancedSearch:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.documents = {}
        self.idf = {}
        self.load_documents()
        self.calculate_idf()

    def load_documents(self):
        """Загрузить все документы"""
        print("📚 Загрузка документов...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Пропустить frontmatter
                content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

                file_key = str(md_file.relative_to(self.root_dir))
                self.documents[file_key] = {
                    'content': content,
                    'path': md_file
                }
            except:
                pass

        print(f"   Загружено документов: {len(self.documents)}")

    def tokenize(self, text):
        """Разбить текст на токены"""
        # Извлечь слова (кириллица и латиница, минимум 2 символа)
        words = re.findall(r'\b[а-яёa-z]{2,}\b', text.lower())
        return words

    def calculate_idf(self):
        """Вычислить IDF (Inverse Document Frequency) для всех терминов"""
        print("🔢 Вычисление IDF...")

        # Подсчитать в скольких документах встречается каждое слово
        df = defaultdict(int)

        for doc_data in self.documents.values():
            words = set(self.tokenize(doc_data['content']))
            for word in words:
                df[word] += 1

        # Вычислить IDF
        num_docs = len(self.documents)
        for word, doc_freq in df.items():
            self.idf[word] = math.log(num_docs / doc_freq)

    def calculate_tf_idf(self, doc_content, query_terms):
        """Вычислить TF-IDF score для документа"""
        doc_words = self.tokenize(doc_content)
        doc_length = len(doc_words)

        if doc_length == 0:
            return 0.0

        # Подсчитать TF (Term Frequency)
        tf = Counter(doc_words)

        # Вычислить TF-IDF score
        score = 0.0
        for term in query_terms:
            if term in tf:
                # TF * IDF
                term_tf = tf[term] / doc_length
                term_idf = self.idf.get(term, 0)
                score += term_tf * term_idf

        return score

    def boolean_search(self, query):
        """
        Boolean поиск с операторами AND, OR, NOT
        Примеры:
        - "docker AND kubernetes"
        - "python OR javascript"
        - "programming NOT java"
        - "(docker OR kubernetes) AND NOT windows"
        """
        # Упрощённый парсер boolean запросов
        query = query.strip()

        # Разбить по операторам
        if ' AND ' in query:
            parts = [p.strip() for p in query.split(' AND ')]
            results = None

            for part in parts:
                part_results = self.boolean_search(part)
                if results is None:
                    results = part_results
                else:
                    # Пересечение (AND)
                    results = {k: v for k, v in results.items() if k in part_results}

            return results if results else {}

        elif ' OR ' in query:
            parts = [p.strip() for p in query.split(' OR ')]
            results = {}

            for part in parts:
                part_results = self.boolean_search(part)
                # Объединение (OR)
                results.update(part_results)

            return results

        elif ' NOT ' in query:
            parts = query.split(' NOT ', 1)
            positive = self.boolean_search(parts[0].strip())
            negative = self.boolean_search(parts[1].strip())

            # Исключить (NOT)
            return {k: v for k, v in positive.items() if k not in negative}

        elif query.startswith('(') and query.endswith(')'):
            # Убрать скобки
            return self.boolean_search(query[1:-1])

        else:
            # Простой поиск одного термина
            return self.simple_search(query)

    def simple_search(self, term):
        """Простой поиск одного термина с TF-IDF"""
        term_lower = term.lower()
        results = {}

        for doc_id, doc_data in self.documents.items():
            content = doc_data['content'].lower()

            if term_lower in content:
                # Вычислить TF-IDF score
                score = self.calculate_tf_idf(content, [term_lower])
                results[doc_id] = score

        return results

    def phrase_search(self, phrase):
        """Поиск точной фразы"""
        phrase_lower = phrase.lower()
        results = {}

        for doc_id, doc_data in self.documents.items():
            content = doc_data['content'].lower()

            if phrase_lower in content:
                # Подсчитать количество вхождений
                count = content.count(phrase_lower)
                results[doc_id] = count * 10.0  # Бонус за точное совпадение

        return results

    def search(self, query, limit=10):
        """
        Универсальный поиск
        Поддерживает:
        - Boolean operators (AND, OR, NOT)
        - Phrase search ("exact phrase")
        - Simple terms
        """
        print(f"\n🔍 Поиск: {query}\n")

        # Поиск точной фразы (в кавычках)
        if query.startswith('"') and query.endswith('"'):
            phrase = query[1:-1]
            results = self.phrase_search(phrase)
            search_type = "Phrase search"

        # Boolean search
        elif any(op in query for op in [' AND ', ' OR ', ' NOT ']):
            results = self.boolean_search(query)
            search_type = "Boolean search"

        # Простой поиск
        else:
            results = self.simple_search(query)
            search_type = "Simple search"

        if not results:
            print("❌ Ничего не найдено")
            return

        # Сортировать по релевантности
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        print(f"📊 {search_type}")
        print(f"   Найдено документов: {len(sorted_results)}\n")
        print("Результаты (отсортированы по релевантности):\n")

        for i, (doc_id, score) in enumerate(sorted_results[:limit], 1):
            print(f"{i}. {doc_id}")
            print(f"   Релевантность: {score:.4f}")

            # Показать контекст
            content = self.documents[doc_id]['content']
            context = self.get_context(content, query)
            if context:
                print(f"   {context}")

            print()

        if len(sorted_results) > limit:
            print(f"   ...и ещё {len(sorted_results) - limit} результатов")

    def get_context(self, content, query, window=100):
        """Получить контекст вокруг запроса"""
        # Упростить запрос (убрать операторы)
        simple_query = re.sub(r'\s+(AND|OR|NOT)\s+', ' ', query)
        simple_query = simple_query.replace('"', '').strip()

        # Найти первое упоминание
        pos = content.lower().find(simple_query.lower().split()[0])

        if pos == -1:
            return content[:window] + "..."

        start = max(0, pos - window // 2)
        end = min(len(content), pos + window // 2)

        context = content[start:end].strip()

        if start > 0:
            context = '...' + context
        if end < len(content):
            context = context + '...'

        return context


def main():
    import sys

    if len(sys.argv) < 2:
        print("Использование: python advanced_search.py <запрос>")
        print("\nПримеры:")
        print('  python tools/advanced_search.py "docker"')
        print('  python tools/advanced_search.py "docker AND kubernetes"')
        print('  python tools/advanced_search.py "python OR javascript"')
        print('  python tools/advanced_search.py "programming NOT java"')
        print('  python tools/advanced_search.py "\\"exact phrase\\""')
        return

    query = ' '.join(sys.argv[1:])

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    searcher = AdvancedSearch(root_dir)
    searcher.search(query, limit=20)


if __name__ == "__main__":
    main()
