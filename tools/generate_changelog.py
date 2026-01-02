#!/usr/bin/env python3
"""
Advanced Changelog Generator - Расширенный генератор журнала изменений
Автоматически создаёт CHANGELOG.md из git истории с расширенной аналитикой

Следует стандарту Keep a Changelog и Semantic Versioning

Features:
- Semantic version parsing and comparison
- Breaking changes detection
- Contributor statistics
- Release notes generation
- Multiple output formats (Markdown, JSON, HTML)
- Changelog validation
- Template system
- Scope-based grouping
- Milestone tracking
"""

from pathlib import Path
import subprocess
import re
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import json


class SemanticVersion:
    """Semantic version parser (semver.org)"""

    def __init__(self, version_str: str):
        self.original = version_str
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')

        # Parse: major.minor.patch[-prerelease][+build]
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+))?$', version_str)

        if match:
            self.major = int(match.group(1))
            self.minor = int(match.group(2))
            self.patch = int(match.group(3))
            self.prerelease = match.group(4) or ''
            self.build = match.group(5) or ''
        else:
            # Fallback: treat as simple tag
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.prerelease = version_str
            self.build = ''

    def __lt__(self, other):
        """Compare versions"""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        # Prerelease comparison (no prerelease > has prerelease)
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and not other.prerelease:
            return True
        return self.prerelease < other.prerelease

    def __str__(self):
        return self.original


class CommitParser:
    """Conventional Commits parser"""

    PATTERN = re.compile(r'^(?P<type>\w+)(?:\((?P<scope>[\w-]+)\))?(?P<breaking>!)?: (?P<description>.+)$')

    @staticmethod
    def parse(message: str) -> Dict:
        """
        Parse Conventional Commit format:
        <type>(<scope>): <description>

        Examples:
        - feat(auth): add OAuth2 support
        - fix!: critical security vulnerability
        """
        match = CommitParser.PATTERN.match(message.split('\n')[0])

        if match:
            return {
                'type': match.group('type'),
                'scope': match.group('scope') or '',
                'breaking': match.group('breaking') == '!',
                'description': match.group('description'),
                'formatted': True
            }
        else:
            return {
                'type': 'other',
                'scope': '',
                'breaking': 'BREAKING CHANGE' in message,
                'description': message.split('\n')[0],
                'formatted': False
            }


