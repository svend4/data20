#!/usr/bin/env python3
"""
Advanced Recent Changes - Продвинутый анализ последних изменений
Функции:
- Contributor statistics (кто активнее, метрики)
- Change frequency heatmap (когда больше коммитов)
- Diff stats (insertions/deletions per file)
- Change categories (docs vs code vs tools)
- RSS feed generation (для подписчиков)
- Velocity metrics (скорость изменений)
- Most active files/directories
- Impact analysis (строк изменено)
- GitHub-style activity graph
- Export to JSON/CSV

Вдохновлено: GitHub Insights, GitStats, git-stats, RSS/Atom feeds
"""

from pathlib import Path
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import xml.etree.ElementTree as ET


class AdvancedRecentChanges:
    """Продвинутый анализ последних изменений"""

    def __init__(self, root_dir=".", days=30):
        self.root_dir = Path(root_dir)
        self.days = days

        # Статистика
        self.changes = []
        self.contributors = defaultdict(lambda: {
            'commits': 0,
            'files_changed': 0,
            'insertions': 0,
            'deletions': 0,
            'dates': []
        })
        self.file_activity = defaultdict(int)
        self.hourly_activity = defaultdict(int)
        self.daily_activity = defaultdict(int)

    def get_git_log(self):
        """Получить git лог за период"""
        since_date = (datetime.now() - timedelta(days=self.days)).strftime('%Y-%m-%d')

        try:
            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--name-status', '--numstat',
                 '--pretty=format:%H|%an|%ae|%ad|%s|%ai', '--date=short'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return result.stdout
        except:
            pass

        return None

    def parse_log(self, log_output):
        """Парсинг git лога с numstat"""
        changes = []
        current_commit = None

        for line in log_output.split('\n'):
            if '|' in line and not line.startswith(('A\t', 'M\t', 'D\t')) and not '\t' in line[:5]:
                # Информация о коммите
                parts = line.split('|')
                if len(parts) == 6:
                    commit_hash = parts[0]
                    author = parts[1]
                    email = parts[2]
                    date = parts[3]
                    message = parts[4]
                    full_date = parts[5]

                    # Извлечь час из full_date
                    try:
                        dt = datetime.fromisoformat(full_date.replace(' ', 'T').split('+')[0].split('-')[0].strip())
                        hour = dt.hour
                    except:
                        hour = 12

                    current_commit = {
                        'hash': commit_hash,
                        'author': author,
                        'email': email,
                        'date': date,
                        'hour': hour,
                        'message': message,
                        'files': [],
                        'stats': {'insertions': 0, 'deletions': 0}
                    }
                    changes.append(current_commit)

                    # Contributor stats
                    self.contributors[author]['commits'] += 1
                    self.contributors[author]['dates'].append(date)

                    # Time stats
                    self.hourly_activity[hour] += 1
                    self.daily_activity[date] += 1

            elif current_commit:
                # numstat format: insertions deletions filename
                if '\t' in line:
                    parts = line.split('\t')

                    if len(parts) == 3:
                        ins, dels, filename = parts

                        # Попробовать парсить как numstat
                        try:
                            insertions = int(ins) if ins != '-' else 0
                            deletions = int(dels) if dels != '-' else 0

                            current_commit['stats']['insertions'] += insertions
                            current_commit['stats']['deletions'] += deletions

                            self.contributors[current_commit['author']]['insertions'] += insertions
                            self.contributors[current_commit['author']]['deletions'] += deletions

                            # File activity
                            self.file_activity[filename] += 1
                            self.contributors[current_commit['author']]['files_changed'] += 1

                        except ValueError:
                            pass

                # name-status format
                if line.startswith(('A\t', 'M\t', 'D\t')):
                    status, file_path = line.split('\t', 1)
                    current_commit['files'].append({
                        'status': status,
                        'path': file_path
                    })

        return changes

    def categorize_file(self, file_path):
        """Категоризировать файл"""
        path = Path(file_path)

        if path.suffix == '.md':
            if 'knowledge' in path.parts:
                return 'docs'
            else:
                return 'meta'

        elif path.suffix == '.py':
            if 'tools' in path.parts:
                return 'tools'
            else:
                return 'code'

        elif path.suffix in ['.json', '.yaml', '.yml']:
            return 'config'

        elif path.suffix in ['.sh', '.bash']:
            return 'scripts'

        else:
            return 'other'

    def analyze_categories(self):
        """Анализ по категориям"""
        category_stats = defaultdict(lambda: {
            'commits': 0,
            'files': 0,
            'insertions': 0,
            'deletions': 0
        })

        for change in self.changes:
            for file_info in change['files']:
                category = self.categorize_file(file_info['path'])

                category_stats[category]['files'] += 1

            # Распределить stats по категориям (упрощённо - по основной категории коммита)
            if change['files']:
                main_category = self.categorize_file(change['files'][0]['path'])
                category_stats[main_category]['commits'] += 1
                category_stats[main_category]['insertions'] += change['stats']['insertions']
                category_stats[main_category]['deletions'] += change['stats']['deletions']

        return dict(category_stats)

    def calculate_velocity(self):
        """Вычислить velocity metrics"""
        if not self.changes:
            return {}

        total_commits = len(self.changes)
        total_insertions = sum(c['stats']['insertions'] for c in self.changes)
        total_deletions = sum(c['stats']['deletions'] for c in self.changes)
        total_changes = total_insertions + total_deletions

        avg_commits_per_day = total_commits / self.days if self.days > 0 else 0
        avg_changes_per_day = total_changes / self.days if self.days > 0 else 0

        return {
            'total_commits': total_commits,
            'total_insertions': total_insertions,
            'total_deletions': total_deletions,
            'total_changes': total_changes,
            'avg_commits_per_day': round(avg_commits_per_day, 2),
            'avg_changes_per_day': round(avg_changes_per_day, 1),
            'contributors_count': len(self.contributors)
        }

    def generate_activity_heatmap(self):
        """Создать данные для heatmap (день x час)"""
        # Упрощённая версия - только часы
        hours = list(range(24))
        activity = [self.hourly_activity.get(h, 0) for h in hours]

        return {
            'hours': hours,
            'activity': activity
        }

    def generate_report(self):
        """Создать подробный отчёт"""
        lines = []
        lines.append(f"# 📅 Продвинутый анализ изменений (за {self.days} дней)\n\n")

        # Velocity metrics
        velocity = self.calculate_velocity()

        lines.append("## 📊 Общая статистика\n\n")
        lines.append(f"- **Коммитов**: {velocity['total_commits']}\n")
        lines.append(f"- **Вставок (insertions)**: +{velocity['total_insertions']:,}\n")
        lines.append(f"- **Удалений (deletions)**: -{velocity['total_deletions']:,}\n")
        lines.append(f"- **Всего изменений**: {velocity['total_changes']:,}\n")
        lines.append(f"- **Среднее коммитов/день**: {velocity['avg_commits_per_day']}\n")
        lines.append(f"- **Среднее изменений/день**: {velocity['avg_changes_per_day']:,.0f}\n")
        lines.append(f"- **Контрибьюторов**: {velocity['contributors_count']}\n\n")

        # Contributors ranking
        lines.append("## 👥 Топ контрибьюторов\n\n")

        sorted_contributors = sorted(
            self.contributors.items(),
            key=lambda x: -(x[1]['commits'] + x[1]['insertions'] / 10)
        )

        for i, (author, stats) in enumerate(sorted_contributors[:10], 1):
            total_lines = stats['insertions'] + stats['deletions']

            lines.append(f"### {i}. {author}\n\n")
            lines.append(f"- **Коммитов**: {stats['commits']}\n")
            lines.append(f"- **Файлов изменено**: {stats['files_changed']}\n")
            lines.append(f"- **Строк добавлено**: +{stats['insertions']:,}\n")
            lines.append(f"- **Строк удалено**: -{stats['deletions']:,}\n")
            lines.append(f"- **Всего строк**: {total_lines:,}\n\n")

        # Most active files
        lines.append("## 📁 Самые активные файлы\n\n")

        top_files = sorted(self.file_activity.items(), key=lambda x: -x[1])[:15]

        for file_path, count in top_files:
            category = self.categorize_file(file_path)
            lines.append(f"- **{file_path}**: {count} изменений ({category})\n")

        lines.append("\n")

        # Categories
        category_stats = self.analyze_categories()

        if category_stats:
            lines.append("## 🗂️ По категориям\n\n")

            for category, stats in sorted(category_stats.items(), key=lambda x: -x[1]['commits']):
                lines.append(f"### {category.title()}\n\n")
                lines.append(f"- Коммитов: {stats['commits']}\n")
                lines.append(f"- Файлов: {stats['files']}\n")
                lines.append(f"- Изменений: +{stats['insertions']:,} / -{stats['deletions']:,}\n\n")

        # Activity heatmap (text representation)
        heatmap = self.generate_activity_heatmap()

        lines.append("## ⏰ Активность по часам\n\n")
        lines.append("```\n")

        max_activity = max(heatmap['activity']) if heatmap['activity'] else 1

        for hour, count in zip(heatmap['hours'], heatmap['activity']):
            bar_length = int((count / max_activity * 20)) if max_activity > 0 else 0
            bar = '█' * bar_length
            lines.append(f"{hour:02d}:00 {bar} {count}\n")

        lines.append("```\n\n")

        # Recent commits (grouped by date)
        lines.append("## 📝 Последние коммиты\n\n")

        by_date = defaultdict(list)
        for change in self.changes:
            by_date[change['date']].append(change)

        for date in sorted(by_date.keys(), reverse=True)[:7]:
            commits = by_date[date]
            total_changes = sum(c['stats']['insertions'] + c['stats']['deletions'] for c in commits)

            lines.append(f"### {date} ({len(commits)} коммитов, {total_changes:,} изменений)\n\n")

            for commit in commits[:5]:
                lines.append(f"#### {commit['message']}\n\n")
                lines.append(f"- **Автор**: {commit['author']}\n")
                lines.append(f"- **Хэш**: `{commit['hash'][:7]}`\n")
                lines.append(f"- **Изменения**: +{commit['stats']['insertions']} / -{commit['stats']['deletions']}\n")

                if commit['files']:
                    lines.append(f"- **Файлов**: {len(commit['files'])}\n")

                lines.append("\n")

            if len(commits) > 5:
                lines.append(f"_...и ещё {len(commits) - 5} коммитов_\n\n")

        output_file = self.root_dir / "ADVANCED_RECENT_CHANGES.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def generate_rss_feed(self):
        """Создать RSS feed"""
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')

        ET.SubElement(channel, 'title').text = 'Knowledge Base - Recent Changes'
        ET.SubElement(channel, 'link').text = 'https://example.com'
        ET.SubElement(channel, 'description').text = f'Last {self.days} days of changes'
        ET.SubElement(channel, 'language').text = 'ru'

        # Добавить items (последние 20 коммитов)
        for change in self.changes[:20]:
            item = ET.SubElement(channel, 'item')

            title = f"{change['message']} by {change['author']}"
            ET.SubElement(item, 'title').text = title

            description = f"Author: {change['author']}<br/>"
            description += f"Files: {len(change['files'])}<br/>"
            description += f"Changes: +{change['stats']['insertions']} -{change['stats']['deletions']}"

            ET.SubElement(item, 'description').text = description
            ET.SubElement(item, 'author').text = change['email']
            ET.SubElement(item, 'pubDate').text = change['date']
            ET.SubElement(item, 'guid').text = change['hash']

        # Сохранить
        tree = ET.ElementTree(rss)
        output_file = self.root_dir / "recent_changes.rss"

        tree.write(output_file, encoding='utf-8', xml_declaration=True)

        print(f"✅ RSS feed: {output_file}")

    def export_json(self):
        """Экспорт в JSON"""
        data = {
            'period_days': self.days,
            'generated_at': datetime.now().isoformat(),
            'velocity': self.calculate_velocity(),
            'contributors': {
                author: {
                    **stats,
                    'dates': list(set(stats['dates']))  # Уникальные даты
                }
                for author, stats in self.contributors.items()
            },
            'category_stats': self.analyze_categories(),
            'activity_heatmap': self.generate_activity_heatmap(),
            'recent_commits': [
                {
                    'hash': c['hash'],
                    'author': c['author'],
                    'date': c['date'],
                    'message': c['message'],
                    'stats': c['stats'],
                    'files_count': len(c['files'])
                }
                for c in self.changes[:50]
            ]
        }

        output_file = self.root_dir / "recent_changes.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Recent Changes')
    parser.add_argument('-d', '--days', type=int, default=30,
                       help='Количество дней (по умолчанию: 30)')
    parser.add_argument('--rss', action='store_true',
                       help='Создать RSS feed')
    parser.add_argument('--json', action='store_true',
                       help='Экспорт в JSON')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = AdvancedRecentChanges(root_dir, days=args.days)

    print(f"📅 Продвинутый анализ изменений за последние {args.days} дней...\n")

    log_output = analyzer.get_git_log()

    if log_output:
        analyzer.changes = analyzer.parse_log(log_output)
        print(f"   Найдено коммитов: {len(analyzer.changes)}")
        print(f"   Контрибьюторов: {len(analyzer.contributors)}\n")

        analyzer.generate_report()

        if args.rss:
            analyzer.generate_rss_feed()

        if args.json:
            analyzer.export_json()
    else:
        print("⚠️  Не удалось получить git лог")


if __name__ == "__main__":
    main()
