#!/usr/bin/env python3
"""
Export Manager - Менеджер экспорта
Экспорт статей в различные форматы

Вдохновлено: Pandoc, Markdown exporters
"""

from pathlib import Path
import yaml
import re
import json
from datetime import datetime


class ExportManager:
    """Менеджер экспорта"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.export_dir = self.root_dir / "exports"

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

    def export_to_html(self):
        """Экспорт в HTML"""
        print("📄 Экспорт в HTML...\n")

        self.export_dir.mkdir(exist_ok=True)
        html_dir = self.export_dir / "html"
        html_dir.mkdir(exist_ok=True)

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Базовая конвертация markdown в HTML
            html_content = content

            # Заголовки
            html_content = re.sub(r'^### (.*)', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
            html_content = re.sub(r'^## (.*)', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
            html_content = re.sub(r'^# (.*)', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)

            # Параграфы
            html_content = re.sub(r'\n\n', '</p><p>', html_content)
            html_content = f"<p>{html_content}</p>"

            # Жирный текст
            html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)

            # Курсив
            html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)

            # Ссылки
            html_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_content)

            # Создать HTML файл
            html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {html_content}
</body>
</html>"""

            # Сохранить
            output_file = html_dir / f"{md_file.stem}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            count += 1

        print(f"   ✅ Экспортировано HTML файлов: {count}\n")

    def export_to_json(self):
        """Экспорт в JSON"""
        print("📄 Экспорт в JSON...\n")

        self.export_dir.mkdir(exist_ok=True)

        articles = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Конвертировать даты в строки для JSON
            metadata = {}
            if frontmatter:
                for key, value in frontmatter.items():
                    if hasattr(value, 'isoformat'):  # datetime/date objects
                        metadata[key] = value.isoformat()
                    else:
                        metadata[key] = value

            article_data = {
                'path': article_path,
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'content': content,
                'metadata': metadata
            }

            articles.append(article_data)

        output_file = self.export_dir / "knowledge_base.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'total_articles': len(articles),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)

        print(f"   ✅ Экспортировано в JSON: {output_file}\n")

    def export_to_plain_text(self):
        """Экспорт в простой текст"""
        print("📄 Экспорт в текст...\n")

        self.export_dir.mkdir(exist_ok=True)
        txt_dir = self.export_dir / "txt"
        txt_dir.mkdir(exist_ok=True)

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Удалить markdown синтаксис
            text_content = content

            # Удалить разметку
            text_content = re.sub(r'[#*`\[\]]', '', text_content)
            text_content = re.sub(r'\(([^)]+)\)', '', text_content)

            # Собрать файл
            full_text = f"{title}\n{'=' * len(title)}\n\n{text_content}"

            # Сохранить
            output_file = txt_dir / f"{md_file.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_text)

            count += 1

        print(f"   ✅ Экспортировано TXT файлов: {count}\n")

    def export_all(self):
        """Экспортировать во все форматы"""
        self.export_to_html()
        self.export_to_json()
        self.export_to_plain_text()

        print(f"✅ Экспорт завершён: {self.export_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Export Manager')
    parser.add_argument('-f', '--format', choices=['html', 'json', 'txt', 'all'], default='all',
                       help='Формат экспорта (по умолчанию: all)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    manager = ExportManager(root_dir)

    if args.format == 'html':
        manager.export_to_html()
    elif args.format == 'json':
        manager.export_to_json()
    elif args.format == 'txt':
        manager.export_to_plain_text()
    else:
        manager.export_all()


if __name__ == "__main__":
    main()
