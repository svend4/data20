#!/usr/bin/env python3
"""
Cross-References - Перекрестные ссылки
Создаёт систему "См.", "См. также", "См. раздел"

Автоматически находит и добавляет связанные статьи
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict


class CrossReferencesBuilder:
    """Построитель перекрестных ссылок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.xrefs = defaultdict(lambda: {'see': [], 'see_also': [], 'see_section': []})

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

    def build_xrefs(self):
        """Построить перекрестные ссылки"""
        print("🔗 Построение перекрестных ссылок...\n")

        # Собрать все статьи с тегами
        articles_by_tag = defaultdict(list)
        articles_by_category = defaultdict(list)
        all_articles = {}

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)
            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem)
            tags = frontmatter.get('tags', [])
            category = frontmatter.get('category', '')
            subcategory = frontmatter.get('subcategory', '')

            all_articles[article_path] = {
                'title': title,
                'tags': tags,
                'category': category,
                'subcategory': subcategory
            }

            # Индексировать по тегам
            for tag in tags:
                articles_by_tag[tag].append(article_path)

            # Индексировать по категориям
            key = f"{category}/{subcategory}" if subcategory else category
            articles_by_category[key].append(article_path)

        # Построить перекрестные ссылки
        for article_path, data in all_articles.items():
            tags = data['tags']
            category = data['category']
            subcategory = data['subcategory']

            # "См. также" - статьи с общими тегами
            related = set()
            for tag in tags:
                for other in articles_by_tag[tag]:
                    if other != article_path:
                        related.add(other)

            # Сортировать по количеству общих тегов
            tag_overlap = {}
            for other in related:
                common_tags = set(tags) & set(all_articles[other]['tags'])
                tag_overlap[other] = len(common_tags)

            see_also = sorted(related, key=lambda x: -tag_overlap[x])[:5]
            self.xrefs[article_path]['see_also'] = see_also

            # "См. раздел" - статьи в той же подкатегории
            if subcategory:
                key = f"{category}/{subcategory}"
                see_section = [a for a in articles_by_category[key] if a != article_path]
                self.xrefs[article_path]['see_section'] = see_section[:3]

        print(f"   Обработано статей: {len(all_articles)}")

    def generate_markdown_xrefs(self, article_path):
        """Создать markdown для перекрестных ссылок"""
        xrefs = self.xrefs[article_path]

        lines = []
        lines.append("---\n\n")
        lines.append("## Перекрестные ссылки\n\n")

        # См. также
        if xrefs['see_also']:
            lines.append("### См. также\n\n")
            for related in xrefs['see_also']:
                # Получить заголовок
                frontmatter = self.extract_frontmatter(self.root_dir / related)
                title = frontmatter.get('title', Path(related).stem) if frontmatter else Path(related).stem

                # Относительная ссылка
                rel_path = Path(related).relative_to(Path(article_path).parent)

                lines.append(f"- [{title}]({rel_path})\n")

            lines.append("\n")

        # См. раздел
        if xrefs['see_section']:
            lines.append("### См. раздел\n\n")
            for section in xrefs['see_section']:
                frontmatter = self.extract_frontmatter(self.root_dir / section)
                title = frontmatter.get('title', Path(section).stem) if frontmatter else Path(section).stem

                rel_path = Path(section).relative_to(Path(article_path).parent)

                lines.append(f"- [{title}]({rel_path})\n")

            lines.append("\n")

        return ''.join(lines) if (xrefs['see_also'] or xrefs['see_section']) else ""

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Отчёт: Перекрестные ссылки\n\n")

        lines.append(f"**Статей с перекрестными ссылками**: {len(self.xrefs)}\n\n")

        # Статистика
        see_also_count = sum(1 for x in self.xrefs.values() if x['see_also'])
        see_section_count = sum(1 for x in self.xrefs.values() if x['see_section'])

        lines.append(f"- **Со ссылками \"См. также\"**: {see_also_count}\n")
        lines.append(f"- **Со ссылками \"См. раздел\"**: {see_section_count}\n\n")

        # Примеры
        lines.append("## Примеры\n\n")

        for article_path in sorted(self.xrefs.keys())[:5]:
            frontmatter = self.extract_frontmatter(self.root_dir / article_path)
            title = frontmatter.get('title', Path(article_path).stem) if frontmatter else Path(article_path).stem

            lines.append(f"### {title}\n\n")
            lines.append(f"`{article_path}`\n\n")

            xref_md = self.generate_markdown_xrefs(article_path)
            if xref_md:
                lines.append(xref_md)

        output_file = self.root_dir / "CROSS_REFERENCES_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = CrossReferencesBuilder(root_dir)
    builder.build_xrefs()
    builder.generate_report()


if __name__ == "__main__":
    main()
