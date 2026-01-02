#!/usr/bin/env python3
"""
Построение графа знаний и его визуализация
"""

import os
import re
from pathlib import Path
import yaml
import json


class KnowledgeGraphBuilder:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.graph = {
            'nodes': [],
            'edges': []
        }

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return None, content

            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except:
            return None, ""

    def find_links(self, content):
        """Найти все markdown ссылки"""
        # Формат: [text](file.md)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        return [link[1] for link in links]

    def build_graph(self):
        """Построить граф"""
        print("🔗 Построение графа знаний...\n")

        node_id = 0
        file_to_id = {}

        # Первый проход: создать узлы
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            fm, content = self.extract_frontmatter(md_file)

            relative_path = str(md_file.relative_to(self.root_dir))

            node = {
                'id': node_id,
                'file': relative_path,
                'label': fm.get('title', md_file.stem) if fm else md_file.stem,
                'category': fm.get('category', 'unknown') if fm else 'unknown',
                'subcategory': fm.get('subcategory', '') if fm else '',
                'tags': fm.get('tags', []) if fm else [],
                'word_count': len(content.split())
            }

            self.graph['nodes'].append(node)
            file_to_id[relative_path] = node_id
            node_id += 1

        print(f"   Создано узлов: {len(self.graph['nodes'])}")

        # Второй проход: создать рёбра
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            relative_path = str(md_file.relative_to(self.root_dir))
            source_id = file_to_id.get(relative_path)

            if source_id is None:
                continue

            fm, content = self.extract_frontmatter(md_file)

            # Найти ссылки
            links = self.find_links(content)

            for link in links:
                # Разрешить относительный путь
                if link.startswith('/'):
                    target_path = link.lstrip('/')
                else:
                    target_path = str((md_file.parent / link).relative_to(self.root_dir))

                target_id = file_to_id.get(target_path)

                if target_id is not None:
                    edge = {
                        'source': source_id,
                        'target': target_id,
                        'type': 'reference'
                    }
                    self.graph['edges'].append(edge)

            # Добавить рёбра по тегам (слабые связи)
            if fm and 'tags' in fm:
                source_tags = set(fm['tags'])

                for other_node in self.graph['nodes']:
                    if other_node['id'] == source_id:
                        continue

                    other_tags = set(other_node['tags'])
                    common_tags = source_tags & other_tags

                    if len(common_tags) >= 2:  # Минимум 2 общих тега
                        edge = {
                            'source': source_id,
                            'target': other_node['id'],
                            'type': 'related',
                            'weight': len(common_tags)
                        }
                        self.graph['edges'].append(edge)

        print(f"   Создано рёбер: {len(self.graph['edges'])}")

    def analyze_graph(self):
        """Анализ графа"""
        print("\n📊 Анализ графа:")

        # Степень узлов
        in_degree = {node['id']: 0 for node in self.graph['nodes']}
        out_degree = {node['id']: 0 for node in self.graph['nodes']}

        for edge in self.graph['edges']:
            out_degree[edge['source']] += 1
            in_degree[edge['target']] += 1

        # Изолированные узлы
        isolated = [node for node in self.graph['nodes']
                   if in_degree[node['id']] == 0 and out_degree[node['id']] == 0]

        print(f"   Изолированных узлов: {len(isolated)}")

        # Hub'ы (узлы с наибольшим количеством связей)
        total_degree = {node['id']: in_degree[node['id']] + out_degree[node['id']]
                       for node in self.graph['nodes']}

        top_hubs = sorted(total_degree.items(), key=lambda x: x[1], reverse=True)[:10]

        print(f"\n   Топ hub'ов (центральные статьи):")
        for node_id, degree in top_hubs:
            node = next(n for n in self.graph['nodes'] if n['id'] == node_id)
            print(f"      {node['label']}: {degree} связей")

    def export_json(self, output_file):
        """Экспорт графа в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Граф сохранён: {output_file}")

    def export_dot(self, output_file):
        """Экспорт в формат DOT (Graphviz)"""
        lines = ['digraph KnowledgeGraph {']
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box, style=rounded];')

        # Узлы
        for node in self.graph['nodes']:
            label = node['label'].replace('"', '\\"')
            color = self.get_category_color(node['category'])
            lines.append(f'  {node["id"]} [label="{label}", fillcolor="{color}", style=filled];')

        # Рёбра
        for edge in self.graph['edges']:
            style = 'solid' if edge['type'] == 'reference' else 'dashed'
            lines.append(f'  {edge["source"]} -> {edge["target"]} [style={style}];')

        lines.append('}')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✅ DOT файл сохранён: {output_file}")
        print(f"   Используйте: dot -Tpng {output_file} -o graph.png")

    def get_category_color(self, category):
        """Цвет по категории"""
        colors = {
            'computers': 'lightblue',
            'household': 'lightgreen',
            'cooking': 'lightyellow',
            'unknown': 'lightgray'
        }
        return colors.get(category, 'white')

    def export_mermaid(self, output_file):
        """Экспорт в Mermaid формат"""
        lines = ['graph LR']

        # Узлы с категориями
        for node in self.graph['nodes']:
            label = node['label'][:30]  # Ограничить длину
            lines.append(f'  {node["id"]}["{label}"]')

        # Рёбра
        for edge in self.graph['edges']:
            arrow = '-->' if edge['type'] == 'reference' else '-.->'
            lines.append(f'  {edge["source"]} {arrow} {edge["target"]}')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✅ Mermaid файл сохранён: {output_file}")

    def run(self):
        """Запустить построение графа"""
        # Построить граф
        self.build_graph()

        # Анализ
        self.analyze_graph()

        # Экспорт
        output_dir = self.root_dir
        self.export_json(output_dir / "knowledge_graph.json")
        self.export_dot(output_dir / "knowledge_graph.dot")
        self.export_mermaid(output_dir / "knowledge_graph.mmd")

        print("\n🎉 Граф знаний построен!")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = KnowledgeGraphBuilder(root_dir)
    builder.run()


if __name__ == "__main__":
    main()
