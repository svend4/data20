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


class CentralityAnalyzer:
    """Расширенный анализ центральности"""

    def __init__(self, graph, undirected_graph, articles):
        self.graph = graph
        self.undirected_graph = undirected_graph
        self.articles = articles

    def calculate_eigenvector_centrality(self, max_iterations=100, tolerance=1e-6):
        """
        Вычислить eigenvector centrality

        Eigenvector centrality - мера влияния узла в сети.
        Узел имеет высокий eigenvector centrality, если связан с узлами,
        которые сами имеют высокий eigenvector centrality.

        Returns:
            dict: {article: eigenvector_score}
        """
        n = len(self.articles)
        centrality = {article: 1.0 / n for article in self.articles}

        for iteration in range(max_iterations):
            new_centrality = {}
            max_diff = 0

            for article in self.articles:
                # Сумма центральности соседей (входящие связи)
                score = 0.0
                for source in self.articles:
                    if article in self.graph[source]:
                        score += centrality[source]

                new_centrality[article] = score
                max_diff = max(max_diff, abs(new_centrality[article] - centrality[article]))

            # Нормализация (L2 norm)
            total = math.sqrt(sum(v * v for v in new_centrality.values()))
            if total > 0:
                new_centrality = {k: v / total for k, v in new_centrality.items()}

            centrality = new_centrality

            # Проверка сходимости
            if max_diff < tolerance:
                break

        return centrality

    def calculate_katz_centrality(self, alpha=0.1, beta=1.0, max_iterations=100):
        """
        Вычислить Katz centrality

        Katz centrality учитывает все пути в графе, взвешивая их по длине.
        Короткие пути имеют больший вес, чем длинные.

        Formula: C_katz(i) = Σ_k Σ_j α^k A^k_ji β
        где α - коэффициент затухания, β - базовая центральность

        Args:
            alpha: коэффициент затухания (должен быть < 1/λ_max)
            beta: базовая центральность каждого узла
            max_iterations: максимум итераций

        Returns:
            dict: {article: katz_score}
        """
        centrality = {article: beta for article in self.articles}

        for iteration in range(max_iterations):
            new_centrality = {}

            for article in self.articles:
                # Базовая центральность + вклад от соседей
                score = beta

                for source in self.articles:
                    if article in self.graph[source]:
                        score += alpha * centrality[source]

                new_centrality[article] = score

            centrality = new_centrality

        return centrality

    def calculate_harmonic_centrality(self):
        """
        Вычислить harmonic centrality

        Harmonic centrality - альтернатива closeness centrality,
        которая лучше работает для несвязных графов.

        Formula: H(i) = Σ_{j≠i} 1/d(i,j)
        где d(i,j) - расстояние между i и j

        Returns:
            dict: {article: harmonic_score}
        """
        harmonic = {}

        for article in self.articles:
            # BFS для поиска расстояний
            distances = {article: 0}
            queue = deque([article])

            while queue:
                node = queue.popleft()

                for neighbor in self.undirected_graph[node]:
                    if neighbor not in distances:
                        distances[neighbor] = distances[node] + 1
                        queue.append(neighbor)

            # Harmonic centrality = сумма 1/расстояние
            score = sum(1.0 / d for d in distances.values() if d > 0)
            harmonic[article] = score

        return harmonic

    def compare_centrality_measures(self, pagerank, betweenness, closeness):
        """
        Сравнить разные меры центральности

        Args:
            pagerank: dict результатов PageRank
            betweenness: dict результатов betweenness centrality
            closeness: dict результатов closeness centrality

        Returns:
            dict: статистика корреляции и различий
        """
        eigenvector = self.calculate_eigenvector_centrality()
        katz = self.calculate_katz_centrality()
        harmonic = self.calculate_harmonic_centrality()

        # Найти топ-10 для каждой меры
        measures = {
            'PageRank': pagerank,
            'Betweenness': betweenness,
            'Closeness': closeness,
            'Eigenvector': eigenvector,
            'Katz': katz,
            'Harmonic': harmonic
        }

        top_10 = {}
        for name, scores in measures.items():
            sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
            top_10[name] = {article for article, _ in sorted_scores[:10]}

        # Подсчитать пересечения топ-10
        overlaps = {}
        measure_names = list(measures.keys())

        for i, name1 in enumerate(measure_names):
            for name2 in measure_names[i+1:]:
                overlap = len(top_10[name1] & top_10[name2])
                overlaps[f"{name1} ∩ {name2}"] = overlap

        return {
            'measures': measures,
            'top_10': top_10,
            'overlaps': overlaps
        }


