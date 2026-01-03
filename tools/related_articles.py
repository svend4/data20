#!/usr/bin/env python3
"""
Related Articles - Рекомендации статей
Умная система рекомендаций на основе контента, тегов и связей

Вдохновлено: рекомендательными системами Amazon, YouTube
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import math
import argparse
from typing import Dict, List, Tuple, Set


class TFIDFAnalyzer:
    """
    Enhanced TF-IDF analysis
    - Detailed TF-IDF scoring with explanations
    - Top-N recommendations with reasoning
    - Similarity matrix generation
    - Keyword importance ranking
    """

    def __init__(self, engine):
        self.engine = engine

    def calculate_tfidf_detailed(self, article_path: str) -> Dict[str, float]:
        """Вычислить TF-IDF для всех слов в статье с детализацией"""
        if article_path not in self.engine.word_counts:
            return {}

        words = self.engine.word_counts[article_path]
        total_docs = len(self.engine.articles)

        tfidf_scores = {}

        for word, count in words.items():
            tf = count
            idf = math.log(total_docs / (1 + self.engine.document_freq[word]))
            tfidf = tf * idf
            tfidf_scores[word] = tfidf

        return tfidf_scores

    def get_top_keywords(self, article_path: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Получить топ-N ключевых слов по TF-IDF"""
        tfidf_scores = self.calculate_tfidf_detailed(article_path)

        sorted_words = sorted(tfidf_scores.items(), key=lambda x: -x[1])
        return sorted_words[:top_n]

    def explain_similarity(self, article1: str, article2: str) -> Dict:
        """Объяснить почему две статьи похожи"""
        explanation = {
            'content_similarity': 0.0,
            'tag_similarity': 0.0,
            'link_score': 0.0,
            'category_match': False,
            'subcategory_match': False,
            'common_keywords': [],
            'common_tags': [],
            'link_relationship': []
        }

        # Content similarity (TF-IDF)
        explanation['content_similarity'] = self.engine.calculate_tf_idf_similarity(article1, article2)

        # Tag similarity
        explanation['tag_similarity'] = self.engine.calculate_tag_similarity(article1, article2)

        # Link score
        explanation['link_score'] = self.engine.calculate_link_score(article1, article2)

        # Category/subcategory
        if self.engine.articles[article1]['category'] == self.engine.articles[article2]['category']:
            explanation['category_match'] = True

        if (self.engine.articles[article1]['subcategory'] and
            self.engine.articles[article1]['subcategory'] == self.engine.articles[article2]['subcategory']):
            explanation['subcategory_match'] = True

        # Common keywords (top TF-IDF words)
        keywords1 = set(word for word, score in self.get_top_keywords(article1, 20))
        keywords2 = set(word for word, score in self.get_top_keywords(article2, 20))
        common = keywords1 & keywords2
        explanation['common_keywords'] = list(common)[:10]

        # Common tags
        tags1 = set(self.engine.articles[article1]['tags'])
        tags2 = set(self.engine.articles[article2]['tags'])
        explanation['common_tags'] = list(tags1 & tags2)

        # Link relationship
        if article2 in self.engine.links[article1]['outgoing']:
            explanation['link_relationship'].append(f"{article1} ссылается на {article2}")
        if article2 in self.engine.links[article1]['incoming']:
            explanation['link_relationship'].append(f"{article2} ссылается на {article1}")

        return explanation

    def generate_similarity_matrix(self) -> Dict[str, Dict[str, float]]:
        """Сгенерировать матрицу сходства между всеми статьями"""
        matrix = defaultdict(dict)

        articles = list(self.engine.articles.keys())

        for i, article1 in enumerate(articles):
            for article2 in articles[i+1:]:
                similarity = self.engine.calculate_similarity(article1, article2)
                matrix[article1][article2] = similarity
                matrix[article2][article1] = similarity

        return dict(matrix)


