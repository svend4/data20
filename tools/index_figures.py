#!/usr/bin/env python3
"""
Index of Figures - Индекс иллюстраций
Создаёт индекс всех изображений, таблиц и примеров кода
"""

from pathlib import Path
import re


class FiguresIndexer:
    """Индексатор иллюстраций"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.figures = {'images': [], 'tables': [], 'code': []}

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

    def index_file(self, file_path):
        """Индексировать файл"""
        content = self.extract_content(file_path)
        if not content:
            return

        article_path = str(file_path.relative_to(self.root_dir))

        # Изображения: ![alt](path)
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        for alt, path in images:
            self.figures['images'].append({
                'alt': alt or 'Без описания',
                'path': path,
                'article': article_path
            })

        # Таблицы
        table_count = 0
        in_table = False
        for line in content.split('\n'):
            if '|' in line and not in_table:
                in_table = True
                table_count += 1
                # Найти заголовок таблицы (строка перед таблицей)
                context = content[:content.find(line)].split('\n')[-5:]
                table_title = "Таблица"
                for ctx_line in reversed(context):
                    if ctx_line.strip().startswith('#'):
                        table_title = ctx_line.strip('#').strip()
                        break

                self.figures['tables'].append({
                    'title': table_title,
                    'article': article_path,
                    'number': table_count
                })
            elif in_table and '|' not in line:
                in_table = False

        # Блоки кода
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        for lang, code in code_blocks:
            # Найти заголовок (строка перед кодом)
            code_start = content.find(f"```{lang or ''}")
            context = content[:code_start].split('\n')[-5:]
            code_title = "Пример кода"
            for ctx_line in reversed(context):
                if ctx_line.strip():
                    code_title = ctx_line.strip('#').strip()
                    break

            self.figures['code'].append({
                'language': lang or 'text',
                'title': code_title[:100],
                'article': article_path,
                'lines': len(code.split('\n'))
            })

    def index_all(self):
        """Индексировать все файлы"""
        print("🖼️  Индексация иллюстраций...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            self.index_file(md_file)

        print(f"   Изображений: {len(self.figures['images'])}")
        print(f"   Таблиц: {len(self.figures['tables'])}")
        print(f"   Примеров кода: {len(self.figures['code'])}\n")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🖼️ Индекс иллюстраций\n\n")

        # Изображения
        lines.append(f"## Изображения ({len(self.figures['images'])})\n\n")
        for img in self.figures['images']:
            lines.append(f"### {img['alt']}\n\n")
            lines.append(f"- **Путь**: `{img['path']}`\n")
            lines.append(f"- **Статья**: [{img['article']}]({img['article']})\n\n")

        # Таблицы
        lines.append(f"\n## Таблицы ({len(self.figures['tables'])})\n\n")
        for table in self.figures['tables']:
            lines.append(f"### {table['title']}\n\n")
            lines.append(f"- **Статья**: [{table['article']}]({table['article']})\n\n")

        # Код
        lines.append(f"\n## Примеры кода ({len(self.figures['code'])})\n\n")

        # Группировать по языкам
        by_lang = {}
        for code in self.figures['code']:
            lang = code['language']
            if lang not in by_lang:
                by_lang[lang] = []
            by_lang[lang].append(code)

        for lang in sorted(by_lang.keys()):
            codes = by_lang[lang]
            lines.append(f"### {lang} ({len(codes)})\n\n")

            for code in codes:
                lines.append(f"- **{code['title']}** ({code['lines']} строк)\n")
                lines.append(f"  - [{code['article']}]({code['article']})\n")

            lines.append("\n")

        output_file = self.root_dir / "FIGURES_INDEX.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    indexer = FiguresIndexer(root_dir)
    indexer.index_all()
    indexer.generate_report()


if __name__ == "__main__":
    main()
