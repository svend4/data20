#!/usr/bin/env python3
"""
Breadcrumbs Navigation - Навигационные крошки
Добавляет навигационный путь в начало статей
"""

from pathlib import Path
import yaml
import re


class BreadcrumbsGenerator:
    """Генератор навигационных крошек"""

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

    def generate_breadcrumbs(self, file_path):
        """Создать навигационные крошки для файла"""
        # Получить относительный путь от knowledge/
        relative_path = file_path.relative_to(self.knowledge_dir)
        parts = list(relative_path.parts)

        breadcrumbs = []
        breadcrumbs.append(f"[🏠 Главная](/{self.root_dir.name}/INDEX.md)")

        # Построить путь
        current_path = self.knowledge_dir

        for i, part in enumerate(parts[:-1]):  # Исключить последний (сам файл)
            current_path = current_path / part

            # Название части (capitalize)
            label = part.replace('-', ' ').replace('_', ' ').title()

            # Ссылка
            if i == 0:
                # Категория - ссылка на index
                link_path = current_path / "index" / "INDEX.md"
            else:
                link_path = current_path / "INDEX.md"

            if link_path.exists():
                rel_link = link_path.relative_to(file_path.parent)
                breadcrumbs.append(f"[{label}]({rel_link})")
            else:
                breadcrumbs.append(label)

        # Текущая страница (без ссылки)
        frontmatter, _ = self.extract_frontmatter_and_content(file_path)
        current_title = frontmatter.get('title', file_path.stem) if frontmatter else file_path.stem
        breadcrumbs.append(current_title)

        # Форматировать
        return " → ".join(breadcrumbs)

    def add_breadcrumbs(self, file_path):
        """Добавить навигационные крошки в файл"""
        frontmatter_str, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return False

        # Создать крошки
        breadcrumbs = self.generate_breadcrumbs(file_path)

        # Проверить, есть ли уже крошки
        if '🏠 Главная' in content or '→' in content[:200]:
            # Удалить старые крошки (первая строка после frontmatter)
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

    def process_all(self):
        """Добавить крошки ко всем статьям"""
        print("🍞 Генерация навигационных крошек...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                if self.add_breadcrumbs(md_file):
                    count += 1
                    print(f"✅ {md_file.relative_to(self.root_dir)}")
            except Exception as e:
                print(f"⚠️  Ошибка: {e}")

        print(f"\n✅ Обработано статей: {count}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = BreadcrumbsGenerator(root_dir)
    generator.process_all()


if __name__ == "__main__":
    main()
