#!/usr/bin/env python3
"""
Network Analyzer - Продвинутый анализ сети
Вычисляет широкий спектр сетевых метрик:
- Centrality (degree, betweenness, closeness, eigenvector, PageRank)
- Clustering coefficient
- Community detection
- Graph properties (density, diameter, components)
- Path analysis

Вдохновлено: NetworkX, Gephi, igraph, Neo4j
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, deque
import json
import math


class AdvancedNetworkAnalyzer:
    """Продвинутый анализатор сети"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.graph = defaultdict(set)  # Направленный граф
        self.undirected_graph = defaultdict(set)  # Ненаправленный для некоторых метрик
        self.articles = set()
        self.article_titles = {}

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

    def build_network(self):
        print("📊 Построение сети...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            source = str(md_file.relative_to(self.root_dir))
            self.articles.add(source)

            # Сохранить заголовок
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            self.article_titles[source] = title

            # Извлечь ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in links:
                if not link.startswith('http'):
                    try:
                        target = (md_file.parent / link.split('#')[0]).resolve()
                        if target.exists() and target.is_relative_to(self.root_dir):
                            target_path = str(target.relative_to(self.root_dir))
                            self.graph[source].add(target_path)
                            self.undirected_graph[source].add(target_path)
                            self.undirected_graph[target_path].add(source)
                            self.articles.add(target_path)
                    except:
                        pass

        print(f"   Nodes: {len(self.articles)}")
        print(f"   Edges: {sum(len(v) for v in self.graph.values())}\n")

    def calculate_degree_centrality(self):
        """Вычислить degree centrality"""
        centrality = {}

        for article in self.articles:
            out_degree = len(self.graph[article])
            in_degree = sum(1 for neighbors in self.graph.values() if article in neighbors)

            centrality[article] = {
                'out_degree': out_degree,
                'in_degree': in_degree,
                'total_degree': out_degree + in_degree
            }

        return centrality

    def bfs_shortest_paths(self, start):
        """BFS для поиска кратчайших путей"""
        distances = {start: 0}
        paths_through = defaultdict(int)  # Количество кратчайших путей через узел
        queue = deque([start])
        predecessors = defaultdict(list)

        while queue:
            node = queue.popleft()

            for neighbor in self.undirected_graph[node]:
                if neighbor not in distances:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)
                    predecessors[neighbor].append(node)
                elif distances[neighbor] == distances[node] + 1:
                    predecessors[neighbor].append(node)

        return distances, predecessors

    def calculate_betweenness_centrality(self):
        """Вычислить betweenness centrality (алгоритм Brandes)"""
        betweenness = {article: 0.0 for article in self.articles}

        for source in self.articles:
            # BFS от source
            distances = {source: 0}
            paths_count = {source: 1}
            stack = []
            predecessors = defaultdict(list)
            queue = deque([source])

            while queue:
                node = queue.popleft()
                stack.append(node)

                for neighbor in self.undirected_graph[node]:
                    # Первое посещение neighbor
                    if neighbor not in distances:
                        distances[neighbor] = distances[node] + 1
                        queue.append(neighbor)

                    # Кратчайший путь к neighbor через node
                    if distances[neighbor] == distances[node] + 1:
                        paths_count[neighbor] = paths_count.get(neighbor, 0) + paths_count[node]
                        predecessors[neighbor].append(node)

            # Обратный проход
            dependency = {article: 0.0 for article in self.articles}

            while stack:
                node = stack.pop()

                for pred in predecessors[node]:
                    dependency[pred] += (paths_count[pred] / paths_count[node]) * (1 + dependency[node])

                if node != source:
                    betweenness[node] += dependency[node]

        # Нормализация
        n = len(self.articles)
        if n > 2:
            normalization = 1.0 / ((n - 1) * (n - 2))
            betweenness = {k: v * normalization for k, v in betweenness.items()}

        return betweenness

    def calculate_closeness_centrality(self):
        """Вычислить closeness centrality"""
        closeness = {}

        for article in self.articles:
            distances, _ = self.bfs_shortest_paths(article)

            # Сумма расстояний до всех достижимых узлов
            total_distance = sum(distances.values())

            # Closeness = (n-1) / sum(distances)
            if total_distance > 0:
                closeness[article] = (len(distances) - 1) / total_distance
            else:
                closeness[article] = 0.0

        return closeness

    def calculate_pagerank(self, damping=0.85, max_iterations=100, tolerance=1e-6):
        """Вычислить PageRank"""
        n = len(self.articles)
        pagerank = {article: 1.0 / n for article in self.articles}

        for iteration in range(max_iterations):
            new_pagerank = {}
            max_diff = 0

            for article in self.articles:
                # Базовая вероятность
                rank = (1 - damping) / n

                # Вклад от входящих ссылок
                for source in self.articles:
                    if article in self.graph[source]:
                        out_degree = len(self.graph[source])
                        if out_degree > 0:
                            rank += damping * pagerank[source] / out_degree

                new_pagerank[article] = rank
                max_diff = max(max_diff, abs(new_pagerank[article] - pagerank[article]))

            pagerank = new_pagerank

            # Проверка сходимости
            if max_diff < tolerance:
                break

        return pagerank

    def calculate_clustering_coefficient(self):
        """Вычислить clustering coefficient (локальный и глобальный)"""
        clustering = {}

        for article in self.articles:
            neighbors = self.undirected_graph[article]
            k = len(neighbors)

            if k < 2:
                clustering[article] = 0.0
                continue

            # Подсчитать связи между соседями
            links_between_neighbors = 0

            for n1 in neighbors:
                for n2 in neighbors:
                    if n1 != n2 and n2 in self.undirected_graph[n1]:
                        links_between_neighbors += 1

            # Коэффициент кластеризации
            max_links = k * (k - 1)
            clustering[article] = links_between_neighbors / max_links if max_links > 0 else 0.0

        # Глобальный коэффициент
        global_clustering = sum(clustering.values()) / len(clustering) if clustering else 0.0

        return clustering, global_clustering

    def detect_communities_simple(self):
        """Простое определение сообществ (connected components)"""
        visited = set()
        communities = []

        def dfs(node, community):
            visited.add(node)
            community.add(node)

            for neighbor in self.undirected_graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, community)

        for article in self.articles:
            if article not in visited:
                community = set()
                dfs(article, community)
                communities.append(community)

        return communities

    def calculate_graph_properties(self):
        """Вычислить общие свойства графа"""
        n = len(self.articles)
        m = sum(len(v) for v in self.graph.values())

        # Плотность
        max_edges = n * (n - 1)
        density = m / max_edges if max_edges > 0 else 0.0

        # Диаметр и средняя длина пути
        all_distances = []

        for article in self.articles:
            distances, _ = self.bfs_shortest_paths(article)
            all_distances.extend(distances.values())

        diameter = max(all_distances) if all_distances else 0
        avg_path_length = sum(all_distances) / len(all_distances) if all_distances else 0

        # Connected components
        communities = self.detect_communities_simple()

        return {
            'nodes': n,
            'edges': m,
            'density': density,
            'diameter': diameter,
            'avg_path_length': avg_path_length,
            'connected_components': len(communities),
            'largest_component': max(len(c) for c in communities) if communities else 0
        }

    def generate_report(self, all_metrics):
        """Создать Markdown отчёт"""
        lines = []
        lines.append("# 📊 Продвинутый сетевой анализ\n\n")
        lines.append("> Комплексный анализ графа знаний\n\n")

        # Свойства графа
        props = all_metrics['graph_properties']

        lines.append("## Свойства графа\n\n")
        lines.append(f"- **Узлов (nodes)**: {props['nodes']}\n")
        lines.append(f"- **Рёбер (edges)**: {props['edges']}\n")
        lines.append(f"- **Плотность (density)**: {props['density']:.4f}\n")
        lines.append(f"- **Диаметр (diameter)**: {props['diameter']}\n")
        lines.append(f"- **Средняя длина пути**: {props['avg_path_length']:.2f}\n")
        lines.append(f"- **Connected components**: {props['connected_components']}\n")
        lines.append(f"- **Largest component**: {props['largest_component']}\n\n")

        # Топ по PageRank
        lines.append("## Топ-10 по PageRank\n\n")
        sorted_pr = sorted(all_metrics['pagerank'].items(), key=lambda x: -x[1])

        for article, score in sorted_pr[:10]:
            title = self.article_titles.get(article, Path(article).stem)
            lines.append(f"1. **{title}**: {score:.6f}\n")

        # Топ по Betweenness
        lines.append("\n## Топ-10 по Betweenness Centrality\n\n")
        lines.append("> Статьи, находящиеся на кратчайших путях между другими\n\n")

        sorted_bt = sorted(all_metrics['betweenness'].items(), key=lambda x: -x[1])

        for article, score in sorted_bt[:10]:
            title = self.article_titles.get(article, Path(article).stem)
            lines.append(f"1. **{title}**: {score:.6f}\n")

        # Топ по Closeness
        lines.append("\n## Топ-10 по Closeness Centrality\n\n")
        lines.append("> Статьи с минимальным средним расстоянием до других\n\n")

        sorted_cl = sorted(all_metrics['closeness'].items(), key=lambda x: -x[1])

        for article, score in sorted_cl[:10]:
            title = self.article_titles.get(article, Path(article).stem)
            lines.append(f"1. **{title}**: {score:.6f}\n")

        # Кластеризация
        lines.append("\n## Кластеризация\n\n")
        lines.append(f"- **Глобальный коэффициент кластеризации**: {all_metrics['global_clustering']:.4f}\n\n")

        lines.append("### Топ-10 по локальной кластеризации\n\n")
        sorted_clust = sorted(all_metrics['clustering'].items(), key=lambda x: -x[1])

        for article, score in sorted_clust[:10]:
            title = self.article_titles.get(article, Path(article).stem)
            lines.append(f"1. **{title}**: {score:.4f}\n")

        # Degree centrality
        lines.append("\n## Топ-10 по Degree Centrality\n\n")
        sorted_deg = sorted(all_metrics['degree'].items(), key=lambda x: -x[1]['total_degree'])

        for article, metrics in sorted_deg[:10]:
            title = self.article_titles.get(article, Path(article).stem)
            lines.append(f"1. **{title}**: {metrics['total_degree']} ")
            lines.append(f"(in: {metrics['in_degree']}, out: {metrics['out_degree']})\n")

        output_file = self.root_dir / "ADVANCED_NETWORK_ANALYSIS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Сетевой анализ: {output_file}")

    def save_json(self, all_metrics):
        """Сохранить все метрики в JSON"""
        data = {
            'graph_properties': all_metrics['graph_properties'],
            'nodes': {}
        }

        # Собрать все метрики для каждого узла
        for article in self.articles:
            title = self.article_titles.get(article, Path(article).stem)

            data['nodes'][article] = {
                'title': title,
                'pagerank': all_metrics['pagerank'].get(article, 0),
                'betweenness': all_metrics['betweenness'].get(article, 0),
                'closeness': all_metrics['closeness'].get(article, 0),
                'clustering': all_metrics['clustering'].get(article, 0),
                'degree': all_metrics['degree'].get(article, {})
            }

        output_file = self.root_dir / "network_metrics.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON метрики: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = AdvancedNetworkAnalyzer(root_dir)
    analyzer.build_network()

    print("📈 Вычисление метрик...\n")

    # Вычислить все метрики
    degree = analyzer.calculate_degree_centrality()
    print("   ✓ Degree centrality")

    pagerank = analyzer.calculate_pagerank()
    print("   ✓ PageRank")

    betweenness = analyzer.calculate_betweenness_centrality()
    print("   ✓ Betweenness centrality")

    closeness = analyzer.calculate_closeness_centrality()
    print("   ✓ Closeness centrality")

    clustering, global_clustering = analyzer.calculate_clustering_coefficient()
    print("   ✓ Clustering coefficient")

    graph_properties = analyzer.calculate_graph_properties()
    print("   ✓ Graph properties\n")

    # Собрать все метрики
    all_metrics = {
        'degree': degree,
        'pagerank': pagerank,
        'betweenness': betweenness,
        'closeness': closeness,
        'clustering': clustering,
        'global_clustering': global_clustering,
        'graph_properties': graph_properties
    }

    # Создать отчёты
    analyzer.generate_report(all_metrics)
    analyzer.save_json(all_metrics)


if __name__ == "__main__":
    main()
