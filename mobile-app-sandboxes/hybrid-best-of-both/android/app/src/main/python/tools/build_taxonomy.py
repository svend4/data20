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
import subprocess
from datetime import datetime


class TaxonomyStatistics:
    """
    Статистический анализ таксономии
    - Анализ глубины и баланса дерева
    - Поиск orphan categories (с 1 статьёй)
    - Поиск overpopulated categories (>50 статей)
    - Рекомендации по реорганизации
    """

    def __init__(self, taxonomy):
        self.taxonomy = taxonomy
        self.root = taxonomy.root

    def analyze_depth(self):
        """Детальный анализ глубины по каждой ветке"""
        depth_analysis = {
            'by_branch': {},
            'max_depth': 0,
            'avg_depth': 0,
            'depth_distribution': defaultdict(int)
        }

        # Анализ по веткам
        for category_node in self.root.children:
            branch_depths = []
            self._collect_depths(category_node, 1, branch_depths)

            depth_analysis['by_branch'][category_node.name] = {
                'max_depth': max(branch_depths) if branch_depths else 1,
                'avg_depth': sum(branch_depths) / len(branch_depths) if branch_depths else 1,
                'nodes': len(branch_depths)
            }

        # Общая статистика
        all_depths = []
        for node in self.taxonomy.nodes.values():
            depth = self._get_node_depth(node)
            all_depths.append(depth)
            depth_analysis['depth_distribution'][depth] += 1

        if all_depths:
            depth_analysis['max_depth'] = max(all_depths)
            depth_analysis['avg_depth'] = sum(all_depths) / len(all_depths)

        return depth_analysis

    def _collect_depths(self, node, current_depth, depths):
        """Рекурсивно собрать глубины"""
        depths.append(current_depth)
        for child in node.children:
            self._collect_depths(child, current_depth + 1, depths)

    def _get_node_depth(self, node):
        """Получить глубину узла от корня"""
        depth = 0
        current = node
        while current.parent:
            depth += 1
            current = current.parent
        return depth

    def analyze_balance(self):
        """Анализ баланса дерева"""
        balance_analysis = {
            'is_balanced': True,
            'imbalance_score': 0,
            'issues': []
        }

        # Проверить баланс между ветками
        category_depths = []
        for category_node in self.root.children:
            max_depth = self._get_max_depth(category_node, 1)
            category_depths.append({
                'category': category_node.name,
                'max_depth': max_depth,
                'article_count': category_node.count_articles()
            })

        if len(category_depths) > 1:
            depths = [c['max_depth'] for c in category_depths]
            max_d = max(depths)
            min_d = min(depths)

            # Дерево несбалансировано если разница > 2 уровня
            if max_d - min_d > 2:
                balance_analysis['is_balanced'] = False
                balance_analysis['imbalance_score'] = max_d - min_d

                deepest = [c for c in category_depths if c['max_depth'] == max_d]
                shallowest = [c for c in category_depths if c['max_depth'] == min_d]

                balance_analysis['issues'].append(
                    f"Глубокие ветки: {', '.join(c['category'] for c in deepest)} (depth={max_d})"
                )
                balance_analysis['issues'].append(
                    f"Мелкие ветки: {', '.join(c['category'] for c in shallowest)} (depth={min_d})"
                )

        balance_analysis['category_depths'] = category_depths
        return balance_analysis

    def _get_max_depth(self, node, current_depth):
        """Получить максимальную глубину поддерева"""
        if not node.children:
            return current_depth

        child_depths = [self._get_max_depth(child, current_depth + 1) for child in node.children]
        return max(child_depths)

    def find_orphan_categories(self):
        """Найти категории с 1 статьёй"""
        orphans = []

        for node in self.taxonomy.nodes.values():
            article_count = node.count_articles()
            direct_count = len(node.articles)

            # Orphan: ровно 1 статья во всём поддереве
            if article_count == 1:
                orphans.append({
                    'path': node.get_path(),
                    'level': node.level,
                    'node': node
                })

        return orphans

    def find_overpopulated_categories(self, threshold=50):
        """Найти категории с >threshold статей"""
        overpopulated = []

        for node in self.taxonomy.nodes.values():
            article_count = node.count_articles()

            if article_count > threshold:
                overpopulated.append({
                    'path': node.get_path(),
                    'level': node.level,
                    'article_count': article_count,
                    'children_count': len(node.children),
                    'node': node
                })

        # Сортировать по количеству статей
        overpopulated.sort(key=lambda x: -x['article_count'])
        return overpopulated

    def generate_recommendations(self):
        """Сгенерировать рекомендации по реорганизации"""
        recommendations = []

        # 1. Orphan categories
        orphans = self.find_orphan_categories()
        if orphans:
            recommendations.append({
                'type': 'orphan_categories',
                'severity': 'low',
                'count': len(orphans),
                'message': f"Найдено {len(orphans)} категорий с 1 статьёй. Рассмотреть объединение или удаление."
            })

        # 2. Overpopulated categories
        overpopulated = self.find_overpopulated_categories()
        if overpopulated:
            recommendations.append({
                'type': 'overpopulated_categories',
                'severity': 'medium',
                'count': len(overpopulated),
                'message': f"Найдено {len(overpopulated)} перегруженных категорий (>50 статей). Рассмотреть разбиение."
            })

        # 3. Balance issues
        balance = self.analyze_balance()
        if not balance['is_balanced']:
            recommendations.append({
                'type': 'imbalance',
                'severity': 'medium',
                'score': balance['imbalance_score'],
                'message': f"Дерево несбалансировано (разница глубины: {balance['imbalance_score']} уровней)."
            })

        return recommendations


