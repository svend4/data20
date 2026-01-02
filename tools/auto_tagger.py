#!/usr/bin/env python3
"""
Auto-Tagger - Автоматическая генерация тегов
Предлагает теги на основе контента статьи

Вдохновлено: WordPress auto-tagging, ML text classification
"""

from pathlib import Path
import yaml
import re
from collections import Counter
import json


class AutoTagger:
    """Автоматический генератор тегов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Стоп-слова (расширенный список)
        self.stop_words = set([
            'и', 'в', 'на', 'с', 'по', 'для', 'к', 'о', 'от', 'из', 'у', 'за',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        ])

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return match.group(1), yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None, None

    def extract_keywords(self, text, num_tags=5):
        """Извлечь ключевые слова"""
        # Удалить markdown
        text = re.sub(r'[#*`\[\]()]', ' ', text)

        # Извлечь слова
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())

        # Фильтровать стоп-слова
        words = [w for w in words if w not in self.stop_words]

        # Подсчёт частоты
        word_freq = Counter(words)

        # Топ слова
        top_words = [word for word, count in word_freq.most_common(num_tags * 2)]

        return top_words[:num_tags]

    def suggest_tags(self, file_path):
        """Предложить теги для статьи"""
        frontmatter_str, frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        article_path = str(file_path.relative_to(self.root_dir))
        title = frontmatter.get('title', file_path.stem) if frontmatter else file_path.stem
        existing_tags = frontmatter.get('tags', []) if frontmatter else []

        # Извлечь ключевые слова
        suggested = self.extract_keywords(content, num_tags=5)

        # Убрать уже существующие
        new_suggestions = [t for t in suggested if t not in [tag.lower() for tag in existing_tags]]

        return {
            'path': article_path,
            'title': title,
            'existing_tags': existing_tags,
            'suggested_tags': new_suggestions[:3]
        }

    def analyze_all(self):
        """Проанализировать все статьи"""
        print("🏷️  Генерация предложений тегов...\n")

        suggestions = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.suggest_tags(md_file)
            if result and result['suggested_tags']:
                suggestions.append(result)

        print(f"   Статей проанализировано: {len(suggestions)}\n")

        return suggestions

    def generate_report(self, suggestions):
        """Создать отчёт"""
        lines = []
        lines.append("# 🏷️ Предложения тегов\n\n")

        for item in suggestions:
            lines.append(f"## {item['title']}\n\n")
            lines.append(f"`{item['path']}`\n\n")
            lines.append(f"**Текущие теги**: {', '.join(item['existing_tags']) if item['existing_tags'] else 'нет'}\n\n")
            lines.append(f"**Предложенные**: {', '.join(item['suggested_tags'])}\n\n")

        output_file = self.root_dir / "AUTO_TAGGING_SUGGESTIONS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tagger = AutoTagger(root_dir)
    suggestions = tagger.analyze_all()
    tagger.generate_report(suggestions)


if __name__ == "__main__":
    main()
