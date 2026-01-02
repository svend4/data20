#!/usr/bin/env python3
"""
Changelog Generator - Генератор журнала изменений
Автоматически создаёт CHANGELOG.md из git истории

Следует стандарту Keep a Changelog и Semantic Versioning
"""

from pathlib import Path
import subprocess
import re
from datetime import datetime
from collections import defaultdict


class ChangelogGenerator:
    """Генератор CHANGELOG"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)

        # Категории изменений
        self.categories = {
            'added': [],      # Новая функциональность
            'changed': [],    # Изменения существующей функциональности
            'deprecated': [], # Скоро будет удалено
            'removed': [],    # Удалённая функциональность
            'fixed': [],      # Исправления багов
            'security': []    # Исправления безопасности
        }

    def get_git_tags(self):
        """Получить все git теги (версии)"""
        try:
            result = subprocess.run(
                ['git', 'tag', '--sort=-version:refname'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
        except:
            pass
        return []

    def get_commits_between(self, tag_from=None, tag_to='HEAD'):
        """Получить коммиты между версиями"""
        try:
            if tag_from:
                range_spec = f"{tag_from}..{tag_to}"
            else:
                range_spec = tag_to

            result = subprocess.run(
                ['git', 'log', range_spec, '--pretty=format:%H|%an|%ad|%s', '--date=short'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                commits = []
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) == 4:
                            commits.append({
                                'hash': parts[0],
                                'author': parts[1],
                                'date': parts[2],
                                'message': parts[3]
                            })
                return commits
        except:
            pass
        return []

    def categorize_commit(self, message):
        """Категоризировать коммит по сообщению"""
        message_lower = message.lower()

        # Ключевые слова для категорий
        if any(word in message_lower for word in ['add', 'добавлен', 'new', 'новый', 'feature', 'feat']):
            return 'added'
        elif any(word in message_lower for word in ['fix', 'исправлен', 'bugfix', 'bug', 'баг']):
            return 'fixed'
        elif any(word in message_lower for word in ['remove', 'delete', 'удалён', 'deleted']):
            return 'removed'
        elif any(word in message_lower for word in ['change', 'update', 'изменён', 'обновлён', 'modify']):
            return 'changed'
        elif any(word in message_lower for word in ['security', 'безопасность', 'sec']):
            return 'security'
        elif any(word in message_lower for word in ['deprecate', 'устарел']):
            return 'deprecated'
        else:
            return 'changed'  # По умолчанию

    def parse_commits(self, commits):
        """Парсинг коммитов по категориям"""
        categorized = defaultdict(list)

        for commit in commits:
            category = self.categorize_commit(commit['message'])
            categorized[category].append(commit)

        return categorized

    def generate_changelog(self):
        """Создать CHANGELOG.md"""
        print("📝 Генерация CHANGELOG.md...\n")

        lines = []
        lines.append("# Changelog\n\n")
        lines.append("> All notable changes to this project will be documented in this file.\n\n")
        lines.append("The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n")
        lines.append("and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n")

        # Получить теги
        tags = self.get_git_tags()

        if not tags:
            # Нет тегов - использовать все коммиты
            print("   Теги не найдены, используются все коммиты\n")

            lines.append(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}\n\n")

            commits = self.get_commits_between(tag_from=None, tag_to='HEAD')
            categorized = self.parse_commits(commits)

            self._write_version_changes(lines, categorized)

        else:
            # Unreleased changes (с последнего тега)
            print(f"   Найдено тегов: {len(tags)}\n")

            unreleased = self.get_commits_between(tag_from=tags[0], tag_to='HEAD')
            if unreleased:
                lines.append(f"## [Unreleased]\n\n")
                categorized = self.parse_commits(unreleased)
                self._write_version_changes(lines, categorized)

            # Released versions
            for i, tag in enumerate(tags):
                tag_from = tags[i + 1] if i + 1 < len(tags) else None

                # Получить дату тега
                try:
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%ad', '--date=short', tag],
                        cwd=self.root_dir,
                        capture_output=True,
                        text=True
                    )
                    tag_date = result.stdout.strip() if result.returncode == 0 else ''
                except:
                    tag_date = ''

                lines.append(f"## [{tag}] - {tag_date}\n\n")

                commits = self.get_commits_between(tag_from=tag_from, tag_to=tag)
                categorized = self.parse_commits(commits)

                self._write_version_changes(lines, categorized)

        # Сохранить
        output_file = self.root_dir / "CHANGELOG.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ CHANGELOG создан: {output_file}")

    def _write_version_changes(self, lines, categorized):
        """Записать изменения версии"""
        # Порядок категорий
        order = ['added', 'changed', 'deprecated', 'removed', 'fixed', 'security']

        # Названия категорий
        titles = {
            'added': 'Added',
            'changed': 'Changed',
            'deprecated': 'Deprecated',
            'removed': 'Removed',
            'fixed': 'Fixed',
            'security': 'Security'
        }

        has_changes = False

        for category in order:
            if category in categorized and categorized[category]:
                has_changes = True
                lines.append(f"### {titles[category]}\n\n")

                for commit in categorized[category]:
                    # Очистить сообщение (убрать префиксы типа [Feature])
                    message = commit['message']
                    message = re.sub(r'^\[.*?\]\s*', '', message)
                    message = re.sub(r'^(feat|fix|chore|docs|style|refactor|test):\s*', '', message, flags=re.I)

                    lines.append(f"- {message} ({commit['hash'][:7]})\n")

                lines.append("\n")

        if not has_changes:
            lines.append("No changes.\n\n")

    def generate_version_summary(self):
        """Создать краткую сводку версий"""
        tags = self.get_git_tags()

        lines = []
        lines.append("# 📋 Version Summary\n\n")

        if not tags:
            lines.append("No tagged versions yet.\n")
        else:
            lines.append(f"**Total versions**: {len(tags)}\n\n")

            for tag in tags:
                # Дата и автор тега
                try:
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%ad|%an', '--date=short', tag],
                        cwd=self.root_dir,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        date, author = result.stdout.strip().split('|')
                    else:
                        date, author = '', ''
                except:
                    date, author = '', ''

                # Количество коммитов в версии
                commits = self.get_commits_between(tag_from=None, tag_to=tag)

                lines.append(f"## {tag}\n\n")
                lines.append(f"- **Date**: {date}\n")
                lines.append(f"- **Author**: {author}\n")
                lines.append(f"- **Commits**: {len(commits)}\n\n")

        output_file = self.root_dir / "VERSION_SUMMARY.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Сводка версий: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Changelog Generator - Генератор CHANGELOG')
    parser.add_argument('-s', '--summary', action='store_true', help='Создать сводку версий')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = ChangelogGenerator(root_dir)

    generator.generate_changelog()

    if args.summary:
        generator.generate_version_summary()


if __name__ == "__main__":
    main()