class CommunityDetector:
    """Продвинутое определение сообществ"""

    def __init__(self, graph, undirected_graph, articles):
        self.graph = graph
        self.undirected_graph = undirected_graph
        self.articles = articles

    def calculate_modularity(self, communities):
        """
        Вычислить modularity для заданного разбиения на сообщества

        Modularity Q ∈ [-1, 1] показывает качество разбиения.
        Q > 0.3 считается хорошим разбиением.

        Formula: Q = 1/(2m) Σ_ij [A_ij - k_i*k_j/(2m)] δ(c_i, c_j)
        где m - число рёбер, k_i - степень узла i, c_i - сообщество узла i

        Args:
            communities: list of sets (каждое сообщество - множество узлов)

        Returns:
            float: modularity score
        """
        # Создать mapping: узел -> сообщество
        node_to_community = {}
        for comm_id, community in enumerate(communities):
            for node in community:
                node_to_community[node] = comm_id

        # Количество рёбер (ненаправленный граф)
        m = sum(len(neighbors) for neighbors in self.undirected_graph.values()) / 2

        if m == 0:
            return 0.0

        modularity = 0.0

        for node_i in self.articles:
            for node_j in self.articles:
                # A_ij - есть ли ребро между i и j
                A_ij = 1 if node_j in self.undirected_graph[node_i] else 0

                # Степени узлов
                k_i = len(self.undirected_graph[node_i])
                k_j = len(self.undirected_graph[node_j])

                # δ(c_i, c_j) - в одном ли сообществе
                same_community = 1 if node_to_community[node_i] == node_to_community[node_j] else 0

                modularity += (A_ij - (k_i * k_j) / (2 * m)) * same_community

        return modularity / (2 * m)

    def louvain_method(self, max_iterations=100):
        """
        Метод Louvain для определения сообществ

        Жадный алгоритм оптимизации modularity.
        Работает в два этапа:
        1. Локальная оптимизация: каждый узел перемещается в сообщество,
           которое максимизирует modularity
        2. Агрегация: сообщества объединяются в супер-узлы

        Returns:
            list of sets: обнаруженные сообщества
        """
        # Инициализация: каждый узел - своё сообщество
        communities = {article: {article} for article in self.articles}
        node_to_community = {article: article for article in self.articles}

        improved = True
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for node in self.articles:
                current_comm = node_to_community[node]
                best_comm = current_comm
                best_delta = 0.0

                # Попробовать переместить узел в сообщество каждого соседа
                neighbor_communities = set()
                for neighbor in self.undirected_graph[node]:
                    neighbor_communities.add(node_to_community[neighbor])

                for test_comm in neighbor_communities:
                    if test_comm == current_comm:
                        continue

                    # Вычислить изменение modularity
                    delta = self._calculate_modularity_delta(
                        node, current_comm, test_comm, communities, node_to_community
                    )

                    if delta > best_delta:
                        best_delta = delta
                        best_comm = test_comm

                # Переместить узел в лучшее сообщество
                if best_comm != current_comm:
                    communities[current_comm].remove(node)
                    communities[best_comm].add(node)
                    node_to_community[node] = best_comm
                    improved = True

        # Вернуть только непустые сообщества
        final_communities = [comm for comm in communities.values() if comm]

        # Удалить дубликаты (одинаковые множества)
        unique_communities = []
        seen = set()

        for comm in final_communities:
            comm_tuple = tuple(sorted(comm))
            if comm_tuple not in seen:
                seen.add(comm_tuple)
                unique_communities.append(comm)

        return unique_communities

    def _calculate_modularity_delta(self, node, from_comm, to_comm, communities, node_to_community):
        """Вычислить изменение modularity при перемещении узла"""
        # Упрощённая эвристика на основе связей
        links_to_from = sum(1 for n in communities[from_comm] if n in self.undirected_graph[node])
        links_to_to = sum(1 for n in communities[to_comm] if n in self.undirected_graph[node])

        return links_to_to - links_to_from

    def label_propagation(self, max_iterations=100):
        """
        Label Propagation Algorithm для определения сообществ

        Простой и быстрый алгоритм:
        1. Каждому узлу присваивается уникальная метка
        2. Итеративно: каждый узел принимает метку большинства соседей
        3. Сходится, когда метки стабилизируются

        Returns:
            list of sets: обнаруженные сообщества
        """
        # Инициализация: каждый узел - своя метка
        labels = {article: i for i, article in enumerate(self.articles)}

        for iteration in range(max_iterations):
            changed = False

            # Перемешать порядок обработки узлов (важно для сходимости)
            nodes_list = list(self.articles)

            for node in nodes_list:
                # Подсчитать метки соседей
                neighbor_labels = defaultdict(int)

                for neighbor in self.undirected_graph[node]:
                    neighbor_labels[labels[neighbor]] += 1

                if not neighbor_labels:
                    continue

                # Выбрать самую частую метку
                most_common_label = max(neighbor_labels.items(), key=lambda x: x[1])[0]

                if labels[node] != most_common_label:
                    labels[node] = most_common_label
                    changed = True

            # Проверка сходимости
            if not changed:
                break

        # Преобразовать метки в сообщества
        communities_dict = defaultdict(set)
        for node, label in labels.items():
            communities_dict[label].add(node)

        return list(communities_dict.values())

    def analyze_communities(self, communities, article_titles):
        """
        Анализ обнаруженных сообществ

        Args:
            communities: list of sets
            article_titles: dict {article: title}

        Returns:
            dict: статистика сообществ
        """
        analysis = {
            'num_communities': len(communities),
            'modularity': self.calculate_modularity(communities),
            'communities': []
        }

        for i, community in enumerate(sorted(communities, key=len, reverse=True)):
            # Внутренние и внешние связи
            internal_edges = 0
            external_edges = 0

            for node in community:
                for neighbor in self.undirected_graph[node]:
                    if neighbor in community:
                        internal_edges += 1
                    else:
                        external_edges += 1

            internal_edges //= 2  # Каждое ребро посчитано дважды

            # Плотность сообщества
            n = len(community)
            max_edges = n * (n - 1) // 2
            density = internal_edges / max_edges if max_edges > 0 else 0.0

            community_info = {
                'id': i + 1,
                'size': n,
                'internal_edges': internal_edges,
                'external_edges': external_edges,
                'density': density,
                'members': [article_titles.get(article, Path(article).stem) for article in list(community)[:10]]
            }

            analysis['communities'].append(community_info)

        return analysis


