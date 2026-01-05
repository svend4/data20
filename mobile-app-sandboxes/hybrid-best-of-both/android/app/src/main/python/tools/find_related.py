#!/usr/bin/env python3
"""
Advanced Related Articles Finder - Продвинутый поиск связанных статей
Функции:
- TF-IDF similarity (текстовая похожесть)
- Cosine similarity (векторное сравнение документов)
- Jaccard similarity (множественное пересечение)
- Content-based filtering (на основе содержимого)
- Hybrid recommendation (комбинация алгоритмов)
- Similarity graph (визуализация связей)
- Auto-linking suggestions (автоматические предложения ссылок)
- Multiple similarity metrics (множественные метрики)
- Related articles network (граф похожести)
- Export formats (JSON, Markdown, Graph)
- Caching for performance (кэширование)
- Weighted scoring (взвешенное ранжирование)

Вдохновлено: Netflix recommendations, Medium related articles, Wikipedia "See also",
              collaborative filtering, content-based recommender systems
"""

import os
import re
from pathlib import Path
import yaml
import sys
import json
import math
from collections import defaultdict, Counter


class AdvancedRelatedFinder:
    """Продвинутый поиск связанных статей"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Кэш документов
        self.documents = {}  # path -> {frontmatter, content, tokens}
        self.document_frequency = Counter()  # Для IDF
        self.total_documents = 0

        # Кэш вычислений
        self.tfidf_cache = {}
        self.similarity_cache = {}

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

    def tokenize(self, text):
        """Токенизация текста"""
        # Удалить markdown форматирование
        text = re.sub(r'!?\[([^\]]*)\]\([^)]+\)', r'\1', text)  # Ссылки и изображения
        text = re.sub(r'[#*`_]', '', text)  # Форматирование
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Код-блоки

        # Токенизировать (слова 3+ символов)
        tokens = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())

        # Стоп-слова (упрощённый список)
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one',
            'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
            'это', 'как', 'для', 'что', 'при', 'или', 'его', 'еще', 'так', 'уже', 'где', 'там',
            'был', 'была', 'было', 'были', 'есть', 'чем', 'все', 'этот', 'эта', 'эти', 'более'
        }

        return [t for t in tokens if t not in stop_words]

    def load_documents(self):
        """Загрузить все документы в память"""
        print("📚 Загрузка документов...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Токенизировать
            tokens = self.tokenize(content)

            # Сохранить
            self.documents[article_path] = {
                'frontmatter': frontmatter or {},
                'content': content,
                'tokens': tokens,
                'token_set': set(tokens)
            }

            # Обновить document frequency
            for token in set(tokens):
                self.document_frequency[token] += 1

        self.total_documents = len(self.documents)
        print(f"   Загружено документов: {self.total_documents}")
        print(f"   Уникальных слов: {len(self.document_frequency)}\n")

    def calculate_tfidf(self, tokens):
        """Вычислить TF-IDF вектор для документа"""
        if not tokens:
            return {}

        # Term Frequency
        tf = Counter(tokens)
        total_terms = len(tokens)

        # TF-IDF
        tfidf = {}
        for term, count in tf.items():
            term_freq = count / total_terms
            doc_freq = self.document_frequency.get(term, 1)
            idf = math.log(self.total_documents / doc_freq) if doc_freq > 0 else 0
            tfidf[term] = term_freq * idf

        return tfidf

    def cosine_similarity(self, vec1, vec2):
        """Вычислить косинусное сходство между двумя TF-IDF векторами"""
        # Найти общие термины
        common_terms = set(vec1.keys()) & set(vec2.keys())

        if not common_terms:
            return 0.0

        # Скалярное произведение
        dot_product = sum(vec1[term] * vec2[term] for term in common_terms)

        # Нормы векторов
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def jaccard_similarity(self, set1, set2):
        """Вычислить сходство Жаккара"""
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def tag_similarity(self, tags1, tags2):
        """Сходство по тегам"""
        if not tags1 or not tags2:
            return 0.0

        set1 = set(tags1)
        set2 = set(tags2)

        return self.jaccard_similarity(set1, set2)

    def category_similarity(self, cat1, cat2, subcat1=None, subcat2=None):
        """Сходство по категориям"""
        score = 0.0

        if cat1 == cat2:
            score += 1.0

        if subcat1 and subcat2 and subcat1 == subcat2:
            score += 0.5

        return score

    def find_related(self, target_file, num_results=10, algorithm='hybrid'):
        """Найти связанные статьи для данного файла"""
        target_path = str(Path(target_file).relative_to(self.root_dir)) if not target_file.startswith('knowledge') else target_file

        if target_path not in self.documents:
            print(f"❌ Файл не найден: {target_file}")
            return []

        target_doc = self.documents[target_path]
        target_fm = target_doc['frontmatter']

        print(f"\n📄 Целевая статья: {target_fm.get('title', target_file)}")
        print(f"🏷️  Теги: {', '.join(target_fm.get('tags', []))}")
        print(f"📂 Категория: {target_fm.get('category')} / {target_fm.get('subcategory')}")
        print(f"📊 Алгоритм: {algorithm}\n")

        # Вычислить TF-IDF для целевого документа
        if target_path not in self.tfidf_cache:
            self.tfidf_cache[target_path] = self.calculate_tfidf(target_doc['tokens'])

        target_tfidf = self.tfidf_cache[target_path]
        target_tags = set(target_fm.get('tags', []))
        target_category = target_fm.get('category')
        target_subcategory = target_fm.get('subcategory')

        # Вычислить сходство со всеми документами
        candidates = []

        for article_path, doc in self.documents.items():
            # Пропустить саму целевую статью
            if article_path == target_path:
                continue

            fm = doc['frontmatter']

            # Кэш ключ
            cache_key = f"{target_path}:{article_path}:{algorithm}"

            if cache_key in self.similarity_cache:
                similarity = self.similarity_cache[cache_key]
            else:
                # Вычислить сходство
                similarity = self.calculate_similarity(
                    target_doc, doc, target_tfidf,
                    algorithm=algorithm
                )
                self.similarity_cache[cache_key] = similarity

            if similarity > 0:
                candidates.append({
                    'file': article_path,
                    'title': fm.get('title', article_path),
                    'similarity': similarity,
                    'tags': fm.get('tags', []),
                    'category': fm.get('category')
                })

        # Сортировать по сходству
        candidates.sort(key=lambda x: -x['similarity'])

        # Вывести результаты
        print(f"🔗 Найдено {len(candidates)} связанных статей\n")
        print("Топ связанных статей:")
        print("=" * 80)

        for i, article in enumerate(candidates[:num_results], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Файл: {article['file']}")
            print(f"   Сходство: {article['similarity']:.4f}")
            print(f"   Категория: {article['category']}")
            print(f"   Теги: {', '.join(article['tags'][:5])}")

        # Предложить добавить ссылки
        print("\n" + "=" * 80)
        print("\n💡 Предложение: добавить в секцию 'См. также':\n")

        for article in candidates[:num_results]:
            filename = Path(article['file']).name
            print(f"- [[{filename}]] - {article['title']}")

        return candidates[:num_results]

    def calculate_similarity(self, doc1, doc2, tfidf1, algorithm='hybrid'):
        """Вычислить сходство между двумя документами"""
        if algorithm == 'tfidf':
            return self.calculate_tfidf_similarity(doc1, doc2, tfidf1)
        elif algorithm == 'jaccard':
            return self.calculate_jaccard_similarity(doc1, doc2)
        elif algorithm == 'tags':
            return self.calculate_tags_similarity(doc1, doc2)
        elif algorithm == 'hybrid':
            return self.calculate_hybrid_similarity(doc1, doc2, tfidf1)
        else:
            return 0.0

    def calculate_tfidf_similarity(self, doc1, doc2, tfidf1):
        """TF-IDF косинусное сходство"""
        # Вычислить TF-IDF для второго документа (с кэшированием)
        doc2_path = None
        for path, d in self.documents.items():
            if d == doc2:
                doc2_path = path
                break

        if doc2_path and doc2_path in self.tfidf_cache:
            tfidf2 = self.tfidf_cache[doc2_path]
        else:
            tfidf2 = self.calculate_tfidf(doc2['tokens'])
            if doc2_path:
                self.tfidf_cache[doc2_path] = tfidf2

        return self.cosine_similarity(tfidf1, tfidf2)

    def calculate_jaccard_similarity(self, doc1, doc2):
        """Жаккар на множествах токенов"""
        return self.jaccard_similarity(doc1['token_set'], doc2['token_set'])

    def calculate_tags_similarity(self, doc1, doc2):
        """Сходство по тегам"""
        tags1 = set(doc1['frontmatter'].get('tags', []))
        tags2 = set(doc2['frontmatter'].get('tags', []))

        return self.jaccard_similarity(tags1, tags2)

    def calculate_hybrid_similarity(self, doc1, doc2, tfidf1):
        """Гибридное сходство (комбинация алгоритмов)"""
        # TF-IDF сходство (40%)
        tfidf_sim = self.calculate_tfidf_similarity(doc1, doc2, tfidf1)

        # Jaccard на токенах (20%)
        jaccard_sim = self.calculate_jaccard_similarity(doc1, doc2)

        # Сходство по тегам (30%)
        tags_sim = self.calculate_tags_similarity(doc1, doc2)

        # Сходство по категориям (10%)
        fm1 = doc1['frontmatter']
        fm2 = doc2['frontmatter']
        cat_sim = self.category_similarity(
            fm1.get('category'), fm2.get('category'),
            fm1.get('subcategory'), fm2.get('subcategory')
        )
        cat_sim = min(cat_sim, 1.0)  # Normalize

        # Взвешенная комбинация
        hybrid = (
            tfidf_sim * 0.40 +
            jaccard_sim * 0.20 +
            tags_sim * 0.30 +
            cat_sim * 0.10
        )

        return hybrid

    def build_similarity_graph(self, threshold=0.2, max_articles=50):
        """Построить граф похожести (для визуализации)"""
        print(f"🕸️  Построение графа похожести (threshold={threshold})...")

        edges = []

        # Ограничить количество статей для производительности
        articles = list(self.documents.keys())[:max_articles]

        for i, article1 in enumerate(articles):
            doc1 = self.documents[article1]

            if article1 not in self.tfidf_cache:
                self.tfidf_cache[article1] = self.calculate_tfidf(doc1['tokens'])

            tfidf1 = self.tfidf_cache[article1]

            for article2 in articles[i+1:]:
                doc2 = self.documents[article2]

                # Вычислить сходство
                similarity = self.calculate_similarity(doc1, doc2, tfidf1, algorithm='hybrid')

                if similarity >= threshold:
                    edges.append({
                        'source': article1,
                        'target': article2,
                        'weight': similarity
                    })

        print(f"   Узлов: {len(articles)}")
        print(f"   Рёбер: {len(edges)}\n")

        return {
            'nodes': [
                {
                    'id': article,
                    'label': self.documents[article]['frontmatter'].get('title', article),
                    'category': self.documents[article]['frontmatter'].get('category')
                }
                for article in articles
            ],
            'edges': edges
        }

    def generate_auto_linking_suggestions(self, min_similarity=0.3):
        """Создать автоматические предложения ссылок для всех статей"""
        print(f"🔗 Генерация предложений ссылок (min_similarity={min_similarity})...")

        suggestions = {}

        for article_path in self.documents.keys():
            # Найти связанные (без вывода)
            doc = self.documents[article_path]
            fm = doc['frontmatter']

            if article_path not in self.tfidf_cache:
                self.tfidf_cache[article_path] = self.calculate_tfidf(doc['tokens'])

            tfidf = self.tfidf_cache[article_path]

            related = []

            for other_path, other_doc in self.documents.items():
                if other_path == article_path:
                    continue

                similarity = self.calculate_similarity(doc, other_doc, tfidf, algorithm='hybrid')

                if similarity >= min_similarity:
                    related.append({
                        'file': other_path,
                        'title': other_doc['frontmatter'].get('title', other_path),
                        'similarity': similarity
                    })

            # Сортировать
            related.sort(key=lambda x: -x['similarity'])

            suggestions[article_path] = {
                'title': fm.get('title', article_path),
                'suggestions': related[:5]  # Топ-5
            }

        print(f"   Обработано статей: {len(suggestions)}\n")

        return suggestions

    def export_suggestions_markdown(self, suggestions):
        """Экспорт предложений в Markdown"""
        lines = []
        lines.append("# 🔗 Автоматические предложения ссылок\n\n")
        lines.append(f"> Всего статей: {len(suggestions)}\n\n")

        for article_path, data in sorted(suggestions.items()):
            if not data['suggestions']:
                continue

            lines.append(f"## {data['title']}\n\n")
            lines.append(f"**Файл**: `{article_path}`\n\n")
            lines.append("**Предлагаемые ссылки:**\n\n")

            for suggestion in data['suggestions']:
                filename = Path(suggestion['file']).name
                lines.append(f"- [[{filename}]] - {suggestion['title']} (сходство: {suggestion['similarity']:.3f})\n")

            lines.append("\n---\n\n")

        output_file = self.root_dir / "AUTO_LINKING_SUGGESTIONS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Предложения: {output_file}")

    def export_graph_json(self, graph):
        """Экспорт графа в JSON"""
        output_file = self.root_dir / "similarity_graph.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        print(f"✅ Граф: {output_file}")

    def export_related_json(self, related_articles, target_file):
        """Экспорт связанных статей в JSON"""
        data = {
            'target': target_file,
            'related': related_articles
        }

        output_file = self.root_dir / "related_articles.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")

    def generate_statistics(self):
        """Создать статистику по сходству"""
        print("📊 Статистика сходства документов...")

        # Выборочный анализ (первые 20 документов)
        sample = list(self.documents.keys())[:20]

        similarities = []

        for i, doc1_path in enumerate(sample):
            doc1 = self.documents[doc1_path]

            if doc1_path not in self.tfidf_cache:
                self.tfidf_cache[doc1_path] = self.calculate_tfidf(doc1['tokens'])

            tfidf1 = self.tfidf_cache[doc1_path]

            for doc2_path in sample[i+1:]:
                doc2 = self.documents[doc2_path]

                sim = self.calculate_similarity(doc1, doc2, tfidf1, algorithm='hybrid')
                similarities.append(sim)

        if similarities:
            avg_sim = sum(similarities) / len(similarities)
            max_sim = max(similarities)
            min_sim = min(similarities)

            print(f"   Пар проанализировано: {len(similarities)}")
            print(f"   Среднее сходство: {avg_sim:.4f}")
            print(f"   Максимальное: {max_sim:.4f}")
            print(f"   Минимальное: {min_sim:.4f}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Related Articles Finder')
    parser.add_argument('target_file', nargs='?', help='Целевая статья')
    parser.add_argument('-n', '--num', type=int, default=10,
                       help='Количество результатов (по умолчанию: 10)')
    parser.add_argument('-a', '--algorithm', choices=['tfidf', 'jaccard', 'tags', 'hybrid'],
                       default='hybrid', help='Алгоритм сходства (по умолчанию: hybrid)')
    parser.add_argument('--graph', action='store_true',
                       help='Построить граф похожести')
    parser.add_argument('--auto-link', action='store_true',
                       help='Создать автоматические предложения ссылок для всех статей')
    parser.add_argument('--stats', action='store_true',
                       help='Показать статистику')
    parser.add_argument('--json', action='store_true',
                       help='Экспорт в JSON')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    finder = AdvancedRelatedFinder(root_dir)
    finder.load_documents()

    if args.stats:
        finder.generate_statistics()

    if args.graph:
        graph = finder.build_similarity_graph(threshold=0.2, max_articles=30)
        finder.export_graph_json(graph)

    if args.auto_link:
        suggestions = finder.generate_auto_linking_suggestions(min_similarity=0.25)
        finder.export_suggestions_markdown(suggestions)

    if args.target_file:
        related = finder.find_related(
            args.target_file,
            num_results=args.num,
            algorithm=args.algorithm
        )

        if args.json:
            finder.export_related_json(related, args.target_file)


if __name__ == "__main__":
    main()