class TaxonomyNavigator:
    """
    Навигация по таксономии
    - Поиск путей между категориями
    - Поиск общего предка
    - Similarity scoring между категориями
    - Рекомендации связанных категорий
    """

    def __init__(self, taxonomy):
        self.taxonomy = taxonomy
        self.root = taxonomy.root

    def find_path_between(self, node1_path, node2_path):
        """Найти путь между двумя узлами"""
        node1 = self.taxonomy.nodes.get(node1_path)
        node2 = self.taxonomy.nodes.get(node2_path)

        if not node1 or not node2:
            return None

        # Найти общего предка
        ancestor = self.find_common_ancestor(node1, node2)
        if not ancestor:
            return None

        # Путь: node1 -> ancestor -> node2
        path_up = []
        current = node1
        while current and current != ancestor:
            path_up.append(current.name)
            current = current.parent

        path_down = []
        current = node2
        while current and current != ancestor:
            path_down.insert(0, current.name)
            current = current.parent

        full_path = path_up + [ancestor.name] + path_down
        return full_path

    def find_common_ancestor(self, node1, node2):
        """Найти ближайшего общего предка"""
        # Получить всех предков node1
        ancestors1 = set()
        current = node1
        while current:
            ancestors1.add(current)
            current = current.parent

        # Найти первого общего предка для node2
        current = node2
        while current:
            if current in ancestors1:
                return current
            current = current.parent

        return None

    def calculate_category_similarity(self, node1, node2):
        """Вычислить similarity score между категориями"""
        score = 0
        reasons = []

        # 1. Общий предок (чем ближе, тем выше score)
        ancestor = self.find_common_ancestor(node1, node2)
        if ancestor:
            # Расстояние от общего предка
            dist1 = self._distance_to_node(node1, ancestor)
            dist2 = self._distance_to_node(node2, ancestor)

            # Чем меньше расстояние, тем выше score
            ancestor_score = max(0, 10 - (dist1 + dist2))
            score += ancestor_score

            if ancestor != self.root:
                reasons.append(f"Общий предок: {ancestor.name} (расстояние: {dist1 + dist2})")

        # 2. Общие статьи (пересечение тегов)
        tags1 = self._collect_all_tags(node1)
        tags2 = self._collect_all_tags(node2)

        common_tags = tags1 & tags2
        if common_tags:
            tag_score = min(len(common_tags) * 2, 20)
            score += tag_score
            reasons.append(f"Общие теги: {len(common_tags)} ({', '.join(list(common_tags)[:3])})")

        # 3. Схожий размер
        count1 = node1.count_articles()
        count2 = node2.count_articles()

        if count1 > 0 and count2 > 0:
            ratio = min(count1, count2) / max(count1, count2)
            if ratio > 0.5:
                score += 5
                reasons.append(f"Схожий размер: {count1} vs {count2} статей")

        return {
            'score': score,
            'reasons': reasons
        }

    def _distance_to_node(self, node, target):
        """Расстояние от node до target"""
        distance = 0
        current = node
        while current and current != target:
            distance += 1
            current = current.parent
        return distance

    def _collect_all_tags(self, node):
        """Собрать все теги в поддереве"""
        tags = set()

        for article in node.articles:
            tags.update(article.get('tags', []))

        for child in node.children:
            tags.update(self._collect_all_tags(child))

        return tags

    def suggest_related_categories(self, node, max_suggestions=5):
        """Предложить связанные категории"""
        suggestions = []

        # Сравнить с другими узлами того же уровня
        for other_node in self.taxonomy.nodes.values():
            if other_node == node:
                continue

            # Сравнивать только узлы схожего уровня
            if abs(other_node.level - node.level) > 1:
                continue

            similarity = self.calculate_category_similarity(node, other_node)

            if similarity['score'] > 0:
                suggestions.append({
                    'category': other_node.get_path(),
                    'score': similarity['score'],
                    'reasons': similarity['reasons']
                })

        # Сортировать по score
        suggestions.sort(key=lambda x: -x['score'])
        return suggestions[:max_suggestions]


