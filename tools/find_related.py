#!/usr/bin/env python3
"""
Скрипт для поиска связанных статей на основе тегов, содержимого и метаданных
"""

import os
import re
from pathlib import Path
import yaml
import sys


class RelatedFinder:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return None, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except:
            return None, content

    def find_related(self, target_file, num_results=5):
        """Найти связанные статьи для данного файла"""
        target_path = self.root_dir / target_file

        if not target_path.exists():
            print(f"❌ Файл не найден: {target_file}")
            return

        # Извлечь данные целевой статьи
        target_fm, target_content = self.extract_frontmatter(target_path)

        if not target_fm:
            print("⚠️  У целевой статьи нет метаданных")
            return

        target_tags = set(target_fm.get('tags', []))
        target_category = target_fm.get('category')
        target_subcategory = target_fm.get('subcategory')

        print(f"\n📄 Целевая статья: {target_fm.get('title', target_file)}")
        print(f"🏷️  Теги: {', '.join(target_tags)}")
        print(f"📂 Категория: {target_category} / {target_subcategory}")

        # Сканировать все статьи и вычислить релевантность
        candidates = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            # Пропустить саму целевую статью
            if md_file.resolve() == target_path.resolve():
                continue

            fm, content = self.extract_frontmatter(md_file)

            if not fm:
                continue

            # Вычислить релевантность
            score = 0
            reasons = []

            # По тегам (самый важный фактор)
            article_tags = set(fm.get('tags', []))
            common_tags = target_tags & article_tags

            if common_tags:
                score += len(common_tags) * 10
                reasons.append(f"{len(common_tags)} общих тегов: {', '.join(list(common_tags)[:3])}")

            # По категории
            if fm.get('category') == target_category:
                score += 5
                reasons.append("та же категория")

            # По подкатегории
            if fm.get('subcategory') == target_subcategory:
                score += 3
                reasons.append("та же подкатегория")

            # По упоминанию в тексте (если есть ссылка)
            if str(target_path.name) in content or target_fm.get('title', '') in content:
                score += 15
                reasons.append("есть упоминание")

            if score > 0:
                candidates.append({
                    'file': str(md_file.relative_to(self.root_dir)),
                    'title': fm.get('title', md_file.name),
                    'score': score,
                    'reasons': reasons,
                    'tags': list(article_tags)
                })

        # Сортировать по релевантности
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Вывести результаты
        print(f"\n🔗 Найдено {len(candidates)} связанных статей\n")
        print("Топ связанных статей:")
        print("=" * 80)

        for i, article in enumerate(candidates[:num_results], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Файл: {article['file']}")
            print(f"   Релевантность: {article['score']}")
            print(f"   Причины: {', '.join(article['reasons'])}")
            print(f"   Теги: {', '.join(article['tags'][:5])}")

        # Предложить добавить ссылки
        print("\n" + "=" * 80)
        print("\n💡 Предложение: добавить в секцию 'См. также':\n")

        for article in candidates[:num_results]:
            filename = Path(article['file']).name
            print(f"- [[{filename}]] - {article['title']}")


def main():
    if len(sys.argv) < 2:
        print("Использование: python find_related.py <путь_к_статье>")
        print("Пример: python find_related.py knowledge/computers/articles/ai/llm-overview-2026.md")
        return

    target_file = sys.argv[1]

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    finder = RelatedFinder(root_dir)
    finder.find_related(target_file)


if __name__ == "__main__":
    main()
