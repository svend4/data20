#!/usr/bin/env python3
"""
Prerequisites Graph - Граф зависимостей
Показывает, какие статьи нужно прочитать перед другими

Вдохновлено: графами зависимостей курсов в университетах

Алгоритмы:
- Topological Sort (Kahn's algorithm) - правильная последовательность изучения
- Tarjan's algorithm - обнаружение циклов и SCC (Strongly Connected Components)
- Critical Path - longest path в DAG
- Curriculum Builder - автоматическое построение учебных планов
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, deque
import json
import argparse
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime


class TopologicalSorter:
    """Topological Sort using Kahn's algorithm"""

    def __init__(self, graph: Dict[str, List[str]]):
        """
        graph: dict mapping node -> list of nodes it depends on
        """
        self.graph = graph
        self.reverse_graph = defaultdict(list)

        # Build reverse graph (node -> nodes that depend on it)
        for node, dependencies in graph.items():
            for dep in dependencies:
                self.reverse_graph[dep].append(node)

    def sort(self) -> Tuple[List[str], List[str]]:
        """
        Returns (sorted_nodes, nodes_in_cycle)

        Kahn's algorithm:
        1. Find all nodes with in-degree 0
        2. Remove node and its edges
        3. Repeat until no more nodes or cycle detected
        """
        in_degree = {node: len(deps) for node, deps in self.graph.items()}

        # Add nodes that are only in reverse_graph
        for node in self.reverse_graph:
            if node not in in_degree:
                in_degree[node] = 0

        # Find all nodes with in-degree 0
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        sorted_nodes = []

        while queue:
            node = queue.popleft()
            sorted_nodes.append(node)

            # Reduce in-degree for neighbors
            for neighbor in self.reverse_graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        nodes_in_cycle = [node for node, degree in in_degree.items() if degree > 0]

        return sorted_nodes, nodes_in_cycle


class CycleDetector:
    """Обнаружение циклов в графе using Tarjan's algorithm"""

    def __init__(self, graph: Dict[str, List[str]]):
        self.graph = graph
        self.index = 0
        self.stack = []
        self.indices = {}
        self.lowlinks = {}
        self.on_stack = set()
        self.sccs = []  # Strongly Connected Components

    def find_sccs(self) -> List[List[str]]:
        """
        Tarjan's algorithm для нахождения SCC (Strongly Connected Components)

        SCC - максимальное множество вершин, где каждая достижима из любой другой
        Цикл = SCC с размером > 1
        """
        for node in self.graph:
            if node not in self.indices:
                self._strongconnect(node)

        return self.sccs

    def _strongconnect(self, v: str):
        """Рекурсивная часть алгоритма Tarjan"""
        self.indices[v] = self.index
        self.lowlinks[v] = self.index
        self.index += 1
        self.stack.append(v)
        self.on_stack.add(v)

        # Рассмотреть соседей
        for w in self.graph.get(v, []):
            if w not in self.indices:
                # Successor w не был посещён; рекурсия
                self._strongconnect(w)
                self.lowlinks[v] = min(self.lowlinks[v], self.lowlinks[w])
            elif w in self.on_stack:
                # Successor w в стеке и следовательно в текущем SCC
                self.lowlinks[v] = min(self.lowlinks[v], self.indices[w])

        # Если v - корень SCC, создать SCC
        if self.lowlinks[v] == self.indices[v]:
            scc = []
            while True:
                w = self.stack.pop()
                self.on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            self.sccs.append(scc)

    def find_cycles(self) -> List[List[str]]:
        """Найти все циклы (SCC с размером > 1)"""
        sccs = self.find_sccs()
        return [scc for scc in sccs if len(scc) > 1]


