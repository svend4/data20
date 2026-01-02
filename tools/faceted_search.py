#!/usr/bin/env python3
"""
Faceted Search - Фасетный поиск
Вдохновлено: S.R. Ranganathan's Colon Classification (1933)

Позволяет фильтровать результаты по множеству независимых критериев (фасетов)
одновременно, постепенно сужая выборку.
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import argparse
import sys


class FacetedSearchEngine:
    """
    Фасетный поиск - поиск с множественными независимыми фильтрами
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Все статьи
        self.articles = []

        # Фасеты (доступные значения для фильтрации)
        self.facets = {
            'categories': set(),
            'subcategories': set(),
            'tags': set(),
            'authors': set(),
            'years': set(),
            'months': set(),
            'statuses': set(),
            'dewey': set()
        }

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                return fm
        except:
            pass
        return None

    def load_articles(self):
        """Загрузить все статьи"""
        print("📚 Загрузка базы знаний...")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)
            if not frontmatter:
                continue

            # Извлечь данные
            title = frontmatter.get('title', md_file.stem)
            category = frontmatter.get('category', '')
            subcategory = frontmatter.get('subcategory', '')
            tags = frontmatter.get('tags', [])
            author = frontmatter.get('author', frontmatter.get('source', ''))
            date = str(frontmatter.get('date', ''))
            status = frontmatter.get('status', 'draft')
            dewey = frontmatter.get('dewey', '')

            # Парсинг даты
            year = ''
            month = ''
            if date and '-' in date:
                parts = date.split('-')
                if len(parts) >= 1:
                    year = parts[0]
                if len(parts) >= 2:
                    month = f"{parts[0]}-{parts[1]}"

            article = {
                'title': title,
                'file': str(md_file.relative_to(self.root_dir)),
                'category': category,
                'subcategory': subcategory,
                'tags': tags if isinstance(tags, list) else [],
                'author': author,
                'date': date,
                'year': year,
                'month': month,
                'status': status,
                'dewey': dewey
            }

            self.articles.append(article)

            # Обновить фасеты
            if category:
                self.facets['categories'].add(category)
            if subcategory:
                self.facets['subcategories'].add(subcategory)
            if author:
                self.facets['authors'].add(author)
            if year:
                self.facets['years'].add(year)
            if month:
                self.facets['months'].add(month)
            if status:
                self.facets['statuses'].add(status)
            if dewey:
                self.facets['dewey'].add(dewey)

            for tag in article['tags']:
                self.facets['tags'].add(tag)

        print(f"   Загружено статей: {len(self.articles)}\n")

    def filter_articles(self, filters):
        """
        Применить фасетные фильтры

        filters = {
            'category': 'computers',
            'tags': ['python', 'AI'],
            'year': '2026',
            ...
        }
        """
        results = self.articles

        # Фильтр по категории
        if 'category' in filters and filters['category']:
            results = [a for a in results if a['category'] == filters['category']]

        # Фильтр по подкатегории
        if 'subcategory' in filters and filters['subcategory']:
            results = [a for a in results if a['subcategory'] == filters['subcategory']]

        # Фильтр по тегам (ИЛИ - хотя бы один тег совпадает)
        if 'tags' in filters and filters['tags']:
            filter_tags = set(filters['tags'])
            results = [a for a in results if any(tag in filter_tags for tag in a['tags'])]

        # Фильтр по тегам (И - все теги должны совпасть)
        if 'tags_all' in filters and filters['tags_all']:
            filter_tags = set(filters['tags_all'])
            results = [a for a in results if filter_tags.issubset(set(a['tags']))]

        # Фильтр по автору
        if 'author' in filters and filters['author']:
            results = [a for a in results if a['author'] == filters['author']]

        # Фильтр по году
        if 'year' in filters and filters['year']:
            results = [a for a in results if a['year'] == filters['year']]

        # Фильтр по месяцу
        if 'month' in filters and filters['month']:
            results = [a for a in results if a['month'] == filters['month']]

        # Фильтр по статусу
        if 'status' in filters and filters['status']:
            results = [a for a in results if a['status'] == filters['status']]

        # Фильтр по Dewey
        if 'dewey' in filters and filters['dewey']:
            results = [a for a in results if a['dewey'] == filters['dewey']]

        # Текстовый поиск в заголовке
        if 'query' in filters and filters['query']:
            query = filters['query'].lower()
            results = [a for a in results if query in a['title'].lower()]

        return results

    def get_facet_counts(self, current_results):
        """Получить количество документов для каждого значения фасета"""
        counts = {
            'categories': defaultdict(int),
            'subcategories': defaultdict(int),
            'tags': defaultdict(int),
            'authors': defaultdict(int),
            'years': defaultdict(int),
            'statuses': defaultdict(int),
            'dewey': defaultdict(int)
        }

        for article in current_results:
            if article['category']:
                counts['categories'][article['category']] += 1
            if article['subcategory']:
                counts['subcategories'][article['subcategory']] += 1
            if article['author']:
                counts['authors'][article['author']] += 1
            if article['year']:
                counts['years'][article['year']] += 1
            if article['status']:
                counts['statuses'][article['status']] += 1
            if article['dewey']:
                counts['dewey'][article['dewey']] += 1

            for tag in article['tags']:
                counts['tags'][tag] += 1

        return counts

    def print_results(self, results, show_facets=True):
        """Вывести результаты поиска"""
        print(f"\n📊 Найдено статей: {len(results)}\n")

        if not results:
            print("❌ Ничего не найдено\n")
            return

        # Показать фасеты (доступные фильтры)
        if show_facets and len(results) < len(self.articles):
            print("🔍 Доступные фильтры для текущей выборки:\n")
            counts = self.get_facet_counts(results)

            # Категории
            if counts['categories']:
                print("   Категории:")
                for cat, count in sorted(counts['categories'].items()):
                    print(f"      {cat}: {count}")

            # Теги (топ-10)
            if counts['tags']:
                top_tags = sorted(counts['tags'].items(), key=lambda x: -x[1])[:10]
                print("\n   Популярные теги:")
                for tag, count in top_tags:
                    print(f"      {tag}: {count}")

            # Авторы
            if counts['authors']:
                print("\n   Авторы:")
                for author, count in sorted(counts['authors'].items()):
                    print(f"      {author}: {count}")

            # Годы
            if counts['years']:
                print("\n   Годы:")
                for year, count in sorted(counts['years'].items(), reverse=True):
                    print(f"      {year}: {count}")

            print("\n" + "="*80 + "\n")

        # Вывести статьи
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   📂 {article['file']}")
            print(f"   🏷️  {article['category']}/{article['subcategory']}")
            if article['tags']:
                tags_str = ', '.join(article['tags'][:5])
                print(f"   🔖 {tags_str}")
            if article['author']:
                print(f"   👤 {article['author']}")
            if article['date']:
                print(f"   📅 {article['date']}")
            print()

    def interactive_search(self):
        """Интерактивный фасетный поиск"""
        print("\n🔍 Интерактивный фасетный поиск\n")
        print("Введите фильтры (или 'help' для справки, 'reset' для сброса, 'quit' для выхода)\n")

        filters = {}

        while True:
            # Применить текущие фильтры
            results = self.filter_articles(filters)

            # Показать текущие фильтры
            if filters:
                print(f"📌 Активные фильтры: {filters}")

            print(f"📊 Результатов: {len(results)}/{len(self.articles)}\n")

            # Показать доступные фасеты
            counts = self.get_facet_counts(results)

            print("Доступные фильтры:")
            print(f"  categories: {', '.join(sorted(counts['categories'].keys()))}")
            print(f"  tags (топ-10): {', '.join([k for k, v in sorted(counts['tags'].items(), key=lambda x: -x[1])[:10]])}")
            print(f"  years: {', '.join(sorted(counts['years'].keys(), reverse=True))}")
            print()

            # Получить команду
            command = input(">>> ").strip()

            if not command:
                continue

            if command == 'quit' or command == 'q':
                break

            if command == 'reset':
                filters = {}
                print("✅ Фильтры сброшены\n")
                continue

            if command == 'show' or command == 'results':
                self.print_results(results, show_facets=False)
                continue

            if command == 'help':
                self.print_help()
                continue

            # Парсинг команды: category=computers, tags=python,AI
            try:
                parts = command.split(',')
                for part in parts:
                    if '=' not in part:
                        print(f"⚠️  Неверный формат: {part}")
                        continue

                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key in ['tags', 'tags_all']:
                        # Множественные значения
                        filters[key] = [v.strip() for v in value.split(' ')]
                    else:
                        filters[key] = value

                print(f"✅ Фильтр добавлен: {part}\n")

            except Exception as e:
                print(f"⚠️  Ошибка: {e}\n")

    def print_help(self):
        """Вывести справку"""
        print("""
📖 Справка по фасетному поиску

Синтаксис:
  фасет=значение

Несколько фильтров (через запятую):
  category=computers, tags=python AI, year=2026

Доступные фасеты:
  category      - категория (computers, household, cooking)
  subcategory   - подкатегория
  tags          - теги (ИЛИ - хотя бы один совпадает)
  tags_all      - теги (И - все должны совпасть)
  author        - автор/источник
  year          - год публикации
  month         - месяц публикации (YYYY-MM)
  status        - статус (draft, published, archived)
  dewey         - номер Dewey классификации
  query         - текстовый поиск в заголовке

Команды:
  show, results - показать текущие результаты
  reset         - сбросить все фильтры
  help          - эта справка
  quit, q       - выход

Примеры:
  category=computers
  category=computers, tags=python AI
  tags_all=python ООП
  year=2026, status=published
  query=холодильник
        """)