class HTMLTreeVisualizer:
    """
    HTML визуализация интерактивного дерева таксономии
    - Collapsible tree с JavaScript
    - Поиск по имени категории
    - Highlight выбранного пути
    - Статистика на hover
    - Color-coded по глубине/размеру
    """

    def __init__(self, taxonomy):
        self.taxonomy = taxonomy
        self.root = taxonomy.root

    def generate_html(self):
        """Сгенерировать полный HTML документ"""
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Интерактивная таксономия</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        h1 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}

        .subtitle {{
            color: #718096;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .search-box {{
            margin-bottom: 30px;
        }}

        .search-box input {{
            width: 100%;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            transition: border-color 0.3s;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .tree {{
            margin-top: 20px;
        }}

        .tree ul {{
            list-style: none;
            padding-left: 30px;
        }}

        .tree > ul {{
            padding-left: 0;
        }}

        .tree-node {{
            margin: 8px 0;
            position: relative;
        }}

        .tree-node-header {{
            cursor: pointer;
            padding: 10px 15px;
            border-radius: 8px;
            transition: all 0.3s;
            display: inline-block;
            user-select: none;
        }}

        .tree-node-header:hover {{
            background-color: #f7fafc;
            transform: translateX(5px);
        }}

        .tree-node-header.highlight {{
            background-color: #fef5e7;
            border-left: 4px solid #f59e0b;
        }}

        .tree-icon {{
            display: inline-block;
            width: 20px;
            text-align: center;
            margin-right: 8px;
            transition: transform 0.3s;
        }}

        .tree-icon.collapsed {{
            transform: rotate(-90deg);
        }}

        .tree-node-name {{
            font-weight: 600;
            color: #2d3748;
        }}

        .tree-node-count {{
            margin-left: 10px;
            color: #718096;
            font-size: 0.9em;
        }}

        .tree-children {{
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}

        .tree-children.collapsed {{
            max-height: 0 !important;
        }}

        .level-1 .tree-node-header {{ color: #2563eb; }}
        .level-2 .tree-node-header {{ color: #7c3aed; }}
        .level-3 .tree-node-header {{ color: #db2777; }}

        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}

            h1 {{
                font-size: 1.8em;
            }}

            .stats-bar {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌳 Интерактивная таксономия</h1>
        <p class="subtitle">Иерархическая структура базы знаний</p>

        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value">{self.root.count_articles()}</div>
                <div class="stat-label">Всего статей</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([n for n in self.taxonomy.nodes.values() if n.level == 1])}</div>
                <div class="stat-label">Категорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([n for n in self.taxonomy.nodes.values() if n.level == 2])}</div>
                <div class="stat-label">Подкатегорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([n for n in self.taxonomy.nodes.values() if n.level == 3])}</div>
                <div class="stat-label">Топиков</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Поиск категории...">
        </div>

        <div class="tree">
            {self._generate_tree_html(self.root)}
        </div>
    </div>

    <script>
        // Toggle node expansion
        function toggleNode(nodeId) {{
            const children = document.getElementById('children-' + nodeId);
            const icon = document.getElementById('icon-' + nodeId);

            if (children) {{
                children.classList.toggle('collapsed');
                icon.classList.toggle('collapsed');
            }}
        }}

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();
            const allNodes = document.querySelectorAll('.tree-node-header');

            allNodes.forEach(node => {{
                const text = node.textContent.toLowerCase();
                if (searchTerm && text.includes(searchTerm)) {{
                    node.classList.add('highlight');
                    // Expand parents
                    expandParents(node);
                }} else {{
                    node.classList.remove('highlight');
                }}
            }});
        }});

        function expandParents(element) {{
            let parent = element.parentElement;
            while (parent) {{
                if (parent.classList && parent.classList.contains('tree-children')) {{
                    parent.classList.remove('collapsed');
                    const nodeId = parent.id.replace('children-', '');
                    const icon = document.getElementById('icon-' + nodeId);
                    if (icon) {{
                        icon.classList.remove('collapsed');
                    }}
                }}
                parent = parent.parentElement;
            }}
        }}

        // Collapse all nodes initially (optional)
        // document.querySelectorAll('.tree-children').forEach(el => el.classList.add('collapsed'));
        // document.querySelectorAll('.tree-icon').forEach(el => el.classList.add('collapsed'));
    </script>
</body>
</html>"""
        return html

    def _generate_tree_html(self, node, node_id=0):
        """Рекурсивно генерировать HTML дерева"""
        if node == self.root:
            html = '<ul>'
            for i, child in enumerate(sorted(node.children, key=lambda x: x.name)):
                html += self._generate_tree_html(child, i)
            html += '</ul>'
            return html

        article_count = node.count_articles()

        # Иконка
        if node.children:
            icon = '▼'
        else:
            icon = '📄'

        html = f'<li class="tree-node level-{node.level}">'
        html += f'<div class="tree-node-header" onclick="toggleNode({node_id})">'
        html += f'<span class="tree-icon" id="icon-{node_id}">{icon}</span>'
        html += f'<span class="tree-node-name">{node.name}</span>'
        html += f'<span class="tree-node-count">({article_count})</span>'
        html += '</div>'

        if node.children:
            html += f'<ul class="tree-children" id="children-{node_id}">'
            for i, child in enumerate(sorted(node.children, key=lambda x: x.name)):
                child_id = node_id * 1000 + i
                html += self._generate_tree_html(child, child_id)
            html += '</ul>'

        html += '</li>'
        return html

    def save_html(self, output_file):
        """Сохранить HTML в файл"""
        html = self.generate_html()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML визуализация: {output_file}")


class TaxonomyEvolution:
    """
    Отслеживание эволюции таксономии во времени
    - Анализ git истории для отслеживания роста категорий
    - Определение новых/удалённых категорий
    - Timeline изменений таксономии
    """

    def __init__(self, taxonomy, root_dir):
        self.taxonomy = taxonomy
        self.root_dir = Path(root_dir)

    def get_git_history(self, days_back=90):
        """Получить историю коммитов за последние N дней"""
        try:
            # Получить список коммитов
            cmd = [
                'git', 'log',
                f'--since={days_back} days ago',
                '--pretty=format:%H|%ai|%s',
                '--', 'knowledge/'
            ]

            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 2)
                if len(parts) == 3:
                    commits.append({
                        'hash': parts[0],
                        'date': parts[1],
                        'message': parts[2]
                    })

            return commits

        except Exception as e:
            print(f"⚠️  Git история недоступна: {e}")
            return []

    def track_category_growth(self):
        """Отследить рост категорий по коммитам"""
        commits = self.get_git_history()

        if not commits:
            return {'error': 'Git история недоступна'}

        # Простая статистика
        timeline = []

        for commit in commits[:20]:  # Последние 20 коммитов
            # Получить файлы, изменённые в коммите
            try:
                cmd = ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit['hash']]
                result = subprocess.run(
                    cmd,
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                files = result.stdout.strip().split('\n')
                md_files = [f for f in files if f.startswith('knowledge/') and f.endswith('.md')]

                if md_files:
                    timeline.append({
                        'date': commit['date'][:10],
                        'message': commit['message'],
                        'files_changed': len(md_files)
                    })

            except:
                continue

        return {
            'total_commits': len(commits),
            'timeline': timeline[:10]
        }

    def generate_evolution_report(self):
        """Сгенерировать отчёт об эволюции"""
        growth = self.track_category_growth()

        lines = []
        lines.append("# 📈 Эволюция таксономии\n\n")
        lines.append("> Отслеживание изменений таксономии во времени\n\n")

        if 'error' in growth:
            lines.append(f"⚠️ {growth['error']}\n")
        else:
            lines.append(f"**Всего коммитов** (90 дней): {growth['total_commits']}\n\n")

            if growth['timeline']:
                lines.append("## Недавние изменения\n\n")
                for item in growth['timeline']:
                    lines.append(f"- **{item['date']}**: {item['message']} ({item['files_changed']} файлов)\n")

        return ''.join(lines)


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
    import argparse

    parser = argparse.ArgumentParser(
        description='🌳 Build Taxonomy - Иерархическая таксономия базы знаний',
        epilog='''Примеры:
  build_taxonomy.py                       # Построить базовую таксономию
  build_taxonomy.py --stats               # С детальной статистикой
  build_taxonomy.py --html tree.html      # Интерактивное HTML дерево
  build_taxonomy.py --evolution           # Анализ эволюции через git
  build_taxonomy.py --all                 # Всё вместе
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--json', metavar='FILE',
                       help='Экспорт таксономии в JSON')
    parser.add_argument('--html', metavar='FILE',
                       help='Генерировать интерактивное HTML дерево')
    parser.add_argument('--stats', action='store_true',
                       help='Детальная статистика (глубина, баланс, orphans)')
    parser.add_argument('--evolution', action='store_true',
                       help='Анализ эволюции таксономии (git history)')
    parser.add_argument('--recommendations', action='store_true',
                       help='Рекомендации по реорганизации')
    parser.add_argument('--all', action='store_true',
                       help='Генерировать все форматы + все анализы')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Построить таксономию
    taxonomy = Taxonomy(root_dir)
    taxonomy.build()

    # Вывести базовую структуру
    print("🌳 Иерархическая структура:\n")
    taxonomy.print_tree()

    # Базовая статистика
    print("\n📊 Базовая статистика:")
    stats = taxonomy.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    print()

    # Сохранить базовые форматы
    print("📝 Сохранение базовой таксономии...\n")
    taxonomy.save_tree_markdown(root_dir / "TAXONOMY.md")
    taxonomy.save_json(root_dir / "taxonomy.json")
    taxonomy.save_mermaid(root_dir / "TAXONOMY_DIAGRAM.md")

    # Детальная статистика
    if args.stats or args.all:
        print("\n📊 Детальная статистика:\n")

        stats_analyzer = TaxonomyStatistics(taxonomy)

        # Анализ глубины
        print("🔍 Анализ глубины:")
        depth_analysis = stats_analyzer.analyze_depth()
        print(f"   Максимальная глубина: {depth_analysis['max_depth']}")
        print(f"   Средняя глубина: {depth_analysis['avg_depth']:.2f}")

        print("\n   По веткам:")
        for branch, info in depth_analysis['by_branch'].items():
            print(f"      {branch}: max={info['max_depth']}, avg={info['avg_depth']:.2f}")

        # Анализ баланса
        print("\n🔍 Анализ баланса:")
        balance = stats_analyzer.analyze_balance()
        if balance['is_balanced']:
            print("   ✅ Дерево сбалансировано")
        else:
            print(f"   ⚠️  Дерево несбалансировано (score: {balance['imbalance_score']})")
            for issue in balance['issues']:
                print(f"      - {issue}")

        # Orphan categories
        orphans = stats_analyzer.find_orphan_categories()
        print(f"\n🔍 Orphan categories (с 1 статьёй): {len(orphans)}")
        if orphans:
            for orphan in orphans[:5]:
                print(f"      - {orphan['path']}")
            if len(orphans) > 5:
                print(f"      ... и ещё {len(orphans) - 5}")

        # Overpopulated categories
        overpopulated = stats_analyzer.find_overpopulated_categories()
        print(f"\n🔍 Overpopulated categories (>50 статей): {len(overpopulated)}")
        if overpopulated:
            for cat in overpopulated[:5]:
                print(f"      - {cat['path']}: {cat['article_count']} статей")
            if len(overpopulated) > 5:
                print(f"      ... и ещё {len(overpopulated) - 5}")

    # Рекомендации
    if args.recommendations or args.all:
        print("\n💡 Рекомендации по реорганизации:\n")

        stats_analyzer = TaxonomyStatistics(taxonomy)
        recommendations = stats_analyzer.generate_recommendations()

        if not recommendations:
            print("   ✅ Нет рекомендаций - таксономия в отличном состоянии!")
        else:
            for rec in recommendations:
                severity_icon = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
                icon = severity_icon.get(rec['severity'], '•')
                print(f"   {icon} {rec['message']}")

    # HTML визуализация
    if args.html or args.all:
        html_file = args.html if args.html else root_dir / "taxonomy_interactive.html"
        print("\n🎨 Генерация интерактивного HTML...\n")

        visualizer = HTMLTreeVisualizer(taxonomy)
        visualizer.save_html(html_file)

    # Эволюция
    if args.evolution or args.all:
        print("\n📈 Анализ эволюции таксономии...\n")

        evolution = TaxonomyEvolution(taxonomy, root_dir)
        growth = evolution.track_category_growth()

        if 'error' in growth:
            print(f"   ⚠️  {growth['error']}")
        else:
            print(f"   Всего коммитов (90 дней): {growth['total_commits']}")

            if growth['timeline']:
                print("\n   Недавние изменения:")
                for item in growth['timeline'][:5]:
                    print(f"      - {item['date']}: {item['message'][:60]}... ({item['files_changed']} файлов)")

        # Сохранить отчёт
        evolution_md = evolution.generate_evolution_report()
        evolution_file = root_dir / "TAXONOMY_EVOLUTION.md"

        with open(evolution_file, 'w', encoding='utf-8') as f:
            f.write(evolution_md)

        print(f"\n   ✅ Отчёт об эволюции: {evolution_file}")

    # JSON экспорт
    if args.json:
        print(f"\n📦 Экспорт в JSON...\n")
        taxonomy.save_json(args.json)

    print("\n✨ Таксономия готова!")

    if not any([args.stats, args.html, args.evolution, args.recommendations, args.all]):
        print("\n💡 Дополнительные опции:")
        print("   --stats              # Детальная статистика")
        print("   --html tree.html     # Интерактивное HTML дерево")
        print("   --evolution          # Анализ эволюции через git")
        print("   --recommendations    # Рекомендации по реорганизации")
        print("   --all                # Всё вместе")


if __name__ == "__main__":
    main()
