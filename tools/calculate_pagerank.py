#!/usr/bin/env python3
"""
PageRank для базы знаний
Вдохновлено: Google PageRank (Larry Page & Sergey Brin, 1996)

Вычисляет важность статей на основе структуры ссылок между ними.
Статьи, на которые ссылаются другие важные статьи, получают более высокий ранг.
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json
import argparse
import math
from typing import Dict, List, Set


class PersonalizedPageRank:
    """
    Персонализированный PageRank
    Topic-specific PageRank с учётом предпочтений пользователя или темы
    """

    def __init__(self, graph, articles, damping=0.85, iterations=100):
        self.graph = graph  # {'node': ['neighbor1', 'neighbor2', ...]}
        self.articles = articles
        self.damping = damping
        self.iterations = iterations

    def calculate_personalized(self, seed_articles: List[str]) -> Dict[str, float]:
        """
        Вычислить персонализированный PageRank от заданных статей

        Args:
            seed_articles: список статей-источников (интересов пользователя)

        Returns:
            Dict[file_path, personalized_score]
        """
        N = len(self.articles)

        if N == 0:
            return {}

        # Normalize seed articles (personalization vector)
        seed_set = set(seed_articles)
        personalization = {}

        for article in self.articles:
            if article in seed_set:
                personalization[article] = 1.0 / len(seed_set)
            else:
                personalization[article] = 0.0

        # Инициализация: используем персонализацию вместо uniform distribution
        pr = personalization.copy()

        # Iterative calculation
        for _ in range(self.iterations):
            new_pr = {}

            for article in self.articles:
                # Teleport to personalized nodes
                rank = (1 - self.damping) * personalization[article]

                # Add contributions from incoming links
                for incoming in self.graph.get('inlinks', {}).get(article, []):
                    outlinks_count = len(self.graph.get('outlinks', {}).get(incoming, []))

                    if outlinks_count > 0:
                        rank += self.damping * (pr[incoming] / outlinks_count)

                new_pr[article] = rank

            pr = new_pr

        return pr

    def recommend_similar(self, article: str, top_n: int = 10) -> List[Dict]:
        """
        Рекомендовать статьи, похожие на заданную (персонализированный PR от одной статьи)
        """
        if article not in self.articles:
            return []

        pr = self.calculate_personalized([article])

        # Sort by score, exclude seed article
        recommendations = [
            {'file': file, 'score': score}
            for file, score in pr.items()
            if file != article
        ]

        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return recommendations[:top_n]


class PageRankVariants:
    """
    Варианты PageRank с различными параметрами
    Исследование влияния damping factor, iterations, topic-sensitive PR
    """

    def __init__(self, articles, inlinks, outlinks):
        self.articles = articles
        self.inlinks = inlinks
        self.outlinks = outlinks

    def compare_damping_factors(self, factors: List[float] = None) -> Dict[float, Dict[str, float]]:
        """
        Сравнить влияние различных damping factors

        Default factors: [0.5, 0.75, 0.85, 0.95]
        """
        if factors is None:
            factors = [0.5, 0.75, 0.85, 0.95]

        results = {}

        for damping in factors:
            pr = self._calculate_with_damping(damping)
            results[damping] = pr

        return results

    def _calculate_with_damping(self, damping: float, iterations: int = 100) -> Dict[str, float]:
        """Вычислить PageRank с заданным damping factor"""
        N = len(self.articles)

        if N == 0:
            return {}

        # Инициализация
        pr = {article: 1.0 / N for article in self.articles}

        # Итерации
        for _ in range(iterations):
            new_pr = {}

            for article in self.articles:
                rank = (1 - damping) / N

                for incoming in self.inlinks[article]:
                    outlinks_count = len(self.outlinks[incoming])

                    if outlinks_count > 0:
                        rank += damping * (pr[incoming] / outlinks_count)

                new_pr[article] = rank

            pr = new_pr

        return pr

    def topic_sensitive_pagerank(self, topics: Dict[str, List[str]], damping=0.85, iterations=100) -> Dict[str, Dict[str, float]]:
        """
        Topic-Sensitive PageRank

        Args:
            topics: {'topic_name': [article1, article2, ...]} - статьи по темам

        Returns:
            {'topic_name': {article: score}}
        """
        results = {}

        for topic_name, topic_articles in topics.items():
            # Персонализированный вектор для темы
            N = len(self.articles)
            personalization = {}

            topic_set = set(topic_articles)

            for article in self.articles:
                if article in topic_set:
                    personalization[article] = 1.0 / len(topic_set)
                else:
                    personalization[article] = 0.0

            # Вычислить PR с персонализацией
            pr = personalization.copy()

            for _ in range(iterations):
                new_pr = {}

                for article in self.articles:
                    rank = (1 - damping) * personalization[article]

                    for incoming in self.inlinks[article]:
                        outlinks_count = len(self.outlinks[incoming])

                        if outlinks_count > 0:
                            rank += damping * (pr[incoming] / outlinks_count)

                    new_pr[article] = rank

                pr = new_pr

            results[topic_name] = pr

        return results


class ConvergenceAnalyzer:
    """
    Анализ сходимости PageRank
    Мониторинг изменений между итерациями, определение оптимального числа итераций
    """

    def __init__(self):
        self.convergence_history = []  # [(iteration, delta), ...]

    def calculate_with_monitoring(self, articles, inlinks, outlinks, damping=0.85, max_iterations=100, tolerance=1e-6):
        """
        Вычислить PageRank с мониторингом сходимости

        Args:
            tolerance: порог изменения для остановки (L1 norm)

        Returns:
            (pagerank_dict, convergence_info)
        """
        N = len(articles)

        if N == 0:
            return {}, {'converged': False, 'iterations': 0}

        # Инициализация
        pr = {article: 1.0 / N for article in articles}

        self.convergence_history = []
        converged = False
        final_iteration = max_iterations

        for iteration in range(max_iterations):
            new_pr = {}

            for article in articles:
                rank = (1 - damping) / N

                for incoming in inlinks[article]:
                    outlinks_count = len(outlinks[incoming])

                    if outlinks_count > 0:
                        rank += damping * (pr[incoming] / outlinks_count)

                new_pr[article] = rank

            # Вычислить изменение (L1 norm)
            delta = sum(abs(new_pr[a] - pr[a]) for a in articles)

            self.convergence_history.append((iteration + 1, delta))

            # Проверка сходимости
            if delta < tolerance:
                converged = True
                final_iteration = iteration + 1
                pr = new_pr
                break

            pr = new_pr

        convergence_info = {
            'converged': converged,
            'iterations': final_iteration,
            'final_delta': self.convergence_history[-1][1] if self.convergence_history else 0,
            'tolerance': tolerance,
            'history': self.convergence_history
        }

        return pr, convergence_info

    def get_convergence_report(self) -> Dict:
        """Получить отчёт о сходимости"""
        if not self.convergence_history:
            return {}

        deltas = [delta for _, delta in self.convergence_history]

        return {
            'total_iterations': len(self.convergence_history),
            'initial_delta': deltas[0],
            'final_delta': deltas[-1],
            'max_delta': max(deltas),
            'min_delta': min(deltas),
            'convergence_rate': deltas[0] / deltas[-1] if deltas[-1] > 0 else float('inf')
        }


class InfluenceScorer:
    """
    Анализ распространения влияния через сеть
    Измерение влияния отдельных узлов на общую структуру рейтинга
    """

    def __init__(self, articles, inlinks, outlinks, pagerank):
        self.articles = articles
        self.inlinks = inlinks
        self.outlinks = outlinks
        self.pagerank = pagerank

    def calculate_influence_spread(self, article: str, hops: int = 3) -> Dict[str, float]:
        """
        Вычислить распространение влияния от статьи за N шагов

        Returns:
            {article: influence_score} - взвешенное влияние по расстоянию
        """
        if article not in self.articles:
            return {}

        # BFS с весами
        influence = {article: 1.0}
        visited = {article}
        queue = [(article, 0)]  # (node, distance)

        while queue:
            current, distance = queue.pop(0)

            if distance >= hops:
                continue

            # Распространение влияния на исходящие ссылки
            for outgoing in self.outlinks.get(current, []):
                if outgoing not in visited:
                    visited.add(outgoing)
                    queue.append((outgoing, distance + 1))

                    # Влияние уменьшается с расстоянием
                    decay = 0.5 ** (distance + 1)
                    influence[outgoing] = influence.get(outgoing, 0) + decay

        return influence

    def find_influential_nodes(self, top_n: int = 10) -> List[Dict]:
        """
        Найти самые влиятельные узлы (комбинация PR + structural influence)
        """
        influence_scores = []

        for article in self.articles:
            pr_score = self.pagerank.get(article, 0)

            # Structural influence: комбинация inlinks, outlinks, и PageRank
            inlinks_count = len(self.inlinks.get(article, []))
            outlinks_count = len(self.outlinks.get(article, []))

            # Influence score: PR × (1 + log(1 + inlinks)) × (1 + log(1 + outlinks))
            structural_bonus = (1 + math.log1p(inlinks_count)) * (1 + math.log1p(outlinks_count))

            total_influence = pr_score * structural_bonus

            influence_scores.append({
                'file': article,
                'influence': total_influence,
                'pagerank': pr_score,
                'inlinks': inlinks_count,
                'outlinks': outlinks_count
            })

        influence_scores.sort(key=lambda x: x['influence'], reverse=True)

        return influence_scores[:top_n]

    def calculate_authority_hub_scores(self) -> Dict[str, Dict[str, float]]:
        """
        HITS algorithm: Authority and Hub scores

        Authority: статья, на которую ссылаются хорошие hubs
        Hub: статья, которая ссылается на хорошие authorities
        """
        N = len(self.articles)

        if N == 0:
            return {}

        # Инициализация
        auth = {a: 1.0 for a in self.articles}
        hub = {a: 1.0 for a in self.articles}

        # Итерации HITS
        for _ in range(100):
            new_auth = {}
            new_hub = {}

            # Authority update: sum of hub scores of incoming links
            for article in self.articles:
                new_auth[article] = sum(hub[inc] for inc in self.inlinks.get(article, []))

            # Hub update: sum of authority scores of outgoing links
            for article in self.articles:
                new_hub[article] = sum(auth[out] for out in self.outlinks.get(article, []))

            # Нормализация
            auth_norm = math.sqrt(sum(v**2 for v in new_auth.values()))
            hub_norm = math.sqrt(sum(v**2 for v in new_hub.values()))

            if auth_norm > 0:
                auth = {a: v / auth_norm for a, v in new_auth.items()}

            if hub_norm > 0:
                hub = {a: v / hub_norm for a, v in new_hub.items()}

        return {
            'authority': auth,
            'hub': hub
        }


class ArticlePageRank:
    """
    PageRank для статей базы знаний
    """

    def __init__(self, root_dir=".", damping=0.85, iterations=20):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Параметры PageRank
        self.damping = damping  # Коэффициент затухания (обычно 0.85)
        self.iterations = iterations  # Количество итераций

        # Граф статей
        self.articles = {}  # file_path -> metadata
        self.outlinks = defaultdict(list)  # from_file -> [to_file1, to_file2, ...]
        self.inlinks = defaultdict(list)   # to_file -> [from_file1, from_file2, ...]

        # Результаты
        self.pagerank = {}  # file_path -> score

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                return fm
        except:
            pass
        return None

    def resolve_link(self, from_file, link):
        """
        Разрешить относительную ссылку в абсолютный путь

        from_file: knowledge/computers/articles/ai/llm.md
        link: ../programming/python.md
        -> knowledge/computers/articles/programming/python.md
        """
        from_path = Path(from_file)

        # Если ссылка абсолютная (начинается с /)
        if link.startswith('/'):
            target = self.root_dir / link.lstrip('/')
        else:
            # Относительная ссылка
            target = (from_path.parent / link).resolve()

        # Нормализовать путь
        try:
            relative = target.relative_to(self.root_dir)
            return str(relative)
        except:
            return None

    def build_graph(self):
        """Построить граф ссылок между статьями"""
        print("🔗 Построение графа ссылок...\n")

        # Первый проход - собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            file_path = str(md_file.relative_to(self.root_dir))
            frontmatter = self.extract_frontmatter(md_file)

            if not frontmatter:
                continue

            self.articles[file_path] = {
                'title': frontmatter.get('title', md_file.stem),
                'category': frontmatter.get('category', ''),
                'subcategory': frontmatter.get('subcategory', ''),
                'related': frontmatter.get('related', [])
            }

        # Второй проход - построить ссылки
        for file_path, metadata in self.articles.items():
            related = metadata['related']

            if not related or not isinstance(related, list):
                continue

            for link in related:
                # Разрешить относительную ссылку
                target = self.resolve_link(file_path, link)

                if target and target in self.articles:
                    # Добавить ребро графа
                    self.outlinks[file_path].append(target)
                    self.inlinks[target].append(file_path)

        print(f"   Статей: {len(self.articles)}")
        print(f"   Ссылок: {sum(len(links) for links in self.outlinks.values())}")

        # Статистика
        articles_with_outlinks = len([f for f in self.articles if self.outlinks[f]])
        articles_with_inlinks = len([f for f in self.articles if self.inlinks[f]])

        print(f"   Статей с исходящими ссылками: {articles_with_outlinks}")
        print(f"   Статей с входящими ссылками: {articles_with_inlinks}\n")

    def calculate(self):
        """Вычислить PageRank"""
        print(f"📊 Вычисление PageRank (damping={self.damping}, iterations={self.iterations})...\n")

        N = len(self.articles)

        if N == 0:
            print("⚠️  Нет статей для ранжирования")
            return

        # Инициализация: все статьи имеют одинаковый начальный ранг
        for file_path in self.articles:
            self.pagerank[file_path] = 1.0 / N

        # Итеративный расчёт PageRank
        for iteration in range(self.iterations):
            new_pagerank = {}

            for file_path in self.articles:
                # Базовое значение (вероятность случайного перехода)
                rank = (1 - self.damping) / N

                # Сумма вкладов от входящих ссылок
                for incoming_file in self.inlinks[file_path]:
                    # Вклад = PageRank источника / количество его исходящих ссылок
                    num_outlinks = len(self.outlinks[incoming_file])

                    if num_outlinks > 0:
                        rank += self.damping * (self.pagerank[incoming_file] / num_outlinks)

                new_pagerank[file_path] = rank

            # Обновить значения
            self.pagerank = new_pagerank

            # Прогресс
            if (iteration + 1) % 5 == 0:
                print(f"   Итерация {iteration + 1}/{self.iterations}")

        print()

    def get_rankings(self):
        """Получить отсортированный список статей по PageRank"""
        rankings = []

        for file_path, score in self.pagerank.items():
            metadata = self.articles[file_path]

            rankings.append({
                'file': file_path,
                'title': metadata['title'],
                'category': metadata['category'],
                'subcategory': metadata['subcategory'],
                'pagerank': score,
                'inlinks_count': len(self.inlinks[file_path]),
                'outlinks_count': len(self.outlinks[file_path])
            })

        # Сортировать по PageRank (убывание)
        rankings.sort(key=lambda x: x['pagerank'], reverse=True)

        return rankings

    def print_rankings(self):
        """Вывести рейтинг статей"""
        rankings = self.get_rankings()

        print("🏆 Рейтинг статей по PageRank:\n")
        print(f"{'Ранг':<6} {'Score':<12} {'→':<4} {'←':<4} {'Заголовок'}")
        print("=" * 80)

        for i, article in enumerate(rankings, 1):
            score = article['pagerank']
            inlinks = article['inlinks_count']
            outlinks = article['outlinks_count']
            title = article['title'][:50]

            print(f"{i:<6} {score:<12.6f} {outlinks:<4} {inlinks:<4} {title}")

        print()

    def save_rankings(self, output_file):
        """Сохранить рейтинг в JSON"""
        rankings = self.get_rankings()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)

        print(f"✅ Рейтинг сохранён: {output_file}")

    def save_markdown_report(self, output_file):
        """Сохранить отчёт в markdown"""
        rankings = self.get_rankings()

        lines = []
        lines.append("# 🏆 PageRank для базы знаний\n\n")
        lines.append(f"> Вычислено по алгоритму Google PageRank (1996)\n\n")

        lines.append("## Параметры\n\n")
        lines.append(f"- **Damping factor**: {self.damping}\n")
        lines.append(f"- **Iterations**: {self.iterations}\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Всего ссылок**: {sum(len(links) for links in self.outlinks.values())}\n\n")

        lines.append("## Рейтинг статей\n\n")
        lines.append("| Ранг | PageRank | ← | → | Статья | Категория |\n")
        lines.append("|------|----------|---|------|--------|----------|\n")

        for i, article in enumerate(rankings, 1):
            score = f"{article['pagerank']:.6f}"
            inlinks = article['inlinks_count']
            outlinks = article['outlinks_count']
            title = article['title']
            category = f"{article['category']}/{article['subcategory']}"
            file_path = article['file']

            lines.append(f"| {i} | {score} | {inlinks} | {outlinks} | [{title}]({file_path}) | {category} |\n")

        lines.append("\n## Топ-10 самых влиятельных статей\n\n")
        lines.append("Статьи с наивысшим PageRank (на них больше всего ссылаются другие важные статьи):\n\n")

        for i, article in enumerate(rankings[:10], 1):
            lines.append(f"### {i}. {article['title']}\n\n")
            lines.append(f"- **PageRank**: {article['pagerank']:.6f}\n")
            lines.append(f"- **Входящих ссылок**: {article['inlinks_count']}\n")
            lines.append(f"- **Исходящих ссылок**: {article['outlinks_count']}\n")
            lines.append(f"- **Файл**: `{article['file']}`\n")
            lines.append(f"- **Категория**: {article['category']}/{article['subcategory']}\n\n")

            # Показать, кто ссылается
            if self.inlinks[article['file']]:
                lines.append("**Ссылаются на эту статью:**\n\n")
                for ref_file in self.inlinks[article['file']][:5]:
                    ref_title = self.articles[ref_file]['title']
                    lines.append(f"- [{ref_title}]({ref_file})\n")
                lines.append("\n")

        lines.append("\n## Статьи без ссылок\n\n")
        orphans = [a for a in rankings if a['inlinks_count'] == 0 and a['outlinks_count'] == 0]

        if orphans:
            lines.append(f"Найдено {len(orphans)} изолированных статей (нет ни входящих, ни исходящих ссылок):\n\n")
            for article in orphans[:10]:
                lines.append(f"- **{article['title']}** — `{article['file']}`\n")
        else:
            lines.append("Все статьи связаны между собой. Отлично! 🎉\n")

        lines.append("\n## Интерпретация\n\n")
        lines.append("- **PageRank** — важность статьи в базе знаний\n")
        lines.append("- **← (Входящие)** — сколько статей ссылается на эту\n")
        lines.append("- **→ (Исходящие)** — на сколько статей ссылается эта\n\n")
        lines.append("Высокий PageRank означает, что статья является ключевой/центральной в базе знаний.\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown отчёт: {output_file}")

    def add_pagerank_to_articles(self):
        """Добавить PageRank в метаданные статей"""
        print("\n📝 Добавление PageRank в метаданные статей...\n")

        count = 0

        for file_path, score in self.pagerank.items():
            full_path = self.root_dir / file_path

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Извлечь frontmatter
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                if not match:
                    continue

                fm = yaml.safe_load(match.group(1))
                body = match.group(2)

                # Добавить или обновить PageRank
                old_rank = fm.get('pagerank')

                fm['pagerank'] = round(score, 6)
                fm['pagerank_inlinks'] = len(self.inlinks[file_path])
                fm['pagerank_outlinks'] = len(self.outlinks[file_path])

                # Записать обратно
                new_content = "---\n"
                new_content += yaml.dump(fm, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += body

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                if old_rank != fm['pagerank']:
                    count += 1
                    print(f"✅ {file_path}")

            except Exception as e:
                print(f"⚠️  Ошибка в {file_path}: {e}")

        print(f"\n✅ Обновлено статей: {count}")

    def save_html_report(self, output_file):
        """Сохранить отчёт в HTML с красивым оформлением"""
        rankings = self.get_rankings()

        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PageRank Rankings</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
        }
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .rank-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            min-width: 40px;
            text-align: center;
        }
        .rank-gold { background: linear-gradient(135deg, #ffd700, #ffed4e); color: #333; }
        .rank-silver { background: linear-gradient(135deg, #c0c0c0, #e8e8e8); color: #333; }
        .rank-bronze { background: linear-gradient(135deg, #cd7f32, #e5a869); color: white; }
        .score {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #667eea;
        }
        .links {
            display: flex;
            gap: 10px;
        }
        .link-badge {
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }
        .link-in { color: #28a745; }
        .link-out { color: #007bff; }
        .category {
            font-size: 0.85em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 PageRank Rankings</h1>
        <p class="subtitle">Вычислено по алгоритму Google PageRank (1996)</p>

        <div class="stats">
            <div class="stat-card">
                <h3>Всего статей</h3>
                <div class="value">""" + str(len(self.articles)) + """</div>
            </div>
            <div class="stat-card">
                <h3>Всего ссылок</h3>
                <div class="value">""" + str(sum(len(links) for links in self.outlinks.values())) + """</div>
            </div>
            <div class="stat-card">
                <h3>Damping Factor</h3>
                <div class="value">""" + str(self.damping) + """</div>
            </div>
            <div class="stat-card">
                <h3>Итераций</h3>
                <div class="value">""" + str(self.iterations) + """</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Ранг</th>
                    <th>Статья</th>
                    <th>PageRank</th>
                    <th>Ссылки</th>
                    <th>Категория</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, article in enumerate(rankings, 1):
            rank_class = ""
            if i == 1:
                rank_class = "rank-gold"
            elif i == 2:
                rank_class = "rank-silver"
            elif i == 3:
                rank_class = "rank-bronze"

            html += f"""                <tr>
                    <td><span class="rank-badge {rank_class}">#{i}</span></td>
                    <td><strong>{article['title']}</strong></td>
                    <td><span class="score">{article['pagerank']:.6f}</span></td>
                    <td>
                        <div class="links">
                            <span class="link-badge link-in">← {article['inlinks_count']}</span>
                            <span class="link-badge link-out">→ {article['outlinks_count']}</span>
                        </div>
                    </td>
                    <td class="category">{article['category']}/{article['subcategory']}</td>
                </tr>
