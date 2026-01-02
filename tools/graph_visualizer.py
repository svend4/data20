#!/usr/bin/env python3
"""
Graph Visualizer - Визуализация графов
Создаёт интерактивные визуализации графов связей между статьями

Вдохновлено: D3.js force graphs, Obsidian graph view
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, deque, Counter
import json
import argparse
import math
from typing import Dict, List, Tuple, Set, Optional


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


class GraphAnalyzer:
    """Анализатор графа - вычисление метрик"""

    def __init__(self, nodes: List[Dict], links: List[Dict]):
        self.nodes = {n['id']: n for n in nodes}
        self.links = links

        # Построить adjacency list
        self.adj_list = defaultdict(set)
        self.reverse_adj = defaultdict(set)  # Для входящих рёбер

        for link in links:
            source = link['source']
            target = link['target']
            self.adj_list[source].add(target)
            self.reverse_adj[target].add(source)

    def calculate_degree_centrality(self) -> Dict[str, Dict]:
        """Вычислить центральность по степени (Degree Centrality)"""
        centrality = {}

        for node_id in self.nodes:
            out_degree = len(self.adj_list.get(node_id, set()))
            in_degree = len(self.reverse_adj.get(node_id, set()))
            total_degree = out_degree + in_degree

            centrality[node_id] = {
                'out_degree': out_degree,
                'in_degree': in_degree,
                'total_degree': total_degree
            }

        return centrality

    def calculate_pagerank(self, iterations: int = 100, damping: float = 0.85) -> Dict[str, float]:
        """
        Вычислить PageRank

        PageRank алгоритм:
        PR(A) = (1-d) + d * Σ(PR(Ti) / C(Ti))
        где d = damping factor, Ti = входящие ссылки, C(Ti) = исходящие ссылки из Ti
        """
        n = len(self.nodes)
        if n == 0:
            return {}

        # Инициализация
        pr = {node_id: 1.0 / n for node_id in self.nodes}

        for _ in range(iterations):
            new_pr = {}

            for node_id in self.nodes:
                rank_sum = 0.0

                # Суммировать вклад от входящих нод
                for incoming in self.reverse_adj.get(node_id, set()):
                    out_count = len(self.adj_list.get(incoming, set()))
                    if out_count > 0:
                        rank_sum += pr[incoming] / out_count

                new_pr[node_id] = (1 - damping) / n + damping * rank_sum

            pr = new_pr

        return pr

    def find_connected_components(self) -> List[Set[str]]:
        """Найти связные компоненты (для неориентированного графа)"""
        visited = set()
        components = []

        def bfs(start):
            component = set()
            queue = deque([start])
            visited.add(start)

            while queue:
                node = queue.popleft()
                component.add(node)

                # Все соседи (входящие и исходящие)
                neighbors = self.adj_list.get(node, set()) | self.reverse_adj.get(node, set())

                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            return component

        for node_id in self.nodes:
            if node_id not in visited:
                components.append(bfs(node_id))

        return components

    def calculate_graph_metrics(self) -> Dict:
        """Вычислить общие метрики графа"""
        n = len(self.nodes)
        m = len(self.links)

        # Density
        max_edges = n * (n - 1)  # Directed graph
        density = m / max_edges if max_edges > 0 else 0

        # Degree stats
        centrality = self.calculate_degree_centrality()
        degrees = [c['total_degree'] for c in centrality.values()]

        avg_degree = sum(degrees) / n if n > 0 else 0
        max_degree = max(degrees) if degrees else 0

        # Connected components
        components = self.find_connected_components()

        return {
            'nodes': n,
            'edges': m,
            'density': round(density, 4),
            'avg_degree': round(avg_degree, 2),
            'max_degree': max_degree,
            'connected_components': len(components),
            'largest_component_size': max([len(c) for c in components]) if components else 0
        }


class CommunityDetector:
    """Обнаружение сообществ в графе"""

    def __init__(self, nodes: List[Dict], links: List[Dict]):
        self.nodes = {n['id']: n for n in nodes}
        self.links = links

        # Build adjacency
        self.adj_list = defaultdict(set)
        for link in links:
            source = link['source']
            target = link['target']
            self.adj_list[source].add(target)
            self.adj_list[target].add(source)  # Treat as undirected

    def detect_communities_simple(self) -> Dict[str, int]:
        """
        Простое обнаружение сообществ через BFS
        (каждая связная компонента = сообщество)
        """
        visited = set()
        communities = {}
        community_id = 0

        def bfs(start, comm_id):
            queue = deque([start])
            visited.add(start)
            communities[start] = comm_id

            while queue:
                node = queue.popleft()

                for neighbor in self.adj_list.get(node, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        communities[neighbor] = comm_id
                        queue.append(neighbor)

        for node_id in self.nodes:
            if node_id not in visited:
                bfs(node_id, community_id)
                community_id += 1

        return communities

    def detect_communities_by_category(self) -> Dict[str, str]:
        """Обнаружение сообществ по категориям статей"""
        communities = {}

        for node_id, node_data in self.nodes.items():
            category = node_data.get('category', 'other')
            communities[node_id] = category

        return communities


class LayoutManager:
    """Менеджер layout'ов для графа"""

    @staticmethod
    def calculate_circular_layout(nodes: List[Dict], width: int = 800, height: int = 600) -> Dict[str, Tuple[float, float]]:
        """Круговой layout"""
        n = len(nodes)
        positions = {}

        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 3

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[node['id']] = (x, y)

        return positions

    @staticmethod
    def calculate_grid_layout(nodes: List[Dict], width: int = 800, height: int = 600) -> Dict[str, Tuple[float, float]]:
        """Сетка"""
        n = len(nodes)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        cell_width = width / (cols + 1)
        cell_height = height / (rows + 1)

        positions = {}

        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols

            x = (col + 1) * cell_width
            y = (row + 1) * cell_height

            positions[node['id']] = (x, y)

        return positions

    @staticmethod
    def calculate_radial_layout(nodes: List[Dict], communities: Dict[str, int],
                               width: int = 800, height: int = 600) -> Dict[str, Tuple[float, float]]:
        """Радиальный layout (сообщества по кругам)"""
        positions = {}

        # Группировать по сообществам
        comm_groups = defaultdict(list)
        for node in nodes:
            comm_id = communities.get(node['id'], 0)
            comm_groups[comm_id].append(node)

        center_x = width / 2
        center_y = height / 2

        num_communities = len(comm_groups)

        for comm_idx, (comm_id, comm_nodes) in enumerate(comm_groups.items()):
            # Angle для этого сообщества
            comm_angle = 2 * math.pi * comm_idx / num_communities

            # Radius для этого сообщества
            base_radius = min(width, height) / 4

            for node_idx, node in enumerate(comm_nodes):
                # Разместить ноды сообщества по кругу
                node_angle = comm_angle + (2 * math.pi * node_idx / len(comm_nodes)) / num_communities
                radius = base_radius + (len(comm_nodes) * 2)

                x = center_x + radius * math.cos(node_angle)
                y = center_y + radius * math.sin(node_angle)

                positions[node['id']] = (x, y)

        return positions