class CriticalPathAnalyzer:
    """Анализ критического пути (longest path in DAG)"""

    def __init__(self, graph: Dict[str, List[str]], weights: Optional[Dict[str, float]] = None):
        """
        graph: dict mapping node -> list of dependencies
        weights: optional dict mapping node -> weight (e.g., estimated study time)
        """
        self.graph = graph
        self.weights = weights or {node: 1.0 for node in graph}

    def find_critical_path(self) -> Tuple[List[str], float]:
        """
        Найти критический путь (longest path) используя topological sort

        Returns: (path, total_weight)
        """
        # Topological sort
        sorter = TopologicalSorter(self.graph)
        topo_order, cycles = sorter.sort()

        if cycles:
            raise ValueError(f"Граф содержит циклы: {cycles}")

        # Calculate longest path to each node
        dist = {node: float('-inf') for node in self.graph}
        predecessor = {node: None for node in self.graph}

        # Initialize nodes with no dependencies
        for node in topo_order:
            if not self.graph.get(node, []):
                dist[node] = self.weights.get(node, 1.0)

        # Relax edges in topological order
        for node in topo_order:
            if dist[node] == float('-inf'):
                dist[node] = self.weights.get(node, 1.0)

            # Update successors
            reverse_graph = defaultdict(list)
            for n, deps in self.graph.items():
                for dep in deps:
                    reverse_graph[dep].append(n)

            for successor in reverse_graph.get(node, []):
                new_dist = dist[node] + self.weights.get(successor, 1.0)
                if new_dist > dist[successor]:
                    dist[successor] = new_dist
                    predecessor[successor] = node

        # Find node with maximum distance
        max_node = max(dist, key=dist.get)
        max_dist = dist[max_node]

        # Reconstruct path
        path = []
        current = max_node
        while current is not None:
            path.append(current)
            current = predecessor[current]

        path.reverse()

        return path, max_dist


class CurriculumBuilder:
    """Построитель учебных планов"""

    def __init__(self, graph: Dict[str, List[str]], articles_info: Dict[str, Dict]):
        self.graph = graph
        self.articles_info = articles_info

    def build_curriculum(self, target_article: str, max_depth: Optional[int] = None) -> List[Dict]:
        """
        Построить учебный план для изучения target_article

        Returns: список уроков с информацией о каждом
        """
        # Find all prerequisites recursively
        visited = set()
        curriculum = []

        def collect_prerequisites(article: str, depth: int = 0):
            if article in visited:
                return
            if max_depth is not None and depth > max_depth:
                return

            visited.add(article)

            # First, collect all prerequisites
            for prereq in self.graph.get(article, []):
                collect_prerequisites(prereq, depth + 1)

            # Then add this article
            info = self.articles_info.get(article, {})
            curriculum.append({
                'article': article,
                'title': info.get('title', article),
                'difficulty': info.get('difficulty', 'средний'),
                'depth': depth,
                'order': len(curriculum) + 1
            })

        collect_prerequisites(target_article)

        return curriculum

    def build_progressive_curriculum(self, difficulty_order: List[str] = None) -> List[List[str]]:
        """
        Построить учебный план с прогрессией сложности

        Returns: список уровней, каждый уровень - список статей
        """
        if difficulty_order is None:
            difficulty_order = ['начальный', 'средний', 'продвинутый', 'экспертный']

        # Topological sort
        sorter = TopologicalSorter(self.graph)
        topo_order, _ = sorter.sort()

        # Group by depth first, then by difficulty
        depth_groups = defaultdict(list)

        for article in topo_order:
            depth = self._calculate_depth(article)
            difficulty = self.articles_info.get(article, {}).get('difficulty', 'средний')
            diff_level = difficulty_order.index(difficulty) if difficulty in difficulty_order else 1

            depth_groups[depth].append((diff_level, article))

        # Sort each depth level by difficulty
        curriculum_levels = []
        for depth in sorted(depth_groups.keys()):
            level = [article for _, article in sorted(depth_groups[depth])]
            curriculum_levels.append(level)

        return curriculum_levels

    def _calculate_depth(self, article: str) -> int:
        """Вычислить глубину статьи"""
        visited = set()

        def dfs(node: str) -> int:
            if node in visited:
                return 0
            visited.add(node)

            if not self.graph.get(node, []):
                return 0

            return 1 + max(dfs(dep) for dep in self.graph[node])

        return dfs(article)


