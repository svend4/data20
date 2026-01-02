#!/usr/bin/env python3
"""
Recent Changes - Последние изменения
Анализирует git историю для отслеживания изменений
"""

from pathlib import Path
import subprocess
from datetime import datetime, timedelta


class RecentChanges:
    """Анализ последних изменений"""

    def __init__(self, root_dir=".", days=30):
        self.root_dir = Path(root_dir)
        self.days = days

    def get_git_log(self):
        """Получить git лог за период"""
        since_date = (datetime.now() - timedelta(days=self.days)).strftime('%Y-%m-%d')

        try:
            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--name-status', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=short'],
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
        """Парсинг git лога"""
        changes = []
        current_commit = None

        for line in log_output.split('\n'):
            if '|' in line and not line.startswith(('A\t', 'M\t', 'D\t')):
                # Информация о коммите
                parts = line.split('|')
                if len(parts) == 5:
                    current_commit = {
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4],
                        'files': []
                    }
                    changes.append(current_commit)
            elif current_commit and line.startswith(('A\t', 'M\t', 'D\t')):
                # Изменённый файл
                status, file_path = line.split('\t', 1)
                current_commit['files'].append({
                    'status': status,
                    'path': file_path
                })

        return changes

    def generate_report(self, changes):
        """Создать отчёт"""
        lines = []
        lines.append(f"# 📅 Последние изменения (за {self.days} дней)\n\n")

        # Группировать по датам
        by_date = {}

        for change in changes:
            date = change['date']
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(change)

        # Вывести по датам (новые первыми)
        for date in sorted(by_date.keys(), reverse=True):
            commits = by_date[date]
            lines.append(f"## {date} ({len(commits)} коммитов)\n\n")

            for commit in commits:
                lines.append(f"### {commit['message']}\n\n")
                lines.append(f"- **Автор**: {commit['author']}\n")
                lines.append(f"- **Коммит**: `{commit['hash'][:7]}`\n\n")

                if commit['files']:
                    lines.append("**Файлы:**\n")
                    for file_info in commit['files'][:10]:
                        status_icon = {'A': '➕', 'M': '✏️', 'D': '❌'}.get(file_info['status'], '•')
                        lines.append(f"- {status_icon} `{file_info['path']}`\n")
                    if len(commit['files']) > 10:
                        lines.append(f"\n...и ещё {len(commit['files']) - 10}\n")

                lines.append("\n")

        output_file = self.root_dir / "RECENT_CHANGES.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Recent Changes - Последние изменения')
    parser.add_argument('-d', '--days', type=int, default=30, help='Количество дней (по умолчанию: 30)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = RecentChanges(root_dir, days=args.days)

    print(f"📅 Анализ изменений за последние {args.days} дней...\n")

    log_output = analyzer.get_git_log()

    if log_output:
        changes = analyzer.parse_log(log_output)
        print(f"   Найдено коммитов: {len(changes)}\n")
        analyzer.generate_report(changes)
    else:
        print("⚠️  Не удалось получить git лог")


if __name__ == "__main__":
    main()
