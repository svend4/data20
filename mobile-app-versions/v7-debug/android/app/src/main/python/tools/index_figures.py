#!/usr/bin/env python3
"""
Advanced Index of Figures - Продвинутый индекс иллюстраций
Функции:
- Image metadata (размер, формат, dimensions)
- Alt text quality check (доступность)
- Broken image detection (проверка существования)
- Auto-numbering (Figure 1.1, Table 2.3 - LaTeX style)
- Cross-reference tracking (ссылки на рисунки)
- Figure captions extraction
- Table of Figures (как в научных статьях)
- Code syntax statistics (языки программирования)
- Usage statistics (популярность)
- Optimization suggestions
- JSON/CSV export

Вдохновлено: LaTeX List of Figures, Sphinx, Markdown Preview Enhanced
"""

from pathlib import Path
import re
import json
from collections import defaultdict, Counter
import yaml
import os
import csv
import base64
from datetime import datetime
from typing import List, Dict, Set


class AdvancedFiguresIndexer:
    """Продвинутый индексатор иллюстраций"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Данные
        self.images = []
        self.tables = []
        self.code_blocks = []

        # Статистика
        self.broken_images = []
        self.alt_text_issues = []
        self.cross_references = defaultdict(list)

        # Счётчики для автонумерации
        self.counters = defaultdict(lambda: defaultdict(int))

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

    def get_image_metadata(self, image_path, article_dir):
        """Получить метаданные изображения"""
        # Относительный путь от статьи
        if image_path.startswith('http://') or image_path.startswith('https://'):
            return {
                'type': 'external',
                'url': image_path,
                'exists': None,
                'size': None,
                'format': None
            }

        # Локальный файл
        if image_path.startswith('/'):
            full_path = self.root_dir / image_path.lstrip('/')
        else:
            full_path = article_dir / image_path

        metadata = {
            'type': 'local',
            'path': str(full_path.relative_to(self.root_dir)) if full_path.exists() else image_path,
            'exists': full_path.exists(),
            'size': None,
            'format': None
        }

        if full_path.exists():
            try:
                stat = full_path.stat()
                metadata['size'] = stat.st_size
                metadata['size_kb'] = round(stat.st_size / 1024, 2)
                metadata['format'] = full_path.suffix.lstrip('.').upper()
            except:
                pass

        return metadata

    def check_alt_text_quality(self, alt_text):
        """Проверить качество alt текста"""
        issues = []

        if not alt_text or alt_text.strip() == '':
            issues.append('missing')
            return issues, 0

        # Оценка качества (0-100)
        score = 100

        # Слишком короткий
        if len(alt_text) < 5:
            issues.append('too_short')
            score -= 40

        # Слишком длинный
        if len(alt_text) > 150:
            issues.append('too_long')
            score -= 20

        # Плохие практики
        bad_phrases = ['image', 'picture', 'photo', 'изображение', 'картинка', 'фото']
        if any(phrase in alt_text.lower() for phrase in bad_phrases):
            issues.append('redundant_description')
            score -= 15

        # Только имя файла
        if re.match(r'^[\w\-]+\.(jpg|png|gif|svg)$', alt_text.lower()):
            issues.append('filename_only')
            score -= 30

        return issues, max(0, score)

    def extract_figure_caption(self, content, position):
        """Извлечь подпись к рисунку"""
        # Ищем текст после изображения
        after_image = content[position:position+200]

        # Паттерны подписей
        patterns = [
            r'\n\*([^\*]+)\*',  # *Caption text*
            r'\n_([^_]+)_',      # _Caption text_
            r'\n> ([^\n]+)',     # > Caption text
            r'\n<em>([^<]+)</em>',  # <em>Caption text</em>
        ]

        for pattern in patterns:
            match = re.search(pattern, after_image)
            if match:
                return match.group(1).strip()

        return None

    def auto_number_figure(self, article_path, figure_type):
        """Автонумерация (LaTeX style)"""
        # Извлечь категорию из пути
        parts = Path(article_path).parts
        category = parts[1] if len(parts) > 1 else 'general'

        # Увеличить счётчик
        self.counters[category][figure_type] += 1

        # Формат: Figure 1.1 (категория.номер)
        category_num = hash(category) % 10 + 1  # Упрощённо
        figure_num = self.counters[category][figure_type]

        return f"{category_num}.{figure_num}"

    def find_cross_references(self, content, figure_number):
        """Найти ссылки на рисунок в тексте"""
        references = []

        # Паттерны ссылок
        patterns = [
            rf'рис(?:унок|\.)?\s*{re.escape(figure_number)}',
            rf'fig(?:ure|\.)?\s*{re.escape(figure_number)}',
            rf'\[{re.escape(figure_number)}\]',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            references.extend([m.start() for m in matches])

        return len(references)

    def index_images(self, file_path, content):
        """Индексировать изображения"""
        article_path = str(file_path.relative_to(self.root_dir))
        article_dir = file_path.parent

        # Паттерн: ![alt](path "title")
        pattern = r'!\[([^\]]*)\]\(([^)]+?)(?:\s+"([^"]+)")?\)'

        for match in re.finditer(pattern, content):
            alt_text = match.group(1)
            image_path = match.group(2)
            title = match.group(3)

            # Метаданные изображения
            metadata = self.get_image_metadata(image_path, article_dir)

            # Проверка alt текста
            alt_issues, alt_score = self.check_alt_text_quality(alt_text)

            # Подпись
            caption = self.extract_figure_caption(content, match.end())

            # Автонумерация
            figure_number = self.auto_number_figure(article_path, 'figure')

            # Ссылки на рисунок
            references_count = self.find_cross_references(content, figure_number)

            image_data = {
                'number': figure_number,
                'alt': alt_text or 'Без описания',
                'title': title,
                'caption': caption,
                'path': image_path,
                'article': article_path,
                'metadata': metadata,
                'alt_quality': {
                    'score': alt_score,
                    'issues': alt_issues
                },
                'references': references_count
            }

            self.images.append(image_data)

            # Отслеживание проблем
            if not metadata['exists'] and metadata['type'] == 'local':
                self.broken_images.append({
                    'article': article_path,
                    'path': image_path
                })

            if alt_issues:
                self.alt_text_issues.append({
                    'article': article_path,
                    'alt': alt_text,
                    'issues': alt_issues,
                    'score': alt_score
                })

    def index_tables(self, file_path, content):
        """Индексировать таблицы"""
        article_path = str(file_path.relative_to(self.root_dir))

        lines = content.split('\n')
        in_table = False
        table_start_line = 0
        table_lines = []

        for i, line in enumerate(lines):
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    # Начало таблицы
                    in_table = True
                    table_start_line = i
                    table_lines = [line]
                else:
                    table_lines.append(line)
            elif in_table and '|' not in line:
                # Конец таблицы
                in_table = False

                # Найти заголовок таблицы
                context_lines = lines[max(0, table_start_line - 5):table_start_line]
                table_title = "Таблица"
                caption = None

                for ctx_line in reversed(context_lines):
                    if ctx_line.strip().startswith('#'):
                        table_title = ctx_line.strip('#').strip()
                        break
                    elif ctx_line.strip() and not ctx_line.startswith('|'):
                        caption = ctx_line.strip()

                # Проанализировать таблицу
                rows = len([l for l in table_lines if l.strip().startswith('|')])

                # Колонки (из первой строки)
                first_row = table_lines[0] if table_lines else ''
                columns = len([c for c in first_row.split('|') if c.strip()])

                # Автонумерация
                table_number = self.auto_number_figure(article_path, 'table')

                # Ссылки на таблицу
                references_count = self.find_cross_references(content, table_number)

                self.tables.append({
                    'number': table_number,
                    'title': table_title,
                    'caption': caption,
                    'article': article_path,
                    'rows': rows,
                    'columns': columns,
                    'size': f"{rows}×{columns}",
                    'references': references_count
                })

    def index_code_blocks(self, file_path, content):
        """Индексировать блоки кода"""
        article_path = str(file_path.relative_to(self.root_dir))

        # Паттерн: ```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)```'

        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2)

            # Найти заголовок/описание
            code_start = match.start()
            context = content[max(0, code_start - 200):code_start]
            context_lines = context.split('\n')

            code_title = "Пример кода"
            for ctx_line in reversed(context_lines[-5:]):
                if ctx_line.strip() and not ctx_line.startswith('```'):
                    code_title = ctx_line.strip('#').strip()[:100]
                    break

            # Анализ кода
            lines = code.split('\n')
            lines_count = len(lines)
            chars_count = len(code)

            # Автонумерация
            listing_number = self.auto_number_figure(article_path, 'listing')

            self.code_blocks.append({
                'number': listing_number,
                'language': language,
                'title': code_title,
                'article': article_path,
                'lines': lines_count,
                'chars': chars_count,
                'size': f"{lines_count} lines"
            })

    def index_file(self, file_path):
        """Индексировать один файл"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return

        self.index_images(file_path, content)
        self.index_tables(file_path, content)
        self.index_code_blocks(file_path, content)

    def index_all(self):
        """Индексировать все файлы"""
        print("🖼️  Продвинутая индексация иллюстраций...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            self.index_file(md_file)

        print(f"   Изображений: {len(self.images)}")
        print(f"   Таблиц: {len(self.tables)}")
        print(f"   Блоков кода: {len(self.code_blocks)}")
        print(f"   Битых ссылок: {len(self.broken_images)}")
        print(f"   Проблем с alt: {len(self.alt_text_issues)}\n")

    def generate_statistics(self):
        """Создать статистику"""
        stats = {
            'images': {
                'total': len(self.images),
                'local': len([i for i in self.images if i['metadata']['type'] == 'local']),
                'external': len([i for i in self.images if i['metadata']['type'] == 'external']),
                'broken': len(self.broken_images),
                'alt_issues': len(self.alt_text_issues),
                'avg_alt_score': round(sum(i['alt_quality']['score'] for i in self.images) / len(self.images), 1) if self.images else 0
            },
            'tables': {
                'total': len(self.tables),
                'avg_rows': round(sum(t['rows'] for t in self.tables) / len(self.tables), 1) if self.tables else 0,
                'avg_columns': round(sum(t['columns'] for t in self.tables) / len(self.tables), 1) if self.tables else 0
            },
            'code': {
                'total': len(self.code_blocks),
                'languages': dict(Counter(c['language'] for c in self.code_blocks)),
                'avg_lines': round(sum(c['lines'] for c in self.code_blocks) / len(self.code_blocks), 1) if self.code_blocks else 0
            }
        }

        return stats

    def generate_report(self):
        """Создать подробный отчёт (Markdown)"""
        stats = self.generate_statistics()

        lines = []
        lines.append("# 🖼️ Индекс иллюстраций (Advanced)\n\n")

        # Статистика
        lines.append("## 📊 Общая статистика\n\n")
        lines.append(f"- **Изображений**: {stats['images']['total']} (локальных: {stats['images']['local']}, внешних: {stats['images']['external']})\n")
        lines.append(f"- **Таблиц**: {stats['tables']['total']}\n")
        lines.append(f"- **Примеров кода**: {stats['code']['total']}\n")
        lines.append(f"- **Битых ссылок**: {stats['images']['broken']}\n")
        lines.append(f"- **Средняя оценка alt текста**: {stats['images']['avg_alt_score']}/100\n\n")

        # Проблемы
        if self.broken_images or self.alt_text_issues:
            lines.append("## ⚠️ Обнаруженные проблемы\n\n")

            if self.broken_images:
                lines.append(f"### Битые ссылки на изображения ({len(self.broken_images)})\n\n")
                for item in self.broken_images[:10]:
                    lines.append(f"- **{item['article']}**: `{item['path']}`\n")
                if len(self.broken_images) > 10:
                    lines.append(f"\n_...и ещё {len(self.broken_images) - 10}_\n")
                lines.append("\n")

            if self.alt_text_issues:
                lines.append(f"### Проблемы с alt текстом ({len(self.alt_text_issues)})\n\n")
                for item in sorted(self.alt_text_issues, key=lambda x: x['score'])[:10]:
                    issues_str = ', '.join(item['issues'])
                    lines.append(f"- **{item['article']}** (оценка: {item['score']}/100)\n")
                    lines.append(f"  - Alt: `{item['alt']}`\n")
                    lines.append(f"  - Проблемы: {issues_str}\n")
                if len(self.alt_text_issues) > 10:
                    lines.append(f"\n_...и ещё {len(self.alt_text_issues) - 10}_\n")
                lines.append("\n")

        # List of Figures
        lines.append("## 📷 Список иллюстраций\n\n")

        for img in sorted(self.images, key=lambda x: x['number']):
            lines.append(f"### Figure {img['number']}: {img['alt']}\n\n")

            if img['caption']:
                lines.append(f"_{img['caption']}_\n\n")

            lines.append(f"- **Статья**: [{img['article']}]({img['article']})\n")
            lines.append(f"- **Путь**: `{img['path']}`\n")

            if img['metadata']['type'] == 'local' and img['metadata']['exists']:
                lines.append(f"- **Размер**: {img['metadata']['size_kb']} KB\n")
                lines.append(f"- **Формат**: {img['metadata']['format']}\n")

            lines.append(f"- **Alt качество**: {img['alt_quality']['score']}/100\n")

            if img['references'] > 0:
                lines.append(f"- **Ссылок в тексте**: {img['references']}\n")

            lines.append("\n")

        # List of Tables
        lines.append("\n## 📊 Список таблиц\n\n")

        for table in sorted(self.tables, key=lambda x: x['number']):
            lines.append(f"### Table {table['number']}: {table['title']}\n\n")

            if table['caption']:
                lines.append(f"_{table['caption']}_\n\n")

            lines.append(f"- **Статья**: [{table['article']}]({table['article']})\n")
            lines.append(f"- **Размер**: {table['size']}\n")

            if table['references'] > 0:
                lines.append(f"- **Ссылок в тексте**: {table['references']}\n")

            lines.append("\n")

        # Code examples by language
        lines.append("\n## 💻 Примеры кода по языкам\n\n")

        by_language = defaultdict(list)
        for code in self.code_blocks:
            by_language[code['language']].append(code)

        for lang in sorted(by_language.keys()):
            codes = by_language[lang]
            lines.append(f"### {lang} ({len(codes)} примеров)\n\n")

            for code in sorted(codes, key=lambda x: x['number']):
                lines.append(f"#### Listing {code['number']}: {code['title']}\n\n")
                lines.append(f"- **Статья**: [{code['article']}]({code['article']})\n")
                lines.append(f"- **Размер**: {code['size']}\n\n")

        output_file = self.root_dir / "ADVANCED_FIGURES_INDEX.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def export_json(self):
        """Экспорт в JSON"""
        data = {
            'statistics': self.generate_statistics(),
            'images': self.images,
            'tables': self.tables,
            'code_blocks': self.code_blocks,
            'issues': {
                'broken_images': self.broken_images,
                'alt_text_issues': self.alt_text_issues
            }
        }

        output_file = self.root_dir / "figures_index.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")


