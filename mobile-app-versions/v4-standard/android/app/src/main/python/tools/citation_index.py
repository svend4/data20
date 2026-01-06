#!/usr/bin/env python3
"""
Citation Index - Индекс цитирований
Отслеживает, какие статьи цитируют друг друга

Вдохновлено: Science Citation Index (Eugene Garfield, 1964)

Метрики:
- h-index: максимальное h, при котором есть h статей с h+ цитированиями
- i10-index: количество статей с 10+ цитированиями
- Impact Factor: среднее цитирований на статью
- Co-citation: статьи цитируемые вместе
- Bibliographic Coupling: статьи цитирующие одни источники
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import argparse
from typing import List, Dict, Tuple, Set
from datetime import datetime
import math


class CitationIndexer:
    """Индексатор цитирований"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Индекс цитирований
        self.citations = defaultdict(lambda: {'cited_by': [], 'cites': [], 'citation_count': 0})

        # Все статьи
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

    def extract_citations(self, content, source_file):
        """Извлечь цитирования из содержимого"""
        citations = []

        # Markdown ссылки на другие статьи
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for text, link in links:
            # Пропустить внешние ссылки
            if link.startswith('http'):
                continue

            # Разрешить относительный путь
            try:
                target = (Path(source_file).parent / link).resolve()

                # Убрать якорь если есть
                if '#' in str(target):
                    target = Path(str(target).split('#')[0])

                # Проверить, что файл существует
                if target.exists() and target.is_relative_to(self.root_dir):
                    target_path = str(target.relative_to(self.root_dir))
                    citations.append({
                        'target': target_path,
                        'context': text,
                        'type': 'link'
                    })
            except:
                pass

        # Ссылки из frontmatter (related)
        frontmatter, _ = self.extract_frontmatter_and_content(source_file)

        if frontmatter and 'related' in frontmatter:
            related = frontmatter['related']
            if isinstance(related, list):
                for link in related:
                    try:
                        target = (Path(source_file).parent / link).resolve()

                        if target.exists() and target.is_relative_to(self.root_dir):
                            target_path = str(target.relative_to(self.root_dir))
                            citations.append({
                                'target': target_path,
                                'context': 'Related article',
                                'type': 'frontmatter'
                            })
                    except:
                        pass

        return citations

    def build_index(self):
        """Построить индекс цитирований"""
        print("📚 Построение индекса цитирований...\n")

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
                'date': frontmatter.get('date', '') if frontmatter else '',
                'author': frontmatter.get('author', frontmatter.get('source', '')) if frontmatter else ''
            }

        # Построить граф цитирований
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            # Извлечь цитирования
            citations = self.extract_citations(content, md_file)

            for citation in citations:
                target = citation['target']

                # Добавить в граф
                if target not in self.citations[article_path]['cites']:
                    self.citations[article_path]['cites'].append({
                        'article': target,
                        'context': citation['context'],
                        'type': citation['type']
                    })

                if article_path not in [c['article'] for c in self.citations[target]['cited_by']]:
                    self.citations[target]['cited_by'].append({
                        'article': article_path,
                        'context': citation['context'],
                        'type': citation['type']
                    })

                # Увеличить счётчик
                self.citations[target]['citation_count'] += 1

        print(f"   Статей проиндексировано: {len(self.articles)}")
        print(f"   Связей найдено: {sum(len(c['cites']) for c in self.citations.values())}\n")

    def calculate_h_index(self, article_path):
        """
        Вычислить h-index для статьи
        h-index = максимальное h, при котором статья имеет h цитирований
        от статей, у которых тоже есть хотя бы h цитирований
        """
        citation_counts = []

        for citing in self.citations[article_path]['cited_by']:
            citing_article = citing['article']
            citing_count = self.citations[citing_article]['citation_count']
            citation_counts.append(citing_count)

        citation_counts.sort(reverse=True)

        h = 0
        for i, count in enumerate(citation_counts, 1):
            if count >= i:
                h = i
            else:
                break

        return h

    def calculate_i10_index(self, article_path):
        """
        i10-index: количество статей с 10+ цитированиями
        """
        count = 0
        for citing in self.citations[article_path]['cited_by']:
            citing_article = citing['article']
            citing_count = self.citations[citing_article]['citation_count']
            if citing_count >= 10:
                count += 1
        return count

    def calculate_impact_factor(self) -> float:
        """Impact Factor: среднее количество цитирований на статью"""
        total_cites = sum(data['citation_count'] for data in self.citations.values())
        return total_cites / len(self.articles) if self.articles else 0.0

    def find_cocitations(self, article_path: str, min_cocitations: int = 2) -> List[Tuple[str, int]]:
        """
        Co-citation analysis: найти статьи, которые цитируются вместе

        Если A и B цитируются вместе в статье C, это co-citation
        """
        cocitations = Counter()

        # Для каждой статьи, которая цитирует нашу
        for citing in self.citations[article_path]['cited_by']:
            citing_article = citing['article']

            # Найти другие статьи, которые она тоже цитирует
            for cited in self.citations[citing_article]['cites']:
                cited_article = cited['article']
                if cited_article != article_path:
                    cocitations[cited_article] += 1

        # Вернуть только с достаточным количеством co-citations
        return [(article, count) for article, count in cocitations.most_common()
                if count >= min_cocitations]

    def find_bibliographic_coupling(self, article_path: str, min_coupling: int = 2) -> List[Tuple[str, int]]:
        """
        Bibliographic Coupling: статьи, цитирующие те же источники

        Если A и B цитируют одни и те же статьи, это coupling
        """
        coupling = Counter()

        # Статьи, которые цитирует наша статья
        our_cites = set(c['article'] for c in self.citations[article_path]['cites'])

        # Для каждой другой статьи
        for other_article in self.articles:
            if other_article == article_path:
                continue

            # Найти общие цитирования
            other_cites = set(c['article'] for c in self.citations[other_article]['cites'])
            common = our_cites & other_cites

            if len(common) >= min_coupling:
                coupling[other_article] = len(common)

        return coupling.most_common()

    def calculate_citation_network_metrics(self) -> Dict:
        """Вычислить метрики сети цитирований"""
        # Граф как adjacency dict
        graph = defaultdict(set)
        for article, data in self.citations.items():
            for cited in data['cites']:
                graph[article].add(cited['article'])

        # Nodes and edges
        nodes = set(self.articles.keys())
        edges = sum(len(neighbors) for neighbors in graph.values())

        # Density: actual edges / possible edges
        n = len(nodes)
        max_edges = n * (n - 1)  # Directed graph
        density = edges / max_edges if max_edges > 0 else 0

        # Average degree
        avg_out_degree = edges / n if n > 0 else 0

        # Find isolated nodes
        isolated = [node for node in nodes
                   if not graph[node] and not self.citations[node]['cited_by']]

        return {
            'nodes': n,
            'edges': edges,
            'density': round(density, 4),
            'avg_out_degree': round(avg_out_degree, 2),
            'isolated_nodes': len(isolated)
        }

    def get_most_cited(self, limit=10):
        """Получить самые цитируемые статьи"""
        cited = [(article, data['citation_count'])
                 for article, data in self.citations.items()
                 if data['citation_count'] > 0]

        cited.sort(key=lambda x: -x[1])

        return cited[:limit]

    def generate_report(self):
        """Создать отчёт по цитированиям"""
        lines = []
        lines.append("# 📚 Индекс цитирований\n\n")
        lines.append("> Science Citation Index style (Eugene Garfield, 1964)\n\n")
        lines.append(f"_Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")

        # Статистика
        total_citations = sum(data['citation_count'] for data in self.citations.values())
        articles_cited = len([a for a, d in self.citations.items() if d['citation_count'] > 0])
        impact_factor = self.calculate_impact_factor()
        network_metrics = self.calculate_citation_network_metrics()

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Статей с цитированиями**: {articles_cited}\n")
        lines.append(f"- **Всего цитирований**: {total_citations}\n")
        lines.append(f"- **Impact Factor**: {impact_factor:.2f}\n\n")

        lines.append("### Метрики сети\n\n")
        lines.append(f"- **Узлов**: {network_metrics['nodes']}\n")
        lines.append(f"- **Рёбер**: {network_metrics['edges']}\n")
        lines.append(f"- **Плотность**: {network_metrics['density']:.4f}\n")
        lines.append(f"- **Avg out-degree**: {network_metrics['avg_out_degree']:.2f}\n")
        lines.append(f"- **Изолированных узлов**: {network_metrics['isolated_nodes']}\n\n")

        # Топ цитируемых
        lines.append("## Топ-10 самых цитируемых статей\n\n")

        most_cited = self.get_most_cited(10)

        for i, (article, count) in enumerate(most_cited, 1):
            title = self.articles.get(article, {}).get('title', article)
            h_index = self.calculate_h_index(article)
            i10_index = self.calculate_i10_index(article)

            lines.append(f"### {i}. {title}\n\n")
            lines.append(f"- **Цитирований**: {count}\n")
            lines.append(f"- **h-index**: {h_index}\n")
            lines.append(f"- **i10-index**: {i10_index}\n")
            lines.append(f"- **Файл**: `{article}`\n\n")

            # Кто цитирует
            if self.citations[article]['cited_by']:
                lines.append("**Цитируют:**\n")
                for citing in self.citations[article]['cited_by'][:5]:
                    citing_title = self.articles.get(citing['article'], {}).get('title', citing['article'])
                    lines.append(f"- [{citing_title}]({citing['article']}) — \"{citing['context']}\"\n")

                if len(self.citations[article]['cited_by']) > 5:
                    lines.append(f"\n...и ещё {len(self.citations[article]['cited_by']) - 5}\n")

                lines.append("\n")

        # Статьи без цитирований
        uncited = [a for a, d in self.citations.items() if d['citation_count'] == 0]

        lines.append(f"\n## Статьи без цитирований ({len(uncited)})\n\n")

        if uncited:
            for article in sorted(uncited)[:10]:
                title = self.articles.get(article, {}).get('title', article)
                lines.append(f"- [{title}]({article})\n")

            if len(uncited) > 10:
                lines.append(f"\n...и ещё {len(uncited) - 10}\n")
        else:
            lines.append("Все статьи имеют цитирования! 🎉\n")

        output_file = self.root_dir / "CITATION_INDEX.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Индекс цитирований: {output_file}")

    def save_json(self):
        """Сохранить индекс в JSON"""
        articles_serializable = {}
        for path, info in self.articles.items():
            articles_serializable[path] = {
                'title': info['title'],
                'date': str(info['date']) if info['date'] else '',
                'author': info['author']
            }

        data = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'impact_factor': self.calculate_impact_factor()
            },
            'network_metrics': self.calculate_citation_network_metrics(),
            'articles': articles_serializable,
            'citations': {
                article: {
                    'citation_count': data['citation_count'],
                    'h_index': self.calculate_h_index(article),
                    'i10_index': self.calculate_i10_index(article),
                    'cited_by': data['cited_by'],
                    'cites': data['cites']
                }
                for article, data in self.citations.items()
            }
        }

        output_file = self.root_dir / "citation_index.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON индекс: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Citation Index - Индекс цитирований',
        epilog="""
Примеры:
  %(prog)s                        # Полный анализ
  %(prog)s --metrics              # Метрики сети
  %(prog)s --cocite article.md    # Co-citation analysis
  %(prog)s --coupling article.md  # Bibliographic coupling
        """
    )

    parser.add_argument('--metrics', action='store_true',
                       help='Показать метрики сети цитирований')
    parser.add_argument('--cocite', metavar='ARTICLE',
                       help='Co-citation analysis для статьи')
    parser.add_argument('--coupling', metavar='ARTICLE',
                       help='Bibliographic coupling для статьи')
    parser.add_argument('--top', type=int, default=10,
                       help='Количество топ статей (default: 10)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    indexer = CitationIndexer(root_dir)
    indexer.build_index()

    if args.metrics:
        print("\n📊 Метрики сети цитирований:\n")
        metrics = indexer.calculate_citation_network_metrics()
        impact = indexer.calculate_impact_factor()

        print(f"Impact Factor: {impact:.2f}")
        print(f"Узлов: {metrics['nodes']}")
        print(f"Рёбер: {metrics['edges']}")
        print(f"Плотность: {metrics['density']:.4f}")
        print(f"Avg out-degree: {metrics['avg_out_degree']:.2f}")
        print(f"Изолированных: {metrics['isolated_nodes']}\n")

    elif args.cocite:
        article_path = f"knowledge/{args.cocite}"
        print(f"\n🔗 Co-citation analysis: {args.cocite}\n")
        cocites = indexer.find_cocitations(article_path)

        if cocites:
            for article, count in cocites[:5]:
                title = indexer.articles.get(article, {}).get('title', article)
                print(f"{count} co-citations: {title}")
        else:
            print("No co-citations found")
        print()

    elif args.coupling:
        article_path = f"knowledge/{args.coupling}"
        print(f"\n📚 Bibliographic coupling: {args.coupling}\n")
        coupling = indexer.find_bibliographic_coupling(article_path)

        if coupling:
            for article, count in coupling[:5]:
                title = indexer.articles.get(article, {}).get('title', article)
                print(f"{count} common citations: {title}")
        else:
            print("No bibliographic coupling found")
        print()

    else:
        indexer.generate_report()
        indexer.save_json()


if __name__ == "__main__":
    main()
