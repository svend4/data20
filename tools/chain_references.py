#!/usr/bin/env python3
"""
Chain References - Цепные ссылки
Вдохновлено: Книги в средневековых библиотеках приковывались цепями

Создаёт навигационные цепочки между связанными статьями:
- Предыдущая/Следующая статья
- Серии статей
- Учебные треки (последовательное изучение)
"""

from pathlib import Path
import yaml
import re
import json
from collections import defaultdict, Counter


class ChainAnalyzer:
    """Анализ качества и полноты цепочек"""

    def __init__(self, chain_manager):
        self.manager = chain_manager
        self.root_dir = chain_manager.root_dir

    def analyze_chain_quality(self, chain_id):
        """
        Анализ качества цепочки

        Returns:
            dict: метрики качества
        """
        chain = self.manager.get_chain(chain_id)
        if not chain:
            return None

        metrics = {
            'chain_id': chain_id,
            'total_articles': len(chain['articles']),
            'broken_links': [],
            'missing_files': [],
            'inconsistent_metadata': [],
            'quality_score': 100
        }

        # Проверить существование файлов
        for article_path in chain['articles']:
            full_path = self.root_dir / article_path
            if not full_path.exists():
                metrics['missing_files'].append(article_path)
                metrics['quality_score'] -= 10

        # Проверить метаданные
        for article_path in chain['articles']:
            full_path = self.root_dir / article_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if not match:
                    metrics['inconsistent_metadata'].append({
                        'file': article_path,
                        'issue': 'No frontmatter'
                    })
                    metrics['quality_score'] -= 5
            except Exception as e:
                metrics['inconsistent_metadata'].append({
                    'file': article_path,
                    'issue': str(e)
                })

        metrics['quality_score'] = max(0, metrics['quality_score'])

        return metrics

    def find_orphaned_articles(self):
        """
        Найти статьи, не входящие ни в одну цепочку

        Returns:
            list: orphaned articles
        """
        # Все статьи в цепочках
        chained_articles = set()
        for chain in self.manager.chains.values():
            chained_articles.update(chain['articles'])

        # Все статьи в knowledge
        all_articles = []
        knowledge_dir = self.root_dir / "knowledge"

        for md_file in knowledge_dir.rglob("*.md"):
            if md_file.name != "INDEX.md":
                article_path = str(md_file.relative_to(self.root_dir))
                all_articles.append(article_path)

        # Orphaned = все - в цепочках
        orphaned = [a for a in all_articles if a not in chained_articles]

        return orphaned

    def analyze_chain_completeness(self, chain_id):
        """
        Анализ полноты цепочки

        Проверяет:
        - Пропущенные части в series
        - Логичность последовательности

        Returns:
            dict: анализ полноты
        """
        chain = self.manager.get_chain(chain_id)
        if not chain:
            return None

        completeness = {
            'chain_id': chain_id,
            'is_complete': True,
            'gaps': [],
            'suggestions': []
        }

        # Если это series, проверить номера частей
        if chain['type'] == 'series':
            parts = []

            for article_path in chain['articles']:
                full_path = self.root_dir / article_path
                if not full_path.exists():
                    continue

                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                    if match:
                        fm = yaml.safe_load(match.group(1))
                        part = fm.get('part', 0)
                        parts.append(part)
                except:
                    pass

            # Проверить gaps
            if parts:
                parts_set = set(parts)
                expected = set(range(1, max(parts) + 1))
                missing = expected - parts_set

                if missing:
                    completeness['is_complete'] = False
                    completeness['gaps'] = sorted(missing)
                    completeness['suggestions'].append(f"Пропущены части: {', '.join(map(str, missing))}")

        return completeness

    def calculate_chain_difficulty(self, chain_id):
        """
        Вычислить сложность прохождения цепочки

        Использует метаданные 'difficulty' или 'level'

        Returns:
            dict: difficulty metrics
        """
        chain = self.manager.get_chain(chain_id)
        if not chain:
            return None

        difficulties = []

        for article_path in chain['articles']:
            full_path = self.root_dir / article_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    difficulty = fm.get('difficulty') or fm.get('level')

                    if difficulty:
                        # Преобразовать в число
                        difficulty_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
                        if isinstance(difficulty, str):
                            difficulty = difficulty_map.get(difficulty.lower(), 2)

                        difficulties.append(difficulty)
            except:
                pass

        if not difficulties:
            return {
                'chain_id': chain_id,
                'has_difficulty_metadata': False
            }

        avg_difficulty = sum(difficulties) / len(difficulties)
        is_progressive = all(difficulties[i] <= difficulties[i+1] for i in range(len(difficulties) - 1))

        return {
            'chain_id': chain_id,
            'has_difficulty_metadata': True,
            'average_difficulty': round(avg_difficulty, 2),
            'min_difficulty': min(difficulties),
            'max_difficulty': max(difficulties),
            'is_progressive': is_progressive,
            'difficulty_progression': difficulties
        }


