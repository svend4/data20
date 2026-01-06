#!/usr/bin/env python3
"""
Duplicate Detector - Детектор дубликатов
Находит дублирующийся и очень похожий контент

Вдохновлено: Google duplicate content detection, Copyscape
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import hashlib
import json
import argparse
import math
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Set


class DuplicateDetector:
    """Детектор дубликатов"""

    def __init__(self, root_dir=".", similarity_threshold=0.8):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.similarity_threshold = similarity_threshold

        # Данные статей
        self.articles = {}

        # Результаты
        self.duplicates = {
            'exact': [],
            'near_duplicate': [],
            'similar_titles': []
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

    def normalize_text(self, text):
        """Нормализовать текст для сравнения"""
        # Удалить лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        # Удалить markdown синтаксис
        text = re.sub(r'[#*`\[\]()]', '', text)
        # Lowercase
        text = text.lower().strip()
        return text

    def calculate_hash(self, text):
        """Вычислить MD5 хеш текста"""
        normalized = self.normalize_text(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def calculate_similarity(self, text1, text2):
        """Вычислить сходство текстов (Jaccard similarity)"""
        # Токенизация
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def levenshtein_distance(self, s1, s2):
        """Вычислить расстояние Левенштейна"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # Стоимость вставки, удаления или замены
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]

    def title_similarity(self, title1, title2):
        """Вычислить сходство заголовков"""
        # Нормализация
        t1 = self.normalize_text(title1)
        t2 = self.normalize_text(title2)

        if t1 == t2:
            return 1.0

        # Расстояние Левенштейна
        max_len = max(len(t1), len(t2))
        if max_len == 0:
            return 0.0

        distance = self.levenshtein_distance(t1, t2)
        similarity = 1.0 - (distance / max_len)

        return similarity

    def collect_articles(self):
        """Собрать все статьи"""
        print("📚 Сбор статей...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            self.articles[article_path] = {
                'title': title,
                'content': content,
                'hash': self.calculate_hash(content),
                'word_count': len(re.findall(r'\b\w+\b', content))
            }

        print(f"   Статей собрано: {len(self.articles)}\n")

    def find_exact_duplicates(self):
        """Найти точные дубликаты (по хешу)"""
        print("🔍 Поиск точных дубликатов...\n")

        # Группировка по хешу
        by_hash = defaultdict(list)

        for article_path, data in self.articles.items():
            by_hash[data['hash']].append(article_path)

        # Найти группы с более чем одной статьёй
        for hash_value, articles in by_hash.items():
            if len(articles) > 1:
                self.duplicates['exact'].append({
                    'type': 'exact',
                    'articles': [
                        {
                            'path': article,
                            'title': self.articles[article]['title']
                        }
                        for article in articles
                    ],
                    'similarity': 1.0
                })

        print(f"   Найдено групп точных дубликатов: {len(self.duplicates['exact'])}\n")

    def find_near_duplicates(self):
        """Найти почти дубликаты (высокое сходство контента)"""
        print("🔎 Поиск похожего контента...\n")

        articles_list = list(self.articles.items())

        for i, (path1, data1) in enumerate(articles_list):
            for path2, data2 in articles_list[i + 1:]:
                # Вычислить сходство
                similarity = self.calculate_similarity(data1['content'], data2['content'])

                if similarity >= self.similarity_threshold:
                    self.duplicates['near_duplicate'].append({
                        'type': 'near_duplicate',
                        'articles': [
                            {'path': path1, 'title': data1['title']},
                            {'path': path2, 'title': data2['title']}
                        ],
                        'similarity': similarity
                    })

        print(f"   Найдено пар похожих статей: {len(self.duplicates['near_duplicate'])}\n")

    def find_similar_titles(self):
        """Найти статьи с похожими заголовками"""
        print("📝 Поиск похожих заголовков...\n")

        articles_list = list(self.articles.items())

        for i, (path1, data1) in enumerate(articles_list):
            for path2, data2 in articles_list[i + 1:]:
                # Вычислить сходство заголовков
                similarity = self.title_similarity(data1['title'], data2['title'])

                if similarity >= 0.7:  # Более низкий порог для заголовков
                    self.duplicates['similar_titles'].append({
                        'type': 'similar_title',
                        'articles': [
                            {'path': path1, 'title': data1['title']},
                            {'path': path2, 'title': data2['title']}
                        ],
                        'similarity': similarity
                    })

        print(f"   Найдено пар с похожими заголовками: {len(self.duplicates['similar_titles'])}\n")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔍 Отчёт: Детектор дубликатов\n\n")
        lines.append("> Поиск дублирующегося и похожего контента\n\n")

        # Статистика
        total_issues = (
            len(self.duplicates['exact']) +
            len(self.duplicates['near_duplicate']) +
            len(self.duplicates['similar_titles'])
        )

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей проверено**: {len(self.articles)}\n")
        lines.append(f"- **Точных дубликатов**: {len(self.duplicates['exact'])}\n")
        lines.append(f"- **Похожих статей**: {len(self.duplicates['near_duplicate'])}\n")
        lines.append(f"- **Похожих заголовков**: {len(self.duplicates['similar_titles'])}\n")
        lines.append(f"- **Всего проблем**: {total_issues}\n\n")

        if total_issues == 0:
            lines.append("✅ **Дубликатов не найдено!**\n\n")
        else:
            lines.append("⚠️  **Обнаружены потенциальные дубликаты**\n\n")

        # Точные дубликаты
        if self.duplicates['exact']:
            lines.append("## ⛔ Точные дубликаты\n\n")
            lines.append("> Идентичный контент (100% совпадение)\n\n")

            for i, dup in enumerate(self.duplicates['exact'], 1):
                lines.append(f"### Группа {i}\n\n")

                for article in dup['articles']:
                    lines.append(f"- **{article['title']}**\n")
                    lines.append(f"  - `{article['path']}`\n")

                lines.append("\n**Рекомендация**: Удалить дубликаты, оставить только одну статью\n\n")

        # Похожие статьи
        if self.duplicates['near_duplicate']:
            lines.append("## ⚠️  Похожий контент\n\n")
            lines.append(f"> Сходство >= {self.similarity_threshold * 100:.0f}%\n\n")

            for i, dup in enumerate(self.duplicates['near_duplicate'], 1):
                lines.append(f"### Пара {i} — Сходство: {dup['similarity'] * 100:.1f}%\n\n")

                for article in dup['articles']:
                    lines.append(f"- **{article['title']}**\n")
                    lines.append(f"  - [{article['path']}]({article['path']})\n")

                lines.append("\n**Рекомендация**: Проверить, можно ли объединить или дифференцировать\n\n")

        # Похожие заголовки
        if self.duplicates['similar_titles']:
            lines.append("## 📝 Похожие заголовки\n\n")
            lines.append("> Могут быть путаницей для читателей\n\n")

            for i, dup in enumerate(self.duplicates['similar_titles'], 1):
                lines.append(f"### Пара {i} — Сходство: {dup['similarity'] * 100:.1f}%\n\n")

                for article in dup['articles']:
                    lines.append(f"- **{article['title']}**\n")
                    lines.append(f"  - [{article['path']}]({article['path']})\n")

                lines.append("\n**Рекомендация**: Сделать заголовки более различимыми\n\n")

        output_file = self.root_dir / "DUPLICATES_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить результаты в JSON"""
        output_file = self.root_dir / "duplicates.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.duplicates, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")

    def calculate_cosine_similarity(self, text1: str, text2: str) -> float:
        """
        Вычислить cosine similarity с TF-IDF

        cos(θ) = (A·B) / (||A|| × ||B||)
        """
        # Токенизация
        words1 = re.findall(r'\b\w+\b', text1.lower())
        words2 = re.findall(r'\b\w+\b', text2.lower())

        # TF (Term Frequency)
        tf1 = Counter(words1)
        tf2 = Counter(words2)

        # Все уникальные слова
        all_words = set(tf1.keys()) | set(tf2.keys())

        # Векторы
        vec1 = [tf1.get(word, 0) for word in all_words]
        vec2 = [tf2.get(word, 0) for word in all_words]

        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Magnitudes
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def get_shingles(self, text: str, k: int = 3) -> Set[str]:
        """
        Создать k-shingles (n-grams) для текста

        Example: "hello world" with k=3 → {"hel", "ell", "llo", ...}
        """
        normalized = self.normalize_text(text)
        shingles = set()

        for i in range(len(normalized) - k + 1):
            shingle = normalized[i:i + k]
            shingles.add(shingle)

        return shingles

    def shingle_similarity(self, text1: str, text2: str, k: int = 3) -> float:
        """Jaccard similarity на основе shingles"""
        shingles1 = self.get_shingles(text1, k)
        shingles2 = self.get_shingles(text2, k)

        if not shingles1 or not shingles2:
            return 0.0

        intersection = len(shingles1 & shingles2)
        union = len(shingles1 | shingles2)

        return intersection / union if union > 0 else 0.0