class SemanticAnalyzer:
    """
    Semantic analysis of articles
    - Topic extraction (key themes)
    - Keyword co-occurrence analysis
    - Semantic clusters (groups of similar articles)
    - Topic evolution tracking
    """

    def __init__(self, engine):
        self.engine = engine

    def extract_topics(self, article_path: str, top_n: int = 5) -> List[str]:
        """Извлечь ключевые темы из статьи"""
        if article_path not in self.engine.word_counts:
            return []

        # Используем TF-IDF для поиска важных слов
        analyzer = TFIDFAnalyzer(self.engine)
        keywords = analyzer.get_top_keywords(article_path, top_n)

        return [word for word, score in keywords]

    def analyze_keyword_cooccurrence(self, min_cooccurrence: int = 3) -> Dict[Tuple[str, str], int]:
        """Анализ совместной встречаемости ключевых слов"""
        cooccurrence = defaultdict(int)

        # Для каждой статьи найти пары ключевых слов
        for article_path in self.engine.articles:
            topics = self.extract_topics(article_path, 10)

            # Все пары слов
            for i, word1 in enumerate(topics):
                for word2 in topics[i+1:]:
                    pair = tuple(sorted([word1, word2]))
                    cooccurrence[pair] += 1

        # Фильтровать по минимальной частоте
        filtered = {pair: count for pair, count in cooccurrence.items()
                   if count >= min_cooccurrence}

        return dict(filtered)

    def find_semantic_clusters(self, similarity_threshold: float = 0.3) -> List[List[str]]:
        """Найти кластеры семантически похожих статей"""
        clusters = []
        visited = set()

        for article in self.engine.articles:
            if article in visited:
                continue

            # Начать новый кластер
            cluster = [article]
            visited.add(article)

            # Найти все похожие статьи
            for other_article in self.engine.articles:
                if other_article in visited:
                    continue

                similarity = self.engine.calculate_similarity(article, other_article)

                if similarity >= similarity_threshold:
                    cluster.append(other_article)
                    visited.add(other_article)

            # Сохранить кластер если в нём >1 статьи
            if len(cluster) > 1:
                clusters.append(cluster)

        # Сортировать кластеры по размеру
        clusters.sort(key=len, reverse=True)

        return clusters

    def get_cluster_topics(self, cluster: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
        """Получить основные темы кластера"""
        word_freq = Counter()

        for article in cluster:
            topics = self.extract_topics(article, 10)
            word_freq.update(topics)

        return word_freq.most_common(top_n)


class ReadingPatternAnalyzer:
    """
    Reading pattern analysis and collaborative filtering
    - "Users who read X also read Y" simulation
    - Reading path analysis
    - Personalized recommendations based on reading history
    - Surprise factor (unexpected but relevant)
    """

    def __init__(self, engine):
        self.engine = engine

    def simulate_reading_patterns(self) -> Dict[str, List[str]]:
        """Симулировать паттерны чтения на основе ссылок"""
        patterns = defaultdict(list)

        # Если пользователь читает A, и A ссылается на B,
        # то вероятно он прочитает и B
        for article_path in self.engine.articles:
            outgoing = self.engine.links[article_path]['outgoing']

            # Статьи которые читают вместе
            co_read = []

            # Прямые ссылки
            co_read.extend(outgoing)

            # Статьи из той же категории
            category = self.engine.articles[article_path]['category']
            for other_article, data in self.engine.articles.items():
                if other_article != article_path and data['category'] == category:
                    co_read.append(other_article)

            patterns[article_path] = co_read

        return dict(patterns)

    def get_collaborative_recommendations(self, article_path: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Collaborative filtering рекомендации"""
        if article_path not in self.engine.articles:
            return []

        # Найти "похожих пользователей" (статьи той же категории/подкатегории)
        similar_articles = []

        category = self.engine.articles[article_path]['category']
        subcategory = self.engine.articles[article_path].get('subcategory', '')

        for other_article, data in self.engine.articles.items():
            if other_article == article_path:
                continue

            # Та же подкатегория (высокая релевантность)
            if subcategory and data.get('subcategory') == subcategory:
                similar_articles.append((other_article, 2.0))
            # Та же категория (средняя релевантность)
            elif data['category'] == category:
                similar_articles.append((other_article, 1.0))

        # Сортировать по релевантности
        similar_articles.sort(key=lambda x: -x[1])

        return similar_articles[:limit]

    def calculate_surprise_factor(self, article1: str, article2: str) -> float:
        """Вычислить фактор неожиданности (unexpectedness)"""
        # Статьи из разных категорий но похожие по контенту = высокий surprise

        cat1 = self.engine.articles[article1]['category']
        cat2 = self.engine.articles[article2]['category']

        # Разные категории
        if cat1 != cat2:
            # Но высокое сходство контента
            content_sim = self.engine.calculate_tf_idf_similarity(article1, article2)

            if content_sim > 0.3:
                return content_sim * 2.0  # Бонус за неожиданность

        return 0.0

    def get_surprise_recommendations(self, article_path: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Рекомендации с фактором неожиданности"""
        recommendations = []

        for other_article in self.engine.articles:
            if other_article == article_path:
                continue

            surprise = self.calculate_surprise_factor(article_path, other_article)

            if surprise > 0:
                recommendations.append((other_article, surprise))

        recommendations.sort(key=lambda x: -x[1])
        return recommendations[:limit]


class RelationshipGraphBuilder:
    """
    Build and visualize relationship graph
    - Build similarity graph (edges = similarity score)
    - Find communities of related articles
    - Detect article clusters
    - Export for graph visualization tools
    - HTML interactive graph view
    """

    def __init__(self, engine):
        self.engine = engine

    def build_graph(self, min_similarity: float = 0.2) -> Dict[str, List[Tuple[str, float]]]:
        """Построить граф связей"""
        graph = defaultdict(list)

        articles = list(self.engine.articles.keys())

        for i, article1 in enumerate(articles):
            for article2 in articles[i+1:]:
                similarity = self.engine.calculate_similarity(article1, article2)

                if similarity >= min_similarity:
                    graph[article1].append((article2, similarity))
                    graph[article2].append((article1, similarity))

        return dict(graph)

    def find_communities(self, graph: Dict[str, List[Tuple[str, float]]]) -> List[Set[str]]:
        """Найти сообщества статей (простой алгоритм)"""
        communities = []
        visited = set()

        def dfs(node, community):
            if node in visited:
                return
            visited.add(node)
            community.add(node)

            if node in graph:
                for neighbor, similarity in graph[node]:
                    if neighbor not in visited:
                        dfs(neighbor, community)

        for article in self.engine.articles:
            if article not in visited:
                community = set()
                dfs(article, community)
                if len(community) > 1:
                    communities.append(community)

        return communities

    def export_to_gephi(self, output_file: Path, min_similarity: float = 0.2):
        """Экспорт в формат Gephi (GraphML)"""
        graph = self.build_graph(min_similarity)

        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')
        lines.append('<graphml>\n')
        lines.append('  <graph edgedefault="undirected">\n')

        # Nodes
        for i, article_path in enumerate(self.engine.articles):
            title = self.engine.articles[article_path]['title']
            lines.append(f'    <node id="{i}" label="{title}"/>\n')

        # Edges
        article_to_id = {path: i for i, path in enumerate(self.engine.articles)}
        edge_id = 0

        for article1, neighbors in graph.items():
            for article2, similarity in neighbors:
                id1 = article_to_id[article1]
                id2 = article_to_id[article2]

                if id1 < id2:  # Avoid duplicates
                    lines.append(f'    <edge id="{edge_id}" source="{id1}" target="{id2}" weight="{similarity:.3f}"/>\n')
                    edge_id += 1

        lines.append('  </graph>\n')
        lines.append('</graphml>\n')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ GraphML экспорт: {output_file}")

    def generate_html_graph(self) -> str:
        """Сгенерировать HTML с интерактивным графом"""
        graph = self.build_graph(min_similarity=0.3)

        # Подготовить данные для D3.js
        nodes = []
        for i, (article_path, data) in enumerate(self.engine.articles.items()):
            nodes.append({
                'id': i,
                'title': data['title'],
                'category': data['category']
            })

        article_to_id = {path: i for i, path in enumerate(self.engine.articles)}

        links = []
        for article1, neighbors in graph.items():
            for article2, similarity in neighbors:
                id1 = article_to_id[article1]
                id2 = article_to_id[article2]

                if id1 < id2:
                    links.append({
                        'source': id1,
                        'target': id2,
                        'value': similarity
                    })

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Article Relationship Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        #graph {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        .links line {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}

        .nodes circle {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
        }}

        .nodes text {{
            font-size: 10px;
            pointer-events: none;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>🔗 Article Relationship Graph</h1>
    <svg id="graph" width="1400" height="800"></svg>

    <script>
        const nodes = {json.dumps(nodes, ensure_ascii=False)};
        const links = {json.dumps(links, ensure_ascii=False)};

        const svg = d3.select("#graph");
        const width = +svg.attr("width");
        const height = +svg.attr("height");

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke-width", d => Math.sqrt(d.value) * 3);

        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("g")
            .data(nodes)
            .enter().append("g");

        node.append("circle")
            .attr("r", 8)
            .attr("fill", "#667eea")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("text")
            .text(d => d.title.substring(0, 20))
            .attr("x", 12)
            .attr("y", 3);

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>"""

        return html

    def save_html_graph(self, output_file: Path):
        """Сохранить HTML граф"""
        html = self.generate_html_graph()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML граф: {output_file}")


class RelatedArticlesEngine:
    """Движок рекомендаций"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Данные статей
        self.articles = {}
        self.links = defaultdict(lambda: {'outgoing': [], 'incoming': []})

        # TF-IDF для контента
        self.word_counts = defaultdict(lambda: defaultdict(int))
        self.document_freq = defaultdict(int)

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

    def tokenize(self, text):
        """Простая токенизация"""
        # Удалить markdown синтаксис
        text = re.sub(r'[#*`\[\]()]', ' ', text)
        # Разбить на слова
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())
        return words

    def build_index(self):
        """Построить индекс"""
        print("🎯 Построение индекса рекомендаций...\n")

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
                'tags': frontmatter.get('tags', []) if frontmatter else [],
                'category': frontmatter.get('category', '') if frontmatter else '',
                'subcategory': frontmatter.get('subcategory', '') if frontmatter else '',
                'difficulty': frontmatter.get('difficulty', 'средний') if frontmatter else 'средний'
            }

            # Токенизация контента
            words = self.tokenize(content)
            unique_words = set(words)

            for word in words:
                self.word_counts[article_path][word] += 1

            for word in unique_words:
                self.document_freq[word] += 1

            # Извлечь ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for text, link in links:
                if link.startswith('http'):
                    continue

                try:
                    target = (md_file.parent / link.split('#')[0]).resolve()

                    if target.exists() and target.is_relative_to(self.root_dir):
                        target_path = str(target.relative_to(self.root_dir))

                        if target_path not in self.links[article_path]['outgoing']:
                            self.links[article_path]['outgoing'].append(target_path)

                        if article_path not in self.links[target_path]['incoming']:
                            self.links[target_path]['incoming'].append(article_path)
                except:
                    pass

        print(f"   Статей проиндексировано: {len(self.articles)}\n")

    def calculate_tf_idf_similarity(self, article1, article2):
        """Вычислить TF-IDF сходство"""
        if article1 not in self.word_counts or article2 not in self.word_counts:
            return 0.0

        words1 = self.word_counts[article1]
        words2 = self.word_counts[article2]

        # Все уникальные слова
        all_words = set(words1.keys()) | set(words2.keys())

        # TF-IDF векторы
        vector1 = []
        vector2 = []

        total_docs = len(self.articles)

        for word in all_words:
            # TF-IDF для article1
            tf1 = words1.get(word, 0)
            idf = math.log(total_docs / (1 + self.document_freq[word]))
            vector1.append(tf1 * idf)

            # TF-IDF для article2
            tf2 = words2.get(word, 0)
            vector2.append(tf2 * idf)

        # Косинусное сходство
        dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
        magnitude1 = math.sqrt(sum(v ** 2 for v in vector1))
        magnitude2 = math.sqrt(sum(v ** 2 for v in vector2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def calculate_tag_similarity(self, article1, article2):
        """Вычислить сходство тегов (Jaccard)"""
        tags1 = set(self.articles[article1]['tags'])
        tags2 = set(self.articles[article2]['tags'])

        if not tags1 or not tags2:
            return 0.0

        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)

        return intersection / union if union > 0 else 0.0

    def calculate_link_score(self, article1, article2):
        """Вычислить оценку связей"""
        score = 0.0

        # Прямая ссылка
        if article2 in self.links[article1]['outgoing']:
            score += 1.0

        # Обратная ссылка
        if article2 in self.links[article1]['incoming']:
            score += 0.5

        # Общие входящие ссылки
        incoming1 = set(self.links[article1]['incoming'])
        incoming2 = set(self.links[article2]['incoming'])
        common_incoming = len(incoming1 & incoming2)
        if common_incoming > 0:
            score += 0.3 * common_incoming

        # Общие исходящие ссылки
        outgoing1 = set(self.links[article1]['outgoing'])
        outgoing2 = set(self.links[article2]['outgoing'])
        common_outgoing = len(outgoing1 & outgoing2)
        if common_outgoing > 0:
            score += 0.2 * common_outgoing

        return score

    def calculate_similarity(self, article1, article2):
        """Вычислить общее сходство"""
        if article1 == article2:
            return 0.0

        # Взвешенная комбинация метрик
        content_sim = self.calculate_tf_idf_similarity(article1, article2)
        tag_sim = self.calculate_tag_similarity(article1, article2)
        link_score = self.calculate_link_score(article1, article2)

        # Бонус за одинаковую категорию
        category_bonus = 0.0
        if self.articles[article1]['category'] == self.articles[article2]['category']:
            category_bonus = 0.2

        # Бонус за одинаковую подкатегорию
        subcategory_bonus = 0.0
        if (self.articles[article1]['subcategory'] and
            self.articles[article1]['subcategory'] == self.articles[article2]['subcategory']):
            subcategory_bonus = 0.3

        # Итоговая оценка
        total = (
            content_sim * 0.3 +
            tag_sim * 0.4 +
            link_score * 0.2 +
            category_bonus +
            subcategory_bonus
        )

        return total

    def get_recommendations(self, article_path, limit=5):
        """Получить рекомендации для статьи"""
        if article_path not in self.articles:
            return []

        similarities = []

        for other_article in self.articles:
            if other_article == article_path:
                continue

            score = self.calculate_similarity(article_path, other_article)
            similarities.append((other_article, score))

        # Сортировать по убыванию
        similarities.sort(key=lambda x: -x[1])

        return similarities[:limit]

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🎯 Рекомендации статей\n\n")
        lines.append("> Умная система рекомендаций на основе контента, тегов и связей\n\n")

        # Для каждой статьи - топ рекомендаций
        for article_path in sorted(self.articles.keys()):
            title = self.articles[article_path]['title']
            recommendations = self.get_recommendations(article_path, limit=5)

            if not recommendations:
                continue

            lines.append(f"## {title}\n\n")
            lines.append(f"`{article_path}`\n\n")
            lines.append("**Рекомендуем прочитать:**\n\n")

            for i, (rec_path, score) in enumerate(recommendations, 1):
                rec_title = self.articles[rec_path]['title']
                lines.append(f"{i}. [{rec_title}]({rec_path}) — *оценка: {score:.2f}*\n")

                # Показать почему рекомендуем
                reasons = []
                tag_sim = self.calculate_tag_similarity(article_path, rec_path)
                if tag_sim > 0.3:
                    reasons.append(f"похожие теги ({tag_sim:.0%})")

                if rec_path in self.links[article_path]['outgoing']:
                    reasons.append("вы ссылаетесь на эту статью")

                if rec_path in self.links[article_path]['incoming']:
                    reasons.append("эта статья ссылается на вас")

                if self.articles[article_path]['category'] == self.articles[rec_path]['category']:
                    reasons.append("та же категория")

                if reasons:
                    lines.append(f"   *{', '.join(reasons)}*\n")

            lines.append("\n")

        output_file = self.root_dir / "RELATED_ARTICLES.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить рекомендации в JSON"""
        data = {}

        for article_path in self.articles:
            recommendations = self.get_recommendations(article_path, limit=10)

            data[article_path] = {
                'title': self.articles[article_path]['title'],
                'recommendations': [
                    {
                        'article': rec_path,
                        'title': self.articles[rec_path]['title'],
                        'score': score
                    }
                    for rec_path, score in recommendations
                ]
            }

        output_file = self.root_dir / "related_articles.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON рекомендации: {output_file}")

    def get_popular_articles(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Получить популярные статьи (по входящим ссылкам)"""
        popularity = []

        for article_path in self.articles:
            incoming_count = len(self.links[article_path]['incoming'])
            popularity.append((article_path, incoming_count))

        return sorted(popularity, key=lambda x: x[1], reverse=True)[:limit]

    def get_trending_articles_by_tags(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Получить статьи с популярными тегами"""
        # Подсчитать частоту тегов
        tag_counts = Counter()
        for article in self.articles.values():
            for tag in article['tags']:
                tag_counts[tag] += 1

        # Оценить статьи по популярности их тегов
        article_scores = []

        for article_path, article_data in self.articles.items():
            score = sum(tag_counts[tag] for tag in article_data['tags'])
            article_scores.append((article_path, score))

        return sorted(article_scores, key=lambda x: x[1], reverse=True)[:top_n]


class CollaborativeFilteringEngine(RelatedArticlesEngine):
    """Рекомендации на основе коллаборативной фильтрации"""

    def find_similar_users_by_category(self, category: str) -> List[str]:
        """Найти статьи той же категории (имитация похожих пользователей)"""
        similar = []

        for article_path, data in self.articles.items():
            if data['category'] == category:
                similar.append(article_path)

        return similar

    def get_category_based_recommendations(self, article_path: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Рекомендации на основе категории"""
        if article_path not in self.articles:
            return []

        category = self.articles[article_path]['category']
        similar_articles = self.find_similar_users_by_category(category)

        recommendations = []

        for other_article in similar_articles:
            if other_article == article_path:
                continue

            # Вычислить сходство
            score = self.calculate_similarity(article_path, other_article)
            recommendations.append((other_article, score))

        return sorted(recommendations, key=lambda x: x[1], reverse=True)[:limit]


def main():
    parser = argparse.ArgumentParser(
        description='🎯 Related Articles - Продвинутая рекомендательная система',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Примеры использования:
  %(prog)s                             # Генерировать рекомендации для всех статей
  %(prog)s --popular                   # Показать популярные статьи
  %(prog)s --trending                  # Показать trending статьи
  %(prog)s --for путь                  # Рекомендации для конкретной статьи
  %(prog)s --tfidf knowledge/ai/ml.md  # TF-IDF анализ и объяснения
  %(prog)s --semantic                  # Семантические кластеры
  %(prog)s --graph graph.html          # Интерактивный граф связей
  %(prog)s --all                       # Всё вместе
        """
    )

    parser.add_argument('--popular', action='store_true',
                       help='Показать популярные статьи (по входящим ссылкам)')
    parser.add_argument('--trending', action='store_true',
                       help='Показать trending статьи (по популярности тегов)')
    parser.add_argument('--for', dest='for_article', type=str, metavar='PATH',
                       help='Рекомендации для конкретной статьи')
    parser.add_argument('--collaborative', action='store_true',
                       help='Использовать коллаборативную фильтрацию')
    parser.add_argument('--tfidf', type=str, metavar='PATH',
                       help='TF-IDF анализ для статьи с объяснениями')
    parser.add_argument('--semantic', action='store_true',
                       help='Найти семантические кластеры статей')
    parser.add_argument('--graph', type=str, metavar='FILE',
                       help='Генерировать HTML граф связей')
    parser.add_argument('--surprise', type=str, metavar='PATH',
                       help='Рекомендации с фактором неожиданности')
    parser.add_argument('--json', action='store_true',
                       help='Экспорт рекомендаций в JSON')
    parser.add_argument('--limit', type=int, default=5,
                       help='Количество рекомендаций (default: 5)')
    parser.add_argument('--all', action='store_true',
                       help='Все анализы + все форматы экспорта')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Выбор engine
    if args.collaborative:
        engine = CollaborativeFilteringEngine(root_dir)
    else:
        engine = RelatedArticlesEngine(root_dir)

    engine.build_index()

    # --popular
    if args.popular or args.all:
        print("📊 Популярные статьи (по входящим ссылкам):\n")
        popular = engine.get_popular_articles(limit=args.limit if not args.all else 10)

        for i, (article_path, incoming_count) in enumerate(popular, 1):
            title = engine.articles[article_path]['title']
            print(f"   {i}. {title} ({incoming_count} входящих ссылок)")
            print(f"      {article_path}\n")

    # --trending
    if args.trending or args.all:
        print("\n🔥 Trending статьи (по популярности тегов):\n")
        trending = engine.get_trending_articles_by_tags(top_n=args.limit if not args.all else 10)

        for i, (article_path, score) in enumerate(trending, 1):
            title = engine.articles[article_path]['title']
            tags = ', '.join(engine.articles[article_path]['tags'])
            print(f"   {i}. {title} (score: {score})")
            print(f"      Теги: {tags}")
            print(f"      {article_path}\n")

    # --tfidf analysis
    if args.tfidf:
        article_path = args.tfidf
        if article_path not in engine.articles:
            print(f"⚠️  Статья не найдена: {article_path}")
            return

        print(f"\n📊 TF-IDF анализ: {engine.articles[article_path]['title']}\n")

        analyzer = TFIDFAnalyzer(engine)

        # Top keywords
        print("   Ключевые слова (TF-IDF):")
        keywords = analyzer.get_top_keywords(article_path, 10)

        for i, (word, score) in enumerate(keywords, 1):
            print(f"      {i}. {word} (score: {score:.2f})")

        # Explain similarity with top recommendation
        recommendations = engine.get_recommendations(article_path, 1)
        if recommendations:
            rec_path, rec_score = recommendations[0]
            print(f"\n   Объяснение сходства с топ рекомендацией:")
            print(f"   {engine.articles[rec_path]['title']}\n")

            explanation = analyzer.explain_similarity(article_path, rec_path)

            print(f"      Content similarity: {explanation['content_similarity']:.3f}")
            print(f"      Tag similarity: {explanation['tag_similarity']:.3f}")
            print(f"      Link score: {explanation['link_score']:.3f}")

            if explanation['common_keywords']:
                print(f"      Common keywords: {', '.join(explanation['common_keywords'][:5])}")

            if explanation['common_tags']:
                print(f"      Common tags: {', '.join(explanation['common_tags'])}")

    # --semantic clustering
    if args.semantic or args.all:
        print("\n🧠 Семантические кластеры:\n")

        semantic = SemanticAnalyzer(engine)
        clusters = semantic.find_semantic_clusters(similarity_threshold=0.3)

        print(f"   Найдено кластеров: {len(clusters)}\n")

        for i, cluster in enumerate(clusters[:5], 1):
            print(f"   Кластер {i} ({len(cluster)} статей):")

            # Показать главные темы кластера
            topics = semantic.get_cluster_topics(cluster, 5)
            print(f"      Темы: {', '.join(word for word, count in topics)}")

            # Показать несколько статей
            for article_path in list(cluster)[:3]:
                title = engine.articles[article_path]['title']
                print(f"      - {title}")

            print()

    # --graph visualization
    if args.graph or args.all:
        html_file = args.graph if args.graph else root_dir / "article_graph.html"
        print(f"\n🔗 Генерация интерактивного графа...\n")

        graph_builder = RelationshipGraphBuilder(engine)
        graph_builder.save_html_graph(html_file)

        # Также экспортировать GraphML
        graphml_file = root_dir / "article_graph.graphml"
        graph_builder.export_to_gephi(graphml_file, min_similarity=0.3)

    # --surprise recommendations
    if args.surprise:
        article_path = args.surprise
        if article_path not in engine.articles:
            print(f"⚠️  Статья не найдена: {article_path}")
            return

        print(f"\n🎲 Рекомендации с фактором неожиданности:\n")
        print(f"   Для: {engine.articles[article_path]['title']}\n")

        pattern_analyzer = ReadingPatternAnalyzer(engine)
        surprise_recs = pattern_analyzer.get_surprise_recommendations(article_path, args.limit)

        if surprise_recs:
            print("   Неожиданные, но релевантные статьи:")
            for i, (rec_path, score) in enumerate(surprise_recs, 1):
                rec_title = engine.articles[rec_path]['title']
                rec_cat = engine.articles[rec_path]['category']
                orig_cat = engine.articles[article_path]['category']

                print(f"   {i}. {rec_title} (score: {score:.2f})")
                print(f"      Категория: {rec_cat} (исходная: {orig_cat})\n")
        else:
            print("   Нет неожиданных рекомендаций (все похожие статьи в той же категории)")

    # --for specific article
    if args.for_article:
        article_path = args.for_article
        if article_path not in engine.articles:
            print(f"⚠️  Статья не найдена: {article_path}")
            return

        print(f"\n🎯 Рекомендации для: {engine.articles[article_path]['title']}\n")

        if args.collaborative and isinstance(engine, CollaborativeFilteringEngine):
            recommendations = engine.get_category_based_recommendations(article_path, args.limit)
        else:
            recommendations = engine.get_recommendations(article_path, args.limit)

        for i, (rec_path, score) in enumerate(recommendations, 1):
            rec_title = engine.articles[rec_path]['title']
            print(f"   {i}. {rec_title} (score: {score:.2f})")
            print(f"      {rec_path}\n")

    # JSON export
    if args.json or args.all:
        print("\n📦 Экспорт в JSON...\n")
        engine.save_json()

    # Default: generate full report
    if not any([args.popular, args.trending, args.for_article, args.tfidf,
                args.semantic, args.graph, args.surprise, args.json, args.all]):
        engine.generate_report()
        engine.save_json()

        print("\n💡 Дополнительные опции:")
        print("   --tfidf PATH        # TF-IDF анализ с объяснениями")
        print("   --semantic          # Найти семантические кластеры")
        print("   --graph FILE        # HTML граф связей")
        print("   --surprise PATH     # Неожиданные рекомендации")
        print("   --all               # Всё вместе")


if __name__ == "__main__":
    main()
