#!/usr/bin/env python3
"""
Network Analyzer - Анализ сети
Вычисляет сетевые метрики (centrality, clustering, etc.)
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class NetworkAnalyzer:
    """Анализатор сети"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.graph = defaultdict(set)
        self.articles = set()

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
        print("📊 Анализ сети...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            source = str(md_file.relative_to(self.root_dir))
            self.articles.add(source)

            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in links:
                if not link.startswith('http'):
                    try:
                        target = (md_file.parent / link.split('#')[0]).resolve()
                        if target.exists() and target.is_relative_to(self.root_dir):
                            target_path = str(target.relative_to(self.root_dir))
                            self.graph[source].add(target_path)
                            self.articles.add(target_path)
                    except:
                        pass

        print(f"   Nodes: {len(self.articles)}")
        print(f"   Edges: {sum(len(v) for v in self.graph.values())}\n")

    def calculate_metrics(self):
        """Вычислить сетевые метрики"""
        metrics = {}

        for article in self.articles:
            # Out-degree
            out_degree = len(self.graph[article])

            # In-degree
            in_degree = sum(1 for neighbors in self.graph.values() if article in neighbors)

            metrics[article] = {
                'out_degree': out_degree,
                'in_degree': in_degree,
                'total_degree': out_degree + in_degree
            }

        return metrics

    def generate_report(self, metrics):
        lines = []
        lines.append("# 📊 Сетевые метрики\n\n")

        # Топ по total degree
        sorted_articles = sorted(metrics.items(), key=lambda x: -x[1]['total_degree'])

        lines.append("## Топ-10 по связанности\n\n")
        for article, m in sorted_articles[:10]:
            lines.append(f"- **{Path(article).stem}**: {m['total_degree']} связей ")
            lines.append(f"(in: {m['in_degree']}, out: {m['out_degree']})\n")

        output_file = self.root_dir / "NETWORK_METRICS.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Метрики: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = NetworkAnalyzer(root_dir)
    analyzer.build_network()
    metrics = analyzer.calculate_metrics()
    analyzer.generate_report(metrics)


if __name__ == "__main__":
    main()
