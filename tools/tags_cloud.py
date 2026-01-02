#!/usr/bin/env python3
"""
Tags Cloud - Облако тегов
Визуализация популярности тегов с различными размерами

Вдохновлено: WordPress tag clouds, Flickr tags
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import math
import argparse
from typing import Dict, List, Tuple, Set
from itertools import combinations


class TagsCloudGenerator:
    """Генератор облака тегов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Статистика тегов
        self.tag_stats = defaultdict(lambda: {
            'count': 0,
            'articles': []
        })

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
        except:
            pass
        return None

    def collect_tags(self):
        """Собрать все теги"""
        print("🏷️  Сбор тегов...\n")

        total_articles = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)

            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem)
            tags = frontmatter.get('tags', [])

            if tags:
                total_articles += 1

                for tag in tags:
                    self.tag_stats[tag]['count'] += 1
                    self.tag_stats[tag]['articles'].append({
                        'path': article_path,
                        'title': title
                    })

        print(f"   Статей обработано: {total_articles}")
        print(f"   Уникальных тегов: {len(self.tag_stats)}\n")

    def calculate_size_classes(self):
        """Вычислить размерные классы для тегов"""
        if not self.tag_stats:
            return {}

        # Найти min и max
        counts = [data['count'] for data in self.tag_stats.values()]
        min_count = min(counts)
        max_count = max(counts)

        # Определить 5 размерных классов
        size_classes = {}

        for tag, data in self.tag_stats.items():
            count = data['count']

            # Логарифмическая шкала для лучшего распределения
            if max_count > min_count:
                normalized = (math.log(count) - math.log(min_count)) / (math.log(max_count) - math.log(min_count))
            else:
                normalized = 1.0

            # Классы: xs, sm, md, lg, xl
            if normalized <= 0.2:
                size_class = 'xs'
                size_px = 12
            elif normalized <= 0.4:
                size_class = 'sm'
                size_px = 16
            elif normalized <= 0.6:
                size_class = 'md'
                size_px = 20
            elif normalized <= 0.8:
                size_class = 'lg'
                size_px = 28
            else:
                size_class = 'xl'
                size_px = 36

            size_classes[tag] = {
                'class': size_class,
                'size': size_px,
                'weight': normalized
            }

        return size_classes

    def generate_html_cloud(self, size_classes):
        """Создать HTML облако тегов"""
        lines = []
        lines.append("<!DOCTYPE html>\n")
        lines.append("<html lang=\"ru\">\n")
        lines.append("<head>\n")
        lines.append("    <meta charset=\"UTF-8\">\n")
        lines.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n")
        lines.append("    <title>Tags Cloud</title>\n")
        lines.append("    <style>\n")
        lines.append("        body {\n")
        lines.append("            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n")
        lines.append("            max-width: 1200px;\n")
        lines.append("            margin: 40px auto;\n")
        lines.append("            padding: 20px;\n")
        lines.append("            background: #f5f5f5;\n")
        lines.append("        }\n")
        lines.append("        .container {\n")
        lines.append("            background: white;\n")
        lines.append("            padding: 40px;\n")
        lines.append("            border-radius: 10px;\n")
        lines.append("            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n")
        lines.append("        }\n")
        lines.append("        h1 {\n")
        lines.append("            text-align: center;\n")
        lines.append("            color: #333;\n")
        lines.append("            margin-bottom: 40px;\n")
        lines.append("        }\n")
        lines.append("        .cloud {\n")
        lines.append("            text-align: center;\n")
        lines.append("            line-height: 3;\n")
        lines.append("        }\n")
        lines.append("        .tag {\n")
        lines.append("            display: inline-block;\n")
        lines.append("            margin: 5px 10px;\n")
        lines.append("            padding: 5px 15px;\n")
        lines.append("            text-decoration: none;\n")
        lines.append("            color: #0066cc;\n")
        lines.append("            transition: all 0.3s;\n")
        lines.append("            border-radius: 5px;\n")
        lines.append("        }\n")
        lines.append("        .tag:hover {\n")
        lines.append("            background: #0066cc;\n")
        lines.append("            color: white;\n")
        lines.append("            transform: scale(1.1);\n")
        lines.append("        }\n")
        lines.append("        .tag.xs { font-size: 12px; opacity: 0.6; }\n")
        lines.append("        .tag.sm { font-size: 16px; opacity: 0.7; }\n")
        lines.append("        .tag.md { font-size: 20px; opacity: 0.8; }\n")
        lines.append("        .tag.lg { font-size: 28px; opacity: 0.9; }\n")
        lines.append("        .tag.xl { font-size: 36px; opacity: 1.0; font-weight: bold; }\n")
        lines.append("        .stats {\n")
        lines.append("            margin-top: 40px;\n")
        lines.append("            padding-top: 20px;\n")
        lines.append("            border-top: 1px solid #eee;\n")
        lines.append("            text-align: center;\n")
        lines.append("            color: #666;\n")
        lines.append("        }\n")
        lines.append("    </style>\n")
        lines.append("</head>\n")
        lines.append("<body>\n")
        lines.append("    <div class=\"container\">\n")
        lines.append("        <h1>🏷️ Tags Cloud</h1>\n")
        lines.append("        <div class=\"cloud\">\n")

        # Сортировать теги по популярности для визуального эффекта
        sorted_tags = sorted(self.tag_stats.items(), key=lambda x: -x[1]['count'])

        for tag, data in sorted_tags:
            size_info = size_classes[tag]
            count = data['count']

            lines.append(f"            <a href=\"#{tag}\" class=\"tag {size_info['class']}\" ")
            lines.append(f"title=\"{count} статей\">{tag}</a>\n")

        lines.append("        </div>\n")
        lines.append(f"        <div class=\"stats\">\n")
        lines.append(f"            📊 Всего тегов: {len(self.tag_stats)} | ")
        lines.append(f"📚 Всего статей: {sum(len(d['articles']) for d in self.tag_stats.values())}\n")
        lines.append(f"        </div>\n")
        lines.append("    </div>\n")
        lines.append("</body>\n")
        lines.append("</html>\n")

        output_file = self.root_dir / "tags_cloud.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ HTML облако: {output_file}")

    def generate_markdown_report(self, size_classes):
        """Создать markdown отчёт"""
        lines = []
        lines.append("# 🏷️ Tags Cloud — Облако тегов\n\n")
        lines.append("> Визуализация популярности тегов в базе знаний\n\n")

        # Статистика
        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего тегов**: {len(self.tag_stats)}\n")
        lines.append(f"- **Всего использований**: {sum(d['count'] for d in self.tag_stats.values())}\n")

        # Топ тегов
        lines.append("\n## Топ-20 популярных тегов\n\n")
        lines.append("| # | Тег | Использований | Размер |\n")
        lines.append("|---|-----|---------------|--------|\n")

        sorted_tags = sorted(self.tag_stats.items(), key=lambda x: -x[1]['count'])

        for i, (tag, data) in enumerate(sorted_tags[:20], 1):
            size_info = size_classes[tag]
            size_visual = '█' * int(size_info['weight'] * 10)

            lines.append(f"| {i} | **{tag}** | {data['count']} | {size_visual} |\n")

        # Все теги по категориям размера
        lines.append("\n## Все теги по популярности\n\n")

        for size_label, size_name in [('xl', 'Очень популярные'), ('lg', 'Популярные'),
                                      ('md', 'Средние'), ('sm', 'Редкие'), ('xs', 'Очень редкие')]:
            tags_in_size = [(tag, data) for tag, data in self.tag_stats.items()
                           if size_classes[tag]['class'] == size_label]

            if tags_in_size:
                lines.append(f"### {size_name} ({len(tags_in_size)})\n\n")

                for tag, data in sorted(tags_in_size, key=lambda x: -x[1]['count']):
                    lines.append(f"- **{tag}** ({data['count']}) — ")

                    # Показать первые 3 статьи
                    article_titles = [a['title'] for a in data['articles'][:3]]
                    lines.append(", ".join(article_titles))

                    if len(data['articles']) > 3:
                        lines.append(f" и ещё {len(data['articles']) - 3}")

                    lines.append("\n")

                lines.append("\n")

        # Детали по каждому тегу
        lines.append("\n## Детальная информация\n\n")

        for tag in sorted(self.tag_stats.keys()):
            data = self.tag_stats[tag]

            lines.append(f"### {tag}\n\n")
            lines.append(f"**Использований**: {data['count']}\n\n")
            lines.append("**Статьи:**\n\n")

            for article in data['articles']:
                lines.append(f"- [{article['title']}]({article['path']})\n")

            lines.append("\n")

        output_file = self.root_dir / "TAGS_CLOUD.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown отчёт: {output_file}")

    def save_json(self):
        """Сохранить данные в JSON"""
        data = {
            'total_tags': len(self.tag_stats),
            'total_uses': sum(d['count'] for d in self.tag_stats.values()),
            'tags': {
                tag: {
                    'count': data['count'],
                    'articles': data['articles']
                }
                for tag, data in self.tag_stats.items()
            },
            'top_tags': [
                {'tag': tag, 'count': data['count']}
                for tag, data in sorted(self.tag_stats.items(), key=lambda x: -x[1]['count'])[:20]
            ]
        }

        output_file = self.root_dir / "tags_cloud.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")


