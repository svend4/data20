#!/usr/bin/env python3
"""
Commonplace Book - Книга выписок
Извлекает ключевые цитаты, важные мысли и памятные отрывки

Вдохновлено: Renaissance commonplace books (15-17 века)
Традиция: John Locke, Marcus Aurelius, Thomas Jefferson
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class CommonplaceBookBuilder:
    """Построитель книги выписок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Выписки по категориям
        self.excerpts = defaultdict(list)

        # Статистика
        self.total_excerpts = 0

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

    def extract_excerpts(self, content, source_file):
        """Извлечь выписки из контента"""
        excerpts = []

        # 1. Блочные цитаты (> текст)
        blockquotes = re.findall(r'^>\s+(.+)$', content, re.MULTILINE)
        for quote in blockquotes:
            if len(quote) > 20:  # Минимальная длина
                excerpts.append({
                    'text': quote.strip(),
                    'type': 'quote',
                    'source': source_file
                })

        # 2. Выделенный текст (**важно**, *важно*)
        important = re.findall(r'\*\*([^*]{20,}?)\*\*', content)
        for text in important:
            # Исключить заголовки
            if not text.isupper() and ':' not in text[:20]:
                excerpts.append({
                    'text': text.strip(),
                    'type': 'important',
                    'source': source_file
                })

        # 3. Ключевые фразы (паттерны)
        key_patterns = [
            r'Важно понимать[,:]\s*(.{30,200}?)[.!]',
            r'Ключевая идея[,:]\s*(.{30,200}?)[.!]',
            r'Главное[,:]\s*(.{30,200}?)[.!]',
            r'Необходимо помнить[,:]\s*(.{30,200}?)[.!]',
            r'Следует отметить[,:]\s*(.{30,200}?)[.!]'
        ]

        for pattern in key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                excerpts.append({
                    'text': match.strip(),
                    'type': 'key_idea',
                    'source': source_file
                })

        # 4. Списки принципов/правил
        principle_patterns = [
            r'^[-*]\s+\*\*(.+?)\*\*\s*[-—–]\s*(.+)$',
            r'^\d+\.\s+\*\*(.+?)\*\*\s*[-—–]\s*(.+)$'
        ]

        for pattern in principle_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for title, description in matches:
                if len(description) > 20:
                    excerpts.append({
                        'text': f"{title}: {description}",
                        'type': 'principle',
                        'source': source_file
                    })

        # 5. Определения терминов
        definitions = re.findall(r'\*\*([А-ЯA-Z][^*]+?)\*\*\s*[-—–]\s*([^.\n]{20,200}?)[.]', content)
        for term, definition in definitions:
            excerpts.append({
                'text': f"{term} — {definition}",
                'type': 'definition',
                'source': source_file
            })

        # 6. Примеры (Example:, Пример:)
        examples = re.findall(r'(?:Example|Пример)[:\s]+(.{50,300}?)(?:\n\n|\n(?=[A-ZА-Я]))', content, re.IGNORECASE)
        for example in examples:
            excerpts.append({
                'text': example.strip(),
                'type': 'example',
                'source': source_file
            })

        return excerpts

    def build_commonplace_book(self):
        """Построить книгу выписок"""
        print("📖 Построение книги выписок...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            category = frontmatter.get('category', 'Общее') if frontmatter else 'Общее'
            tags = frontmatter.get('tags', []) if frontmatter else []

            # Извлечь выписки
            excerpts = self.extract_excerpts(content, article_path)

            for excerpt in excerpts:
                excerpt['article_title'] = title
                excerpt['category'] = category
                excerpt['tags'] = tags

                # Группировать по категориям
                self.excerpts[category].append(excerpt)
                self.total_excerpts += 1

        print(f"   Выписок собрано: {self.total_excerpts}")
        print(f"   Категорий: {len(self.excerpts)}\n")

    def generate_report(self):
        """Создать книгу выписок"""
        lines = []
        lines.append("# 📖 Commonplace Book — Книга выписок\n\n")
        lines.append("> Собрание ключевых мыслей, цитат и идей из базы знаний\n\n")
        lines.append("*Вдохновлено традицией Renaissance commonplace books*\n\n")

        # Статистика
        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего выписок**: {self.total_excerpts}\n")
        lines.append(f"- **Категорий**: {len(self.excerpts)}\n\n")

        # Типы выписок
        type_counts = defaultdict(int)
        for category_excerpts in self.excerpts.values():
            for excerpt in category_excerpts:
                type_counts[excerpt['type']] += 1

        lines.append("**По типам:**\n\n")
        type_names = {
            'quote': 'Цитаты',
            'important': 'Важные мысли',
            'key_idea': 'Ключевые идеи',
            'principle': 'Принципы',
            'definition': 'Определения',
            'example': 'Примеры'
        }

        for excerpt_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            name = type_names.get(excerpt_type, excerpt_type)
            lines.append(f"- **{name}**: {count}\n")

        lines.append("\n---\n\n")

        # Выписки по категориям
        for category in sorted(self.excerpts.keys()):
            excerpts = self.excerpts[category]

            lines.append(f"## {category}\n\n")
            lines.append(f"*{len(excerpts)} выписок*\n\n")

            # Группировать по типам
            by_type = defaultdict(list)
            for excerpt in excerpts:
                by_type[excerpt['type']].append(excerpt)

            for excerpt_type in ['quote', 'key_idea', 'important', 'principle', 'definition', 'example']:
                if excerpt_type not in by_type:
                    continue

                type_name = type_names.get(excerpt_type, excerpt_type)
                lines.append(f"### {type_name}\n\n")

                for excerpt in by_type[excerpt_type][:10]:  # Топ-10 по типу
                    lines.append(f"> {excerpt['text']}\n\n")
                    lines.append(f"— *[{excerpt['article_title']}]({excerpt['source']})*\n\n")

                if len(by_type[excerpt_type]) > 10:
                    lines.append(f"*...и ещё {len(by_type[excerpt_type]) - 10}*\n\n")

            lines.append("\n")

        output_file = self.root_dir / "COMMONPLACE_BOOK.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Книга выписок: {output_file}")

    def generate_by_topic(self):
        """Создать указатель по темам"""
        lines = []
        lines.append("# 📚 Выписки по темам\n\n")

        # Собрать все теги
        all_tags = defaultdict(list)

        for category_excerpts in self.excerpts.values():
            for excerpt in category_excerpts:
                for tag in excerpt['tags']:
                    all_tags[tag].append(excerpt)

        # Вывести по тегам
        for tag in sorted(all_tags.keys()):
            excerpts = all_tags[tag]

            lines.append(f"## {tag}\n\n")
            lines.append(f"*{len(excerpts)} выписок*\n\n")

            for excerpt in excerpts[:15]:
                lines.append(f"> {excerpt['text'][:150]}{'...' if len(excerpt['text']) > 150 else ''}\n\n")
                lines.append(f"— *[{excerpt['article_title']}]({excerpt['source']})*\n\n")

            if len(excerpts) > 15:
                lines.append(f"*...и ещё {len(excerpts) - 15}*\n\n")

            lines.append("\n")

        output_file = self.root_dir / "EXCERPTS_BY_TOPIC.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Выписки по темам: {output_file}")

    def save_json(self):
        """Сохранить выписки в JSON"""
        data = {
            'total': self.total_excerpts,
            'categories': {}
        }

        for category, excerpts in self.excerpts.items():
            data['categories'][category] = [
                {
                    'text': e['text'],
                    'type': e['type'],
                    'source': e['source'],
                    'article_title': e['article_title'],
                    'tags': e['tags']
                }
                for e in excerpts
            ]

        output_file = self.root_dir / "commonplace_book.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = CommonplaceBookBuilder(root_dir)
    builder.build_commonplace_book()
    builder.generate_report()
    builder.generate_by_topic()
    builder.save_json()


if __name__ == "__main__":
    main()
