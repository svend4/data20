#!/usr/bin/env python3
"""
Version History Analysis - Анализ истории версий
Детальный анализ эволюции статей через git историю

Вдохновлено: Wikipedia revision history, Git blame
"""

from pathlib import Path
import subprocess
from datetime import datetime
from collections import defaultdict
import json


class VersionHistoryAnalyzer:
    """Анализатор истории версий"""

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
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = VersionHistoryAnalyzer(root_dir)
    analyzer.analyze_all()
    analyzer.generate_report()
    analyzer.save_json()


if __name__ == "__main__":
    main()