class TagStatisticsAnalyzer:
    """Продвинутый анализ статистики тегов"""

    def __init__(self, tag_stats: Dict):
        self.tag_stats = tag_stats

    def calculate_co_occurrence(self) -> Dict[Tuple[str, str], int]:
        """Вычислить совместную встречаемость тегов (co-occurrence matrix)"""
        co_occurrence = Counter()

        # Собрать все комбинации тегов из каждой статьи
        article_tags = defaultdict(set)

        for tag, data in self.tag_stats.items():
            for article in data['articles']:
                article_tags[article['path']].add(tag)

        # Подсчитать пары
        for tags in article_tags.values():
            if len(tags) >= 2:
                for tag1, tag2 in combinations(sorted(tags), 2):
                    co_occurrence[(tag1, tag2)] += 1

        return dict(co_occurrence)

    def find_tag_clusters(self, min_co_occurrence: int = 2) -> List[Set[str]]:
        """Найти кластеры связанных тегов"""
        co_occ = self.calculate_co_occurrence()

        # Построить граф связей
        graph = defaultdict(set)

        for (tag1, tag2), count in co_occ.items():
            if count >= min_co_occurrence:
                graph[tag1].add(tag2)
                graph[tag2].add(tag1)

        # Найти связные компоненты через BFS
        visited = set()
        clusters = []

        def bfs(start):
            cluster = set()
            queue = [start]
            visited.add(start)

            while queue:
                node = queue.pop(0)
                cluster.add(node)

                for neighbor in graph.get(node, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            return cluster

        for tag in graph:
            if tag not in visited:
                cluster = bfs(tag)
                if len(cluster) > 1:
                    clusters.append(cluster)

        return clusters

    def calculate_tag_diversity(self) -> float:
        """
        Вычислить разнообразие тегов (Shannon Entropy)

        H = -Σ(p(tag) × log2(p(tag)))
        """
        total = sum(d['count'] for d in self.tag_stats.values())
        if total == 0:
            return 0.0

        entropy = 0.0

        for data in self.tag_stats.values():
            p = data['count'] / total
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy


class TagNormalizer:
    """Нормализация тегов (lowercase, plurals, synonyms)"""

    # Общие правила плюрализации (упрощённо)
    PLURAL_RULES = {
        's': '',
        'es': '',
        'ies': 'y'
    }

    @staticmethod
    def normalize(tag: str) -> str:
        """Нормализовать тег"""
        # Lowercase
        normalized = tag.lower().strip()

        # Remove extra spaces
        normalized = ' '.join(normalized.split())

        return normalized

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """
        Вычислить расстояние Левенштейна

        Dynamic Programming: O(m×n)
        """
        if len(s1) < len(s2):
            return TagNormalizer.levenshtein_distance(s2, s1)

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

    @staticmethod
    def find_similar_tags(tags: List[str], threshold: int = 2) -> Dict[str, List[str]]:
        """Найти похожие теги (расстояние Левенштейна <= threshold)"""
        similar = defaultdict(list)

        for i, tag1 in enumerate(tags):
            for tag2 in tags[i + 1:]:
                dist = TagNormalizer.levenshtein_distance(tag1, tag2)
                if dist <= threshold:
                    similar[tag1].append(tag2)
                    similar[tag2].append(tag1)

        return dict(similar)


class TagRecommender:
    """Рекомендатель тегов"""

    def __init__(self, tag_stats: Dict):
        self.tag_stats = tag_stats
        self.analyzer = TagStatisticsAnalyzer(tag_stats)

    def recommend_tags(self, existing_tags: List[str], limit: int = 5) -> List[Tuple[str, float]]:
        """
        Рекомендовать теги на основе уже существующих

        Используется co-occurrence matrix
        """
        co_occ = self.analyzer.calculate_co_occurrence()

        recommendations = Counter()

        for tag in existing_tags:
            if tag in self.tag_stats:
                # Найти теги, которые часто встречаются вместе
                for (tag1, tag2), count in co_occ.items():
                    if tag1 == tag and tag2 not in existing_tags:
                        recommendations[tag2] += count
                    elif tag2 == tag and tag1 not in existing_tags:
                        recommendations[tag1] += count

        # Нормализовать по частоте
        total = sum(recommendations.values())

        if total == 0:
            return []

        scored_recs = [(tag, count / total) for tag, count in recommendations.items()]

        return sorted(scored_recs, key=lambda x: x[1], reverse=True)[:limit]

    def get_popular_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Получить топ популярных тегов"""
        return sorted(
            [(tag, data['count']) for tag, data in self.tag_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:limit]


class InteractiveCloudGenerator:
    """Генератор интерактивного облака с D3.js"""

    @staticmethod
    def generate_d3_cloud(tag_stats: Dict, size_classes: Dict) -> str:
        """Генерировать D3.js облако тегов"""
        # Подготовить данные
        tag_data = []

        for tag, data in tag_stats.items():
            size_info = size_classes[tag]
            tag_data.append({
                'text': tag,
                'size': size_info['size'],
                'count': data['count'],
                'weight': size_info['weight']
            })

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Tags Cloud</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 40px;
            max-width: 1200px;
            margin: 0 auto;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        #cloud {{
            text-align: center;
            min-height: 400px;
            padding: 20px;
        }}
        .tag {{
            cursor: pointer;
            transition: all 0.3s;
            display: inline-block;
            margin: 5px;
            padding: 8px 16px;
            border-radius: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            opacity: 0.8;
        }}
        .tag:hover {{
            opacity: 1;
            transform: scale(1.2);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        #info {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 10px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 14px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏷️ Interactive Tags Cloud</h1>
        <p class="subtitle">Click on tags to see details</p>
        <div id="cloud"></div>
        <div id="info"></div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(tag_stats)}</div>
                <div class="stat-label">Unique Tags</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(d['count'] for d in tag_stats.values())}</div>
                <div class="stat-label">Total Uses</div>
            </div>
        </div>
    </div>
    <script>
        const tags = {json.dumps(tag_data, ensure_ascii=False)};

        const cloud = d3.select('#cloud');

        tags.forEach(tag => {{
            cloud.append('span')
                .attr('class', 'tag')
                .style('font-size', tag.size + 'px')
                .text(tag.text)
                .on('click', function() {{
                    d3.select('#info').html(
                        `<strong>${{tag.text}}</strong>: используется ${{tag.count}} раз (вес: ${{(tag.weight * 100).toFixed(1)}}%)`
                    );
                }});
        }});
    </script>
</body>
</html>"""

        return html


def main():
    parser = argparse.ArgumentParser(
        description='🏷️ Tags Cloud - Облако тегов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --generate              # Генерировать все форматы (HTML, Markdown, JSON)
  %(prog)s --analyze               # Продвинутый анализ тегов
  %(prog)s --recommend python ai   # Рекомендовать теги на основе существующих
  %(prog)s --similar               # Найти похожие теги
  %(prog)s --interactive           # Генерировать интерактивное D3.js облако
  %(prog)s --clusters              # Найти кластеры связанных тегов
        """
    )

    parser.add_argument('--generate', action='store_true',
                        help='Генерировать облако тегов (все форматы)')
    parser.add_argument('--analyze', action='store_true',
                        help='Продвинутый анализ тегов')
    parser.add_argument('--recommend', type=str, nargs='+', metavar='TAG',
                        help='Рекомендовать теги на основе существующих')
    parser.add_argument('--similar', action='store_true',
                        help='Найти похожие теги (Levenshtein distance)')
    parser.add_argument('--interactive', action='store_true',
                        help='Генерировать интерактивное D3.js облако')
    parser.add_argument('--clusters', action='store_true',
                        help='Найти кластеры связанных тегов')
    parser.add_argument('--output', type=str,
                        help='Выходной файл')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Если аргументы не указаны, показать help
    if not any(vars(args).values()):
        parser.print_help()
        return

    generator = TagsCloudGenerator(root_dir)
    generator.collect_tags()

    tag_stats = generator.tag_stats
    size_classes = generator.calculate_size_classes()

    # --generate: стандартная генерация
    if args.generate:
        print("🎨 Генерация облака тегов...\n")
        generator.generate_html_cloud(size_classes)
        generator.generate_markdown_report(size_classes)
        generator.save_json()

    # --analyze: продвинутый анализ
    if args.analyze:
        print("📊 Продвинутый анализ тегов...\n")
        analyzer = TagStatisticsAnalyzer(tag_stats)

        # Shannon Entropy
        diversity = analyzer.calculate_tag_diversity()
        print(f"## Разнообразие тегов (Shannon Entropy)\n")
        print(f"   H = {diversity:.4f} bits")
        print(f"   (max: {math.log2(len(tag_stats)):.4f} bits при равномерном распределении)\n")

        # Co-occurrence
        co_occ = analyzer.calculate_co_occurrence()
        print(f"## Совместная встречаемость (топ-10 пар)\n")

        top_co_occ = sorted(co_occ.items(), key=lambda x: x[1], reverse=True)[:10]
        for (tag1, tag2), count in top_co_occ:
            print(f"   {tag1} + {tag2}: {count} раз")
        print()

        # Tag clusters
        clusters = analyzer.find_tag_clusters(min_co_occurrence=1)
        print(f"## Кластеры связанных тегов\n")
        print(f"   Найдено кластеров: {len(clusters)}\n")
        for i, cluster in enumerate(sorted(clusters, key=len, reverse=True)[:5], 1):
            print(f"   {i}. {', '.join(sorted(cluster))} ({len(cluster)} тегов)")
        print()

    # --recommend: рекомендации тегов
    if args.recommend:
        existing_tags = args.recommend
        print(f"💡 Рекомендации на основе: {', '.join(existing_tags)}\n")

        recommender = TagRecommender(tag_stats)
        recommendations = recommender.recommend_tags(existing_tags, limit=10)

        if recommendations:
            print("Рекомендуемые теги:\n")
            for i, (tag, score) in enumerate(recommendations, 1):
                print(f"   {i}. {tag} (релевантность: {score:.2%})")
        else:
            print("   Нет рекомендаций (теги не найдены или нет совместных упоминаний)")
        print()

    # --similar: похожие теги
    if args.similar:
        print("🔍 Поиск похожих тегов (Levenshtein distance ≤ 2)...\n")

        all_tags = list(tag_stats.keys())
        similar = TagNormalizer.find_similar_tags(all_tags, threshold=2)

        if similar:
            print(f"Найдено похожих пар: {len(similar)}\n")
            for tag, similar_tags in sorted(similar.items())[:10]:
                print(f"   {tag} → {', '.join(similar_tags)}")
        else:
            print("   Похожих тегов не найдено")
        print()

    # --interactive: интерактивное облако
    if args.interactive:
        print("🎨 Генерация интерактивного D3.js облака...\n")

        html = InteractiveCloudGenerator.generate_d3_cloud(tag_stats, size_classes)

        output_file = args.output or root_dir / "tags_cloud_interactive.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Интерактивное облако: {output_file}")

    # --clusters: кластеры тегов
    if args.clusters:
        print("🔍 Поиск кластеров тегов...\n")

        analyzer = TagStatisticsAnalyzer(tag_stats)
        clusters = analyzer.find_tag_clusters(min_co_occurrence=1)

        print(f"Найдено кластеров: {len(clusters)}\n")

        for i, cluster in enumerate(sorted(clusters, key=len, reverse=True), 1):
            print(f"## Кластер {i} ({len(cluster)} тегов)\n")
            print(f"   Теги: {', '.join(sorted(cluster))}\n")

            # Показать статьи, которые используют эти теги
            articles_with_cluster = set()
            for tag in cluster:
                for article in tag_stats[tag]['articles']:
                    articles_with_cluster.add(article['title'])

            print(f"   Статей использующих эти теги: {len(articles_with_cluster)}\n")


if __name__ == "__main__":
    main()
