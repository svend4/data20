#!/usr/bin/env python3
"""
Taxonomia - Иерархическая классификация
Вдохновлено: Carl Linnaeus's Systema Naturae (1735)

Создаёт древовидную иерархическую структуру знаний, аналогичную
биологической таксономии (Kingdom → Phylum → Class → Order → Family → Genus → Species)

Для базы знаний:
Root → Category → Subcategory → Topic → Article
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class Node:
    """Узел таксономического дерева"""

    def __init__(self, name, level, parent=None):
        self.name = name
        self.level = level  # 0=root, 1=category, 2=subcategory, 3=topic, 4=article
        self.parent = parent
        self.children = []
        self.articles = []
        self.metadata = {}

    def add_child(self, child):
        """Добавить дочерний узел"""
        self.children.append(child)
        child.parent = self

    def add_article(self, article):
        """Добавить статью к узлу"""
        self.articles.append(article)

    def get_path(self):
        """Получить полный путь от корня"""
        path = []
        node = self
        while node:
            if node.name != "root":
                path.insert(0, node.name)
            node = node.parent
        return " → ".join(path)

    def count_articles(self):
        """Посчитать все статьи в этом узле и его потомках"""
        count = len(self.articles)
        for child in self.children:
            count += child.count_articles()
        return count

    def to_dict(self):
        """Преобразовать в словарь для JSON"""
        return {
            'name': self.name,
            'level': self.level,
            'path': self.get_path(),
            'article_count': self.count_articles(),
            'direct_articles': len(self.articles),
            'children': [child.to_dict() for child in self.children],
            'metadata': self.metadata
        }


class Taxonomy:
    """
    Иерархическая таксономия базы знаний
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Корень дерева
        self.root = Node("root", 0)

        # Индекс узлов для быстрого доступа
        self.nodes = {}  # path -> Node

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

    def get_or_create_node(self, path, level, parent):
        """Получить или создать узел по пути"""
        if path in self.nodes:
            return self.nodes[path]

        # Создать новый узел
        name = path.split(" → ")[-1] if " → " in path else path
        node = Node(name, level, parent)
        self.nodes[path] = node

        if parent:
            parent.add_child(node)

        return node

    def build(self):
        """Построить таксономическое дерево"""
        print("🌳 Построение иерархической таксономии...\n")

        article_count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)
            if not frontmatter:
                continue

            # Извлечь таксономические данные
            category = frontmatter.get('category', 'uncategorized')
            subcategory = frontmatter.get('subcategory', '')
            tags = frontmatter.get('tags', [])

            # Построить путь в дереве
            # Level 1: Category
            category_path = category
            category_node = self.get_or_create_node(category_path, 1, self.root)

            # Level 2: Subcategory
            if subcategory:
                subcategory_path = f"{category} → {subcategory}"
                subcategory_node = self.get_or_create_node(subcategory_path, 2, category_node)
                current_node = subcategory_node
            else:
                current_node = category_node

            # Level 3: Topic (первый тег как топик)
            if tags and len(tags) > 0:
                topic = tags[0]
                if subcategory:
                    topic_path = f"{category} → {subcategory} → {topic}"
                else:
                    topic_path = f"{category} → {topic}"

                topic_node = self.get_or_create_node(topic_path, 3, current_node)
                current_node = topic_node

            # Добавить статью к текущему узлу
            article_info = {
                'title': frontmatter.get('title', md_file.stem),
                'file': str(md_file.relative_to(self.root_dir)),
                'tags': tags,
                'date': str(frontmatter.get('date', '')),
                'author': frontmatter.get('author', frontmatter.get('source', ''))
            }

            current_node.add_article(article_info)
            article_count += 1

        print(f"   Статей: {article_count}")
        print(f"   Узлов таксономии: {len(self.nodes)}")
        print()

    def print_tree(self, node=None, indent=0, show_articles=False):
        """Вывести дерево в консоль"""
        if node is None:
            node = self.root

        # Символы дерева
        prefix = "  " * indent

        if node != self.root:
            article_count = node.count_articles()
            direct_count = len(node.articles)

            # Иконки по уровню
            icons = ["", "📁", "📂", "🏷️", "📄"]
            icon = icons[node.level] if node.level < len(icons) else "•"

            print(f"{prefix}{icon} {node.name} ({article_count} статей)")

            # Показать статьи если запрошено
            if show_articles and node.articles:
                for article in node.articles:
                    print(f"{prefix}    📄 {article['title']}")

        # Рекурсивно вывести детей
        for child in sorted(node.children, key=lambda x: x.name):
            self.print_tree(child, indent + 1, show_articles)

    def save_tree_markdown(self, output_file):
        """Сохранить дерево в markdown"""
        lines = []
        lines.append("# 🌳 Таксономия базы знаний\n\n")
        lines.append("> Иерархическая классификация по методу Линнея (1735)\n\n")

        lines.append("## Структура\n\n")
        lines.append("```\n")
        self._write_tree_text(self.root, lines, 0)
        lines.append("```\n\n")

        lines.append("## Детальное описание\n\n")
        self._write_tree_detailed(self.root, lines, 0)

        lines.append("\n## Статистика\n\n")
        stats = self.get_statistics()

        lines.append(f"- **Всего статей**: {stats['total_articles']}\n")
        lines.append(f"- **Категорий**: {stats['categories']}\n")
        lines.append(f"- **Подкатегорий**: {stats['subcategories']}\n")
        lines.append(f"- **Топиков**: {stats['topics']}\n")
        lines.append(f"- **Средняя глубина**: {stats['avg_depth']:.2f}\n")
        lines.append(f"- **Максимальная глубина**: {stats['max_depth']}\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Таксономия в markdown: {output_file}")

    def _write_tree_text(self, node, lines, indent):
        """Записать дерево как текст"""
        prefix = "│   " * indent

        if node != self.root:
            article_count = node.count_articles()
            icons = ["", "📁", "📂", "🏷️", "📄"]
            icon = icons[node.level] if node.level < len(icons) else "•"

            lines.append(f"{prefix}├── {icon} {node.name} ({article_count})\n")

        for child in sorted(node.children, key=lambda x: x.name):
            self._write_tree_text(child, lines, indent + 1)

    def _write_tree_detailed(self, node, lines, level):
        """Записать детальное описание дерева"""
        if node == self.root:
            for child in sorted(node.children, key=lambda x: x.name):
                self._write_tree_detailed(child, lines, level)
            return

        # Заголовок
        article_count = node.count_articles()
        direct_count = len(node.articles)

        heading = "#" * (level + 2)
        lines.append(f"{heading} {node.name}\n\n")

        lines.append(f"**Путь**: {node.get_path()}  \n")
        lines.append(f"**Всего статей**: {article_count}  \n")
        lines.append(f"**Прямых статей**: {direct_count}  \n\n")

        # Статьи в этом узле
        if node.articles:
            lines.append("**Статьи:**\n\n")
            for article in sorted(node.articles, key=lambda x: x['title']):
                lines.append(f"- [{article['title']}]({article['file']})")
                if article['date']:
                    lines.append(f" — {article['date']}")
                lines.append("\n")
            lines.append("\n")

        # Рекурсивно для детей
        for child in sorted(node.children, key=lambda x: x.name):
            self._write_tree_detailed(child, lines, level + 1)

    def save_json(self, output_file):
        """Сохранить таксономию в JSON"""
        data = {
            'root': self.root.to_dict(),
            'statistics': self.get_statistics()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Таксономия в JSON: {output_file}")

    def get_statistics(self):
        """Получить статистику таксономии"""
        categories = len([n for n in self.nodes.values() if n.level == 1])
        subcategories = len([n for n in self.nodes.values() if n.level == 2])
        topics = len([n for n in self.nodes.values() if n.level == 3])

        # Глубина дерева
        depths = []
        for node in self.nodes.values():
            depth = 0
            current = node
            while current.parent:
                depth += 1
                current = current.parent
            depths.append(depth)

        return {
            'total_articles': self.root.count_articles(),
            'total_nodes': len(self.nodes),
            'categories': categories,
            'subcategories': subcategories,
            'topics': topics,
            'max_depth': max(depths) if depths else 0,
            'avg_depth': sum(depths) / len(depths) if depths else 0
        }

    def generate_mermaid_diagram(self):
        """Создать Mermaid диаграмму дерева"""
        lines = []
        lines.append("```mermaid\n")
        lines.append("graph TD\n")

        # Генерировать ID для узлов
        node_ids = {}
        counter = [0]

        def get_id(node):
            if node not in node_ids:
                counter[0] += 1
                node_ids[node] = f"node{counter[0]}"
            return node_ids[node]

        # Рекурсивно добавить узлы и связи
        def add_node(node):
            if node == self.root:
                for child in node.children:
                    add_node(child)
                return

            node_id = get_id(node)
            article_count = node.count_articles()

            # Стиль по уровню
            if node.level == 1:
                style = f"{node_id}[\"{node.name}<br/>{article_count} статей\"]"
            elif node.level == 2:
                style = f"{node_id}(\"{node.name}<br/>{article_count} статей\")"
            else:
                style = f"{node_id}{{{node.name}<br/>{article_count} статей}}"

            lines.append(f"    {style}\n")

            # Связи с родителем
            if node.parent and node.parent != self.root:
                parent_id = get_id(node.parent)
                lines.append(f"    {parent_id} --> {node_id}\n")

            # Рекурсия для детей
            for child in node.children:
                add_node(child)

        add_node(self.root)

        lines.append("```\n")

        return ''.join(lines)

    def save_mermaid(self, output_file):
        """Сохранить Mermaid диаграмму"""
        content = "# 🌳 Диаграмма таксономии\n\n"
        content += self.generate_mermaid_diagram()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Mermaid диаграмма: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    taxonomy = Taxonomy(root_dir)

    # Построить таксономию
    taxonomy.build()

    # Вывести в консоль
    print("🌳 Иерархическая структура:\n")
    taxonomy.print_tree()

    # Сохранить
    print("\n📝 Сохранение таксономии...\n")

    taxonomy.save_tree_markdown(root_dir / "TAXONOMY.md")
    taxonomy.save_json(root_dir / "taxonomy.json")
    taxonomy.save_mermaid(root_dir / "TAXONOMY_DIAGRAM.md")

    # Статистика
    print("\n📊 Статистика:")
    stats = taxonomy.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")

    print("\n✨ Таксономия готова!")
    print("\n💡 Использование:")
    print("   - Просмотр структуры: cat TAXONOMY.md")
    print("   - JSON данные: cat taxonomy.json")
    print("   - Диаграмма: cat TAXONOMY_DIAGRAM.md")


if __name__ == "__main__":
    main()