class AdvancedDuplicateDetector(DuplicateDetector):
    """Продвинутый детектор с дополнительными алгоритмами"""

    def find_duplicates_by_cosine(self, threshold: float = 0.8) -> List[Dict]:
        """Найти дубликаты используя cosine similarity"""
        print(f"🔍 Поиск дубликатов (cosine similarity >= {threshold})...\n")

        duplicates = []
        articles_list = list(self.articles.items())

        for i, (path1, data1) in enumerate(articles_list):
            for path2, data2 in articles_list[i + 1:]:
                similarity = self.calculate_cosine_similarity(data1['content'], data2['content'])

                if similarity >= threshold:
                    duplicates.append({
                        'type': 'cosine_duplicate',
                        'articles': [
                            {'path': path1, 'title': data1['title']},
                            {'path': path2, 'title': data2['title']}
                        ],
                        'similarity': similarity,
                        'method': 'cosine'
                    })

        print(f"   Найдено пар (cosine): {len(duplicates)}\n")
        return duplicates

    def find_duplicates_by_shingles(self, threshold: float = 0.7, k: int = 3) -> List[Dict]:
        """Найти дубликаты используя shingle similarity"""
        print(f"🔍 Поиск дубликатов (shingles k={k}, threshold={threshold})...\n")

        duplicates = []
        articles_list = list(self.articles.items())

        for i, (path1, data1) in enumerate(articles_list):
            for path2, data2 in articles_list[i + 1:]:
                similarity = self.shingle_similarity(data1['content'], data2['content'], k)

                if similarity >= threshold:
                    duplicates.append({
                        'type': 'shingle_duplicate',
                        'articles': [
                            {'path': path1, 'title': data1['title']},
                            {'path': path2, 'title': data2['title']}
                        ],
                        'similarity': similarity,
                        'method': f'shingles-{k}'
                    })

        print(f"   Найдено пар (shingles): {len(duplicates)}\n")
        return duplicates

    def analyze_similarity_distribution(self) -> Dict:
        """Анализ распределения сходства между всеми парами"""
        print("📊 Анализ распределения сходства...\n")

        similarities = []
        articles_list = list(self.articles.items())

        for i, (path1, data1) in enumerate(articles_list):
            for path2, data2 in articles_list[i + 1:]:
                jaccard = self.calculate_similarity(data1['content'], data2['content'])
                cosine = self.calculate_cosine_similarity(data1['content'], data2['content'])

                similarities.append({
                    'pair': (data1['title'], data2['title']),
                    'jaccard': jaccard,
                    'cosine': cosine
                })

        if not similarities:
            return {}

        # Statistics
        jaccard_scores = [s['jaccard'] for s in similarities]
        cosine_scores = [s['cosine'] for s in similarities]

        stats = {
            'total_pairs': len(similarities),
            'jaccard': {
                'mean': sum(jaccard_scores) / len(jaccard_scores),
                'max': max(jaccard_scores),
                'min': min(jaccard_scores)
            },
            'cosine': {
                'mean': sum(cosine_scores) / len(cosine_scores),
                'max': max(cosine_scores),
                'min': min(cosine_scores)
            },
            'top_similar': sorted(similarities, key=lambda x: x['cosine'], reverse=True)[:5]
        }

        print(f"   Всего пар проанализировано: {stats['total_pairs']}")
        print(f"   Jaccard: mean={stats['jaccard']['mean']:.3f}, max={stats['jaccard']['max']:.3f}")
        print(f"   Cosine: mean={stats['cosine']['mean']:.3f}, max={stats['cosine']['max']:.3f}\n")

        return stats


