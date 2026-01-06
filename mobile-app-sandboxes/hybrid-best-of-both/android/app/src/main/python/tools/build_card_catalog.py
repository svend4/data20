#!/usr/bin/env python3
"""
Card Catalog (Карточный каталог) - Множественные индексы
Вдохновлено: Library Card Catalog системой (1800-е годы)

Создаёт несколько видов индексов для одного и того же набора статей:
- По автору (Author Index)
- По заголовку (Title Index)
- По предмету/теме (Subject Index)
- По дате (Chronological Index)
- По ключевым словам (Keyword Index)
- По категории (Category Index)
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
from datetime import datetime
import json
import csv
import argparse


class CardCatalog:
    """
    Карточный каталог - система множественных индексов
    Каждая статья индексируется по разным критериям
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Хранилища для разных индексов
        self.by_author = defaultdict(list)
        self.by_title = {}
        self.by_subject = defaultdict(list)
        self.by_date = defaultdict(list)
        self.by_keyword = defaultdict(list)
        self.by_category = defaultdict(list)
        self.by_dewey = defaultdict(list)
        self.by_status = defaultdict(list)

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

    def add_to_catalog(self, file_path, frontmatter):
        """Добавить статью во все индексы"""
        relative_path = str(file_path.relative_to(self.root_dir))

        # Базовая информация
        title = frontmatter.get('title', file_path.stem)
        author = frontmatter.get('author', frontmatter.get('source', 'Неизвестен'))
        date = frontmatter.get('date', 'Без даты')
        category = frontmatter.get('category', 'Без категории')
        subcategory = frontmatter.get('subcategory', '')
        tags = frontmatter.get('tags', [])
        status = frontmatter.get('status', 'draft')
        dewey = frontmatter.get('dewey', '')

        # Создать карточку
        card = {
            'title': title,
            'file': relative_path,
            'author': author,
            'date': date,
            'category': category,
            'subcategory': subcategory,
            'tags': tags,
            'status': status,
            'dewey': dewey
        }

        # Индекс по автору
        self.by_author[author].append(card)

        # Индекс по заголовку (первая буква)
        first_letter = self.get_first_letter(title)
        if first_letter not in self.by_title:
            self.by_title[first_letter] = []
        self.by_title[first_letter].append(card)

        # Индекс по предмету (категория + подкатегория)
        subject = f"{category}/{subcategory}" if subcategory else category
        self.by_subject[subject].append(card)

        # Индекс по дате
        date_key = self.extract_year_month(date)
        self.by_date[date_key].append(card)

        # Индекс по ключевым словам
        for tag in tags:
            self.by_keyword[tag].append(card)

        # Индекс по категории
        self.by_category[category].append(card)

        # Индекс по Dewey номеру
        if dewey:
            self.by_dewey[dewey].append(card)

        # Индекс по статусу
        self.by_status[status].append(card)

    def get_first_letter(self, text):
        """Получить первую значимую букву"""
        text = text.strip().upper()
        if not text:
            return '#'

        first_char = text[0]

        # Кириллица
        if 'А' <= first_char <= 'Я' or first_char == 'Ё':
            return first_char

        # Латиница
        if 'A' <= first_char <= 'Z':
            return first_char

        # Цифры и прочее
        return '#'

    def extract_year_month(self, date_str):
        """Извлечь год-месяц из даты"""
        if not date_str or date_str == 'Без даты':
            return 'Без даты'

        # Попробовать разные форматы
        try:
            # ISO формат: 2026-01-02
            if isinstance(date_str, str) and '-' in date_str:
                parts = date_str.split('-')
                if len(parts) >= 2:
                    return f"{parts[0]}-{parts[1]}"

            # Datetime объект
            if hasattr(date_str, 'strftime'):
                return date_str.strftime('%Y-%m')
        except:
            pass

        return str(date_str)[:7] if len(str(date_str)) >= 7 else 'Без даты'

    def build(self):
        """Построить все индексы"""
        print("📇 Построение карточного каталога...")
        print("   Вдохновлено библиотечными картотеками XIX века\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)
            if frontmatter:
                self.add_to_catalog(md_file, frontmatter)
                count += 1

        print(f"   Проиндексировано статей: {count}")
        print(f"   Создано индексов: 8 видов\n")

    def save_author_index(self, output_file):
        """Сохранить индекс по авторам"""
        lines = []
        lines.append("# 📇 Индекс по авторам\n\n")
        lines.append("> Все статьи, отсортированные по автору/источнику\n\n")

        for author in sorted(self.by_author.keys()):
            cards = self.by_author[author]
            lines.append(f"## {author} ({len(cards)} статей)\n\n")

            # Сортировать по заголовку
            for card in sorted(cards, key=lambda x: x['title']):
                lines.append(f"- **{card['title']}**\n")
                lines.append(f"  - 📂 `{card['file']}`\n")
                lines.append(f"  - 📅 {card['date']}\n")
                lines.append(f"  - 🏷️  {card['category']}/{card['subcategory']}\n")
                if card['tags']:
                    tags_str = ', '.join(card['tags'][:5])
                    lines.append(f"  - 🔖 {tags_str}\n")
                lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Индекс по авторам: {output_file}")

    def save_title_index(self, output_file):
        """Сохранить алфавитный индекс по заголовкам"""
        lines = []
        lines.append("# 📇 Алфавитный указатель (Title Index)\n\n")
        lines.append("> Все статьи от А до Я\n\n")

        for letter in sorted(self.by_title.keys()):
            cards = self.by_title[letter]
            lines.append(f"## {letter}\n\n")

            # Сортировать по заголовку
            for card in sorted(cards, key=lambda x: x['title'].lower()):
                lines.append(f"### {card['title']}\n\n")
                lines.append(f"- 📂 `{card['file']}`\n")
                lines.append(f"- 👤 {card['author']}\n")
                lines.append(f"- 📅 {card['date']}\n")
                lines.append(f"- 🏷️  {card['category']}/{card['subcategory']}\n")
                if card['dewey']:
                    lines.append(f"- 📚 Dewey: {card['dewey']}\n")
                lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Алфавитный указатель: {output_file}")

    def save_subject_index(self, output_file):
        """Сохранить предметный указатель"""
        lines = []
        lines.append("# 📇 Предметный указатель (Subject Index)\n\n")
        lines.append("> Статьи по темам и предметам\n\n")

        for subject in sorted(self.by_subject.keys()):
            cards = self.by_subject[subject]
            lines.append(f"## {subject} ({len(cards)} статей)\n\n")

            for card in sorted(cards, key=lambda x: x['title']):
                lines.append(f"- **{card['title']}**")
                if card['dewey']:
                    lines.append(f" *[{card['dewey']}]*")
                lines.append("\n")
                lines.append(f"  - 📂 `{card['file']}`\n")
                lines.append(f"  - 📅 {card['date']}\n")
                lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Предметный указатель: {output_file}")

    def save_chronological_index(self, output_file):
        """Сохранить хронологический индекс"""
        lines = []
        lines.append("# 📇 Хронологический указатель (Chronological Index)\n\n")
        lines.append("> Статьи по датам публикации\n\n")

        # Сортировать по дате (в обратном порядке - новые первыми)
        for date_key in sorted(self.by_date.keys(), reverse=True):
            if date_key == 'Без даты':
                continue

            cards = self.by_date[date_key]
            lines.append(f"## {date_key} ({len(cards)} статей)\n\n")

            for card in sorted(cards, key=lambda x: x['date'], reverse=True):
                lines.append(f"- **{card['title']}** — {card['date']}\n")
                lines.append(f"  - 🏷️  {card['category']}/{card['subcategory']}\n")
                lines.append(f"  - 📂 `{card['file']}`\n")
                lines.append("\n")

        # Статьи без даты в конце
        if 'Без даты' in self.by_date:
            cards = self.by_date['Без даты']
            lines.append(f"## Без даты ({len(cards)} статей)\n\n")
            for card in cards:
                lines.append(f"- **{card['title']}**\n")
                lines.append(f"  - 📂 `{card['file']}`\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Хронологический указатель: {output_file}")

    def save_keyword_index(self, output_file):
        """Сохранить индекс по ключевым словам"""
        lines = []
        lines.append("# 📇 Индекс ключевых слов (Keyword Index)\n\n")
        lines.append("> Все статьи, отсортированные по тегам и ключевым словам\n\n")

        # Сортировать по частоте (популярные теги первыми)
        keyword_counts = [(kw, len(cards)) for kw, cards in self.by_keyword.items()]
        keyword_counts.sort(key=lambda x: (-x[1], x[0]))

        for keyword, count in keyword_counts:
            cards = self.by_keyword[keyword]
            lines.append(f"## {keyword} ({count} статей)\n\n")

            for card in sorted(cards, key=lambda x: x['title']):
                lines.append(f"- **{card['title']}**\n")
                lines.append(f"  - 🏷️  {card['category']}\n")
                lines.append(f"  - 📂 `{card['file']}`\n")
                lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Индекс ключевых слов: {output_file}")

    def save_dewey_index(self, output_file):
        """Сохранить индекс по Dewey номерам"""
        lines = []
        lines.append("# 📇 Dewey Decimal Index\n\n")
        lines.append("> Статьи по классификации Дьюи\n\n")

        for dewey in sorted(self.by_dewey.keys()):
            cards = self.by_dewey[dewey]
            lines.append(f"## {dewey} ({len(cards)} статей)\n\n")

            for card in sorted(cards, key=lambda x: x['title']):
                lines.append(f"- **{card['title']}**\n")
                lines.append(f"  - 🏷️  {card['category']}/{card['subcategory']}\n")
                lines.append(f"  - 📂 `{card['file']}`\n")
                lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Dewey Decimal Index: {output_file}")

    def save_master_catalog(self, output_file):
        """Сохранить главный каталог со ссылками на все индексы"""
        lines = []
        lines.append("# 📇 Карточный каталог (Card Catalog)\n\n")
        lines.append("> Множественные индексы базы знаний\n\n")
        lines.append("## О системе\n\n")
        lines.append("Карточный каталог — это система множественных индексов, где каждая статья\n")
        lines.append("может быть найдена разными способами, как в библиотечной картотеке.\n\n")

        lines.append("## 📚 Доступные индексы\n\n")

        lines.append("### 1. 👤 [Индекс по авторам](catalogs/by_author.md)\n")
        lines.append(f"   - {len(self.by_author)} авторов/источников\n")
        lines.append("   - Найти все статьи одного автора\n\n")

        lines.append("### 2. 🔤 [Алфавитный указатель](catalogs/by_title.md)\n")
        lines.append(f"   - {len(self.by_title)} разделов (A-Z, А-Я)\n")
        lines.append("   - Найти статью по названию\n\n")

        lines.append("### 3. 📚 [Предметный указатель](catalogs/by_subject.md)\n")
        lines.append(f"   - {len(self.by_subject)} тем/предметов\n")
        lines.append("   - Найти статьи по теме\n\n")

        lines.append("### 4. 📅 [Хронологический указатель](catalogs/by_date.md)\n")
        lines.append(f"   - {len([k for k in self.by_date.keys() if k != 'Без даты'])} периодов\n")
        lines.append("   - Найти статьи по дате публикации\n\n")

        lines.append("### 5. 🔖 [Индекс ключевых слов](catalogs/by_keyword.md)\n")
        lines.append(f"   - {len(self.by_keyword)} ключевых слов\n")
        lines.append("   - Найти статьи по тегам\n\n")

        lines.append("### 6. 🏷️  [Индекс по категориям](catalogs/by_category.md)\n")
        lines.append(f"   - {len(self.by_category)} категорий\n")
        lines.append("   - Найти статьи по основной категории\n\n")

        lines.append("### 7. 📖 [Dewey Decimal Index](catalogs/by_dewey.md)\n")
        lines.append(f"   - {len(self.by_dewey)} классификационных номеров\n")
        lines.append("   - Библиотечная классификация\n\n")

        lines.append("### 8. ✅ [Индекс по статусу](catalogs/by_status.md)\n")
        lines.append(f"   - {len(self.by_status)} статусов\n")
        lines.append("   - Найти черновики, опубликованные, архивные\n\n")

        lines.append("## Статистика\n\n")

        total_articles = sum(len(cards) for cards in self.by_category.values())
        lines.append(f"- **Всего статей**: {total_articles}\n")
        lines.append(f"- **Авторов/источников**: {len(self.by_author)}\n")
        lines.append(f"- **Категорий**: {len(self.by_category)}\n")
        lines.append(f"- **Предметов**: {len(self.by_subject)}\n")
        lines.append(f"- **Ключевых слов**: {len(self.by_keyword)}\n")
        lines.append(f"- **Классификационных номеров**: {len(self.by_dewey)}\n\n")

        lines.append("## Использование\n\n")
        lines.append("Выберите нужный индекс в зависимости от того, что вы знаете:\n\n")
        lines.append("- Знаете автора? → [Индекс по авторам](catalogs/by_author.md)\n")
        lines.append("- Знаете название? → [Алфавитный указатель](catalogs/by_title.md)\n")
        lines.append("- Знаете тему? → [Предметный указатель](catalogs/by_subject.md)\n")
        lines.append("- Помните примерную дату? → [Хронологический указатель](catalogs/by_date.md)\n")
        lines.append("- Есть ключевое слово? → [Индекс ключевых слов](catalogs/by_keyword.md)\n")
        lines.append("- Знаете категорию? → [Индекс по категориям](catalogs/by_category.md)\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Главный каталог: {output_file}")

    def save_category_index(self, output_file):
        """Сохранить индекс по категориям"""
        lines = []
        lines.append("# 📇 Индекс по категориям\n\n")

        for category in sorted(self.by_category.keys()):
            cards = self.by_category[category]
            lines.append(f"## {category.title()} ({len(cards)} статей)\n\n")

            # Группировать по подкатегориям
            by_subcat = defaultdict(list)
            for card in cards:
                subcat = card['subcategory'] or 'Общие'
                by_subcat[subcat].append(card)

            for subcat in sorted(by_subcat.keys()):
                lines.append(f"### {subcat}\n\n")
                for card in sorted(by_subcat[subcat], key=lambda x: x['title']):
                    lines.append(f"- **{card['title']}**\n")
                    lines.append(f"  - 📂 `{card['file']}`\n")
                    lines.append(f"  - 📅 {card['date']}\n")
                    lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Индекс по категориям: {output_file}")

    def save_status_index(self, output_file):
        """Сохранить индекс по статусам"""
        lines = []
        lines.append("# 📇 Индекс по статусу публикации\n\n")

        status_order = ['published', 'reviewed', 'draft', 'archived']

        for status in status_order:
            if status in self.by_status:
                cards = self.by_status[status]
                lines.append(f"## {status.title()} ({len(cards)} статей)\n\n")

                for card in sorted(cards, key=lambda x: x['date'], reverse=True):
                    lines.append(f"- **{card['title']}** — {card['date']}\n")
                    lines.append(f"  - 🏷️  {card['category']}/{card['subcategory']}\n")
                    lines.append(f"  - 📂 `{card['file']}`\n")
                    lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Индекс по статусу: {output_file}")


class CatalogAnalyzer:
    """
    Статистический анализ карточного каталога
    Анализирует распределение статей по разным критериям
    """

    def __init__(self, catalog):
        self.catalog = catalog

    def analyze_distribution(self):
        """Анализ распределения статей"""
        total_articles = sum(len(cards) for cards in self.catalog.by_category.values())

        analysis = {
            'total_articles': total_articles,
            'total_authors': len(self.catalog.by_author),
            'total_categories': len(self.catalog.by_category),
            'total_subjects': len(self.catalog.by_subject),
            'total_keywords': len(self.catalog.by_keyword),
            'total_statuses': len(self.catalog.by_status)
        }

        # Топ авторы
        author_counts = [(author, len(cards)) for author, cards in self.catalog.by_author.items()]
        author_counts.sort(key=lambda x: -x[1])
        analysis['top_authors'] = author_counts[:10]

        # Топ категории
        category_counts = [(cat, len(cards)) for cat, cards in self.catalog.by_category.items()]
        category_counts.sort(key=lambda x: -x[1])
        analysis['top_categories'] = category_counts[:10]

        # Топ ключевые слова
        keyword_counts = [(kw, len(cards)) for kw, cards in self.catalog.by_keyword.items()]
        keyword_counts.sort(key=lambda x: -x[1])
        analysis['top_keywords'] = keyword_counts[:20]

        # Распределение по статусам
        status_dist = {status: len(cards) for status, cards in self.catalog.by_status.items()}
        analysis['status_distribution'] = status_dist

        # Распределение по датам
        date_counts = [(date, len(cards)) for date, cards in self.catalog.by_date.items() if date != 'Без даты']
        date_counts.sort(key=lambda x: x[0], reverse=True)
        analysis['recent_periods'] = date_counts[:12]

        return analysis

    def calculate_diversity(self):
        """Вычислить индекс разнообразия каталога"""
        total_articles = sum(len(cards) for cards in self.catalog.by_category.values())

        if total_articles == 0:
            return 0.0

        # Shannon diversity index для категорий
        category_counts = [len(cards) for cards in self.catalog.by_category.values()]
        diversity = 0.0

        for count in category_counts:
            if count > 0:
                p = count / total_articles
                diversity -= p * (p ** 0.5)  # Simplified Shannon index

        return round(diversity * 100, 2)

    def find_prolific_authors(self, min_articles=3):
        """Найти самых продуктивных авторов"""
        prolific = []

        for author, cards in self.catalog.by_author.items():
            if len(cards) >= min_articles:
                avg_tags = sum(len(c['tags']) for c in cards) / len(cards)
                categories = set(c['category'] for c in cards)

                prolific.append({
                    'author': author,
                    'articles': len(cards),
                    'categories': len(categories),
                    'avg_tags': round(avg_tags, 1)
                })

        prolific.sort(key=lambda x: -x['articles'])
        return prolific

    def analyze_temporal_trends(self):
        """Анализ временных трендов публикаций"""
        trends = {}

        for date_key, cards in self.catalog.by_date.items():
            if date_key == 'Без даты':
                continue

            trends[date_key] = {
                'count': len(cards),
                'categories': len(set(c['category'] for c in cards)),
                'authors': len(set(c['author'] for c in cards))
            }

        return dict(sorted(trends.items(), reverse=True)[:24])

    def save_analysis_report(self, output_file):
        """Сохранить отчёт анализа"""
        analysis = self.analyze_distribution()
        diversity = self.calculate_diversity()
        prolific = self.find_prolific_authors()
        trends = self.analyze_temporal_trends()

        lines = []
        lines.append("# 📊 Анализ карточного каталога\n\n")

        lines.append("## Общая статистика\n\n")
        lines.append(f"- **Всего статей**: {analysis['total_articles']}\n")
        lines.append(f"- **Авторов**: {analysis['total_authors']}\n")
        lines.append(f"- **Категорий**: {analysis['total_categories']}\n")
        lines.append(f"- **Предметов**: {analysis['total_subjects']}\n")
        lines.append(f"- **Ключевых слов**: {analysis['total_keywords']}\n")
        lines.append(f"- **Индекс разнообразия**: {diversity}%\n\n")

        lines.append("## 👥 Топ-10 авторов\n\n")
        for i, (author, count) in enumerate(analysis['top_authors'], 1):
            lines.append(f"{i}. **{author}** — {count} статей\n")
        lines.append("\n")

        lines.append("## 🏷️ Топ-10 категорий\n\n")
        for i, (cat, count) in enumerate(analysis['top_categories'], 1):
            lines.append(f"{i}. **{cat}** — {count} статей\n")
        lines.append("\n")

        lines.append("## 🔖 Топ-20 ключевых слов\n\n")
        for i, (kw, count) in enumerate(analysis['top_keywords'], 1):
            lines.append(f"{i}. `{kw}` — {count} статей\n")
        lines.append("\n")

        lines.append("## ✅ Распределение по статусам\n\n")
        for status, count in analysis['status_distribution'].items():
            lines.append(f"- **{status}**: {count} статей\n")
        lines.append("\n")

        lines.append("## 🚀 Самые продуктивные авторы (3+ статей)\n\n")
        for author_info in prolific[:15]:
            lines.append(f"### {author_info['author']}\n\n")
            lines.append(f"- Статей: {author_info['articles']}\n")
            lines.append(f"- Категорий: {author_info['categories']}\n")
            lines.append(f"- Ср. тегов на статью: {author_info['avg_tags']}\n\n")

        lines.append("## 📈 Временные тренды\n\n")
        for period, stats in list(trends.items())[:12]:
            lines.append(f"### {period}\n\n")
            lines.append(f"- Статей: {stats['count']}\n")
            lines.append(f"- Категорий: {stats['categories']}\n")
            lines.append(f"- Авторов: {stats['authors']}\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"📊 Отчёт анализа сохранён: {output_file}")


class CrossReferenceBuilder:
    """
    Построение перекрёстных ссылок между индексами
    Находит связи между авторами, категориями, ключевыми словами
    """

    def __init__(self, catalog):
        self.catalog = catalog

    def build_author_category_matrix(self):
        """Матрица: какие категории предпочитает каждый автор"""
        matrix = {}

        for author, cards in self.catalog.by_author.items():
            category_counts = Counter(card['category'] for card in cards)
            matrix[author] = dict(category_counts.most_common(5))

        return matrix

    def build_category_keyword_matrix(self):
        """Матрица: какие ключевые слова популярны в каждой категории"""
        matrix = {}

        for category, cards in self.catalog.by_category.items():
            keyword_counts = Counter()
            for card in cards:
                for tag in card['tags']:
                    keyword_counts[tag] += 1

            matrix[category] = dict(keyword_counts.most_common(10))

        return matrix

    def find_author_collaborations(self):
        """Найти авторов с похожими интересами (по категориям и ключевым словам)"""
        author_interests = {}

        for author, cards in self.catalog.by_author.items():
            categories = set(card['category'] for card in cards)
            keywords = set()
            for card in cards:
                keywords.update(card['tags'])

            author_interests[author] = {
                'categories': categories,
                'keywords': keywords
            }

        # Найти похожих авторов
        collaborations = []
        authors = list(author_interests.keys())

        for i, author1 in enumerate(authors):
            for author2 in authors[i+1:]:
                int1 = author_interests[author1]
                int2 = author_interests[author2]

                common_cats = int1['categories'] & int2['categories']
                common_kws = int1['keywords'] & int2['keywords']

                if len(common_cats) >= 1 or len(common_kws) >= 3:
                    collaborations.append({
                        'author1': author1,
                        'author2': author2,
                        'common_categories': len(common_cats),
                        'common_keywords': len(common_kws),
                        'similarity': len(common_kws) + len(common_cats) * 2
                    })

        collaborations.sort(key=lambda x: -x['similarity'])
        return collaborations[:20]

    def build_dewey_category_mapping(self):
        """Сопоставление Dewey номеров с категориями"""
        mapping = defaultdict(lambda: defaultdict(int))

        for dewey, cards in self.catalog.by_dewey.items():
            for card in cards:
                mapping[dewey][card['category']] += 1

        return dict(mapping)

    def save_cross_references(self, output_file):
        """Сохранить перекрёстные ссылки"""
        author_cat_matrix = self.build_author_category_matrix()
        cat_kw_matrix = self.build_category_keyword_matrix()
        collaborations = self.find_author_collaborations()
        dewey_mapping = self.build_dewey_category_mapping()

        lines = []
        lines.append("# 🔗 Перекрёстные ссылки каталога\n\n")

        lines.append("## 👥↔️🏷️ Авторы и их предпочтительные категории\n\n")
        for author, categories in sorted(author_cat_matrix.items()):
            if not categories:
                continue
            lines.append(f"### {author}\n\n")
            for cat, count in categories.items():
                lines.append(f"- {cat}: {count} статей\n")
            lines.append("\n")

        lines.append("## 🏷️↔️🔖 Популярные ключевые слова по категориям\n\n")
        for category, keywords in sorted(cat_kw_matrix.items()):
            if not keywords:
                continue
            lines.append(f"### {category}\n\n")
            for kw, count in keywords.items():
                lines.append(f"- `{kw}`: {count} статей\n")
            lines.append("\n")

        lines.append("## 🤝 Авторы с похожими интересами\n\n")
        for collab in collaborations:
            lines.append(f"### {collab['author1']} ↔️ {collab['author2']}\n\n")
            lines.append(f"- Общих категорий: {collab['common_categories']}\n")
            lines.append(f"- Общих ключевых слов: {collab['common_keywords']}\n")
            lines.append(f"- Индекс схожести: {collab['similarity']}\n\n")

        if dewey_mapping:
            lines.append("## 📚 Dewey ↔️ Категории\n\n")
            for dewey, categories in sorted(dewey_mapping.items()):
                lines.append(f"### {dewey}\n\n")
                for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                    lines.append(f"- {cat}: {count} статей\n")
                lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"🔗 Перекрёстные ссылки сохранены: {output_file}")


class CatalogVisualizer:
    """
    HTML визуализация карточного каталога
    Создаёт интерактивный dashboard с графиками
    """

    def __init__(self, catalog):
        self.catalog = catalog

    def create_html_dashboard(self, output_file):
        """Создать HTML dashboard с визуализациями"""
        total_articles = sum(len(cards) for cards in self.catalog.by_category.values())

        # Данные для графиков
        top_categories = sorted(
            [(cat, len(cards)) for cat, cards in self.catalog.by_category.items()],
            key=lambda x: -x[1]
        )[:10]

        top_authors = sorted(
            [(author, len(cards)) for author, cards in self.catalog.by_author.items()],
            key=lambda x: -x[1]
        )[:10]

        top_keywords = sorted(
            [(kw, len(cards)) for kw, cards in self.catalog.by_keyword.items()],
            key=lambda x: -x[1]
        )[:15]

        # Распределение по статусам
        status_data = {status: len(cards) for status, cards in self.catalog.by_status.items()}

        # Временное распределение
        date_data = sorted(
            [(date, len(cards)) for date, cards in self.catalog.by_date.items() if date != 'Без даты'],
            key=lambda x: x[0]
        )[-12:]

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📇 Card Catalog Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 40px;
            font-size: 1.2em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        .chart-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #333;
            font-weight: 600;
        }}
        .chart-container {{
            position: relative;
            height: 350px;
        }}
        .index-list {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-top: 30px;
        }}
        .index-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .index-item {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        .index-item h3 {{
            color: #667eea;
            margin-bottom: 8px;
        }}
        .index-item p {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📇 Card Catalog Dashboard</h1>
        <p class="subtitle">Интерактивная статистика карточного каталога</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_articles}</div>
                <div class="stat-label">Всего статей</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.catalog.by_author)}</div>
                <div class="stat-label">Авторов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.catalog.by_category)}</div>
                <div class="stat-label">Категорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.catalog.by_keyword)}</div>
                <div class="stat-label">Ключевых слов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.catalog.by_subject)}</div>
                <div class="stat-label">Предметов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.catalog.by_dewey)}</div>
                <div class="stat-label">Dewey классов</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <h2 class="chart-title">📊 Топ-10 категорий</h2>
                <div class="chart-container">
                    <canvas id="categoriesChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">👥 Топ-10 авторов</h2>
                <div class="chart-container">
                    <canvas id="authorsChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">✅ Распределение по статусам</h2>
                <div class="chart-container">
                    <canvas id="statusChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">🔖 Топ-15 ключевых слов</h2>
                <div class="chart-container">
                    <canvas id="keywordsChart"></canvas>
                </div>
            </div>
        </div>

        <div class="chart-card" style="margin-bottom: 30px;">
            <h2 class="chart-title">📈 Публикации по периодам</h2>
            <div class="chart-container">
                <canvas id="timelineChart"></canvas>
            </div>
        </div>

        <div class="index-list">
            <h2 class="chart-title">📚 Доступные индексы</h2>
            <div class="index-grid">
                <div class="index-item">
                    <h3>👤 Индекс по авторам</h3>
                    <p>{len(self.catalog.by_author)} авторов/источников</p>
                </div>
                <div class="index-item">
                    <h3>🔤 Алфавитный указатель</h3>
                    <p>{len(self.catalog.by_title)} разделов (A-Z, А-Я)</p>
                </div>
                <div class="index-item">
                    <h3>📚 Предметный указатель</h3>
                    <p>{len(self.catalog.by_subject)} тем/предметов</p>
                </div>
                <div class="index-item">
                    <h3>📅 Хронологический</h3>
                    <p>{len([k for k in self.catalog.by_date.keys() if k != 'Без даты'])} периодов</p>
                </div>
                <div class="index-item">
                    <h3>🔖 Ключевые слова</h3>
                    <p>{len(self.catalog.by_keyword)} ключевых слов</p>
                </div>
                <div class="index-item">
                    <h3>🏷️ По категориям</h3>
                    <p>{len(self.catalog.by_category)} категорий</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Топ категории
        new Chart(document.getElementById('categoriesChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([cat for cat, _ in top_categories])},
                datasets: [{{
                    label: 'Статей',
                    data: {json.dumps([count for _, count in top_categories])},
                    backgroundColor: '#667eea',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Топ авторы
        new Chart(document.getElementById('authorsChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([author[:30] for author, _ in top_authors])},
                datasets: [{{
                    label: 'Статей',
                    data: {json.dumps([count for _, count in top_authors])},
                    backgroundColor: '#764ba2',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Статусы (pie chart)
        new Chart(document.getElementById('statusChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(list(status_data.keys()))},
                datasets: [{{
                    data: {json.dumps(list(status_data.values()))},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false
            }}
        }});

        // Ключевые слова
        new Chart(document.getElementById('keywordsChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([kw for kw, _ in top_keywords])},
                datasets: [{{
                    label: 'Статей',
                    data: {json.dumps([count for _, count in top_keywords])},
                    backgroundColor: '#f093fb',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Временная линия
        new Chart(document.getElementById('timelineChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([date for date, _ in date_data])},
                datasets: [{{
                    label: 'Публикаций',
                    data: {json.dumps([count for _, count in date_data])},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: true }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"🎨 HTML dashboard сохранён: {output_file}")


class CatalogSearcher:
    """
    Продвинутый поиск по карточному каталогу
    Поддерживает фильтры и комбинированные запросы
    """

    def __init__(self, catalog):
        self.catalog = catalog

    def search(self, query, filters=None):
        """
        Поиск по каталогу с фильтрами

        filters: {
            'author': str,
            'category': str,
            'keyword': str,
            'date_from': str,
            'date_to': str,
            'status': str
        }
        """
        results = []
        query_lower = query.lower() if query else ''

        # Собрать все карточки
        all_cards = []
        for cards in self.catalog.by_category.values():
            all_cards.extend(cards)

        # Убрать дубликаты
        seen_files = set()
        unique_cards = []
        for card in all_cards:
            if card['file'] not in seen_files:
                unique_cards.append(card)
                seen_files.add(card['file'])

        # Применить фильтры
        for card in unique_cards:
            # Текстовый поиск
            if query_lower:
                title_match = query_lower in card['title'].lower()
                category_match = query_lower in card['category'].lower()
                tags_match = any(query_lower in tag.lower() for tag in card['tags'])

                if not (title_match or category_match or tags_match):
                    continue

            # Фильтры
            if filters:
                if 'author' in filters and filters['author']:
                    if filters['author'].lower() not in card['author'].lower():
                        continue

                if 'category' in filters and filters['category']:
                    if filters['category'].lower() not in card['category'].lower():
                        continue

                if 'keyword' in filters and filters['keyword']:
                    if not any(filters['keyword'].lower() in tag.lower() for tag in card['tags']):
                        continue

                if 'status' in filters and filters['status']:
                    if card['status'] != filters['status']:
                        continue

            results.append(card)

        return results

    def save_search_results(self, results, output_file, query):
        """Сохранить результаты поиска"""
        lines = []
        lines.append(f"# 🔍 Результаты поиска: {query}\n\n")
        lines.append(f"Найдено: **{len(results)}** статей\n\n")

        for i, card in enumerate(results, 1):
            lines.append(f"## {i}. {card['title']}\n\n")
            lines.append(f"- 📂 `{card['file']}`\n")
            lines.append(f"- 👤 {card['author']}\n")
            lines.append(f"- 📅 {card['date']}\n")
            lines.append(f"- 🏷️ {card['category']}/{card['subcategory']}\n")
            lines.append(f"- ✅ {card['status']}\n")
            if card['tags']:
                lines.append(f"- 🔖 {', '.join(card['tags'])}\n")
            if card['dewey']:
                lines.append(f"- 📚 Dewey: {card['dewey']}\n")
            lines.append("\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"🔍 Результаты поиска сохранены: {output_file}")
        return len(results)

    def export_to_json(self, results, output_file):
        """Экспорт результатов в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"📄 JSON экспорт: {output_file}")

    def export_to_csv(self, results, output_file):
        """Экспорт результатов в CSV"""
        if not results:
            print("⚠️ Нет результатов для экспорта")
            return

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'file', 'author', 'date', 'category', 'subcategory', 'status', 'dewey'])
            writer.writeheader()

            for card in results:
                writer.writerow({
                    'title': card['title'],
                    'file': card['file'],
                    'author': card['author'],
                    'date': card['date'],
                    'category': card['category'],
                    'subcategory': card['subcategory'],
                    'status': card['status'],
                    'dewey': card['dewey']
                })

        print(f"📊 CSV экспорт: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='📇 Card Catalog - Система множественных индексов для базы знаний',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                          # Построить все индексы
  %(prog)s --html                   # Создать HTML dashboard
  %(prog)s --analyze                # Статистический анализ
  %(prog)s --cross-refs             # Перекрёстные ссылки
  %(prog)s --search "python"        # Поиск по каталогу
  %(prog)s --search "ML" --filter-category "ai"  # Поиск с фильтром
  %(prog)s --json                   # Экспорт в JSON
  %(prog)s --csv                    # Экспорт в CSV
  %(prog)s --all                    # Все опции
        """
    )

    parser.add_argument('--html', action='store_true',
                       help='🎨 Создать HTML dashboard с графиками')
    parser.add_argument('--analyze', action='store_true',
                       help='📊 Выполнить статистический анализ каталога')
    parser.add_argument('--cross-refs', action='store_true',
                       help='🔗 Построить перекрёстные ссылки между индексами')
    parser.add_argument('--search', type=str, metavar='QUERY',
                       help='🔍 Поиск по каталогу')
    parser.add_argument('--filter-author', type=str, metavar='AUTHOR',
                       help='👤 Фильтр по автору')
    parser.add_argument('--filter-category', type=str, metavar='CATEGORY',
                       help='🏷️ Фильтр по категории')
    parser.add_argument('--filter-keyword', type=str, metavar='KEYWORD',
                       help='🔖 Фильтр по ключевому слову')
    parser.add_argument('--filter-status', type=str, metavar='STATUS',
                       help='✅ Фильтр по статусу (published, draft, etc.)')
    parser.add_argument('--json', action='store_true',
                       help='📄 Экспорт результатов в JSON')
    parser.add_argument('--csv', action='store_true',
                       help='📊 Экспорт результатов в CSV')
    parser.add_argument('--all', action='store_true',
                       help='🚀 Выполнить все опции (HTML, анализ, перекрёстные ссылки)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Создать и построить каталог
    catalog = CardCatalog(root_dir)
    catalog.build()

    # Создать директорию для каталогов
    catalogs_dir = root_dir / "catalogs"
    catalogs_dir.mkdir(exist_ok=True)

    # Базовые индексы (всегда создаются)
    print("\n📝 Сохранение базовых индексов...\n")
    catalog.save_master_catalog(root_dir / "CARD_CATALOG.md")
    catalog.save_author_index(catalogs_dir / "by_author.md")
    catalog.save_title_index(catalogs_dir / "by_title.md")
    catalog.save_subject_index(catalogs_dir / "by_subject.md")
    catalog.save_chronological_index(catalogs_dir / "by_date.md")
    catalog.save_keyword_index(catalogs_dir / "by_keyword.md")
    catalog.save_category_index(catalogs_dir / "by_category.md")
    catalog.save_dewey_index(catalogs_dir / "by_dewey.md")
    catalog.save_status_index(catalogs_dir / "by_status.md")

    # HTML dashboard
    if args.html or args.all:
        print("\n🎨 Создание HTML dashboard...\n")
        visualizer = CatalogVisualizer(catalog)
        visualizer.create_html_dashboard(root_dir / "CARD_CATALOG_DASHBOARD.html")

    # Статистический анализ
    if args.analyze or args.all:
        print("\n📊 Анализ каталога...\n")
        analyzer = CatalogAnalyzer(catalog)
        analyzer.save_analysis_report(catalogs_dir / "analysis_report.md")

    # Перекрёстные ссылки
    if args.cross_refs or args.all:
        print("\n🔗 Построение перекрёстных ссылок...\n")
        cross_ref = CrossReferenceBuilder(catalog)
        cross_ref.save_cross_references(catalogs_dir / "cross_references.md")

    # Поиск
    if args.search:
        print(f"\n🔍 Поиск: {args.search}\n")
        searcher = CatalogSearcher(catalog)

        filters = {}
        if args.filter_author:
            filters['author'] = args.filter_author
        if args.filter_category:
            filters['category'] = args.filter_category
        if args.filter_keyword:
            filters['keyword'] = args.filter_keyword
        if args.filter_status:
            filters['status'] = args.filter_status

        results = searcher.search(args.search, filters if filters else None)

        # Сохранить результаты
        searcher.save_search_results(results, catalogs_dir / "search_results.md", args.search)

        # Экспорт
        if args.json:
            searcher.export_to_json(results, catalogs_dir / "search_results.json")
        if args.csv:
            searcher.export_to_csv(results, catalogs_dir / "search_results.csv")

        print(f"\n✨ Найдено: {len(results)} статей")

    # Экспорт всего каталога
    if args.json and not args.search:
        print("\n📄 Экспорт каталога в JSON...\n")
        all_cards = []
        for cards in catalog.by_category.values():
            all_cards.extend(cards)

        # Убрать дубликаты
        seen = set()
        unique_cards = []
        for card in all_cards:
            if card['file'] not in seen:
                unique_cards.append(card)
                seen.add(card['file'])

        with open(catalogs_dir / "catalog_full.json", 'w', encoding='utf-8') as f:
            json.dump(unique_cards, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON: catalogs/catalog_full.json ({len(unique_cards)} статей)")

    if args.csv and not args.search:
        print("\n📊 Экспорт каталога в CSV...\n")
        all_cards = []
        for cards in catalog.by_category.values():
            all_cards.extend(cards)

        # Убрать дубликаты
        seen = set()
        unique_cards = []
        for card in all_cards:
            if card['file'] not in seen:
                unique_cards.append(card)
                seen.add(card['file'])

        with open(catalogs_dir / "catalog_full.csv", 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'file', 'author', 'date', 'category', 'subcategory', 'status', 'dewey'])
            writer.writeheader()
            for card in unique_cards:
                writer.writerow({
                    'title': card['title'],
                    'file': card['file'],
                    'author': card['author'],
                    'date': card['date'],
                    'category': card['category'],
                    'subcategory': card['subcategory'],
                    'status': card['status'],
                    'dewey': card['dewey']
                })
        print(f"📊 CSV: catalogs/catalog_full.csv ({len(unique_cards)} статей)")

    print("\n✨ Карточный каталог готов!")
    print(f"\n📖 Главный каталог: CARD_CATALOG.md")
    print(f"📂 Все индексы: catalogs/")


if __name__ == "__main__":
    main()
