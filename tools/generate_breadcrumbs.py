#!/usr/bin/env python3
"""
Advanced Breadcrumbs Generator - Продвинутый генератор навигационных крошек
Функции:
- Smart path detection (множественные пути к одной статье)
- Context-aware breadcrumbs (разные крошки в зависимости от контекста)
- Schema.org BreadcrumbList (JSON-LD для SEO)
- Multiple trails (альтернативные пути навигации)
- Breadcrumb analytics (популярные пути)
- Hierarchical detection (автоматическое определение иерархии)
- Parent/child relationships (связи между статьями)
- Breadcrumb caching (для производительности)
- Custom breadcrumbs (через frontmatter)
- HTML/Markdown output

Вдохновлено: Schema.org, Google rich snippets, WordPress breadcrumbs, Yoast SEO
"""

from pathlib import Path
import yaml
import re
import json
from collections import defaultdict


class AdvancedBreadcrumbsGenerator:
    """Продвинутый генератор навигационных крошек"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Кэш для производительности
        self.cache = {}
        self.hierarchy = {}
        self.relationships = defaultdict(list)

        # Статистика
        self.breadcrumb_stats = defaultdict(int)

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

    def build_hierarchy(self):
        """Построить иерархию статей"""
        print("🗂️  Построение иерархии...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, _ = self.extract_frontmatter_and_content(md_file)
            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Сохранить метаданные
            self.hierarchy[article_path] = {
                'title': frontmatter.get('title', md_file.stem),
                'category': frontmatter.get('category'),
                'subcategory': frontmatter.get('subcategory'),
                'parent': frontmatter.get('parent'),  # Явный родитель
                'breadcrumbs': frontmatter.get('breadcrumbs'),  # Кастомные крошки
                'path_parts': list(md_file.relative_to(self.knowledge_dir).parts)
            }

            # Построить отношения parent/child
            parent = frontmatter.get('parent')
            if parent:
                self.relationships[parent].append(article_path)

    def detect_smart_paths(self, article_path):
        """Определить возможные пути к статье"""
        paths = []

        if article_path not in self.hierarchy:
            return paths

        metadata = self.hierarchy[article_path]

        # Путь 1: На основе директорий (filesystem)
        filesystem_path = self.build_filesystem_path(article_path)
        if filesystem_path:
            paths.append({
                'type': 'filesystem',
                'trail': filesystem_path,
                'priority': 10
            })

        # Путь 2: На основе категории/подкатегории
        if metadata['category']:
            category_path = self.build_category_path(article_path)
            if category_path:
                paths.append({
                    'type': 'category',
                    'trail': category_path,
                    'priority': 20
                })

        # Путь 3: На основе явного parent (frontmatter)
        if metadata['parent']:
            parent_path = self.build_parent_path(article_path)
            if parent_path:
                paths.append({
                    'type': 'parent',
                    'trail': parent_path,
                    'priority': 30
                })

        # Путь 4: Кастомные крошки (highest priority)
        if metadata['breadcrumbs']:
            custom_path = self.build_custom_path(article_path)
            if custom_path:
                paths.append({
                    'type': 'custom',
                    'trail': custom_path,
                    'priority': 100
                })

        # Сортировать по приоритету
        paths.sort(key=lambda x: -x['priority'])

        return paths

    def build_filesystem_path(self, article_path):
        """Построить путь на основе файловой системы"""
        trail = []

        file_path = self.root_dir / article_path
        relative_path = file_path.relative_to(self.knowledge_dir)

        # Главная
        trail.append({
            'title': '🏠 Главная',
            'url': '/INDEX.md',
            'position': 1
        })

        # Части пути
        current_path = self.knowledge_dir
        for i, part in enumerate(relative_path.parts[:-1], start=2):
            current_path = current_path / part

            # Название части
            label = part.replace('-', ' ').replace('_', ' ').title()

            # Поиск INDEX.md
            index_file = current_path / "INDEX.md"
            if not index_file.exists():
                # Попробовать index/INDEX.md
                index_file = current_path / "index" / "INDEX.md"

            url = None
            if index_file.exists():
                url = str(index_file.relative_to(self.root_dir))

            trail.append({
                'title': label,
                'url': url,
                'position': i
            })

        # Текущая страница
        metadata = self.hierarchy.get(article_path, {})
        trail.append({
            'title': metadata.get('title', file_path.stem),
            'url': None,  # Текущая страница - без ссылки
            'position': len(trail) + 1
        })

        return trail

    def build_category_path(self, article_path):
        """Построить путь на основе категории"""
        metadata = self.hierarchy.get(article_path)
        if not metadata:
            return None

        trail = []

        # Главная
        trail.append({
            'title': '🏠 Главная',
            'url': '/INDEX.md',
            'position': 1
        })

        # Категория
        if metadata['category']:
            # Найти INDEX для категории
            category_index = self.find_index_by_category(metadata['category'])

            trail.append({
                'title': metadata['category'],
                'url': category_index,
                'position': 2
            })

        # Подкатегория
        if metadata['subcategory']:
            subcategory_index = self.find_index_by_subcategory(
                metadata['category'],
                metadata['subcategory']
            )

            trail.append({
                'title': metadata['subcategory'],
                'url': subcategory_index,
                'position': 3
            })

        # Текущая страница
        trail.append({
            'title': metadata['title'],
            'url': None,
            'position': len(trail) + 1
        })

        return trail

    def build_parent_path(self, article_path):
        """Построить путь на основе явного parent"""
        metadata = self.hierarchy.get(article_path)
        if not metadata or not metadata['parent']:
            return None

        trail = []

        # Рекурсивно собрать путь от корня
        def collect_parents(path, position=1):
            if path not in self.hierarchy:
                return position

            meta = self.hierarchy[path]

            # Если есть parent, сначала обработать его
            if meta['parent']:
                position = collect_parents(meta['parent'], position)

            # Добавить текущий уровень
            trail.append({
                'title': meta['title'],
                'url': path,
                'position': position
            })

            return position + 1

        # Главная
        trail.append({
            'title': '🏠 Главная',
            'url': '/INDEX.md',
            'position': 1
        })

        # Собрать родителей
        collect_parents(metadata['parent'], position=2)

        # Текущая страница
        trail.append({
            'title': metadata['title'],
            'url': None,
            'position': len(trail) + 1
        })

        return trail

    def build_custom_path(self, article_path):
        """Построить кастомный путь из frontmatter"""
        metadata = self.hierarchy.get(article_path)
        if not metadata or not metadata['breadcrumbs']:
            return None

        trail = []
        custom_crumbs = metadata['breadcrumbs']

        # Формат: [{"title": "Home", "url": "/INDEX.md"}, ...]
        if isinstance(custom_crumbs, list):
            for i, crumb in enumerate(custom_crumbs, start=1):
                if isinstance(crumb, dict):
                    trail.append({
                        'title': crumb.get('title', 'Untitled'),
                        'url': crumb.get('url'),
                        'position': i
                    })

        # Текущая страница
        trail.append({
            'title': metadata['title'],
            'url': None,
            'position': len(trail) + 1
        })

        return trail

    def find_index_by_category(self, category):
        """Найти INDEX для категории"""
        for path, meta in self.hierarchy.items():
            if path.endswith('INDEX.md') and category.lower() in path.lower():
                return path
        return None

    def find_index_by_subcategory(self, category, subcategory):
        """Найти INDEX для подкатегории"""
        for path, meta in self.hierarchy.items():
            if path.endswith('INDEX.md'):
                if category.lower() in path.lower() and subcategory.lower() in path.lower():
                    return path
        return None

    def generate_breadcrumbs(self, article_path, output_format='markdown'):
        """Создать навигационные крошки для статьи"""
        # Проверить кэш
        cache_key = f"{article_path}:{output_format}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Определить возможные пути
        paths = self.detect_smart_paths(article_path)

        if not paths:
            return None

        # Использовать путь с наивысшим приоритетом
        primary_path = paths[0]
        trail = primary_path['trail']

        # Статистика
        self.breadcrumb_stats[primary_path['type']] += 1

        # Форматирование
        if output_format == 'markdown':
            result = self.format_markdown(trail)
        elif output_format == 'html':
            result = self.format_html(trail)
        elif output_format == 'json-ld':
            result = self.format_json_ld(trail, article_path)
        else:
            result = None

        # Кэш
        self.cache[cache_key] = result

        return result

    def format_markdown(self, trail):
        """Форматировать в Markdown"""
        crumbs = []

        for item in trail:
            if item['url']:
                crumbs.append(f"[{item['title']}]({item['url']})")
            else:
                crumbs.append(item['title'])

        return " → ".join(crumbs)

    def format_html(self, trail):
        """Форматировать в HTML"""
        html = '<nav class="breadcrumbs" aria-label="breadcrumb">\n'
        html += '  <ol>\n'

        for item in trail:
            html += '    <li>'

            if item['url']:
                html += f'<a href="{item["url"]}">{item["title"]}</a>'
            else:
                html += f'<span aria-current="page">{item["title"]}</span>'

            html += '</li>\n'

        html += '  </ol>\n'
        html += '</nav>'

        return html

    def format_json_ld(self, trail, article_path):
        """Форматировать в JSON-LD (Schema.org BreadcrumbList)"""
        base_url = "https://example.com"  # Настройка

        breadcrumb_list = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": []
        }

        for item in trail:
            if item['url']:
                list_item = {
                    "@type": "ListItem",
                    "position": item['position'],
                    "name": item['title'],
                    "item": f"{base_url}/{item['url']}"
                }
                breadcrumb_list["itemListElement"].append(list_item)

        return json.dumps(breadcrumb_list, ensure_ascii=False, indent=2)

    def add_breadcrumbs_to_file(self, file_path, format='markdown'):
        """Добавить навигационные крошки в файл"""
        article_path = str(file_path.relative_to(self.root_dir))

        frontmatter_str, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return False

        # Создать крошки
        breadcrumbs = self.generate_breadcrumbs(article_path, output_format=format)

        if not breadcrumbs:
            return False

        # Удалить старые крошки (первая строка с → или 🏠)
        lines = content.split('\n')
        if lines and ('🏠' in lines[0] or '→' in lines[0]):
            lines = lines[1:]
            if lines and lines[0].strip() == '':
                lines = lines[1:]
            content = '\n'.join(lines)

        # Добавить новые крошки
        new_content = f"{breadcrumbs}\n\n{content}"

        # Собрать файл
        full_content = f"---\n{frontmatter_str}\n---\n\n{new_content}"

        # Записать
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return True

    def generate_analytics_report(self):
        """Создать отчёт по аналитике крошек"""
        lines = []
        lines.append("# 🍞 Breadcrumbs Analytics\n\n")

        # Статистика по типам
        lines.append("## Статистика по типам путей\n\n")

        total = sum(self.breadcrumb_stats.values())

        for path_type, count in sorted(self.breadcrumb_stats.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"- **{path_type}**: {count} ({pct:.1f}%)\n")

        lines.append(f"\n**Всего**: {total}\n\n")

        # Рекомендации
        lines.append("## Рекомендации\n\n")

        if self.breadcrumb_stats.get('custom', 0) < total * 0.1:
            lines.append("- ⚠️ Рассмотрите добавление кастомных breadcrumbs в frontmatter для важных статей\n")

        if self.breadcrumb_stats.get('parent', 0) > 0:
            lines.append("- ✅ Хорошо: используются явные parent отношения\n")

        output_file = self.root_dir / "BREADCRUMBS_ANALYTICS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Аналитика: {output_file}")

    def process_all(self, output_format='markdown', generate_schema=False):
        """Добавить крошки ко всем статьям"""
        print("🍞 Генерация продвинутых навигационных крошек...\n")

        # Построить иерархию
        self.build_hierarchy()

        count = 0
        schema_data = {}

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            try:
                # Добавить markdown крошки
                if self.add_breadcrumbs_to_file(md_file, format=output_format):
                    count += 1
                    print(f"✅ {article_path}")

                # Сгенерировать Schema.org JSON-LD
                if generate_schema:
                    paths = self.detect_smart_paths(article_path)
                    if paths:
                        trail = paths[0]['trail']
                        schema_data[article_path] = self.format_json_ld(trail, article_path)

            except Exception as e:
                print(f"⚠️  Ошибка {article_path}: {e}")

        print(f"\n✅ Обработано статей: {count}")

        # Сохранить Schema.org данные
        if generate_schema and schema_data:
            output_file = self.root_dir / "breadcrumbs_schema.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Schema.org JSON-LD: {output_file}")

        # Аналитика
        self.generate_analytics_report()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Breadcrumbs Generator')
    parser.add_argument('--format', choices=['markdown', 'html'], default='markdown',
                       help='Формат вывода (по умолчанию: markdown)')
    parser.add_argument('--schema', action='store_true',
                       help='Генерировать Schema.org JSON-LD')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = AdvancedBreadcrumbsGenerator(root_dir)
    generator.process_all(output_format=args.format, generate_schema=args.schema)


if __name__ == "__main__":
    main()
