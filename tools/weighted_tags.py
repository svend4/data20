#!/usr/bin/env python3
"""
Weighted Tags - Взвешенные теги
Вычисляет важность/вес тегов на основе частоты использования

Веса используются для:
- Облака тегов
- Приоритизации в поиске
- Выявления ключевых тем базы знаний
"""

from pathlib import Path
import yaml
import re
import json
from collections import Counter
import math


class WeightedTagsAnalyzer:
    """Анализатор взвешенных тегов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

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

    def calculate_weights(self):
        """Вычислить веса тегов"""
        tag_counts = Counter()
        tag_articles = {}
        total_articles = 0

        # Собрать статистику
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)
            if not frontmatter:
                continue

            total_articles += 1
            tags = frontmatter.get('tags', [])

            for tag in tags:
                tag_counts[tag] += 1
                if tag not in tag_articles:
                    tag_articles[tag] = []
                tag_articles[tag].append(str(md_file.relative_to(self.root_dir)))

        # Вычислить веса (TF-IDF подобный подход)
        tag_weights = {}

        for tag, count in tag_counts.items():
            # TF: частота тега
            tf = count

            # IDF: обратная частота документа (для нормализации)
            # Чем реже тег, тем он специфичнее
            idf = math.log(total_articles / count) if count > 0 else 0

            # Вес = TF * IDF (но можно использовать просто count)
            # Для облака тегов используем простой count
            weight = count

            tag_weights[tag] = {
                'count': count,
                'weight': weight,
                'idf': round(idf, 3),
                'articles': tag_articles[tag]
            }

        return tag_weights

    def save_weights(self, tag_weights):
        """Сохранить веса"""
        output_file = self.root_dir / "tag_weights.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tag_weights, f, ensure_ascii=False, indent=2)

        print(f"✅ Веса тегов сохранены: {output_file}")

    def generate_tag_cloud_html(self, tag_weights):
        """Создать HTML облако тегов"""
        # Нормализовать веса для размеров шрифта (10-40px)
        max_weight = max(w['weight'] for w in tag_weights.values())
        min_weight = min(w['weight'] for w in tag_weights.values())

        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tag Cloud</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
        .tag-cloud { text-align: center; background: white; padding: 40px; border-radius: 10px; }
        .tag { display: inline-block; margin: 5px; cursor: pointer; transition: 0.3s; }
        .tag:hover { transform: scale(1.1); color: #007bff; }
    </style>
</head>
<body>
    <h1 style="text-align: center;">🏷️ Tag Cloud</h1>
    <div class="tag-cloud">
"""

        for tag in sorted(tag_weights.keys()):
            weight = tag_weights[tag]['weight']
            # Размер шрифта пропорционален весу
            size = 10 + (weight - min_weight) / (max_weight - min_weight) * 30 if max_weight > min_weight else 20
            html += f'        <span class="tag" style="font-size: {size}px;" title="{weight} articles">{tag}</span>\n'

        html += """    </div>
</body>
</html>
"""

        output_file = self.root_dir / "TAG_CLOUD.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML облако тегов: {output_file}")

    def generate_report(self, tag_weights):
        """Создать отчёт"""
        lines = []
        lines.append("# 🏷️ Отчёт: Взвешенные теги\n\n")

        total_tags = len(tag_weights)
        total_usage = sum(w['count'] for w in tag_weights.values())

        lines.append(f"- **Всего уникальных тегов**: {total_tags}\n")
        lines.append(f"- **Общее использование**: {total_usage}\n")
        lines.append(f"- **Среднее на тег**: {total_usage / total_tags:.1f}\n\n")

        # Топ тегов
        lines.append("## Топ-20 самых используемых тегов\n\n")

        sorted_tags = sorted(tag_weights.items(), key=lambda x: -x[1]['count'])

        for i, (tag, data) in enumerate(sorted_tags[:20], 1):
            pct = (data['count'] / total_usage) * 100
            bar = '█' * int(pct * 2)
            lines.append(f"{i}. **{tag}** — {data['count']} раз ({pct:.1f}%) {bar}\n")

        # Редкие теги
        lines.append("\n## Редкие теги (используются 1 раз)\n\n")
        rare_tags = [tag for tag, data in tag_weights.items() if data['count'] == 1]
        if rare_tags:
            lines.append(f"Найдено {len(rare_tags)} редких тегов:\n\n")
            for tag in sorted(rare_tags)[:20]:
                lines.append(f"- {tag}\n")
            if len(rare_tags) > 20:
                lines.append(f"\n...и ещё {len(rare_tags) - 20}\n")
        else:
            lines.append("Нет редких тегов - все используются минимум 2 раза!\n")

        output_file = self.root_dir / "TAG_WEIGHTS_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = WeightedTagsAnalyzer(root_dir)

    print("🏷️ Вычисление весов тегов...\n")

    tag_weights = analyzer.calculate_weights()

    print(f"   Найдено тегов: {len(tag_weights)}\n")

    analyzer.save_weights(tag_weights)
    analyzer.generate_tag_cloud_html(tag_weights)
    analyzer.generate_report(tag_weights)


if __name__ == "__main__":
    main()
