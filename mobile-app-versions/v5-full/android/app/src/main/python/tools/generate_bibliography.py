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
from collections import defaultdict, Counter
from datetime import datetime
import argparse
from typing import Dict, List, Tuple
import json
import hashlib


class CitationStyleFormatter:
    """
    Форматирование цитирований в различных академических стилях
    Поддержка: APA 7th, MLA 9th, Chicago 17th, Harvard, IEEE
    """

    def __init__(self):
        pass

    def format_author(self, author: str, style: str = 'apa') -> str:
        """
        Форматировать имя автора согласно стилю

        APA: LastName, F. M.
        MLA: LastName, FirstName
        Chicago: LastName, FirstName MiddleName
        """
        if not author or author == 'Unknown':
            return 'Unknown'

        # Разбить на части (если есть)
        parts = author.split()

        if style == 'apa':
            if len(parts) == 1:
                return parts[0]
            elif len(parts) == 2:
                return f"{parts[1]}, {parts[0][0]}."
            else:
                return f"{parts[-1]}, {parts[0][0]}. {parts[1][0]}."

        elif style == 'mla':
            if len(parts) == 1:
                return parts[0]
            else:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"

        elif style == 'chicago':
            if len(parts) == 1:
                return parts[0]
            else:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"

        return author

    def format_title(self, title: str, style: str = 'apa', is_article: bool = False) -> str:
        """
        Форматировать заголовок согласно стилю

        APA: Sentence case, italic for books
        MLA: Title Case, quotes for articles, italic for books
        Chicago: Title Case
        """
        if not title:
            return ''

        if style == 'apa':
            # Sentence case (только первая буква заглавная)
            formatted = title[0].upper() + title[1:].lower() if len(title) > 1 else title
            return f"*{formatted}*" if not is_article else formatted

        elif style == 'mla':
            # Title Case
            words = title.split()
            formatted = ' '.join(w.capitalize() for w in words)
            return f'"{formatted}"' if is_article else f"*{formatted}*"

        elif style == 'chicago':
            words = title.split()
            formatted = ' '.join(w.capitalize() for w in words)
            return f'"{formatted}"' if is_article else f"*{formatted}*"

        return title

    def format_date(self, date: any, style: str = 'apa') -> str:
        """Форматировать дату согласно стилю"""
        if not date:
            return 'n.d.'

        if isinstance(date, datetime):
            if style == 'apa':
                return str(date.year)
            elif style == 'mla':
                return date.strftime('%d %b. %Y')
            elif style == 'chicago':
                return date.strftime('%B %d, %Y')

        elif isinstance(date, str):
            if '-' in date:  # ISO format
                year = date.split('-')[0]
                return year if style == 'apa' else date

        return str(date)

    def format_citation_apa(self, source: Dict) -> str:
        """
        APA 7th Edition format

        Book: Author, A. A. (Year). Title of work. Publisher.
        Article: Author, A. A. (Year). Title of article. Journal Name, volume(issue), pages.
        Website: Author, A. A. (Year, Month Day). Title. Site Name. URL
        """
        author = self.format_author(source.get('author', 'Unknown'), 'apa')
        date = self.format_date(source.get('date', ''), 'apa')
        title = self.format_title(source.get('title', 'Untitled'), 'apa')

        citation = f"{author}. ({date}). {title}."

        # Добавить URL если есть
        if source.get('url'):
            citation += f" Retrieved from {source['url']}"

        return citation

    def format_citation_mla(self, source: Dict) -> str:
        """
        MLA 9th Edition format

        Author Last Name, First Name. "Title of Source." Title of Container,
        Other contributors, Version, Number, Publisher, Publication Date, Location.
        """
        author = self.format_author(source.get('author', 'Unknown'), 'mla')
        title = self.format_title(source.get('title', 'Untitled'), 'mla', is_article=True)
        date = self.format_date(source.get('date', ''), 'mla')

        citation = f"{author}. {title}. {date}."

        if source.get('url'):
            citation += f" {source['url']}."

        return citation

    def format_citation_chicago(self, source: Dict) -> str:
        """
        Chicago 17th Edition format (Author-Date system)

        Author Last Name, First Name. Year. "Title of Article." Journal Name volume (issue): pages.
        """
        author = self.format_author(source.get('author', 'Unknown'), 'chicago')
        date = self.format_date(source.get('date', ''), 'chicago')
        title = self.format_title(source.get('title', 'Untitled'), 'chicago', is_article=True)

        citation = f"{author}. {date}. {title}."

        if source.get('url'):
            citation += f" {source['url']}."

        return citation

    def format_citation_harvard(self, source: Dict) -> str:
        """
        Harvard referencing style

        Author(s), Year. Title. Place of publication: Publisher.
        """
        author = source.get('author', 'Unknown')
        year = self.format_date(source.get('date', ''), 'apa')
        title = source.get('title', 'Untitled')

        citation = f"{author}, {year}. *{title}*."

        if source.get('url'):
            citation += f" Available at: {source['url']}"

        return citation

    def format_citation_ieee(self, source: Dict, ref_number: int) -> str:
        """
        IEEE format

        [1] A. A. Author, "Title of article," Abbrev. Journal, vol. x, no. x, pp. xxx-xxx, Mon. Year.
        """
        author = source.get('author', 'Unknown')
        title = source.get('title', 'Untitled')

        citation = f"[{ref_number}] {author}, \"{title},\""

        if source.get('url'):
            citation += f" {source['url']}"

        return citation


