#!/usr/bin/env python3
"""
Backlinks Generator - Генератор обратных ссылок
Автоматически добавляет секцию "Кто ссылается на эту статью"

Вдохновлено: Wikipedia backlinks, Roam Research bidirectional links
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import argparse
from typing import Dict, List, Tuple, Set
import math


class BacklinkAnalyzer:
    """Анализатор метрик обратных ссылок"""

    def __init__(self, backlinks: Dict, articles: Dict):
        self.backlinks = backlinks
        self.articles = articles

    def calculate_citation_strength(self, article_path: str) -> float:
        """Вычислить силу цитирования (учитывает количество и качество)"""
        if article_path not in self.backlinks:
            return 0.0

        backlinks = self.backlinks[article_path]
        if not backlinks:
            return 0.0

        # Базовое количество
        count_score = len(backlinks)

        # Бонус за разнообразие источников (категории/директории)
        sources = set()
        for bl in backlinks:
            source_dir = Path(bl['source']).parent
            sources.add(str(source_dir))

        diversity_bonus = len(sources) / len(backlinks) if backlinks else 0

        # Финальная оценка
        return count_score * (1 + diversity_bonus)

    def get_backlink_distribution(self) -> Dict[int, int]:
        """Распределение: сколько статей имеют N обратных ссылок"""
        distribution = Counter()

        # Все статьи, включая те, у которых 0 backlinks
        for article_path in self.articles:
            count = len(self.backlinks.get(article_path, []))
            distribution[count] += 1

        return dict(sorted(distribution.items()))

    def find_citation_hubs(self, min_backlinks: int = 5) -> List[Tuple[str, int]]:
        """Найти статьи-хабы (на них много ссылаются)"""
        hubs = []

        for article_path, backlinks in self.backlinks.items():
            if len(backlinks) >= min_backlinks:
                hubs.append((article_path, len(backlinks)))

        return sorted(hubs, key=lambda x: -x[1])

    def calculate_citation_network_density(self) -> float:
        """Плотность сети цитирования: actual_links / max_possible_links"""
        n = len(self.articles)
        if n <= 1:
            return 0.0

        max_possible = n * (n - 1)  # Направленный граф
        actual_links = sum(len(links) for links in self.backlinks.values())

        return actual_links / max_possible if max_possible > 0 else 0.0

    def get_mutual_citations(self) -> List[Tuple[str, str]]:
        """Найти взаимные цитирования (A→B и B→A)"""
        mutual = []

        # Построить forward links из backlinks
        forward_links = defaultdict(set)
        for target, backlinks in self.backlinks.items():
            for bl in backlinks:
                forward_links[bl['source']].add(target)

        # Найти взаимные
        checked = set()
        for article_a in forward_links:
            for article_b in forward_links[article_a]:
                if article_a in forward_links.get(article_b, set()):
                    pair = tuple(sorted([article_a, article_b]))
                    if pair not in checked:
                        mutual.append(pair)
                        checked.add(pair)

        return mutual


class BacklinkScorer:
    """Оценка важности обратных ссылок"""

    def __init__(self, backlinks: Dict, articles: Dict):
        self.backlinks = backlinks
        self.articles = articles

    def score_backlink(self, backlink: Dict) -> float:
        """Оценить важность одной обратной ссылки"""
        score = 1.0

        # Фактор 1: Контекст ссылки (длина текста)
        context = backlink.get('context', '')
        if context:
            context_len = len(context)
            if context_len > 50:
                score *= 1.5  # Длинный контекст = важная ссылка
            elif context_len > 20:
                score *= 1.2
            elif context_len < 10:
                score *= 0.8  # Короткий контекст = менее важная

        # Фактор 2: Источник имеет много исходящих ссылок?
        # (если статья ссылается на всё подряд, каждая ссылка менее ценна)
        source_path = backlink['source']
        source_outgoing = 0

        for _, backlinks_list in self.backlinks.items():
            source_outgoing += sum(1 for bl in backlinks_list if bl['source'] == source_path)

        if source_outgoing > 0:
            # Penalty за большое количество исходящих ссылок
            penalty = 1 / math.sqrt(source_outgoing)
            score *= penalty

        return score

    def get_weighted_backlinks(self, article_path: str) -> List[Tuple[Dict, float]]:
        """Получить обратные ссылки с весами (отсортированы по важности)"""
        if article_path not in self.backlinks:
            return []

        weighted = []
        for backlink in self.backlinks[article_path]:
            score = self.score_backlink(backlink)
            weighted.append((backlink, score))

        return sorted(weighted, key=lambda x: -x[1])

    def calculate_authority_score(self, article_path: str) -> float:
        """Authority score: сумма весов входящих ссылок"""
        weighted = self.get_weighted_backlinks(article_path)
        return sum(score for _, score in weighted)


class BrokenBacklinksDetector:
    """Детектор сломанных/некорректных обратных ссылок"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.knowledge_dir = root_dir / "knowledge"

    def check_backlinks(self, backlinks: Dict, articles: Dict) -> Dict[str, List[Dict]]:
        """Проверить все обратные ссылки на корректность"""
        issues = defaultdict(list)

        for target_path, backlinks_list in backlinks.items():
            # Проверка 1: Целевой файл существует?
            if target_path not in articles:
                issues['missing_targets'].append({
                    'target': target_path,
                    'backlinks_count': len(backlinks_list)
                })
                continue

            target_file = articles[target_path]['file']
            if not target_file.exists():
                issues['missing_files'].append({
                    'target': target_path,
                    'file': str(target_file)
                })

            # Проверка 2: Источники существуют?
            for backlink in backlinks_list:
                source_path = backlink['source']
                if source_path not in articles:
                    issues['missing_sources'].append({
                        'source': source_path,
                        'target': target_path
                    })
                    continue

                source_file = articles[source_path]['file']
                if not source_file.exists():
                    issues['missing_source_files'].append({
                        'source': source_path,
                        'target': target_path,
                        'file': str(source_file)
                    })

        return dict(issues)

    def find_orphaned_articles(self, backlinks: Dict, articles: Dict) -> List[str]:
        """Найти статьи-сироты (нет входящих И исходящих ссылок)"""
        orphaned = []

        # Статьи с исходящими ссылками
        has_outgoing = set()
        for _, backlinks_list in backlinks.items():
            for bl in backlinks_list:
                has_outgoing.add(bl['source'])

        # Проверить каждую статью
        for article_path in articles:
            has_incoming = article_path in backlinks and len(backlinks[article_path]) > 0
            has_out = article_path in has_outgoing

            if not has_incoming and not has_out:
                orphaned.append(article_path)

        return sorted(orphaned)


