#!/usr/bin/env python3
"""
Orphaned Articles Finder - Поиск статей-сирот
Находит статьи без входящих ссылок (на них никто не ссылается)
"""

from pathlib import Path
import re
import yaml


class OrphanFinder:
    """Поиск статей-сирот"""

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
                return yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None

    def find_orphans(self):
        """Найти статьи-сироты"""
        print("🔍 Поиск статей-сирот...\n")

        # Собрать все статьи
        all_articles = set()
        linked_articles = set()

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            all_articles.add(article_path)

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            # Найти все markdown ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in links:
                # Пропустить внешние ссылки
                if link.startswith('http'):
                    continue

                # Разрешить относительный путь
                target = (md_file.parent / link).resolve()

                try:
                    target_path = str(target.relative_to(self.root_dir))
                    linked_articles.add(target_path)
                except:
                    pass

            # Ссылки из frontmatter (related)
            if frontmatter and 'related' in frontmatter:
                related = frontmatter['related']
                if isinstance(related, list):
                    for link in related:
                        target = (md_file.parent / link).resolve()
                        try:
                            target_path = str(target.relative_to(self.root_dir))
                            linked_articles.add(target_path)
                        except:
                            pass

        # Найти сироты
        orphans = all_articles - linked_articles

        print(f"   Всего статей: {len(all_articles)}")
        print(f"   Со ссылками: {len(linked_articles)}")
        print(f"   Сироты: {len(orphans)}\n")

        return sorted(orphans)

    def generate_report(self, orphans):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔍 Отчёт: Статьи-сироты\n\n")
        lines.append("> Статьи, на которые нет ссылок из других статей\n\n")

        lines.append(f"**Найдено сирот**: {len(orphans)}\n\n")

        if orphans:
            lines.append("## Список статей-сирот\n\n")
            lines.append("⚠️  Рекомендуется добавить ссылки на эти статьи из связанных материалов.\n\n")

            for orphan in orphans:
                lines.append(f"- [`{orphan}`]({orphan})\n")
        else:
            lines.append("✅ Нет статей-сирот! Все статьи связаны.\n")

        output_file = self.root_dir / "ORPHANED_ARTICLES.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    finder = OrphanFinder(root_dir)
    orphans = finder.find_orphans()
    finder.generate_report(orphans)


if __name__ == "__main__":
    main()