class GraphFilter:
    """Фильтрация графа"""

    @staticmethod
    def filter_by_category(nodes: List[Dict], links: List[Dict], categories: List[str]) -> Tuple[List[Dict], List[Dict]]:
        """Фильтровать по категориям"""
        filtered_nodes = [n for n in nodes if n.get('category') in categories]
        node_ids = {n['id'] for n in filtered_nodes}

        filtered_links = [l for l in links if l['source'] in node_ids and l['target'] in node_ids]

        return filtered_nodes, filtered_links

    @staticmethod
    def filter_by_degree(nodes: List[Dict], links: List[Dict], min_degree: int = 1) -> Tuple[List[Dict], List[Dict]]:
        """Фильтровать по минимальной степени"""
        # Подсчитать степени
        degree = Counter()

        for link in links:
            degree[link['source']] += 1
            degree[link['target']] += 1

        filtered_nodes = [n for n in nodes if degree[n['id']] >= min_degree]
        node_ids = {n['id'] for n in filtered_nodes}

        filtered_links = [l for l in links if l['source'] in node_ids and l['target'] in node_ids]

        return filtered_nodes, filtered_links

    @staticmethod
    def get_top_nodes_by_pagerank(nodes: List[Dict], links: List[Dict], limit: int = 10) -> List[Dict]:
        """Получить топ-N нод по PageRank"""
        analyzer = GraphAnalyzer(nodes, links)
        pagerank = analyzer.calculate_pagerank()

        # Сортировать по PageRank
        sorted_nodes = sorted(nodes, key=lambda n: pagerank.get(n['id'], 0), reverse=True)

        return sorted_nodes[:limit]