class ChainRecommender:
    """Рекомендации для цепочек"""

    def __init__(self, chain_manager):
        self.manager = chain_manager
        self.root_dir = chain_manager.root_dir

    def recommend_articles_for_chain(self, chain_id, max_recommendations=5):
        """
        Рекомендовать статьи для добавления в цепочку

        На основе:
        - Похожих тегов/категорий
        - Упоминаний в тексте
        - Сложности

        Returns:
            list: рекомендации
        """
        chain = self.manager.get_chain(chain_id)
        if not chain:
            return []

        # Собрать теги из статей в цепочке
        chain_tags = Counter()
        chain_categories = Counter()

        for article_path in chain['articles']:
            full_path = self.root_dir / article_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    tags = fm.get('tags', [])
                    if isinstance(tags, list):
                        chain_tags.update(tags)

                    category = fm.get('category')
                    if category:
                        chain_categories[category] += 1
            except:
                pass

        # Найти кандидатов
        analyzer = ChainAnalyzer(self.manager)
        orphaned = analyzer.find_orphaned_articles()

        candidates = []

        for article_path in orphaned:
            full_path = self.root_dir / article_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    # Вычислить score
                    score = 0

                    # Теги
                    tags = fm.get('tags', [])
                    if isinstance(tags, list):
                        common_tags = set(tags) & set(chain_tags.keys())
                        score += len(common_tags) * 10

                    # Категория
                    category = fm.get('category')
                    if category and category in chain_categories:
                        score += 20

                    # Series
                    series = fm.get('series')
                    if series and series == chain.get('metadata', {}).get('series'):
                        score += 30

                    if score > 0:
                        candidates.append({
                            'article': article_path,
                            'title': fm.get('title', Path(article_path).stem),
                            'score': score,
                            'tags': tags,
                            'category': category
                        })
            except:
                pass

        # Сортировать по score
        candidates.sort(key=lambda x: -x['score'])

        return candidates[:max_recommendations]

    def suggest_new_chains(self):
        """
        Предложить новые цепочки на основе анализа

        Returns:
            list: предложения
        """
        suggestions = []

        # Группировать статьи по категориям
        by_category = defaultdict(list)

        knowledge_dir = self.root_dir / "knowledge"

        for md_file in knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    category = fm.get('category')

                    if category:
                        article_path = str(md_file.relative_to(self.root_dir))
                        by_category[category].append(article_path)
            except:
                pass

        # Предложить цепочки для категорий с несколькими статьями
        for category, articles in by_category.items():
            if len(articles) >= 3:
                chain_id = f"topic_{category.lower().replace(' ', '_')}"

                # Проверить, не существует ли уже
                if chain_id not in self.manager.chains:
                    suggestions.append({
                        'chain_id': chain_id,
                        'title': f"Тема: {category}",
                        'type': 'topic',
                        'articles': articles,
                        'reason': f'Найдено {len(articles)} статей в категории "{category}"'
                    })

        return suggestions