class PathAnalyzer:
    """Анализ путей в графе"""

    def __init__(self, graph, undirected_graph, articles):
        self.graph = graph
        self.undirected_graph = undirected_graph
        self.articles = articles

    def find_shortest_path(self, source, target):
        """
        Найти кратчайший путь между двумя узлами (BFS)

        Args:
            source: исходный узел
            target: целевой узел

        Returns:
            list: путь [source, ..., target] или None если пути нет
        """
        if source not in self.articles or target not in self.articles:
            return None

        if source == target:
            return [source]

        # BFS с отслеживанием родителей
        visited = {source}
        queue = deque([(source, [source])])

        while queue:
            node, path = queue.popleft()

            for neighbor in self.undirected_graph[node]:
                if neighbor == target:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None  # Путь не найден

    def find_all_paths(self, source, target, max_length=5):
        """
        Найти все простые пути между двумя узлами (DFS)

        Args:
            source: исходный узел
            target: целевой узел
            max_length: максимальная длина пути

        Returns:
            list of lists: все найденные пути
        """
        if source not in self.articles or target not in self.articles:
            return []

        all_paths = []

        def dfs(node, path):
            if len(path) > max_length:
                return

            if node == target:
                all_paths.append(path[:])
                return

            for neighbor in self.undirected_graph[node]:
                if neighbor not in path:
                    path.append(neighbor)
                    dfs(neighbor, path)
                    path.pop()

        dfs(source, [source])
        return all_paths

    def find_bottlenecks(self, betweenness_centrality, threshold=0.1):
        """
        Найти узлы-bottlenecks (узкие места) в сети

        Bottleneck - узел, через который проходит много кратчайших путей.
        Удаление такого узла сильно увеличивает среднюю длину пути.

        Args:
            betweenness_centrality: dict результатов betweenness centrality
            threshold: порог для определения bottleneck

        Returns:
            list: узлы-bottlenecks с их метриками
        """
        bottlenecks = []

        for article, bc_score in betweenness_centrality.items():
            if bc_score >= threshold:
                # Вычислить impact: насколько изменится сеть при удалении узла
                impact = self._calculate_removal_impact(article)

                bottlenecks.append({
                    'article': article,
                    'betweenness': bc_score,
                    'impact': impact
                })

        # Сортировать по betweenness
        bottlenecks.sort(key=lambda x: -x['betweenness'])

        return bottlenecks

    def _calculate_removal_impact(self, node):
        """Вычислить impact от удаления узла"""
        # Подсчитать пары узлов, которые потеряют связность
        disconnected_pairs = 0

        # Простая эвристика: посчитать степень узла
        degree = len(self.undirected_graph[node])

        # Impact ~ количество потенциально разорванных путей
        # Для точного расчёта нужно пересчитывать все кратчайшие пути
        return degree * degree  # Приблизительная оценка

    def find_critical_paths(self, top_n=10):
        """
        Найти критические пути в сети

        Критический путь - путь между важными узлами (high PageRank),
        который проходит через bottleneck узлы.

        Args:
            top_n: количество путей для анализа

        Returns:
            list: критические пути с их метриками
        """
        # Найти узлы с высокой степенью (hubs)
        hubs = sorted(
            self.articles,
            key=lambda a: len(self.undirected_graph[a]),
            reverse=True
        )[:10]

        critical_paths = []

        # Найти пути между всеми парами hubs
        for i, hub1 in enumerate(hubs):
            for hub2 in hubs[i+1:]:
                path = self.find_shortest_path(hub1, hub2)

                if path and len(path) > 2:
                    # Вычислить "критичность" пути
                    path_length = len(path)
                    intermediate_nodes = path[1:-1]
                    avg_degree = sum(len(self.undirected_graph[n]) for n in intermediate_nodes) / len(intermediate_nodes)

                    critical_paths.append({
                        'path': path,
                        'length': path_length,
                        'avg_intermediate_degree': avg_degree
                    })

        # Сортировать по комбинации длины и степени промежуточных узлов
        critical_paths.sort(key=lambda x: x['avg_intermediate_degree'])

        return critical_paths[:top_n]

    def calculate_path_diversity(self, source, target):
        """
        Вычислить разнообразие путей между двумя узлами

        Args:
            source: исходный узел
            target: целевой узел

        Returns:
            dict: метрики разнообразия путей
        """
        all_paths = self.find_all_paths(source, target, max_length=6)

        if not all_paths:
            return {
                'num_paths': 0,
                'shortest_length': None,
                'longest_length': None,
                'avg_length': None,
                'unique_nodes': 0
            }

        lengths = [len(path) for path in all_paths]
        unique_nodes = set()
        for path in all_paths:
            unique_nodes.update(path)

        return {
            'num_paths': len(all_paths),
            'shortest_length': min(lengths),
            'longest_length': max(lengths),
            'avg_length': sum(lengths) / len(lengths),
            'unique_nodes': len(unique_nodes)
        }


