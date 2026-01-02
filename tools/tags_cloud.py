#!/usr/bin/env python3
"""
Tags Cloud - Облако тегов
Визуализация популярности тегов с различными размерами

Вдохновлено: WordPress tag clouds, Flickr tags
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json
import math


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


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = TagsCloudGenerator(root_dir)
    generator.collect_tags()

    size_classes = generator.calculate_size_classes()

    generator.generate_html_cloud(size_classes)
    generator.generate_markdown_report(size_classes)
    generator.save_json()


if __name__ == "__main__":
    main()
