#!/usr/bin/env python3
"""
Advanced Tag Analytics - Продвинутая аналитика тегов

Комплексная система анализа тегов с поддержкой:
- Multi-dimensional weighting (frequency + recency + importance)
- Tag co-occurrence matrix (какие теги появляются вместе)
- Tag hierarchies/taxonomy
- Tag trending analysis (emerging, mature, declining)
- Tag entropy (специфичность тега)
- Semantic tag clustering
- Tag normalization (синонимы, множественное число)
- Tag coverage metrics
- Tag recommendation quality

Inspired by: Stack Overflow tags, Folksonomy research, Tag recommender systems

Author: Advanced Knowledge Management System
Version: 2.0
"""

from pathlib import Path
import yaml
import re
import json
from collections import Counter, defaultdict
import math
from datetime import datetime
import argparse


class AdvancedTagAnalyzer:
    """
    Продвинутый анализатор тегов

    Features:
    - Multi-dimensional tag weighting
    - Co-occurrence analysis (tag pairs)
    - Tag lifecycle tracking (emerging/mature/declining)
    - Tag entropy (specificity measure)
    - Semantic clustering
    - Tag normalization
    - Coverage metrics
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Data structures
        self.articles = []
        self.tag_stats = {}
        self.co_occurrence = defaultdict(lambda: defaultdict(int))
        self.tag_timeline = defaultdict(list)

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter и метаданные"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2)
                return frontmatter, body
        except:
            pass
        return None, ""

    def normalize_tag(self, tag):
        """
        Нормализация тега
        - Lowercase
        - Убрать множественное число (s)
        - Заменить дефисы на подчёркивания
        """
        normalized = tag.lower().strip()

        # Убрать множественное число (простая эвристика)
        if normalized.endswith('s') and len(normalized) > 3:
            # Не трогать теги вроде "css", "os"
            if not normalized.endswith(('ss', 'is', 'us')):
                normalized = normalized[:-1]

        # Унифицировать разделители
        normalized = normalized.replace('-', '_')

        return normalized

    def scan_articles(self):
        """Сканировать все статьи"""
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter(md_file)
            if not frontmatter:
                continue

            # Попытка извлечь дату создания
            created = frontmatter.get('created', frontmatter.get('date'))
            if created and isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                except:
                    created = None

            article = {
                'file': str(md_file.relative_to(self.root_dir)),
                'title': frontmatter.get('title'),
                'tags': frontmatter.get('tags', []),
                'category': frontmatter.get('category'),
                'created': created,
                'content_length': len(content)
            }

            self.articles.append(article)

    # ==================== Tag Weighting ====================

    def calculate_multidimensional_weights(self):
        """
        Многомерные веса тегов

        Dimensions:
        - Frequency: сколько раз используется
        - Recency: как недавно используется
        - Importance: на основе контента (длина статей с тегом)
        - Specificity: насколько специфичен (entropy)
        """
        tag_counts = Counter()
        tag_articles = defaultdict(list)
        tag_content_lengths = defaultdict(list)
        tag_dates = defaultdict(list)

        # Собрать статистику
        for article in self.articles:
            for tag in article['tags']:
                normalized = self.normalize_tag(tag)
                tag_counts[normalized] += 1
                tag_articles[normalized].append(article['file'])
                tag_content_lengths[normalized].append(article['content_length'])

                if article['created']:
                    tag_dates[normalized].append(article['created'])

        # Вычислить веса
        total_articles = len(self.articles)
        now = datetime.now()

        for tag in tag_counts:
            count = tag_counts[tag]

            # 1. Frequency weight (0-100)
            freq_weight = min(100, count * 10)

            # 2. Recency weight (0-100)
            recency_weight = 0
            if tag_dates[tag]:
                avg_age_days = sum((now - d).days for d in tag_dates[tag]) / len(tag_dates[tag])
                recency_weight = max(0, 100 - avg_age_days / 3)  # Decay over ~300 days

            # 3. Importance weight (на основе длины контента)
            avg_content_length = sum(tag_content_lengths[tag]) / len(tag_content_lengths[tag])
            importance_weight = min(100, avg_content_length / 50)  # Normalize to 0-100

            # 4. Specificity (TF-IDF like)
            idf = math.log(total_articles / count) if count > 0 else 0
            specificity = min(100, idf * 30)

            # 5. Combined weight (weighted average)
            combined_weight = (
                freq_weight * 0.4 +
                recency_weight * 0.2 +
                importance_weight * 0.2 +
                specificity * 0.2
            )

            self.tag_stats[tag] = {
                'count': count,
                'frequency_weight': round(freq_weight, 2),
                'recency_weight': round(recency_weight, 2),
                'importance_weight': round(importance_weight, 2),
                'specificity': round(specificity, 2),
                'combined_weight': round(combined_weight, 2),
                'articles': tag_articles[tag],
                'avg_content_length': round(avg_content_length, 0)
            }

        return self.tag_stats

    # ==================== Co-occurrence Analysis ====================

    def calculate_tag_cooccurrence(self):
        """
        Матрица совместной встречаемости тегов

        Какие теги часто появляются вместе?
        """
        for article in self.articles:
            tags = [self.normalize_tag(t) for t in article['tags']]

            # Все пары тегов в статье
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    # Симметричная матрица
                    self.co_occurrence[tag1][tag2] += 1
                    self.co_occurrence[tag2][tag1] += 1

        # Конвертировать в обычный dict для сериализации
        result = {}
        for tag1 in self.co_occurrence:
            result[tag1] = dict(self.co_occurrence[tag1])

        return result

    def get_related_tags(self, tag, top_n=5):
        """Получить наиболее связанные теги"""
        normalized = self.normalize_tag(tag)

        if normalized not in self.co_occurrence:
            return []

        # Сортировать по частоте совместной встречаемости
        related = sorted(
            self.co_occurrence[normalized].items(),
            key=lambda x: -x[1]
        )

        return related[:top_n]

    # ==================== Tag Lifecycle ====================

    def analyze_tag_lifecycle(self):
        """
        Анализ жизненного цикла тегов

        Categories:
        - Emerging: новые теги (появились недавно, растут)
        - Mature: устоявшиеся теги (используются давно, стабильны)
        - Declining: угасающие теги (давно не используются)
        """
        lifecycle = {}

        for tag, stats in self.tag_stats.items():
            count = stats['count']
            recency = stats['recency_weight']

            # Классификация
            if count <= 2 and recency > 70:
                category = 'emerging'
            elif count >= 5 and recency > 50:
                category = 'mature'
            elif recency < 30:
                category = 'declining'
            else:
                category = 'growing'

            lifecycle[tag] = {
                'category': category,
                'count': count,
                'recency': recency
            }

        return lifecycle

    # ==================== Tag Entropy ====================

    def calculate_tag_entropy(self):
        """
        Энтропия тега - мера специфичности

        Высокая энтропия = тег используется в разных категориях (общий)
        Низкая энтропия = тег используется в одной категории (специфичный)
        """
        tag_categories = defaultdict(lambda: defaultdict(int))

        for article in self.articles:
            category = article.get('category', 'uncategorized')
            for tag in article['tags']:
                normalized = self.normalize_tag(tag)
                tag_categories[normalized][category] += 1

        entropies = {}

        for tag in tag_categories:
            counts = list(tag_categories[tag].values())
            total = sum(counts)

            # Shannon entropy
            entropy = 0
            for count in counts:
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)

            # Normalize to 0-100
            max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1
            normalized_entropy = (entropy / max_entropy * 100) if max_entropy > 0 else 0

            entropies[tag] = {
                'entropy': round(normalized_entropy, 2),
                'categories': dict(tag_categories[tag]),
                'interpretation': 'general' if normalized_entropy > 50 else 'specific'
            }

        return entropies

    # ==================== Semantic Clustering ====================

    def cluster_similar_tags(self, threshold=0.5):
        """
        Кластеризация похожих тегов

        Используем простую string similarity (Jaccard на буквах)
        """
        clusters = []
        tags = list(self.tag_stats.keys())
        visited = set()

        def jaccard_similarity(s1, s2):
            set1 = set(s1)
            set2 = set(s2)
            intersection = set1 & set2
            union = set1 | set2
            return len(intersection) / len(union) if union else 0.0

        for i, tag1 in enumerate(tags):
            if tag1 in visited:
                continue

            cluster = [tag1]
            visited.add(tag1)

            for tag2 in tags[i+1:]:
                if tag2 in visited:
                    continue

                similarity = jaccard_similarity(tag1, tag2)
                if similarity >= threshold:
                    cluster.append(tag2)
                    visited.add(tag2)

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    # ==================== Tag Coverage ====================

    def calculate_tag_coverage(self):
        """
        Метрики покрытия тегами

        - Сколько статей имеют теги
        - Среднее количество тегов на статью
        - Распределение количества тегов
        """
        total_articles = len(self.articles)
        tagged_articles = sum(1 for a in self.articles if a['tags'])
        untagged_articles = total_articles - tagged_articles

        tag_counts = [len(a['tags']) for a in self.articles]
        avg_tags = sum(tag_counts) / total_articles if total_articles > 0 else 0

        # Распределение
        distribution = Counter(tag_counts)

        coverage = {
            'total_articles': total_articles,
            'tagged_articles': tagged_articles,
            'untagged_articles': untagged_articles,
            'coverage_percent': round(tagged_articles / total_articles * 100, 2) if total_articles > 0 else 0,
            'avg_tags_per_article': round(avg_tags, 2),
            'tag_distribution': dict(distribution)
        }

        return coverage

    # ==================== Report Generation ====================

    def generate_statistics(self):
        """Общая статистика"""
        stats = {
            'total_unique_tags': len(self.tag_stats),
            'total_tag_usage': sum(t['count'] for t in self.tag_stats.values()),
            'avg_usage_per_tag': round(sum(t['count'] for t in self.tag_stats.values()) / len(self.tag_stats), 2) if self.tag_stats else 0
        }

        return stats

    def generate_report(self, format='markdown'):
        """Создать отчёт"""
        if format == 'json':
            return self.generate_json_report()
        else:
            return self.generate_markdown_report()

    def generate_markdown_report(self):
        """Markdown отчёт"""
        lines = []
        lines.append("# 🏷️ Advanced Tag Analytics Report\n\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Overall statistics
        stats = self.generate_statistics()
        coverage = self.calculate_tag_coverage()

        lines.append("## 📊 Summary Statistics\n\n")
        lines.append(f"- **Total unique tags**: {stats['total_unique_tags']}\n")
        lines.append(f"- **Total tag usage**: {stats['total_tag_usage']}\n")
        lines.append(f"- **Avg usage per tag**: {stats['avg_usage_per_tag']}\n")
        lines.append(f"- **Tagged articles**: {coverage['tagged_articles']} / {coverage['total_articles']} ({coverage['coverage_percent']}%)\n")
        lines.append(f"- **Avg tags per article**: {coverage['avg_tags_per_article']}\n\n")

        # Top tags by combined weight
        lines.append("## 🔝 Top 20 Tags (Multi-dimensional Weight)\n\n")
        sorted_tags = sorted(self.tag_stats.items(), key=lambda x: -x[1]['combined_weight'])

        for i, (tag, data) in enumerate(sorted_tags[:20], 1):
            lines.append(f"{i}. **{tag}** — Weight: {data['combined_weight']:.1f}/100 (used {data['count']}x)\n")
            lines.append(f"   - Frequency: {data['frequency_weight']:.1f} | ")
            lines.append(f"Recency: {data['recency_weight']:.1f} | ")
            lines.append(f"Importance: {data['importance_weight']:.1f} | ")
            lines.append(f"Specificity: {data['specificity']:.1f}\n")

        lines.append("\n")

        # Tag lifecycle
        lifecycle = self.analyze_tag_lifecycle()
        lifecycle_by_category = defaultdict(list)
        for tag, data in lifecycle.items():
            lifecycle_by_category[data['category']].append(tag)

        lines.append("## 🌱 Tag Lifecycle Analysis\n\n")
        for category in ['emerging', 'growing', 'mature', 'declining']:
            tags = lifecycle_by_category.get(category, [])
            if tags:
                emoji = {'emerging': '🌱', 'growing': '📈', 'mature': '🌳', 'declining': '📉'}[category]
                lines.append(f"### {emoji} {category.capitalize()} ({len(tags)} tags)\n\n")
                for tag in sorted(tags)[:10]:
                    lines.append(f"- {tag}\n")
                if len(tags) > 10:
                    lines.append(f"  ...and {len(tags) - 10} more\n")
                lines.append("\n")

        # Co-occurrence
        lines.append("## 🔗 Tag Co-occurrence (Top Pairs)\n\n")
        all_pairs = []
        for tag1 in self.co_occurrence:
            for tag2, count in self.co_occurrence[tag1].items():
                if tag1 < tag2:  # Avoid duplicates
                    all_pairs.append((tag1, tag2, count))

        all_pairs.sort(key=lambda x: -x[2])

        for tag1, tag2, count in all_pairs[:15]:
            lines.append(f"- **{tag1}** + **{tag2}** → {count} times\n")

        lines.append("\n")

        # Semantic clusters
        clusters = self.cluster_similar_tags(threshold=0.5)
        if clusters:
            lines.append(f"## 🎯 Similar Tag Clusters ({len(clusters)})\n\n")
            for i, cluster in enumerate(clusters[:10], 1):
                lines.append(f"{i}. {', '.join(f'`{t}`' for t in cluster)}\n")

        # Entropy (specificity)
        entropies = self.calculate_tag_entropy()
        specific_tags = [(t, e['entropy']) for t, e in entropies.items() if e['interpretation'] == 'specific']
        general_tags = [(t, e['entropy']) for t, e in entropies.items() if e['interpretation'] == 'general']

        lines.append(f"\n## 🎲 Tag Specificity (Entropy)\n\n")

        if specific_tags:
            lines.append(f"### Specific tags ({len(specific_tags)})\n\n")
            for tag, entropy in sorted(specific_tags, key=lambda x: x[1])[:10]:
                lines.append(f"- **{tag}** (entropy: {entropy:.1f})\n")

        if general_tags:
            lines.append(f"\n### General tags ({len(general_tags)})\n\n")
            for tag, entropy in sorted(general_tags, key=lambda x: -x[1])[:10]:
                lines.append(f"- **{tag}** (entropy: {entropy:.1f})\n")

        output_file = self.root_dir / "TAG_ANALYTICS_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown report: {output_file}")
        return output_file

    def generate_json_report(self):
        """JSON отчёт со всеми данными"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.generate_statistics(),
            'tag_weights': self.tag_stats,
            'co_occurrence': {k: dict(v) for k, v in self.co_occurrence.items()},
            'lifecycle': self.analyze_tag_lifecycle(),
            'entropy': self.calculate_tag_entropy(),
            'coverage': self.calculate_tag_coverage(),
            'semantic_clusters': self.cluster_similar_tags()
        }

        output_file = self.root_dir / "tag_analytics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON report: {output_file}")
        return output_file

    def generate_tag_cloud_html(self):
        """HTML облако тегов с весами"""
        if not self.tag_stats:
            return

        max_weight = max(t['combined_weight'] for t in self.tag_stats.values())
        min_weight = min(t['combined_weight'] for t in self.tag_stats.values())

        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Advanced Tag Cloud</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
        .tag-cloud { text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .tag { display: inline-block; margin: 8px; cursor: pointer; transition: 0.3s; color: #333; }
        .tag:hover { transform: scale(1.15); color: #007bff; }
        .tag-emerging { color: #28a745; }
        .tag-mature { color: #007bff; }
        .tag-declining { color: #dc3545; }
        h1 { text-align: center; color: #333; }
        .stats { text-align: center; color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🏷️ Advanced Tag Cloud</h1>
    <div class="stats">
"""

        stats = self.generate_statistics()
        html += f"        <p>{stats['total_unique_tags']} unique tags | {stats['total_tag_usage']} total uses</p>\n"
        html += "    </div>\n    <div class=\"tag-cloud\">\n"

        lifecycle = self.analyze_tag_lifecycle()

        for tag in sorted(self.tag_stats.keys()):
            weight = self.tag_stats[tag]['combined_weight']
            count = self.tag_stats[tag]['count']

            # Размер шрифта
            size = 12 + (weight - min_weight) / (max_weight - min_weight) * 36 if max_weight > min_weight else 20

            # CSS class на основе lifecycle
            category = lifecycle[tag]['category']
            css_class = f"tag tag-{category}"

            html += f'        <span class="{css_class}" style="font-size: {size}px;" '
            html += f'title="{tag}: {count} uses, weight {weight:.1f}, {category}">{tag}</span>\n'

        html += """    </div>
</body>
</html>
"""

        output_file = self.root_dir / "TAG_CLOUD_ADVANCED.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML tag cloud: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Advanced Tag Analytics')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Report format (default: markdown)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = AdvancedTagAnalyzer(root_dir)

    print("🏷️ Advanced Tag Analytics\n")
    print("   Scanning articles...")
    analyzer.scan_articles()
    print(f"   Found: {len(analyzer.articles)} articles\n")

    print("   Calculating multi-dimensional weights...")
    analyzer.calculate_multidimensional_weights()

    print("   Analyzing co-occurrence...")
    analyzer.calculate_tag_cooccurrence()

    print("   Generating reports...\n")
    analyzer.generate_report(format=args.format)
    analyzer.generate_tag_cloud_html()

    # Print summary
    stats = analyzer.generate_statistics()
    print(f"\n📊 Summary:")
    print(f"   Unique tags: {stats['total_unique_tags']}")
    print(f"   Total usage: {stats['total_tag_usage']}")
    print(f"   Avg per tag: {stats['avg_usage_per_tag']}")

    coverage = analyzer.calculate_tag_coverage()
    print(f"   Coverage: {coverage['coverage_percent']:.1f}%")
    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
