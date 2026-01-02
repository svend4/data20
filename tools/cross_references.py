#!/usr/bin/env python3
"""
Advanced Cross-References - Умная система перекрестных ссылок
Создаёт продвинутую систему "См.", "См. также", "Сравните с", "Prerequisite"

Возможности:
- Automatic "See" inference (редиректы для синонимов)
- "See also" scoring (релевантность 0-100)
- Bidirectional cross-references (A→B автоматически создаёт B→A)
- Context-aware suggestions (на основе категорий, тегов, prerequisites)
- Cross-reference types: see_also, compare_with, contrast_with, prerequisite
- Circular reference detection (A→B→C→A)
- Cross-reference strength (strong/medium/weak)
- Interactive HTML visualization
- Quality metrics

Вдохновлено: Wikipedia "See also", Encyclopedia cross-references, Academic citations
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import argparse
from datetime import datetime


class AdvancedCrossReferencesBuilder:
    """Продвинутый построитель перекрестных ссылок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Перекрестные ссылки с типами и силой связи
        self.xrefs = defaultdict(lambda: {
            'see': None,  # Редирект на главную статью
            'see_also': [],  # {target, score, strength}
            'compare_with': [],  # Сравните с
            'contrast_with': [],  # Контрастирует с
            'prerequisite': [],  # Требуемые знания
            'related_by': [],  # Обратные ссылки
        })

        # Статьи
        self.articles = {}

        # Синонимы (для "См.")
        self.synonyms = defaultdict(set)

        # Статистика
        self.stats = {
            'total_articles': 0,
            'see_redirects': 0,
            'see_also': 0,
            'bidirectional': 0,
            'circular_refs': 0,
            'quality_score': 0.0,
        }

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и контент"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None

    def calculate_text_similarity(self, text1, text2):
        """Jaccard similarity для текстов"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def calculate_xref_score(self, article1_path, article2_path):
        """
        Вычислить score перекрестной ссылки (0-100)
        На основе: общих тегов, категории, текста, prerequisites
        """
        art1 = self.articles[article1_path]
        art2 = self.articles[article2_path]

        score = 0.0

        # 1. Общие теги (0-40)
        tags1 = set(art1['tags'])
        tags2 = set(art2['tags'])
        common_tags = tags1 & tags2
        if tags1 and tags2:
            tag_score = len(common_tags) / max(len(tags1), len(tags2)) * 40
            score += tag_score

        # 2. Та же категория (0-20)
        if art1['category'] == art2['category']:
            score += 20
            # Та же подкатегория (бонус +10)
            if art1['subcategory'] == art2['subcategory'] and art1['subcategory']:
                score += 10

        # 3. Similarity текста (0-20)
        text_sim = self.calculate_text_similarity(art1.get('content', ''), art2.get('content', ''))
        score += text_sim * 20

        # 4. Prerequisites (0-10)
        prereqs1 = set(art1.get('prerequisites', []))
        if article2_path in prereqs1:
            score += 10

        return min(100.0, score)

    def determine_xref_strength(self, score):
        """Определить силу связи: strong/medium/weak"""
        if score >= 70:
            return 'strong'
        elif score >= 40:
            return 'medium'
        else:
            return 'weak'

    def detect_synonyms(self):
        """
        Обнаружить синонимы (дубликаты, альтернативные названия)
        Используется для "См." redirects
        """
        articles_list = list(self.articles.items())

        for i, (path1, art1) in enumerate(articles_list):
            for path2, art2 in articles_list[i+1:]:
                title1 = art1['title'].lower()
                title2 = art2['title'].lower()

                # Одинаковые слова в названиях
                words1 = set(re.findall(r'\b\w+\b', title1))
                words2 = set(re.findall(r'\b\w+\b', title2))

                common = words1 & words2
                union = words1 | words2

                # Similarity > 0.6 = вероятно синонимы
                if len(union) > 0:
                    sim = len(common) / len(union)
                    if sim > 0.6:
                        self.synonyms[path1].add(path2)
                        self.synonyms[path2].add(path1)

    def build_see_redirects(self):
        """
        Построить "См." redirects
        Короткие/устаревшие статьи → основные статьи
        """
        for path, synonyms in self.synonyms.items():
            if not synonyms:
                continue

            art = self.articles[path]
            content_len = len(art.get('content', ''))

            # Найти самую длинную статью среди синонимов
            main_article = max(
                synonyms,
                key=lambda p: len(self.articles[p].get('content', '')),
                default=None
            )

            if main_article:
                main_len = len(self.articles[main_article].get('content', ''))

                # Если текущая статья значительно короче - редирект
                if content_len < main_len * 0.3:
                    self.xrefs[path]['see'] = main_article
                    self.stats['see_redirects'] += 1

    def build_xrefs(self):
        """Построить все перекрестные ссылки"""
        print("🔗 Построение продвинутых перекрестных ссылок...\n")

        # Загрузить все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            self.articles[article_path] = {
                'title': frontmatter.get('title', md_file.stem),
                'tags': frontmatter.get('tags', []),
                'category': frontmatter.get('category', ''),
                'subcategory': frontmatter.get('subcategory', ''),
                'prerequisites': frontmatter.get('prerequisites', []),
                'content': content if content else '',
            }

        self.stats['total_articles'] = len(self.articles)

        # Обработка синонимов и redirects
        self.detect_synonyms()
        self.build_see_redirects()

        # Построить перекрестные ссылки между всеми статьями
        articles_list = list(self.articles.keys())

        for i, article1 in enumerate(articles_list):
            # Пропустить если есть redirect
            if self.xrefs[article1]['see']:
                continue

            art1 = self.articles[article1]

            for article2 in articles_list[i+1:]:
                if self.xrefs[article2]['see']:
                    continue

                # Вычислить score
                score = self.calculate_xref_score(article1, article2)

                # Пропустить слабые связи
                if score < 15:
                    continue

                strength = self.determine_xref_strength(score)

                # Определить тип связи
                xref_type = 'see_also'  # По умолчанию

                art2 = self.articles[article2]

                # Prerequisites
                if article2 in art1.get('prerequisites', []):
                    xref_type = 'prerequisite'
                    self.xrefs[article1]['prerequisite'].append({
                        'target': article2,
                        'score': score,
                        'strength': strength,
                    })
                    continue

                # Compare with (та же категория, высокий score)
                if art1['category'] == art2['category'] and score >= 60:
                    xref_type = 'compare_with'
                    self.xrefs[article1]['compare_with'].append({
                        'target': article2,
                        'score': score,
                        'strength': strength,
                    })

                # See also
                self.xrefs[article1]['see_also'].append({
                    'target': article2,
                    'score': score,
                    'strength': strength,
                })

                # Bidirectional (создать обратную ссылку)
                self.xrefs[article2]['see_also'].append({
                    'target': article1,
                    'score': score,
                    'strength': strength,
                })
                self.xrefs[article2]['related_by'].append(article1)

                self.stats['bidirectional'] += 1

        # Подсчёт ссылок
        for path, xrefs in self.xrefs.items():
            if xrefs['see_also']:
                self.stats['see_also'] += 1

        # Сортировка по score (топ-N)
        for path in self.xrefs:
            for xref_type in ['see_also', 'compare_with', 'prerequisite']:
                self.xrefs[path][xref_type].sort(key=lambda x: -x['score'])
                self.xrefs[path][xref_type] = self.xrefs[path][xref_type][:5]  # Топ-5

        print(f"   Статей: {self.stats['total_articles']}")
        print(f"   См. (redirects): {self.stats['see_redirects']}")
        print(f"   См. также: {self.stats['see_also']}")
        print(f"   Bidirectional: {self.stats['bidirectional']}")
        print()

    def detect_circular_references(self):
        """Обнаружить циклические ссылки (A→B→C→A)"""
        circular = []

        def dfs_detect_cycle(start, current, visited, path):
            if current == start and len(path) > 1:
                circular.append(path.copy())
                return

            if current in visited and len(path) > 1:
                return

            visited.add(current)

            # Проверить все "see_also" и "prerequisite"
            for xref in self.xrefs[current].get('see_also', []):
                target = xref['target']
                if target not in visited or target == start:
                    dfs_detect_cycle(start, target, visited.copy(), path + [target])

        for article in self.articles.keys():
            dfs_detect_cycle(article, article, set(), [article])

        self.stats['circular_refs'] = len(circular)
        return circular

    def calculate_quality_metrics(self):
        """Вычислить метрики качества cross-references"""
        total = len(self.articles)
        if total == 0:
            return

        # Coverage: сколько статей имеют хотя бы 1 cross-ref
        with_xrefs = sum(
            1 for x in self.xrefs.values()
            if x['see_also'] or x['compare_with'] or x['prerequisite']
        )

        coverage = (with_xrefs / total) * 100 if total > 0 else 0

        # Avg score
        all_scores = []
        for xrefs in self.xrefs.values():
            for ref_list in [xrefs['see_also'], xrefs['compare_with'], xrefs['prerequisite']]:
                all_scores.extend(r['score'] for r in ref_list)

        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        # Overall quality
        quality = (coverage * 0.6 + avg_score * 0.4)
        self.stats['quality_score'] = quality

        return {
            'coverage_pct': coverage,
            'avg_score': avg_score,
            'quality_overall': quality,
        }

    def generate_markdown_report(self, output_file='CROSS_REFERENCES_REPORT.md'):
        """Создать детальный Markdown отчёт"""
        lines = []
        lines.append("# 🔗 Отчёт: Продвинутые перекрестные ссылки\n\n")
        lines.append(f"> Создан {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        # Статистика
        lines.append("## 📊 Статистика\n\n")
        lines.append(f"- **Всего статей**: {self.stats['total_articles']}\n")
        lines.append(f"- **См. (redirects)**: {self.stats['see_redirects']}\n")
        lines.append(f"- **См. также**: {self.stats['see_also']}\n")
        lines.append(f"- **Bidirectional связей**: {self.stats['bidirectional']}\n")
        lines.append(f"- **Циклических ссылок**: {self.stats['circular_refs']}\n")

        quality = self.calculate_quality_metrics()
        if quality:
            lines.append(f"\n### Качество\n\n")
            lines.append(f"- **Coverage**: {quality['coverage_pct']:.1f}%\n")
            lines.append(f"- **Avg Score**: {quality['avg_score']:.1f}/100\n")
            lines.append(f"- **Quality Overall**: {quality['quality_overall']:.1f}/100\n")

        lines.append("\n---\n\n")

        # Примеры по типам
        lines.append("## 📚 Примеры по типам\n\n")

        # См. (redirects)
        lines.append("### См. (Redirects)\n\n")
        redirect_examples = [p for p, x in self.xrefs.items() if x['see']][:5]
        for path in redirect_examples:
            target = self.xrefs[path]['see']
            lines.append(f"- **{self.articles[path]['title']}** → *См.* **{self.articles[target]['title']}**\n")
        lines.append("\n")

        # Сильные связи
        lines.append("### Сильные связи (score ≥ 70)\n\n")
        strong_links = []
        for path, xrefs in self.xrefs.items():
            for ref in xrefs['see_also']:
                if ref['strength'] == 'strong':
                    strong_links.append((path, ref['target'], ref['score']))

        for source, target, score in sorted(strong_links, key=lambda x: -x[2])[:10]:
            lines.append(f"- **{self.articles[source]['title']}** ↔ **{self.articles[target]['title']}** ({score:.1f})\n")
        lines.append("\n")

        # Prerequisites
        lines.append("### Prerequisites\n\n")
        prereq_examples = [(p, x) for p, x in self.xrefs.items() if x['prerequisite']][:5]
        for path, xrefs in prereq_examples:
            lines.append(f"**{self.articles[path]['title']}** требует:\n")
            for prereq in xrefs['prerequisite']:
                lines.append(f"- {self.articles[prereq['target']]['title']}\n")
            lines.append("\n")

        # Circular references
        if self.stats['circular_refs'] > 0:
            lines.append("### ⚠️ Циклические ссылки\n\n")
            circular = self.detect_circular_references()
            for cycle in circular[:5]:
                cycle_titles = [self.articles[p]['title'] for p in cycle]
                lines.append(f"- {' → '.join(cycle_titles)} → ...\n")
            lines.append("\n")

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown отчёт: {output_path}")

    def export_to_json(self, output_file='cross_references.json'):
        """Полный JSON экспорт"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.stats,
            'quality_metrics': self.calculate_quality_metrics(),
            'cross_references': {}
        }

        for path, xrefs in self.xrefs.items():
            data['cross_references'][path] = {
                'title': self.articles[path]['title'],
                'see': xrefs['see'],
                'see_also': xrefs['see_also'],
                'compare_with': xrefs['compare_with'],
                'contrast_with': xrefs['contrast_with'],
                'prerequisite': xrefs['prerequisite'],
                'related_by': xrefs['related_by'],
            }

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON экспорт: {output_path}")

    def generate_html_visualization(self, output_file='cross_references_map.html'):
        """Интерактивная HTML визуализация сети cross-references"""
        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cross-References Network</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card h3 {
            font-size: 1.8em;
            margin-bottom: 5px;
        }
        .stat-card p {
            opacity: 0.9;
            font-size: 0.9em;
        }
        .search-box {
            margin: 20px 0;
            text-align: center;
        }
        .search-box input {
            width: 60%;
            padding: 10px;
            font-size: 16px;
            border: 2px solid #667eea;
            border-radius: 5px;
        }
        .xref-list {
            margin-top: 20px;
        }
        .xref-item {
            margin: 15px 0;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }
        .xref-title {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }
        .xref-refs {
            margin-top: 10px;
        }
        .xref-ref {
            display: inline-block;
            margin: 5px;
            padding: 5px 10px;
            background: #667eea;
            color: white;
            border-radius: 15px;
            font-size: 0.9em;
        }
        .xref-ref.strong { background: #e53935; }
        .xref-ref.medium { background: #ff9800; }
        .xref-ref.weak { background: #9e9e9e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Cross-References Network</h1>

        <div class="stats">
            <div class="stat-card">
                <h3>""" + str(self.stats['total_articles']) + """</h3>
                <p>Статей</p>
            </div>
            <div class="stat-card">
                <h3>""" + str(self.stats['see_also']) + """</h3>
                <p>См. также</p>
            </div>
            <div class="stat-card">
                <h3>""" + str(self.stats['bidirectional']) + """</h3>
                <p>Bidirectional</p>
            </div>
            <div class="stat-card">
                <h3>""" + f"{self.stats['quality_score']:.0f}" + """</h3>
                <p>Quality Score</p>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Поиск по статьям..." onkeyup="filterItems()">
        </div>

        <div class="xref-list" id="xrefList">
"""

        # Топ-20 статей с cross-references
        articles_with_xrefs = [
            (p, x) for p, x in self.xrefs.items()
            if x['see_also'] or x['prerequisite'] or x['compare_with']
        ]

        # Сортировка по количеству ссылок
        articles_with_xrefs.sort(
            key=lambda x: len(x[1]['see_also']) + len(x[1]['prerequisite']) + len(x[1]['compare_with']),
            reverse=True
        )

        for path, xrefs in articles_with_xrefs[:20]:
            title = self.articles[path]['title']
            html += f'            <div class="xref-item" data-title="{title.lower()}">\n'
            html += f'                <div class="xref-title">{title}</div>\n'
            html += '                <div class="xref-refs">\n'

            # Prerequisites
            for prereq in xrefs.get('prerequisite', []):
                target_title = self.articles[prereq['target']]['title']
                html += f'                    <span class="xref-ref prerequisite" title="Prerequisite">📚 {target_title}</span>\n'

            # Compare with
            for comp in xrefs.get('compare_with', []):
                target_title = self.articles[comp['target']]['title']
                html += f'                    <span class="xref-ref compare" title="Compare">⚖️ {target_title}</span>\n'

            # See also
            for ref in xrefs.get('see_also', [])[:5]:
                target_title = self.articles[ref['target']]['title']
                strength_class = ref['strength']
                html += f'                    <span class="xref-ref {strength_class}" title="{ref["score"]:.0f}/100">{target_title}</span>\n'

            html += '                </div>\n'
            html += '            </div>\n'

        html += """        </div>
    </div>

    <script>
        function filterItems() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const items = document.querySelectorAll('.xref-item');

            items.forEach(item => {
                const title = item.getAttribute('data-title');
                if (title.includes(filter)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML визуализация: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Продвинутая система перекрестных ссылок'
    )
    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Создать Markdown отчёт'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Экспортировать в JSON'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Создать HTML визуализацию'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = AdvancedCrossReferencesBuilder(root_dir)
    builder.build_xrefs()

    # Экспорты
    if args.markdown or not any([args.json, args.html]):
        builder.generate_markdown_report()

    if args.json:
        builder.export_to_json()

    if args.html:
        builder.generate_html_visualization()

    # По умолчанию - всё
    if not any([args.markdown, args.json, args.html]):
        builder.export_to_json()
        builder.generate_html_visualization()

    print("\n✅ Перекрестные ссылки построены!")


if __name__ == "__main__":
    main()
