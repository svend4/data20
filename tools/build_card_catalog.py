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
from collections import defaultdict
from datetime import datetime


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


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    catalog = CardCatalog(root_dir)

    # Построить индексы
    catalog.build()

    # Создать директорию для каталогов
    catalogs_dir = root_dir / "catalogs"
    catalogs_dir.mkdir(exist_ok=True)

    # Сохранить все индексы
    print("\n📝 Сохранение индексов...\n")

    catalog.save_master_catalog(root_dir / "CARD_CATALOG.md")
    catalog.save_author_index(catalogs_dir / "by_author.md")
    catalog.save_title_index(catalogs_dir / "by_title.md")
    catalog.save_subject_index(catalogs_dir / "by_subject.md")
    catalog.save_chronological_index(catalogs_dir / "by_date.md")
    catalog.save_keyword_index(catalogs_dir / "by_keyword.md")
    catalog.save_category_index(catalogs_dir / "by_category.md")
    catalog.save_dewey_index(catalogs_dir / "by_dewey.md")
    catalog.save_status_index(catalogs_dir / "by_status.md")

    print("\n✨ Карточный каталог готов!")
    print(f"\n📖 Главный каталог: CARD_CATALOG.md")
    print(f"📂 Все индексы: catalogs/")


if __name__ == "__main__":
    main()
