#!/usr/bin/env python3
"""
Table of Contents Generator - Генератор оглавления
Автоматически создаёт оглавление для markdown файлов

Функции:
- Извлечение заголовков из markdown
- Создание якорных ссылок
- Многоуровневое оглавление
- Автоматическое добавление в начало файла
- Auto-numbering (1.1, 1.2, etc.)
- Multi-format export (Markdown, HTML, JSON)
- TOC validation (проверка якорей)
- Cross-reference detection
- Interactive HTML TOC
"""

from pathlib import Path
import re
import json
import argparse
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from collections import defaultdict


class AutoNumbering:
    """Автоматическая нумерация заголовков"""

    def __init__(self, style='decimal'):
        """
        style: 'decimal' (1.1.1), 'roman' (I.A.1), 'legal' (1.1.1.1)
        """
        self.style = style
        self.counters = defaultdict(int)

    def generate_number(self, level: int) -> str:
        """Сгенерировать номер для уровня"""
        # Reset deeper levels when going back up
        for l in range(level + 1, 7):
            self.counters[l] = 0

        self.counters[level] += 1

        if self.style == 'decimal':
            # 1.1.1
            numbers = [str(self.counters[l]) for l in range(1, level + 1)]
            return '.'.join(numbers)
        elif self.style == 'legal':
            # 1.1.1.1
            numbers = [str(self.counters[l]) for l in range(1, level + 1)]
            return '.'.join(numbers)
        elif self.style == 'roman':
            # I.A.1
            roman_map = [
                lambda n: self._to_roman(n).upper(),  # I, II, III
                lambda n: chr(64 + n),                # A, B, C
                lambda n: str(n),                     # 1, 2, 3
                lambda n: chr(96 + n),                # a, b, c
            ]
            if level <= len(roman_map):
                return roman_map[level - 1](self.counters[level])
            return str(self.counters[level])

        return ''

    @staticmethod
    def _to_roman(num: int) -> str:
        """Convert to Roman numerals"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        roman = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman += syms[i]
                num -= val[i]
            i += 1
        return roman


class TOCValidator:
    """Валидатор оглавления"""

    def __init__(self, content: str, headings: List[Tuple[int, str, str]]):
        self.content = content
        self.headings = headings

    def validate(self) -> Dict:
        """
        Проверить корректность оглавления

        Returns: {
            'valid': bool,
            'issues': [{'type': str, 'message': str, 'anchor': str}, ...],
            'stats': {...}
        }
        """
        issues = []

        # Check for duplicate anchors
        anchors = [h[2] for h in self.headings]
        anchor_counts = defaultdict(int)
        for anchor in anchors:
            anchor_counts[anchor] += 1

        for anchor, count in anchor_counts.items():
            if count > 1:
                issues.append({
                    'type': 'duplicate_anchor',
                    'message': f'Якорь "{anchor}" встречается {count} раз',
                    'anchor': anchor,
                    'severity': 'high'
                })

        # Check for empty headings
        for level, text, anchor in self.headings:
            if not text.strip():
                issues.append({
                    'type': 'empty_heading',
                    'message': f'Пустой заголовок уровня {level}',
                    'anchor': anchor,
                    'severity': 'medium'
                })

        # Check heading hierarchy (no skipped levels)
        prev_level = 0
        for level, text, anchor in self.headings:
            if level > prev_level + 1 and prev_level > 0:
                issues.append({
                    'type': 'skipped_level',
                    'message': f'Пропущен уровень: {prev_level} → {level} в "{text}"',
                    'anchor': anchor,
                    'severity': 'low'
                })
            prev_level = level

        # Stats
        stats = {
            'total_headings': len(self.headings),
            'levels': defaultdict(int),
            'max_depth': max((h[0] for h in self.headings), default=0),
            'unique_anchors': len(set(anchors))
        }

        for level, _, _ in self.headings:
            stats['levels'][f'h{level}'] = stats['levels'].get(f'h{level}', 0) + 1

        return {
            'valid': len([i for i in issues if i['severity'] in ['high', 'critical']]) == 0,
            'issues': issues,
            'stats': dict(stats['levels']) | {
                'total': stats['total_headings'],
                'max_depth': stats['max_depth'],
                'unique_anchors': stats['unique_anchors']
            }
        }


class CrossReferenceDetector:
    """Детектор перекрёстных ссылок"""

    def __init__(self, content: str, file_path: Path, root_dir: Path):
        self.content = content
        self.file_path = file_path
        self.root_dir = root_dir

    def find_internal_links(self) -> List[Dict]:
        """Найти все внутренние ссылки [text](url)"""
        # Pattern: [text](url) or [text](url#anchor)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, self.content)

        links = []
        for text, url in matches:
            # Skip external URLs
            if url.startswith('http'):
                continue

            # Parse URL and anchor
            if '#' in url:
                path, anchor = url.split('#', 1)
            else:
                path = url
                anchor = ''

            links.append({
                'text': text,
                'url': url,
                'path': path,
                'anchor': anchor,
                'type': 'internal' if path else 'anchor_only'
            })

        return links

    def validate_links(self, links: List[Dict]) -> List[Dict]:
        """Проверить, что все ссылки работают"""
        broken = []

        for link in links:
            if link['type'] == 'anchor_only':
                # Anchor within same file - would need TOC to validate
                continue

            # Check if file exists
            if link['path']:
                # Resolve relative to current file
                target = (self.file_path.parent / link['path']).resolve()

                if not target.exists():
                    broken.append({
                        'link': link,
                        'reason': f'Файл не найден: {link["path"]}',
                        'severity': 'high'
                    })
                elif target.is_dir():
                    broken.append({
                        'link': link,
                        'reason': f'Ссылка на директорию: {link["path"]}',
                        'severity': 'medium'
                    })

        return broken


class TOCGenerator:
    """Генератор оглавления"""

    def __init__(self, root_dir=".", numbered=False, numbering_style='decimal'):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.numbered = numbered
        self.numbering_style = numbering_style

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return match.group(1), match.group(2)
        except:
            pass
        return None, None

    def extract_headings(self, content):
        """
        Извлечь заголовки из markdown

        Возвращает список: [(level, text, anchor), ...]
        """
        headings = []

        for line in content.split('\n'):
            # Проверить на заголовок
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                hashes = match.group(1)
                text = match.group(2).strip()

                level = len(hashes)

                # Создать якорь (как GitHub)
                anchor = text.lower()
                # Удалить специальные символы
                anchor = re.sub(r'[^\w\s-]', '', anchor)
                # Заменить пробелы на дефисы
                anchor = re.sub(r'\s+', '-', anchor)
                # Удалить множественные дефисы
                anchor = re.sub(r'-+', '-', anchor)
                # Удалить дефисы в начале и конце
                anchor = anchor.strip('-')

                headings.append((level, text, anchor))

        return headings

    def generate_toc(self, headings, min_level=2, max_level=4, numbered=None):
        """
        Создать оглавление из заголовков

        min_level: минимальный уровень заголовков (обычно 2, чтобы пропустить h1)
        max_level: максимальный уровень заголовков (для контроля глубины)
        numbered: использовать ли нумерацию (None = use self.numbered)
        """
        if not headings:
            return ""

        if numbered is None:
            numbered = self.numbered

        lines = []
        lines.append("## 📑 Содержание\n\n")

        # Auto numbering
        numbering = AutoNumbering(self.numbering_style) if numbered else None

        for level, text, anchor in headings:
            # Пропустить слишком высокие или низкие уровни
            if level < min_level or level > max_level:
                continue

            # Пропустить само оглавление
            if 'содержание' in text.lower() or 'table of contents' in text.lower():
                continue

            # Отступ пропорционален уровню
            indent = "  " * (level - min_level)

            # Нумерация
            if numbering:
                number = numbering.generate_number(level)
                lines.append(f"{indent}- {number} [{text}](#{anchor})\n")
            else:
                lines.append(f"{indent}- [{text}](#{anchor})\n")

        lines.append("\n")

        return ''.join(lines)

    def generate_toc_html(self, headings, min_level=2, max_level=4) -> str:
        """Создать интерактивное HTML оглавление"""
        if not headings:
            return ""

        html_lines = []
        html_lines.append('<nav class="toc">\n')
        html_lines.append('  <h2>📑 Содержание</h2>\n')
        html_lines.append('  <ul class="toc-list">\n')

        numbering = AutoNumbering(self.numbering_style) if self.numbered else None
        current_level = min_level

        for level, text, anchor in headings:
            if level < min_level or level > max_level:
                continue
            if 'содержание' in text.lower():
                continue

            # Handle nesting
            while current_level < level:
                html_lines.append('    ' * current_level + '  <ul>\n')
                current_level += 1

            while current_level > level:
                html_lines.append('    ' * current_level + '  </ul>\n')
                current_level -= 1

            number = numbering.generate_number(level) + ' ' if numbering else ''
            indent = '    ' * (level - min_level + 1)
            html_lines.append(f'{indent}<li><a href="#{anchor}">{number}{text}</a></li>\n')

        # Close remaining lists
        while current_level >= min_level:
            html_lines.append('    ' * current_level + '  </ul>\n')
            current_level -= 1

        html_lines.append('  </ul>\n')
        html_lines.append('</nav>\n')

        return ''.join(html_lines)

    def generate_toc_json(self, headings, min_level=2, max_level=4) -> str:
        """Экспорт оглавления в JSON"""
        toc_data = []

        numbering = AutoNumbering(self.numbering_style) if self.numbered else None

        for level, text, anchor in headings:
            if level < min_level or level > max_level:
                continue
            if 'содержание' in text.lower():
                continue

            item = {
                'level': level,
                'text': text,
                'anchor': anchor
            }

            if numbering:
                item['number'] = numbering.generate_number(level)

            toc_data.append(item)

        return json.dumps(toc_data, ensure_ascii=False, indent=2)

    def generate_toc_plaintext(self, headings, min_level=2, max_level=4) -> str:
        """Создать plaintext оглавление (для терминала)"""
        if not headings:
            return ""

        lines = []
        lines.append("📑 Содержание\n")
        lines.append("=" * 50 + "\n\n")

        numbering = AutoNumbering(self.numbering_style) if self.numbered else None

        for level, text, anchor in headings:
            if level < min_level or level > max_level:
                continue
            if 'содержание' in text.lower():
                continue

            indent = "  " * (level - min_level)

            if numbering:
                number = numbering.generate_number(level)
                lines.append(f"{indent}{number}. {text}\n")
            else:
                lines.append(f"{indent}• {text}\n")

        return ''.join(lines)

    def calculate_toc_stats(self, headings) -> Dict:
        """Вычислить статистику оглавления"""
        if not headings:
            return {}

        levels = defaultdict(int)
        total_chars = 0

        for level, text, anchor in headings:
            levels[f'h{level}'] += 1
            total_chars += len(text)

        return {
            'total_headings': len(headings),
            'levels': dict(levels),
            'max_depth': max(h[0] for h in headings),
            'min_depth': min(h[0] for h in headings),
            'avg_heading_length': round(total_chars / len(headings), 1) if headings else 0,
            'total_chars': total_chars
        }

    def add_toc_to_file(self, file_path):
        """Добавить оглавление в файл"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return False

        # Извлечь заголовки
        headings = self.extract_headings(content)

        if not headings:
            return False

        # Проверить, есть ли уже оглавление
        if '## 📑 Содержание' in content or '## Table of Contents' in content:
            # Удалить старое оглавление
            content = re.sub(
                r'## 📑 Содержание\n\n.*?\n\n',
                '',
                content,
                flags=re.DOTALL
            )
            content = re.sub(
                r'## Table of Contents\n\n.*?\n\n',
                '',
                content,
                flags=re.DOTALL
            )

        # Создать новое оглавление
        toc = self.generate_toc(headings)

        # Вставить оглавление после первого заголовка (обычно h1)
        lines = content.split('\n')
        insert_index = 0

        for i, line in enumerate(lines):
            if re.match(r'^#\s+', line):
                # Найти конец первого блока (пустую строку после заголовка)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == '':
                        insert_index = j + 1
                        break
                break

        # Вставить оглавление
        lines.insert(insert_index, toc.rstrip('\n'))

        # Собрать файл обратно
        new_content = "---\n" + frontmatter + "\n---\n\n" + '\n'.join(lines)

        # Записать
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    def process_all_articles(self):
        """Добавить оглавление ко всем статьям"""
        print("📑 Генерация оглавлений...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                if self.add_toc_to_file(md_file):
                    count += 1
                    print(f"✅ {md_file.relative_to(self.root_dir)}")
            except Exception as e:
                print(f"⚠️  Ошибка в {md_file}: {e}")

        print(f"\n✅ Обработано статей: {count}")

    def validate_file_toc(self, file_path) -> Dict:
        """Валидировать оглавление файла"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return {'error': 'Не удалось прочитать файл'}

        headings = self.extract_headings(content)

        if not headings:
            return {'error': 'Заголовки не найдены'}

        # Validate TOC
        validator = TOCValidator(content, headings)
        validation = validator.validate()

        # Find and validate cross-references
        detector = CrossReferenceDetector(content, file_path, self.root_dir)
        links = detector.find_internal_links()
        broken_links = detector.validate_links(links)

        # Calculate stats
        stats = self.calculate_toc_stats(headings)

        return {
            'file': str(file_path.relative_to(self.root_dir)),
            'validation': validation,
            'cross_references': {
                'total_links': len(links),
                'broken_links': broken_links
            },
            'stats': stats
        }

    def validate_all_tocs(self):
        """Валидировать все оглавления в базе знаний"""
        print("🔍 Валидация оглавлений...\n")

        results = []
        issues_count = 0
        broken_links_count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.validate_file_toc(md_file)

            if 'error' not in result:
                validation = result['validation']
                issues = [i for i in validation['issues'] if i['severity'] in ['high', 'critical']]
                broken = result['cross_references']['broken_links']

                if issues or broken:
                    print(f"\n⚠️  {result['file']}")

                    if issues:
                        print(f"   Issues: {len(issues)}")
                        for issue in issues:
                            print(f"     - {issue['message']}")
                        issues_count += len(issues)

                    if broken:
                        print(f"   Broken links: {len(broken)}")
                        for link_issue in broken[:3]:  # Show first 3
                            print(f"     - {link_issue['reason']}")
                        broken_links_count += len(broken)

                results.append(result)

        print(f"\n✅ Проверено файлов: {len(results)}")
        print(f"   Всего issues: {issues_count}")
        print(f"   Broken links: {broken_links_count}")

        # Save detailed report
        output_file = self.root_dir / "toc_validation_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'summary': {
                    'files_checked': len(results),
                    'total_issues': issues_count,
                    'broken_links': broken_links_count
                },
                'results': results
            }, f, ensure_ascii=False, indent=2)

        print(f"📄 Detailed report: {output_file}")

    def generate_master_toc(self):
        """Создать главное оглавление всей базы знаний"""
        print("\n📚 Создание главного оглавления...\n")

        lines = []
        lines.append("# 📚 Главное оглавление базы знаний\n\n")
        lines.append("> Полный список всех статей с их содержанием\n\n")
        lines.append(f"_Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")

        # Группировать по категориям
        by_category = {}
        total_headings = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            # Определить категорию из пути
            parts = md_file.relative_to(self.knowledge_dir).parts
            if len(parts) > 0:
                category = parts[0]

                if category not in by_category:
                    by_category[category] = []

                frontmatter, content = self.extract_frontmatter_and_content(md_file)

                if content:
                    headings = self.extract_headings(content)
                    total_headings += len(headings)

                    by_category[category].append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'headings': headings
                    })

        # Summary stats
        lines.append("## 📊 Статистика\n\n")
        lines.append(f"- **Категорий**: {len(by_category)}\n")
        total_articles = sum(len(articles) for articles in by_category.values())
        lines.append(f"- **Статей**: {total_articles}\n")
        lines.append(f"- **Заголовков**: {total_headings}\n\n")

        # Вывести по категориям
        for category in sorted(by_category.keys()):
            lines.append(f"## {category.title()}\n\n")

            for article in sorted(by_category[category], key=lambda x: x['file']):
                # Название статьи (первый заголовок или имя файла)
                title = Path(article['file']).stem
                if article['headings']:
                    title = article['headings'][0][1]

                lines.append(f"### [{title}]({article['file']})\n\n")

                # Оглавление статьи
                if len(article['headings']) > 1:
                    for level, text, anchor in article['headings'][1:]:
                        if level <= 3:  # Только h2 и h3
                            indent = "  " * (level - 2)
                            lines.append(f"{indent}- {text}\n")
                    lines.append("\n")

        output_file = self.root_dir / "MASTER_TOC.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Главное оглавление: {output_file}")
        print(f"   Категорий: {len(by_category)}")
        print(f"   Статей: {total_articles}")
        print(f"   Заголовков: {total_headings}")


def main():
    parser = argparse.ArgumentParser(
        description='Table of Contents Generator - Генератор оглавления',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # Создать TOC для всех статей
  %(prog)s --file article.md                  # TOC для конкретного файла
  %(prog)s --master                           # Главное оглавление базы
  %(prog)s --validate                         # Валидация всех TOC
  %(prog)s --numbered --style decimal         # С нумерацией 1.1.1
  %(prog)s --export html --file article.md    # Экспорт в HTML
  %(prog)s --stats                            # Статистика по TOC
        """
    )

    parser.add_argument(
        '-f', '--file',
        help='Добавить оглавление к конкретному файлу'
    )

    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Добавить оглавление ко всем статьям'
    )

    parser.add_argument(
        '-m', '--master',
        action='store_true',
        help='Создать главное оглавление всей базы'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Валидировать все оглавления (проверка якорей, broken links)'
    )

    parser.add_argument(
        '--numbered',
        action='store_true',
        help='Использовать нумерацию заголовков'
    )

    parser.add_argument(
        '--style',
        choices=['decimal', 'roman', 'legal'],
        default='decimal',
        help='Стиль нумерации: decimal (1.1.1), roman (I.A.1), legal (1.1.1.1)'
    )

    parser.add_argument(
        '--export',
        choices=['markdown', 'html', 'json', 'plaintext'],
        help='Экспорт в указанном формате'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Показать статистику по оглавлению'
    )

    parser.add_argument(
        '--min-level',
        type=int,
        default=2,
        help='Минимальный уровень заголовков (по умолчанию 2)'
    )

    parser.add_argument(
        '--max-level',
        type=int,
        default=4,
        help='Максимальный уровень заголовков (по умолчанию 4)'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = TOCGenerator(root_dir, numbered=args.numbered, numbering_style=args.style)

    # Validation mode
    if args.validate:
        generator.validate_all_tocs()
        return

    # Export mode
    if args.export and args.file:
        file_path = root_dir / args.file
        frontmatter, content = generator.extract_frontmatter_and_content(file_path)

        if not content:
            print(f"❌ Не удалось прочитать файл: {args.file}")
            return

        headings = generator.extract_headings(content)

        if not headings:
            print(f"❌ Заголовки не найдены в {args.file}")
            return

        print(f"\n📤 Экспорт TOC в формат: {args.export}\n")

        if args.export == 'markdown':
            toc = generator.generate_toc(headings, args.min_level, args.max_level)
            print(toc)
        elif args.export == 'html':
            toc = generator.generate_toc_html(headings, args.min_level, args.max_level)
            print(toc)
        elif args.export == 'json':
            toc = generator.generate_toc_json(headings, args.min_level, args.max_level)
            print(toc)
        elif args.export == 'plaintext':
            toc = generator.generate_toc_plaintext(headings, args.min_level, args.max_level)
            print(toc)

        return

    # Stats mode
    if args.stats:
        print("\n📊 Статистика оглавлений по всей базе знаний\n")

        total_files = 0
        total_headings_count = 0
        levels_overall = defaultdict(int)

        for md_file in generator.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = generator.extract_frontmatter_and_content(md_file)

            if content:
                headings = generator.extract_headings(content)
                stats = generator.calculate_toc_stats(headings)

                if stats:
                    total_files += 1
                    total_headings_count += stats['total_headings']

                    for level, count in stats['levels'].items():
                        levels_overall[level] += count

        print(f"Файлов проанализировано: {total_files}")
        print(f"Всего заголовков: {total_headings_count}")
        print(f"Среднее на файл: {total_headings_count / total_files:.1f}" if total_files > 0 else "N/A")
        print(f"\nРаспределение по уровням:")

        for level in sorted(levels_overall.keys()):
            count = levels_overall[level]
            percent = (count / total_headings_count * 100) if total_headings_count > 0 else 0
            print(f"  {level}: {count} ({percent:.1f}%)")

        return

    # File mode
    if args.file:
        file_path = root_dir / args.file
        if generator.add_toc_to_file(file_path):
            print(f"✅ Оглавление добавлено к {args.file}")

            # Show validation
            result = generator.validate_file_toc(file_path)

            if 'error' not in result:
                print(f"\n📊 Статистика:")
                for key, value in result['stats'].items():
                    print(f"   {key}: {value}")

                if result['validation']['issues']:
                    print(f"\n⚠️  Issues: {len(result['validation']['issues'])}")
                    for issue in result['validation']['issues'][:3]:
                        print(f"     - {issue['message']}")
        else:
            print(f"⚠️  Не удалось добавить оглавление")

    # All mode
    elif args.all:
        generator.process_all_articles()

    # Master mode
    elif args.master:
        generator.generate_master_toc()

    else:
        # По умолчанию - оба действия
        generator.process_all_articles()
        generator.generate_master_toc()


if __name__ == "__main__":
    main()
