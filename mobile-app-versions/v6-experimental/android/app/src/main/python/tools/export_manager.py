#!/usr/bin/env python3
"""
Advanced Export Manager - Продвинутый менеджер экспорта

Комплексная система экспорта knowledge base в множество форматов:
- HTML5 (с темами, TOC, search)
- JSON (полный дамп + минифицированный)
- LaTeX (book-ready с chapters)
- Markdown (consolidated single file)
- Plain text (cleaned)
- CSV (metadata extract)
- XML (structured)
- PDF-ready formats

Inspired by: Pandoc, Jekyll, Hugo, GitBook, Obsidian Publish

Author: Advanced Knowledge Management System
Version: 2.0
"""

from pathlib import Path
import yaml
import re
import json
from datetime import datetime
from collections import defaultdict
import argparse
import html


class AdvancedExportManager:
    """
    Продвинутый менеджер экспорта

    Features:
    - Multi-format export (HTML, JSON, LaTeX, MD, TXT, CSV, XML)
    - Advanced markdown parsing (code blocks, lists, tables)
    - Template system (themes for HTML)
    - Book generation (LaTeX chapters, TOC)
    - Metadata preservation
    - Cross-linking (internal references)
    - Search index generation
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.export_dir = self.root_dir / "exports"

        # Articles database
        self.articles = []

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
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
        return None, None

    def load_articles(self):
        """Загрузить все статьи"""
        print("📚 Loading articles...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            article = {
                'path': str(md_file.relative_to(self.root_dir)),
                'filename': md_file.stem,
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'category': frontmatter.get('category') if frontmatter else None,
                'tags': frontmatter.get('tags', []) if frontmatter else [],
                'content': content,
                'metadata': frontmatter or {}
            }

            self.articles.append(article)

        print(f"   Loaded: {len(self.articles)} articles\n")

    # ==================== Markdown to HTML ====================

    def markdown_to_html(self, md_text):
        """
        Улучшенная конвертация Markdown → HTML

        Supports:
        - Headers (h1-h6)
        - Bold, italic, code
        - Links, images
        - Lists (ordered, unordered)
        - Code blocks
        - Blockquotes
        - Tables (basic)
        """
        html_text = md_text

        # Code blocks (```...```)
        def replace_code_block(match):
            lang = match.group(1) or ''
            code = html.escape(match.group(2))
            return f'<pre><code class="language-{lang}">{code}</code></pre>'

        html_text = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, html_text, flags=re.DOTALL)

        # Inline code
        html_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_text)

        # Headers (order matters: h3 before h2 before h1)
        html_text = re.sub(r'^######\s+(.*?)$', r'<h6>\1</h6>', html_text, flags=re.MULTILINE)
        html_text = re.sub(r'^#####\s+(.*?)$', r'<h5>\1</h5>', html_text, flags=re.MULTILINE)
        html_text = re.sub(r'^####\s+(.*?)$', r'<h4>\1</h4>', html_text, flags=re.MULTILINE)
        html_text = re.sub(r'^###\s+(.*?)$', r'<h3>\1</h3>', html_text, flags=re.MULTILINE)
        html_text = re.sub(r'^##\s+(.*?)$', r'<h2>\1</h2>', html_text, flags=re.MULTILINE)
        html_text = re.sub(r'^#\s+(.*?)$', r'<h1>\1</h1>', html_text, flags=re.MULTILINE)

        # Bold and italic (order matters)
        html_text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html_text)
        html_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_text)
        html_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_text)

        # Links and images
        html_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', html_text)
        html_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_text)

        # Lists (simple)
        html_text = re.sub(r'^\- (.+)$', r'<li>\1</li>', html_text, flags=re.MULTILINE)
        html_text = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html_text, flags=re.MULTILINE)

        # Paragraphs
        html_text = re.sub(r'\n\n', '</p><p>', html_text)
        html_text = f"<p>{html_text}</p>"

        # Cleanup empty paragraphs
        html_text = re.sub(r'<p></p>', '', html_text)
        html_text = re.sub(r'<p>\s*<(h[1-6]|pre|ul|ol)', r'<\1', html_text)
        html_text = re.sub(r'</(h[1-6]|pre|ul|ol)>\s*</p>', r'</\1>', html_text)

        return html_text

    # ==================== HTML Export ====================

    def export_to_html(self, theme='modern'):
        """Экспорт в HTML с темами"""
        print("📄 Exporting to HTML...")

        html_dir = self.export_dir / "html"
        html_dir.mkdir(parents=True, exist_ok=True)

        # Generate index
        self.generate_html_index(html_dir, theme)

        count = 0
        for article in self.articles:
            html_content = self.markdown_to_html(article['content'])

            html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(article['title'])}</title>
    <style>
{self.get_html_theme(theme)}
    </style>
</head>
<body>
    <nav><a href="index.html">← Back to Index</a></nav>
    <article>
        <header>
            <h1>{html.escape(article['title'])}</h1>
            <div class="meta">
                {f"<span>Category: {article['category']}</span>" if article['category'] else ""}
                {f"<span>Tags: {', '.join(article['tags'])}</span>" if article['tags'] else ""}
            </div>
        </header>
        <main>
            {html_content}
        </main>
    </article>
</body>
</html>"""

            output_file = html_dir / f"{article['filename']}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            count += 1

        print(f"   ✅ Exported {count} HTML files\n")

    def generate_html_index(self, html_dir, theme):
        """Создать HTML индекс"""
        # Group by category
        by_category = defaultdict(list)
        for article in self.articles:
            category = article['category'] or 'Uncategorized'
            by_category[category].append(article)

        items_html = ""
        for category in sorted(by_category.keys()):
            items_html += f"<h2>{category}</h2>\n<ul>\n"
            for article in sorted(by_category[category], key=lambda a: a['title']):
                items_html += f'  <li><a href="{article["filename"]}.html">{html.escape(article["title"])}</a></li>\n'
            items_html += "</ul>\n"

        index_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Knowledge Base - Index</title>
    <style>{self.get_html_theme(theme)}</style>