def main():
    parser = argparse.ArgumentParser(
        description='Faceted Search - Фасетный поиск по базе знаний'
    )

    parser.add_argument(
        '-c', '--category',
        help='Фильтр по категории'
    )

    parser.add_argument(
        '-s', '--subcategory',
        help='Фильтр по подкатегории'
    )

    parser.add_argument(
        '-t', '--tags',
        nargs='+',
        help='Фильтр по тегам (ИЛИ)'
    )

    parser.add_argument(
        '--tags-all',
        nargs='+',
        help='Фильтр по тегам (И - все должны совпасть)'
    )

    parser.add_argument(
        '-a', '--author',
        help='Фильтр по автору'
    )

    parser.add_argument(
        '-y', '--year',
        help='Фильтр по году'
    )

    parser.add_argument(
        '--status',
        help='Фильтр по статусу'
    )

    parser.add_argument(
        '-d', '--dewey',
        help='Фильтр по Dewey номеру'
    )

    parser.add_argument(
        '-q', '--query',
        help='Текстовый поиск в заголовке'
    )

    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Интерактивный режим'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    engine = FacetedSearchEngine(root_dir)
    engine.load_articles()

    # Интерактивный режим
    if args.interactive:
        engine.interactive_search()
        return

    # Построить фильтры из аргументов
    filters = {}

    if args.category:
        filters['category'] = args.category
    if args.subcategory:
        filters['subcategory'] = args.subcategory
    if args.tags:
        filters['tags'] = args.tags
    if args.tags_all:
        filters['tags_all'] = args.tags_all
    if args.author:
        filters['author'] = args.author
    if args.year:
        filters['year'] = args.year
    if args.status:
        filters['status'] = args.status
    if args.dewey:
        filters['dewey'] = args.dewey
    if args.query:
        filters['query'] = args.query

    # Если нет фильтров - показать справку
    if not filters:
        print("🔍 Faceted Search - Фасетный поиск\n")
        print("Используйте флаги для фильтрации или -i для интерактивного режима\n")
        parser.print_help()
        print("\nПримеры:")
        print("  python tools/faceted_search.py -c computers -t python AI")
        print("  python tools/faceted_search.py -y 2026 --status published")
        print("  python tools/faceted_search.py -q холодильник")
        print("  python tools/faceted_search.py -i  # интерактивный режим")
        return

    # Применить фильтры
    results = engine.filter_articles(filters)
    engine.print_results(results)


if __name__ == "__main__":
    main()
