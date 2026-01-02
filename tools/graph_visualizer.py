#!/usr/bin/env python3
"""
Graph Visualizer - Визуализация графов
Создаёт интерактивные визуализации графов связей между статьями

Вдохновлено: D3.js force graphs, Obsidian graph view
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class GraphVisualizer:
    """Визуализатор графов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Граф
        self.nodes = []
        self.links = []
        self.articles = {}

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

    def build_graph(self):
        """Построить граф"""
        print("🕸️  Построение графа связей...\n")

        # Собрать все статьи (nodes)
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            tags = frontmatter.get('tags', []) if frontmatter else []
            category = frontmatter.get('category', 'Другое') if frontmatter else 'Другое'

            self.articles[article_path] = {
                'title': title,
                'tags': tags,
                'category': category,
                'file': md_file
            }

            # Добавить ноду
            self.nodes.append({
                'id': article_path,
                'label': title,
                'category': category,
                'size': len(content) / 100  # Размер пропорционален длине
            })

        # Построить связи (edges)
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            source = str(md_file.relative_to(self.root_dir))

            # Извлечь ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for text, link in links:
                if link.startswith('http'):
                    continue

                try:
                    target_file = (md_file.parent / link.split('#')[0]).resolve()

                    if target_file.exists() and target_file.is_relative_to(self.root_dir):
                        target = str(target_file.relative_to(self.root_dir))

                        if target in self.articles:
                            self.links.append({
                                'source': source,
                                'target': target,
                                'label': text
                            })
                except:
                    pass

        print(f"   Nodes: {len(self.nodes)}")
        print(f"   Edges: {len(self.links)}\n")

    def generate_d3_visualization(self):
        """Создать D3.js визуализацию"""
        # Цвета для категорий
        category_colors = {
            'Технологии': '#3498db',
            'Наука': '#2ecc71',
            'Другое': '#95a5a6'
        }

        html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a1a;
            color: #fff;
        }}
        #graph {{
            width: 100vw;
            height: 100vh;
        }}
        .node {{
            cursor: pointer;
        }}
        .node circle {{
            stroke: #fff;
            stroke-width: 1.5px;
        }}
        .node text {{
            font-size: 10px;
            pointer-events: none;
            fill: #fff;
        }}
        .link {{
            stroke: #999;
            stroke-opacity: 0.3;
            stroke-width: 1px;
        }}
        .link:hover {{
            stroke-opacity: 0.8;
        }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 8px;
            max-width: 300px;
        }}
        h3 {{
            margin: 0 0 10px 0;
        }}
        .stats {{
            font-size: 12px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div id="info">
        <h3>🕸️ Knowledge Graph</h3>
        <div class="stats">
            Nodes: {len(self.nodes)}<br>
            Links: {len(self.links)}
        </div>
    </div>
    <svg id="graph"></svg>
    <script>
        const width = window.innerWidth;
        const height = window.innerHeight;

        const nodes = {json.dumps(self.nodes, ensure_ascii=False)};
        const links = {json.dumps(self.links, ensure_ascii=False)};

        const svg = d3.select("#graph")
            .attr("width", width)
            .attr("height", height);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(20));

        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link");

        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("class", "node")
            .call(drag(simulation));

        node.append("circle")
            .attr("r", d => Math.max(5, Math.min(20, d.size)))
            .attr("fill", d => {{
                const colors = {json.dumps(category_colors)};
                return colors[d.category] || "#95a5a6";
            }});

        node.append("text")
            .attr("dx", 12)
            .attr("dy", 4)
            .text(d => d.label.substring(0, 20));

        node.append("title")
            .text(d => d.label);

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function drag(simulation) {{
            function dragstarted(event) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }}

            function dragged(event) {{
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }}

            function dragended(event) {{
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }}

            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }}
    </script>
</body>
</html>'''

        output_file = self.root_dir / "knowledge_graph.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Интерактивный граф: {output_file}")

    def save_json(self):
        """Сохранить граф в JSON"""
        data = {
            'nodes': self.nodes,
            'links': self.links
        }

        output_file = self.root_dir / "knowledge_graph.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON граф: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    visualizer = GraphVisualizer(root_dir)
    visualizer.build_graph()
    visualizer.generate_d3_visualization()
    visualizer.save_json()


if __name__ == "__main__":
    main()