class NetworkVisualizer:
    """Визуализация сети"""

    def __init__(self, graph, undirected_graph, articles, article_titles):
        self.graph = graph
        self.undirected_graph = undirected_graph
        self.articles = articles
        self.article_titles = article_titles

    def generate_html_graph(self, pagerank=None, communities=None):
        """
        Создать интерактивный HTML граф с D3.js

        Args:
            pagerank: dict результатов PageRank (для размера узлов)
            communities: list of sets (для цвета узлов)

        Returns:
            str: путь к созданному HTML файлу
        """
        # Подготовить данные для D3.js
        nodes = []
        node_to_community = {}

        # Определить принадлежность к сообществам
        if communities:
            for comm_id, community in enumerate(communities):
                for node in community:
                    node_to_community[node] = comm_id

        for article in self.articles:
            title = self.article_titles.get(article, Path(article).stem)
            pr_score = pagerank.get(article, 0) if pagerank else 0

            nodes.append({
                'id': article,
                'title': title,
                'pagerank': pr_score,
                'community': node_to_community.get(article, 0),
                'degree': len(self.undirected_graph[article])
            })

        # Подготовить рёбра
        links = []
        seen_pairs = set()

        for source in self.articles:
            for target in self.graph[source]:
                if target in self.articles:
                    # Избегать дублирования (A->B и B->A)
                    pair = tuple(sorted([source, target]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        links.append({
                            'source': source,
                            'target': target
                        })

        # Создать HTML с D3.js
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Интерактивная сеть знаний</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .controls {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}

        .controls label {{
            margin-right: 10px;
            font-weight: 600;
        }}

        .controls input, .controls select {{
            margin-right: 20px;
            padding: 5px 10px;
            border: 2px solid #667eea;
            border-radius: 5px;
        }}

        #graph {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .node {{
            cursor: pointer;
            stroke: white;
            stroke-width: 2px;
        }}

        .node:hover {{
            stroke: #667eea;
            stroke-width: 3px;
        }}

        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 1px;
        }}

        .node-label {{
            font-size: 12px;
            pointer-events: none;
            text-shadow: 0 1px 2px white, 1px 0 2px white, -1px 0 2px white, 0 -1px 2px white;
        }}

        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            display: none;
            font-size: 14px;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🕸️ Интерактивная сеть знаний</h1>

        <div class="controls">
            <label>Поиск:</label>
            <input type="text" id="search" placeholder="Введите название статьи...">

            <label>Показывать метки:</label>
            <input type="checkbox" id="showLabels" checked>

            <label>Сила притяжения:</label>
            <input type="range" id="chargeStrength" min="-500" max="-50" value="-200" step="10">

            <label>Расстояние связей:</label>
            <input type="range" id="linkDistance" min="30" max="200" value="100" step="10">
        </div>

        <div id="graph"></div>
        <div class="tooltip" id="tooltip"></div>
    </div>

    <script>
        // Данные
        const nodes = {json.dumps(nodes, ensure_ascii=False)};
        const links = {json.dumps(links, ensure_ascii=False)};

        // Размеры
        const width = 1400;
        const height = 800;

        // Цветовая палитра для сообществ
        const color = d3.scaleOrdinal(d3.schemeCategory10);

        // SVG
        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .call(d3.zoom().on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }}));

        const g = svg.append('g');

        // Tooltip
        const tooltip = d3.select('#tooltip');

        // Сила симуляции
        let chargeStrength = -200;
        let linkDistance = 100;

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(linkDistance))
            .force('charge', d3.forceManyBody().strength(chargeStrength))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.pagerank * 50000) + 5));

        // Линии (связи)
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .join('line')
            .attr('class', 'link');

        // Узлы
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .join('circle')
            .attr('class', 'node')
            .attr('r', d => Math.max(5, Math.sqrt(d.pagerank * 50000)))
            .attr('fill', d => color(d.community))
            .call(drag(simulation))
            .on('mouseover', (event, d) => {{
                tooltip
                    .style('display', 'block')
                    .html(`
                        <strong>${{d.title}}</strong><br>
                        PageRank: ${{d.pagerank.toFixed(6)}}<br>
                        Степень: ${{d.degree}}<br>
                        Сообщество: ${{d.community + 1}}
                    `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
            }})
            .on('mouseout', () => {{
                tooltip.style('display', 'none');
            }});

        // Метки
        const labels = g.append('g')
            .selectAll('text')
            .data(nodes)
            .join('text')
            .attr('class', 'node-label')
            .text(d => d.title.length > 30 ? d.title.substring(0, 30) + '...' : d.title)
            .attr('text-anchor', 'middle')
            .attr('dy', -10);

        // Обновление позиций
        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }});

        // Drag & drop
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
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended);
        }}

        // Поиск
        d3.select('#search').on('input', function() {{
            const searchTerm = this.value.toLowerCase();

            node.attr('opacity', d => {{
                if (searchTerm === '' || d.title.toLowerCase().includes(searchTerm)) {{
                    return 1;
                }} else {{
                    return 0.2;
                }}
            }});

            labels.attr('opacity', d => {{
                if (searchTerm === '' || d.title.toLowerCase().includes(searchTerm)) {{
                    return 1;
                }} else {{
                    return 0.2;
                }}
            }});
        }});

        // Показывать/скрывать метки
        d3.select('#showLabels').on('change', function() {{
            labels.attr('display', this.checked ? 'block' : 'none');
        }});

        // Сила притяжения
        d3.select('#chargeStrength').on('input', function() {{
            chargeStrength = +this.value;
            simulation.force('charge', d3.forceManyBody().strength(chargeStrength));
            simulation.alpha(0.3).restart();
        }});

        // Расстояние связей
        d3.select('#linkDistance').on('input', function() {{
            linkDistance = +this.value;
            simulation.force('link', d3.forceLink(links).id(d => d.id).distance(linkDistance));
            simulation.alpha(0.3).restart();
        }});
    </script>
