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
import re


class ContributorAnalyzer:
    """Детальный анализ контрибьюторов"""

    def __init__(self, contributors, changes):
        self.contributors = contributors
        self.changes = changes

    def analyze_contributor_patterns(self, author):
        """
        Анализ паттернов работы контрибьютора

        Args:
            author: имя автора

        Returns:
            dict: паттерны работы
        """
        if author not in self.contributors:
            return None

        stats = self.contributors[author]
        author_commits = [c for c in self.changes if c['author'] == author]

        if not author_commits:
            return None

        # Анализ времени работы
        hours = [c['hour'] for c in author_commits]
        most_active_hour = Counter(hours).most_common(1)[0][0] if hours else 12

        # Определить "тип" контрибьютора
        avg_commit_size = (stats['insertions'] + stats['deletions']) / stats['commits'] if stats['commits'] > 0 else 0

        if avg_commit_size > 500:
            contributor_type = 'major_refactorer'  # Большие изменения
        elif avg_commit_size > 100:
            contributor_type = 'feature_developer'  # Средние изменения
        else:
            contributor_type = 'bug_fixer'  # Маленькие изменения

        # Частота коммитов
        unique_dates = len(set(stats['dates']))
        commit_frequency = stats['commits'] / unique_dates if unique_dates > 0 else 0

        return {
            'author': author,
            'most_active_hour': most_active_hour,
            'contributor_type': contributor_type,
            'avg_commit_size': int(avg_commit_size),
            'commit_frequency': round(commit_frequency, 2),
            'unique_days': unique_dates,
            'commits_per_day': round(stats['commits'] / unique_dates, 2) if unique_dates > 0 else 0
        }

    def calculate_specialization(self, author):
        """
        Вычислить специализацию контрибьютора по типам файлов

        Args:
            author: имя автора

        Returns:
            dict: специализация по категориям
        """
        author_commits = [c for c in self.changes if c['author'] == author]
        category_changes = defaultdict(int)

        for commit in author_commits:
            for file_info in commit['files']:
                # Категоризация файлов
                path = Path(file_info['path'])
                if path.suffix == '.py':
                    category_changes['python'] += 1
                elif path.suffix == '.md':
                    category_changes['docs'] += 1
                elif path.suffix in ['.json', '.yaml', '.yml']:
                    category_changes['config'] += 1
                elif path.suffix in ['.sh', '.bash']:
                    category_changes['scripts'] += 1
                else:
                    category_changes['other'] += 1

        total = sum(category_changes.values())
        if total == 0:
            return {}

        # Преобразовать в проценты
        specialization = {
            category: round((count / total) * 100, 1)
            for category, count in category_changes.items()
        }

        return dict(sorted(specialization.items(), key=lambda x: -x[1]))

    def find_collaboration_pairs(self):
        """
        Найти пары контрибьюторов, работающих над одними файлами

        Returns:
            list: пары с коэффициентом сотрудничества
        """
        # Файлы, измененные каждым контрибьютором
        contributor_files = defaultdict(set)

        for commit in self.changes:
            author = commit['author']
            for file_info in commit['files']:
                contributor_files[author].add(file_info['path'])

        # Найти пересечения
        collaborations = []
        authors = list(contributor_files.keys())

        for i, author1 in enumerate(authors):
            for author2 in authors[i+1:]:
                common_files = contributor_files[author1] & contributor_files[author2]
                if common_files:
                    collaboration_score = len(common_files)
                    collaborations.append({
                        'authors': (author1, author2),
                        'common_files': len(common_files),
                        'collaboration_score': collaboration_score
                    })

        # Сортировать по score
        collaborations.sort(key=lambda x: -x['collaboration_score'])

        return collaborations[:10]

    def calculate_bus_factor(self):
        """
        Вычислить bus factor (сколько людей нужно потерять, чтобы проект остановился)

        Основан на распределении коммитов.

        Returns:
            dict: bus factor метрики
        """
        total_commits = sum(stats['commits'] for stats in self.contributors.values())

        # Сортировать контрибьюторов по количеству коммитов
        sorted_contributors = sorted(
            self.contributors.items(),
            key=lambda x: -x[1]['commits']
        )

        # Найти минимальное число контрибьюторов, делающих 50% коммитов
        cumulative_commits = 0
        bus_factor = 0

        for author, stats in sorted_contributors:
            cumulative_commits += stats['commits']
            bus_factor += 1

            if cumulative_commits >= total_commits * 0.5:
                break

        # Bus factor < 3 - критично!
        risk_level = 'critical' if bus_factor < 3 else 'medium' if bus_factor < 5 else 'healthy'

        return {
            'bus_factor': bus_factor,
            'risk_level': risk_level,
            'top_contributors_percentage': round((cumulative_commits / total_commits) * 100, 1) if total_commits > 0 else 0
        }