class SimilarityAnalyzer:
    """
    Сравнение различных метрик сходства
    Анализирует корреляцию между Jaccard, Cosine, Levenshtein, Shingles
    """

    def __init__(self, detector):
        self.detector = detector
        self.comparisons = []

    def compare_all_metrics(self):
        """Сравнить все метрики сходства для каждой пары"""
        print("🔬 Сравнение метрик сходства...\n")

        articles_list = list(self.detector.articles.items())

        for i, (path1, data1) in enumerate(articles_list):
            for path2, data2 in articles_list[i + 1:]:
                jaccard = self.detector.calculate_similarity(data1['content'], data2['content'])
                cosine = self.detector.calculate_cosine_similarity(data1['content'], data2['content'])
                shingles = self.detector.shingle_similarity(data1['content'], data2['content'], k=3)

                # Title similarity (Levenshtein-based)
                title_sim = self.detector.title_similarity(data1['title'], data2['title'])

                self.comparisons.append({
                    'pair': (data1['title'], data2['title']),
                    'paths': (path1, path2),
                    'jaccard': jaccard,
                    'cosine': cosine,
                    'shingles': shingles,
                    'title_levenshtein': title_sim
                })

        print(f"   Сравнено пар: {len(self.comparisons)}\n")

    def calculate_correlation(self):
        """Вычислить корреляцию между метриками"""
        if not self.comparisons:
            return {}

        # Извлечь значения
        jaccard_vals = [c['jaccard'] for c in self.comparisons]
        cosine_vals = [c['cosine'] for c in self.comparisons]
        shingles_vals = [c['shingles'] for c in self.comparisons]

        # Простая корреляция Пирсона
        def pearson_correlation(x, y):
            n = len(x)
            mean_x = sum(x) / n
            mean_y = sum(y) / n

            numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
            denominator_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
            denominator_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))

            if denominator_x == 0 or denominator_y == 0:
                return 0.0

            return numerator / (denominator_x * denominator_y)

        correlations = {
            'jaccard_cosine': pearson_correlation(jaccard_vals, cosine_vals),
            'jaccard_shingles': pearson_correlation(jaccard_vals, shingles_vals),
            'cosine_shingles': pearson_correlation(cosine_vals, shingles_vals)
        }

        return correlations

    def find_metric_disagreements(self, threshold_diff=0.3):
        """Найти пары, где метрики сильно расходятся"""
        disagreements = []

        for comp in self.comparisons:
            metrics = [comp['jaccard'], comp['cosine'], comp['shingles']]
            max_diff = max(metrics) - min(metrics)

            if max_diff >= threshold_diff:
                disagreements.append({
                    'pair': comp['pair'],
                    'jaccard': comp['jaccard'],
                    'cosine': comp['cosine'],
                    'shingles': comp['shingles'],
                    'max_diff': max_diff
                })

        return sorted(disagreements, key=lambda x: -x['max_diff'])

    def generate_metrics_report(self):
        """Создать отчёт сравнения метрик"""
        lines = []
        lines.append("# 🔬 Отчёт: Сравнение метрик сходства\n\n")

        # Корреляции
        correlations = self.calculate_correlation()
        lines.append("## Корреляции между метриками\n\n")
        lines.append(f"- **Jaccard ↔ Cosine**: {correlations.get('jaccard_cosine', 0):.3f}\n")
        lines.append(f"- **Jaccard ↔ Shingles**: {correlations.get('jaccard_shingles', 0):.3f}\n")
        lines.append(f"- **Cosine ↔ Shingles**: {correlations.get('cosine_shingles', 0):.3f}\n\n")

        # Расхождения
        disagreements = self.find_metric_disagreements(threshold_diff=0.3)
        if disagreements:
            lines.append(f"## Расхождения метрик (топ-10)\n\n")
            lines.append("> Пары, где метрики сильно расходятся\n\n")

            for i, dis in enumerate(disagreements[:10], 1):
                lines.append(f"### {i}. {dis['pair'][0]} ↔ {dis['pair'][1]}\n\n")
                lines.append(f"- Jaccard: {dis['jaccard']:.3f}\n")
                lines.append(f"- Cosine: {dis['cosine']:.3f}\n")
                lines.append(f"- Shingles: {dis['shingles']:.3f}\n")
                lines.append(f"- **Макс. разница**: {dis['max_diff']:.3f}\n\n")

        return ''.join(lines)


