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


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Index of Figures')
    parser.add_argument('--json', action='store_true', help='Экспорт в JSON')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    indexer = AdvancedFiguresIndexer(root_dir)
    indexer.index_all()
    indexer.generate_report()

    if args.json:
        indexer.export_json()


if __name__ == "__main__":
    main()
