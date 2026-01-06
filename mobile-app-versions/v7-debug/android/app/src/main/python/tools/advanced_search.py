#!/usr/bin/env python3
"""
Advanced Search Engine - Расширенный поиск с ранжированием
Комбинирует:
- Boolean operators (AND, OR, NOT)
- TF-IDF ranking
- BM25 ranking algorithm
- Fuzzy matching (Levenshtein distance)
- Phrase search
- Faceted search (filters)
- Query expansion (synonyms)
- Result highlighting
- Multiple export formats

Features:
- Advanced ranking algorithms (TF-IDF, BM25)
- Fuzzy search with edit distance
- Faceted filtering (category, tags, date)
- Search history and suggestions
- Result highlighting
- Export to JSON/HTML
"""

import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import math
import json
import argparse
from datetime import datetime


class LevenshteinDistance:
    """Levenshtein distance для fuzzy matching"""

    @staticmethod
    def calculate(s1: str, s2: str) -> int:
        """
        Вычислить Levenshtein distance (edit distance)
        Количество операций (вставка, удаление, замена) для превращения s1 в s2
        """
        if len(s1) < len(s2):
            return LevenshteinDistance.calculate(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Стоимость операций
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def similarity(s1: str, s2: str) -> float:
        """
        Similarity score (0-1)
        1.0 = exact match, 0.0 = completely different
        """
        distance = LevenshteinDistance.calculate(s1, s2)
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0


class BM25Ranker:
    """BM25 ranking algorithm (better than TF-IDF for search)"""

    def __init__(self, k1=1.5, b=0.75):
        """
        BM25 parameters:
        - k1: term frequency saturation parameter (default: 1.5)
        - b: length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b

    def score(self, query_terms: List[str], doc_words: List[str], doc_freq: Dict[str, int],
              avg_doc_length: float, num_docs: int) -> float:
        """
        BM25 score calculation:
        BM25(q,d) = Σ IDF(qi) × (f(qi,d) × (k1+1)) / (f(qi,d) + k1×(1-b+b×|d|/avgdl))

        где:
        - qi = query term
        - f(qi,d) = term frequency in document
        - |d| = document length
        - avgdl = average document length
        """
        score = 0.0
        doc_length = len(doc_words)

        for term in query_terms:
            if term not in doc_words:
                continue

            # Term frequency in document
            tf = doc_words.count(term)

            # Document frequency (how many docs contain this term)
            df = doc_freq.get(term, 1)

            # IDF: log((N - df + 0.5) / (df + 0.5))
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)

            # BM25 term score
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / avg_doc_length))

            score += idf * (numerator / denominator)

        return score


class AdvancedSearch:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.documents = {}
        self.metadata = {}
        self.idf = {}
        self.doc_freq = defaultdict(int)
        self.avg_doc_length = 0
        self.bm25 = BM25Ranker()
        self.search_history = []

        self.load_documents()
        self.calculate_idf()

    def load_documents(self):
        """Загрузить все документы с метаданными"""
        print("📚 Загрузка документов...")

        total_length = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    full_content = f.read()

                # Extract frontmatter
                frontmatter = {}
                content = full_content

                if full_content.startswith('---'):
                    parts = full_content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter_text = parts[1]
                        content = parts[2]

                        # Parse YAML-like frontmatter (simple)
                        for line in frontmatter_text.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                frontmatter[key.strip()] = value.strip().strip("'\"")

                file_key = str(md_file.relative_to(self.root_dir))
                words = self.tokenize(content)

                self.documents[file_key] = {
                    'content': content,
                    'words': words,
                    'path': md_file
                }

                self.metadata[file_key] = frontmatter
                total_length += len(words)

                # Update document frequency
                for word in set(words):
                    self.doc_freq[word] += 1

            except Exception as e:
                pass

        self.avg_doc_length = total_length / len(self.documents) if self.documents else 0
        print(f"   Загружено документов: {len(self.documents)}")
        print(f"   Средняя длина: {self.avg_doc_length:.0f} слов")

    def tokenize(self, text):
        """Разбить текст на токены"""
        # Извлечь слова (кириллица и латиница, минимум 2 символа)
        words = re.findall(r'\b[а-яёa-z]{2,}\b', text.lower())
        return words

    def calculate_idf(self):
        """Вычислить IDF (Inverse Document Frequency) для всех терминов"""
        print("🔢 Вычисление IDF...")

        # IDF уже учтён в doc_freq, просто вычислим значения
        num_docs = len(self.documents)
        for word, doc_freq in self.doc_freq.items():
            self.idf[word] = math.log(num_docs / doc_freq)

    def calculate_tf_idf(self, doc_words, query_terms):
        """Вычислить TF-IDF score для документа"""
        if not doc_words:
            return 0.0

        # Подсчитать TF (Term Frequency)
        tf = Counter(doc_words)
        doc_length = len(doc_words)

        # Вычислить TF-IDF score
        score = 0.0
        for term in query_terms:
            if term in tf:
                # TF * IDF
                term_tf = tf[term] / doc_length
                term_idf = self.idf.get(term, 0)
                score += term_tf * term_idf

        return score

    def fuzzy_search(self, term: str, max_distance: int = 2) -> Dict[str, float]:
        """
        Fuzzy search с Levenshtein distance
        Находит термины, похожие на запрос (опечатки, вариации)
        """
        results = {}

        for doc_id, doc_data in self.documents.items():
            # Найти похожие слова в документе
            matched_words = set()

            for word in doc_data['words']:
                if len(word) < 3:  # Skip short words
                    continue

                distance = LevenshteinDistance.calculate(term.lower(), word)
                if distance <= max_distance:
                    matched_words.add(word)

            if matched_words:
                # Score based on similarity
                best_similarity = max(LevenshteinDistance.similarity(term.lower(), w) for w in matched_words)
                results[doc_id] = best_similarity

        return results

    def faceted_search(self, query: str, filters: Dict[str, str]) -> Dict[str, float]:
        """
        Faceted search с фильтрами
        filters: {'category': 'computers', 'tags': 'python', 'date': '2026'}
        """
        # Сначала выполним обычный поиск
        base_results = self.simple_search(query)

        # Применим фильтры
        filtered_results = {}

        for doc_id, score in base_results.items():
            metadata = self.metadata.get(doc_id, {})

            # Check each filter
            match = True

            if 'category' in filters:
                if metadata.get('category', '') != filters['category']:
                    match = False

            if 'tags' in filters and match:
                doc_tags = metadata.get('tags', '')
                if filters['tags'] not in doc_tags:
                    match = False

            if 'date' in filters and match:
                doc_date = metadata.get('date', '')
                if filters['date'] not in doc_date:
                    match = False

            if match:
                filtered_results[doc_id] = score

        return filtered_results

    def boolean_search(self, query):
        """
        Boolean поиск с операторами AND, OR, NOT
        Примеры:
        - "docker AND kubernetes"
        - "python OR javascript"
        - "programming NOT java"
        """
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

    def simple_search(self, term, algorithm='bm25'):
        """Простой поиск одного термина"""
        term_lower = term.lower()
        results = {}

        query_terms = self.tokenize(term_lower)

        for doc_id, doc_data in self.documents.items():
            doc_words = doc_data['words']

            # Check if term is in document
            if any(qt in doc_words for qt in query_terms):
                if algorithm == 'bm25':
                    score = self.bm25.score(
                        query_terms, doc_words, self.doc_freq,
                        self.avg_doc_length, len(self.documents)
                    )
                else:  # tf-idf
                    score = self.calculate_tf_idf(doc_words, query_terms)

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

    def search(self, query, limit=10, algorithm='bm25', fuzzy=False, filters=None):
        """
        Универсальный поиск

        Args:
            query: search query
            limit: max results
            algorithm: 'bm25' or 'tfidf'
            fuzzy: enable fuzzy matching
            filters: dict of faceted filters
        """
        print(f"\n🔍 Поиск: {query}")
        print(f"   Алгоритм: {algorithm.upper()}")
        if fuzzy:
            print(f"   Fuzzy matching: включён")
        if filters:
            print(f"   Фильтры: {filters}")
        print()

        # Add to history
        self.search_history.append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'algorithm': algorithm
        })

        # Поиск точной фразы (в кавычках)
        if query.startswith('"') and query.endswith('"'):
            phrase = query[1:-1]
            results = self.phrase_search(phrase)
            search_type = "Phrase search"

        # Faceted search
        elif filters:
            results = self.faceted_search(query, filters)
            search_type = "Faceted search"

        # Fuzzy search
        elif fuzzy:
            term = query.split()[0]  # First term
            results = self.fuzzy_search(term, max_distance=2)
            search_type = "Fuzzy search"

        # Boolean search
        elif any(op in query for op in [' AND ', ' OR ', ' NOT ']):
            results = self.boolean_search(query)
            search_type = "Boolean search"

        # Простой поиск
        else:
            results = self.simple_search(query, algorithm=algorithm)
            search_type = f"Simple search ({algorithm})"

        if not results:
            print("❌ Ничего не найдено")
            return []

        # Сортировать по релевантности
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        print(f"📊 {search_type}")
        print(f"   Найдено документов: {len(sorted_results)}\n")
        print("Результаты (отсортированы по релевантности):\n")

        for i, (doc_id, score) in enumerate(sorted_results[:limit], 1):
            print(f"{i}. {doc_id}")
            print(f"   Релевантность: {score:.4f}")

            # Metadata
            metadata = self.metadata.get(doc_id, {})
            if 'title' in metadata:
                print(f"   Название: {metadata['title']}")
            if 'category' in metadata:
                print(f"   Категория: {metadata['category']}")

            # Показать контекст с подсветкой
            content = self.documents[doc_id]['content']
            context = self.get_context_highlighted(content, query)
            if context:
                print(f"   {context}")

            print()

        if len(sorted_results) > limit:
            print(f"   ...и ещё {len(sorted_results) - limit} результатов")

        return sorted_results[:limit]

    def get_context_highlighted(self, content, query, window=100):
        """Получить контекст с подсветкой найденных терминов"""
        # Упростить запрос
        simple_query = re.sub(r'\s+(AND|OR|NOT)\s+', ' ', query)
        simple_query = simple_query.replace('"', '').strip()

        query_terms = simple_query.split()
        if not query_terms:
            return content[:window] + "..."

        # Найти первое упоминание любого термина
        first_pos = len(content)
        for term in query_terms:
            pos = content.lower().find(term.lower())
            if pos != -1 and pos < first_pos:
                first_pos = pos

        if first_pos == len(content):
            return content[:window] + "..."

        start = max(0, first_pos - window // 2)
        end = min(len(content), first_pos + window // 2)

        context = content[start:end].strip()

        # Highlight terms with **term**
        for term in query_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            context = pattern.sub(f"**{term.upper()}**", context)

        if start > 0:
            context = '...' + context
        if end < len(content):
            context = context + '...'

        return context

    def export_results(self, results: List[Tuple[str, float]], format='json'):
        """Export search results"""
        if format == 'json':
            data = []
            for doc_id, score in results:
                data.append({
                    'document': doc_id,
                    'score': score,
                    'metadata': self.metadata.get(doc_id, {})
                })

            output_file = self.root_dir / "search_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ Results exported to: {output_file}")

        elif format == 'html':
            html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Search Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        .result {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
        .title {{ font-size: 18px; font-weight: bold; color: #007bff; }}
        .score {{ color: #666; font-size: 14px; }}
        .metadata {{ color: #888; font-size: 13px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Search Results</h1>
        {results_html}
    </div>
</body>
</html>"""

            results_html = []
            for i, (doc_id, score) in enumerate(results, 1):
                metadata = self.metadata.get(doc_id, {})
                title = metadata.get('title', doc_id)

                results_html.append(f'''
                <div class="result">
                    <div class="title">{i}. {title}</div>
                    <div class="score">Score: {score:.4f}</div>
                    <div class="metadata">Path: {doc_id}</div>
                    <div class="metadata">Category: {metadata.get('category', 'N/A')}</div>
                </div>
                ''')

            html = html_template.format(results_html=''.join(results_html))

            output_file = self.root_dir / "search_results.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"✅ Results exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Search Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  advanced_search.py "python"                          # Simple search
  advanced_search.py "docker AND kubernetes"           # Boolean AND
  advanced_search.py "python OR javascript"            # Boolean OR
  advanced_search.py "programming NOT java"            # Boolean NOT
  advanced_search.py '"exact phrase"'                  # Phrase search
  advanced_search.py "pythn" --fuzzy                   # Fuzzy search (typos)
  advanced_search.py "python" --algorithm tfidf        # Use TF-IDF
  advanced_search.py "python" --category computers     # Faceted search
  advanced_search.py "python" --export json            # Export results
        """
    )

    parser.add_argument('query', nargs='+', help='Search query')
    parser.add_argument('-l', '--limit', type=int, default=10, help='Max results (default: 10)')
    parser.add_argument('-a', '--algorithm', choices=['bm25', 'tfidf'], default='bm25',
                        help='Ranking algorithm (default: bm25)')
    parser.add_argument('-f', '--fuzzy', action='store_true', help='Enable fuzzy matching')
    parser.add_argument('--category', type=str, help='Filter by category')
    parser.add_argument('--tags', type=str, help='Filter by tags')
    parser.add_argument('--date', type=str, help='Filter by date')
    parser.add_argument('-e', '--export', choices=['json', 'html'], help='Export results')

    args = parser.parse_args()

    query = ' '.join(args.query)

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    searcher = AdvancedSearch(root_dir)

    # Build filters
    filters = {}
    if args.category:
        filters['category'] = args.category
    if args.tags:
        filters['tags'] = args.tags
    if args.date:
        filters['date'] = args.date

    results = searcher.search(
        query,
        limit=args.limit,
        algorithm=args.algorithm,
        fuzzy=args.fuzzy,
        filters=filters if filters else None
    )

    if args.export and results:
        searcher.export_results(results, format=args.export)


if __name__ == "__main__":
    main()
