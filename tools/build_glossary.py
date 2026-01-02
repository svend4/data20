#!/usr/bin/env python3
"""
Glossary Builder - Построитель глоссария
Создаёт словарь специальных терминов с определениями

Автоматически извлекает:
- Термины в жирном шрифте с определениями
- Термины из тезауруса
- Аббревиатуры
"""

from pathlib import Path
import re
import json


class GlossaryBuilder:
    """Построитель глоссария"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.glossary = {}

    def extract_content(self, file_path):
        """Извлечь содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n.*?\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def extract_definitions(self, content):
        """Извлечь определения терминов"""
        definitions = []

        # Паттерн: **Термин** — определение
        pattern1 = r'\*\*([^*]+)\*\*\s*[-—–]\s*([^.\n]+[.])'
        for match in re.finditer(pattern1, content):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            definitions.append((term, definition))

        # Паттерн: **Термин**: определение
        pattern2 = r'\*\*([^*]+)\*\*:\s*([^.\n]+[.])'
        for match in re.finditer(pattern2, content):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if (term, definition) not in definitions:
                definitions.append((term, definition))

        return definitions

    def extract_abbreviations(self, content):
        """Извлечь аббревиатуры"""
        abbrevs = []

        # Паттерн: ABBR (Full Name)
        pattern = r'\b([A-ZА-Я]{2,})\s*\(([^)]+)\)'
        for match in re.finditer(pattern, content):
            abbr = match.group(1).strip()
            full = match.group(2).strip()
            abbrevs.append((abbr, full))

        return abbrevs

    def build(self):
        """Построить глоссарий"""
        print("📖 Построение глоссария...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            content = self.extract_content(md_file)
            if not content:
                continue

            article_file = str(md_file.relative_to(self.root_dir))

            # Извлечь определения
            definitions = self.extract_definitions(content)
            for term, definition in definitions:
                if term not in self.glossary:
                    self.glossary[term] = {
                        'definition': definition,
                        'articles': []
                    }
                if article_file not in self.glossary[term]['articles']:
                    self.glossary[term]['articles'].append(article_file)

            # Извлечь аббревиатуры
            abbrevs = self.extract_abbreviations(content)
            for abbr, full in abbrevs:
                if abbr not in self.glossary:
                    self.glossary[abbr] = {
                        'definition': f"Сокращение от: {full}",
                        'articles': []
                    }
                if article_file not in self.glossary[abbr]['articles']:
                    self.glossary[abbr]['articles'].append(article_file)

        print(f"   Найдено терминов: {len(self.glossary)}")

    def save_markdown(self):
        """Сохранить глоссарий в markdown"""
        lines = []
        lines.append("# 📖 Глоссарий\n\n")
        lines.append("> Словарь терминов и аббревиатур\n\n")

        lines.append(f"**Всего терминов**: {len(self.glossary)}\n\n")

        # Алфавитный порядок
        current_letter = None

        for term in sorted(self.glossary.keys(), key=lambda x: x.lower()):
            data = self.glossary[term]

            # Новая буква
            first_letter = term[0].upper()
            if first_letter != current_letter:
                current_letter = first_letter
                lines.append(f"\n## {current_letter}\n\n")

            # Термин
            lines.append(f"### {term}\n\n")
            lines.append(f"{data['definition']}\n\n")

            # Ссылки на статьи
            if data['articles']:
                lines.append("**Встречается в:**\n")
                for article in data['articles'][:3]:
                    lines.append(f"- [{article}]({article})\n")
                if len(data['articles']) > 3:
                    lines.append(f"\n...и ещё {len(data['articles']) - 3}\n")
                lines.append("\n")

        output_file = self.root_dir / "GLOSSARY.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Глоссарий: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = GlossaryBuilder(root_dir)
    builder.build()
    builder.save_markdown()


if __name__ == "__main__":
    main()
