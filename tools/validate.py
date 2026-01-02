#!/usr/bin/env python3
"""
Скрипт для валидации структуры и метаданных базы знаний
Проверяет наличие обязательных полей, корректность ссылок и т.д.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import yaml


class KnowledgeBaseValidator:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.errors = []
        self.warnings = []
        self.stats = defaultdict(int)

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные из frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not match:
                return None, content

            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter, content
        except Exception as e:
            self.errors.append(f"❌ Ошибка чтения {file_path}: {e}")
            return None, ""

    def validate_frontmatter(self, file_path, frontmatter):
        """Валидация метаданных"""
        required_fields = ['title', 'date', 'tags', 'category']

        if not frontmatter:
            self.errors.append(f"❌ {file_path}: Отсутствует frontmatter")
            return False

        # Проверка обязательных полей
        for field in required_fields:
            if field not in frontmatter:
                self.errors.append(f"❌ {file_path}: Отсутствует поле '{field}'")

        # Проверка тегов
        tags = frontmatter.get('tags', [])
        if not isinstance(tags, list):
            self.errors.append(f"❌ {file_path}: 'tags' должен быть списком")
        elif len(tags) < 3:
            self.warnings.append(f"⚠️  {file_path}: Мало тегов ({len(tags)}, рекомендуется 3+)")

        # Проверка даты
        date = frontmatter.get('date')
        if date and not re.match(r'\d{4}-\d{2}-\d{2}', str(date)):
            self.warnings.append(f"⚠️  {file_path}: Неверный формат даты '{date}' (должен быть YYYY-MM-DD)")

        # Проверка статуса
        status = frontmatter.get('status')
        valid_statuses = ['draft', 'published', 'archived', 'reviewed']
        if status and status not in valid_statuses:
            self.warnings.append(f"⚠️  {file_path}: Неизвестный статус '{status}'")

        return True

    def validate_links(self, file_path, content):
        """Проверка ссылок на другие файлы"""
        # Найти все markdown ссылки вида [text](path.md)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)

        for link_text, link_path in links:
            # Пропустить внешние ссылки
            if link_path.startswith('http'):
                continue

            # Проверить существование файла
            if link_path.startswith('/'):
                target = self.root_dir / link_path.lstrip('/')
            else:
                target = file_path.parent / link_path

            target = target.resolve()

            if not target.exists():
                self.errors.append(f"❌ {file_path}: Битая ссылка на {link_path}")

    def validate_file_naming(self, file_path):
        """Проверка соглашений об именовании файлов"""
        filename = file_path.name

        # Проверка на кириллицу в именах файлов
        if re.search(r'[а-яА-ЯёЁ]', filename):
            self.warnings.append(f"⚠️  {file_path}: Кириллица в имени файла (рекомендуется латиница)")

        # Проверка на пробелы
        if ' ' in filename:
            self.warnings.append(f"⚠️  {file_path}: Пробелы в имени файла (используйте дефисы)")

        # Проверка на uppercase
        if filename != filename.lower() and filename != 'INDEX.md' and filename != 'README.md':
            self.warnings.append(f"⚠️  {file_path}: Заглавные буквы в имени файла (рекомендуется lowercase)")

    def validate_structure(self):
        """Проверка структуры директорий"""
        required_dirs = ['inbox', 'knowledge', 'tools', 'docs', 'archive']

        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                self.warnings.append(f"⚠️  Отсутствует директория: {dir_name}")

        # Проверка категорий
        if self.knowledge_dir.exists():
            categories = [d for d in self.knowledge_dir.iterdir() if d.is_dir()]
            if len(categories) == 0:
                self.errors.append(f"❌ Нет категорий в knowledge/")

            for category in categories:
                # Проверка наличия index
                index_file = category / "index" / "INDEX.md"
                if not index_file.exists():
                    self.warnings.append(f"⚠️  Отсутствует индекс: {index_file}")

                # Проверка наличия articles
                articles_dir = category / "articles"
                if not articles_dir.exists():
                    self.warnings.append(f"⚠️  Отсутствует директория articles: {articles_dir}")

    def validate_article(self, file_path):
        """Валидация одной статьи"""
        self.stats['total_articles'] += 1

        # Извлечь frontmatter и контент
        frontmatter, content = self.extract_frontmatter(file_path)

        # Валидация frontmatter
        if frontmatter:
            self.stats['with_frontmatter'] += 1
            self.validate_frontmatter(file_path, frontmatter)

            # Подсчет тегов
            tags = frontmatter.get('tags', [])
            if len(tags) >= 3:
                self.stats['good_tags'] += 1

        # Валидация ссылок
        self.validate_links(file_path, content)

        # Валидация именования
        self.validate_file_naming(file_path)

    def scan_and_validate(self):
        """Сканировать и валидировать все статьи"""
        for md_file in self.knowledge_dir.rglob("*.md"):
            # Пропустить индексы
            if md_file.name == "INDEX.md":
                continue

            self.validate_article(md_file)

    def print_report(self):
        """Вывести отчет о валидации"""
        print("\n" + "="*60)
        print("📋 ОТЧЕТ О ВАЛИДАЦИИ БАЗЫ ЗНАНИЙ")
        print("="*60 + "\n")

        # Статистика
        print("📊 Статистика:")
        print(f"   Всего статей: {self.stats['total_articles']}")
        print(f"   С frontmatter: {self.stats['with_frontmatter']}")
        print(f"   С хорошими тегами (3+): {self.stats['good_tags']}")

        # Покрытие метаданными
        if self.stats['total_articles'] > 0:
            coverage = (self.stats['with_frontmatter'] / self.stats['total_articles']) * 100
            print(f"   Покрытие метаданными: {coverage:.1f}%")

        print()

        # Ошибки
        if self.errors:
            print(f"❌ Ошибки ({len(self.errors)}):")
            for error in self.errors[:20]:  # Показать первые 20
                print(f"   {error}")
            if len(self.errors) > 20:
                print(f"   ... и еще {len(self.errors) - 20} ошибок")
            print()
        else:
            print("✅ Ошибок не найдено!\n")

        # Предупреждения
        if self.warnings:
            print(f"⚠️  Предупреждения ({len(self.warnings)}):")
            for warning in self.warnings[:20]:  # Показать первые 20
                print(f"   {warning}")
            if len(self.warnings) > 20:
                print(f"   ... и еще {len(self.warnings) - 20} предупреждений")
            print()
        else:
            print("✅ Предупреждений нет!\n")

        # Итоговый статус
        print("="*60)
        if not self.errors:
            print("✅ ВАЛИДАЦИЯ УСПЕШНА!")
        else:
            print("❌ ВАЛИДАЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ")
        print("="*60 + "\n")

    def run(self):
        """Запустить валидацию"""
        print("🔍 Начинаю валидацию базы знаний...\n")

        # Проверка структуры
        self.validate_structure()

        # Валидация статей
        self.scan_and_validate()

        # Вывод отчета
        self.print_report()

        # Возвращаем код выхода
        return 0 if not self.errors else 1


def main():
    """Точка входа"""
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    validator = KnowledgeBaseValidator(root_dir)
    exit_code = validator.run()
    exit(exit_code)


if __name__ == "__main__":
    main()