"""

        html += """            </tbody>
        </table>
    </div>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML отчёт: {output_file}")

    def analyze_convergence(self, tolerance=1e-6, max_iterations=100):
        """Анализировать сходимость PageRank"""
        print(f"\n🔬 Анализ сходимости PageRank (tolerance={tolerance})...\n")

        analyzer = ConvergenceAnalyzer()
        pr, info = analyzer.calculate_with_monitoring(
            self.articles.keys(),
            self.inlinks,
            self.outlinks,
            damping=self.damping,
            max_iterations=max_iterations,
            tolerance=tolerance
        )

        self.pagerank = pr

        print(f"   Сходимость: {'✅ Да' if info['converged'] else '❌ Нет'}")
        print(f"   Итераций: {info['iterations']}/{max_iterations}")
        print(f"   Финальная ошибка: {info['final_delta']:.2e}")
        print()

        return info

    def calculate_influence_scores(self):
        """Вычислить influence scores (комбинация PR + structural влияние)"""
        print("\n💫 Вычисление influence scores...\n")

        influence_scorer = InfluenceScorer(
            self.articles.keys(),
            self.inlinks,
            self.outlinks,
            self.pagerank
        )

        influential = influence_scorer.find_influential_nodes(top_n=10)

        print("Топ-10 самых влиятельных узлов:\n")
        print(f"{'Ранг':<6} {'Influence':<12} {'PageRank':<12} {'Links':<10} {'Заголовок'}")
        print("=" * 80)

        for i, node in enumerate(influential, 1):
            file_path = node['file']
            title = self.articles[file_path]['title'][:40]
            links = f"←{node['inlinks']} →{node['outlinks']}"

            print(f"{i:<6} {node['influence']:<12.6f} {node['pagerank']:<12.6f} {links:<10} {title}")

        print()

        return influential

    def calculate_hits_scores(self):
        """Вычислить HITS (Authority/Hub) scores"""
        print("\n🎯 Вычисление HITS scores (Authority & Hub)...\n")

        influence_scorer = InfluenceScorer(
            self.articles.keys(),
            self.inlinks,
            self.outlinks,
            self.pagerank
        )

        hits = influence_scorer.calculate_authority_hub_scores()

        # Топ authorities
        top_auth = sorted(
            [(file, score) for file, score in hits['authority'].items()],
            key=lambda x: -x[1]
        )[:5]

        # Топ hubs
        top_hubs = sorted(
            [(file, score) for file, score in hits['hub'].items()],
            key=lambda x: -x[1]
        )[:5]

        print("Топ-5 Authorities (на них ссылаются хорошие hubs):")
        for i, (file, score) in enumerate(top_auth, 1):
            title = self.articles[file]['title'][:50]
            print(f"  {i}. {title:<50} {score:.6f}")

        print("\nТоп-5 Hubs (ссылаются на хорошие authorities):")
        for i, (file, score) in enumerate(top_hubs, 1):
            title = self.articles[file]['title'][:50]
            print(f"  {i}. {title:<50} {score:.6f}")

        print()

        return hits