class BibTeXGenerator:
    """
    Генератор BibTeX формата
    Для использования с LaTeX/BibLaTeX
    """

    def __init__(self):
        pass

    def generate_citation_key(self, source: Dict) -> str:
        """
        Генерировать ключ цитирования

        Format: AuthorLastNameYearFirstWordOfTitle
        Example: Smith2023Introduction
        """
        author = source.get('author', 'Unknown')
        date = source.get('date', '')
        title = source.get('title', 'Untitled')

        # Извлечь фамилию автора
        author_parts = author.split()
        last_name = author_parts[-1] if author_parts else 'Unknown'

        # Извлечь год
        year = ''
        if isinstance(date, datetime):
            year = str(date.year)
        elif isinstance(date, str) and '-' in date:
            year = date.split('-')[0]
        elif isinstance(date, str):
            year = date

        # Первое слово заголовка
        title_words = title.split()
        first_word = title_words[0] if title_words else 'Untitled'
        first_word = re.sub(r'[^a-zA-Z0-9]', '', first_word)

        key = f"{last_name}{year}{first_word}"
        return key

    def format_article(self, source: Dict) -> str:
        """
        BibTeX entry for article

        @article{key,
          author = {Author Name},
          title = {Title of Article},
          journal = {Journal Name},
          year = {2023},
          volume = {10},
          number = {2},
          pages = {123-145}
        }
        """
        key = self.generate_citation_key(source)

        lines = [f"@article{{{key},"]
        lines.append(f"  author = {{{source.get('author', 'Unknown')}}},")
        lines.append(f"  title = {{{{{source.get('title', 'Untitled')}}}}},")

        if source.get('journal'):
            lines.append(f"  journal = {{{source['journal']}}},")

        if source.get('date'):
            year = str(source['date'])[:4] if isinstance(source['date'], str) else source['date'].year
            lines.append(f"  year = {{{year}}},")

        if source.get('volume'):
            lines.append(f"  volume = {{{source['volume']}}},")

        if source.get('number'):
            lines.append(f"  number = {{{source['number']}}},")

        if source.get('pages'):
            lines.append(f"  pages = {{{source['pages']}}},")

        if source.get('url'):
            lines.append(f"  url = {{{source['url']}}},")

        lines.append("}")

        return '\n'.join(lines)

    def format_book(self, source: Dict) -> str:
        """BibTeX entry for book"""
        key = self.generate_citation_key(source)

        lines = [f"@book{{{key},"]
        lines.append(f"  author = {{{source.get('author', 'Unknown')}}},")
        lines.append(f"  title = {{{{{source.get('title', 'Untitled')}}}}},")

        if source.get('publisher'):
            lines.append(f"  publisher = {{{source['publisher']}}},")

        if source.get('date'):
            year = str(source['date'])[:4] if isinstance(source['date'], str) else source['date'].year
            lines.append(f"  year = {{{year}}},")

        if source.get('url'):
            lines.append(f"  url = {{{source['url']}}},")

        lines.append("}")

        return '\n'.join(lines)

    def format_online(self, source: Dict) -> str:
        """BibTeX entry for online resource"""
        key = self.generate_citation_key(source)

        lines = [f"@online{{{key},"]

        if source.get('author'):
            lines.append(f"  author = {{{source['author']}}},")

        lines.append(f"  title = {{{{{source.get('title', 'Untitled')}}}}},")

        if source.get('url'):
            lines.append(f"  url = {{{source['url']}}},")

        if source.get('date'):
            year = str(source['date'])[:4] if isinstance(source['date'], str) else source['date'].year
            lines.append(f"  year = {{{year}}},")

        if source.get('urldate'):
            lines.append(f"  urldate = {{{source['urldate']}}},")

        lines.append("}")

        return '\n'.join(lines)


