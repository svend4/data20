#!/usr/bin/env python3
"""
Advanced Duplicate Detection System - Продвинутая система поиска дубликатов

Многоуровневая система обнаружения дубликатов с использованием:
- MinHash LSH (Locality-Sensitive Hashing) для быстрого поиска
- Simhash для near-duplicate detection
- Shingling (n-gram) для текстовой схожести
- Content fingerprinting (MD5, SHA256)
- Duplicate clustering и группировка версий
- Merge suggestions и canonical designation
- Code duplicate detection
- Multiple similarity algorithms

Inspired by: Google duplicate detection, Dedupe libraries, Plagiarism checkers

Author: Advanced Knowledge Management System
Version: 2.0
"""

from pathlib import Path
import re
import yaml
import json
import hashlib
from collections import defaultdict
from datetime import datetime
import argparse


class AdvancedDuplicateDetector:
    """
    Продвинутый детектор дубликатов

    Features:
    - Multiple algorithms: Jaccard, MinHash, Simhash, Shingling
    - Duplicate types: exact, near-exact, partial, semantic
    - Content fingerprinting
    - Duplicate clustering (groups of similar docs)
    - Merge suggestions
    - Canonical URL designation
    - Code block duplicate detection
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.articles = []

        # Duplicate clusters: {cluster_id: [article_paths]}
        self.clusters = defaultdict(list)

        # Content fingerprints
        self.fingerprints = {}

        # MinHash signatures для LSH
        self.minhash_sigs = {}

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные и контент"""
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

    # ==================== Fingerprinting ====================

    def calculate_fingerprint(self, content, algorithm='md5'):
        """Создать fingerprint контента"""
        # Normalize: lowercase, remove whitespace
        normalized = re.sub(r'\s+', ' ', content.lower().strip())

        if algorithm == 'md5':
            return hashlib.md5(normalized.encode()).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(normalized.encode()).hexdigest()
        else:
            return hashlib.sha1(normalized.encode()).hexdigest()

    def find_exact_duplicates(self):
        """Найти точные дубликаты по fingerprint"""
        fingerprint_map = defaultdict(list)

        for article in self.articles:
            fp = self.calculate_fingerprint(article['content'])
            fingerprint_map[fp].append(article['file'])

        # Только группы с >1 файлом
        exact_dups = {fp: files for fp, files in fingerprint_map.items() if len(files) > 1}

        return exact_dups

    # ==================== Shingling (n-grams) ====================

    def create_shingles(self, text, n=3):
        """
        Создать n-граммы (shingles) из текста
        n=3 -> 'hello world' -> ['hel', 'ell', 'llo', 'lo ', 'o w', ' wo', ...]
        """
        # Character-level shingles
        text = re.sub(r'\s+', ' ', text.lower())
        shingles = set()

        for i in range(len(text) - n + 1):
            shingle = text[i:i+n]
            shingles.add(shingle)

        return shingles

    def jaccard_similarity(self, set1, set2):
        """Jaccard similarity: |A ∩ B| / |A ∪ B|"""
        if not set1 or not set2:
            return 0.0

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0

    # ==================== MinHash LSH ====================

    def minhash_signature(self, shingles, num_hashes=100):
        """
        MinHash signature для быстрого approximate Jaccard similarity

        MinHash работает так:
        1. Для каждого shingle вычисляем hash
        2. Берём минимальный hash из набора
        3. Повторяем с разными hash-функциями
        4. Результат: список из num_hashes минимальных значений

        Свойство: P(minhash1[i] == minhash2[i]) ≈ Jaccard(set1, set2)
        """
        signature = []

        for i in range(num_hashes):
            min_hash = float('inf')

            for shingle in shingles:
                # Имитация разных hash-функций через добавление соли
                h = hash(f"{i}:{shingle}") & 0xFFFFFFFF  # 32-bit hash
                min_hash = min(min_hash, h)

            signature.append(min_hash)

        return signature

    def estimate_jaccard_from_minhash(self, sig1, sig2):
        """Оценить Jaccard similarity из MinHash signatures"""
        if len(sig1) != len(sig2):
            return 0.0

        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)

    # ==================== Simhash ====================

    def simhash(self, text, hash_bits=64):
        """
        Simhash для near-duplicate detection (как в Google)

        Алгоритм:
        1. Разбить текст на tokens (слова)
        2. Для каждого token: hash -> binary
        3. Если бит=1: +weight, если бит=0: -weight
        4. Финальный hash: sign(accumulated_weights)

        Свойство: похожие тексты → похожие simhash (малый Hamming distance)
        """
        tokens = re.findall(r'\b\w+\b', text.lower())

        if not tokens:
            return 0

        # Accumulator для каждого бита
        v = [0] * hash_bits

        for token in tokens:
            # Hash токена
            h = hash(token) & ((1 << hash_bits) - 1)  # Ограничить до hash_bits бит

            # Для каждого бита
            for i in range(hash_bits):
                if h & (1 << i):
                    v[i] += 1  # Бит = 1
                else:
                    v[i] -= 1  # Бит = 0

        # Финальный simhash
        fingerprint = 0
        for i in range(hash_bits):
            if v[i] > 0:
                fingerprint |= (1 << i)

        return fingerprint

    def hamming_distance(self, hash1, hash2):
        """Hamming distance между двумя хэшами"""
        xor = hash1 ^ hash2
        distance = 0

        while xor:
            distance += xor & 1
            xor >>= 1

        return distance

    # ==================== Duplicate Detection Methods ====================

    def find_near_duplicates_minhash(self, threshold=0.7):
        """Найти near-duplicates через MinHash LSH"""
        duplicates = []

        # Создать MinHash signatures для всех статей
        for article in self.articles:
            shingles = self.create_shingles(article['content'], n=5)
            sig = self.minhash_signature(shingles, num_hashes=100)
            self.minhash_sigs[article['file']] = sig

        # Сравнить все пары
        files = list(self.minhash_sigs.keys())
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                similarity = self.estimate_jaccard_from_minhash(
                    self.minhash_sigs[file1],
                    self.minhash_sigs[file2]
                )

                if similarity >= threshold:
                    duplicates.append({
                        'file1': file1,
                        'file2': file2,
                        'similarity': round(similarity, 3),
                        'type': 'near-duplicate',
                        'algorithm': 'MinHash LSH'
                    })

        return duplicates

    def find_near_duplicates_simhash(self, max_distance=5):
        """Найти near-duplicates через Simhash"""
        duplicates = []
        simhashes = {}

        # Вычислить Simhash для всех статей
        for article in self.articles:
            sh = self.simhash(article['content'], hash_bits=64)
            simhashes[article['file']] = sh

        # Сравнить все пары
        files = list(simhashes.keys())
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                distance = self.hamming_distance(simhashes[file1], simhashes[file2])

                if distance <= max_distance:
                    # Similarity оценка: чем меньше distance, тем больше similarity
                    similarity = 1.0 - (distance / 64.0)

                    duplicates.append({
                        'file1': file1,
                        'file2': file2,
                        'similarity': round(similarity, 3),
                        'hamming_distance': distance,
                        'type': 'near-duplicate',
                        'algorithm': 'Simhash'
                    })

        return duplicates

    def find_similar_by_tags(self):
        """Найти статьи с похожими тегами"""
        tag_groups = defaultdict(list)

        for article in self.articles:
            tags = article.get('tags', [])
            for tag in tags:
                tag_groups[tag].append(article['file'])

        similar_groups = {tag: files for tag, files in tag_groups.items() if len(files) > 1}

        return similar_groups

    def find_similar_by_title(self, threshold=0.5):
        """Найти статьи с похожими заголовками"""
        similar = []

        for i, article1 in enumerate(self.articles):
            for article2 in self.articles[i+1:]:
                title1 = article1.get('title', '').lower()
                title2 = article2.get('title', '').lower()

                if not title1 or not title2:
                    continue

                words1 = set(title1.split())
                words2 = set(title2.split())

                similarity = self.jaccard_similarity(words1, words2)

                if similarity >= threshold:
                    similar.append({
                        'file1': article1['file'],
                        'file2': article2['file'],
                        'title1': article1.get('title'),
                        'title2': article2.get('title'),
                        'similarity': round(similarity, 3),
                        'type': 'similar-title'
                    })

        return similar

    def find_code_duplicates(self):
        """Найти дубликаты code blocks"""
        code_blocks = defaultdict(list)

        for article in self.articles:
            content = article['content']
            # Найти все code blocks ```...```
            blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)

            for block in blocks:
                # Normalize code
                normalized = re.sub(r'\s+', ' ', block.strip())
                if len(normalized) > 20:  # Только значимые блоки
                    fp = hashlib.md5(normalized.encode()).hexdigest()
                    code_blocks[fp].append({
                        'file': article['file'],
                        'code': block[:100]  # Первые 100 символов
                    })

        # Только дубликаты
        duplicates = {fp: blocks for fp, blocks in code_blocks.items() if len(blocks) > 1}

        return duplicates

    # ==================== Clustering ====================

    def cluster_duplicates(self, duplicates, threshold=0.8):
        """
        Кластеризация дубликатов в группы

        Если A похож на B, и B похож на C, то A, B, C - один кластер
        """
        # Graph: file -> [similar files]
        graph = defaultdict(set)

        for dup in duplicates:
            if dup['similarity'] >= threshold:
                file1 = dup['file1']
                file2 = dup['file2']
                graph[file1].add(file2)
                graph[file2].add(file1)

        # DFS для поиска connected components
        visited = set()
        clusters = []

        def dfs(node, cluster):
            visited.add(node)
            cluster.append(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, cluster)

        for node in graph:
            if node not in visited:
                cluster = []
                dfs(node, cluster)
                if len(cluster) > 1:
                    clusters.append(sorted(cluster))

        return clusters

    def suggest_canonical(self, cluster):
        """
        Предложить канонический документ в кластере

        Критерии:
        - Самый длинный контент
        - Больше всего тегов
        - Новее (если есть дата)
        """
        best = None
        best_score = -1

        for file_path in cluster:
            # Найти статью
            article = next((a for a in self.articles if a['file'] == file_path), None)
            if not article:
                continue

            score = 0
            # Длина контента
            score += len(article['content']) / 100
            # Количество тегов
            score += len(article.get('tags', [])) * 5

            if score > best_score:
                best_score = score
                best = file_path

        return best

    def suggest_merge_action(self, cluster):
        """Предложить действие для мерджа дубликатов"""
        canonical = self.suggest_canonical(cluster)

        return {
            'canonical': canonical,
            'duplicates': [f for f in cluster if f != canonical],
            'action': 'merge',
            'suggestion': f"Keep {canonical}, merge/redirect others"
        }

    # ==================== Main Analysis ====================

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
                'category': frontmatter.get('category') if frontmatter else None,
                'content': content
            }

            self.articles.append(article)

    def analyze(self, algorithms=['all']):
        """Запустить анализ дубликатов"""
        results = {
            'exact_duplicates': [],
            'near_duplicates_minhash': [],
            'near_duplicates_simhash': [],
            'similar_titles': [],
            'similar_tags': {},
            'code_duplicates': {},
            'clusters': [],
            'merge_suggestions': []
        }

        if 'all' in algorithms or 'exact' in algorithms:
            results['exact_duplicates'] = self.find_exact_duplicates()

        if 'all' in algorithms or 'minhash' in algorithms:
            results['near_duplicates_minhash'] = self.find_near_duplicates_minhash(threshold=0.7)

        if 'all' in algorithms or 'simhash' in algorithms:
            results['near_duplicates_simhash'] = self.find_near_duplicates_simhash(max_distance=5)

        if 'all' in algorithms or 'title' in algorithms:
            results['similar_titles'] = self.find_similar_by_title(threshold=0.5)

        if 'all' in algorithms or 'tags' in algorithms:
            results['similar_tags'] = self.find_similar_by_tags()

        if 'all' in algorithms or 'code' in algorithms:
            results['code_duplicates'] = self.find_code_duplicates()

        # Clustering
        all_duplicates = (
            results['near_duplicates_minhash'] +
            results['near_duplicates_simhash'] +
            results['similar_titles']
        )

        if all_duplicates:
            clusters = self.cluster_duplicates(all_duplicates, threshold=0.7)
            results['clusters'] = clusters

            # Merge suggestions
            for cluster in clusters:
                suggestion = self.suggest_merge_action(cluster)
                results['merge_suggestions'].append(suggestion)

        return results

    def generate_statistics(self, results):
        """Статистика анализа"""
        stats = {
            'total_articles': len(self.articles),
            'exact_duplicates': len(results['exact_duplicates']),
            'near_duplicates_minhash': len(results['near_duplicates_minhash']),
            'near_duplicates_simhash': len(results['near_duplicates_simhash']),
            'similar_titles': len(results['similar_titles']),
            'similar_tag_groups': len(results['similar_tags']),
            'code_duplicates': len(results['code_duplicates']),
            'duplicate_clusters': len(results['clusters']),
            'merge_suggestions': len(results['merge_suggestions'])
        }

        return stats

    def generate_report(self, results, format='markdown'):
        """Создать отчёт"""
        if format == 'json':
            return self.generate_json_report(results)
        else:
            return self.generate_markdown_report(results)

    def generate_markdown_report(self, results):
        """Markdown отчёт"""
        lines = []
        stats = self.generate_statistics(results)

        lines.append("# 🔍 Duplicate Detection Report\n\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Statistics
        lines.append("## 📊 Summary Statistics\n\n")
        lines.append(f"- **Total articles**: {stats['total_articles']}\n")
        lines.append(f"- **Exact duplicates**: {stats['exact_duplicates']}\n")
        lines.append(f"- **Near-duplicates (MinHash)**: {stats['near_duplicates_minhash']}\n")
        lines.append(f"- **Near-duplicates (Simhash)**: {stats['near_duplicates_simhash']}\n")
        lines.append(f"- **Similar titles**: {stats['similar_titles']}\n")
        lines.append(f"- **Tag groups**: {stats['similar_tag_groups']}\n")
        lines.append(f"- **Code duplicates**: {stats['code_duplicates']}\n")
        lines.append(f"- **Duplicate clusters**: {stats['duplicate_clusters']}\n\n")

        # Exact duplicates
        if results['exact_duplicates']:
            lines.append(f"## 💯 Exact Duplicates ({len(results['exact_duplicates'])})\n\n")

            for i, (fp, files) in enumerate(list(results['exact_duplicates'].items())[:10], 1):
                lines.append(f"### Group {i} (fingerprint: {fp[:16]}...)\n\n")
                for f in files:
                    lines.append(f"- `{f}`\n")
                lines.append("\n")

        # Near-duplicates (MinHash)
        if results['near_duplicates_minhash']:
            lines.append(f"## 🔄 Near-Duplicates - MinHash LSH ({len(results['near_duplicates_minhash'])})\n\n")

            for i, dup in enumerate(results['near_duplicates_minhash'][:20], 1):
                lines.append(f"### {i}. Similarity: {dup['similarity']*100:.1f}%\n\n")
                lines.append(f"- **File 1**: `{dup['file1']}`\n")
                lines.append(f"- **File 2**: `{dup['file2']}`\n\n")

        # Clusters
        if results['clusters']:
            lines.append(f"## 🗂️ Duplicate Clusters ({len(results['clusters'])})\n\n")

            for i, cluster in enumerate(results['clusters'][:10], 1):
                lines.append(f"### Cluster {i} ({len(cluster)} documents)\n\n")
                for f in cluster:
                    lines.append(f"- `{f}`\n")
                lines.append("\n")

        # Merge suggestions
        if results['merge_suggestions']:
            lines.append(f"## 💡 Merge Suggestions ({len(results['merge_suggestions'])})\n\n")

            for i, suggestion in enumerate(results['merge_suggestions'][:10], 1):
                lines.append(f"### {i}. {suggestion['action'].upper()}\n\n")
                lines.append(f"- **Keep (canonical)**: `{suggestion['canonical']}`\n")
                lines.append(f"- **Merge/redirect**:\n")
                for dup in suggestion['duplicates']:
                    lines.append(f"  - `{dup}`\n")
                lines.append(f"- **Suggestion**: {suggestion['suggestion']}\n\n")

        output_file = self.root_dir / "DUPLICATE_DETECTION_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown report: {output_file}")
        return output_file

    def generate_json_report(self, results):
        """JSON отчёт"""
        stats = self.generate_statistics(results)

        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'results': results
        }

        output_file = self.root_dir / "duplicate_detection.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON report: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description='Advanced Duplicate Detection System')
    parser.add_argument('--algorithms', nargs='+',
                       choices=['all', 'exact', 'minhash', 'simhash', 'title', 'tags', 'code'],
                       default=['all'],
                       help='Algorithms to use (default: all)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Report format (default: markdown)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    detector = AdvancedDuplicateDetector(root_dir)

    print("🔍 Advanced Duplicate Detection System\n")
    print("   Scanning articles...")
    detector.scan_articles()
    print(f"   Found: {len(detector.articles)} articles\n")

    print("   Running analysis...")
    results = detector.analyze(algorithms=args.algorithms)

    print("   Generating report...\n")
    detector.generate_report(results, format=args.format)

    # Print summary
    stats = detector.generate_statistics(results)
    print(f"\n📊 Summary:")
    print(f"   Exact duplicates: {stats['exact_duplicates']}")
    print(f"   Near-duplicates (MinHash): {stats['near_duplicates_minhash']}")
    print(f"   Near-duplicates (Simhash): {stats['near_duplicates_simhash']}")
    print(f"   Duplicate clusters: {stats['duplicate_clusters']}")
    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