class ChangeImpactAnalyzer:
    """Анализ влияния изменений"""

    def __init__(self, changes, file_activity):
        self.changes = changes
        self.file_activity = file_activity

    def calculate_risk_score(self, commit):
        """
        Вычислить risk score для коммита

        Факторы риска:
        - Много измененных строк
        - Изменения в core файлах
        - Изменения конфиг файлов
        - Большое количество файлов

        Args:
            commit: данные коммита

        Returns:
            dict: risk score и причины
        """
        risk_score = 0
        risk_factors = []

        # Размер изменений
        total_changes = commit['stats']['insertions'] + commit['stats']['deletions']

        if total_changes > 1000:
            risk_score += 40
            risk_factors.append('Очень большие изменения (>1000 строк)')
        elif total_changes > 500:
            risk_score += 25
            risk_factors.append('Большие изменения (>500 строк)')
        elif total_changes > 200:
            risk_score += 10
            risk_factors.append('Средние изменения (>200 строк)')

        # Количество файлов
        files_count = len(commit['files'])

        if files_count > 20:
            risk_score += 30
            risk_factors.append(f'Много файлов ({files_count})')
        elif files_count > 10:
            risk_score += 15
            risk_factors.append(f'Умеренно много файлов ({files_count})')

        # Изменения в конфиг файлах
        config_files = [f for f in commit['files'] if Path(f['path']).suffix in ['.json', '.yaml', '.yml', '.toml']]
        if config_files:
            risk_score += 20
            risk_factors.append(f'Изменения в конфиг файлах ({len(config_files)})')

        # Изменения в часто изменяемых файлах (core)
        core_files = [f for f in commit['files'] if self.file_activity.get(f['path'], 0) > 10]
        if core_files:
            risk_score += 15
            risk_factors.append(f'Изменения в core файлах ({len(core_files)})')

        # Удаление файлов
        deletions = [f for f in commit['files'] if f['status'] == 'D']
        if deletions:
            risk_score += 25
            risk_factors.append(f'Удаление файлов ({len(deletions)})')

        # Risk level
        if risk_score >= 80:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'risk_factors': risk_factors
        }

    def identify_hotspots(self, top_n=10):
        """
        Определить hotspots (файлы с частыми изменениями)

        Args:
            top_n: количество hotspots

        Returns:
            list: hotspots с метриками
        """
        hotspots = []

        for file_path, change_count in sorted(self.file_activity.items(), key=lambda x: -x[1])[:top_n]:
            # Вычислить churn (количество строк изменено во всех коммитах)
            total_churn = 0

            for commit in self.changes:
                for file_info in commit['files']:
                    if file_info['path'] == file_path:
                        total_churn += commit['stats']['insertions'] + commit['stats']['deletions']

            avg_churn = total_churn / change_count if change_count > 0 else 0

            hotspots.append({
                'file': file_path,
                'changes': change_count,
                'total_churn': total_churn,
                'avg_churn': round(avg_churn, 1)
            })

        return hotspots

    def analyze_change_velocity(self):
        """
        Анализ скорости изменений по времени

        Returns:
            dict: velocity тренды
        """
        # Группировать изменения по датам
        daily_stats = defaultdict(lambda: {'commits': 0, 'changes': 0})

        for commit in self.changes:
            date = commit['date']
            daily_stats[date]['commits'] += 1
            daily_stats[date]['changes'] += commit['stats']['insertions'] + commit['stats']['deletions']

        # Сортировать по дате
        sorted_dates = sorted(daily_stats.keys())

        if len(sorted_dates) < 2:
            return {'trend': 'insufficient_data'}

        # Разделить на первую и вторую половину
        mid_point = len(sorted_dates) // 2
        first_half = sorted_dates[:mid_point]
        second_half = sorted_dates[mid_point:]

        first_avg = sum(daily_stats[d]['commits'] for d in first_half) / len(first_half)
        second_avg = sum(daily_stats[d]['commits'] for d in second_half) / len(second_half)

        # Определить тренд
        if second_avg > first_avg * 1.2:
            trend = 'accelerating'
        elif second_avg < first_avg * 0.8:
            trend = 'decelerating'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'first_half_avg': round(first_avg, 2),
            'second_half_avg': round(second_avg, 2),
            'change_percentage': round(((second_avg - first_avg) / first_avg * 100), 1) if first_avg > 0 else 0
        }