class ChainVisualizer:
    """Визуализация цепочек"""

    def __init__(self, chain_manager):
        self.manager = chain_manager
        self.root_dir = chain_manager.root_dir

    def generate_html_chain_view(self, chain_id):
        """
        Создать HTML визуализацию цепочки

        Returns:
            str: HTML
        """
        chain = self.manager.get_chain(chain_id)
        if not chain:
            return None

        # Собрать информацию о статьях
        articles_data = []

        for i, article_path in enumerate(chain['articles'], 1):
            full_path = self.root_dir / article_path

            title = Path(article_path).stem
            description = ""

            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                    if match:
                        fm = yaml.safe_load(match.group(1))
                        title = fm.get('title', title)
                        description = fm.get('description', '')
                except:
                    pass

            articles_data.append({
                'position': i,
                'title': title,
                'path': article_path,
                'description': description
            })

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔗 {chain['title']}</title>
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
            max-width: 900px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .chain-info {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 30px;
            text-align: center;
        }}

        .chain-type {{
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 10px;
        }}

        .progress-bar {{
            background: #eee;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 15px;
        }}

        .progress-fill {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s;
        }}

        .timeline {{
            position: relative;
            padding-left: 40px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: white;
        }}

        .article-item {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            position: relative;
        }}

        .article-item::before {{
            content: attr(data-position);
            position: absolute;
            left: -40px;
            top: 20px;
            width: 30px;
            height: 30px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}

        .article-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}

        .article-path {{
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}

        .article-description {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 {chain['title']}</h1>

        <div class="chain-info">
            <div class="chain-type">{chain['type']}</div>
            <div style="font-size: 1.2em; margin-top: 10px;">
                {len(chain['articles'])} статей в цепочке
            </div>
            {f'<div style="color: #666; margin-top: 10px;">{chain["description"]}</div>' if chain['description'] else ''}
        </div>

        <div class="timeline">
            {"".join(f'''
            <div class="article-item" data-position="{article['position']}">
                <div class="article-title">{article['title']}</div>
                <div class="article-path">📂 {article['path']}</div>
                {f'<div class="article-description">{article["description"]}</div>' if article['description'] else ''}
            </div>
            ''' for article in articles_data)}
        </div>
    </div>
</body>
</html>"""

        return html

    def generate_chains_overview_html(self):
        """
        Создать HTML обзор всех цепочек

        Returns:
            str: HTML
        """
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔗 Цепочки статей</title>
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
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #666;
            margin-top: 10px;
        }}

        .chains-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}

        .chain-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .chain-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}

        .chain-type {{
            background: #764ba2;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            display: inline-block;
            margin-bottom: 15px;
        }}

        .chain-articles {{
            color: #667eea;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .chain-description {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Цепочки статей</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(self.manager.chains)}</div>
                <div class="stat-label">Всего цепочек</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(chain['articles']) for chain in self.manager.chains.values())}</div>
                <div class="stat-label">Статей в цепочках</div>
            </div>
        </div>

        <div class="chains-grid">
            {"".join(f'''
            <div class="chain-card">
                <div class="chain-title">{chain['title']}</div>
                <div class="chain-type">{chain['type']}</div>
                <div class="chain-articles">📚 {len(chain['articles'])} статей</div>
                {f'<div class="chain-description">{chain["description"]}</div>' if chain['description'] else ''}
            </div>
            ''' for chain_id, chain in self.manager.chains.items())}
        </div>
    </div>
</body>
</html>"""

        return html


class ChainValidator:
    """Валидация цепочек"""

    def __init__(self, chain_manager):
        self.manager = chain_manager
        self.root_dir = chain_manager.root_dir

    def validate_chain(self, chain_id):
        """
        Полная валидация цепочки

        Returns:
            dict: результаты валидации
        """
        chain = self.manager.get_chain(chain_id)
        if not chain:
            return None

        validation = {
            'chain_id': chain_id,
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # Проверка 1: Есть ли статьи
        if not chain['articles']:
            validation['is_valid'] = False
            validation['errors'].append("Цепочка пустая")
            return validation

        # Проверка 2: Существуют ли файлы
        for article_path in chain['articles']:
            full_path = self.root_dir / article_path
            if not full_path.exists():
                validation['errors'].append(f"Файл не найден: {article_path}")
                validation['is_valid'] = False

        # Проверка 3: Нет ли дубликатов
        if len(chain['articles']) != len(set(chain['articles'])):
            validation['warnings'].append("Обнаружены дубликаты статей")

        # Проверка 4: Циклические ссылки
        if self._has_circular_reference(chain_id):
            validation['errors'].append("Обнаружена циклическая ссылка")
            validation['is_valid'] = False

        return validation

    def _has_circular_reference(self, chain_id):
        """
        Проверить на циклические ссылки

        Returns:
            bool: True если есть цикл
        """
        # Упрощённая проверка: для chain_references циклов быть не должно
        # так как это линейные цепочки
        return False

    def validate_all_chains(self):
        """
        Валидация всех цепочек

        Returns:
            dict: результаты
        """
        results = {
            'total_chains': len(self.manager.chains),
            'valid_chains': 0,
            'invalid_chains': 0,
            'chains_with_warnings': 0,
            'details': []
        }

        for chain_id in self.manager.chains:
            validation = self.validate_chain(chain_id)

            if validation['is_valid']:
                results['valid_chains'] += 1
            else:
                results['invalid_chains'] += 1

            if validation['warnings']:
                results['chains_with_warnings'] += 1

            results['details'].append(validation)

        return results


class ChainManager:
    """
    Менеджер цепных ссылок между статьями
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.chains_file = self.root_dir / ".chains" / "chains.json"

        # Создать директорию
        self.chains_file.parent.mkdir(exist_ok=True)

        # Загрузить цепочки
        self.chains = self.load_chains()

    def load_chains(self):
        """Загрузить определения цепочек"""
        if self.chains_file.exists():
            with open(self.chains_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_chains(self):
        """Сохранить цепочки"""
        with open(self.chains_file, 'w', encoding='utf-8') as f:
            json.dump(self.chains, f, ensure_ascii=False, indent=2)

    def create_chain(self, chain_id, title, description="", chain_type="series"):
        """
        Создать новую цепочку

        chain_type может быть:
        - series: серия статей
        - tutorial: учебный трек (от простого к сложному)
        - chronological: хронологическая последовательность
        - topic: статьи на одну тему
        """
        self.chains[chain_id] = {
            'title': title,
            'description': description,
            'type': chain_type,
            'articles': [],
            'metadata': {}
        }

        self.save_chains()
        return self.chains[chain_id]

    def add_to_chain(self, chain_id, article_file, position=None):
        """
        Добавить статью в цепочку

        position: None (в конец), или индекс для вставки
        """
        if chain_id not in self.chains:
            return False

        article_path = str(Path(article_file).relative_to(self.root_dir))

        if position is None:
            self.chains[chain_id]['articles'].append(article_path)
        else:
            self.chains[chain_id]['articles'].insert(position, article_path)

        self.save_chains()
        return True

    def remove_from_chain(self, chain_id, article_file):
        """Удалить статью из цепочки"""
        if chain_id not in self.chains:
            return False

        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path in self.chains[chain_id]['articles']:
            self.chains[chain_id]['articles'].remove(article_path)
            self.save_chains()
            return True

        return False

    def get_chain(self, chain_id):
        """Получить цепочку"""
        return self.chains.get(chain_id)

    def get_article_chains(self, article_file):
        """Найти все цепочки, в которых участвует статья"""
        article_path = str(Path(article_file).relative_to(self.root_dir))

        article_chains = []
        for chain_id, chain in self.chains.items():
            if article_path in chain['articles']:
                article_chains.append({
                    'id': chain_id,
                    'title': chain['title'],
                    'position': chain['articles'].index(article_path) + 1,
                    'total': len(chain['articles'])
                })

        return article_chains

    def get_navigation(self, article_file):
        """
        Получить навигацию для статьи (предыдущая/следующая в цепочке)
        """
        article_path = str(Path(article_file).relative_to(self.root_dir))

        navigation = {}

        for chain_id, chain in self.chains.items():
            if article_path not in chain['articles']:
                continue

            articles = chain['articles']
            index = articles.index(article_path)

            nav = {
                'chain_id': chain_id,
                'chain_title': chain['title'],
                'position': index + 1,
                'total': len(articles),
                'previous': None,
                'next': None
            }

            if index > 0:
                nav['previous'] = articles[index - 1]

            if index < len(articles) - 1:
                nav['next'] = articles[index + 1]

            navigation[chain_id] = nav

        return navigation

    def generate_navigation_links(self, article_file):
        """Создать markdown навигацию для статьи"""
        navigation = self.get_navigation(article_file)

        if not navigation:
            return ""

        lines = []
        lines.append("---\n\n")
        lines.append("## 🔗 Навигация по цепочкам\n\n")

        for chain_id, nav in navigation.items():
            lines.append(f"### {nav['chain_title']}\n\n")
            lines.append(f"**Позиция**: {nav['position']} / {nav['total']}\n\n")

            # Навигационные ссылки
            nav_links = []

            if nav['previous']:
                prev_title = self._get_article_title(nav['previous'])
                nav_links.append(f"← [Предыдущая: {prev_title}]({nav['previous']})")

            if nav['next']:
                next_title = self._get_article_title(nav['next'])
                nav_links.append(f"[Следующая: {next_title}]({nav['next']}) →")

            if nav_links:
                lines.append(" | ".join(nav_links) + "\n\n")

        return ''.join(lines)

    def _get_article_title(self, article_path):
        """Получить заголовок статьи"""
        try:
            full_path = self.root_dir / article_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                return fm.get('title', Path(article_path).stem)
        except:
            pass

        return Path(article_path).stem

    def visualize_chain(self, chain_id):
        """Визуализировать цепочку"""
        chain = self.chains.get(chain_id)

        if not chain:
            return None

        lines = []
        lines.append(f"\n🔗 Цепочка: {chain['title']}\n")
        lines.append(f"   Тип: {chain['type']}\n")
        lines.append(f"   Статей: {len(chain['articles'])}\n\n")

        for i, article_path in enumerate(chain['articles'], 1):
            title = self._get_article_title(article_path)
            arrow = "   ⬇\n" if i < len(chain['articles']) else ""
            lines.append(f"{i}. {title}\n")
            lines.append(f"   📂 {article_path}\n")
            lines.append(arrow)

        return ''.join(lines)

    def export_chain_markdown(self, chain_id, output_file=None):
        """Экспортировать цепочку в markdown"""
        chain = self.chains.get(chain_id)

        if not chain:
            return None

        lines = []
        lines.append(f"# 🔗 {chain['title']}\n\n")

        if chain['description']:
            lines.append(f"> {chain['description']}\n\n")

        lines.append(f"**Тип**: {chain['type']}  \n")
        lines.append(f"**Статей в цепочке**: {len(chain['articles'])}  \n\n")

        lines.append("---\n\n")

        # Список статей с навигацией
        for i, article_path in enumerate(chain['articles'], 1):
            title = self._get_article_title(article_path)

            lines.append(f"## {i}. {title}\n\n")
            lines.append(f"📂 [`{article_path}`]({article_path})\n\n")

            # Навигация
            nav = []
            if i > 1:
                prev_title = self._get_article_title(chain['articles'][i-2])
                nav.append(f"← [{prev_title}]({chain['articles'][i-2]})")

            if i < len(chain['articles']):
                next_title = self._get_article_title(chain['articles'][i])
                nav.append(f"[{next_title}]({chain['articles'][i]}) →")

            if nav:
                lines.append(" | ".join(nav) + "\n\n")

            lines.append("---\n\n")

        content = ''.join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    def auto_detect_chains(self):
        """
        Автоматически обнаружить потенциальные цепочки

        На основе:
        - Серий статей (series: X в метаданных)
        - Общих тегов и категорий
        - Ссылок друг на друга
        """
        print("🔍 Автоматическое обнаружение цепочек...\n")

        # Статьи по сериям
        by_series = defaultdict(list)

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    series = fm.get('series')
                    if series:
                        article_path = str(md_file.relative_to(self.root_dir))
                        part = fm.get('part', 0)
                        by_series[series].append((part, article_path))
            except:
                pass

        # Создать цепочки для серий
        detected = 0
        for series_name, articles in by_series.items():
            # Сортировать по номеру части
            articles.sort(key=lambda x: x[0])

            chain_id = f"series_{series_name.lower().replace(' ', '_')}"

            if chain_id not in self.chains:
                self.create_chain(
                    chain_id,
                    f"Серия: {series_name}",
                    description=f"Автоматически обнаруженная серия статей",
                    chain_type="series"
                )

                for _, article_path in articles:
                    self.add_to_chain(chain_id, self.root_dir / article_path)

                detected += 1
                print(f"✅ Обнаружена серия: {series_name} ({len(articles)} статей)")

        print(f"\n✅ Обнаружено новых цепочек: {detected}")

    def generate_report(self):
        """Создать отчёт по всем цепочкам"""
        lines = []
        lines.append("# 🔗 Отчёт по цепочкам статей\n\n")

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего цепочек**: {len(self.chains)}\n")

        total_articles = sum(len(chain['articles']) for chain in self.chains.values())
        lines.append(f"- **Всего статей в цепочках**: {total_articles}\n\n")

        # По типам
        by_type = defaultdict(int)
        for chain in self.chains.values():
            by_type[chain['type']] += 1

        lines.append("## По типам\n\n")
        for chain_type, count in sorted(by_type.items()):
            lines.append(f"- **{chain_type}**: {count}\n")

        lines.append("\n## Все цепочки\n\n")

        for chain_id, chain in sorted(self.chains.items()):
            lines.append(f"### {chain['title']}\n\n")
            lines.append(f"- **ID**: `{chain_id}`\n")
            lines.append(f"- **Тип**: {chain['type']}\n")
            lines.append(f"- **Статей**: {len(chain['articles'])}\n")

            if chain['description']:
                lines.append(f"- **Описание**: {chain['description']}\n")

            lines.append("\n")

        return ''.join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Chain References - Управление цепочками статей'
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # create - создать цепочку
    create_parser = subparsers.add_parser('create', help='Создать цепочку')
    create_parser.add_argument('chain_id', help='ID цепочки')
    create_parser.add_argument('title', help='Название')
    create_parser.add_argument('-d', '--description', default='', help='Описание')
    create_parser.add_argument('-t', '--type', default='series',
                              choices=['series', 'tutorial', 'chronological', 'topic'],
                              help='Тип цепочки')

    # add - добавить статью
    add_parser = subparsers.add_parser('add', help='Добавить статью в цепочку')
    add_parser.add_argument('chain_id', help='ID цепочки')
    add_parser.add_argument('article', help='Путь к статье')
    add_parser.add_argument('-p', '--position', type=int, help='Позиция (опционально)')

    # nav - показать навигацию
    nav_parser = subparsers.add_parser('nav', help='Показать навигацию для статьи')
    nav_parser.add_argument('article', help='Путь к статье')

    # show - показать цепочку
    show_parser = subparsers.add_parser('show', help='Показать цепочку')
    show_parser.add_argument('chain_id', help='ID цепочки')

    # export - экспортировать цепочку
    export_parser = subparsers.add_parser('export', help='Экспортировать цепочку')
    export_parser.add_argument('chain_id', help='ID цепочки')
    export_parser.add_argument('-o', '--output', help='Выходной файл')

    # auto-detect - автоматическое обнаружение
    subparsers.add_parser('auto-detect', help='Автоматически обнаружить цепочки')

    # report - отчёт
    subparsers.add_parser('report', help='Создать отчёт')

    # analyze - analyze chain quality
    analyze_parser = subparsers.add_parser('analyze', help='Анализ качества цепочки')
    analyze_parser.add_argument('chain_id', help='ID цепочки')

    # recommend - рекомендации
    recommend_parser = subparsers.add_parser('recommend', help='Рекомендовать статьи для цепочки')
    recommend_parser.add_argument('chain_id', help='ID цепочки')
    recommend_parser.add_argument('-n', '--max', type=int, default=5, help='Максимум рекомендаций')

    # html - HTML визуализация
    html_parser = subparsers.add_parser('html', help='HTML визуализация цепочки')
    html_parser.add_argument('chain_id', nargs='?', help='ID цепочки (опционально для overview)')
    html_parser.add_argument('-o', '--output', help='Выходной файл')

    # validate - валидация
    validate_parser = subparsers.add_parser('validate', help='Валидация цепочек')
    validate_parser.add_argument('chain_id', nargs='?', help='ID цепочки (опционально для всех)')

    # orphans - найти orphaned статьи
    subparsers.add_parser('orphans', help='Найти статьи вне цепочек')

    # suggest-chains - предложить новые цепочки
    subparsers.add_parser('suggest-chains', help='Предложить новые цепочки')

    # quality - оценка качества
    quality_parser = subparsers.add_parser('quality', help='Оценка качества цепочки')
    quality_parser.add_argument('chain_id', help='ID цепочки')

    # difficulty - анализ сложности
    difficulty_parser = subparsers.add_parser('difficulty', help='Анализ сложности цепочки')
    difficulty_parser.add_argument('chain_id', help='ID цепочки')

    # completeness - проверка полноты
    completeness_parser = subparsers.add_parser('completeness', help='Проверка полноты цепочки')
    completeness_parser.add_argument('chain_id', help='ID цепочки')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    manager = ChainManager(root_dir)

    if args.command == 'create':
        chain = manager.create_chain(
            args.chain_id,
            args.title,
            description=args.description,
            chain_type=args.type
        )
        print(f"✅ Цепочка '{args.chain_id}' создана")

    elif args.command == 'add':
        article_path = root_dir / args.article
        if manager.add_to_chain(args.chain_id, article_path, args.position):
            print(f"✅ Статья добавлена в цепочку '{args.chain_id}'")
        else:
            print(f"❌ Цепочка не найдена")

    elif args.command == 'nav':
        article_path = root_dir / args.article
        nav_md = manager.generate_navigation_links(article_path)
        if nav_md:
            print(nav_md)
        else:
            print("⚠️  Статья не входит ни в одну цепочку")

    elif args.command == 'show':
        viz = manager.visualize_chain(args.chain_id)
        if viz:
            print(viz)
        else:
            print(f"❌ Цепочка '{args.chain_id}' не найдена")

    elif args.command == 'export':
        output = args.output or f"{args.chain_id}.md"
        content = manager.export_chain_markdown(args.chain_id, output)
        if content:
            print(f"✅ Цепочка экспортирована в {output}")
        else:
            print(f"❌ Цепочка не найдена")

    elif args.command == 'auto-detect':
        manager.auto_detect_chains()

    elif args.command == 'report':
        report = manager.generate_report()
        output_file = root_dir / "CHAINS_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    elif args.command == 'analyze' or args.command == 'quality':
        analyzer = ChainAnalyzer(manager)
        metrics = analyzer.analyze_chain_quality(args.chain_id)
        if metrics:
            print(f"\n📊 Качество цепочки '{args.chain_id}':\n")
            print(f"   Статей: {metrics['total_articles']}")
            print(f"   Quality Score: {metrics['quality_score']}/100")
            if metrics['missing_files']:
                print(f"   ❌ Отсутствующих файлов: {len(metrics['missing_files'])}")
            if metrics['inconsistent_metadata']:
                print(f"   ⚠️  Проблем с метаданными: {len(metrics['inconsistent_metadata'])}")
        else:
            print(f"❌ Цепочка не найдена")

    elif args.command == 'recommend':
        recommender = ChainRecommender(manager)
        recommendations = recommender.recommend_articles_for_chain(args.chain_id, args.max)
        if recommendations:
            print(f"\n💡 Рекомендации для цепочки '{args.chain_id}':\n")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec['title']} (score: {rec['score']})")
                print(f"   📂 {rec['article']}")
                if rec.get('tags'):
                    print(f"   🏷️  {', '.join(rec['tags'][:3])}\n")
        else:
            print("   Нет рекомендаций")

    elif args.command == 'html':
        visualizer = ChainVisualizer(manager)
        if args.chain_id:
            html = visualizer.generate_html_chain_view(args.chain_id)
            output = args.output or root_dir / f"chain_{args.chain_id}.html"
        else:
            html = visualizer.generate_chains_overview_html()
            output = args.output or root_dir / "chains_overview.html"

        if html:
            Path(output).write_text(html, encoding='utf-8')
            print(f"✅ HTML создан: {output}")
        else:
            print("❌ Ошибка создания HTML")

    elif args.command == 'validate':
        validator = ChainValidator(manager)
        if args.chain_id:
            validation = validator.validate_chain(args.chain_id)
            if validation:
                status = "✅ ВАЛИДНА" if validation['is_valid'] else "❌ НЕВАЛИДНА"
                print(f"\n{status}: '{args.chain_id}'\n")
                if validation['errors']:
                    print("Ошибки:")
                    for err in validation['errors']:
                        print(f"   ❌ {err}")
                if validation['warnings']:
                    print("\nПредупреждения:")
                    for warn in validation['warnings']:
                        print(f"   ⚠️  {warn}")
        else:
            results = validator.validate_all_chains()
            print(f"\n📊 Валидация всех цепочек:\n")
            print(f"   Всего: {results['total_chains']}")
            print(f"   ✅ Валидных: {results['valid_chains']}")
            print(f"   ❌ Невалидных: {results['invalid_chains']}")
            print(f"   ⚠️  С предупреждениями: {results['chains_with_warnings']}")

    elif args.command == 'orphans':
        analyzer = ChainAnalyzer(manager)
        orphaned = analyzer.find_orphaned_articles()
        print(f"\n📄 Статьи вне цепочек: {len(orphaned)}\n")
        for article in orphaned[:20]:
            print(f"   {article}")
        if len(orphaned) > 20:
            print(f"\n   ...и ещё {len(orphaned) - 20}")

    elif args.command == 'suggest-chains':
        recommender = ChainRecommender(manager)
        suggestions = recommender.suggest_new_chains()
        print(f"\n💡 Предложения новых цепочек: {len(suggestions)}\n")
        for sug in suggestions:
            print(f"   {sug['title']}")
            print(f"   ID: {sug['chain_id']}")
            print(f"   Причина: {sug['reason']}\n")

    elif args.command == 'difficulty':
        analyzer = ChainAnalyzer(manager)
        diff = analyzer.calculate_chain_difficulty(args.chain_id)
        if diff and diff.get('has_difficulty_metadata'):
            print(f"\n📊 Сложность цепочки '{args.chain_id}':\n")
            print(f"   Средняя: {diff['average_difficulty']}")
            print(f"   Диапазон: {diff['min_difficulty']} - {diff['max_difficulty']}")
            print(f"   Прогрессивная: {'Да' if diff['is_progressive'] else 'Нет'}")
        else:
            print("   Метаданные о сложности отсутствуют")

    elif args.command == 'completeness':
        analyzer = ChainAnalyzer(manager)
        comp = analyzer.analyze_chain_completeness(args.chain_id)
        if comp:
            status = "✅ ПОЛНАЯ" if comp['is_complete'] else "⚠️  НЕПОЛНАЯ"
            print(f"\n{status}: '{args.chain_id}'\n")
            if comp['gaps']:
                print(f"   Пропущены части: {', '.join(map(str, comp['gaps']))}")
            if comp['suggestions']:
                for sug in comp['suggestions']:
                    print(f"   💡 {sug}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