def main():
    parser = argparse.ArgumentParser(
        description='🕸️ Graph Visualizer - Визуализация графов знаний',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --build                    # Построить и визуализировать граф
  %(prog)s --analyze                  # Анализ графа (метрики, PageRank)
  %(prog)s --communities              # Обнаружение сообществ
  %(prog)s --layout circular          # Использовать круговой layout
  %(prog)s --filter-category computers # Фильтровать по категории
  %(prog)s --top 10                   # Топ-10 нод по PageRank
        """
    )

    parser.add_argument('--build', action='store_true',
                        help='Построить граф и создать визуализацию')
    parser.add_argument('--analyze', action='store_true',
                        help='Анализ графа (метрики, centrality, PageRank)')
    parser.add_argument('--communities', action='store_true',
                        help='Обнаружение сообществ')
    parser.add_argument('--layout', type=str, choices=['force', 'circular', 'grid', 'radial'],
                        default='force', help='Тип layout для визуализации')
    parser.add_argument('--filter-category', type=str, nargs='+',
                        help='Фильтровать по категориям')
    parser.add_argument('--filter-degree', type=int, metavar='MIN',
                        help='Фильтровать по минимальной степени')
    parser.add_argument('--top', type=int, metavar='N',
                        help='Показать топ-N нод по PageRank')
    parser.add_argument('--output', type=str,
                        help='Выходной файл')
    parser.add_argument('--json', action='store_true',
                        help='Сохранить граф в JSON')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Если аргументы не указаны, показать help
    if not any(vars(args).values()):
        parser.print_help()
        return

    visualizer = GraphVisualizer(root_dir)
    visualizer.build_graph()

    nodes = visualizer.nodes
    links = visualizer.links

    # Apply filters
    if args.filter_category:
        print(f"🔍 Фильтр по категориям: {', '.join(args.filter_category)}")
        nodes, links = GraphFilter.filter_by_category(nodes, links, args.filter_category)
        print(f"   Осталось узлов: {len(nodes)}, рёбер: {len(links)}\n")

    if args.filter_degree:
        print(f"🔍 Фильтр по степени >= {args.filter_degree}")
        nodes, links = GraphFilter.filter_by_degree(nodes, links, args.filter_degree)
        print(f"   Осталось узлов: {len(nodes)}, рёбер: {len(links)}\n")

    # --analyze: анализ графа
    if args.analyze:
        print("📊 Анализ графа...\n")
        analyzer = GraphAnalyzer(nodes, links)

        # Graph metrics
        metrics = analyzer.calculate_graph_metrics()
        print("## Метрики графа\n")
        print(f"   Узлы: {metrics['nodes']}")
        print(f"   Рёбра: {metrics['edges']}")
        print(f"   Плотность: {metrics['density']}")
        print(f"   Средняя степень: {metrics['avg_degree']}")
        print(f"   Макс. степень: {metrics['max_degree']}")
        print(f"   Связные компоненты: {metrics['connected_components']}")
        print(f"   Размер наибольшей компоненты: {metrics['largest_component_size']}\n")

        # PageRank
        pagerank = analyzer.calculate_pagerank()
        print("## Топ-5 по PageRank\n")
        top_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (node_id, pr) in enumerate(top_pr, 1):
            node_data = visualizer.articles.get(node_id, {})
            title = node_data.get('title', node_id)
            print(f"   {i}. {title}: {pr:.4f}")
        print()

        # Degree centrality
        centrality = analyzer.calculate_degree_centrality()
        print("## Топ-5 по степени\n")
        top_degree = sorted(centrality.items(), key=lambda x: x[1]['total_degree'], reverse=True)[:5]
        for i, (node_id, deg) in enumerate(top_degree, 1):
            node_data = visualizer.articles.get(node_id, {})
            title = node_data.get('title', node_id)
            print(f"   {i}. {title}: {deg['total_degree']} (in: {deg['in_degree']}, out: {deg['out_degree']})")
        print()

    # --communities: обнаружение сообществ
    if args.communities:
        print("🔍 Обнаружение сообществ...\n")
        detector = CommunityDetector(nodes, links)

        # Simple BFS communities
        communities = detector.detect_communities_simple()
        comm_counter = Counter(communities.values())

        print(f"Найдено сообществ: {len(comm_counter)}\n")
        for comm_id, count in sorted(comm_counter.items()):
            print(f"   Сообщество {comm_id}: {count} узлов")
        print()

        # Category-based communities
        cat_communities = detector.detect_communities_by_category()
        cat_counter = Counter(cat_communities.values())

        print(f"Сообщества по категориям: {len(cat_counter)}\n")
        for category, count in sorted(cat_counter.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} узлов")
        print()

    # --top: топ нод по PageRank
    if args.top:
        print(f"📊 Топ-{args.top} узлов по PageRank...\n")
        top_nodes = GraphFilter.get_top_nodes_by_pagerank(nodes, links, args.top)

        analyzer = GraphAnalyzer(nodes, links)
        pagerank = analyzer.calculate_pagerank()

        for i, node in enumerate(top_nodes, 1):
            node_id = node['id']
            title = node.get('label', node_id)
            pr = pagerank.get(node_id, 0)
            category = node.get('category', 'unknown')
            print(f"   {i}. {title}")
            print(f"      PageRank: {pr:.4f}, Категория: {category}\n")

    # --build: создать визуализацию
    if args.build:
        print("🎨 Создание визуализации...\n")

        # Update visualizer with filtered nodes/links
        visualizer.nodes = nodes
        visualizer.links = links

        if args.layout == 'force':
            # Default D3 force layout
            visualizer.generate_d3_visualization()
        else:
            # Static layouts
            print(f"   Layout: {args.layout}")

            if args.layout == 'circular':
                positions = LayoutManager.calculate_circular_layout(nodes)
            elif args.layout == 'grid':
                positions = LayoutManager.calculate_grid_layout(nodes)
            elif args.layout == 'radial':
                detector = CommunityDetector(nodes, links)
                communities = detector.detect_communities_simple()
                positions = LayoutManager.calculate_radial_layout(nodes, communities)

            # Generate static visualization with positions
            # (Would need to create a static SVG renderer here)
            # For now, just save as JSON with positions
            data = {
                'nodes': nodes,
                'links': links,
                'layout': args.layout,
                'positions': {k: {'x': v[0], 'y': v[1]} for k, v in positions.items()}
            }

            output_file = args.output or root_dir / f"knowledge_graph_{args.layout}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"   ✅ Граф с {args.layout} layout: {output_file}")

    # --json: сохранить JSON
    if args.json:
        visualizer.save_json()


if __name__ == "__main__":
    main()