class PrerequisitesGraph:
    """Построитель графа зависимостей"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Граф зависимостей
        self.prerequisites = defaultdict(lambda: {'requires': [], 'required_by': []})
        self.articles = {}

        # Кэш для вычислений
        self._depth_cache = {}
        self._cycles_cache = None

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
        """Построить граф зависимостей"""
        print("🔗 Построение графа зависимостей...\n")

        # Собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            self.articles[article_path] = {
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'difficulty': frontmatter.get('difficulty', 'средний') if frontmatter else 'средний',
                'tags': frontmatter.get('tags', []) if frontmatter else []
            }

            # Извлечь prerequisites из frontmatter
            if frontmatter and 'prerequisites' in frontmatter:
                prereqs = frontmatter['prerequisites']
                if isinstance(prereqs, list):
                    for prereq in prereqs:
                        try:
                            target = (md_file.parent / prereq).resolve()

                            if target.exists() and target.is_relative_to(self.root_dir):
                                target_path = str(target.relative_to(self.root_dir))

                                # Добавить в граф
                                if target_path not in self.prerequisites[article_path]['requires']:
                                    self.prerequisites[article_path]['requires'].append(target_path)

                                if article_path not in self.prerequisites[target_path]['required_by']:
                                    self.prerequisites[target_path]['required_by'].append(article_path)
                        except:
                            pass

            # Анализировать контент на наличие фраз типа "предполагает знание"
            prereq_patterns = [
                r'предполагает знание \[([^\]]+)\]\(([^)]+)\)',
                r'требует понимания \[([^\]]+)\]\(([^)]+)\)',
                r'основывается на \[([^\]]+)\]\(([^)]+)\)',
                r'см\. сначала \[([^\]]+)\]\(([^)]+)\)'
            ]

            for pattern in prereq_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for text, link in matches:
                    if link.startswith('http'):
                        continue

                    try:
                        target = (md_file.parent / link.split('#')[0]).resolve()

                        if target.exists() and target.is_relative_to(self.root_dir):
                            target_path = str(target.relative_to(self.root_dir))

                            if target_path not in self.prerequisites[article_path]['requires']:
                                self.prerequisites[article_path]['requires'].append(target_path)

                            if article_path not in self.prerequisites[target_path]['required_by']:
                                self.prerequisites[target_path]['required_by'].append(article_path)
                    except:
                        pass

        print(f"   Статей проиндексировано: {len(self.articles)}")
        print(f"   Зависимостей найдено: {sum(len(p['requires']) for p in self.prerequisites.values())}\n")

    def find_learning_path(self, target_article):
        """Найти путь обучения для статьи"""
        visited = set()
        path = []

        def dfs(article):
            if article in visited:
                return

            visited.add(article)

            # Рекурсивно обработать зависимости
            for prereq in self.prerequisites[article]['requires']:
                dfs(prereq)

            path.append(article)

        dfs(target_article)
        return path

    def calculate_depth(self, article_path):
        """Вычислить глубину статьи (максимальная длина пути до неё)"""
        if article_path in self._depth_cache:
            return self._depth_cache[article_path]

        visited = set()

        def dfs(article):
            if article in visited:
                return 0

            visited.add(article)

            if not self.prerequisites[article]['requires']:
                return 0

            max_depth = 0
            for prereq in self.prerequisites[article]['requires']:
                depth = dfs(prereq)
                max_depth = max(max_depth, depth + 1)

            return max_depth

        depth = dfs(article_path)
        self._depth_cache[article_path] = depth
        return depth

    def detect_cycles(self) -> List[List[str]]:
        """Обнаружить циклические зависимости"""
        if self._cycles_cache is not None:
            return self._cycles_cache

        graph = {article: prereqs['requires'] for article, prereqs in self.prerequisites.items()}
        detector = CycleDetector(graph)
        cycles = detector.find_cycles()

        self._cycles_cache = cycles
        return cycles

    def topological_sort(self) -> Tuple[List[str], List[str]]:
        """
        Получить правильную последовательность изучения (topological sort)

        Returns: (sorted_articles, articles_in_cycles)
        """
        graph = {article: prereqs['requires'] for article, prereqs in self.prerequisites.items()}
        sorter = TopologicalSorter(graph)
        return sorter.sort()

    def find_critical_path(self) -> Tuple[List[str], int]:
        """
        Найти критический путь - самую длинную последовательность зависимостей

        Returns: (path, length)
        """
        graph = {article: prereqs['requires'] for article, prereqs in self.prerequisites.items()}

        # Use article count as weight
        analyzer = CriticalPathAnalyzer(graph)

        try:
            path, length = analyzer.find_critical_path()
            return path, int(length)
        except ValueError:
            # Graph has cycles
            return [], 0

    def build_curriculum_for(self, target_article: str) -> List[Dict]:
        """Построить учебный план для конкретной статьи"""
        graph = {article: prereqs['requires'] for article, prereqs in self.prerequisites.items()}
        builder = CurriculumBuilder(graph, self.articles)
        return builder.build_curriculum(target_article)

    def calculate_graph_metrics(self) -> Dict:
        """Вычислить метрики графа"""
        num_articles = len(self.articles)
        num_edges = sum(len(prereqs['requires']) for prereqs in self.prerequisites.values())

        # Maximum possible edges in directed graph
        max_edges = num_articles * (num_articles - 1)

        # Density: actual_edges / max_possible_edges
        density = num_edges / max_edges if max_edges > 0 else 0

        # Average in-degree and out-degree
        avg_in_degree = num_edges / num_articles if num_articles > 0 else 0
        avg_out_degree = avg_in_degree  # Same in directed graph

        # Find max depth (diameter approximation)
        max_depth = max((self.calculate_depth(article) for article in self.articles), default=0)

        cycles = self.detect_cycles()

        return {
            'num_articles': num_articles,
            'num_dependencies': num_edges,
            'density': round(density, 4),
            'avg_prerequisites_per_article': round(avg_in_degree, 2),
            'max_depth': max_depth,
            'num_cycles': len(cycles),
            'is_dag': len(cycles) == 0
        }

    def find_entry_points(self):
        """Найти статьи-точки входа (без зависимостей)"""
        entry_points = []

        for article in self.articles:
            if not self.prerequisites[article]['requires']:
                entry_points.append(article)

        return entry_points

    def find_advanced_topics(self):
        """Найти продвинутые темы (много зависимостей)"""
        advanced = []

        for article, prereqs in self.prerequisites.items():
            if len(prereqs['requires']) >= 2:
                advanced.append((article, len(prereqs['requires'])))

        advanced.sort(key=lambda x: -x[1])
        return advanced

    def export_to_dot(self, output_file: Path = None) -> str:
        """
        Экспорт в DOT format (Graphviz)

        Можно визуализировать: dot -Tpng graph.dot -o graph.png
        """
        if output_file is None:
            output_file = self.root_dir / "prerequisites_graph.dot"

        lines = []
        lines.append("digraph PrerequisitesGraph {\n")
        lines.append("  rankdir=LR;\n")
        lines.append("  node [shape=box, style=rounded];\n\n")

        # Add nodes with attributes
        for article, info in self.articles.items():
            difficulty = info.get('difficulty', 'средний')
            depth = self.calculate_depth(article)

            # Color by difficulty
            color_map = {
                'начальный': 'lightgreen',
                'средний': 'lightblue',
                'продвинутый': 'orange',
                'экспертный': 'red'
            }
            color = color_map.get(difficulty, 'lightgray')

            label = info['title'].replace('"', '\\"')
            lines.append(f'  "{article}" [label="{label}", fillcolor={color}, style="rounded,filled"];\n')

        lines.append("\n")

        # Add edges
        for article, prereqs in self.prerequisites.items():
            for prereq in prereqs['requires']:
                lines.append(f'  "{prereq}" -> "{article}";\n')

        lines.append("}\n")

        dot_content = ''.join(lines)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dot_content)

        print(f"✅ DOT файл: {output_file}")
        print(f"   Визуализация: dot -Tpng {output_file.name} -o graph.png")

        return dot_content

    def generate_html_visualization(self, output_file: Path = None) -> str:
        """Создать интерактивную HTML визуализацию с vis.js"""
        if output_file is None:
            output_file = self.root_dir / "prerequisites_graph.html"

        # Prepare data for vis.js
        nodes = []
        for i, (article, info) in enumerate(self.articles.items()):
            difficulty = info.get('difficulty', 'средний')
            depth = self.calculate_depth(article)

            # Color by difficulty
            color_map = {
                'начальный': '#90EE90',
                'средний': '#ADD8E6',
                'продвинутый': '#FFA500',
                'экспертный': '#FF6B6B'
            }
            color = color_map.get(difficulty, '#CCCCCC')

            nodes.append({
                'id': i,
                'label': info['title'],
                'title': f"{article}<br>Difficulty: {difficulty}<br>Depth: {depth}",
                'color': color,
                'article_path': article,
                'difficulty': difficulty,
                'depth': depth
            })

        # Build article to id mapping
        article_to_id = {article: i for i, article in enumerate(self.articles.keys())}

        edges = []
        for article, prereqs in self.prerequisites.items():
            if article in article_to_id:
                target_id = article_to_id[article]
                for prereq in prereqs['requires']:
                    if prereq in article_to_id:
                        source_id = article_to_id[prereq]
                        edges.append({
                            'from': source_id,
                            'to': target_id,
                            'arrows': 'to'
                        })

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Prerequisites Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        #mynetwork {{ width: 100%; height: 800px; border: 1px solid #ddd; }}
        .info {{ margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
        .legend {{ display: flex; gap: 20px; margin-top: 10px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🔗 Prerequisites Graph</h1>

    <div class="info">
        <h3>Граф зависимостей статей</h3>
        <p>Показывает последовательность изучения. Стрелка A → B означает "B требует знания A".</p>
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #90EE90;"></div>
                <span>Начальный</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ADD8E6;"></div>
                <span>Средний</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FFA500;"></div>
                <span>Продвинутый</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF6B6B;"></div>
                <span>Экспертный</span>
            </div>
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes, ensure_ascii=False)});
        var edges = new vis.DataSet({json.dumps(edges, ensure_ascii=False)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'LR',
                    sortMethod: 'directed',
                    levelSeparation: 200,
                    nodeSpacing: 150
                }}
            }},
            physics: {{
                enabled: false
            }},
            nodes: {{
                shape: 'box',
                margin: 10,
                font: {{
                    size: 14
                }}
            }},
            edges: {{
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'horizontal'
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }}
            }}
        }};

        var network = new vis.Network(container, data, options);

        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                alert('Article: ' + node.article_path + '\\nTitle: ' + node.label + '\\nDifficulty: ' + node.difficulty + '\\nDepth: ' + node.depth);
            }}
        }});
    </script>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML визуализация: {output_file}")

        return html_content

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Граф зависимостей\n\n")
        lines.append("> Показывает последовательность изучения материала\n\n")

        # Метрики графа
        metrics = self.calculate_graph_metrics()

        lines.append("## Метрики графа\n\n")
        lines.append(f"- **Всего статей**: {metrics['num_articles']}\n")
        lines.append(f"- **Зависимостей**: {metrics['num_dependencies']}\n")
        lines.append(f"- **Плотность графа**: {metrics['density']:.4f}\n")
        lines.append(f"- **Средне prereq/статья**: {metrics['avg_prerequisites_per_article']:.2f}\n")
        lines.append(f"- **Максимальная глубина**: {metrics['max_depth']}\n")
        lines.append(f"- **Циклов найдено**: {metrics['num_cycles']}\n")
        lines.append(f"- **Является DAG**: {'✅ Да' if metrics['is_dag'] else '❌ Нет (есть циклы)'}\n\n")

        # Циклы (если есть)
        cycles = self.detect_cycles()
        if cycles:
            lines.append("## ⚠️ Циклические зависимости\n\n")
            lines.append("> Эти статьи образуют циклы - нужно разорвать зависимости!\n\n")
            for i, cycle in enumerate(cycles, 1):
                lines.append(f"### Цикл {i}\n\n")
                for article in cycle:
                    title = self.articles.get(article, {}).get('title', article)
                    lines.append(f"- [{title}]({article})\n")
                lines.append("\n")

        # Критический путь
        critical_path, length = self.find_critical_path()
        if critical_path:
            lines.append("## 🎯 Критический путь\n\n")
            lines.append(f"> Самая длинная последовательность зависимостей ({length} статей)\n\n")
            for i, article in enumerate(critical_path, 1):
                title = self.articles.get(article, {}).get('title', article)
                lines.append(f"{i}. [{title}]({article})\n")
            lines.append("\n")

        # Статистика
        entry_points = self.find_entry_points()
        advanced_topics = self.find_advanced_topics()

        lines.append("## Статистика\n\n")
        lines.append(f"- **Точки входа** (без зависимостей): {len(entry_points)}\n")
        lines.append(f"- **Продвинутые темы** (2+ зависимости): {len(advanced_topics)}\n\n")

        # Точки входа
        lines.append("## Точки входа (начните здесь)\n\n")
        lines.append("> Эти статьи можно читать первыми\n\n")

        for article in entry_points[:10]:
            title = self.articles[article]['title']
            difficulty = self.articles[article]['difficulty']
            lines.append(f"### {title}\n\n")
            lines.append(f"- **Файл**: [{article}]({article})\n")
            lines.append(f"- **Сложность**: {difficulty}\n")

            if self.prerequisites[article]['required_by']:
                lines.append(f"- **Открывает доступ к**: {len(self.prerequisites[article]['required_by'])} статьям\n")

            lines.append("\n")

        # Продвинутые темы
        if advanced_topics:
            lines.append("\n## Продвинутые темы\n\n")
            lines.append("> Требуют предварительного изучения\n\n")

            for article, prereq_count in advanced_topics[:10]:
                title = self.articles[article]['title']
                depth = self.calculate_depth(article)

                lines.append(f"### {title}\n\n")
                lines.append(f"- **Файл**: [{article}]({article})\n")
                lines.append(f"- **Зависимостей**: {prereq_count}\n")
                lines.append(f"- **Глубина**: {depth} уровень\n")

                # Показать зависимости
                if self.prerequisites[article]['requires']:
                    lines.append("\n**Требует знания:**\n")
                    for prereq in self.prerequisites[article]['requires']:
                        prereq_title = self.articles.get(prereq, {}).get('title', prereq)
                        lines.append(f"- [{prereq_title}]({prereq})\n")

                # Путь обучения
                learning_path = self.find_learning_path(article)
                if len(learning_path) > 1:
                    lines.append("\n**Рекомендуемый путь обучения:**\n")
                    for i, step in enumerate(learning_path, 1):
                        step_title = self.articles.get(step, {}).get('title', step)
                        lines.append(f"{i}. [{step_title}]({step})\n")

                lines.append("\n")

        output_file = self.root_dir / "PREREQUISITES_GRAPH.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить граф в JSON"""
        metrics = self.calculate_graph_metrics()
        cycles = self.detect_cycles()
        critical_path, path_length = self.find_critical_path()
        topo_order, nodes_in_cycles = self.topological_sort()

        data = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'num_articles': len(self.articles),
                'num_dependencies': sum(len(p['requires']) for p in self.prerequisites.values())
            },
            'metrics': metrics,
            'articles': self.articles,
            'graph': {
                article: {
                    'requires': prereqs['requires'],
                    'required_by': prereqs['required_by'],
                    'depth': self.calculate_depth(article)
                }
                for article, prereqs in self.prerequisites.items()
            },
            'analysis': {
                'entry_points': self.find_entry_points(),
                'advanced_topics': [
                    {'article': article, 'prerequisites': count}
                    for article, count in self.find_advanced_topics()
                ],
                'cycles': cycles,
                'critical_path': {
                    'path': critical_path,
                    'length': path_length
                },
                'topological_order': topo_order,
                'nodes_in_cycles': nodes_in_cycles
            }
        }

        output_file = self.root_dir / "prerequisites_graph.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON граф: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Prerequisites Graph - Граф зависимостей между статьями',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                    # Полный анализ
  %(prog)s --cycles                           # Проверка циклов
  %(prog)s --critical-path                    # Показать критический путь
  %(prog)s --curriculum "article.md"          # Учебный план для статьи
  %(prog)s --topo-sort                        # Правильная последовательность изучения
  %(prog)s --export dot                       # Экспорт в Graphviz DOT
  %(prog)s --export html                      # Интерактивная HTML визуализация
  %(prog)s --metrics                          # Метрики графа
        """
    )

    parser.add_argument(
        '--cycles',
        action='store_true',
        help='Проверить наличие циклических зависимостей'
    )

    parser.add_argument(
        '--critical-path',
        action='store_true',
        help='Показать критический путь (longest path)'
    )

    parser.add_argument(
        '--curriculum',
        metavar='ARTICLE',
        help='Построить учебный план для указанной статьи'
    )

    parser.add_argument(
        '--topo-sort',
        action='store_true',
        help='Показать правильную последовательность изучения (topological sort)'
    )

    parser.add_argument(
        '--export',
        choices=['dot', 'html', 'json'],
        help='Экспорт графа в указанном формате'
    )

    parser.add_argument(
        '--metrics',
        action='store_true',
        help='Показать метрики графа'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Создать полный отчёт (по умолчанию)'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    graph = PrerequisitesGraph(root_dir)
    graph.build_graph()

    # Если нет специфичных флагов, выполнить полный анализ
    if not any([args.cycles, args.critical_path, args.curriculum, args.topo_sort,
                args.export, args.metrics]):
        args.report = True

    # Обработка команд
    if args.cycles:
        print("\n🔍 Проверка циклических зависимостей...\n")
        cycles = graph.detect_cycles()

        if cycles:
            print(f"❌ Найдено {len(cycles)} циклов:\n")
            for i, cycle in enumerate(cycles, 1):
                print(f"Цикл {i}:")
                for article in cycle:
                    title = graph.articles.get(article, {}).get('title', article)
                    print(f"  - {title} ({article})")
                print()
        else:
            print("✅ Циклов не обнаружено. Граф является DAG (Directed Acyclic Graph).\n")

    if args.critical_path:
        print("\n🎯 Критический путь (longest path):\n")
        critical_path, length = graph.find_critical_path()

        if critical_path:
            print(f"Длина: {length} статей\n")
            for i, article in enumerate(critical_path, 1):
                title = graph.articles.get(article, {}).get('title', article)
                depth = graph.calculate_depth(article)
                print(f"{i}. {title}")
                print(f"   Файл: {article}")
                print(f"   Глубина: {depth}\n")
        else:
            print("❌ Невозможно вычислить критический путь (граф содержит циклы)\n")

    if args.curriculum:
        print(f"\n📚 Учебный план для: {args.curriculum}\n")
        curriculum = graph.build_curriculum_for(args.curriculum)

        if curriculum:
            print(f"Всего статей для изучения: {len(curriculum)}\n")
            print("Последовательность изучения:\n")
            for lesson in curriculum:
                print(f"{lesson['order']}. {lesson['title']}")
                print(f"   Сложность: {lesson['difficulty']}")
                print(f"   Глубина: {lesson['depth']}")
                print(f"   Файл: {lesson['article']}\n")
        else:
            print(f"❌ Статья '{args.curriculum}' не найдена.\n")

    if args.topo_sort:
        print("\n📋 Правильная последовательность изучения (Topological Sort):\n")
        topo_order, nodes_in_cycles = graph.topological_sort()

        if nodes_in_cycles:
            print(f"⚠️ Внимание: {len(nodes_in_cycles)} статей в циклах (не включены в сортировку)\n")

        print(f"Всего статей: {len(topo_order)}\n")
        for i, article in enumerate(topo_order[:20], 1):  # Показать первые 20
            title = graph.articles.get(article, {}).get('title', article)
            depth = graph.calculate_depth(article)
            print(f"{i}. {title} (глубина: {depth})")

        if len(topo_order) > 20:
            print(f"\n... и ещё {len(topo_order) - 20} статей")

        print()

    if args.metrics:
        print("\n📊 Метрики графа:\n")
        metrics = graph.calculate_graph_metrics()

        print(f"Статей: {metrics['num_articles']}")
        print(f"Зависимостей: {metrics['num_dependencies']}")
        print(f"Плотность: {metrics['density']:.4f}")
        print(f"Средне prereq/статья: {metrics['avg_prerequisites_per_article']:.2f}")
        print(f"Максимальная глубина: {metrics['max_depth']}")
        print(f"Циклов: {metrics['num_cycles']}")
        print(f"Является DAG: {'✅ Да' if metrics['is_dag'] else '❌ Нет'}\n")

    if args.export:
        print(f"\n📤 Экспорт в формат: {args.export}\n")

        if args.export == 'dot':
            graph.export_to_dot()
        elif args.export == 'html':
            graph.generate_html_visualization()
        elif args.export == 'json':
            graph.save_json()

        print()

    if args.report:
        print()
        graph.generate_report()
        graph.save_json()
        graph.generate_html_visualization()
        graph.export_to_dot()
        print()


if __name__ == "__main__":
    main()
