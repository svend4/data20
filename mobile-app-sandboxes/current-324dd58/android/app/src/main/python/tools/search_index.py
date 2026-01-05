#!/usr/bin/env python3
"""
Advanced Search Index - Продвинутая поисковая система
Полнотекстовый поиск с BM25, fuzzy search, boolean queries

Возможности:
- BM25 scoring (лучше чем TF-IDF для поиска)
- Phrase search ("exact phrase" в кавычках)
- Proximity search (слова рядом друг с другом)
- Field boosting (title x3, headers x2, body x1)
- Fuzzy search (typo tolerance, Levenshtein distance)
- Boolean queries (AND, OR, NOT)
- Search suggestions ("did you mean?")
- Search analytics (популярные запросы, no-result queries)
- Incremental indexing
- Multiple export formats

Вдохновлено: Elasticsearch, Apache Lucene, Solr
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import math
import argparse
from datetime import datetime


class AdvancedSearchIndex:
    """Продвинутая поисковая система с BM25"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Инвертированный индекс: term -> {doc_id: {tf, positions}}
        self.index = defaultdict(lambda: defaultdict(lambda: {'tf': 0, 'positions': []}))

        # Документы: doc_id -> metadata
        self.documents = {}

        # Field-specific indexes (для field boosting)
        self.title_index = defaultdict(lambda: defaultdict(int))
        self.header_index = defaultdict(lambda: defaultdict(int))

        # IDF
        self.idf = {}

        # BM25 parameters
        self.k1 = 1.5  # term frequency saturation
        self.b = 0.75  # length normalization

        # Avg document length
        self.avg_doc_length = 0

        # Search analytics
        self.search_history = []
        self.no_result_queries = []

        # Stop words (frequent words to ignore)
        self.stop_words = {
            'и', 'в', 'на', 'с', 'к', 'по', 'для', 'из', 'что', 'это',
            'как', 'или', 'но', 'а', 'о', 'от', 'до', 'за', 'при', 'не',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'as', 'by', 'with', 'from', 'is', 'are', 'was', 'were',
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

    def tokenize(self, text, remove_stop_words=True):
        """Токенизация с опциональным удалением stop words"""
        # Удалить markdown
        text = re.sub(r'[#*`\[\]()]', ' ', text)

        # Извлечь слова (русский + английский)
        words = re.findall(r'\b[а-яёa-z]{2,}\b', text.lower())

        if remove_stop_words:
            words = [w for w in words if w not in self.stop_words]

        return words

    def extract_headers(self, content):
        """Извлечь все заголовки из markdown"""
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        return ' '.join(headers)

    def levenshtein_distance(self, s1, s2):
        """Расстояние Левенштейна для fuzzy search"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def build_index(self):
        """Построить полный индекс"""
        print("🔍 Построение продвинутого поискового индекса...\n")

        total_words = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            doc_id = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            tags = frontmatter.get('tags', []) if frontmatter else []

            # Извлечь заголовки
            headers = self.extract_headers(content)

            # Токенизация по полям (для field boosting)
            title_words = self.tokenize(title)
            header_words = self.tokenize(headers)
            body_words = self.tokenize(content)

            # Сохранить в field-specific indexes
            for word in title_words:
                self.title_index[word][doc_id] += 1

            for word in header_words:
                self.header_index[word][doc_id] += 1

            # Объединить все слова с позициями
            all_words = title_words + header_words + body_words

            # Построить индекс с позициями (для proximity search)
            for position, word in enumerate(all_words):
                self.index[word][doc_id]['tf'] += 1
                self.index[word][doc_id]['positions'].append(position)

            # Сохранить метаданные документа
            word_count = len(all_words)
            total_words += word_count

            self.documents[doc_id] = {
                'title': title,
                'tags': tags,
                'word_count': word_count,
                'title_words': len(title_words),
                'header_words': len(header_words),
            }

        # Вычислить avg document length
        if self.documents:
            self.avg_doc_length = total_words / len(self.documents)

        # Вычислить IDF
        total_docs = len(self.documents)
        for word, docs in self.index.items():
            df = len(docs)
            self.idf[word] = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)

        print(f"   Документов: {len(self.documents)}")
        print(f"   Уникальных слов: {len(self.index)}")
        print(f"   Avg doc length: {self.avg_doc_length:.1f}\n")

    def calculate_bm25_score(self, query_words, doc_id):
        """
        Вычислить BM25 score
        BM25 = sum(IDF(qi) * (tf(qi, D) * (k1 + 1)) / (tf(qi, D) + k1 * (1 - b + b * |D| / avgdl)))
        """
        score = 0.0
        doc_length = self.documents[doc_id]['word_count']

        for word in query_words:
            if word not in self.index or doc_id not in self.index[word]:
                continue

            tf = self.index[word][doc_id]['tf']
            idf = self.idf.get(word, 0)

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))

            score += idf * (numerator / denominator)

        return score

    def apply_field_boosting(self, query_words, doc_id, base_score):
        """
        Применить field boosting
        title: x3, headers: x2, body: x1
        """
        boost = 0.0

        for word in query_words:
            # Title boost (x3)
            if word in self.title_index and doc_id in self.title_index[word]:
                boost += self.title_index[word][doc_id] * 3.0

            # Header boost (x2)
            if word in self.header_index and doc_id in self.header_index[word]:
                boost += self.header_index[word][doc_id] * 2.0

        return base_score + boost * 0.1

    def phrase_search(self, phrase):
        """
        Поиск точной фразы
        Проверяет что слова идут подряд
        """
        words = self.tokenize(phrase, remove_stop_words=False)
        if not words:
            return []

        # Найти документы содержащие ВСЕ слова
        candidate_docs = set(self.index[words[0]].keys())
        for word in words[1:]:
            if word in self.index:
                candidate_docs &= set(self.index[word].keys())
            else:
                return []

        results = []

        for doc_id in candidate_docs:
            # Проверить что слова идут подряд
            positions = [self.index[word][doc_id]['positions'] for word in words]

            # Найти совпадения
            phrase_found = False
            for start_pos in positions[0]:
                match = True
                for i, word_positions in enumerate(positions[1:], 1):
                    if start_pos + i not in word_positions:
                        match = False
                        break
                if match:
                    phrase_found = True
                    break

            if phrase_found:
                results.append({
                    'path': doc_id,
                    'title': self.documents[doc_id]['title'],
                    'score': 100.0,  # Exact match
                })

        return results

    def proximity_search(self, word1, word2, max_distance=5):
        """
        Proximity search: найти документы где word1 и word2 близко друг к другу
        """
        if word1 not in self.index or word2 not in self.index:
            return []

        results = []
        candidate_docs = set(self.index[word1].keys()) & set(self.index[word2].keys())

        for doc_id in candidate_docs:
            positions1 = self.index[word1][doc_id]['positions']
            positions2 = self.index[word2][doc_id]['positions']

            # Найти минимальное расстояние
            min_dist = float('inf')
            for p1 in positions1:
                for p2 in positions2:
                    dist = abs(p1 - p2)
                    if dist < min_dist:
                        min_dist = dist

            if min_dist <= max_distance:
                # Score на основе proximity (ближе = лучше)
                proximity_score = 100 / min_dist if min_dist > 0 else 100
                results.append({
                    'path': doc_id,
                    'title': self.documents[doc_id]['title'],
                    'score': proximity_score,
                    'distance': min_dist,
                })

        results.sort(key=lambda x: -x['score'])
        return results

    def fuzzy_search(self, query_word, max_distance=2):
        """
        Fuzzy search с Levenshtein distance
        Находит похожие слова (для опечаток)
        """
        similar_words = []

        for indexed_word in self.index.keys():
            distance = self.levenshtein_distance(query_word, indexed_word)
            if distance <= max_distance:
                similar_words.append((indexed_word, distance))

        return sorted(similar_words, key=lambda x: x[1])

    def search_with_boolean(self, query):
        """
        Поиск с boolean операторами (AND, OR, NOT)
        Примеры:
        - "python AND programming"
        - "machine learning OR deep learning"
        - "python NOT java"
        """
        # Простой парсинг boolean запросов
        if ' AND ' in query:
            parts = query.split(' AND ')
            # Все части должны присутствовать
            results_sets = [set(r['path'] for r in self.search(part.strip())) for part in parts]
            common_docs = set.intersection(*results_sets) if results_sets else set()
            return [{'path': doc, 'title': self.documents[doc]['title'], 'score': 50.0}
                    for doc in common_docs]

        elif ' OR ' in query:
            parts = query.split(' OR ')
            # Хотя бы одна часть
            all_results = []
            for part in parts:
                all_results.extend(self.search(part.strip()))
            # Дедупликация
            seen = set()
            unique_results = []
            for r in all_results:
                if r['path'] not in seen:
                    seen.add(r['path'])
                    unique_results.append(r)
            return unique_results

        elif ' NOT ' in query:
            parts = query.split(' NOT ')
            if len(parts) == 2:
                include_results = self.search(parts[0].strip())
                exclude_docs = set(r['path'] for r in self.search(parts[1].strip()))
                return [r for r in include_results if r['path'] not in exclude_docs]

        # Fallback to regular search
        return self.search(query)

    def search(self, query, limit=10):
        """Основной поиск с BM25"""
        # Проверка на phrase search
        if query.startswith('"') and query.endswith('"'):
            phrase = query.strip('"')
            return self.phrase_search(phrase)[:limit]

        # Токенизация запроса
        query_words = self.tokenize(query)

        if not query_words:
            self.no_result_queries.append(query)
            return []

        # Вычислить BM25 scores
        scores = {}

        for doc_id in self.documents.keys():
            bm25_score = self.calculate_bm25_score(query_words, doc_id)
            if bm25_score > 0:
                # Применить field boosting
                final_score = self.apply_field_boosting(query_words, doc_id, bm25_score)
                scores[doc_id] = final_score

        # Сортировка
        results = [
            {
                'path': doc_id,
                'title': self.documents[doc_id]['title'],
                'score': score
            }
            for doc_id, score in scores.items()
        ]

        results.sort(key=lambda x: -x['score'])

        # Сохранить в analytics
        self.search_history.append({
            'query': query,
            'results_count': len(results),
            'timestamp': datetime.now().isoformat(),
        })

        if not results:
            self.no_result_queries.append(query)

        return results[:limit]

    def suggest_query(self, query):
        """
        Предложить исправленный запрос ("did you mean?")
        Использует fuzzy search для опечаток
        """
        query_words = self.tokenize(query)
        suggestions = []

        for word in query_words:
            if word in self.index:
                continue  # Слово найдено, исправление не нужно

            # Fuzzy search
            similar = self.fuzzy_search(word, max_distance=2)
            if similar:
                # Взять самое популярное похожее слово
                best_match = max(similar, key=lambda x: len(self.index[x[0]]))
                suggestions.append((word, best_match[0]))

        if suggestions:
            corrected = query
            for original, suggested in suggestions:
                corrected = corrected.replace(original, suggested)
            return corrected

        return None

    def get_search_analytics(self):
        """Получить аналитику поиска"""
        if not self.search_history:
            return {}

        # Популярные запросы
        all_queries = [h['query'] for h in self.search_history]
        popular_queries = Counter(all_queries).most_common(10)

        # No-result queries
        no_result_counts = Counter(self.no_result_queries).most_common(10)

        # Avg results per query
        avg_results = sum(h['results_count'] for h in self.search_history) / len(self.search_history)

        return {
            'total_searches': len(self.search_history),
            'popular_queries': popular_queries,
            'no_result_queries': no_result_counts,
            'avg_results_per_query': avg_results,
        }

    def export_to_json(self, output_file='search_index.json'):
        """Полный JSON экспорт"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': {
                'total_documents': len(self.documents),
                'unique_words': len(self.index),
                'avg_doc_length': self.avg_doc_length,
            },
            'documents': self.documents,
            'analytics': self.get_search_analytics(),
        }

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Индекс: {output_path}")

    def generate_analytics_report(self, output_file='SEARCH_ANALYTICS.md'):
        """Создать отчёт по аналитике поиска"""
        analytics = self.get_search_analytics()

        lines = []
        lines.append("# 🔍 Search Analytics\n\n")
        lines.append(f"> Создан {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        if analytics:
            lines.append("## 📊 Статистика\n\n")
            lines.append(f"- **Всего поисков**: {analytics['total_searches']}\n")
            lines.append(f"- **Avg результатов**: {analytics['avg_results_per_query']:.1f}\n\n")

            # Популярные запросы
            if analytics['popular_queries']:
                lines.append("## 🔥 Популярные запросы\n\n")
                for query, count in analytics['popular_queries']:
                    lines.append(f"- **{query}** ({count} раз)\n")
                lines.append("\n")

            # No-result queries
            if analytics['no_result_queries']:
                lines.append("## ❌ Запросы без результатов\n\n")
                for query, count in analytics['no_result_queries']:
                    lines.append(f"- **{query}** ({count} раз)\n")
                lines.append("\n")

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Analytics: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Продвинутая поисковая система с BM25'
    )
    parser.add_argument(
        '-q', '--query',
        help='Поисковый запрос (используйте "фраза" для точного поиска)'
    )
    parser.add_argument(
        '-n', '--limit',
        type=int,
        default=10,
        help='Количество результатов'
    )
    parser.add_argument(
        '--fuzzy',
        action='store_true',
        help='Включить fuzzy search'
    )
    parser.add_argument(
        '--analytics',
        action='store_true',
        help='Показать search analytics'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    index = AdvancedSearchIndex(root_dir)
    index.build_index()
    index.export_to_json()

    if args.query:
        print(f"\n🔍 Поиск: '{args.query}'\n")

        # Boolean search
        results = index.search_with_boolean(args.query) if ' AND ' in args.query or ' OR ' in args.query or ' NOT ' in args.query else index.search(args.query, limit=args.limit)

        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} (score: {result['score']:.2f})")
                print(f"   {result['path']}\n")
        else:
            print("❌ Ничего не найдено")

            # Suggest correction
            suggestion = index.suggest_query(args.query)
            if suggestion:
                print(f"\n💡 Возможно, вы имели в виду: '{suggestion}'")

    if args.analytics:
        index.generate_analytics_report()

    print()


if __name__ == "__main__":
    main()