class ClusterAnalyzer:
    """
    Кластеризация дубликатов
    Группирует похожие документы в кластеры
    """

    def __init__(self, detector):
        self.detector = detector
        self.clusters = []

    def simple_clustering(self, similarity_threshold=0.6):
        """Простая кластеризация: greedy algorithm"""
        print(f"🔗 Кластеризация (threshold={similarity_threshold})...\n")

        articles_list = list(self.detector.articles.items())
        visited = set()

        for i, (path1, data1) in enumerate(articles_list):
            if path1 in visited:
                continue

            # Создать новый кластер
            cluster = {
                'representative': {'path': path1, 'title': data1['title']},
                'members': [{'path': path1, 'title': data1['title']}],
                'avg_similarity': 0.0
            }

            similarities = []

            # Найти похожие документы
            for j, (path2, data2) in enumerate(articles_list):
                if i == j or path2 in visited:
                    continue

                similarity = self.detector.calculate_similarity(data1['content'], data2['content'])

                if similarity >= similarity_threshold:
                    cluster['members'].append({'path': path2, 'title': data2['title']})
                    visited.add(path2)
                    similarities.append(similarity)

            visited.add(path1)

            # Вычислить среднее сходство
            if similarities:
                cluster['avg_similarity'] = sum(similarities) / len(similarities)

            # Добавить кластер только если в нём > 1 документа
            if len(cluster['members']) > 1:
                self.clusters.append(cluster)

        print(f"   Найдено кластеров: {len(self.clusters)}\n")

    def get_cluster_statistics(self):
        """Статистика кластеров"""
        if not self.clusters:
            return {}

        cluster_sizes = [len(c['members']) for c in self.clusters]

        stats = {
            'total_clusters': len(self.clusters),
            'total_documents_clustered': sum(cluster_sizes),
            'avg_cluster_size': sum(cluster_sizes) / len(cluster_sizes),
            'max_cluster_size': max(cluster_sizes),
            'min_cluster_size': min(cluster_sizes),
            'largest_cluster': max(self.clusters, key=lambda c: len(c['members']))
        }

        return stats

    def generate_cluster_report(self):
        """Создать отчёт кластеризации"""
        lines = []
        lines.append("# 🔗 Отчёт: Кластеризация дубликатов\n\n")

        stats = self.get_cluster_statistics()

        if not stats:
            lines.append("⚠️ Кластеров не найдено\n\n")
            return ''.join(lines)

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего кластеров**: {stats['total_clusters']}\n")
        lines.append(f"- **Документов в кластерах**: {stats['total_documents_clustered']}\n")
        lines.append(f"- **Средний размер кластера**: {stats['avg_cluster_size']:.1f}\n")
        lines.append(f"- **Макс. размер кластера**: {stats['max_cluster_size']}\n\n")

        # Кластеры
        lines.append("## Кластеры\n\n")

        for i, cluster in enumerate(self.clusters, 1):
            lines.append(f"### Кластер {i} ({len(cluster['members'])} документов)\n\n")
            lines.append(f"**Представитель**: {cluster['representative']['title']}\n\n")
            lines.append(f"**Среднее сходство**: {cluster['avg_similarity']:.3f}\n\n")
            lines.append("**Члены кластера**:\n\n")

            for member in cluster['members']:
                lines.append(f"- {member['title']}\n")
                lines.append(f"  - `{member['path']}`\n")

            lines.append("\n")

        return ''.join(lines)


