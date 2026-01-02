#!/usr/bin/env python3
"""
Advanced Orphan Finder - Продвинутый поиск статей-сирот
Функции:
- Orphan classification (новые, старые, критичные)
- Fix suggestions (предложения где добавить ссылки)
- Severity levels (high, medium, low)
- Integration candidates (статьи, которые могут ссылаться)
- Orphan age detection
- Link density analysis
- Category-based analysis
- Automatic fix generation
- JSON export
- Graph visualization data

Вдохновлено: Wikipedia orphan detection, SEO tools, Content auditing tools
"""

from pathlib import Path
import re
import yaml
from datetime import datetime, timedelta
import json
from collections import defaultdict


class AdvancedOrphanFinder:
    """Продвинутый поиск статей-сирот"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Статистика
        self.all_articles = {}  # path -> metadata
        self.incoming_links = defaultdict(set)  # target -> sources
        self.outgoing_links = defaultdict(set)  # source -> targets

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

    def analyze_article(self, file_path):
        """Проанализировать статью"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        # Базовая информация
        article_path = str(file_path.relative_to(self.root_dir))

        # Дата создания/модификации
        mtime = file_path.stat().st_mtime
        modified_date = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - modified_date).days

        # Размер контента
        content_length = len(content) if content else 0

        # Теги/категории
        tags = []
        category = None
        if frontmatter:
            tags = frontmatter.get('tags', [])
            category = frontmatter.get('category', None)

        # Сохранить метаданные
        self.all_articles[article_path] = {
            'path': article_path,
            'frontmatter': frontmatter,
            'content_length': content_length,
            'modified_date': modified_date,
            'age_days': age_days,
            'tags': tags,
            'category': category,
            'file_path': file_path
        }

        return content

    def build_link_graph(self):
        """Построить граф ссылок"""
        print("🔍 Анализ статей и ссылок...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            # Анализировать статью
            content = self.analyze_article(md_file)
            article_path = str(md_file.relative_to(self.root_dir))

            if not content:
                continue

            # Найти все markdown ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in links:
                # Пропустить внешние ссылки и якоря
                if link.startswith('http') or link.startswith('#'):
                    continue

                # Разрешить относительный путь
                try:
                    target = (md_file.parent / link.split('#')[0]).resolve()
                    target_path = str(target.relative_to(self.root_dir))

                    # Записать связь
                    self.outgoing_links[article_path].add(target_path)
                    self.incoming_links[target_path].add(article_path)
                except:
                    pass

            # Ссылки из frontmatter (related)
            frontmatter = self.all_articles[article_path]['frontmatter']
            if frontmatter and 'related' in frontmatter:
                related = frontmatter['related']
                if isinstance(related, list):
                    for link in related:
                        try:
                            target = (md_file.parent / link).resolve()
                            target_path = str(target.relative_to(self.root_dir))

                            self.outgoing_links[article_path].add(target_path)
                            self.incoming_links[target_path].add(article_path)
                        except:
                            pass

        print(f"   Статей: {len(self.all_articles)}")
        print(f"   Связей: {sum(len(v) for v in self.outgoing_links.values())}\n")

    def classify_orphan(self, article_path):
        """Классифицировать сироту"""
        metadata = self.all_articles[article_path]

        age_days = metadata['age_days']
        content_length = metadata['content_length']
        outgoing_links_count = len(self.outgoing_links.get(article_path, set()))

        # Классификация
        classification = {
            'type': 'unknown',
            'severity': 'medium',
            'reason': []
        }

        # Новая статья (< 7 дней)
        if age_days < 7:
            classification['type'] = 'new'
            classification['severity'] = 'low'
            classification['reason'].append('Новая статья, возможно еще не интегрирована')

        # Старая статья (> 90 дней) без ссылок
        elif age_days > 90:
            classification['type'] = 'old_orphan'
            classification['severity'] = 'high'
            classification['reason'].append('Старая статья без ссылок - требует внимания')

        # Короткая статья
        if content_length < 500:
            classification['type'] = 'stub'
            classification['severity'] = 'low'
            classification['reason'].append('Короткая статья (stub)')

        # Статья со ссылками наружу но без входящих
        if outgoing_links_count > 0:
            classification['type'] = 'isolated'
            classification['severity'] = 'medium'
            classification['reason'].append(f'Ссылается на {outgoing_links_count} статей, но на нее никто не ссылается')

        # Полностью изолированная статья
        if outgoing_links_count == 0:
            classification['type'] = 'completely_isolated'
            classification['severity'] = 'high'
            classification['reason'].append('Полностью изолирована (нет ссылок ни в одну сторону)')

        return classification

    def find_integration_candidates(self, orphan_path, max_candidates=5):
        """Найти статьи, которые могут ссылаться на сироту"""
        orphan_metadata = self.all_articles[orphan_path]
        candidates = []

        orphan_tags = set(orphan_metadata.get('tags', []))
        orphan_category = orphan_metadata.get('category')

        for article_path, metadata in self.all_articles.items():
            if article_path == orphan_path:
                continue

            score = 0
            reasons = []

            # Общие теги
            article_tags = set(metadata.get('tags', []))
            common_tags = orphan_tags & article_tags
            if common_tags:
                score += len(common_tags) * 2
                reasons.append(f"Общие теги: {', '.join(common_tags)}")

            # Та же категория
            if metadata.get('category') == orphan_category and orphan_category:
                score += 3
                reasons.append(f"Та же категория: {orphan_category}")

            # Сирота ссылается на эту статью
            if article_path in self.outgoing_links.get(orphan_path, set()):
                score += 5
                reasons.append("Сирота ссылается на эту статью (можно сделать взаимную ссылку)")

            # Эта статья в той же директории
            if Path(article_path).parent == Path(orphan_path).parent:
                score += 1
                reasons.append("В той же директории")

            # Много исходящих ссылок (hub)
            outgoing_count = len(self.outgoing_links.get(article_path, set()))
            if outgoing_count > 5:
                score += 1
                reasons.append(f"Hub-статья ({outgoing_count} ссылок)")

            if score > 0:
                candidates.append({
                    'path': article_path,
                    'score': score,
                    'reasons': reasons
                })

        # Сортировать по score
        candidates.sort(key=lambda x: -x['score'])

        return candidates[:max_candidates]

    def generate_fix_suggestion(self, orphan_path, candidate):
        """Сгенерировать предложение по исправлению"""
        orphan_name = Path(orphan_path).stem
        candidate_name = Path(candidate['path']).stem

        suggestion = f"В файле `{candidate['path']}` можно добавить ссылку на `{orphan_path}`:\n"
        suggestion += f"```markdown\n"
        suggestion += f"[{orphan_name}]({Path(orphan_path).name})\n"
        suggestion += f"```\n"
        suggestion += f"Причина: {', '.join(candidate['reasons'])}"

        return suggestion

    def find_orphans(self):
        """Найти и классифицировать сирот"""
        # Построить граф
        self.build_link_graph()

        print("🔍 Поиск статей-сирот...\n")

        # Найти сироты
        orphans = []

        for article_path in self.all_articles.keys():
            incoming_count = len(self.incoming_links.get(article_path, set()))

            if incoming_count == 0:
                # Классифицировать
                classification = self.classify_orphan(article_path)

                # Найти кандидатов для интеграции
                candidates = self.find_integration_candidates(article_path)

                orphan_data = {
                    'path': article_path,
                    'metadata': self.all_articles[article_path],
                    'classification': classification,
                    'candidates': candidates
                }

                orphans.append(orphan_data)

        # Статистика
        total = len(self.all_articles)
        linked = total - len(orphans)

        print(f"   Всего статей: {total}")
        print(f"   Со ссылками: {linked}")
        print(f"   Сироты: {len(orphans)}\n")

        # Статистика по типам
        if orphans:
            types = defaultdict(int)
            for orphan in orphans:
                types[orphan['classification']['type']] += 1

            print("   Типы сирот:")
            for orphan_type, count in sorted(types.items(), key=lambda x: -x[1]):
                print(f"      {orphan_type}: {count}")
            print()

        return orphans

    def generate_report(self, orphans):
        """Создать подробный отчёт"""
        lines = []
        lines.append("# 🔍 Продвинутый отчёт: Статьи-сироты\n\n")
        lines.append("> Статьи без входящих ссылок с анализом и предложениями\n\n")

        lines.append(f"**Найдено сирот**: {len(orphans)}\n\n")

        if not orphans:
            lines.append("✅ Нет статей-сирот! Все статьи связаны.\n")
        else:
            # Группировать по severity
            by_severity = defaultdict(list)
            for orphan in orphans:
                severity = orphan['classification']['severity']
                by_severity[severity].append(orphan)

            # High severity
            if 'high' in by_severity:
                lines.append("## 🔴 Критичные сироты (High Severity)\n\n")
                lines.append("Требуют немедленного внимания\n\n")

                for orphan in by_severity['high']:
                    self._add_orphan_section(lines, orphan)

            # Medium severity
            if 'medium' in by_severity:
                lines.append("\n## 🟡 Средний приоритет (Medium Severity)\n\n")

                for orphan in by_severity['medium']:
                    self._add_orphan_section(lines, orphan)

            # Low severity
            if 'low' in by_severity:
                lines.append("\n## 🟢 Низкий приоритет (Low Severity)\n\n")

                for orphan in by_severity['low']:
                    self._add_orphan_section(lines, orphan)

        output_file = self.root_dir / "ORPHANED_ARTICLES_ADVANCED.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def _add_orphan_section(self, lines, orphan):
        """Добавить секцию для одной сироты"""
        path = orphan['path']
        classification = orphan['classification']
        metadata = orphan['metadata']
        candidates = orphan['candidates']

        lines.append(f"### {Path(path).stem}\n\n")
        lines.append(f"- **Путь**: `{path}`\n")
        lines.append(f"- **Тип**: {classification['type']}\n")
        lines.append(f"- **Severity**: {classification['severity']}\n")
        lines.append(f"- **Возраст**: {metadata['age_days']} дней\n")
        lines.append(f"- **Размер**: {metadata['content_length']} символов\n")

        if classification['reason']:
            lines.append(f"- **Причины**:\n")
            for reason in classification['reason']:
                lines.append(f"  - {reason}\n")

        # Кандидаты для интеграции
        if candidates:
            lines.append(f"\n**Предложения по интеграции** (топ-{len(candidates)}):\n\n")

            for i, candidate in enumerate(candidates, 1):
                lines.append(f"{i}. **{Path(candidate['path']).stem}** (score: {candidate['score']})\n")
                lines.append(f"   - Файл: `{candidate['path']}`\n")
                for reason in candidate['reasons']:
                    lines.append(f"   - {reason}\n")
                lines.append("\n")

        lines.append("\n---\n\n")

    def export_json(self, orphans):
        """Экспорт в JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(self.all_articles),
            'total_orphans': len(orphans),
            'orphans': []
        }

        for orphan in orphans:
            # Конвертировать datetime в string
            metadata = orphan['metadata'].copy()
            metadata['modified_date'] = metadata['modified_date'].isoformat()
            metadata.pop('file_path', None)  # Удалить Path object

            # Конвертировать frontmatter (может содержать date объекты)
            frontmatter = metadata.get('frontmatter')
            if frontmatter:
                frontmatter_clean = {}
                for key, value in frontmatter.items():
                    if hasattr(value, 'isoformat'):  # datetime или date
                        frontmatter_clean[key] = value.isoformat()
                    else:
                        frontmatter_clean[key] = value
                metadata['frontmatter'] = frontmatter_clean

            data['orphans'].append({
                'path': orphan['path'],
                'metadata': metadata,
                'classification': orphan['classification'],
                'candidates': orphan['candidates']
            })

        output_file = self.root_dir / "orphans_analysis.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Orphan Finder')
    parser.add_argument('--json', action='store_true',
                       help='Экспорт в JSON')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    finder = AdvancedOrphanFinder(root_dir)
    orphans = finder.find_orphans()
    finder.generate_report(orphans)

    if args.json:
        finder.export_json(orphans)


if __name__ == "__main__":
    main()
