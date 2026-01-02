#!/usr/bin/env python3
"""
Knowledge Graph Builder - Построитель графа знаний
Создаёт семантический граф знаний с сущностями и отношениями
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class KnowledgeGraphBuilder:
    """Построитель графа знаний"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.entities = defaultdict(lambda: {'type': '', 'mentions': []})
        self.relations = []

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

    def extract_entities(self, content, article_path):
        """Простое извлечение сущностей"""
        # Выделенные термины как сущности
        entities = re.findall(r'\*\*([А-ЯA-Z][^\*]{2,30}?)\*\*', content)

        for entity in entities:
            self.entities[entity]['type'] = 'Concept'
            self.entities[entity]['mentions'].append(article_path)

    def build_graph(self):
        print("🕸️  Построение графа знаний...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            self.extract_entities(content, article_path)

        print(f"   Сущностей: {len(self.entities)}\n")

    def save_json(self):
        data = {
            'entities': [
                {'name': name, 'type': data['type'], 'mentions': data['mentions']}
                for name, data in self.entities.items()
            ]
        }

        output_file = self.root_dir / "knowledge_graph_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Граф знаний: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = KnowledgeGraphBuilder(root_dir)
    builder.build_graph()
    builder.save_json()


if __name__ == "__main__":
    main()