</body>
</html>"""

        return html

    def generate_graphml(self, output_file):
        """
        Экспортировать граф в формат GraphML (для Gephi, Cytoscape)

        GraphML - стандартный XML формат для графов.

        Args:
            output_file: путь к выходному файлу

        Returns:
            str: путь к созданному файлу
        """
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
        lines.append('  <key id="title" for="node" attr.name="title" attr.type="string"/>')
        lines.append('  <key id="degree" for="node" attr.name="degree" attr.type="int"/>')
        lines.append('  <graph id="G" edgedefault="directed">')

        # Узлы
        for article in self.articles:
            title = self.article_titles.get(article, Path(article).stem)
            degree = len(self.undirected_graph[article])

            # Экранировать XML
            title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            article_escaped = article.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            lines.append(f'    <node id="{article_escaped}">')
            lines.append(f'      <data key="title">{title_escaped}</data>')
            lines.append(f'      <data key="degree">{degree}</data>')
            lines.append('    </node>')

        # Рёбра
        edge_id = 0
        for source in self.articles:
            for target in self.graph[source]:
                if target in self.articles:
                    source_escaped = source.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    target_escaped = target.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                    lines.append(f'    <edge id="e{edge_id}" source="{source_escaped}" target="{target_escaped}"/>')
                    edge_id += 1

        lines.append('  </graph>')
        lines.append('</graphml>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return str(output_file)

    def generate_gexf(self, output_file):
        """
        Экспортировать граф в формат GEXF (для Gephi)

        GEXF - Graph Exchange XML Format, оптимизированный для Gephi.

        Args:
            output_file: путь к выходному файлу

        Returns:
            str: путь к созданному файлу
        """
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
        lines.append('  <meta>')
        lines.append('    <creator>Network Analyzer</creator>')
        lines.append('    <description>Knowledge Graph Export</description>')
        lines.append('  </meta>')
        lines.append('  <graph mode="static" defaultedgetype="directed">')
        lines.append('    <attributes class="node">')
        lines.append('      <attribute id="0" title="title" type="string"/>')
        lines.append('      <attribute id="1" title="degree" type="integer"/>')
        lines.append('    </attributes>')

        # Узлы
        lines.append('    <nodes>')
        for i, article in enumerate(self.articles):
            title = self.article_titles.get(article, Path(article).stem)
            degree = len(self.undirected_graph[article])

            title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            lines.append(f'      <node id="{i}" label="{title_escaped}">')
            lines.append('        <attvalues>')
            lines.append(f'          <attvalue for="0" value="{title_escaped}"/>')
            lines.append(f'          <attvalue for="1" value="{degree}"/>')
            lines.append('        </attvalues>')
            lines.append('      </node>')

        lines.append('    </nodes>')

        # Рёбра
        lines.append('    <edges>')
        article_to_id = {article: i for i, article in enumerate(self.articles)}
        edge_id = 0

        for source in self.articles:
            for target in self.graph[source]:
                if target in self.articles:
                    source_id = article_to_id[source]
                    target_id = article_to_id[target]

                    lines.append(f'      <edge id="{edge_id}" source="{source_id}" target="{target_id}"/>')
                    edge_id += 1

        lines.append('    </edges>')
        lines.append('  </graph>')
        lines.append('</gexf>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return str(output_file)


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
    import argparse

    parser = argparse.ArgumentParser(
        description='📊 Продвинутый анализ сети',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:

  # Базовый анализ (Markdown + JSON)
  %(prog)s

  # Интерактивная HTML визуализация
  %(prog)s --html

  # Расширенный анализ центральности
  %(prog)s --centrality

  # Определение сообществ (Louvain)
  %(prog)s --communities

  # Анализ путей и bottlenecks
  %(prog)s --paths

  # Экспорт в GraphML (для Gephi)
  %(prog)s --graphml

  # Экспорт в GEXF (для Gephi)
  %(prog)s --gexf

  # Полный анализ (все метрики + HTML)
  %(prog)s --all

  # Поиск пути между двумя статьями
  %(prog)s --find-path "knowledge/foo.md" "knowledge/bar.md"

  # Сравнение мер центральности
  %(prog)s --compare-centrality

Вдохновлено: NetworkX, Gephi, igraph, Neo4j
        '''
    )

    parser.add_argument('--html', action='store_true',
                        help='Создать интерактивную HTML визуализацию с D3.js')
    parser.add_argument('--centrality', action='store_true',
                        help='Расширенный анализ центральности (eigenvector, Katz, harmonic)')
    parser.add_argument('--communities', action='store_true',
                        help='Определение сообществ (Louvain method)')
    parser.add_argument('--paths', action='store_true',
                        help='Анализ путей и bottlenecks')
    parser.add_argument('--graphml', action='store_true',
                        help='Экспортировать в формат GraphML')
    parser.add_argument('--gexf', action='store_true',
                        help='Экспортировать в формат GEXF')
    parser.add_argument('--compare-centrality', action='store_true',
                        help='Сравнить разные меры центральности')
    parser.add_argument('--find-path', nargs=2, metavar=('SOURCE', 'TARGET'),
                        help='Найти кратчайший путь между двумя статьями')
    parser.add_argument('--all', action='store_true',
                        help='Выполнить полный анализ (все опции)')
    parser.add_argument('--json', action='store_true',
                        help='Сохранить JSON метрики')

    args = parser.parse_args()

    # --all включает все опции
    if args.all:
        args.html = True
        args.centrality = True
        args.communities = True
        args.paths = True
        args.graphml = True
        args.gexf = True
        args.compare_centrality = True
        args.json = True

    # Если нет опций, показать базовый анализ
    if not any([args.html, args.centrality, args.communities, args.paths,
                args.graphml, args.gexf, args.compare_centrality, args.find_path,
                args.json]):
        args.json = True

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = AdvancedNetworkAnalyzer(root_dir)
    analyzer.build_network()

    print("📈 Вычисление базовых метрик...\n")

    # Вычислить базовые метрики
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

    # Собрать базовые метрики
    all_metrics = {
        'degree': degree,
        'pagerank': pagerank,
        'betweenness': betweenness,
        'closeness': closeness,
        'clustering': clustering,
        'global_clustering': global_clustering,
        'graph_properties': graph_properties
    }

    # Создать базовый отчёт
    analyzer.generate_report(all_metrics)

    # JSON экспорт
    if args.json:
        analyzer.save_json(all_metrics)

    # Расширенный анализ центральности
    if args.centrality or args.compare_centrality:
        print("🎯 Расширенный анализ центральности...\n")

        centrality_analyzer = CentralityAnalyzer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles
        )

        eigenvector = centrality_analyzer.calculate_eigenvector_centrality()
        print("   ✓ Eigenvector centrality")

        katz = centrality_analyzer.calculate_katz_centrality()
        print("   ✓ Katz centrality")

        harmonic = centrality_analyzer.calculate_harmonic_centrality()
        print("   ✓ Harmonic centrality\n")

        # Сохранить топ-10 по каждой мере
        centrality_report = []
        centrality_report.append("# 🎯 Расширенный анализ центральности\n\n")

        # Eigenvector
        centrality_report.append("## Eigenvector Centrality\n\n")
        centrality_report.append("> Мера влияния узла: связь с влиятельными узлами\n\n")
        sorted_eig = sorted(eigenvector.items(), key=lambda x: -x[1])
        for article, score in sorted_eig[:10]:
            title = analyzer.article_titles.get(article, Path(article).stem)
            centrality_report.append(f"1. **{title}**: {score:.6f}\n")

        # Katz
        centrality_report.append("\n## Katz Centrality\n\n")
        centrality_report.append("> Учитывает все пути в графе, взвешивая их по длине\n\n")
        sorted_katz = sorted(katz.items(), key=lambda x: -x[1])
        for article, score in sorted_katz[:10]:
            title = analyzer.article_titles.get(article, Path(article).stem)
            centrality_report.append(f"1. **{title}**: {score:.4f}\n")

        # Harmonic
        centrality_report.append("\n## Harmonic Centrality\n\n")
        centrality_report.append("> Альтернатива closeness, лучше работает для несвязных графов\n\n")
        sorted_harm = sorted(harmonic.items(), key=lambda x: -x[1])
        for article, score in sorted_harm[:10]:
            title = analyzer.article_titles.get(article, Path(article).stem)
            centrality_report.append(f"1. **{title}**: {score:.2f}\n")

        output_file = root_dir / "CENTRALITY_ANALYSIS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(centrality_report)
        print(f"✅ Анализ центральности: {output_file}")

    # Сравнение мер центральности
    if args.compare_centrality:
        print("\n🔄 Сравнение мер центральности...\n")

        centrality_analyzer = CentralityAnalyzer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles
        )

        comparison = centrality_analyzer.compare_centrality_measures(
            pagerank, betweenness, closeness
        )

        # Сохранить сравнение
        comparison_report = []
        comparison_report.append("# 🔄 Сравнение мер центральности\n\n")
        comparison_report.append("## Пересечения топ-10\n\n")
        comparison_report.append("> Сколько статей входят в топ-10 по обеим мерам\n\n")

        for pair, overlap in sorted(comparison['overlaps'].items(), key=lambda x: -x[1]):
            comparison_report.append(f"- **{pair}**: {overlap}/10 статей\n")

        output_file = root_dir / "CENTRALITY_COMPARISON.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(comparison_report)
        print(f"✅ Сравнение центральности: {output_file}\n")

    # Определение сообществ
    if args.communities:
        print("👥 Определение сообществ...\n")

        community_detector = CommunityDetector(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles
        )

        communities_louvain = community_detector.louvain_method()
        print(f"   ✓ Louvain method: {len(communities_louvain)} сообществ")

        communities_label = community_detector.label_propagation()
        print(f"   ✓ Label propagation: {len(communities_label)} сообществ\n")

        # Анализ сообществ Louvain
        analysis = community_detector.analyze_communities(
            communities_louvain,
            analyzer.article_titles
        )

        # Сохранить отчёт
        community_report = []
        community_report.append("# 👥 Анализ сообществ\n\n")
        community_report.append(f"**Количество сообществ**: {analysis['num_communities']}\n\n")
        community_report.append(f"**Modularity**: {analysis['modularity']:.4f}\n\n")
        community_report.append("> Modularity > 0.3 считается хорошим разбиением\n\n")

        community_report.append("## Топ-10 сообществ\n\n")

        for comm in analysis['communities'][:10]:
            community_report.append(f"### Сообщество {comm['id']}\n\n")
            community_report.append(f"- **Размер**: {comm['size']} статей\n")
            community_report.append(f"- **Внутренние связи**: {comm['internal_edges']}\n")
            community_report.append(f"- **Внешние связи**: {comm['external_edges']}\n")
            community_report.append(f"- **Плотность**: {comm['density']:.4f}\n\n")

            if comm['members']:
                community_report.append("**Члены сообщества** (до 10):\n\n")
                for member in comm['members']:
                    community_report.append(f"- {member}\n")
                community_report.append("\n")

        output_file = root_dir / "COMMUNITY_ANALYSIS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(community_report)
        print(f"✅ Анализ сообществ: {output_file}")

        # Сохранить для HTML визуализации
        communities_for_html = communities_louvain

    # Анализ путей
    if args.paths:
        print("\n🛤️  Анализ путей и bottlenecks...\n")

        path_analyzer = PathAnalyzer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles
        )

        bottlenecks = path_analyzer.find_bottlenecks(betweenness, threshold=0.01)
        print(f"   ✓ Найдено {len(bottlenecks)} bottlenecks")

        critical_paths = path_analyzer.find_critical_paths(top_n=10)
        print(f"   ✓ Найдено {len(critical_paths)} критических путей\n")

        # Сохранить отчёт
        path_report = []
        path_report.append("# 🛤️  Анализ путей\n\n")

        path_report.append("## Узлы-Bottlenecks\n\n")
        path_report.append("> Узлы, через которые проходит много кратчайших путей\n\n")

        for bn in bottlenecks[:10]:
            title = analyzer.article_titles.get(bn['article'], Path(bn['article']).stem)
            path_report.append(f"1. **{title}**\n")
            path_report.append(f"   - Betweenness: {bn['betweenness']:.6f}\n")
            path_report.append(f"   - Impact: {bn['impact']}\n")

        path_report.append("\n## Критические пути\n\n")
        path_report.append("> Пути между важными узлами (hubs)\n\n")

        for i, cp in enumerate(critical_paths, 1):
            path_report.append(f"### Путь {i}\n\n")
            path_report.append(f"- **Длина**: {cp['length']}\n")
            path_report.append(f"- **Средняя степень промежуточных узлов**: {cp['avg_intermediate_degree']:.2f}\n\n")

            path_report.append("**Маршрут**:\n\n")
            for node in cp['path']:
                title = analyzer.article_titles.get(node, Path(node).stem)
                path_report.append(f"→ {title}\n")
            path_report.append("\n")

        output_file = root_dir / "PATH_ANALYSIS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(path_report)
        print(f"✅ Анализ путей: {output_file}")

    # Поиск пути между двумя статьями
    if args.find_path:
        source, target = args.find_path

        path_analyzer = PathAnalyzer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles
        )

        path = path_analyzer.find_shortest_path(source, target)

        if path:
            print(f"\n🔍 Кратчайший путь найден ({len(path)} шагов):\n")
            for node in path:
                title = analyzer.article_titles.get(node, Path(node).stem)
                print(f"   → {title}")

            # Разнообразие путей
            diversity = path_analyzer.calculate_path_diversity(source, target)
            print(f"\n📊 Разнообразие путей:")
            print(f"   Всего путей: {diversity['num_paths']}")
            if diversity['num_paths'] > 0:
                print(f"   Кратчайший: {diversity['shortest_length']} шагов")
                print(f"   Длиннейший: {diversity['longest_length']} шагов")
                print(f"   Средняя длина: {diversity['avg_length']:.2f} шагов")
                print(f"   Уникальных узлов: {diversity['unique_nodes']}")
        else:
            print(f"\n❌ Путь не найден между {source} и {target}")

    # GraphML экспорт
    if args.graphml:
        print("\n📦 Экспорт в GraphML...\n")

        visualizer = NetworkVisualizer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles,
            analyzer.article_titles
        )

        output_file = root_dir / "network.graphml"
        visualizer.generate_graphml(output_file)
        print(f"✅ GraphML: {output_file}")

    # GEXF экспорт
    if args.gexf:
        print("\n📦 Экспорт в GEXF...\n")

        visualizer = NetworkVisualizer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles,
            analyzer.article_titles
        )

        output_file = root_dir / "network.gexf"
        visualizer.generate_gexf(output_file)
        print(f"✅ GEXF: {output_file}")

    # HTML визуализация
    if args.html:
        print("\n🎨 Создание интерактивной визуализации...\n")

        # Определить сообщества если ещё не определены
        if not args.communities:
            community_detector = CommunityDetector(
                analyzer.graph,
                analyzer.undirected_graph,
                analyzer.articles
            )
            communities_for_html = community_detector.louvain_method()
        else:
            communities_for_html = communities_louvain

        visualizer = NetworkVisualizer(
            analyzer.graph,
            analyzer.undirected_graph,
            analyzer.articles,
            analyzer.article_titles
        )

        html_content = visualizer.generate_html_graph(
            pagerank=pagerank,
            communities=communities_for_html
        )

        output_file = root_dir / "network_graph.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Интерактивная визуализация: {output_file}")
        print(f"   Откройте {output_file} в браузере")

    print("\n✨ Анализ завершён!")


if __name__ == "__main__":
    main()