class DOIResolver:
    """
    Обработка DOI (Digital Object Identifier)
    Извлечение и валидация DOI
    """

    def __init__(self):
        # DOI pattern: 10.xxxx/xxxxx
        self.doi_pattern = re.compile(r'10\.\d{4,}/[^\s]+')

    def extract_doi(self, text: str) -> List[str]:
        """Извлечь все DOI из текста"""
        dois = self.doi_pattern.findall(text)
        return list(set(dois))  # Убрать дубликаты

    def is_valid_doi(self, doi: str) -> bool:
        """Проверить валидность DOI"""
        return bool(self.doi_pattern.match(doi))

    def extract_doi_from_url(self, url: str) -> str:
        """
        Извлечь DOI из URL

        Examples:
        https://doi.org/10.1234/example → 10.1234/example
        https://dx.doi.org/10.1234/example → 10.1234/example
        """
        if 'doi.org/' in url:
            parts = url.split('doi.org/')
            if len(parts) > 1:
                return parts[1].split('?')[0]  # Remove query params
        return ''

    def format_doi_url(self, doi: str) -> str:
        """Форматировать DOI как URL"""
        doi = doi.strip()
        if doi.startswith('http'):
            return doi
        return f"https://doi.org/{doi}"

    def generate_doi_citation(self, doi: str) -> str:
        """
        Генерировать цитирование с DOI

        DOI: 10.xxxx/xxxxx
        """
        return f"DOI: {doi}"


class ReferenceGrouper:
    """
    Группировка и организация ссылок
    По типу, году, автору, категории
    """

    def __init__(self):
        pass

    def group_by_type(self, sources: List[Dict]) -> Dict[str, List[Dict]]:
        """Группировать по типу источника"""
        grouped = defaultdict(list)

        for source in sources:
            source_type = source.get('source_type', source.get('type', 'Unknown'))
            grouped[source_type].append(source)

        return dict(grouped)

    def group_by_year(self, sources: List[Dict]) -> Dict[str, List[Dict]]:
        """Группировать по году публикации"""
        grouped = defaultdict(list)

        for source in sources:
            date = source.get('date', '')
            year = 'Unknown'

            if isinstance(date, datetime):
                year = str(date.year)
            elif isinstance(date, str) and '-' in date:
                year = date.split('-')[0]
            elif date:
                year = str(date)

            grouped[year].append(source)

        return dict(grouped)

    def group_by_author(self, sources: List[Dict]) -> Dict[str, List[Dict]]:
        """Группировать по автору"""
        grouped = defaultdict(list)

        for source in sources:
            author = source.get('author', 'Unknown')

            # Извлечь фамилию (последнее слово)
            author_parts = author.split()
            last_name = author_parts[-1] if author_parts else 'Unknown'

            grouped[last_name].append(source)

        return dict(grouped)

    def group_by_domain(self, sources: List[Dict]) -> Dict[str, List[Dict]]:
        """Группировать по домену (для URL)"""
        grouped = defaultdict(list)

        for source in sources:
            if source.get('url'):
                domain_match = re.search(r'https?://([^/]+)', source['url'])
                domain = domain_match.group(1) if domain_match else 'Unknown'
                grouped[domain].append(source)
            else:
                grouped['No URL'].append(source)

        return dict(grouped)

    def get_statistics(self, sources: List[Dict]) -> Dict[str, any]:
        """Получить статистику по источникам"""
        total = len(sources)

        # По типам
        by_type = self.group_by_type(sources)
        type_counts = {t: len(sources) for t, sources in by_type.items()}

        # По годам
        by_year = self.group_by_year(sources)
        year_counts = {y: len(sources) for y, sources in by_year.items()}

        # По авторам
        by_author = self.group_by_author(sources)
        top_authors = sorted(
            [(author, len(sources)) for author, sources in by_author.items()],
            key=lambda x: -x[1]
        )[:10]

        # По доменам
        by_domain = self.group_by_domain(sources)
        top_domains = sorted(
            [(domain, len(sources)) for domain, sources in by_domain.items()],
            key=lambda x: -x[1]
        )[:10]

        return {
            'total': total,
            'by_type': type_counts,
            'by_year': year_counts,
            'top_authors': top_authors,
            'top_domains': top_domains,
            'unique_authors': len(by_author),
            'unique_domains': len(by_domain),
            'unique_years': len(by_year)
        }


