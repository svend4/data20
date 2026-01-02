#!/usr/bin/env python3
"""
Master Index - Главный указатель
Создаёт полный алфавитный указатель всех терминов и концепций

Вдохновлено: Book index, Encyclopedia index
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class MasterIndexBuilder:
    """Построитель главного указателя"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Индекс: термин -> список статей
        self.index = defaultdict(list)

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

    def extract_terms(self, content):
        """Извлечь термины из контента"""
        terms = set()

        # Выделенные термины (**термин**)
        bold_terms = re.findall(r'\*\*([А-ЯA-Z][^\*]{2,40}?)\*\*', content)
        terms.update(bold_terms)

        # Термины из заголовков
        headings = re.findall(r'^#{2,6}\s+(.+)$', content, re.MULTILINE)
        terms.update(headings)

        return terms

    def build_index(self):
        """Построить индекс"""
        print("📇 Построение главного указателя...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Извлечь термины
            terms = self.extract_terms(content)

            # Добавить термины в индекс
            for term in terms:
                # Нормализация
                term_clean = term.strip()

                if len(term_clean) < 3:
                    continue

                # Добавить в индекс
                if article_path not in [a['path'] for a in self.index[term_clean]]:
                    self.index[term_clean].append({
                        'path': article_path,
                        'title': title
                    })

            # Добавить теги как термины
            if frontmatter and 'tags' in frontmatter:
                for tag in frontmatter['tags']:
                    if article_path not in [a['path'] for a in self.index[tag]]:
                        self.index[tag].append({
                            'path': article_path,
                            'title': title
                        })

        print(f"   Терминов в указателе: {len(self.index)}")
        print(f"   Ссылок: {sum(len(articles) for articles in self.index.values())}\n")

    def generate_master_index(self):
        """Создать главный указатель"""
        lines = []
        lines.append("# 📇 Главный указатель\n\n")
        lines.append("> Алфавитный указатель всех терминов и концепций\n\n")

        # Статистика
        lines.append("## Статистика\n\n")
        lines.append(f"- **Терминов**: {len(self.index)}\n")
        lines.append(f"- **Всего ссылок**: {sum(len(articles) for articles in self.index.values())}\n\n")

        # Группировать по первой букве
        by_letter = defaultdict(list)

        for term in sorted(self.index.keys(), key=str.lower):
            first_letter = term[0].upper()
            by_letter[first_letter].append(term)

        # Навигация
        lines.append("## Навигация\n\n")
        for letter in sorted(by_letter.keys()):
            lines.append(f"[{letter}](#{letter}) ")
        lines.append("\n\n")

        # Термины по буквам
        for letter in sorted(by_letter.keys()):
            lines.append(f"## {letter}\n\n")

            for term in sorted(by_letter[letter], key=str.lower):
                articles = self.index[term]

                lines.append(f"### {term}\n\n")

                for article in articles:
                    lines.append(f"- [{article['title']}]({article['path']})\n")

                lines.append("\n")

        output_file = self.root_dir / "MASTER_INDEX.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Главный указатель: {output_file}")

    def save_json(self):
        """Сохранить в JSON"""
        data = {
            'total_terms': len(self.index),
            'total_references': sum(len(articles) for articles in self.index.values()),
            'index': {
                term: articles
                for term, articles in sorted(self.index.items())
            }
        }

        output_file = self.root_dir / "master_index.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON индекс: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = MasterIndexBuilder(root_dir)
    builder.build_index()
    builder.generate_master_index()
    builder.save_json()

    print("\n🎉 ВСЕ 47 МЕТОДОВ РЕАЛИЗОВАНЫ!")


if __name__ == "__main__":
    main()
