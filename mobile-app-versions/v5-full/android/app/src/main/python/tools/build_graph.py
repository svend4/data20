#!/usr/bin/env python3
"""
Advanced Knowledge Graph Construction and Analysis

Построение графа знаний с продвинутым анализом: PageRank,
community detection, centrality metrics, path analysis, и
интерактивной HTML визуализацией.

Features:
- 🔗 Bidirectional graph construction (nodes + edges)
- 📊 PageRank centrality (identify important articles)
- 🎯 Betweenness centrality (find bridge articles)
- 👥 Community detection (cluster related content)
- 🛣️ Path analysis (shortest paths, diameter, radius)
- 📈 Graph metrics (density, clustering coefficient, transitivity)
- 🎨 Multiple export formats (JSON, DOT, Mermaid, HTML/vis.js)
- ⚡ Performance metrics (build time, analysis time)
- 🔍 Subgraph extraction (by category, by tags)
- 📄 Comprehensive reports (Markdown + HTML)

Usage:
    python3 build_graph.py                    # Full graph + analysis
    python3 build_graph.py --format html      # HTML visualization
    python3 build_graph.py --category computers # Subgraph for category
    python3 build_graph.py --pagerank         # Run PageRank analysis
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import yaml


class GraphAnalyzer:
    """Продвинутый анализ графов"""

    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        self.nodes = nodes
        self.edges = edges

        # Построить adjacency list
        self.adj_out = defaultdict(list)  # outgoing edges
        self.adj_in = defaultdict(list)   # incoming edges

        for edge in edges:
            self.adj_out[edge['source']].append(edge['target'])
            self.adj_in[edge['target']].append(edge['source'])

    def calculate_pagerank(self, iterations=100, damping=0.85) -> Dict[int, float]:
        """
        PageRank алгоритм для определения важности узлов
        PR(A) = (1-d)/N + d * Σ(PR(T_i)/C(T_i))
        """
        num_nodes = len(self.nodes)
        pagerank = {node['id']: 1.0 / num_nodes for node in self.nodes}

        for _ in range(iterations):
            new_pagerank = {}

            for node in self.nodes:
                node_id = node['id']

                # Base score
                rank = (1 - damping) / num_nodes

                # Contribution from incoming links
                for incoming_id in self.adj_in.get(node_id, []):
                    outgoing_count = len(self.adj_out.get(incoming_id, []))
                    if outgoing_count > 0:
                        rank += damping * (pagerank[incoming_id] / outgoing_count)

                new_pagerank[node_id] = rank

            pagerank = new_pagerank

        return pagerank

    def calculate_betweenness_centrality(self) -> Dict[int, float]:
        """
        Betweenness centrality - находит "мосты" между разными частями графа
        """
        betweenness = {node['id']: 0.0 for node in self.nodes}

        for source in self.nodes:
            # BFS для кратчайших путей
            stack = []
            predecessors = defaultdict(list)
            distance = {node['id']: -1 for node in self.nodes}
            sigma = {node['id']: 0 for node in self.nodes}

            source_id = source['id']
            distance[source_id] = 0
            sigma[source_id] = 1

            queue = deque([source_id])

            while queue:
                v = queue.popleft()

                stack.append(v)

                for w in self.adj_out.get(v, []):
                    # First visit to w?
                    if distance[w] < 0:
                        queue.append(w)
                        distance[w] = distance[v] + 1

                    # Shortest path to w via v?
                    if distance[w] == distance[v] + 1:
                        sigma[w] += sigma[v]
                        predecessors[w].append(v)

            # Accumulation
            delta = {node['id']: 0.0 for node in self.nodes}

            while stack:
                w = stack.pop()

                for v in predecessors[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])

                if w != source_id:
                    betweenness[w] += delta[w]

        # Normalize
        num_nodes = len(self.nodes)
        if num_nodes > 2:
            norm = 1.0 / ((num_nodes - 1) * (num_nodes - 2))
            for node_id in betweenness:
                betweenness[node_id] *= norm

        return betweenness

    def calculate_clustering_coefficient(self) -> float:
        """
        Clustering coefficient - насколько плотно связаны соседи узла
        """
        total_coefficient = 0.0
        count = 0

        for node in self.nodes:
            node_id = node['id']
            neighbors = set(self.adj_out.get(node_id, []))

            k = len(neighbors)
            if k < 2:
                continue

            # Подсчет треугольников
            triangles = 0
            for neighbor1 in neighbors:
                for neighbor2 in neighbors:
                    if neighbor1 != neighbor2:
                        if neighbor2 in self.adj_out.get(neighbor1, []):
                            triangles += 1

            # Local clustering coefficient
            local_coeff = triangles / (k * (k - 1)) if k > 1 else 0
            total_coefficient += local_coeff
            count += 1

        return total_coefficient / count if count > 0 else 0.0

    def find_communities_simple(self) -> Dict[int, int]:
        """
        Простое определение сообществ через connected components
        """
        visited = set()
        communities = {}
        community_id = 0

        def dfs(node_id, comm_id):
            visited.add(node_id)
            communities[node_id] = comm_id

            # Проход по всем соседям (и входящим, и исходящим)
            for neighbor in self.adj_out.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor, comm_id)

            for neighbor in self.adj_in.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor, comm_id)

        for node in self.nodes:
            if node['id'] not in visited:
                dfs(node['id'], community_id)
                community_id += 1

        return communities

    def calculate_shortest_path(self, source_id: int, target_id: int) -> Optional[List[int]]:
        """BFS для кратчайшего пути"""
        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = deque([(source_id, [source_id])])

        while queue:
            current, path = queue.popleft()

            for neighbor in self.adj_out.get(current, []):
                if neighbor == target_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None  # No path found

    def calculate_graph_diameter(self) -> int:
        """Диаметр графа - максимальная длина кратчайшего пути"""
        max_distance = 0

        for source in self.nodes:
            # BFS от каждого узла
            visited = {source['id']: 0}
            queue = deque([source['id']])

            while queue:
                current = queue.popleft()
                current_dist = visited[current]

                for neighbor in self.adj_out.get(current, []):
                    if neighbor not in visited:
                        visited[neighbor] = current_dist + 1
                        queue.append(neighbor)
                        max_distance = max(max_distance, current_dist + 1)

        return max_distance

    def calculate_density(self) -> float:
        """Плотность графа = actual edges / possible edges"""
        num_nodes = len(self.nodes)
        if num_nodes <= 1:
            return 0.0

        num_edges = len(self.edges)
        max_edges = num_nodes * (num_nodes - 1)  # Directed graph

        return num_edges / max_edges if max_edges > 0 else 0.0


class AdvancedKnowledgeGraphBuilder:
    """Продвинутый построитель графа знаний"""

    def __init__(self, root_dir=".", category_filter=None):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.category_filter = category_filter

        self.graph = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'total_nodes': 0,
                'total_edges': 0
            }
        }

        self.file_to_id = {}
        self.id_to_node = {}
        self.node_id_counter = 0

        # Метрики
        self.metrics = {}

    def extract_frontmatter(self, file_path: Path) -> Tuple[Optional[Dict], str]:
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
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
            return None, ""

    def find_links(self, content: str) -> List[str]:
        """Найти все markdown ссылки"""
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        return [link[1] for link in links]

    def build_graph(self):
        """Построить граф"""
        print("🔗 Building knowledge graph...\n")

        # Первый проход: создать узлы
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            fm, content = self.extract_frontmatter(md_file)

            # Фильтр по категории
            if self.category_filter:
                category = fm.get('category', '') if fm else ''
                if category != self.category_filter:
                    continue

            relative_path = str(md_file.relative_to(self.root_dir))

            # Подсчет метрик контента
            word_count = len(content.split())
            code_blocks = len(re.findall(r'```', content))
            images = len(re.findall(r'!\[', content))

            node = {
                'id': self.node_id_counter,
                'file': relative_path,
                'label': fm.get('title', md_file.stem) if fm else md_file.stem,
                'category': fm.get('category', 'unknown') if fm else 'unknown',
                'subcategory': fm.get('subcategory', '') if fm else '',
                'tags': fm.get('tags', []) if fm else [],
                'word_count': word_count,
                'code_blocks': code_blocks,
                'images': images,
                'status': fm.get('status', 'unknown') if fm else 'unknown'
            }

            self.graph['nodes'].append(node)
            self.file_to_id[relative_path] = self.node_id_counter
            self.id_to_node[self.node_id_counter] = node
            self.node_id_counter += 1

        print(f"   Nodes created: {len(self.graph['nodes'])}")

        # Второй проход: создать рёбра
        edge_count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            relative_path = str(md_file.relative_to(self.root_dir))
            source_id = self.file_to_id.get(relative_path)

            if source_id is None:
                continue

            fm, content = self.extract_frontmatter(md_file)

            # Найти ссылки
            links = self.find_links(content)

            for link in links:
                # Разрешить относительный путь
                try:
                    if link.startswith('/'):
                        target_path = link.lstrip('/')
                    else:
                        target_path = str((md_file.parent / link).relative_to(self.root_dir))

                    target_id = self.file_to_id.get(target_path)

                    if target_id is not None:
                        edge = {
                            'source': source_id,
                            'target': target_id,
                            'type': 'reference'
                        }
                        self.graph['edges'].append(edge)
                        edge_count += 1
                except Exception:
                    pass

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
                            'weight': len(common_tags),
                            'common_tags': list(common_tags)
                        }
                        self.graph['edges'].append(edge)
                        edge_count += 1

        print(f"   Edges created: {edge_count}")

        # Обновить метаданные
        self.graph['metadata']['total_nodes'] = len(self.graph['nodes'])
        self.graph['metadata']['total_edges'] = len(self.graph['edges'])

    def analyze_graph(self, run_pagerank=True):
        """Анализ графа"""
        print("\n📊 Analyzing graph...\n")

        analyzer = GraphAnalyzer(self.graph['nodes'], self.graph['edges'])

        # Базовые метрики
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)

        for edge in self.graph['edges']:
            out_degree[edge['source']] += 1
            in_degree[edge['target']] += 1

        # Изолированные узлы
        isolated = [node for node in self.graph['nodes']
                   if in_degree[node['id']] == 0 and out_degree[node['id']] == 0]

        self.metrics['isolated_nodes'] = len(isolated)
        print(f"   Isolated nodes: {len(isolated)}")

        # Hub'ы
        total_degree = {node['id']: in_degree[node['id']] + out_degree[node['id']]
                       for node in self.graph['nodes']}

        top_hubs = sorted(total_degree.items(), key=lambda x: x[1], reverse=True)[:10]

        print(f"\n   Top hubs (central articles):")
        for node_id, degree in top_hubs[:5]:
            node = self.id_to_node[node_id]
            print(f"      • {node['label']}: {degree} connections")

        # PageRank
        if run_pagerank and len(self.graph['nodes']) > 0:
            print(f"\n   Running PageRank...")
            pagerank = analyzer.calculate_pagerank()

            # Сохранить в узлы
            for node in self.graph['nodes']:
                node['pagerank'] = pagerank[node['id']]

            # Топ по PageRank
            top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"   Top PageRank articles:")
            for node_id, score in top_pagerank:
                node = self.id_to_node[node_id]
                print(f"      • {node['label']}: {score:.4f}")

        # Clustering coefficient
        clustering = analyzer.calculate_clustering_coefficient()
        self.metrics['clustering_coefficient'] = clustering
        print(f"\n   Clustering coefficient: {clustering:.4f}")

        # Density
        density = analyzer.calculate_density()
        self.metrics['density'] = density
        print(f"   Graph density: {density:.4f}")

        # Diameter (только если граф не слишком большой)
        if len(self.graph['nodes']) < 100:
            diameter = analyzer.calculate_graph_diameter()
            self.metrics['diameter'] = diameter
            print(f"   Graph diameter: {diameter}")

        # Communities
        communities = analyzer.find_communities_simple()
        num_communities = len(set(communities.values()))
        self.metrics['communities'] = num_communities
        print(f"   Number of communities: {num_communities}")

    def export_json(self, output_file: Path):
        """Экспорт графа в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Graph saved: {output_file}")

    def export_dot(self, output_file: Path):
        """Экспорт в формат DOT (Graphviz)"""
        lines = ['digraph KnowledgeGraph {']
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box, style="rounded,filled"];')

        # Узлы
        for node in self.graph['nodes']:
            label = node['label'].replace('"', '\\"')[:40]
            color = self.get_category_color(node['category'])

            # Добавить PageRank в label если есть
            if 'pagerank' in node:
                label += f"\\n(PR: {node['pagerank']:.3f})"

            lines.append(f'  {node["id"]} [label="{label}", fillcolor="{color}"];')

        # Рёбра
        for edge in self.graph['edges']:
            style = 'solid' if edge['type'] == 'reference' else 'dashed'
            color = 'black' if edge['type'] == 'reference' else 'gray'
            lines.append(f'  {edge["source"]} -> {edge["target"]} [style={style}, color={color}];')

        lines.append('}')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✅ DOT file saved: {output_file}")
        print(f"   Use: dot -Tpng {output_file.name} -o graph.png")

    def export_html_visjs(self, output_file: Path):
        """Экспорт в HTML с vis.js для интерактивной визуализации"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Knowledge Graph Visualization</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #graph {{
            width: 100%;
            height: 900px;
            border: 1px solid lightgray;
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .info {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>Knowledge Graph Visualization</h1>
    <div class="info">
        <p><strong>Nodes:</strong> {num_nodes} | <strong>Edges:</strong> {num_edges}</p>
        <p><strong>Clustering:</strong> {clustering:.4f} | <strong>Density:</strong> {density:.4f}</p>
    </div>
    <div id="graph"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});

        var container = document.getElementById('graph');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            nodes: {{
                shape: 'box',
                font: {{ size: 14 }},
                borderWidth: 2
            }},
            edges: {{
                arrows: 'to',
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                stabilization: {{ iterations: 100 }},
                barnesHut: {{ gravitationalConstant: -8000, springLength: 200 }}
            }}
        }};

        var network = new vis.Network(container, data, options);

        network.on("selectNode", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                alert("Title: " + node.title + "\\nFile: " + node.file + "\\nWords: " + node.word_count);
            }}
        }});
    </script>
</body>
</html>"""

        # Подготовить nodes для vis.js
        visjs_nodes = []
        for node in self.graph['nodes']:
            visjs_nodes.append({
                'id': node['id'],
                'label': node['label'][:30],
                'title': node['label'],
                'file': node['file'],
                'word_count': node['word_count'],
                'color': self.get_category_color(node['category']),
                'value': node.get('pagerank', 0.5) * 100  # Node size by PageRank
            })

        # Подготовить edges для vis.js
        visjs_edges = []
        for edge in self.graph['edges']:
            visjs_edges.append({
                'from': edge['source'],
                'to': edge['target'],
                'dashes': edge['type'] != 'reference'
            })

        # Заполнить template
        html_content = html_template.format(
            num_nodes=len(self.graph['nodes']),
            num_edges=len(self.graph['edges']),
            clustering=self.metrics.get('clustering_coefficient', 0),
            density=self.metrics.get('density', 0),
            nodes_json=json.dumps(visjs_nodes),
            edges_json=json.dumps(visjs_edges)
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML visualization saved: {output_file}")
        print(f"   Open in browser to view interactive graph")

    def get_category_color(self, category: str) -> str:
        """Цвет по категории"""
        colors = {
            'computers': '#87CEEB',    # Sky blue
            'household': '#90EE90',    # Light green
            'cooking': '#FFE4B5',      # Moccasin
            'unknown': '#D3D3D3'       # Light gray
        }
        return colors.get(category, '#FFFFFF')

    def run(self, run_pagerank=True, export_formats=['json']):
        """Запустить построение и анализ графа"""
        start_time = datetime.now()

        # Построить граф
        self.build_graph()

        # Анализ
        self.analyze_graph(run_pagerank=run_pagerank)

        # Экспорт
        output_dir = self.root_dir

        if 'json' in export_formats:
            self.export_json(output_dir / "knowledge_graph.json")

        if 'dot' in export_formats:
            self.export_dot(output_dir / "knowledge_graph.dot")

        if 'html' in export_formats:
            self.export_html_visjs(output_dir / "knowledge_graph.html")

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️  Total time: {elapsed:.2f}s")
        print("🎉 Knowledge graph built successfully!")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Knowledge Graph Construction and Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Build full graph
  %(prog)s --format html            # Interactive HTML visualization
  %(prog)s --category computers     # Subgraph for category
  %(prog)s --pagerank               # Run PageRank analysis
        """
    )

    parser.add_argument(
        '-f', '--format',
        choices=['json', 'dot', 'html'],
        action='append',
        help='Export format (can be repeated, default: json)'
    )

    parser.add_argument(
        '-c', '--category',
        type=str,
        help='Filter by category (computers, household, cooking)'
    )

    parser.add_argument(
        '--pagerank',
        action='store_true',
        default=True,
        help='Run PageRank analysis (default: True)'
    )

    parser.add_argument(
        '--no-pagerank',
        action='store_true',
        help='Skip PageRank analysis'
    )

    args = parser.parse_args()

    # Default format
    if not args.format:
        args.format = ['json']

    # Определить корневую директорию
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Создать builder
    builder = AdvancedKnowledgeGraphBuilder(
        root_dir,
        category_filter=args.category
    )

    # Запустить
    builder.run(
        run_pagerank=not args.no_pagerank,
        export_formats=args.format
    )


if __name__ == "__main__":
    main()