class BacklinksGenerator:
    """Генератор обратных ссылок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Граф ссылок
        self.backlinks = defaultdict(list)
        self.articles = {}

        # Анализаторы
        self.analyzer = None
        self.scorer = None
        self.broken_detector = None

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return match.group(1), match.group(2)
        except:
            pass
        return None, None

    def build_backlinks_graph(self):
        """Построить граф обратных ссылок"""
        print("🔗 Построение графа обратных ссылок...\n")

        # Собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter_str, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            # Парсинг frontmatter для заголовка
            if frontmatter_str:
                try:
                    frontmatter = yaml.safe_load(frontmatter_str)
                    title = frontmatter.get('title', md_file.stem)
                except:
                    title = md_file.stem
            else:
                title = md_file.stem

            self.articles[article_path] = {
                'title': title,
                'file': md_file
            }

        # Построить граф ссылок
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            source_path = str(md_file.relative_to(self.root_dir))
            source_title = self.articles[source_path]['title']

            # Извлечь все markdown ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for link_text, link_url in links:
                # Пропустить внешние ссылки
                if link_url.startswith('http'):
                    continue

                # Пропустить якорные ссылки
                if link_url.startswith('#'):
                    continue

                try:
                    # Разрешить относительный путь
                    target = (md_file.parent / link_url.split('#')[0]).resolve()

                    if target.exists() and target.is_relative_to(self.root_dir):
                        target_path = str(target.relative_to(self.root_dir))

                        # Добавить обратную ссылку
                        if target_path in self.articles:
                            self.backlinks[target_path].append({
                                'source': source_path,
                                'title': source_title,
                                'context': link_text
                            })
                except:
                    pass

        print(f"   Статей обработано: {len(self.articles)}")
        print(f"   Обратных ссылок: {sum(len(links) for links in self.backlinks.values())}\n")

        # Инициализировать анализаторы
        self.analyzer = BacklinkAnalyzer(self.backlinks, self.articles)
        self.scorer = BacklinkScorer(self.backlinks, self.articles)
        self.broken_detector = BrokenBacklinksDetector(self.root_dir)

    def generate_backlinks_section(self, article_path):
        """Создать секцию обратных ссылок"""
        if article_path not in self.backlinks:
            return ""

        backlinks = self.backlinks[article_path]

        if not backlinks:
            return ""

        lines = []
        lines.append("\n---\n\n")
        lines.append("## 🔗 Обратные ссылки\n\n")
        lines.append(f"> Эту статью цитируют {len(backlinks)} статей:\n\n")

        for backlink in backlinks:
            # Вычислить относительный путь
            article_file = self.articles[article_path]['file']
            source_file = self.articles[backlink['source']]['file']

            try:
                rel_path = source_file.relative_to(article_file.parent)
            except:
                rel_path = backlink['source']

            lines.append(f"- [{backlink['title']}]({rel_path})")

            if backlink['context']:
                lines.append(f" — *\"{backlink['context']}\"*")

            lines.append("\n")

        return ''.join(lines)

    def update_article(self, article_path):
        """Обновить статью с обратными ссылками"""
        article_file = self.articles[article_path]['file']

        frontmatter_str, content = self.extract_frontmatter_and_content(article_file)

        if not content:
            return False

        # Удалить существующую секцию обратных ссылок
        # Ищем "## 🔗 Обратные ссылки" до конца файла
        content = re.sub(
            r'\n---\s*\n+##\s*🔗\s*Обратные ссылки.*',
            '',
            content,
            flags=re.DOTALL
        )

        # Также удалить старые варианты
        content = re.sub(
            r'\n---\s*\n+##\s*Обратные ссылки.*',
            '',
            content,
            flags=re.DOTALL
        )

        # Добавить новую секцию
        backlinks_section = self.generate_backlinks_section(article_path)

        if backlinks_section:
            content += backlinks_section

        # Собрать файл
        full_content = f"---\n{frontmatter_str}\n---\n\n{content}"

        # Записать
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return bool(backlinks_section)

    def update_all(self, dry_run=False):
        """Обновить все статьи"""
        print("✍️  Обновление статей...\n")

        updated = 0
        skipped = 0

        for article_path in self.articles:
            if article_path in self.backlinks and self.backlinks[article_path]:
                if not dry_run:
                    if self.update_article(article_path):
                        updated += 1
                        print(f"   ✅ {article_path} ({len(self.backlinks[article_path])} обратных ссылок)")
                else:
                    print(f"   [DRY RUN] {article_path} — будет добавлено {len(self.backlinks[article_path])} обратных ссылок")
                    updated += 1
            else:
                skipped += 1

        print(f"\n✅ Обновлено статей: {updated}")
        print(f"⏭️  Пропущено (нет обратных ссылок): {skipped}")

    def run_analysis(self):
        """Провести полный анализ обратных ссылок"""
        if not self.analyzer:
            print("⚠️  Сначала постройте граф (build_backlinks_graph)")
            return

        print("\n📊 Анализ обратных ссылок\n")

        # 1. Распределение
        distribution = self.analyzer.get_backlink_distribution()
        print("Распределение обратных ссылок:")
        for count, articles in sorted(distribution.items())[:10]:
            print(f"   {count} ссылок: {articles} статей")
        if len(distribution) > 10:
            print(f"   ... (всего {len(distribution)} уникальных значений)")

        # 2. Плотность сети
        density = self.analyzer.calculate_citation_network_density()
        print(f"\nПлотность сети цитирования: {density:.4f}")
        print(f"   ({density*100:.2f}% от максимально возможных связей)")

        # 3. Хабы
        hubs = self.analyzer.find_citation_hubs(min_backlinks=3)
        if hubs:
            print(f"\n🎯 Топ-5 статей-хабов:")
            for article_path, count in hubs[:5]:
                title = self.articles[article_path]['title']
                strength = self.analyzer.calculate_citation_strength(article_path)
                print(f"   • {title}")
                print(f"     Ссылок: {count}, Сила цитирования: {strength:.2f}")

        # 4. Взаимные цитирования
        mutual = self.analyzer.get_mutual_citations()
        if mutual:
            print(f"\n↔️  Взаимных цитирований: {len(mutual)}")
            for a, b in mutual[:3]:
                title_a = self.articles[a]['title']
                title_b = self.articles[b]['title']
                print(f"   • {title_a} ↔ {title_b}")
            if len(mutual) > 3:
                print(f"   ... и ещё {len(mutual) - 3}")

    def check_broken_links(self):
        """Проверить сломанные ссылки"""
        if not self.broken_detector:
            print("⚠️  Сначала постройте граф (build_backlinks_graph)")
            return

        print("\n🔍 Проверка целостности ссылок\n")

        issues = self.broken_detector.check_backlinks(self.backlinks, self.articles)

        if not issues:
            print("✅ Проблем не найдено!")
        else:
            for issue_type, items in issues.items():
                print(f"\n⚠️  {issue_type}: {len(items)}")
                for item in items[:5]:
                    print(f"   • {item}")
                if len(items) > 5:
                    print(f"   ... и ещё {len(items) - 5}")

        # Статьи-сироты
        orphaned = self.broken_detector.find_orphaned_articles(self.backlinks, self.articles)
        if orphaned:
            print(f"\n🏝️  Статьи-сироты (нет связей): {len(orphaned)}")
            for article_path in orphaned[:10]:
                title = self.articles[article_path]['title']
                print(f"   • {title}")
            if len(orphaned) > 10:
                print(f"   ... и ещё {len(orphaned) - 10}")

    def export_json(self, output_file: str = "backlinks.json"):
        """Экспортировать в JSON"""
        data = {
            'metadata': {
                'total_articles': len(self.articles),
                'total_backlinks': sum(len(links) for links in self.backlinks.values()),
                'articles_with_backlinks': len([a for a in self.backlinks.values() if a])
            },
            'articles': {},
            'backlinks': {}
        }

        # Статьи
        for article_path, info in self.articles.items():
            data['articles'][article_path] = {
                'title': info['title'],
                'file': str(info['file'])
            }

        # Обратные ссылки
        for article_path, backlinks in self.backlinks.items():
            data['backlinks'][article_path] = [
                {
                    'source': bl['source'],
                    'title': bl['title'],
                    'context': bl['context']
                }
                for bl in backlinks
            ]

        # Метрики (если анализатор доступен)
        if self.analyzer:
            data['metrics'] = {
                'distribution': self.analyzer.get_backlink_distribution(),
                'network_density': self.analyzer.calculate_citation_network_density(),
                'hubs': [
                    {'article': path, 'backlinks': count}
                    for path, count in self.analyzer.find_citation_hubs(min_backlinks=1)[:20]
                ],
                'mutual_citations': [
                    {'article_a': a, 'article_b': b}
                    for a, b in self.analyzer.get_mutual_citations()
                ]
            }

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ JSON экспорт: {output_path}")

    def export_html(self, output_file: str = "backlinks.html"):
        """Экспортировать в HTML"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='ru'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("  <title>Граф обратных ссылок</title>")
        html.append("  <style>")
        html.append("    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; background: #f5f5f5; }")
        html.append("    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }")
        html.append("    h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }")
        html.append("    h2 { color: #555; margin-top: 30px; }")
        html.append("    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }")
        html.append("    .stat-card { background: #f9f9f9; padding: 20px; border-radius: 6px; border-left: 4px solid #4CAF50; }")
        html.append("    .stat-value { font-size: 32px; font-weight: bold; color: #4CAF50; }")
        html.append("    .stat-label { color: #777; font-size: 14px; }")
        html.append("    .article { margin: 15px 0; padding: 15px; background: #fafafa; border-radius: 6px; }")
        html.append("    .article-title { font-weight: bold; color: #333; margin-bottom: 5px; }")
        html.append("    .backlinks { margin-left: 20px; }")
        html.append("    .backlink-item { margin: 5px 0; color: #666; }")
        html.append("    .backlink-context { font-style: italic; color: #999; font-size: 14px; }")
        html.append("    .badge { display: inline-block; background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("  <div class='container'>")
        html.append("    <h1>🔗 Граф обратных ссылок</h1>")

        # Статистика
        total_backlinks = sum(len(links) for links in self.backlinks.values())
        articles_with_backlinks = len([a for a in self.backlinks.values() if a])

        html.append("    <div class='stats'>")
        html.append(f"      <div class='stat-card'><div class='stat-value'>{len(self.articles)}</div><div class='stat-label'>Всего статей</div></div>")
        html.append(f"      <div class='stat-card'><div class='stat-value'>{total_backlinks}</div><div class='stat-label'>Обратных ссылок</div></div>")
        html.append(f"      <div class='stat-card'><div class='stat-value'>{articles_with_backlinks}</div><div class='stat-label'>Статей с ссылками</div></div>")

        if self.analyzer:
            density = self.analyzer.calculate_citation_network_density()
            html.append(f"      <div class='stat-card'><div class='stat-value'>{density*100:.1f}%</div><div class='stat-label'>Плотность сети</div></div>")

        html.append("    </div>")

        # Статьи с обратными ссылками
        html.append("    <h2>Статьи с обратными ссылками</h2>")

        sorted_articles = sorted(
            [(path, links) for path, links in self.backlinks.items() if links],
            key=lambda x: -len(x[1])
        )

        for article_path, backlinks in sorted_articles:
            title = self.articles[article_path]['title']
            count = len(backlinks)

            html.append(f"    <div class='article'>")
            html.append(f"      <div class='article-title'>{title} <span class='badge'>{count}</span></div>")
            html.append(f"      <div class='backlinks'>")

            for bl in backlinks[:10]:
                html.append(f"        <div class='backlink-item'>← {bl['title']}")
                if bl['context']:
                    html.append(f" <span class='backlink-context'>\"{bl['context']}\"</span>")
                html.append("</div>")

            if len(backlinks) > 10:
                html.append(f"        <div class='backlink-item'>... и ещё {len(backlinks) - 10}</div>")

            html.append("      </div>")
            html.append("    </div>")

        html.append("  </div>")
        html.append("</body>")
        html.append("</html>")

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))

        print(f"\n✅ HTML экспорт: {output_path}")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Отчёт: Обратные ссылки\n\n")
        lines.append("> Карта цитирований между статьями\n\n")

        # Статистика
        total_backlinks = sum(len(links) for links in self.backlinks.values())
        articles_with_backlinks = len([a for a in self.backlinks.values() if a])

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Статей с обратными ссылками**: {articles_with_backlinks}\n")
        lines.append(f"- **Всего обратных ссылок**: {total_backlinks}\n")

        # Дополнительные метрики
        if self.analyzer:
            density = self.analyzer.calculate_citation_network_density()
            lines.append(f"- **Плотность сети цитирования**: {density:.4f} ({density*100:.2f}%)\n")

            mutual = self.analyzer.get_mutual_citations()
            if mutual:
                lines.append(f"- **Взаимных цитирований**: {len(mutual)}\n")

            orphaned = self.broken_detector.find_orphaned_articles(self.backlinks, self.articles)
            if orphaned:
                lines.append(f"- **Статей-сирот** (нет связей): {len(orphaned)}\n")

        lines.append("\n")

        # Топ цитируемых
        lines.append("## Топ-10 самых цитируемых\n\n")

        sorted_articles = sorted(
            self.backlinks.items(),
            key=lambda x: -len(x[1])
        )

        for i, (article_path, backlinks) in enumerate(sorted_articles[:10], 1):
            if not backlinks:
                break

            title = self.articles[article_path]['title']

            lines.append(f"### {i}. {title}\n\n")
            lines.append(f"- **Файл**: [{article_path}]({article_path})\n")
            lines.append(f"- **Обратных ссылок**: {len(backlinks)}\n\n")

            lines.append("**Цитируют:**\n")
            for backlink in backlinks[:5]:
                lines.append(f"- [{backlink['title']}]({backlink['source']})")
                if backlink['context']:
                    lines.append(f" — *\"{backlink['context']}\"*")
                lines.append("\n")

            if len(backlinks) > 5:
                lines.append(f"\n...и ещё {len(backlinks) - 5}\n")

            lines.append("\n")

        output_file = self.root_dir / "BACKLINKS_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"\n✅ Отчёт: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='🔗 Backlinks Generator - Генератор обратных ссылок',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                          # Обновить все статьи и создать отчёт
  %(prog)s --dry-run                # Показать что будет сделано
  %(prog)s --analyze                # Провести анализ обратных ссылок
  %(prog)s --check-broken           # Проверить сломанные ссылки
  %(prog)s --export-json            # Экспортировать в JSON
  %(prog)s --export-html            # Экспортировать в HTML
  %(prog)s --all --json out.json    # Всё: обновить, анализ, экспорты
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Не изменять файлы, только показать что будет сделано'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Провести полный анализ обратных ссылок'
    )

    parser.add_argument(
        '--check-broken',
        action='store_true',
        help='Проверить сломанные и некорректные ссылки'
    )

    parser.add_argument(
        '--export-json',
        dest='json_file',
        metavar='FILE',
        nargs='?',
        const='backlinks.json',
        help='Экспортировать в JSON (по умолчанию: backlinks.json)'
    )

    parser.add_argument(
        '--export-html',
        dest='html_file',
        metavar='FILE',
        nargs='?',
        const='backlinks.html',
        help='Экспортировать в HTML (по умолчанию: backlinks.html)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Выполнить всё: обновить статьи, анализ, экспорты'
    )

    parser.add_argument(
        '--no-update',
        action='store_true',
        help='Не обновлять файлы статей'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Не создавать markdown отчёт'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = BacklinksGenerator(root_dir)

    # Построить граф
    generator.build_backlinks_graph()

    # Режим --all
    if args.all:
        if not args.no_update:
            generator.update_all(dry_run=args.dry_run)
        generator.run_analysis()
        generator.check_broken_links()
        if not args.no_report:
            generator.generate_report()
        generator.export_json(args.json_file or 'backlinks.json')
        generator.export_html(args.html_file or 'backlinks.html')
        return

    # Анализ
    if args.analyze:
        generator.run_analysis()

    # Проверка сломанных ссылок
    if args.check_broken:
        generator.check_broken_links()

    # Экспорты
    if args.json_file:
        generator.export_json(args.json_file)

    if args.html_file:
        generator.export_html(args.html_file)

    # Действия по умолчанию (если не указаны флаги)
    if not any([args.analyze, args.check_broken, args.json_file, args.html_file]):
        if not args.no_update:
            generator.update_all(dry_run=args.dry_run)
        if not args.no_report:
            generator.generate_report()


if __name__ == "__main__":
    main()