class DuplicateVisualizer:
    """
    HTML визуализация дубликатов
    Dashboard с Chart.js графиками
    """

    def __init__(self, detector, similarity_analyzer=None, cluster_analyzer=None):
        self.detector = detector
        self.similarity_analyzer = similarity_analyzer
        self.cluster_analyzer = cluster_analyzer

    def generate_html_dashboard(self, output_file='DUPLICATES_DASHBOARD.html'):
        """Создать HTML dashboard"""
        print("🎨 Создание HTML dashboard...\n")

        # Подготовить данные
        stats = self._prepare_statistics()
        chart_data = self._prepare_chart_data()

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Duplicate Detector Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 40px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-value {{
            color: #667eea;
            font-size: 3em;
            font-weight: bold;
        }}

        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}

        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .chart-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        canvas {{
            max-height: 350px;
        }}

        .footer {{
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Duplicate Detector Dashboard</h1>
        <p class="subtitle">Анализ дубликатов и сходства контента</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего статей</div>
                <div class="stat-value">{stats['total_articles']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Точных дубликатов</div>
                <div class="stat-value">{stats['exact_duplicates']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Похожих пар</div>
                <div class="stat-value">{stats['near_duplicates']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Кластеров</div>
                <div class="stat-value">{stats['clusters']}</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-title">📊 Типы дубликатов</div>
                <canvas id="duplicateTypesChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">📈 Распределение сходства (Jaccard)</div>
                <canvas id="similarityDistChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">🔬 Сравнение метрик</div>
                <canvas id="metricsComparisonChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">🔗 Размеры кластеров</div>
                <canvas id="clusterSizesChart"></canvas>
            </div>
        </div>

        <div class="footer">
            Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Duplicate Detector v2.0
        </div>
    </div>

    <script>
        // Типы дубликатов
        new Chart(document.getElementById('duplicateTypesChart'), {{
            type: 'doughnut',
            data: {{
                labels: {chart_data['duplicate_types']['labels']},
                datasets: [{{
                    data: {chart_data['duplicate_types']['values']},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});

        // Распределение сходства
        new Chart(document.getElementById('similarityDistChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['similarity_dist']['labels']},
                datasets: [{{
                    label: 'Количество пар',
                    data: {chart_data['similarity_dist']['values']},
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Сравнение метрик
        new Chart(document.getElementById('metricsComparisonChart'), {{
            type: 'radar',
            data: {{
                labels: ['Jaccard', 'Cosine', 'Shingles', 'Levenshtein'],
                datasets: [{{
                    label: 'Среднее значение',
                    data: {chart_data['metrics_comparison']},
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: '#667eea',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 1.0
                    }}
                }}
            }}
        }});

        // Размеры кластеров
        new Chart(document.getElementById('clusterSizesChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['cluster_sizes']['labels']},
                datasets: [{{
                    label: 'Размер кластера',
                    data: {chart_data['cluster_sizes']['values']},
                    backgroundColor: '#764ba2'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        output_path = self.detector.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML Dashboard: {output_path}\n")

    def _prepare_statistics(self):
        """Подготовить статистику"""
        stats = {
            'total_articles': len(self.detector.articles),
            'exact_duplicates': len(self.detector.duplicates.get('exact', [])),
            'near_duplicates': len(self.detector.duplicates.get('near_duplicate', [])),
            'clusters': 0
        }

        if self.cluster_analyzer and self.cluster_analyzer.clusters:
            stats['clusters'] = len(self.cluster_analyzer.clusters)

        return stats

    def _prepare_chart_data(self):
        """Подготовить данные для графиков"""
        chart_data = {
            'duplicate_types': {
                'labels': ['Точные', 'Похожие', 'Похожие заголовки', 'Кластеры'],
                'values': [
                    len(self.detector.duplicates.get('exact', [])),
                    len(self.detector.duplicates.get('near_duplicate', [])),
                    len(self.detector.duplicates.get('similar_titles', [])),
                    len(self.cluster_analyzer.clusters) if self.cluster_analyzer else 0
                ]
            },
            'similarity_dist': self._get_similarity_distribution(),
            'metrics_comparison': self._get_metrics_comparison(),
            'cluster_sizes': self._get_cluster_sizes()
        }

        return chart_data

    def _get_similarity_distribution(self):
        """Распределение сходства"""
        # Собрать все значения сходства
        similarities = []

        for dup in self.detector.duplicates.get('near_duplicate', []):
            similarities.append(dup['similarity'])

        # Создать гистограмму
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
        counts = [0] * (len(bins) - 1)

        for sim in similarities:
            for i in range(len(bins) - 1):
                if bins[i] <= sim < bins[i + 1]:
                    counts[i] += 1
                    break

        return {'labels': labels, 'values': counts}

    def _get_metrics_comparison(self):
        """Сравнение метрик"""
        if not self.similarity_analyzer or not self.similarity_analyzer.comparisons:
            return [0, 0, 0, 0]

        # Средние значения метрик
        jaccard_avg = sum(c['jaccard'] for c in self.similarity_analyzer.comparisons) / len(self.similarity_analyzer.comparisons)
        cosine_avg = sum(c['cosine'] for c in self.similarity_analyzer.comparisons) / len(self.similarity_analyzer.comparisons)
        shingles_avg = sum(c['shingles'] for c in self.similarity_analyzer.comparisons) / len(self.similarity_analyzer.comparisons)
        levenshtein_avg = sum(c['title_levenshtein'] for c in self.similarity_analyzer.comparisons) / len(self.similarity_analyzer.comparisons)

        return [
            round(jaccard_avg, 3),
            round(cosine_avg, 3),
            round(shingles_avg, 3),
            round(levenshtein_avg, 3)
        ]

    def _get_cluster_sizes(self):
        """Размеры кластеров"""
        if not self.cluster_analyzer or not self.cluster_analyzer.clusters:
            return {'labels': [], 'values': []}

        labels = [f"Кластер {i+1}" for i in range(len(self.cluster_analyzer.clusters))]
        values = [len(c['members']) for c in self.cluster_analyzer.clusters]

        return {'labels': labels, 'values': values}


class MergeRecommender:
    """
    Рекомендации по слиянию дубликатов
    Анализирует пары и предлагает стратегию
    """

    def __init__(self, detector):
        self.detector = detector
        self.recommendations = []

    def analyze_duplicates(self):
        """Проанализировать дубликаты и создать рекомендации"""
        print("💡 Анализ дубликатов для рекомендаций...\n")

        # Точные дубликаты - высокая уверенность в слиянии
        for dup in self.detector.duplicates.get('exact', []):
            self.recommendations.append({
                'type': 'exact_duplicate',
                'articles': dup['articles'],
                'action': 'merge',
                'confidence': 1.0,
                'reason': 'Идентичный контент (100% совпадение)'
            })

        # Похожие статьи - анализировать глубже
        for dup in self.detector.duplicates.get('near_duplicate', []):
            similarity = dup['similarity']

            if similarity >= 0.95:
                action = 'merge'
                reason = f'Очень высокое сходство ({similarity*100:.1f}%)'
                confidence = 0.95
            elif similarity >= 0.85:
                action = 'review'
                reason = f'Высокое сходство ({similarity*100:.1f}%), требует проверки'
                confidence = 0.7
            else:
                action = 'keep_separate'
                reason = f'Умеренное сходство ({similarity*100:.1f}%), вероятно разные темы'
                confidence = 0.5

            self.recommendations.append({
                'type': 'near_duplicate',
                'articles': dup['articles'],
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'similarity': similarity
            })

        print(f"   Создано рекомендаций: {len(self.recommendations)}\n")

    def get_recommendations_by_action(self, action):
        """Получить рекомендации по типу действия"""
        return [r for r in self.recommendations if r['action'] == action]

    def generate_merge_plan(self):
        """Создать план слияния"""
        lines = []
        lines.append("# 💡 План слияния дубликатов\n\n")
        lines.append(f"> Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        # Статистика
        merge_count = len([r for r in self.recommendations if r['action'] == 'merge'])
        review_count = len([r for r in self.recommendations if r['action'] == 'review'])
        keep_count = len([r for r in self.recommendations if r['action'] == 'keep_separate'])

        lines.append("## Статистика рекомендаций\n\n")
        lines.append(f"- **Слить**: {merge_count}\n")
        lines.append(f"- **Проверить вручную**: {review_count}\n")
        lines.append(f"- **Оставить раздельно**: {keep_count}\n")
        lines.append(f"- **Всего**: {len(self.recommendations)}\n\n")

        # Рекомендации по слиянию
        merge_recs = self.get_recommendations_by_action('merge')
        if merge_recs:
            lines.append("## ✅ Рекомендуется слить\n\n")

            for i, rec in enumerate(merge_recs, 1):
                lines.append(f"### {i}. Уверенность: {rec['confidence']*100:.0f}%\n\n")
                lines.append(f"**Причина**: {rec['reason']}\n\n")

                for article in rec['articles']:
                    lines.append(f"- {article['title']}\n")
                    lines.append(f"  - `{article['path']}`\n")

                lines.append("\n**Действие**: Удалить дубликаты, сохранить самую полную версию\n\n")

        # Требует проверки
        review_recs = self.get_recommendations_by_action('review')
        if review_recs:
            lines.append("## ⚠️ Требует ручной проверки\n\n")

            for i, rec in enumerate(review_recs, 1):
                lines.append(f"### {i}. Сходство: {rec.get('similarity', 0)*100:.1f}%\n\n")
                lines.append(f"**Причина**: {rec['reason']}\n\n")

                for article in rec['articles']:
                    lines.append(f"- {article['title']}\n")
                    lines.append(f"  - `{article['path']}`\n")

                lines.append("\n**Действие**: Сравнить вручную, решить о слиянии\n\n")

        return ''.join(lines)

    def export_to_csv(self, output_file='merge_recommendations.csv'):
        """Экспорт рекомендаций в CSV"""
        csv_path = self.detector.root_dir / output_file

        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Тип', 'Статья 1', 'Статья 2', 'Действие', 'Уверенность', 'Причина'])

            for rec in self.recommendations:
                if len(rec['articles']) >= 2:
                    writer.writerow([
                        rec['type'],
                        rec['articles'][0]['title'],
                        rec['articles'][1]['title'],
                        rec['action'],
                        f"{rec['confidence']:.2f}",
                        rec['reason']
                    ])

        print(f"✅ CSV рекомендации: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description='🔍 Duplicate Detector v2.0 - Расширенный детектор дубликатов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                              # Стандартный поиск дубликатов
  %(prog)s --html                       # HTML dashboard с графиками
  %(prog)s --cluster                    # Кластеризация похожих документов
  %(prog)s --compare-metrics            # Сравнение метрик сходства
  %(prog)s --recommend-merges           # Рекомендации по слиянию
  %(prog)s --csv                        # Экспорт рекомендаций в CSV
  %(prog)s --all                        # Все функции сразу
  %(prog)s --threshold 0.9 --cluster    # Кластеризация с порогом 0.9
  %(prog)s --clustering-method advanced # Продвинутая кластеризация

Новые возможности v2.0:
  - 🔬 Сравнение 4 метрик сходства (Jaccard, Cosine, Shingles, Levenshtein)
  - 🔗 Кластеризация дубликатов
  - 🎨 HTML dashboard с Chart.js визуализациями
  - 💡 Умные рекомендации по слиянию
  - 📊 Корреляционный анализ метрик
  - 📈 Экспорт в CSV для анализа
        """
    )

    # Основные параметры
    parser.add_argument('-t', '--threshold', type=float, default=0.8,
                       help='Порог сходства (0.0-1.0, default: 0.8)')
    parser.add_argument('--method', type=str, choices=['jaccard', 'cosine', 'shingles', 'all'],
                       default='all', help='Метод обнаружения дубликатов')

    # Новые опции v2.0
    parser.add_argument('--html', action='store_true',
                       help='🎨 Создать HTML dashboard с интерактивными графиками')
    parser.add_argument('--cluster', action='store_true',
                       help='🔗 Выполнить кластеризацию похожих документов')
    parser.add_argument('--compare-metrics', action='store_true',
                       help='🔬 Сравнить различные метрики сходства')
    parser.add_argument('--recommend-merges', action='store_true',
                       help='💡 Создать рекомендации по слиянию дубликатов')
    parser.add_argument('--csv', action='store_true',
                       help='📊 Экспортировать рекомендации в CSV')

    # Параметры кластеризации
    parser.add_argument('--min-cluster-size', type=int, default=2,
                       help='Минимальный размер кластера (default: 2)')
    parser.add_argument('--cluster-threshold', type=float, default=0.6,
                       help='Порог сходства для кластеризации (default: 0.6)')
    parser.add_argument('--clustering-method', type=str, choices=['simple', 'advanced'],
                       default='simple', help='Метод кластеризации')

    # Экспорт
    parser.add_argument('--export-metrics', action='store_true',
                       help='📈 Экспортировать отчёт сравнения метрик')

    # Комплексные режимы
    parser.add_argument('--advanced', action='store_true',
                       help='🚀 Использовать продвинутые методы (cosine, shingles)')
    parser.add_argument('--analyze', action='store_true',
                       help='📊 Анализ распределения сходства')
    parser.add_argument('--all', action='store_true',
                       help='🔥 Выполнить все опции (полный анализ)')

    args = parser.parse_args()

    # --all включает все опции
    if args.all:
        args.html = True
        args.cluster = True
        args.compare_metrics = True
        args.recommend_merges = True
        args.csv = True
        args.export_metrics = True
        args.advanced = True
        args.analyze = True

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Выбор детектора
    if args.advanced or args.method in ['cosine', 'shingles', 'all'] or args.all:
        detector = AdvancedDuplicateDetector(root_dir, similarity_threshold=args.threshold)
    else:
        detector = DuplicateDetector(root_dir, similarity_threshold=args.threshold)

    # Сбор статей
    detector.collect_articles()

    # Standard methods
    if args.method in ['jaccard', 'all']:
        detector.find_exact_duplicates()
        detector.find_near_duplicates()
        detector.find_similar_titles()

    # Advanced methods
    if args.advanced or args.method in ['cosine', 'shingles', 'all']:
        if isinstance(detector, AdvancedDuplicateDetector):
            if args.method in ['cosine', 'all']:
                detector.find_duplicates_by_cosine(args.threshold)
            if args.method in ['shingles', 'all']:
                detector.find_duplicates_by_shingles(threshold=0.7, k=3)

    # Analyze
    if args.analyze and isinstance(detector, AdvancedDuplicateDetector):
        stats = detector.analyze_similarity_distribution()

        print("📊 Топ-5 самых похожих пар:\n")
        for i, sim in enumerate(stats.get('top_similar', []), 1):
            print(f"   {i}. {sim['pair'][0]} ↔ {sim['pair'][1]}")
            print(f"      Jaccard: {sim['jaccard']:.3f}, Cosine: {sim['cosine']:.3f}\n")

    # ========== НОВЫЕ ФУНКЦИИ V2.0 ==========

    # 1. Сравнение метрик
    similarity_analyzer = None
    if args.compare_metrics or args.html:
        if isinstance(detector, AdvancedDuplicateDetector):
            similarity_analyzer = SimilarityAnalyzer(detector)
            similarity_analyzer.compare_all_metrics()

            if args.export_metrics or args.all:
                report = similarity_analyzer.generate_metrics_report()
                metrics_file = root_dir / 'METRICS_COMPARISON.md'
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"✅ Отчёт сравнения метрик: {metrics_file}\n")

    # 2. Кластеризация
    cluster_analyzer = None
    if args.cluster or args.html:
        if isinstance(detector, AdvancedDuplicateDetector):
            cluster_analyzer = ClusterAnalyzer(detector)
            cluster_analyzer.simple_clustering(similarity_threshold=args.cluster_threshold)

            # Фильтр по минимальному размеру
            cluster_analyzer.clusters = [
                c for c in cluster_analyzer.clusters
                if len(c['members']) >= args.min_cluster_size
            ]

            report = cluster_analyzer.generate_cluster_report()
            cluster_file = root_dir / 'CLUSTERS_REPORT.md'
            with open(cluster_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Отчёт кластеризации: {cluster_file}\n")

    # 3. Рекомендации по слиянию
    if args.recommend_merges or args.all:
        recommender = MergeRecommender(detector)
        recommender.analyze_duplicates()

        plan = recommender.generate_merge_plan()
        plan_file = root_dir / 'MERGE_PLAN.md'
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan)
        print(f"✅ План слияния: {plan_file}\n")

        # CSV export
        if args.csv or args.all:
            recommender.export_to_csv()

    # 4. HTML Dashboard
    if args.html or args.all:
        visualizer = DuplicateVisualizer(detector, similarity_analyzer, cluster_analyzer)
        visualizer.generate_html_dashboard()

    # Generate standard reports
    detector.generate_report()
    detector.save_json()

    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    print(f"Всего статей проверено: {len(detector.articles)}")
    print(f"Точных дубликатов: {len(detector.duplicates.get('exact', []))}")
    print(f"Похожих пар: {len(detector.duplicates.get('near_duplicate', []))}")
    print(f"Похожих заголовков: {len(detector.duplicates.get('similar_titles', []))}")

    if cluster_analyzer and cluster_analyzer.clusters:
        print(f"Кластеров: {len(cluster_analyzer.clusters)}")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
