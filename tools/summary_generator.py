#!/usr/bin/env python3
"""
Summary Generator - Генератор резюме
Автоматическое создание кратких резюме статей
"""

from pathlib import Path
import yaml
import re


class SummaryGenerator:
    """Генератор резюме"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def extract_frontmatter_and_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None

    def generate_summary(self, content, max_sentences=3):
        """Простое извлекающее резюме"""
        # Разбить на предложения
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Взять первые N предложений (простая стратегия)
        return '. '.join(sentences[:max_sentences]) + '.'

    def process_all(self):
        print("📝 Генерация резюме...\n")

        lines = []
        lines.append("# 📝 Резюме статей\n\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            summary = self.generate_summary(content)

            lines.append(f"## {title}\n\n")
            lines.append(f"> {summary}\n\n")

        output_file = self.root_dir / "SUMMARIES.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Резюме: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = SummaryGenerator(root_dir)
    generator.process_all()


if __name__ == "__main__":
    main()
