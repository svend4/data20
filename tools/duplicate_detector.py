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


def main():
    parser = argparse.ArgumentParser(
        description='🔍 Duplicate Detector - Детектор дубликатов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                        # Стандартный поиск дубликатов
  %(prog)s --advanced             # Продвинутый анализ (cosine, shingles)
  %(prog)s --analyze              # Анализ распределения сходства
  %(prog)s --threshold 0.9        # Установить порог сходства
  %(prog)s --method cosine        # Использовать только cosine similarity
        """
    )

    parser.add_argument('-t', '--threshold', type=float, default=0.8,
                       help='Порог сходства (0.0-1.0, default: 0.8)')
    parser.add_argument('--advanced', action='store_true',
                       help='Использовать продвинутые методы (cosine, shingles)')
    parser.add_argument('--analyze', action='store_true',
                       help='Анализ распределения сходства')
    parser.add_argument('--method', type=str, choices=['jaccard', 'cosine', 'shingles', 'all'],
                       default='all', help='Метод обнаружения дубликатов')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    if args.advanced or args.method in ['cosine', 'shingles', 'all']:
        detector = AdvancedDuplicateDetector(root_dir, similarity_threshold=args.threshold)
    else:
        detector = DuplicateDetector(root_dir, similarity_threshold=args.threshold)

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

    # Generate reports
    detector.generate_report()
    detector.save_json()


if __name__ == "__main__":
    main()
