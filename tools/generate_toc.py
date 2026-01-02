#!/usr/bin/env python3
"""
Table of Contents Generator - Генератор оглавления
Автоматически создаёт оглавление для markdown файлов

Функции:
- Извлечение заголовков из markdown
- Создание якорных ссылок
- Многоуровневое оглавление
- Автоматическое добавление в начало файла
"""

from pathlib import Path
import re


class TOCGenerator:
    """Генератор оглавления"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

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

    def generate_toc(self, headings, min_level=2, max_level=4):
        """
        Создать оглавление из заголовков

        min_level: минимальный уровень заголовков (обычно 2, чтобы пропустить h1)
        max_level: максимальный уровень заголовков (для контроля глубины)
        """
        if not headings:
            return ""

        lines = []
        lines.append("## 📑 Содержание\n\n")

        for level, text, anchor in headings:
            # Пропустить слишком высокие или низкие уровни
            if level < min_level or level > max_level:
                continue

            # Пропустить само оглавление
            if 'содержание' in text.lower() or 'table of contents' in text.lower():
                continue

            # Отступ пропорционален уровню
            indent = "  " * (level - min_level)

            # Ссылка
            lines.append(f"{indent}- [{text}](#{anchor})\n")

        lines.append("\n")

        return ''.join(lines)

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

    def generate_master_toc(self):
        """Создать главное оглавление всей базы знаний"""
        print("\n📚 Создание главного оглавления...\n")

        lines = []
        lines.append("# 📚 Главное оглавление базы знаний\n\n")
        lines.append("> Полный список всех статей с их содержанием\n\n")

        # Группировать по категориям
        by_category = {}

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

                    by_category[category].append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'headings': headings
                    })

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


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Table of Contents Generator - Генератор оглавления'
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

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = TOCGenerator(root_dir)

    if args.file:
        file_path = root_dir / args.file
        if generator.add_toc_to_file(file_path):
            print(f"✅ Оглавление добавлено к {args.file}")
        else:
            print(f"⚠️  Не удалось добавить оглавление")

    elif args.all:
        generator.process_all_articles()

    elif args.master:
        generator.generate_master_toc()

    else:
        # По умолчанию - оба действия
        generator.process_all_articles()
        generator.generate_master_toc()


if __name__ == "__main__":
    main()
