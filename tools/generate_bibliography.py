#!/usr/bin/env python3
"""
Bibliography Generator - Генератор библиографии
Собирает все источники и создаёт библиографические списки

Функции:
- Извлечение источников из метаданных
- Парсинг внешних ссылок
- Форматирование в разных стилях (APA, MLA, Chicago)
- Создание общей библиографии
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
from datetime import datetime


class BibliographyGenerator:
    """Генератор библиографии"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Собранные источники
        self.sources = []

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

    def extract_urls(self, content):
        """Извлечь все URL из содержимого"""
        urls = []

        # Markdown ссылки: [text](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
        for text, url in markdown_links:
            urls.append({'text': text, 'url': url, 'type': 'link'})

        # Голые URL
        bare_urls = re.findall(r'(?<!\()(https?://[^\s\)]+)', content)
        for url in bare_urls:
            if not any(u['url'] == url for u in urls):
                urls.append({'text': '', 'url': url, 'type': 'bare'})

        return urls

    def parse_url_metadata(self, url):
        """Извлечь метаданные из URL (упрощённо)"""
        # Определить тип источника
        if 'github.com' in url:
            source_type = 'GitHub Repository'
        elif 'arxiv.org' in url:
            source_type = 'arXiv Paper'
        elif 'wikipedia.org' in url:
            source_type = 'Wikipedia'
        elif 'stackoverflow.com' in url:
            source_type = 'Stack Overflow'
        elif 'youtube.com' in url or 'youtu.be' in url:
            source_type = 'YouTube Video'
        elif any(ext in url for ext in ['.pdf', '.doc', '.docx']):
            source_type = 'Document'
        else:
            source_type = 'Web Page'

        # Попробовать извлечь домен
        domain_match = re.search(r'https?://([^/]+)', url)
        domain = domain_match.group(1) if domain_match else ''

        return {
            'type': source_type,
            'domain': domain
        }

    def collect_sources(self):
        """Собрать все источники из базы знаний"""
        print("📚 Сбор источников...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not frontmatter:
                continue

            article_file = str(md_file.relative_to(self.root_dir))
            article_title = frontmatter.get('title', md_file.stem)

            # Источник из метаданных
            source = frontmatter.get('source')
            if source:
                self.sources.append({
                    'title': article_title,
                    'source': source,
                    'author': frontmatter.get('author', ''),
                    'date': frontmatter.get('date', ''),
                    'url': frontmatter.get('source_url', ''),
                    'article': article_file,
                    'type': 'metadata'
                })

            # URL из содержимого
            if content:
                urls = self.extract_urls(content)

                for url_data in urls:
                    url_meta = self.parse_url_metadata(url_data['url'])

                    self.sources.append({
                        'title': url_data['text'] or url_meta['domain'],
                        'url': url_data['url'],
                        'domain': url_meta['domain'],
                        'source_type': url_meta['type'],
                        'article': article_file,
                        'article_title': article_title,
                        'type': 'url'
                    })

        print(f"   Найдено источников: {len(self.sources)}")

    def format_source_apa(self, source):
        """Форматировать источник в стиле APA"""
        if source['type'] == 'metadata':
            author = source.get('author', 'Unknown')
            date = source.get('date', 'n.d.')
            if isinstance(date, datetime):
                date = date.year
            elif isinstance(date, str) and '-' in date:
                date = date.split('-')[0]

            title = source['title']

            result = f"{author}. ({date}). *{title}*."

            if source.get('url'):
                result += f" Retrieved from {source['url']}"

            return result

        elif source['type'] == 'url':
            title = source['title'] or source['domain']
            url = source['url']
            source_type = source.get('source_type', 'Web page')

            return f"*{title}*. {source_type}. {url}"

        return str(source)

    def format_source_mla(self, source):
        """Форматировать источник в стиле MLA"""
        if source['type'] == 'metadata':
            author = source.get('author', 'Unknown')
            title = source['title']
            date = source.get('date', 'n.d.')

            return f"{author}. \"{title}.\" {date}."

        elif source['type'] == 'url':
            title = source['title'] or source['domain']
            url = source['url']

            return f"\"{title}.\" Web. {url}"

        return str(source)

    def generate_bibliography_by_article(self):
        """Создать библиографию с группировкой по статьям"""
        lines = []
        lines.append("# 📚 Библиография по статьям\n\n")

        # Группировать по статьям
        by_article = defaultdict(list)

        for source in self.sources:
            article = source.get('article', 'Unknown')
            by_article[article].append(source)

        # Вывести
        for article in sorted(by_article.keys()):
            sources = by_article[article]

            # Заголовок статьи
            article_title = sources[0].get('article_title', article)
            lines.append(f"## [{article_title}]({article})\n\n")

            # Источники
            for i, source in enumerate(sources, 1):
                formatted = self.format_source_apa(source)
                lines.append(f"{i}. {formatted}\n")

            lines.append("\n")

        output_file = self.root_dir / "BIBLIOGRAPHY_BY_ARTICLE.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Библиография по статьям: {output_file}")

    def generate_master_bibliography(self):
        """Создать общую библиографию всех источников"""
        lines = []
        lines.append("# 📚 Общая библиография\n\n")
        lines.append("> Все источники, использованные в базе знаний\n\n")

        lines.append(f"**Всего источников**: {len(self.sources)}\n\n")

        # Группировать по типу
        by_type = defaultdict(list)

        for source in self.sources:
            if source['type'] == 'url':
                source_type = source.get('source_type', 'Web Page')
            else:
                source_type = 'Article Source'

            by_type[source_type].append(source)

        # Вывести по типам
        for source_type in sorted(by_type.keys()):
            sources = by_type[source_type]
            lines.append(f"## {source_type} ({len(sources)})\n\n")

            # Убрать дубликаты по URL
            seen_urls = set()
            unique_sources = []

            for source in sources:
                url = source.get('url', source.get('source', ''))
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_sources.append(source)
                elif not url:
                    unique_sources.append(source)

            # Вывести
            for i, source in enumerate(unique_sources, 1):
                formatted = self.format_source_apa(source)
                lines.append(f"{i}. {formatted}\n")

            lines.append("\n")

        output_file = self.root_dir / "MASTER_BIBLIOGRAPHY.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Общая библиография: {output_file}")

    def generate_sources_by_domain(self):
        """Создать список источников по доменам"""
        lines = []
        lines.append("# 🌐 Источники по доменам\n\n")

        # Собрать URL источники
        url_sources = [s for s in self.sources if s['type'] == 'url']

        # Группировать по доменам
        by_domain = defaultdict(list)

        for source in url_sources:
            domain = source.get('domain', 'Unknown')
            by_domain[domain].append(source)

        lines.append(f"**Всего доменов**: {len(by_domain)}\n\n")

        # Статистика
        lines.append("## Топ-10 доменов\n\n")

        domain_counts = [(domain, len(sources)) for domain, sources in by_domain.items()]
        domain_counts.sort(key=lambda x: -x[1])

        for i, (domain, count) in enumerate(domain_counts[:10], 1):
            lines.append(f"{i}. **{domain}** — {count} ссылок\n")

        lines.append("\n## По доменам\n\n")

        # Детали по доменам
        for domain in sorted(by_domain.keys()):
            sources = by_domain[domain]
            lines.append(f"### {domain} ({len(sources)})\n\n")

            # Убрать дубликаты
            seen_urls = set()
            for source in sources[:10]:  # Максимум 10 на домен
                url = source['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    title = source['title'] or 'Untitled'
                    lines.append(f"- [{title}]({url})\n")

            if len(sources) > 10:
                lines.append(f"\n...и ещё {len(sources) - 10}\n")

            lines.append("\n")

        output_file = self.root_dir / "SOURCES_BY_DOMAIN.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Источники по доменам: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Bibliography Generator - Генератор библиографии'
    )

    parser.add_argument(
        '-s', '--style',
        choices=['apa', 'mla', 'chicago'],
        default='apa',
        help='Стиль цитирования (по умолчанию: APA)'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = BibliographyGenerator(root_dir)

    # Собрать источники
    generator.collect_sources()

    print("\n📝 Генерация библиографий...\n")

    # Создать библиографии
    generator.generate_bibliography_by_article()
    generator.generate_master_bibliography()
    generator.generate_sources_by_domain()

    print("\n✅ Готово!")


if __name__ == "__main__":
    main()