def main():
    parser = argparse.ArgumentParser(
        description='📊 PageRank Calculator - Продвинутый анализ важности статей',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                          # Базовый расчёт PageRank
  %(prog)s --damping 0.95 --iterations 100          # Кастомные параметры
  %(prog)s --convergence                            # Анализ сходимости с автостопом
  %(prog)s --influence                              # Анализ влияния узлов
  %(prog)s --hits                                   # HITS algorithm (Authority/Hub)
  %(prog)s --html pagerank.html                     # Экспорт в HTML
  %(prog)s --json pagerank.json                     # Экспорт в JSON
  %(prog)s --all                                    # Все анализы + все экспорты
  %(prog)s --update-metadata                        # Добавить PageRank в frontmatter статей

Алгоритмы:
  - PageRank: классический алгоритм Google (1996)
  - Personalized PageRank: topic-specific ранжирование
  - HITS: Authority и Hub scores (Kleinberg, 1999)
  - Convergence analysis: мониторинг сходимости
  - Influence scoring: структурное влияние узлов
        """
    )

    # Параметры PageRank
    parser.add_argument(
        '-d', '--damping',
        type=float,
        default=0.85,
        help='Damping factor (по умолчанию: 0.85)'
    )

    parser.add_argument(
        '-i', '--iterations',
        type=int,
        default=20,
        help='Количество итераций (по умолчанию: 20)'
    )

    # Режимы анализа
    parser.add_argument(
        '--convergence',
        action='store_true',
        help='Анализ сходимости с автостопом (tolerance=1e-6)'
    )

    parser.add_argument(
        '--influence',
        action='store_true',
        help='Вычислить influence scores (PR + structural importance)'
    )

    parser.add_argument(
        '--hits',
        action='store_true',
        help='Вычислить HITS scores (Authority и Hub)'
    )

    # Форматы экспорта
    parser.add_argument(
        '--json',
        metavar='FILE',
        help='Экспортировать в JSON'
    )

    parser.add_argument(
        '--html',
        metavar='FILE',
        help='Экспортировать в HTML с красивым оформлением'
    )

    parser.add_argument(
        '--markdown',
        metavar='FILE',
        help='Экспортировать в Markdown отчёт'
    )

    # Метаданные
    parser.add_argument(
        '--update-metadata',
        action='store_true',
        help='Добавить PageRank в frontmatter статей'
    )

    # Всё сразу
    parser.add_argument(
        '--all',
        action='store_true',
        help='Выполнить все анализы и создать все экспорты'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Создать PageRank калькулятор
    pr = ArticlePageRank(root_dir, damping=args.damping, iterations=args.iterations)

    # Построить граф
    pr.build_graph()

    # Вычислить PageRank
    if args.convergence or args.all:
        # С анализом сходимости
        pr.analyze_convergence(tolerance=1e-6, max_iterations=100)
    else:
        # Обычный расчёт
        pr.calculate()

    # Вывести результаты
    pr.print_rankings()

    # Дополнительные анализы
    if args.influence or args.all:
        pr.calculate_influence_scores()

    if args.hits or args.all:
        pr.calculate_hits_scores()

    # Экспорты
    if args.json or args.all:
        json_file = args.json if args.json else root_dir / "pagerank.json"
        pr.save_rankings(json_file)

    if args.markdown or args.all:
        md_file = args.markdown if args.markdown else root_dir / "PAGERANK.md"
        pr.save_markdown_report(md_file)

    if args.html or args.all:
        html_file = args.html if args.html else root_dir / "pagerank.html"
        pr.save_html_report(html_file)

    # Обновить метаданные
    if args.update_metadata or args.all:
        pr.add_pagerank_to_articles()

    print("\n✨ PageRank готов!")

    if args.all:
        print("\n💡 Созданные файлы:")
        print("   - pagerank.json - JSON данные")
        print("   - PAGERANK.md - Markdown отчёт")
        print("   - pagerank.html - HTML визуализация")
        print("   - Метаданные обновлены во всех статьях")
    else:
        print("\n💡 Подсказка: используйте --all для полного анализа и всех экспортов")


if __name__ == "__main__":
    main()
