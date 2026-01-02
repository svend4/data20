#!/usr/bin/env python3
"""
Prerequisites Graph - Граф зависимостей
Показывает, какие статьи нужно прочитать перед другими

Вдохновлено: графами зависимостей курсов в университетах
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class PrerequisitesGraph:
    """Построитель графа зависимостей"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Граф зависимостей
        self.prerequisites = defaultdict(lambda: {'requires': [], 'required_by': []})
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

        return dfs(article_path)

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

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Граф зависимостей\n\n")
        lines.append("> Показывает последовательность изучения материала\n\n")

        # Статистика
        entry_points = self.find_entry_points()
        advanced_topics = self.find_advanced_topics()

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Зависимостей**: {sum(len(p['requires']) for p in self.prerequisites.values())}\n")
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
        data = {
            'articles': self.articles,
            'graph': {
                article: {
                    'requires': prereqs['requires'],
                    'required_by': prereqs['required_by'],
                    'depth': self.calculate_depth(article)
                }
                for article, prereqs in self.prerequisites.items()
            },
            'entry_points': self.find_entry_points(),
            'advanced_topics': [
                {'article': article, 'prerequisites': count}
                for article, count in self.find_advanced_topics()
            ]
        }

        output_file = self.root_dir / "prerequisites_graph.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON граф: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    graph = PrerequisitesGraph(root_dir)
    graph.build_graph()
    graph.generate_report()
    graph.save_json()


if __name__ == "__main__":
    main()
