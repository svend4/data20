#!/usr/bin/env python3
"""
Backlinks Generator - Генератор обратных ссылок
Автоматически добавляет секцию "Кто ссылается на эту статью"

Вдохновлено: Wikipedia backlinks, Roam Research bidirectional links
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict


class BacklinksGenerator:
    """Генератор обратных ссылок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Граф ссылок
        self.backlinks = defaultdict(list)
        self.articles = {}

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

    def build_backlinks_graph(self):
        """Построить граф обратных ссылок"""
        print("🔗 Построение графа обратных ссылок...\n")

        # Собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter_str, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Парсинг frontmatter для заголовка
            if frontmatter_str:
                try:
                    frontmatter = yaml.safe_load(frontmatter_str)
                    title = frontmatter.get('title', md_file.stem)
                except:
                    title = md_file.stem
            else:
                title = md_file.stem

            self.articles[article_path] = {
                'title': title,
                'file': md_file
            }

        # Построить граф ссылок
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            source_path = str(md_file.relative_to(self.root_dir))
            source_title = self.articles[source_path]['title']

            # Извлечь все markdown ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for link_text, link_url in links:
                # Пропустить внешние ссылки
                if link_url.startswith('http'):
                    continue

                # Пропустить якорные ссылки
                if link_url.startswith('#'):
                    continue

                try:
                    # Разрешить относительный путь
                    target = (md_file.parent / link_url.split('#')[0]).resolve()

                    if target.exists() and target.is_relative_to(self.root_dir):
                        target_path = str(target.relative_to(self.root_dir))

                        # Добавить обратную ссылку
                        if target_path in self.articles:
                            self.backlinks[target_path].append({
                                'source': source_path,
                                'title': source_title,
                                'context': link_text
                            })
                except:
                    pass

        print(f"   Статей обработано: {len(self.articles)}")
        print(f"   Обратных ссылок: {sum(len(links) for links in self.backlinks.values())}\n")

    def generate_backlinks_section(self, article_path):
        """Создать секцию обратных ссылок"""
        if article_path not in self.backlinks:
            return ""

        backlinks = self.backlinks[article_path]

        if not backlinks:
            return ""

        lines = []
        lines.append("\n---\n\n")
        lines.append("## 🔗 Обратные ссылки\n\n")
        lines.append(f"> Эту статью цитируют {len(backlinks)} статей:\n\n")

        for backlink in backlinks:
            # Вычислить относительный путь
            article_file = self.articles[article_path]['file']
            source_file = self.articles[backlink['source']]['file']

            try:
                rel_path = source_file.relative_to(article_file.parent)
            except:
                rel_path = backlink['source']

            lines.append(f"- [{backlink['title']}]({rel_path})")

            if backlink['context']:
                lines.append(f" — *\"{backlink['context']}\"*")

            lines.append("\n")

        return ''.join(lines)

    def update_article(self, article_path):
        """Обновить статью с обратными ссылками"""
        article_file = self.articles[article_path]['file']

        frontmatter_str, content = self.extract_frontmatter_and_content(article_file)

        if not content:
            return False

        # Удалить существующую секцию обратных ссылок
        # Ищем "## 🔗 Обратные ссылки" до конца файла
        content = re.sub(
            r'\n---\s*\n+##\s*🔗\s*Обратные ссылки.*',
            '',
            content,
            flags=re.DOTALL
        )

        # Также удалить старые варианты
        content = re.sub(
            r'\n---\s*\n+##\s*Обратные ссылки.*',
            '',
            content,
            flags=re.DOTALL
        )

        # Добавить новую секцию
        backlinks_section = self.generate_backlinks_section(article_path)

        if backlinks_section:
            content += backlinks_section

        # Собрать файл
        full_content = f"---\n{frontmatter_str}\n---\n\n{content}"

        # Записать
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return bool(backlinks_section)

    def update_all(self, dry_run=False):
        """Обновить все статьи"""
        print("✍️  Обновление статей...\n")

        updated = 0
        skipped = 0

        for article_path in self.articles:
            if article_path in self.backlinks and self.backlinks[article_path]:
                if not dry_run:
                    if self.update_article(article_path):
                        updated += 1
                        print(f"   ✅ {article_path} ({len(self.backlinks[article_path])} обратных ссылок)")
                else:
                    print(f"   [DRY RUN] {article_path} — будет добавлено {len(self.backlinks[article_path])} обратных ссылок")
                    updated += 1
            else:
                skipped += 1

        print(f"\n✅ Обновлено статей: {updated}")
        print(f"⏭️  Пропущено (нет обратных ссылок): {skipped}")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Отчёт: Обратные ссылки\n\n")
        lines.append("> Карта цитирований между статьями\n\n")

        # Статистика
        total_backlinks = sum(len(links) for links in self.backlinks.values())
        articles_with_backlinks = len([a for a in self.backlinks.values() if a])

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Статей с обратными ссылками**: {articles_with_backlinks}\n")
        lines.append(f"- **Всего обратных ссылок**: {total_backlinks}\n\n")

        # Топ цитируемых
        lines.append("## Топ-10 самых цитируемых\n\n")

        sorted_articles = sorted(
            self.backlinks.items(),
            key=lambda x: -len(x[1])
        )

        for i, (article_path, backlinks) in enumerate(sorted_articles[:10], 1):
            if not backlinks:
                break

            title = self.articles[article_path]['title']

            lines.append(f"### {i}. {title}\n\n")
            lines.append(f"- **Файл**: [{article_path}]({article_path})\n")
            lines.append(f"- **Обратных ссылок**: {len(backlinks)}\n\n")

            lines.append("**Цитируют:**\n")
            for backlink in backlinks[:5]:
                lines.append(f"- [{backlink['title']}]({backlink['source']})")
                if backlink['context']:
                    lines.append(f" — *\"{backlink['context']}\"*")
                lines.append("\n")

            if len(backlinks) > 5:
                lines.append(f"\n...и ещё {len(backlinks) - 5}\n")

            lines.append("\n")

        output_file = self.root_dir / "BACKLINKS_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"\n✅ Отчёт: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Backlinks Generator')
    parser.add_argument('--dry-run', action='store_true', help='Не изменять файлы, только показать что будет сделано')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = BacklinksGenerator(root_dir)
    generator.build_backlinks_graph()
    generator.update_all(dry_run=args.dry_run)
    generator.generate_report()


if __name__ == "__main__":
    main()