class BibliographyGenerator:
    """Генератор библиографии"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Собранные источники
        self.sources = []

        # Инициализация новых помощников
        self.style_formatter = CitationStyleFormatter()
        self.bibtex_generator = BibTeXGenerator()
        self.doi_resolver = DOIResolver()
        self.reference_grouper = ReferenceGrouper()

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

    def export_bibtex(self, output_file: str):
        """Экспорт в BibTeX формат"""
        lines = []
        lines.append("% Bibliography in BibTeX format\n")
        lines.append("% Generated automatically\n\n")

        for source in self.sources:
            if source['type'] == 'url':
                entry = self.bibtex_generator.format_online(source)
            elif source.get('journal'):
                entry = self.bibtex_generator.format_article(source)
            else:
                entry = self.bibtex_generator.format_book(source)

            lines.append(entry)
            lines.append("\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ BibTeX экспорт: {output_file}")

    def export_json(self, output_file: str):
        """Экспорт в JSON"""
        # Подготовить данные
        data = {
            'generated_at': datetime.now().isoformat(),
            'total_sources': len(self.sources),
            'statistics': self.reference_grouper.get_statistics(self.sources),
            'sources': self.sources
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        print(f"✅ JSON экспорт: {output_file}")

    def export_html(self, output_file: str, style: str = 'apa'):
        """Экспорт в HTML с красивым оформлением"""
        html = []
        html.append('<!DOCTYPE html>\n<html lang="ru">\n<head>\n')
        html.append('<meta charset="UTF-8">\n')
        html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        html.append('<title>Библиография</title>\n')
        html.append('<style>\n')
        html.append('body { font-family: "Georgia", serif; max-width: 900px; margin: 0 auto; ')
        html.append('padding: 40px 20px; background: #f9f9f9; line-height: 1.6; }\n')
        html.append('h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }\n')
        html.append('h2 { color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; ')
        html.append('padding-left: 15px; }\n')
        html.append('.source { background: white; padding: 15px 20px; margin: 10px 0; ')
        html.append('border-left: 3px solid #ecf0f1; border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }\n')
        html.append('.source-number { color: #7f8c8d; font-weight: bold; margin-right: 10px; }\n')
        html.append('.source-text { color: #2c3e50; }\n')
        html.append('a { color: #3498db; text-decoration: none; }\n')
        html.append('a:hover { text-decoration: underline; }\n')
        html.append('.stats { background: white; padding: 20px; border-radius: 5px; ')
        html.append('margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n')
        html.append('.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); ')
        html.append('gap: 15px; margin-top: 15px; }\n')
        html.append('.stat-box { text-align: center; padding: 15px; background: #ecf0f1; border-radius: 5px; }\n')
        html.append('.stat-value { font-size: 2em; font-weight: bold; color: #3498db; }\n')
        html.append('.stat-label { font-size: 0.9em; color: #7f8c8d; margin-top: 5px; }\n')
        html.append('</style>\n</head>\n<body>\n')

        html.append(f'<h1>📚 Библиография ({style.upper()})</h1>\n')

        # Статистика
        stats = self.reference_grouper.get_statistics(self.sources)
        html.append('<div class="stats">\n')
        html.append('<h2>Статистика</h2>\n')
        html.append('<div class="stat-grid">\n')
        html.append(f'<div class="stat-box"><div class="stat-value">{stats["total"]}</div>')
        html.append('<div class="stat-label">Всего источников</div></div>\n')
        html.append(f'<div class="stat-box"><div class="stat-value">{stats["unique_authors"]}</div>')
        html.append('<div class="stat-label">Уникальных авторов</div></div>\n')
        html.append(f'<div class="stat-box"><div class="stat-value">{stats["unique_domains"]}</div>')
        html.append('<div class="stat-label">Уникальных доменов</div></div>\n')
        html.append(f'<div class="stat-box"><div class="stat-value">{stats["unique_years"]}</div>')
        html.append('<div class="stat-label">Годов публикации</div></div>\n')
        html.append('</div>\n')
        html.append('</div>\n')

        # Группировать по типу
        grouped = self.reference_grouper.group_by_type(self.sources)

        for source_type in sorted(grouped.keys()):
            sources = grouped[source_type]
            html.append(f'<h2>{source_type} ({len(sources)})</h2>\n')

            # Убрать дубликаты
            seen = set()
            unique_sources = []
            for source in sources:
                url = source.get('url', source.get('source', ''))
                if url:
                    if url not in seen:
                        seen.add(url)
                        unique_sources.append(source)
                else:
                    unique_sources.append(source)

            # Вывести источники
            for i, source in enumerate(unique_sources, 1):
                # Форматировать согласно стилю
                if style == 'apa':
                    formatted = self.style_formatter.format_citation_apa(source)
                elif style == 'mla':
                    formatted = self.style_formatter.format_citation_mla(source)
                elif style == 'chicago':
                    formatted = self.style_formatter.format_citation_chicago(source)
                elif style == 'harvard':
                    formatted = self.style_formatter.format_citation_harvard(source)
                elif style == 'ieee':
                    formatted = self.style_formatter.format_citation_ieee(source, i)
                else:
                    formatted = self.format_source_apa(source)

                html.append('<div class="source">\n')
                html.append(f'<span class="source-number">[{i}]</span>\n')
                html.append(f'<span class="source-text">{formatted}</span>\n')
                html.append('</div>\n')

        html.append('</body>\n</html>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(html))

        print(f"✅ HTML экспорт: {output_file}")

    def generate_statistics_report(self):
        """Создать отчёт по статистике источников"""
        stats = self.reference_grouper.get_statistics(self.sources)

        lines = []
        lines.append("# 📊 Статистика библиографии\n\n")

        lines.append("## Общая информация\n\n")
        lines.append(f"- **Всего источников**: {stats['total']}\n")
        lines.append(f"- **Уникальных авторов**: {stats['unique_authors']}\n")
        lines.append(f"- **Уникальных доменов**: {stats['unique_domains']}\n")
        lines.append(f"- **Годов публикации**: {stats['unique_years']}\n\n")

        # По типам
        lines.append("## Распределение по типам\n\n")
        for source_type, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            lines.append(f"- **{source_type}**: {count}\n")
        lines.append("\n")

        # Топ авторов
        lines.append("## Топ-10 авторов\n\n")
        for i, (author, count) in enumerate(stats['top_authors'], 1):
            lines.append(f"{i}. **{author}** — {count} публикаций\n")
        lines.append("\n")

        # Топ доменов
        lines.append("## Топ-10 доменов\n\n")
        for i, (domain, count) in enumerate(stats['top_domains'], 1):
            lines.append(f"{i}. **{domain}** — {count} ссылок\n")
        lines.append("\n")

        # По годам
        lines.append("## Распределение по годам\n\n")
        year_items = [(year, count) for year, count in stats['by_year'].items() if year != 'Unknown']
        year_items.sort(reverse=True)
        for year, count in year_items[:15]:  # Последние 15 лет
            lines.append(f"- **{year}**: {count}\n")
        lines.append("\n")

        output_file = self.root_dir / "BIBLIOGRAPHY_STATISTICS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Статистика: {output_file}")

    def extract_and_report_dois(self):
        """Извлечь и создать отчёт по DOI"""
        all_dois = []

        # Извлечь DOI из всех источников
        for source in self.sources:
            # Из URL
            if source.get('url'):
                doi = self.doi_resolver.extract_doi_from_url(source['url'])
                if doi:
                    all_dois.append({
                        'doi': doi,
                        'source': source,
                        'url': self.doi_resolver.format_doi_url(doi)
                    })

            # Из текста (если есть)
            if source.get('title'):
                dois = self.doi_resolver.extract_doi(source['title'])
                for doi in dois:
                    if self.doi_resolver.is_valid_doi(doi):
                        all_dois.append({
                            'doi': doi,
                            'source': source,
                            'url': self.doi_resolver.format_doi_url(doi)
                        })

        if not all_dois:
            print("ℹ️  DOI не найдены")
            return

        lines = []
        lines.append("# 🔬 DOI (Digital Object Identifiers)\n\n")
        lines.append(f"**Найдено DOI**: {len(all_dois)}\n\n")

        for i, item in enumerate(all_dois, 1):
            doi = item['doi']
            source = item['source']
            title = source.get('title', 'Untitled')

            lines.append(f"## {i}. {title}\n\n")
            lines.append(f"**DOI**: [{doi}]({item['url']})\n\n")

            if source.get('author'):
                lines.append(f"**Автор**: {source['author']}\n\n")

        output_file = self.root_dir / "DOIS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ DOI отчёт: {output_file} ({len(all_dois)} найдено)")


def main():
    parser = argparse.ArgumentParser(
        description='📚 Bibliography Generator - Продвинутый генератор библиографии',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                          # Базовая генерация библиографий
  %(prog)s --style apa                              # APA стиль цитирования
  %(prog)s --style mla                              # MLA стиль
  %(prog)s --bibtex bibliography.bib                # Экспорт в BibTeX
  %(prog)s --json bibliography.json                 # Экспорт в JSON
  %(prog)s --html bibliography.html --style chicago # HTML с Chicago стилем
  %(prog)s --stats                                  # Создать статистический отчёт
  %(prog)s --dois                                   # Извлечь и отчёт по DOI
  %(prog)s --all                                    # Все форматы экспорта
        """
    )

    # Стили цитирования
    parser.add_argument(
        '-s', '--style',
        choices=['apa', 'mla', 'chicago', 'harvard', 'ieee'],
        default='apa',
        help='Стиль цитирования (по умолчанию: APA 7th)'
    )

    # Форматы экспорта
    parser.add_argument(
        '--bibtex',
        metavar='FILE',
        help='Экспортировать в BibTeX формат'
    )

    parser.add_argument(
        '--json',
        metavar='FILE',
        help='Экспортировать в JSON с полными метаданными'
    )

    parser.add_argument(
        '--html',
        metavar='FILE',
        help='Экспортировать в HTML с красивым оформлением'
    )

    # Отчёты и анализ
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Создать статистический отчёт'
    )

    parser.add_argument(
        '--dois',
        action='store_true',
        help='Извлечь и создать отчёт по DOI (Digital Object Identifiers)'
    )

    parser.add_argument(
        '--by-article',
        action='store_true',
        help='Группировать по статьям (Markdown)'
    )

    parser.add_argument(
        '--by-domain',
        action='store_true',
        help='Группировать по доменам (Markdown)'
    )

    parser.add_argument(
        '--master',
        action='store_true',
        help='Создать общую библиографию (Markdown)'
    )

    # Специальные опции
    parser.add_argument(
        '--all',
        action='store_true',
        help='Создать все виды отчётов и экспортов'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = BibliographyGenerator(root_dir)

    # Собрать источники
    generator.collect_sources()

    if not generator.sources:
        print("❌ Источники не найдены")
        return

    print(f"\n📊 Найдено источников: {len(generator.sources)}\n")

    # Обработка --all
    if args.all:
        args.by_article = True
        args.master = True
        args.by_domain = True
        args.stats = True
        args.dois = True
        if not args.bibtex:
            args.bibtex = str(root_dir / "bibliography.bib")
        if not args.json:
            args.json = str(root_dir / "bibliography.json")
        if not args.html:
            args.html = str(root_dir / "bibliography.html")

    print("📝 Генерация библиографий...\n")

    # Markdown отчёты
    if args.by_article or (not any([args.bibtex, args.json, args.html, args.stats, args.dois])):
        generator.generate_bibliography_by_article()

    if args.master or (not any([args.bibtex, args.json, args.html, args.stats, args.dois])):
        generator.generate_master_bibliography()

    if args.by_domain or (not any([args.bibtex, args.json, args.html, args.stats, args.dois])):
        generator.generate_sources_by_domain()

    # Статистика
    if args.stats or args.all:
        generator.generate_statistics_report()

    # DOI
    if args.dois or args.all:
        generator.extract_and_report_dois()

    # Экспорты
    if args.bibtex:
        bibtex_path = root_dir / args.bibtex if not Path(args.bibtex).is_absolute() else Path(args.bibtex)
        generator.export_bibtex(str(bibtex_path))

    if args.json:
        json_path = root_dir / args.json if not Path(args.json).is_absolute() else Path(args.json)
        generator.export_json(str(json_path))

    if args.html:
        html_path = root_dir / args.html if not Path(args.html).is_absolute() else Path(args.html)
        generator.export_html(str(html_path), style=args.style)

    print("\n✅ Готово!")


if __name__ == "__main__":
    main()