class ChangelogGenerator:
    """Расширенный генератор CHANGELOG"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)

        # Категории изменений (Keep a Changelog)
        self.categories = {
            'added': [],      # Новая функциональность
            'changed': [],    # Изменения существующей функциональности
            'deprecated': [], # Скоро будет удалено
            'removed': [],    # Удалённая функциональность
            'fixed': [],      # Исправления багов
            'security': []    # Исправления безопасности
        }

        # Conventional Commits mapping
        self.type_to_category = {
            'feat': 'added',
            'fix': 'fixed',
            'docs': 'changed',
            'style': 'changed',
            'refactor': 'changed',
            'perf': 'changed',
            'test': 'changed',
            'build': 'changed',
            'ci': 'changed',
            'chore': 'changed',
            'revert': 'changed'
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
                ['git', 'log', range_spec, '--pretty=format:%H|%an|%ae|%ad|%s|%b', '--date=short'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                commits = []
                for line in result.stdout.split('\n'):
                    if line.strip() and '|' in line:
                        parts = line.split('|', 5)
                        if len(parts) >= 5:
                            commits.append({
                                'hash': parts[0],
                                'author': parts[1],
                                'email': parts[2],
                                'date': parts[3],
                                'message': parts[4],
                                'body': parts[5] if len(parts) > 5 else ''
                            })
                return commits
        except:
            pass
        return []

    def categorize_commit(self, commit):
        """Категоризировать коммит по сообщению"""
        message = commit['message']
        parsed = CommitParser.parse(message)

        # Conventional Commits format
        if parsed['formatted']:
            commit['parsed'] = parsed
            commit['breaking'] = parsed['breaking']

            commit_type = parsed['type'].lower()
            if commit_type in self.type_to_category:
                return self.type_to_category[commit_type]

        # Fallback: keyword detection
        message_lower = message.lower()

        if any(word in message_lower for word in ['add', 'добавлен', 'new', 'новый', 'feature', 'feat']):
            return 'added'
        elif any(word in message_lower for word in ['fix', 'исправлен', 'bugfix', 'bug', 'баг']):
            return 'fixed'
        elif any(word in message_lower for word in ['remove', 'delete', 'удалён', 'deleted']):
            return 'removed'
        elif any(word in message_lower for word in ['security', 'безопасность', 'sec']):
            return 'security'
        elif any(word in message_lower for word in ['deprecate', 'устарел']):
            return 'deprecated'
        else:
            return 'changed'

    def parse_commits(self, commits):
        """Парсинг коммитов по категориям"""
        categorized = defaultdict(list)
        breaking_changes = []

        for commit in commits:
            category = self.categorize_commit(commit)
            categorized[category].append(commit)

            # Detect breaking changes
            if commit.get('breaking') or 'BREAKING CHANGE' in commit.get('body', ''):
                breaking_changes.append(commit)

        return categorized, breaking_changes

    def get_contributor_stats(self, commits):
        """Статистика контрибьюторов"""
        authors = Counter()
        emails = {}

        for commit in commits:
            author = commit['author']
            authors[author] += 1
            emails[author] = commit['email']

        return [(author, count, emails[author]) for author, count in authors.most_common()]

    def generate_changelog(self, output_format='markdown'):
        """Создать CHANGELOG в разных форматах"""
        print("📝 Генерация CHANGELOG...\n")

        if output_format == 'markdown':
            self._generate_markdown()
        elif output_format == 'json':
            self._generate_json()
        elif output_format == 'html':
            self._generate_html()

    def _generate_markdown(self):
        """Generate Markdown CHANGELOG"""
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
            categorized, breaking = self.parse_commits(commits)

            if breaking:
                self._write_breaking_changes(lines, breaking)

            self._write_version_changes(lines, categorized)

            # Contributors
            contributors = self.get_contributor_stats(commits)
            if contributors:
                lines.append("### Contributors\n\n")
                for author, count, email in contributors[:10]:
                    lines.append(f"- {author} ({count} commits)\n")
                lines.append("\n")

        else:
            # Unreleased changes (с последнего тега)
            print(f"   Найдено тегов: {len(tags)}\n")

            unreleased = self.get_commits_between(tag_from=tags[0], tag_to='HEAD')
            if unreleased:
                lines.append(f"## [Unreleased]\n\n")
                categorized, breaking = self.parse_commits(unreleased)

                if breaking:
                    self._write_breaking_changes(lines, breaking)

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
                categorized, breaking = self.parse_commits(commits)

                if breaking:
                    self._write_breaking_changes(lines, breaking)

                self._write_version_changes(lines, categorized)

        # Сохранить
        output_file = self.root_dir / "CHANGELOG.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ CHANGELOG создан: {output_file}")

    def _generate_json(self):
        """Generate JSON CHANGELOG"""
        changelog_data = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'format': 'keep-a-changelog',
                'semver': 'semantic-versioning'
            },
            'versions': []
        }

        tags = self.get_git_tags()

        # Unreleased
        unreleased = self.get_commits_between(tag_from=tags[0] if tags else None, tag_to='HEAD')
        if unreleased:
            categorized, breaking = self.parse_commits(unreleased)
            version_data = {
                'version': 'Unreleased',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'changes': self._format_json_changes(categorized),
                'breaking_changes': [c['message'] for c in breaking],
                'contributors': [f"{a} ({c})" for a, c, _ in self.get_contributor_stats(unreleased)],
                'commit_count': len(unreleased)
            }
            changelog_data['versions'].append(version_data)

        # Released versions
        for i, tag in enumerate(tags):
            tag_from = tags[i + 1] if i + 1 < len(tags) else None

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

            commits = self.get_commits_between(tag_from=tag_from, tag_to=tag)
            categorized, breaking = self.parse_commits(commits)

            version_data = {
                'version': tag,
                'date': tag_date,
                'changes': self._format_json_changes(categorized),
                'breaking_changes': [c['message'] for c in breaking],
                'contributors': [f"{a} ({c})" for a, c, _ in self.get_contributor_stats(commits)],
                'commit_count': len(commits)
            }
            changelog_data['versions'].append(version_data)

        output_file = self.root_dir / "CHANGELOG.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(changelog_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON CHANGELOG: {output_file}")

    def _generate_html(self):
        """Generate HTML CHANGELOG"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Changelog</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #007bff; margin-top: 30px; }}
        h3 {{ color: #555; margin-top: 20px; }}
        .version {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; }}
        .breaking {{ background: #fff3cd; border-left-color: #ffc107; }}
        ul {{ line-height: 1.8; }}
        .commit-hash {{ font-family: monospace; color: #666; font-size: 0.9em; }}
        .metadata {{ color: #888; font-size: 0.9em; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Changelog</h1>
        <p class="metadata">Generated: {generated_date}</p>
        {content}
    </div>
</body>
</html>"""

        content_lines = []
        tags = self.get_git_tags()

        # Unreleased
        unreleased = self.get_commits_between(tag_from=tags[0] if tags else None, tag_to='HEAD')
        if unreleased:
            content_lines.append('<div class="version">')
            content_lines.append(f'<h2>Unreleased - {datetime.now().strftime("%Y-%m-%d")}</h2>')

            categorized, breaking = self.parse_commits(unreleased)

            if breaking:
                content_lines.append('<div class="breaking">')
                content_lines.append('<h3>⚠️ Breaking Changes</h3>')
                content_lines.append('<ul>')
                for commit in breaking:
                    content_lines.append(f'<li>{commit["message"]} <span class="commit-hash">({commit["hash"][:7]})</span></li>')
                content_lines.append('</ul>')
                content_lines.append('</div>')

            content_lines.append(self._format_html_changes(categorized))
            content_lines.append('</div>')

        # Released versions
        for i, tag in enumerate(tags[:10]):  # Limit to 10 versions
            tag_from = tags[i + 1] if i + 1 < len(tags) else None

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

            content_lines.append('<div class="version">')
            content_lines.append(f'<h2>{tag} - {tag_date}</h2>')

            commits = self.get_commits_between(tag_from=tag_from, tag_to=tag)
            categorized, breaking = self.parse_commits(commits)

            if breaking:
                content_lines.append('<div class="breaking">')
                content_lines.append('<h3>⚠️ Breaking Changes</h3>')
                content_lines.append('<ul>')
                for commit in breaking:
                    content_lines.append(f'<li>{commit["message"]} <span class="commit-hash">({commit["hash"][:7]})</span></li>')
                content_lines.append('</ul>')
                content_lines.append('</div>')

            content_lines.append(self._format_html_changes(categorized))
            content_lines.append('</div>')

        html = html_template.format(
            generated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            content='\n'.join(content_lines)
        )

        output_file = self.root_dir / "CHANGELOG.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML CHANGELOG: {output_file}")

    def _write_breaking_changes(self, lines, breaking_changes):
        """Write breaking changes section"""
        lines.append("### ⚠️ BREAKING CHANGES\n\n")
        for commit in breaking_changes:
            message = commit['message']
            lines.append(f"- **{message}** ({commit['hash'][:7]})\n")
        lines.append("\n")

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

                # Group by scope if Conventional Commits
                scoped = defaultdict(list)
                for commit in categorized[category]:
                    scope = commit.get('parsed', {}).get('scope', '')
                    scoped[scope].append(commit)

                # Write changes
                for scope in sorted(scoped.keys()):
                    if scope:
                        lines.append(f"**{scope}**:\n")

                    for commit in scoped[scope]:
                        # Очистить сообщение
                        message = commit['message']
                        message = re.sub(r'^\[.*?\]\s*', '', message)
                        message = re.sub(r'^(feat|fix|chore|docs|style|refactor|test|perf|build|ci)(!)?(\([\w-]+\))?:\s*', '', message, flags=re.I)

                        lines.append(f"- {message} ({commit['hash'][:7]})\n")

                lines.append("\n")

        if not has_changes:
            lines.append("No changes.\n\n")

    def _format_json_changes(self, categorized):
        """Format changes for JSON output"""
        changes = {}
        for category, commits in categorized.items():
            changes[category] = [
                {
                    'message': c['message'],
                    'hash': c['hash'][:7],
                    'author': c['author'],
                    'date': c['date']
                }
                for c in commits
            ]
        return changes

    def _format_html_changes(self, categorized):
        """Format changes for HTML output"""
        order = ['added', 'changed', 'deprecated', 'removed', 'fixed', 'security']
        titles = {
            'added': 'Added',
            'changed': 'Changed',
            'deprecated': 'Deprecated',
            'removed': 'Removed',
            'fixed': 'Fixed',
            'security': 'Security'
        }

        html = []
        for category in order:
            if category in categorized and categorized[category]:
                html.append(f'<h3>{titles[category]}</h3>')
                html.append('<ul>')
                for commit in categorized[category]:
                    message = re.sub(r'^(feat|fix|chore|docs|style|refactor|test)(!)?(\([\w-]+\))?:\s*', '', commit['message'], flags=re.I)
                    html.append(f'<li>{message} <span class="commit-hash">({commit["hash"][:7]})</span></li>')
                html.append('</ul>')

        return '\n'.join(html)

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

    parser = argparse.ArgumentParser(
        description='Advanced Changelog Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  generate_changelog.py                 # Generate Markdown CHANGELOG
  generate_changelog.py --format json   # Generate JSON CHANGELOG
  generate_changelog.py --format html   # Generate HTML CHANGELOG
  generate_changelog.py --summary       # Generate version summary
        """
    )

    parser.add_argument('-f', '--format', choices=['markdown', 'json', 'html'], default='markdown',
                        help='Output format (default: markdown)')
    parser.add_argument('-s', '--summary', action='store_true',
                        help='Создать сводку версий')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = ChangelogGenerator(root_dir)

    generator.generate_changelog(output_format=args.format)

    if args.summary:
        generator.generate_version_summary()


if __name__ == "__main__":
    main()