class CommitPatternAnalyzer:
    """Анализ паттернов коммитов"""

    def __init__(self, changes):
        self.changes = changes

    def categorize_commit_message(self, message):
        """
        Категоризировать коммит по сообщению

        Использует conventional commits pattern.

        Args:
            message: сообщение коммита

        Returns:
            str: категория
        """
        message_lower = message.lower()

        # Conventional commits patterns
        patterns = {
            'feat': r'^(feat|feature|✨)',
            'fix': r'^(fix|bugfix|🐛)',
            'docs': r'^(docs|documentation|📝)',
            'style': r'^(style|💄)',
            'refactor': r'^(refactor|♻️)',
            'perf': r'^(perf|performance|⚡)',
            'test': r'^(test|✅)',
            'build': r'^(build|👷)',
            'ci': r'^(ci|💚)',
            'chore': r'^(chore|🔧)',
        }

        for category, pattern in patterns.items():
            if re.search(pattern, message_lower):
                return category

        # Эвристики для некатегоризированных коммитов
        if any(word in message_lower for word in ['add', 'create', 'implement']):
            return 'feat'
        elif any(word in message_lower for word in ['fix', 'resolve', 'correct']):
            return 'fix'
        elif any(word in message_lower for word in ['update', 'improve', 'enhance']):
            return 'improvement'
        elif any(word in message_lower for word in ['remove', 'delete', 'clean']):
            return 'cleanup'
        else:
            return 'other'

    def analyze_commit_types(self):
        """
        Анализ типов коммитов

        Returns:
            dict: статистика по типам
        """
        type_stats = defaultdict(int)

        for commit in self.changes:
            commit_type = self.categorize_commit_message(commit['message'])
            type_stats[commit_type] += 1

        return dict(sorted(type_stats.items(), key=lambda x: -x[1]))

    def analyze_commit_sizes(self):
        """
        Анализ размеров коммитов

        Returns:
            dict: статистика размеров
        """
        sizes = {
            'tiny': 0,      # < 10 строк
            'small': 0,     # 10-50 строк
            'medium': 0,    # 50-200 строк
            'large': 0,     # 200-500 строк
            'huge': 0       # > 500 строк
        }

        for commit in self.changes:
            total = commit['stats']['insertions'] + commit['stats']['deletions']

            if total < 10:
                sizes['tiny'] += 1
            elif total < 50:
                sizes['small'] += 1
            elif total < 200:
                sizes['medium'] += 1
            elif total < 500:
                sizes['large'] += 1
            else:
                sizes['huge'] += 1

        return sizes

    def find_message_patterns(self):
        """
        Найти часто используемые слова в сообщениях коммитов

        Returns:
            list: топ слов
        """
        all_words = []

        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'to', 'in', 'is', 'a', 'of', 'with', 'from', 'by'
        }

        for commit in self.changes:
            message = commit['message'].lower()
            # Удалить emoji и спецсимволы
            message = re.sub(r'[^\w\s]', ' ', message)
            words = message.split()

            for word in words:
                if len(word) > 2 and word not in stop_words:
                    all_words.append(word)

        word_freq = Counter(all_words)
        return word_freq.most_common(15)

    def calculate_message_quality_score(self, message):
        """
        Оценить качество сообщения коммита

        Args:
            message: сообщение коммита

        Returns:
            int: score 0-100
        """
        score = 0

        # Длина сообщения (оптимально 20-100 символов)
        length = len(message)
        if 20 <= length <= 100:
            score += 30
        elif 10 <= length < 20 or 100 < length <= 150:
            score += 15

        # Начинается с заглавной буквы
        if message and message[0].isupper():
            score += 10

        # Содержит глагол действия
        action_verbs = ['add', 'fix', 'update', 'remove', 'refactor', 'implement', 'improve', 'enhance']
        if any(verb in message.lower() for verb in action_verbs):
            score += 20

        # Соответствует conventional commits
        if re.match(r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: ', message.lower()):
            score += 30

        # Не заканчивается точкой (best practice)
        if message and message[-1] != '.':
            score += 10

        return min(score, 100)


class ActivityVisualizer:
    """Визуализация активности"""

    def __init__(self, changes, contributors, hourly_activity, daily_activity):
        self.changes = changes
        self.contributors = contributors
        self.hourly_activity = hourly_activity
        self.daily_activity = daily_activity

    def generate_html_dashboard(self):
        """
        Создать HTML dashboard с визуализацией активности

        Returns:
            str: HTML контент
        """
        # Подготовить данные
        total_commits = len(self.changes)
        total_contributors = len(self.contributors)

        # Топ контрибьюторы
        top_contributors = sorted(
            self.contributors.items(),
            key=lambda x: -x[1]['commits']
        )[:10]

        # Активность по часам
        hours = list(range(24))
        hourly_commits = [self.hourly_activity.get(h, 0) for h in hours]

        # Активность по дням (последние 30)
        sorted_dates = sorted(self.daily_activity.keys(), reverse=True)[:30]
        daily_commits = [self.daily_activity[d] for d in reversed(sorted_dates)]
        daily_labels = list(reversed(sorted_dates))

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Activity Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .stat-label {{
            color: #666;
            font-size: 1.1em;
        }}

        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}

        .chart-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }}

        .contributors-list {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .contributor-item {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .contributor-item:last-child {{
            border-bottom: none;
        }}

        .contributor-name {{
            font-weight: 600;
            font-size: 1.1em;
        }}

        .contributor-stats {{
            color: #666;
            font-size: 0.95em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Activity Dashboard</h1>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_commits}</div>
                <div class="stat-label">Коммитов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_contributors}</div>
                <div class="stat-label">Контрибьюторов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(c['stats']['insertions'] for c in self.changes):,}</div>
                <div class="stat-label">Добавлено строк</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(c['stats']['deletions'] for c in self.changes):,}</div>
                <div class="stat-label">Удалено строк</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📈 Активность по дням</div>
            <canvas id="dailyChart"></canvas>
        </div>

        <div class="chart-container">
            <div class="chart-title">⏰ Активность по часам</div>
            <canvas id="hourlyChart"></canvas>
        </div>

        <div class="contributors-list">
            <div class="chart-title">👥 Топ контрибьюторов</div>
            {"".join(f'''
            <div class="contributor-item">
                <div class="contributor-name">{i}. {author}</div>
                <div class="contributor-stats">
                    {stats['commits']} коммитов | +{stats['insertions']:,} / -{stats['deletions']:,} строк
                </div>
            </div>
            ''' for i, (author, stats) in enumerate(top_contributors, 1))}
        </div>
    </div>

    <script>
        // Daily activity chart
        const dailyCtx = document.getElementById('dailyChart').getContext('2d');
        new Chart(dailyCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(daily_labels)},
                datasets: [{{
                    label: 'Коммитов',
                    data: {daily_commits},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Hourly activity chart
        const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
        new Chart(hourlyCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([f"{h:02d}:00" for h in hours])},
                datasets: [{{
                    label: 'Коммитов',
                    data: {hourly_commits},
                    backgroundColor: '#764ba2'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        return html


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

    parser = argparse.ArgumentParser(
        description='🔍 Advanced Recent Changes - Продвинутый анализ истории изменений',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --days 30                     # Базовый отчёт за 30 дней
  %(prog)s --html                        # HTML dashboard с Chart.js
  %(prog)s --contributors                # Детальный анализ контрибьюторов
  %(prog)s --impact                      # Анализ влияния и риск-скоринг
  %(prog)s --patterns                    # Анализ паттернов коммитов
  %(prog)s --bus-factor                  # Вычислить bus factor
  %(prog)s --hotspots 15                 # Топ 15 hotspots
  %(prog)s --velocity                    # Анализ velocity тренда
  %(prog)s --all --days 60               # Все анализы за 60 дней
  %(prog)s --json --rss                  # Экспорт в JSON и RSS

Новые возможности:
  • Contributor Analysis: паттерны работы, специализация, коллаборация
  • Impact Analysis: risk scoring, hotspots, velocity
  • Pattern Analysis: conventional commits, message quality
  • Activity Visualization: интерактивный HTML dashboard с Chart.js
        """
    )

    # Основные параметры
    parser.add_argument('-d', '--days', type=int, default=30,
                       help='Количество дней истории (по умолчанию: 30)')
    parser.add_argument('--path', type=str, default='.',
                       help='Путь к репозиторию (по умолчанию: текущая директория)')

    # Новые анализы
    parser.add_argument('--html', action='store_true',
                       help='🎨 Создать HTML dashboard с визуализацией активности')
    parser.add_argument('--contributors', action='store_true',
                       help='👥 Детальный анализ контрибьюторов (паттерны, специализация)')
    parser.add_argument('--impact', action='store_true',
                       help='💥 Анализ влияния изменений (risk scoring, hotspots)')
    parser.add_argument('--patterns', action='store_true',
                       help='📋 Анализ паттернов коммитов (conventional commits, quality)')
    parser.add_argument('--bus-factor', action='store_true',
                       help='🚌 Вычислить bus factor и риски проекта')
    parser.add_argument('--hotspots', type=int, metavar='N',
                       help='🔥 Найти топ N hotspots (часто изменяемые файлы)')
    parser.add_argument('--velocity', action='store_true',
                       help='📈 Анализ velocity (скорость изменений по времени)')
    parser.add_argument('--author', type=str, metavar='NAME',
                       help='🔎 Анализ конкретного контрибьютора')

    # Экспорт
    parser.add_argument('--json', action='store_true',
                       help='💾 Экспорт в JSON')
    parser.add_argument('--rss', action='store_true',
                       help='📡 Создать RSS feed')
    parser.add_argument('--csv', action='store_true',
                       help='📊 Экспорт статистики в CSV')

    # Специальные
    parser.add_argument('--all', action='store_true',
                       help='🎯 Запустить все доступные анализы')

    args = parser.parse_args()

    # Определить root_dir
    if args.path == '.':
        script_dir = Path(__file__).parent
        root_dir = script_dir.parent
    else:
        root_dir = Path(args.path)

    # Создать главный analyzer
    analyzer = AdvancedRecentChanges(root_dir, days=args.days)

    print(f"📅 Продвинутый анализ изменений за последние {args.days} дней...")
    print(f"📂 Репозиторий: {root_dir}\n")

    # Получить данные
    log_output = analyzer.get_git_log()

    if not log_output:
        print("⚠️  Не удалось получить git лог")
        return

    analyzer.changes = analyzer.parse_log(log_output)
    print(f"✅ Найдено коммитов: {len(analyzer.changes)}")
    print(f"✅ Контрибьюторов: {len(analyzer.contributors)}")
    print(f"✅ Файлов изменено: {len(analyzer.file_activity)}\n")

    # Базовый отчёт всегда генерируется
    analyzer.generate_report()

    # --all активирует все анализы
    if args.all:
        args.html = True
        args.contributors = True
        args.impact = True
        args.patterns = True
        args.bus_factor = True
        args.hotspots = 15
        args.velocity = True
        args.json = True
        args.rss = True
        args.csv = True

    # HTML Dashboard
    if args.html:
        print("\n🎨 Генерация HTML dashboard...")
        visualizer = ActivityVisualizer(
            analyzer.changes,
            dict(analyzer.contributors),
            dict(analyzer.hourly_activity),
            dict(analyzer.daily_activity)
        )
        html_content = visualizer.generate_html_dashboard()

        html_file = root_dir / "activity_dashboard.html"
        html_file.write_text(html_content, encoding='utf-8')
        print(f"✅ HTML dashboard: {html_file}")

    # Contributor Analysis
    if args.contributors or args.author:
        print("\n👥 Анализ контрибьюторов...")
        contributor_analyzer = ContributorAnalyzer(
            dict(analyzer.contributors),
            analyzer.changes
        )

        if args.author:
            # Анализ конкретного автора
            pattern = contributor_analyzer.analyze_contributor_patterns(args.author)
            spec = contributor_analyzer.calculate_specialization(args.author)

            if pattern:
                print(f"\n📊 Паттерны работы: {args.author}")
                print(f"   Тип контрибьютора: {pattern['contributor_type']}")
                print(f"   Самый активный час: {pattern['most_active_hour']}:00")
                print(f"   Средний размер коммита: {pattern['avg_commit_size']} строк")
                print(f"   Частота коммитов: {pattern['commit_frequency']:.2f} коммитов/день")
                print(f"   Уникальных дней активности: {pattern['unique_days']}")

                if spec:
                    print(f"\n🎯 Специализация:")
                    for category, percentage in spec.items():
                        print(f"   {category}: {percentage}%")
            else:
                print(f"❌ Контрибьютор '{args.author}' не найден")
        else:
            # Общий анализ
            print("\n🔍 Топ контрибьюторов с паттернами:")
            top_contributors = sorted(
                analyzer.contributors.items(),
                key=lambda x: -x[1]['commits']
            )[:5]

            for author, stats in top_contributors:
                pattern = contributor_analyzer.analyze_contributor_patterns(author)
                if pattern:
                    print(f"\n   {author}:")
                    print(f"   - Коммитов: {stats['commits']}")
                    print(f"   - Тип: {pattern['contributor_type']}")
                    print(f"   - Активен в: {pattern['most_active_hour']}:00")

            # Коллаборация
            collaborations = contributor_analyzer.find_collaboration_pairs()
            if collaborations:
                print(f"\n🤝 Топ пар коллабораторов:")
                for collab in collaborations[:5]:
                    print(f"   {collab['authors'][0]} ↔ {collab['authors'][1]}: {collab['common_files']} общих файлов")

    # Bus Factor
    if args.bus_factor:
        print("\n🚌 Bus Factor Analysis...")
        contributor_analyzer = ContributorAnalyzer(
            dict(analyzer.contributors),
            analyzer.changes
        )
        bus_factor = contributor_analyzer.calculate_bus_factor()

        print(f"   Bus Factor: {bus_factor['bus_factor']}")
        print(f"   Risk Level: {bus_factor['risk_level'].upper()}")
        print(f"   Топ {bus_factor['bus_factor']} контрибьюторов делают {bus_factor['top_contributors_percentage']}% коммитов")

        if bus_factor['risk_level'] == 'critical':
            print("   ⚠️  КРИТИЧЕСКИЙ РИСК: Проект зависит от слишком малого числа людей!")
        elif bus_factor['risk_level'] == 'medium':
            print("   ⚡ Умеренный риск: Рекомендуется расширить команду")
        else:
            print("   ✅ Здоровое распределение работы")

    # Impact Analysis
    if args.impact:
        print("\n💥 Impact Analysis...")
        impact_analyzer = ChangeImpactAnalyzer(
            analyzer.changes,
            dict(analyzer.file_activity)
        )

        # Risky commits
        risky_commits = []
        for commit in analyzer.changes:
            risk = impact_analyzer.calculate_risk_score(commit)
            if risk['risk_level'] in ['high', 'critical']:
                risky_commits.append((commit, risk))

        if risky_commits:
            print(f"\n⚠️  Найдено {len(risky_commits)} коммитов с высоким риском:")
            for commit, risk in sorted(risky_commits, key=lambda x: -x[1]['risk_score'])[:5]:
                print(f"\n   [{commit['hash'][:7]}] {commit['message'][:60]}")
                print(f"   Risk Score: {risk['risk_score']}/100 ({risk['risk_level'].upper()})")
                print(f"   Факторы: {', '.join(risk['risk_factors'][:3])}")

        # Hotspots
        if args.hotspots:
            hotspots = impact_analyzer.identify_hotspots(args.hotspots)
            print(f"\n🔥 Топ {len(hotspots)} hotspots:")
            for spot in hotspots:
                print(f"   {spot['file']}")
                print(f"      Изменений: {spot['changes']}, Churn: {spot['total_churn']:,} строк (avg: {spot['avg_churn']:.1f})")

    # Hotspots (отдельно)
    if args.hotspots and not args.impact:
        print(f"\n🔥 Hotspot Analysis (топ {args.hotspots})...")
        impact_analyzer = ChangeImpactAnalyzer(
            analyzer.changes,
            dict(analyzer.file_activity)
        )
        hotspots = impact_analyzer.identify_hotspots(args.hotspots)

        for i, spot in enumerate(hotspots, 1):
            print(f"{i}. {spot['file']}")
            print(f"   Изменений: {spot['changes']}, Total churn: {spot['total_churn']:,}, Avg: {spot['avg_churn']:.1f}")

    # Velocity Analysis
    if args.velocity:
        print("\n📈 Velocity Analysis...")
        impact_analyzer = ChangeImpactAnalyzer(
            analyzer.changes,
            dict(analyzer.file_activity)
        )
        velocity_trend = impact_analyzer.analyze_change_velocity()

        if velocity_trend['trend'] != 'insufficient_data':
            print(f"   Тренд: {velocity_trend['trend'].upper()}")
            print(f"   Первая половина периода: {velocity_trend['first_half_avg']:.2f} коммитов/день")
            print(f"   Вторая половина периода: {velocity_trend['second_half_avg']:.2f} коммитов/день")
            print(f"   Изменение: {velocity_trend['change_percentage']:+.1f}%")

            if velocity_trend['trend'] == 'accelerating':
                print("   📈 Скорость разработки растёт!")
            elif velocity_trend['trend'] == 'decelerating':
                print("   📉 Скорость разработки снижается")
            else:
                print("   ➡️  Стабильная скорость разработки")
        else:
            print("   ⚠️  Недостаточно данных для анализа тренда")

    # Pattern Analysis
    if args.patterns:
        print("\n📋 Commit Pattern Analysis...")
        pattern_analyzer = CommitPatternAnalyzer(analyzer.changes)

        # Типы коммитов
        commit_types = pattern_analyzer.analyze_commit_types()
        print("\n📊 Распределение по типам коммитов:")
        for commit_type, count in list(commit_types.items())[:8]:
            percentage = (count / len(analyzer.changes)) * 100
            print(f"   {commit_type}: {count} ({percentage:.1f}%)")

        # Размеры коммитов
        commit_sizes = pattern_analyzer.analyze_commit_sizes()
        print("\n📏 Размеры коммитов:")
        for size_cat, count in commit_sizes.items():
            percentage = (count / len(analyzer.changes)) * 100
            print(f"   {size_cat}: {count} ({percentage:.1f}%)")

        # Частые слова
        top_words = pattern_analyzer.find_message_patterns()
        print("\n🔤 Топ слов в сообщениях коммитов:")
        for word, freq in top_words[:10]:
            print(f"   {word}: {freq}")

        # Quality scoring (sample)
        quality_scores = [
            pattern_analyzer.calculate_message_quality_score(c['message'])
            for c in analyzer.changes
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        print(f"\n✨ Средний quality score сообщений: {avg_quality:.1f}/100")

    # Export JSON
    if args.json:
        analyzer.export_json()

    # Export RSS
    if args.rss:
        analyzer.generate_rss_feed()

    # Export CSV
    if args.csv:
        print("\n📊 Экспорт в CSV...")
        csv_file = root_dir / "recent_changes.csv"

        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Author,Commits,Files Changed,Insertions,Deletions,Total Changes\n")
            for author, stats in sorted(analyzer.contributors.items(), key=lambda x: -x[1]['commits']):
                f.write(f"{author},{stats['commits']},{stats['files_changed']},{stats['insertions']},{stats['deletions']},{stats['insertions'] + stats['deletions']}\n")

        print(f"✅ CSV: {csv_file}")

    print("\n✅ Анализ завершён!")


if __name__ == "__main__":
    main()