class FigureExtractor:
    """
    Извлечение метаданных изображений
    Поиск orphaned images, embedded base64
    """

    def __init__(self, indexer):
        self.indexer = indexer
        self.orphaned_images = []
        self.embedded_images = []
        self.referenced_paths = set()

    def find_orphaned_images(self):
        """Найти изображения, не упомянутые в статьях"""
        print("🔍 Поиск orphaned images...\n")

        # Собрать все упомянутые пути
        for img in self.indexer.images:
            if img['metadata']['type'] == 'local':
                self.referenced_paths.add(img['path'])

        # Сканировать директории с изображениями
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp'}
        images_dir = self.indexer.root_dir / 'knowledge'

        for img_file in images_dir.rglob('*'):
            if img_file.suffix.lower() in image_extensions:
                relative_path = str(img_file.relative_to(self.indexer.root_dir))

                if relative_path not in self.referenced_paths:
                    stat = img_file.stat()
                    self.orphaned_images.append({
                        'path': relative_path,
                        'name': img_file.name,
                        'size_kb': round(stat.st_size / 1024, 2),
                        'format': img_file.suffix.lstrip('.').upper(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
                    })

        print(f"   Найдено orphaned: {len(self.orphaned_images)}\n")

    def extract_embedded_images(self):
        """Найти embedded base64 изображения"""
        print("🔍 Поиск embedded (base64) изображений...\n")

        pattern = r'!\[([^\]]*)\]\(data:image/([^;]+);base64,([A-Za-z0-9+/=]+)\)'

        for md_file in self.indexer.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for match in re.finditer(pattern, content):
                    alt_text = match.group(1)
                    format_type = match.group(2)
                    base64_data = match.group(3)

                    size_bytes = len(base64.b64decode(base64_data))

                    self.embedded_images.append({
                        'article': str(md_file.relative_to(self.indexer.root_dir)),
                        'alt': alt_text,
                        'format': format_type.upper(),
                        'size_kb': round(size_bytes / 1024, 2)
                    })
            except:
                pass

        print(f"   Найдено embedded: {len(self.embedded_images)}\n")

    def generate_extraction_report(self):
        """Создать отчёт извлечения"""
        lines = []
        lines.append("# 🔍 Отчёт: Извлечение метаданных изображений\n\n")

        # Orphaned images
        if self.orphaned_images:
            lines.append(f"## 🗑️ Orphaned Images ({len(self.orphaned_images)})\n\n")
            lines.append("> Изображения в репозитории, не упомянутые в статьях\n\n")

            total_size = sum(img['size_kb'] for img in self.orphaned_images)
            lines.append(f"**Общий размер**: {total_size:.2f} KB\n\n")

            for img in sorted(self.orphaned_images, key=lambda x: -x['size_kb'])[:20]:
                lines.append(f"- `{img['path']}` — {img['format']}, {img['size_kb']} KB\n")

            if len(self.orphaned_images) > 20:
                lines.append(f"\n_...и ещё {len(self.orphaned_images) - 20}_\n")
            lines.append("\n")

        # Embedded images
        if self.embedded_images:
            lines.append(f"## 📦 Embedded Images ({len(self.embedded_images)})\n\n")
            lines.append("> Base64-encoded изображения в markdown\n\n")

            for img in self.embedded_images:
                lines.append(f"- **{img['article']}**: {img['format']}, {img['size_kb']} KB\n")
                lines.append(f"  - Alt: `{img['alt']}`\n")

            lines.append("\n")

        return ''.join(lines)


class CaptionAnalyzer:
    """
    Анализ качества подписей к изображениям
    Извлечение keywords, дубликаты
    """

    def __init__(self, indexer):
        self.indexer = indexer
        self.caption_quality = []
        self.duplicate_captions = []
        self.keywords_freq = Counter()

    def analyze_caption_quality(self):
        """Анализировать качество подписей"""
        print("📝 Анализ качества подписей...\n")

        caption_counts = Counter()

        for img in self.indexer.images:
            caption = img.get('caption')

            if not caption:
                score = 0
                issues = ['missing']
            else:
                score = 100
                issues = []

                # Слишком короткая
                if len(caption) < 10:
                    issues.append('too_short')
                    score -= 40

                # Слишком длинная
                if len(caption) > 200:
                    issues.append('too_long')
                    score -= 20

                # Только одно слово
                words = caption.split()
                if len(words) < 3:
                    issues.append('too_few_words')
                    score -= 30

                # Дубликаты
                caption_counts[caption] += 1

                # Извлечь ключевые слова
                keywords = [w.lower() for w in words if len(w) > 4]
                self.keywords_freq.update(keywords)

            self.caption_quality.append({
                'image': img['number'],
                'article': img['article'],
                'caption': caption or 'Нет подписи',
                'score': max(0, score),
                'issues': issues
            })

        # Найти дубликаты
        for caption, count in caption_counts.items():
            if count > 1:
                images = [
                    img['number'] for img in self.indexer.images
                    if img.get('caption') == caption
                ]
                self.duplicate_captions.append({
                    'caption': caption,
                    'count': count,
                    'images': images
                })

        print(f"   Проанализировано подписей: {len(self.caption_quality)}\n")

    def get_top_keywords(self, n=20):
        """Получить топ N ключевых слов"""
        return self.keywords_freq.most_common(n)

    def generate_captions_report(self):
        """Создать отчёт анализа подписей"""
        lines = []
        lines.append("# 📝 Отчёт: Анализ подписей к изображениям\n\n")

        # Статистика
        avg_score = sum(c['score'] for c in self.caption_quality) / len(self.caption_quality) if self.caption_quality else 0
        missing_count = len([c for c in self.caption_quality if 'missing' in c['issues']])

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего изображений**: {len(self.caption_quality)}\n")
        lines.append(f"- **Без подписи**: {missing_count}\n")
        lines.append(f"- **Средняя оценка качества**: {avg_score:.1f}/100\n")
        lines.append(f"- **Дубликатов подписей**: {len(self.duplicate_captions)}\n\n")

        # Топ keywords
        top_keywords = self.get_top_keywords(20)
        if top_keywords:
            lines.append("## Топ ключевых слов в подписях\n\n")
            for word, count in top_keywords:
                lines.append(f"- **{word}**: {count}\n")
            lines.append("\n")

        # Низкое качество
        low_quality = sorted([c for c in self.caption_quality if c['score'] < 50], key=lambda x: x['score'])
        if low_quality:
            lines.append(f"## Подписи низкого качества (топ-15)\n\n")
            for cap in low_quality[:15]:
                lines.append(f"### Figure {cap['image']} — Оценка: {cap['score']}/100\n\n")
                lines.append(f"- **Статья**: {cap['article']}\n")
                lines.append(f"- **Подпись**: {cap['caption']}\n")
                lines.append(f"- **Проблемы**: {', '.join(cap['issues'])}\n\n")

        # Дубликаты
        if self.duplicate_captions:
            lines.append("## Дубликаты подписей\n\n")
            for dup in self.duplicate_captions:
                lines.append(f"### \"{dup['caption']}\" ({dup['count']} раз)\n\n")
                lines.append(f"Изображения: {', '.join(dup['images'])}\n\n")

        return ''.join(lines)


class FigureVisualizer:
    """
    HTML визуализация галереи изображений
    Dashboard с Chart.js
    """

    def __init__(self, indexer, extractor=None, caption_analyzer=None):
        self.indexer = indexer
        self.extractor = extractor
        self.caption_analyzer = caption_analyzer

    def generate_html_gallery(self, output_file='FIGURES_GALLERY.html'):
        """Создать HTML галерею"""
        print("🎨 Создание HTML галереи...\n")

        stats = self._prepare_statistics()
        chart_data = self._prepare_chart_data()

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🖼️ Figures Gallery</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 40px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .stat-label {{
            color: #666;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            color: #667eea;
            font-size: 2.5em;
            font-weight: bold;
        }}

        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}

        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .chart-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
        }}

        canvas {{
            max-height: 350px;
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }}

        .gallery-item {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }}

        .gallery-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}

        .gallery-item img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
            margin-bottom: 10px;
        }}

        .gallery-caption {{
            font-size: 0.85em;
            color: #666;
            line-height: 1.4;
        }}

        .footer {{
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Figures Gallery</h1>
        <p class="subtitle">Интерактивная галерея изображений и визуализаций</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего изображений</div>
                <div class="stat-value">{stats['total_images']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Таблицы</div>
                <div class="stat-value">{stats['total_tables']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Примеры кода</div>
                <div class="stat-value">{stats['total_code']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Битые ссылки</div>
                <div class="stat-value">{stats['broken_links']}</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Orphaned</div>
                <div class="stat-value">{stats['orphaned']}</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-title">📊 Форматы изображений</div>
                <canvas id="formatsChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">📈 Размеры файлов</div>
                <canvas id="sizesChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">💻 Языки программирования</div>
                <canvas id="languagesChart"></canvas>
            </div>

            <div class="chart-container">
                <div class="chart-title">📝 Качество Alt-текста</div>
                <canvas id="altQualityChart"></canvas>
            </div>
        </div>

        <div class="footer">
            Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Figures Gallery v2.0
        </div>
    </div>

    <script>
        // Форматы изображений
        new Chart(document.getElementById('formatsChart'), {{
            type: 'doughnut',
            data: {{
                labels: {chart_data['formats']['labels']},
                datasets: [{{
                    data: {chart_data['formats']['values']},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#a8edea']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});

        // Размеры файлов
        new Chart(document.getElementById('sizesChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['sizes']['labels']},
                datasets: [{{
                    label: 'Количество файлов',
                    data: {chart_data['sizes']['values']},
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Языки программирования
        new Chart(document.getElementById('languagesChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['languages']['labels']},
                datasets: [{{
                    label: 'Примеров кода',
                    data: {chart_data['languages']['values']},
                    backgroundColor: '#764ba2'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Качество alt-текста
        new Chart(document.getElementById('altQualityChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['alt_quality']['labels']},
                datasets: [{{
                    label: 'Количество',
                    data: {chart_data['alt_quality']['values']},
                    backgroundColor: ['#ef4444', '#f59e0b', '#10b981']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        output_path = self.indexer.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML Gallery: {output_path}\n")

    def _prepare_statistics(self):
        """Подготовить статистику"""
        stats = {
            'total_images': len(self.indexer.images),
            'total_tables': len(self.indexer.tables),
            'total_code': len(self.indexer.code_blocks),
            'broken_links': len(self.indexer.broken_images),
            'orphaned': 0
        }

        if self.extractor and self.extractor.orphaned_images:
            stats['orphaned'] = len(self.extractor.orphaned_images)

        return stats

    def _prepare_chart_data(self):
        """Подготовить данные для графиков"""
        chart_data = {
            'formats': self._get_formats_distribution(),
            'sizes': self._get_sizes_distribution(),
            'languages': self._get_languages_distribution(),
            'alt_quality': self._get_alt_quality_distribution()
        }

        return chart_data

    def _get_formats_distribution(self):
        """Распределение форматов"""
        formats = Counter()

        for img in self.indexer.images:
            if img['metadata']['type'] == 'local' and img['metadata']['exists']:
                fmt = img['metadata'].get('format', 'UNKNOWN')
                formats[fmt] += 1

        labels = list(formats.keys())
        values = list(formats.values())

        return {'labels': labels, 'values': values}

    def _get_sizes_distribution(self):
        """Распределение размеров"""
        bins = [0, 50, 100, 500, 1000, float('inf')]
        labels = ['0-50 KB', '50-100 KB', '100-500 KB', '500KB-1MB', '>1MB']
        counts = [0] * (len(bins) - 1)

        for img in self.indexer.images:
            if img['metadata']['type'] == 'local' and img['metadata']['exists']:
                size_kb = img['metadata'].get('size_kb', 0)

                for i in range(len(bins) - 1):
                    if bins[i] <= size_kb < bins[i + 1]:
                        counts[i] += 1
                        break

        return {'labels': labels, 'values': counts}

    def _get_languages_distribution(self):
        """Распределение языков программирования"""
        languages = Counter(c['language'] for c in self.indexer.code_blocks)

        labels = list(languages.keys())[:10]
        values = list(languages.values())[:10]

        return {'labels': labels, 'values': values}

    def _get_alt_quality_distribution(self):
        """Распределение качества alt-текста"""
        categories = {'Плохое (0-50)': 0, 'Среднее (50-80)': 0, 'Хорошее (80-100)': 0}

        for img in self.indexer.images:
            score = img['alt_quality']['score']

            if score < 50:
                categories['Плохое (0-50)'] += 1
            elif score < 80:
                categories['Среднее (50-80)'] += 1
            else:
                categories['Хорошее (80-100)'] += 1

        labels = list(categories.keys())
        values = list(categories.values())

        return {'labels': labels, 'values': values}


class FigureValidator:
    """
    Валидация изображений
    Проверка ссылок, размеров, подписей
    """

    def __init__(self, indexer):
        self.indexer = indexer
        self.validation_results = []

    def validate_all(self):
        """Выполнить все проверки"""
        print("✅ Валидация изображений...\n")

        for img in self.indexer.images:
            issues = []
            warnings = []

            # Проверка существования
            if img['metadata']['type'] == 'local' and not img['metadata']['exists']:
                issues.append('Файл не найден')

            # Проверка alt текста
            if img['alt_quality']['score'] < 50:
                warnings.append(f"Низкое качество alt-текста ({img['alt_quality']['score']}/100)")

            # Проверка размера
            if img['metadata']['type'] == 'local' and img['metadata']['exists']:
                size_kb = img['metadata'].get('size_kb', 0)

                if size_kb > 1000:
                    warnings.append(f'Файл слишком большой ({size_kb:.1f} KB)')
                elif size_kb < 5:
                    warnings.append(f'Файл слишком маленький ({size_kb:.1f} KB)')

            # Проверка подписи
            if not img.get('caption'):
                warnings.append('Отсутствует подпись')

            # Проверка references
            if img['references'] == 0:
                warnings.append('Нет ссылок на рисунок в тексте')

            self.validation_results.append({
                'image': img['number'],
                'article': img['article'],
                'path': img['path'],
                'issues': issues,
                'warnings': warnings,
                'status': 'error' if issues else ('warning' if warnings else 'ok')
            })

        errors_count = len([r for r in self.validation_results if r['status'] == 'error'])
        warnings_count = len([r for r in self.validation_results if r['status'] == 'warning'])

        print(f"   Ошибки: {errors_count}")
        print(f"   Предупреждения: {warnings_count}\n")

    def generate_validation_report(self):
        """Создать отчёт валидации"""
        lines = []
        lines.append("# ✅ Отчёт: Валидация изображений\n\n")

        errors = [r for r in self.validation_results if r['status'] == 'error']
        warnings = [r for r in self.validation_results if r['status'] == 'warning']
        ok = [r for r in self.validation_results if r['status'] == 'ok']

        lines.append("## Статистика\n\n")
        lines.append(f"- **Ошибки**: {len(errors)}\n")
        lines.append(f"- **Предупреждения**: {len(warnings)}\n")
        lines.append(f"- **OK**: {len(ok)}\n")
        lines.append(f"- **Всего**: {len(self.validation_results)}\n\n")

        # Ошибки
        if errors:
            lines.append("## ❌ Ошибки\n\n")

            for result in errors:
                lines.append(f"### Figure {result['image']}\n\n")
                lines.append(f"- **Статья**: {result['article']}\n")
                lines.append(f"- **Путь**: `{result['path']}`\n")
                lines.append("- **Проблемы**:\n")

                for issue in result['issues']:
                    lines.append(f"  - {issue}\n")

                lines.append("\n")

        # Предупреждения
        if warnings:
            lines.append("## ⚠️ Предупреждения (топ-20)\n\n")

            for result in warnings[:20]:
                lines.append(f"### Figure {result['image']}\n\n")
                lines.append(f"- **Статья**: {result['article']}\n")
                lines.append("- **Предупреждения**:\n")

                for warning in result['warnings']:
                    lines.append(f"  - {warning}\n")

                lines.append("\n")

        return ''.join(lines)

    def export_to_csv(self, output_file='figures_validation.csv'):
        """Экспорт результатов валидации в CSV"""
        csv_path = self.indexer.root_dir / output_file

        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Figure', 'Article', 'Path', 'Status', 'Issues', 'Warnings'])

            for result in self.validation_results:
                writer.writerow([
                    result['image'],
                    result['article'],
                    result['path'],
                    result['status'],
                    '; '.join(result['issues']),
                    '; '.join(result['warnings'])
                ])

        print(f"✅ CSV валидация: {csv_path}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='🖼️ Advanced Index of Figures v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                        # Базовая индексация
  %(prog)s --html                 # HTML галерея с Chart.js
  %(prog)s --extract              # Поиск orphaned/embedded изображений
  %(prog)s --analyze-captions     # Анализ качества подписей
  %(prog)s --validate             # Валидация изображений
  %(prog)s --csv                  # Экспорт валидации в CSV
  %(prog)s --all                  # Все функции сразу
  %(prog)s --json --html --csv    # Множественный экспорт

Новые возможности v2.0:
  - 🔍 Поиск orphaned и embedded изображений
  - 📝 Анализ качества подписей с ключевыми словами
  - 🎨 HTML галерея с интерактивными графиками
  - ✅ Валидация ссылок, размеров, подписей
  - 📊 4 визуализации: форматы, размеры, языки, качество
  - 📈 CSV экспорт для внешнего анализа
        """
    )

    # Основные опции
    parser.add_argument('--json', action='store_true',
                       help='📄 Экспорт в JSON')

    # Новые опции v2.0
    parser.add_argument('--html', action='store_true',
                       help='🎨 Создать HTML галерею с Chart.js графиками')
    parser.add_argument('--extract', action='store_true',
                       help='🔍 Найти orphaned и embedded изображения')
    parser.add_argument('--analyze-captions', action='store_true',
                       help='📝 Анализировать качество подписей')
    parser.add_argument('--validate', action='store_true',
                       help='✅ Валидация изображений (ссылки, размеры, подписи)')
    parser.add_argument('--csv', action='store_true',
                       help='📊 Экспортировать валидацию в CSV')

    # Фильтры
    parser.add_argument('--filter-format', type=str,
                       help='🔎 Фильтровать по формату (PNG, JPG, SVG, и т.д.)')
    parser.add_argument('--min-size', type=int, default=0,
                       help='📏 Минимальный размер файла в KB (default: 0)')

    # Отчёты
    parser.add_argument('--export-extraction', action='store_true',
                       help='📁 Экспортировать отчёт извлечения')
    parser.add_argument('--export-captions', action='store_true',
                       help='📝 Экспортировать отчёт анализа подписей')
    parser.add_argument('--export-validation', action='store_true',
                       help='✅ Экспортировать отчёт валидации')

    # Все функции
    parser.add_argument('--all', action='store_true',
                       help='🔥 Выполнить все опции (полный анализ)')

    args = parser.parse_args()

    # --all включает все опции
    if args.all:
        args.html = True
        args.extract = True
        args.analyze_captions = True
        args.validate = True
        args.csv = True
        args.json = True
        args.export_extraction = True
        args.export_captions = True
        args.export_validation = True

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Основная индексация
    indexer = AdvancedFiguresIndexer(root_dir)
    indexer.index_all()
    indexer.generate_report()

    # ========== НОВЫЕ ФУНКЦИИ V2.0 ==========

    # 1. Извлечение метаданных
    extractor = None
    if args.extract or args.html or args.all:
        extractor = FigureExtractor(indexer)
        extractor.find_orphaned_images()
        extractor.extract_embedded_images()

        if args.export_extraction or args.all:
            report = extractor.generate_extraction_report()
            extraction_file = root_dir / 'FIGURES_EXTRACTION.md'
            with open(extraction_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Отчёт извлечения: {extraction_file}\n")

    # 2. Анализ подписей
    caption_analyzer = None
    if args.analyze_captions or args.html or args.all:
        caption_analyzer = CaptionAnalyzer(indexer)
        caption_analyzer.analyze_caption_quality()

        if args.export_captions or args.all:
            report = caption_analyzer.generate_captions_report()
            captions_file = root_dir / 'CAPTIONS_ANALYSIS.md'
            with open(captions_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Отчёт анализа подписей: {captions_file}\n")

    # 3. Валидация
    if args.validate or args.all:
        validator = FigureValidator(indexer)
        validator.validate_all()

        if args.export_validation or args.all:
            report = validator.generate_validation_report()
            validation_file = root_dir / 'FIGURES_VALIDATION.md'
            with open(validation_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Отчёт валидации: {validation_file}\n")

        # CSV export
        if args.csv or args.all:
            validator.export_to_csv()

    # 4. HTML галерея
    if args.html or args.all:
        visualizer = FigureVisualizer(indexer, extractor, caption_analyzer)
        visualizer.generate_html_gallery()

    # JSON export
    if args.json or args.all:
        indexer.export_json()

    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    print(f"Изображений: {len(indexer.images)}")
    print(f"Таблиц: {len(indexer.tables)}")
    print(f"Примеров кода: {len(indexer.code_blocks)}")
    print(f"Битых ссылок: {len(indexer.broken_images)}")
    print(f"Проблем с alt: {len(indexer.alt_text_issues)}")

    if extractor:
        print(f"Orphaned изображений: {len(extractor.orphaned_images)}")
        print(f"Embedded изображений: {len(extractor.embedded_images)}")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
