#!/usr/bin/env python3
"""
Скрипт для автоматического обновления индексных файлов
Сканирует все статьи в базе знаний и обновляет индексы
"""

import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import yaml


class IndexUpdater:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.stats = defaultdict(lambda: defaultdict(int))

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные из frontmatter"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Поиск frontmatter между ---
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter
        except yaml.YAMLError:
            return None

    def scan_articles(self, category_path):
        """Сканировать все статьи в категории"""
        articles = []
        articles_dir = category_path / "articles"

        if not articles_dir.exists():
            return articles

        for md_file in articles_dir.rglob("*.md"):
            frontmatter = self.extract_frontmatter(md_file)
            if frontmatter:
                relative_path = md_file.relative_to(category_path)
                articles.append({
                    'path': str(relative_path),
                    'file': md_file,
                    'title': frontmatter.get('title', md_file.stem),
                    'tags': frontmatter.get('tags', []),
                    'subcategory': frontmatter.get('subcategory', 'other'),
                    'date': frontmatter.get('date', 'unknown'),
                    'status': frontmatter.get('status', 'unknown')
                })

        return articles

    def group_by_subcategory(self, articles):
        """Группировать статьи по подкатегориям"""
        grouped = defaultdict(list)
        for article in articles:
            grouped[article['subcategory']].append(article)
        return grouped

    def update_category_index(self, category_name):
        """Обновить индекс категории"""
        category_path = self.knowledge_dir / category_name
        index_file = category_path / "index" / "INDEX.md"

        if not index_file.exists():
            print(f"⚠️  Индекс не найден: {index_file}")
            return

        # Сканировать статьи
        articles = self.scan_articles(category_path)
        grouped = self.group_by_subcategory(articles)

        # Статистика
        total_articles = len(articles)
        today = datetime.now().strftime("%Y-%m-%d")

        print(f"📊 {category_name}: найдено {total_articles} статей")

        # Обновить статистику в индексе
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Обновить дату обновления в frontmatter
        content = re.sub(
            r'date_updated: \d{4}-\d{2}-\d{2}',
            f'date_updated: {today}',
            content
        )

        # Обновить статистику в секции "Статистика"
        stats_pattern = r'(##\s+Статистика.*?\n)(.*?)(\n##|\Z)'

        def update_stats(match):
            header = match.group(1)
            stats_text = (
                f"- Всего подразделов: {len(grouped)}\n"
                f"- Всего статей: {total_articles}\n"
                f"- Дата создания: {match.group(2).split('Дата создания:')[1].split('\\n')[0].strip() if 'Дата создания:' in match.group(2) else today}\n"
                f"- Дата последнего обновления: {today}\n"
            )
            return header + stats_text + match.group(3)

        content = re.sub(stats_pattern, update_stats, content, flags=re.DOTALL)

        # Сохранить обновленный индекс
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Индекс обновлен: {index_file}")

        # Сохранить статистику
        self.stats[category_name]['total'] = total_articles
        self.stats[category_name]['subcategories'] = len(grouped)

    def update_main_index(self):
        """Обновить главный индекс"""
        index_file = self.root_dir / "INDEX.md"

        if not index_file.exists():
            self.create_main_index()
            return

        total_articles = sum(cat['total'] for cat in self.stats.values())
        total_categories = len(self.stats)
        today = datetime.now().strftime("%Y-%m-%d")

        print(f"\n📊 Общая статистика:")
        print(f"   Категорий: {total_categories}")
        print(f"   Всего статей: {total_articles}")

        # Обновить статистику
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Обновить дату
        content = re.sub(
            r'date_updated: \d{4}-\d{2}-\d{2}',
            f'date_updated: {today}',
            content
        )

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Главный индекс обновлен")

    def create_main_index(self):
        """Создать главный индекс, если его нет"""
        index_file = self.root_dir / "INDEX.md"
        today = datetime.now().strftime("%Y-%m-%d")

        content = f"""---
title: "Главный индекс базы знаний"
type: main-index
date_created: {today}
date_updated: {today}
---

# База знаний: Главный индекс

## Категории знаний

### 💻 [Компьютерная техника и технологии](knowledge/computers/index/INDEX.md)
Программирование, hardware, AI, сети, базы данных и другие IT-технологии

### 🏠 [Бытовая техника и домашнее хозяйство](knowledge/household/index/INDEX.md)
Выбор и обслуживание бытовой техники, ремонт, уборка, энергоэффективность

### 🍳 [Кулинария и рецепты](knowledge/cooking/index/INDEX.md)
Рецепты, техники приготовления, кулинарные советы

## Сервисные разделы

- 📥 [Входящие материалы](inbox/) - Необработанная информация
- 📚 [Документация](docs/) - Методология и инструкции
- 🛠️ [Инструменты](tools/) - Скрипты автоматизации
- 📦 [Архив](archive/) - Устаревшая информация

## Быстрый старт

1. Новую информацию добавляйте в `inbox/raw/`
2. Обрабатывайте через скрипты в `tools/`
3. Читайте методологию в `docs/METHODOLOGY.md`
4. Используйте шаблоны из `docs/TEMPLATES.md`

## Навигация по базе знаний

**По категориям:** Используйте индексные файлы в каждой категории
**По тегам:** Поиск через grep или скрипты
**По ссылкам:** Переходите по связанным статьям

## Статистика

Обновляется автоматически через `tools/update_indexes.py`

Последнее обновление: {today}
"""

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Создан главный индекс: {index_file}")

    def run(self):
        """Запустить обновление всех индексов"""
        print("🔄 Обновление индексов базы знаний...\n")

        # Найти все категории
        categories = [d.name for d in self.knowledge_dir.iterdir()
                     if d.is_dir() and not d.name.startswith('.')]

        # Обновить индексы категорий
        for category in categories:
            self.update_category_index(category)

        # Обновить главный индекс
        self.update_main_index()

        print("\n✅ Все индексы обновлены!")


def main():
    """Точка входа"""
    # Определить корневую директорию (на уровень выше tools/)
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    updater = IndexUpdater(root_dir)
    updater.run()


if __name__ == "__main__":
    main()