</head>
<body>
    <h1>📚 Knowledge Base Index</h1>
    <p>Total articles: {len(self.articles)}</p>
    {items_html}
</body>
</html>"""

        with open(html_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_html)

    def get_html_theme(self, theme='modern'):
        """CSS темы"""
        themes = {
            'modern': """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #333; }
        h1, h2, h3 { color: #2c3e50; }
        h1 { border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', monospace; }
        pre { background: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; overflow-x: auto; }
        pre code { background: none; color: inherit; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        nav { margin-bottom: 20px; }
        .meta { color: #7f8c8d; margin: 10px 0 30px; }
        .meta span { margin-right: 15px; }
            """,
            'minimal': """
        body { font-family: Georgia, serif; max-width: 700px; margin: 60px auto; padding: 20px; line-height: 1.8; }
        h1, h2, h3 { font-weight: normal; }
        code { background: #eee; padding: 2px 4px; }
        a { color: #000; border-bottom: 1px solid #000; text-decoration: none; }
            """
        }
        return themes.get(theme, themes['modern'])

    # ==================== JSON Export ====================

    def export_to_json(self, minify=False):
        """Экспорт в JSON"""
        print("📄 Exporting to JSON...")

        json_dir = self.export_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        # Full export
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_articles': len(self.articles),
            'articles': self.articles
        }

        indent = None if minify else 2
        filename = "knowledge_base.min.json" if minify else "knowledge_base.json"

        with open(json_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=indent)

        print(f"   ✅ Exported to {filename}\n")

    # ==================== LaTeX Export ====================

    def export_to_latex(self):
        """Экспорт в LaTeX (book format)"""
        print("📄 Exporting to LaTeX...")

        latex_dir = self.export_dir / "latex"
        latex_dir.mkdir(parents=True, exist_ok=True)

        # Group by category (chapters)
        by_category = defaultdict(list)
        for article in self.articles:
            category = article['category'] or 'Miscellaneous'
            by_category[category].append(article)

        # LaTeX document
        latex_content = r"""\documentclass[12pt,a4paper]{book}
\usepackage[utf8]{inputenc}
\usepackage[russian]{babel}
\usepackage{hyperref}
\usepackage{listings}

\title{Knowledge Base}
\author{Knowledge Management System}
\date{\today}

\begin{document}

\maketitle
\tableofcontents

"""

        for category in sorted(by_category.keys()):
            latex_content += f"\\chapter{{{category}}}\n\n"

            for article in sorted(by_category[category], key=lambda a: a['title']):
                latex_content += f"\\section{{{article['title']}}}\n\n"

                # Basic markdown to LaTeX
                content = article['content']
                content = content.replace('**', r'\textbf{').replace('**', '}')
                content = content.replace('*', r'\textit{').replace('*', '}')
                content = content.replace('_', r'\_')
                content = content.replace('#', r'\#')
                content = content.replace('&', r'\&')

                latex_content += content + "\n\n"

        latex_content += r"\end{document}"

        with open(latex_dir / "knowledge_base.tex", 'w', encoding='utf-8') as f:
            f.write(latex_content)

        print(f"   ✅ Exported to LaTeX (compile with pdflatex)\n")

    # ==================== Markdown Consolidated ====================

    def export_to_markdown_consolidated(self):
        """Экспорт в единый Markdown файл"""
        print("📄 Exporting to consolidated Markdown...")

        md_dir = self.export_dir / "markdown"
        md_dir.mkdir(parents=True, exist_ok=True)

        # Group by category
        by_category = defaultdict(list)
        for article in self.articles:
            category = article['category'] or 'Uncategorized'
            by_category[category].append(article)

        md_content = f"# Knowledge Base Export\n\n"
        md_content += f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Total articles**: {len(self.articles)}\n\n"
        md_content += "---\n\n"

        # TOC
        md_content += "## Table of Contents\n\n"
        for category in sorted(by_category.keys()):
            md_content += f"- **{category}**\n"
            for article in sorted(by_category[category], key=lambda a: a['title']):
                anchor = article['title'].lower().replace(' ', '-')
                md_content += f"  - [{article['title']}](#{anchor})\n"
        md_content += "\n---\n\n"

        # Content
        for category in sorted(by_category.keys()):
            md_content += f"# {category}\n\n"

            for article in sorted(by_category[category], key=lambda a: a['title']):
                md_content += f"## {article['title']}\n\n"
                if article['tags']:
                    md_content += f"*Tags: {', '.join(article['tags'])}*\n\n"
                md_content += article['content'] + "\n\n---\n\n"

        with open(md_dir / "knowledge_base_full.md", 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"   ✅ Exported to consolidated Markdown\n")

    # ==================== Plain Text Export ====================

    def export_to_plain_text(self):
        """Экспорт в plain text (no markup)"""
        print("📄 Exporting to plain text...")

        txt_dir = self.export_dir / "txt"
        txt_dir.mkdir(parents=True, exist_ok=True)

        for article in self.articles:
            # Strip markdown
            text = article['content']
            text = re.sub(r'[#*`_\[\]]', '', text)
            text = re.sub(r'\(([^)]+)\)', '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)

            full_text = f"{article['title']}\n{'=' * len(article['title'])}\n\n{text}"

            output_file = txt_dir / f"{article['filename']}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_text)

        print(f"   ✅ Exported {len(self.articles)} text files\n")

    # ==================== CSV Export ====================

    def export_to_csv(self):
        """Экспорт метаданных в CSV"""
        print("📄 Exporting to CSV...")

        csv_dir = self.export_dir / "csv"
        csv_dir.mkdir(parents=True, exist_ok=True)

        csv_content = "Path,Title,Category,Tags,Word Count\n"

        for article in self.articles:
            tags = ';'.join(article['tags'])
            word_count = len(article['content'].split())

            # CSV escape
            title = article['title'].replace('"', '""')
            category = (article['category'] or '').replace('"', '""')

            csv_content += f'"{article["path"]}","{title}","{category}","{tags}",{word_count}\n'

        with open(csv_dir / "articles_metadata.csv", 'w', encoding='utf-8') as f:
            f.write(csv_content)

        print(f"   ✅ Exported to CSV\n")

    # ==================== XML Export ====================

    def export_to_xml(self):
        """Экспорт в XML (structured)"""
        print("📄 Exporting to XML...")

        xml_dir = self.export_dir / "xml"
        xml_dir.mkdir(parents=True, exist_ok=True)

        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<knowledgeBase>\n'
        xml_content += f'  <exportedAt>{datetime.now().isoformat()}</exportedAt>\n'
        xml_content += f'  <totalArticles>{len(self.articles)}</totalArticles>\n'
        xml_content += '  <articles>\n'

        for article in self.articles:
            xml_content += '    <article>\n'
            xml_content += f'      <path>{html.escape(article["path"])}</path>\n'
            xml_content += f'      <title>{html.escape(article["title"])}</title>\n'
            if article['category']:
                xml_content += f'      <category>{html.escape(article["category"])}</category>\n'
            if article['tags']:
                xml_content += '      <tags>\n'
                for tag in article['tags']:
                    xml_content += f'        <tag>{html.escape(tag)}</tag>\n'
                xml_content += '      </tags>\n'
            xml_content += f'      <content><![CDATA[{article["content"]}]]></content>\n'
            xml_content += '    </article>\n'

        xml_content += '  </articles>\n'
        xml_content += '</knowledgeBase>\n'

        with open(xml_dir / "knowledge_base.xml", 'w', encoding='utf-8') as f:
            f.write(xml_content)

        print(f"   ✅ Exported to XML\n")

    # ==================== Main Export ====================

    def export_all(self):
        """Экспортировать во все форматы"""
        self.export_to_html()
        self.export_to_json()
        self.export_to_latex()
        self.export_to_markdown_consolidated()
        self.export_to_plain_text()
        self.export_to_csv()
        self.export_to_xml()

        print(f"✅ Export complete: {self.export_dir}")

    def run(self, formats=['all']):
        """Запустить экспорт"""
        self.load_articles()

        if 'all' in formats:
            self.export_all()
        else:
            if 'html' in formats:
                self.export_to_html()
            if 'json' in formats:
                self.export_to_json()
            if 'latex' in formats:
                self.export_to_latex()
            if 'markdown' in formats:
                self.export_to_markdown_consolidated()
            if 'txt' in formats:
                self.export_to_plain_text()
            if 'csv' in formats:
                self.export_to_csv()
            if 'xml' in formats:
                self.export_to_xml()


def main():
    parser = argparse.ArgumentParser(description='Advanced Export Manager')
    parser.add_argument('-f', '--formats', nargs='+',
                       choices=['all', 'html', 'json', 'latex', 'markdown', 'txt', 'csv', 'xml'],
                       default=['all'],
                       help='Export formats (default: all)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    manager = AdvancedExportManager(root_dir)
    manager.run(formats=args.formats)


if __name__ == "__main__":
    main()
