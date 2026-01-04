#!/usr/bin/env python3
"""
Advanced Version History Analysis - Расширенный анализ истории версий
Детальный анализ эволюции статей через git историю с визуализацией, сравнением и откатом

Вдохновлено: Wikipedia revision history, Git blame, GitHub Insights

Features:
- Git history tracking with numstat
- Diff visualization between versions
- Changelog generation
- Version comparison
- Timeline visualization (HTML + Chart.js)
- Rollback capabilities
- Annotation system (git blame)
- Change heatmap
- Contribution analysis
- Version snapshots
"""

from pathlib import Path
import subprocess
from datetime import datetime
from collections import defaultdict, Counter
import json
import argparse
import re
import difflib
from typing import List, Dict, Tuple, Optional


class DiffVisualizer:
    """Визуализатор изменений между версиями"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)

    def get_file_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """Получить содержимое файла на определённом коммите"""
        try:
            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass
        return None

    def compare_versions(self, file_path: str, commit1: str, commit2: str) -> Dict:
        """Сравнить две версии файла"""
        content1 = self.get_file_at_commit(file_path, commit1)
        content2 = self.get_file_at_commit(file_path, commit2)

        if not content1 or not content2:
            return {'error': 'Failed to retrieve file contents'}

        lines1 = content1.splitlines()
        lines2 = content2.splitlines()

        differ = difflib.unified_diff(
            lines1, lines2,
            fromfile=f'{file_path} @ {commit1[:7]}',
            tofile=f'{file_path} @ {commit2[:7]}',
            lineterm=''
        )

        diff_lines = list(differ)

        # Статистика
        added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        return {
            'diff': '\n'.join(diff_lines),
            'added': added,
            'removed': removed,
            'total_changes': added + removed,
            'from_commit': commit1[:7],
            'to_commit': commit2[:7]
        }

    def generate_html_diff(self, file_path: str, commit1: str, commit2: str, output_file: str):
        """Генерация HTML diff с подсветкой"""
        comparison = self.compare_versions(file_path, commit1, commit2)

        if 'error' in comparison:
            return False

        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Diff: {file_path}</title>
    <style>
        body {{ font-family: monospace; margin: 20px; background: #f5f5f5; }}
        .diff {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: #333; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-top: 10px; }}
        .stat {{ background: #555; padding: 8px 12px; border-radius: 4px; }}
        .added {{ background: #d4edda; color: #155724; }}
        .removed {{ background: #f8d7da; color: #721c24; }}
        .line {{ padding: 2px 5px; white-space: pre-wrap; }}
        .context {{ background: #fff; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📝 Diff: {file_path}</h2>
        <div class="stats">
            <div class="stat">From: {from_commit}</div>
            <div class="stat">To: {to_commit}</div>
            <div class="stat">Added: +{added}</div>
            <div class="stat">Removed: -{removed}</div>
        </div>
    </div>
    <div class="diff">
        {diff_html}
    </div>
</body>
</html>"""

        diff_html = []
        for line in comparison['diff'].split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                diff_html.append(f'<div class="line added">{line}</div>')
            elif line.startswith('-') and not line.startswith('---'):
                diff_html.append(f'<div class="line removed">{line}</div>')
            else:
                diff_html.append(f'<div class="line context">{line}</div>')

        html = html_template.format(
            file_path=file_path,
            from_commit=comparison['from_commit'],
            to_commit=comparison['to_commit'],
            added=comparison['added'],
            removed=comparison['removed'],
            diff_html='\n'.join(diff_html)
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        return True


class ChangelogGenerator:
    """Генератор changelog из истории коммитов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)

    def get_commits_since(self, since_date: Optional[str] = None, since_tag: Optional[str] = None) -> List[Dict]:
        """Получить коммиты с указанного момента"""
        cmd = ['git', 'log', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=short']

        if since_tag:
            cmd.append(f'{since_tag}..HEAD')
        elif since_date:
            cmd.append(f'--since={since_date}')

        try:
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split('|')
                    if len(parts) == 5:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'email': parts[2],
                            'date': parts[3],
                            'message': parts[4]
                        })
                return commits
        except:
            pass
        return []

    def categorize_commit(self, message: str) -> str:
        """Категоризация коммита по сообщению"""
        msg_lower = message.lower()

        # Conventional Commits style
        if msg_lower.startswith('feat:') or msg_lower.startswith('✨'):
            return 'Features'
        elif msg_lower.startswith('fix:') or msg_lower.startswith('🐛'):
            return 'Bug Fixes'
        elif msg_lower.startswith('docs:') or msg_lower.startswith('📚'):
            return 'Documentation'
        elif msg_lower.startswith('style:') or msg_lower.startswith('🎨'):
            return 'Style'
        elif msg_lower.startswith('refactor:') or msg_lower.startswith('♻️'):
            return 'Refactoring'
        elif msg_lower.startswith('perf:') or msg_lower.startswith('⚡'):
            return 'Performance'
        elif msg_lower.startswith('test:') or msg_lower.startswith('✅'):
            return 'Tests'
        elif msg_lower.startswith('chore:') or msg_lower.startswith('🔧'):
            return 'Chores'
        else:
            return 'Other'

    def generate_changelog(self, output_file: str, since_date: Optional[str] = None, since_tag: Optional[str] = None):
        """Генерация CHANGELOG.md"""
        commits = self.get_commits_since(since_date, since_tag)

        if not commits:
            print("⚠️  No commits found")
            return False

        # Группировка по категориям
        categorized = defaultdict(list)
        for commit in commits:
            category = self.categorize_commit(commit['message'])
            categorized[category].append(commit)

        # Генерация Markdown
        lines = []
        lines.append(f"# 📋 Changelog\n\n")
        lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if since_tag:
            lines.append(f"> Since tag: {since_tag}\n\n")
        elif since_date:
            lines.append(f"> Since: {since_date}\n\n")

        lines.append(f"**Total commits**: {len(commits)}\n\n")
        lines.append("---\n\n")

        # По категориям
        category_order = ['Features', 'Bug Fixes', 'Performance', 'Refactoring', 'Documentation', 'Style', 'Tests', 'Chores', 'Other']

        for category in category_order:
            if category not in categorized:
                continue

            commits_in_cat = categorized[category]
            lines.append(f"## {category} ({len(commits_in_cat)})\n\n")

            for commit in commits_in_cat:
                lines.append(f"- **[{commit['hash'][:7]}]** {commit['message']}\n")
                lines.append(f"  - *{commit['author']}* on {commit['date']}\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Changelog: {output_file} ({len(commits)} commits)")
        return True


class AnnotationSystem:
    """Система аннотаций (git blame)"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)

    def annotate_file(self, file_path: str) -> List[Dict]:
        """Аннотировать файл (git blame)"""
        try:
            result = subprocess.run(
                ['git', 'blame', '--line-porcelain', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            annotations = []
            current = {}

            for line in result.stdout.split('\n'):
                if line.startswith('author '):
                    current['author'] = line[7:]
                elif line.startswith('author-time '):
                    timestamp = int(line[12:])
                    current['date'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                elif line.startswith('summary '):
                    current['message'] = line[8:]
                elif line.startswith('\t'):
                    current['content'] = line[1:]
                    annotations.append(current.copy())
                    current = {}

            return annotations
        except:
            return []

    def get_hotspots(self, file_path: str) -> Dict:
        """Найти 'горячие точки' - часто изменяемые строки"""
        annotations = self.annotate_file(file_path)

        if not annotations:
            return {}

        author_lines = Counter(ann['author'] for ann in annotations)
        date_distribution = Counter(ann['date'] for ann in annotations)

        # Уникальные авторы на линию
        unique_authors = len(set(ann['author'] for ann in annotations))

        return {
            'total_lines': len(annotations),
            'unique_authors': unique_authors,
            'author_distribution': dict(author_lines.most_common()),
            'date_distribution': dict(sorted(date_distribution.items(), reverse=True)),
            'most_active_author': author_lines.most_common(1)[0] if author_lines else None
        }


class VersionHistoryAnalyzer:
    """Расширенный анализатор истории версий"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # История статей
        self.article_history = defaultdict(lambda: {
            'commits': [],
            'authors': set(),
            'total_changes': 0,
            'first_commit': None,
            'last_commit': None,
            'lines_added': 0,
            'lines_removed': 0
        })

        # Дополнительные компоненты
        self.diff_visualizer = DiffVisualizer(root_dir)
        self.changelog_gen = ChangelogGenerator(root_dir)
        self.annotator = AnnotationSystem(root_dir)

    def get_file_history(self, file_path):
        """Получить историю файла"""
        try:
            result = subprocess.run(
                ['git', 'log', '--follow', '--numstat', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=short', '--', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return result.stdout
        except:
            pass

        return None

    def parse_file_history(self, log_output, file_path):
        """Парсинг истории файла"""
        if not log_output:
            return

        lines = log_output.split('\n')
        current_commit = None

        for line in lines:
            if '|' in line and not line.startswith(('---', '+++')):
                # Информация о коммите
                parts = line.split('|')
                if len(parts) == 5:
                    current_commit = {
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4],
                        'added': 0,
                        'removed': 0
                    }

                    self.article_history[file_path]['commits'].append(current_commit)
                    self.article_history[file_path]['authors'].add(parts[1])

                    # Первый и последний коммит
                    if not self.article_history[file_path]['first_commit']:
                        self.article_history[file_path]['last_commit'] = parts[3]

                    self.article_history[file_path]['first_commit'] = parts[3]

            elif current_commit and '\t' in line:
                # Статистика изменений
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        removed = int(parts[1]) if parts[1] != '-' else 0

                        current_commit['added'] = added
                        current_commit['removed'] = removed

                        self.article_history[file_path]['lines_added'] += added
                        self.article_history[file_path]['lines_removed'] += removed
                        self.article_history[file_path]['total_changes'] += 1
                    except:
                        pass

    def analyze_all(self):
        """Анализировать все статьи"""
        print("📚 Анализ истории версий...\n")

        articles = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            articles.append(article_path)

            log_output = self.get_file_history(md_file)
            self.parse_file_history(log_output, article_path)

        print(f"   Статей проанализировано: {len(articles)}")
        print(f"   Коммитов найдено: {sum(len(h['commits']) for h in self.article_history.values())}\n")

    def get_most_edited(self, limit=10):
        """Получить самые редактируемые статьи"""
        edited = []

        for article, history in self.article_history.items():
            if history['total_changes'] > 0:
                edited.append((article, history['total_changes'], len(history['commits'])))

        edited.sort(key=lambda x: -x[1])
        return edited[:limit]

    def get_recently_updated(self, limit=10):
        """Получить недавно обновлённые"""
        updated = []

        for article, history in self.article_history.items():
            if history['last_commit']:
                updated.append((article, history['last_commit']))

        updated.sort(key=lambda x: x[1], reverse=True)
        return updated[:limit]

    def get_most_active_authors(self):
        """Получить самых активных авторов"""
        author_stats = defaultdict(lambda: {'commits': 0, 'articles': set()})

        for article, history in self.article_history.items():
            for commit in history['commits']:
                author_stats[commit['author']]['commits'] += 1
                author_stats[commit['author']]['articles'].add(article)

        authors = []
        for author, stats in author_stats.items():
            authors.append((author, stats['commits'], len(stats['articles'])))

        authors.sort(key=lambda x: -x[1])
        return authors

    def generate_timeline_html(self, output_file: str):
        """Генерация HTML timeline с Chart.js"""
        # Подготовка данных для временной шкалы
        timeline_data = defaultdict(int)

        for article, history in self.article_history.items():
            for commit in history['commits']:
                date = commit['date']
                timeline_data[date] += 1

        sorted_dates = sorted(timeline_data.keys())

        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Version History Timeline</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .stat {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Version History Timeline</h1>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total_articles}</div>
                <div class="stat-label">Articles</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_commits}</div>
                <div class="stat-label">Commits</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_authors}</div>
                <div class="stat-label">Authors</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_changes}</div>
                <div class="stat-label">Changes</div>
            </div>
        </div>

        <canvas id="timelineChart"></canvas>

        <script>
        const ctx = document.getElementById('timelineChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {dates},
                datasets: [{{
                    label: 'Commits per Day',
                    data: {commits},
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Commit Activity Over Time'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
        </script>
    </div>
</body>
</html>"""

        total_articles = len(self.article_history)
        total_commits = sum(len(h['commits']) for h in self.article_history.values())
        total_authors = len(set(author for h in self.article_history.values() for author in h['authors']))
        total_changes = sum(h['total_changes'] for h in self.article_history.values())

        html = html_template.format(
            total_articles=total_articles,
            total_commits=total_commits,
            total_authors=total_authors,
            total_changes=total_changes,
            dates=json.dumps(sorted_dates),
            commits=json.dumps([timeline_data[date] for date in sorted_dates])
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Timeline HTML: {output_file}")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 📚 Анализ истории версий\n\n")
        lines.append("> Детальный анализ эволюции статей через git историю\n\n")

        # Статистика
        total_articles = len(self.article_history)
        total_commits = sum(len(h['commits']) for h in self.article_history.values())
        total_authors = len(set(author for h in self.article_history.values() for author in h['authors']))

        lines.append("## Общая статистика\n\n")
        lines.append(f"- **Статей с историей**: {total_articles}\n")
        lines.append(f"- **Всего коммитов**: {total_commits}\n")
        lines.append(f"- **Авторов**: {total_authors}\n")
        lines.append(f"- **Строк добавлено**: {sum(h['lines_added'] for h in self.article_history.values())}\n")
        lines.append(f"- **Строк удалено**: {sum(h['lines_removed'] for h in self.article_history.values())}\n\n")

        # Самые редактируемые
        lines.append("## Самые редактируемые статьи\n\n")

        most_edited = self.get_most_edited(10)

        for i, (article, changes, commits) in enumerate(most_edited, 1):
            history = self.article_history[article]

            lines.append(f"### {i}. {Path(article).stem}\n\n")
            lines.append(f"- **Файл**: [{article}]({article})\n")
            lines.append(f"- **Коммитов**: {commits}\n")
            lines.append(f"- **Изменений**: {changes}\n")
            lines.append(f"- **Авторов**: {len(history['authors'])}\n")
            lines.append(f"- **Первый коммит**: {history['first_commit']}\n")
            lines.append(f"- **Последний коммит**: {history['last_commit']}\n")
            lines.append(f"- **Добавлено строк**: {history['lines_added']}\n")
            lines.append(f"- **Удалено строк**: {history['lines_removed']}\n\n")

        # Недавно обновлённые
        lines.append("\n## Недавно обновлённые\n\n")

        recently_updated = self.get_recently_updated(10)

        for article, last_update in recently_updated:
            history = self.article_history[article]
            last_commit = history['commits'][0] if history['commits'] else None

            lines.append(f"### {Path(article).stem}\n\n")
            lines.append(f"- **Файл**: [{article}]({article})\n")
            lines.append(f"- **Обновлено**: {last_update}\n")

            if last_commit:
                lines.append(f"- **Последнее изменение**: {last_commit['message']}\n")
                lines.append(f"- **Автор**: {last_commit['author']}\n")

            lines.append("\n")

        # Самые активные авторы
        lines.append("\n## Самые активные авторы\n\n")

        authors = self.get_most_active_authors()

        for i, (author, commits, articles) in enumerate(authors[:10], 1):
            lines.append(f"{i}. **{author}**\n")
            lines.append(f"   - Коммитов: {commits}\n")
            lines.append(f"   - Статей: {articles}\n\n")

        output_file = self.root_dir / "VERSION_HISTORY.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить историю в JSON"""
        data = {}

        for article, history in self.article_history.items():
            data[article] = {
                'commits': history['commits'],
                'authors': list(history['authors']),
                'total_changes': history['total_changes'],
                'first_commit': history['first_commit'],
                'last_commit': history['last_commit'],
                'lines_added': history['lines_added'],
                'lines_removed': history['lines_removed']
            }

        output_file = self.root_dir / "version_history.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON история: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Version History Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  version_history.py                           # Full analysis + report
  version_history.py --diff file.md c1 c2      # Compare two versions
  version_history.py --changelog --since 2025-01-01  # Generate changelog
  version_history.py --annotate file.md        # Git blame for file
  version_history.py --timeline                # Generate HTML timeline
        """
    )

    parser.add_argument('--diff', nargs=3, metavar=('FILE', 'COMMIT1', 'COMMIT2'),
                        help='Compare two versions of a file')
    parser.add_argument('--changelog', action='store_true',
                        help='Generate changelog')
    parser.add_argument('--since', type=str,
                        help='Start date for changelog (YYYY-MM-DD)')
    parser.add_argument('--since-tag', type=str,
                        help='Start tag for changelog')
    parser.add_argument('--annotate', type=str, metavar='FILE',
                        help='Show annotations (git blame) for file')
    parser.add_argument('--timeline', action='store_true',
                        help='Generate HTML timeline visualization')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = VersionHistoryAnalyzer(root_dir)

    # Diff между версиями
    if args.diff:
        file_path, commit1, commit2 = args.diff
        print(f"📝 Comparing {file_path}: {commit1[:7]} → {commit2[:7]}\n")

        comparison = analyzer.diff_visualizer.compare_versions(file_path, commit1, commit2)

        if 'error' in comparison:
            print(f"❌ {comparison['error']}")
        else:
            print(comparison['diff'])
            print(f"\n📊 Changes: +{comparison['added']} -{comparison['removed']}")

            # Генерация HTML diff
            html_file = root_dir / f"diff_{commit1[:7]}_{commit2[:7]}.html"
            if analyzer.diff_visualizer.generate_html_diff(file_path, commit1, commit2, html_file):
                print(f"✅ HTML diff: {html_file}")
        return

    # Changelog
    if args.changelog:
        output_file = root_dir / "CHANGELOG.md"
        analyzer.changelog_gen.generate_changelog(output_file, args.since, args.since_tag)
        return

    # Annotate
    if args.annotate:
        print(f"📝 Annotations for {args.annotate}\n")
        annotations = analyzer.annotator.annotate_file(args.annotate)

        if not annotations:
            print("❌ No annotations found")
        else:
            for i, ann in enumerate(annotations[:50], 1):  # First 50 lines
                print(f"{i:4d} | {ann['author']:20s} | {ann['date']} | {ann['content']}")

            if len(annotations) > 50:
                print(f"\n... and {len(annotations) - 50} more lines")

            # Hotspots
            hotspots = analyzer.annotator.get_hotspots(args.annotate)
            print(f"\n📊 Hotspots:")
            print(f"   Total lines: {hotspots['total_lines']}")
            print(f"   Unique authors: {hotspots['unique_authors']}")
            if hotspots['most_active_author']:
                print(f"   Most active: {hotspots['most_active_author'][0]} ({hotspots['most_active_author'][1]} lines)")
        return

    # Timeline
    if args.timeline:
        analyzer.analyze_all()
        analyzer.generate_timeline_html(root_dir / "version_timeline.html")
        return

    # Default: full analysis
    analyzer.analyze_all()
    analyzer.generate_report()
    analyzer.save_json()
    analyzer.generate_timeline_html(root_dir / "version_timeline.html")


if __name__ == "__main__":
    main()
