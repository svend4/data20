#!/usr/bin/env python3
"""
Advanced Reading Progress Tracker - Продвинутый трекер прогресса чтения
Функции:
- Reading time estimation (на основе слов)
- Reading speed tracking (слов/мин)
- Session tracking (время чтения)
- Achievements/badges
- Reading streak (дни подряд)
- Category/tag progress
- Reading history timeline
- Recommendations based on reading
- Detailed statistics
- CSV/JSON export
- Progress visualization

Вдохновлено: Kindle, Pocket, Goodreads, Duolingo streaks
"""

from pathlib import Path
import json
from datetime import datetime, timedelta
import yaml
import re
from collections import defaultdict, Counter
import calendar


class ProgressTracker:
    """
    Enhanced progress tracking
    - Progress by categories
    - Completion percentage
    - Estimated time to completion
    - Reading velocity (articles/day, week)
    - Personal reading goals
    """

    def __init__(self, tracker):
        self.tracker = tracker
        self.progress = tracker.progress

    def calculate_category_progress(self):
        """Вычислить прогресс по категориям"""
        all_articles = list(self.tracker.knowledge_dir.rglob("*.md"))
        all_articles = [str(f.relative_to(self.tracker.root_dir)) for f in all_articles if f.name != "INDEX.md"]

        category_progress = defaultdict(lambda: {'total': 0, 'read': 0, 'in_progress': 0, 'unread': 0})

        for article_path in all_articles:
            metadata = self.tracker.get_article_metadata(article_path)
            if not metadata:
                continue

            category = metadata.get('category', 'Uncategorized')
            category_progress[category]['total'] += 1

            if article_path in self.progress['articles']:
                status = self.progress['articles'][article_path]['status']
                if status == 'read':
                    category_progress[category]['read'] += 1
                elif status == 'in_progress':
                    category_progress[category]['in_progress'] += 1
            else:
                category_progress[category]['unread'] += 1

        # Вычислить проценты
        for category, stats in category_progress.items():
            total = stats['total']
            if total > 0:
                stats['completion_pct'] = (stats['read'] / total) * 100
            else:
                stats['completion_pct'] = 0

        return dict(category_progress)

    def calculate_reading_velocity(self):
        """Вычислить скорость чтения (статей в день/неделю)"""
        read_articles = [
            (path, data) for path, data in self.progress['articles'].items()
            if data['status'] == 'read' and 'completed_at' in data
        ]

        if not read_articles:
            return {
                'articles_per_day': 0,
                'articles_per_week': 0,
                'estimated_days_to_completion': None
            }

        # Сортировать по дате
        read_articles.sort(key=lambda x: x[1]['completed_at'])

        # Первая и последняя дата
        first_date = datetime.fromisoformat(read_articles[0][1]['completed_at'])
        last_date = datetime.fromisoformat(read_articles[-1][1]['completed_at'])

        days_span = (last_date - first_date).days + 1

        if days_span < 1:
            days_span = 1

        articles_per_day = len(read_articles) / days_span
        articles_per_week = articles_per_day * 7

        # Estimated time to completion
        all_articles = list(self.tracker.knowledge_dir.rglob("*.md"))
        total_articles = len([f for f in all_articles if f.name != "INDEX.md"])
        unread_count = total_articles - len(read_articles)

        if articles_per_day > 0:
            estimated_days = unread_count / articles_per_day
        else:
            estimated_days = None

        return {
            'articles_per_day': round(articles_per_day, 2),
            'articles_per_week': round(articles_per_week, 2),
            'estimated_days_to_completion': int(estimated_days) if estimated_days else None
        }

    def get_reading_goals(self):
        """Получить личные цели чтения"""
        goals = self.progress.get('goals', {})

        # Default goals
        default_goals = {
            'daily_articles': 1,
            'weekly_articles': 7,
            'monthly_articles': 30,
            'total_articles_target': 100
        }

        return {**default_goals, **goals}

    def calculate_goal_progress(self):
        """Вычислить прогресс к целям"""
        goals = self.get_reading_goals()

        # Сегодня, эта неделя, этот месяц
        now = datetime.now()
        today = now.date()

        # Статьи, прочитанные сегодня
        today_articles = [
            path for path, data in self.progress['articles'].items()
            if data['status'] == 'read' and 'completed_at' in data
            and datetime.fromisoformat(data['completed_at']).date() == today
        ]

        # Статьи за эту неделю
        week_start = today - timedelta(days=today.weekday())
        week_articles = [
            path for path, data in self.progress['articles'].items()
            if data['status'] == 'read' and 'completed_at' in data
            and datetime.fromisoformat(data['completed_at']).date() >= week_start
        ]

        # Статьи за этот месяц
        month_start = today.replace(day=1)
        month_articles = [
            path for path, data in self.progress['articles'].items()
            if data['status'] == 'read' and 'completed_at' in data
            and datetime.fromisoformat(data['completed_at']).date() >= month_start
        ]

        # Total read
        total_read = sum(1 for d in self.progress['articles'].values() if d['status'] == 'read')

        return {
            'daily': {
                'current': len(today_articles),
                'goal': goals['daily_articles'],
                'achieved': len(today_articles) >= goals['daily_articles']
            },
            'weekly': {
                'current': len(week_articles),
                'goal': goals['weekly_articles'],
                'achieved': len(week_articles) >= goals['weekly_articles']
            },
            'monthly': {
                'current': len(month_articles),
                'goal': goals['monthly_articles'],
                'achieved': len(month_articles) >= goals['monthly_articles']
            },
            'total': {
                'current': total_read,
                'goal': goals['total_articles_target'],
                'achieved': total_read >= goals['total_articles_target']
            }
        }


class AchievementSystem:
    """
    Advanced achievement system
    - Badges/achievements
    - Milestones (25/50/100/500)
    - Challenges (read 10 in category X)
    """

    def __init__(self, tracker):
        self.tracker = tracker
        self.progress = tracker.progress

    def get_all_achievements(self):
        """Получить все возможные достижения"""
        read_count = sum(1 for d in self.progress['articles'].values() if d['status'] == 'read')
        current_streak = self.progress['statistics'].get('current_streak', 0)

        # Подсчитать статьи по категориям
        category_counts = defaultdict(int)
        for article, data in self.progress['articles'].items():
            if data['status'] == 'read':
                category = data.get('category', 'Uncategorized')
                category_counts[category] += 1

        achievements = []

        # Reading count milestones
        milestones = [
            (1, '📖', 'Первая статья', 'Прочитана первая статья'),
            (5, '📚', '5 статей', 'Прочитано 5 статей'),
            (10, '🎯', '10 статей', 'Прочитано 10 статей'),
            (25, '🏅', '25 статей', 'Прочитано 25 статей'),
            (50, '🏆', '50 статей', 'Прочитано 50 статей'),
            (100, '💯', '100 статей', 'Прочитано 100 статей'),
            (200, '🌟', '200 статей', 'Прочитано 200 статей'),
            (500, '👑', '500 статей', 'Прочитано 500 статей'),
        ]

        for count, icon, name, desc in milestones:
            achievements.append({
                'id': f'read_{count}',
                'icon': icon,
                'name': name,
                'description': desc,
                'unlocked': read_count >= count,
                'progress': min(read_count, count),
                'required': count
            })

        # Streak achievements
        streaks = [
            (3, '🔥', '3 дня подряд', 'Читал 3 дня подряд'),
            (7, '🔥', 'Недельный streak', 'Читал 7 дней подряд'),
            (14, '🔥', '2 недели', 'Читал 14 дней подряд'),
            (30, '🔥', 'Месячный streak', 'Читал 30 дней подряд'),
            (100, '🔥', '100 дней', 'Читал 100 дней подряд'),
        ]

        for count, icon, name, desc in streaks:
            achievements.append({
                'id': f'streak_{count}',
                'icon': icon,
                'name': name,
                'description': desc,
                'unlocked': current_streak >= count,
                'progress': min(current_streak, count),
                'required': count
            })

        # Category mastery (10+ articles in one category)
        for category, count in category_counts.items():
            if count >= 10:
                achievements.append({
                    'id': f'category_{category}',
                    'icon': '🎓',
                    'name': f'Мастер {category}',
                    'description': f'Прочитано 10+ статей по {category}',
                    'unlocked': True,
                    'progress': count,
                    'required': 10
                })

        return achievements

    def get_unlocked_achievements(self):
        """Получить разблокированные достижения"""
        all_achievements = self.get_all_achievements()
        return [a for a in all_achievements if a['unlocked']]

    def get_next_achievements(self, max_count=5):
        """Получить следующие достижения к разблокировке"""
        all_achievements = self.get_all_achievements()
        locked = [a for a in all_achievements if not a['unlocked']]

        # Сортировать по прогрессу
        locked.sort(key=lambda x: x['progress'] / x['required'], reverse=True)

        return locked[:max_count]


class ReadingRecommendations:
    """
    Reading recommendations engine
    - Suggest next article based on reading history
    - "Continue where you left off"
    - Related articles to what you read
    - Fill gaps (topics not covered yet)
    """

    def __init__(self, tracker):
        self.tracker = tracker
        self.progress = tracker.progress

    def suggest_continue(self):
        """Предложить продолжить начатые статьи"""
        in_progress = [
            (path, data) for path, data in self.progress['articles'].items()
            if data['status'] == 'in_progress'
        ]

        # Сортировать по дате начала
        in_progress.sort(key=lambda x: x[1].get('started_at', ''), reverse=True)

        suggestions = []
        for path, data in in_progress[:5]:
            suggestions.append({
                'path': path,
                'reason': 'В процессе чтения',
                'started_at': data.get('started_at'),
                'estimated_time_min': data.get('estimated_time_min', 0),
                'score': 100
            })

        return suggestions

    def suggest_related_to_recent(self, max_suggestions=5):
        """Предложить статьи, связанные с недавно прочитанными"""
        # Получить последние прочитанные статьи
        read_articles = [
            (path, data) for path, data in self.progress['articles'].items()
            if data['status'] == 'read' and 'completed_at' in data
        ]

        if not read_articles:
            return []

        # Сортировать по дате
        read_articles.sort(key=lambda x: x[1]['completed_at'], reverse=True)
        recent = read_articles[:5]

        # Собрать теги и категории из недавно прочитанных
        recent_tags = set()
        recent_categories = set()

        for path, data in recent:
            recent_tags.update(data.get('tags', []))
            cat = data.get('category')
            if cat:
                recent_categories.add(cat)

        # Найти непрочитанные статьи с похожими тегами/категориями
        all_articles = list(self.tracker.knowledge_dir.rglob("*.md"))
        all_articles = [str(f.relative_to(self.tracker.root_dir)) for f in all_articles if f.name != "INDEX.md"]

        suggestions = []

        for article_path in all_articles:
            # Пропустить уже прочитанные
            if article_path in self.progress['articles']:
                status = self.progress['articles'][article_path]['status']
                if status == 'read':
                    continue

            metadata = self.tracker.get_article_metadata(article_path)
            if not metadata:
                continue

            score = 0
            reasons = []

            # Общие теги
            article_tags = set(metadata.get('tags', []))
            common_tags = recent_tags & article_tags

            if common_tags:
                score += len(common_tags) * 10
                reasons.append(f"Общие теги: {', '.join(list(common_tags)[:3])}")

            # Та же категория
            article_category = metadata.get('category')
            if article_category in recent_categories:
                score += 20
                reasons.append(f"Категория: {article_category}")

            if score > 0:
                suggestions.append({
                    'path': article_path,
                    'reason': '; '.join(reasons),
                    'estimated_time_min': metadata.get('estimated_time_min', 0),
                    'score': score
                })

        # Сортировать по score
        suggestions.sort(key=lambda x: -x['score'])

        return suggestions[:max_suggestions]

    def suggest_fill_gaps(self, max_suggestions=5):
        """Предложить статьи из категорий/тегов, которые мало изучены"""
        # Подсчитать, сколько прочитано в каждой категории
        all_articles = list(self.tracker.knowledge_dir.rglob("*.md"))
        all_articles = [str(f.relative_to(self.tracker.root_dir)) for f in all_articles if f.name != "INDEX.md"]

        category_stats = defaultdict(lambda: {'total': 0, 'read': 0})

        for article_path in all_articles:
            metadata = self.tracker.get_article_metadata(article_path)
            if not metadata:
                continue

            category = metadata.get('category', 'Uncategorized')
            category_stats[category]['total'] += 1

            if article_path in self.progress['articles']:
                if self.progress['articles'][article_path]['status'] == 'read':
                    category_stats[category]['read'] += 1

        # Найти категории с низким прогрессом
        gaps = []
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                completion = stats['read'] / stats['total']
                if completion < 0.5:  # < 50%
                    gaps.append({
                        'category': category,
                        'completion': completion,
                        'read': stats['read'],
                        'total': stats['total']
                    })

        # Сортировать по completion (меньше = больший gap)
        gaps.sort(key=lambda x: x['completion'])

        # Предложить статьи из gap-категорий
        suggestions = []

        for gap in gaps[:3]:  # Топ-3 gap-категории
            category = gap['category']

            # Найти непрочитанные статьи в этой категории
            for article_path in all_articles:
                if article_path in self.progress['articles']:
                    if self.progress['articles'][article_path]['status'] == 'read':
                        continue

                metadata = self.tracker.get_article_metadata(article_path)
                if not metadata:
                    continue

                if metadata.get('category') == category:
                    suggestions.append({
                        'path': article_path,
                        'reason': f"Заполнить gap в категории {category} ({gap['read']}/{gap['total']})",
                        'estimated_time_min': metadata.get('estimated_time_min', 0),
                        'score': 50 - int(gap['completion'] * 50)
                    })

                    if len(suggestions) >= max_suggestions:
                        break

            if len(suggestions) >= max_suggestions:
                break

        return suggestions[:max_suggestions]


class VisualizationGenerator:
    """
    HTML visualization generator
    - HTML dashboard with progress
    - Heatmap calendar (GitHub-style)
    - Progress bars by category
    - Reading streak visualization
    - Graphs: articles per day/week/month
    """

    def __init__(self, tracker):
        self.tracker = tracker
        self.progress = tracker.progress

    def generate_heatmap_data(self):
        """Сгенерировать данные для heatmap календаря"""
        # Получить все даты чтения
        read_by_date = defaultdict(int)

        for article, data in self.progress['articles'].items():
            if data['status'] == 'read' and 'completed_at' in data:
                date = datetime.fromisoformat(data['completed_at']).date()
                read_by_date[str(date)] += 1

        return dict(read_by_date)

    def generate_html_dashboard(self):
        """Сгенерировать HTML dashboard"""
        stats = self.tracker.calculate_statistics()
        heatmap_data = self.generate_heatmap_data()

        # Category progress для графиков
        category_progress = defaultdict(lambda: {'read': 0, 'total': 0})
        all_articles = list(self.tracker.knowledge_dir.rglob("*.md"))
        all_articles_paths = [str(f.relative_to(self.tracker.root_dir)) for f in all_articles if f.name != "INDEX.md"]

        for article_path in all_articles_paths:
            metadata = self.tracker.get_article_metadata(article_path)
            if metadata:
                category = metadata.get('category', 'Uncategorized')
                category_progress[category]['total'] += 1

                if article_path in self.progress['articles']:
                    if self.progress['articles'][article_path]['status'] == 'read':
                        category_progress[category]['read'] += 1

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reading Progress Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        h1 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}

        .subtitle {{
            color: #718096;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 8px;
        }}

        .stat-label {{
            font-size: 0.95em;
            opacity: 0.95;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        .progress-bar-container {{
            margin-bottom: 15px;
        }}

        .progress-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            color: #4a5568;
            font-weight: 500;
        }}

        .progress-bar {{
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}

        .heatmap {{
            display: inline-block;
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
        }}

        .heatmap-row {{
            display: flex;
            gap: 3px;
            margin-bottom: 3px;
        }}

        .heatmap-cell {{
            width: 12px;
            height: 12px;
            background: #ebedf0;
            border-radius: 2px;
        }}

        .heatmap-cell[data-count="1"] {{ background: #c6e48b; }}
        .heatmap-cell[data-count="2"] {{ background: #7bc96f; }}
        .heatmap-cell[data-count="3"] {{ background: #239a3b; }}
        .heatmap-cell[data-count="4"] {{ background: #196127; }}

        .achievements {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
        }}

        .achievement {{
            background: #f7fafc;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e2e8f0;
        }}

        .achievement.unlocked {{
            border-color: #667eea;
            background: linear-gradient(135deg, #f0f4ff 0%, #f5f0ff 100%);
        }}

        .achievement-icon {{
            font-size: 2em;
            margin-bottom: 8px;
        }}

        .achievement-name {{
            font-weight: bold;
            color: #2d3748;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}

            h1 {{
                font-size: 1.8em;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Reading Progress Dashboard</h1>
        <p class="subtitle">Ваш прогресс в чтении базы знаний</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['read']}</div>
                <div class="stat-label">Прочитано</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['in_progress']}</div>
                <div class="stat-label">В процессе</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_time_hours']}h</div>
                <div class="stat-label">Всего времени</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['current_streak']}</div>
                <div class="stat-label">🔥 Streak (дней)</div>
            </div>
        </div>

        <div class="section">
            <h2>Прогресс по категориям</h2>"""

        for category, cat_stats in sorted(category_progress.items(), key=lambda x: -x[1]['read']):
            read_cat = cat_stats['read']
            total_cat = cat_stats['total']
            pct = (read_cat / total_cat * 100) if total_cat > 0 else 0

            html += f"""
            <div class="progress-bar-container">
                <div class="progress-label">
                    <span>{category}</span>
                    <span>{read_cat}/{total_cat}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {pct}%">
                        {pct:.0f}%
                    </div>
                </div>
            </div>"""

        # Achievements
        achievement_system = AchievementSystem(self.tracker)
        unlocked = achievement_system.get_unlocked_achievements()

        html += f"""
        </div>

        <div class="section">
            <h2>🏆 Достижения ({len(unlocked)} разблокировано)</h2>
            <div class="achievements">"""

        for ach in unlocked[:12]:
            html += f"""
                <div class="achievement unlocked">
                    <div class="achievement-icon">{ach['icon']}</div>
                    <div class="achievement-name">{ach['name']}</div>
                </div>"""

        html += """
            </div>
        </div>
    </div>
</body>
</html>"""

        return html

    def save_html(self, output_file):
        """Сохранить HTML dashboard"""
        html = self.generate_html_dashboard()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML dashboard: {output_file}")


class AdvancedReadingProgressTracker:
    """Продвинутый трекер прогресса чтения"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.progress_file = self.root_dir / ".reading_progress.json"

        # Средняя скорость чтения (слов/мин)
        self.avg_reading_speed = 200  # words per minute

        # Загрузить существующий прогресс
        self.progress = self.load_progress()

    def load_progress(self):
        """Загрузить прогресс из файла"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            'articles': {},  # path -> article data
            'sessions': [],  # reading sessions
            'statistics': {
                'total_read': 0,
                'total_in_progress': 0,
                'total_unread': 0,
                'total_reading_time_min': 0,
                'current_streak': 0,
                'longest_streak': 0
            },
            'achievements': [],
            'settings': {
                'reading_speed_wpm': 200
            }
        }

    def save_progress(self):
        """Сохранить прогресс в файл"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

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

    def count_words(self, content):
        """Подсчитать количество слов"""
        if not content:
            return 0

        # Удалить markdown форматирование
        text = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # Изображения
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Ссылки
        text = re.sub(r'[#*`_]', '', text)  # Форматирование
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Код-блоки

        # Подсчитать слова
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    def estimate_reading_time(self, word_count):
        """Оценить время чтения (в минутах)"""
        speed = self.progress['settings'].get('reading_speed_wpm', self.avg_reading_speed)
        return max(1, word_count / speed)

    def get_article_metadata(self, article_path):
        """Получить метаданные статьи"""
        file_path = self.root_dir / article_path

        if not file_path.exists():
            return None

        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        word_count = self.count_words(content)
        estimated_time = self.estimate_reading_time(word_count)

        metadata = {
            'path': article_path,
            'word_count': word_count,
            'estimated_time_min': round(estimated_time, 1),
            'tags': [],
            'category': None
        }

        if frontmatter:
            metadata['tags'] = frontmatter.get('tags', [])
            metadata['category'] = frontmatter.get('category', None)

        return metadata

    def mark_as_read(self, article_path, reading_time_min=None):
        """Пометить статью как прочитанную"""
        now = datetime.now()

        # Получить метаданные
        metadata = self.get_article_metadata(article_path)

        if not metadata:
            print(f"❌ Статья не найдена: {article_path}")
            return

        # Записать данные о чтении
        article_data = {
            'status': 'read',
            'completed_at': now.isoformat(),
            'word_count': metadata['word_count'],
            'estimated_time_min': metadata['estimated_time_min'],
            'actual_time_min': reading_time_min if reading_time_min else metadata['estimated_time_min'],
            'tags': metadata['tags'],
            'category': metadata['category']
        }

        # Если была in_progress, взять started_at
        if article_path in self.progress['articles']:
            old_data = self.progress['articles'][article_path]
            if 'started_at' in old_data:
                article_data['started_at'] = old_data['started_at']

        self.progress['articles'][article_path] = article_data

        # Добавить сессию
        session = {
            'article': article_path,
            'timestamp': now.isoformat(),
            'type': 'completed',
            'reading_time_min': article_data['actual_time_min']
        }
        self.progress['sessions'].append(session)

        # Обновить streak
        self.update_streak(now)

        # Проверить achievements
        self.check_achievements()

        self.save_progress()
        print(f"✅ Отмечено как прочитанное: {article_path}")
        print(f"   Слов: {metadata['word_count']}, Время: ~{metadata['estimated_time_min']} мин")

    def mark_in_progress(self, article_path):
        """Пометить статью как в процессе"""
        now = datetime.now()

        metadata = self.get_article_metadata(article_path)

        if not metadata:
            print(f"❌ Статья не найдена: {article_path}")
            return

        self.progress['articles'][article_path] = {
            'status': 'in_progress',
            'started_at': now.isoformat(),
            'word_count': metadata['word_count'],
            'estimated_time_min': metadata['estimated_time_min'],
            'tags': metadata['tags'],
            'category': metadata['category']
        }

        self.save_progress()
        print(f"📖 В процессе: {article_path}")
        print(f"   Слов: {metadata['word_count']}, Время: ~{metadata['estimated_time_min']} мин")

    def update_streak(self, now):
        """Обновить reading streak"""
        # Получить даты чтения
        read_dates = []

        for article, data in self.progress['articles'].items():
            if data['status'] == 'read' and 'completed_at' in data:
                read_date = datetime.fromisoformat(data['completed_at']).date()
                read_dates.append(read_date)

        if not read_dates:
            self.progress['statistics']['current_streak'] = 0
            return

        # Сортировать даты
        read_dates = sorted(set(read_dates), reverse=True)

        # Подсчитать текущий streak
        current_streak = 0
        today = now.date()

        for i, date in enumerate(read_dates):
            expected_date = today - timedelta(days=i)

            if date == expected_date:
                current_streak += 1
            else:
                break

        # Обновить
        self.progress['statistics']['current_streak'] = current_streak

        # Longest streak
        if current_streak > self.progress['statistics'].get('longest_streak', 0):
            self.progress['statistics']['longest_streak'] = current_streak

    def check_achievements(self):
        """Проверить и разблокировать достижения"""
        achievements_unlocked = []

        read_count = sum(1 for d in self.progress['articles'].values() if d['status'] == 'read')
        current_streak = self.progress['statistics'].get('current_streak', 0)

        # Определения достижений
        achievements_definitions = [
            {'id': 'first_article', 'name': '📖 Первая статья', 'condition': read_count >= 1},
            {'id': 'read_10', 'name': '🎯 10 статей', 'condition': read_count >= 10},
            {'id': 'read_50', 'name': '🏆 50 статей', 'condition': read_count >= 50},
            {'id': 'read_100', 'name': '💯 100 статей', 'condition': read_count >= 100},
            {'id': 'streak_3', 'name': '🔥 3 дня подряд', 'condition': current_streak >= 3},
            {'id': 'streak_7', 'name': '🔥 Недельный streak', 'condition': current_streak >= 7},
            {'id': 'streak_30', 'name': '🔥 Месячный streak', 'condition': current_streak >= 30},
        ]

        existing_achievements = set(a['id'] for a in self.progress.get('achievements', []))

        for ach in achievements_definitions:
            if ach['condition'] and ach['id'] not in existing_achievements:
                achievement = {
                    'id': ach['id'],
                    'name': ach['name'],
                    'unlocked_at': datetime.now().isoformat()
                }
                self.progress['achievements'].append(achievement)
                achievements_unlocked.append(ach['name'])

        if achievements_unlocked:
            print(f"\n🎉 Разблокировано достижений: {len(achievements_unlocked)}")
            for ach in achievements_unlocked:
                print(f"   {ach}")

    def calculate_statistics(self):
        """Вычислить подробную статистику"""
        all_articles = list(self.knowledge_dir.rglob("*.md"))
        all_articles = [str(f.relative_to(self.root_dir)) for f in all_articles if f.name != "INDEX.md"]

        read = [a for a, d in self.progress['articles'].items() if d['status'] == 'read']
        in_progress = [a for a, d in self.progress['articles'].items() if d['status'] == 'in_progress']
        unread = [a for a in all_articles if a not in self.progress['articles']]

        # Время чтения
        total_time = sum(d.get('actual_time_min', 0) for d in self.progress['articles'].values() if d['status'] == 'read')

        # По категориям
        category_stats = defaultdict(lambda: {'read': 0, 'total': 0})

        for article_path in all_articles:
            metadata = self.get_article_metadata(article_path)
            if metadata:
                category = metadata.get('category', 'Uncategorized')
                category_stats[category]['total'] += 1

                if article_path in self.progress['articles'] and self.progress['articles'][article_path]['status'] == 'read':
                    category_stats[category]['read'] += 1

        # По тегам
        tag_stats = Counter()

        for article, data in self.progress['articles'].items():
            if data['status'] == 'read':
                for tag in data.get('tags', []):
                    tag_stats[tag] += 1

        return {
            'total': len(all_articles),
            'read': len(read),
            'in_progress': len(in_progress),
            'unread': len(unread),
            'total_time_min': round(total_time, 1),
            'total_time_hours': round(total_time / 60, 1),
            'category_stats': dict(category_stats),
            'tag_stats': dict(tag_stats),
            'current_streak': self.progress['statistics'].get('current_streak', 0),
            'longest_streak': self.progress['statistics'].get('longest_streak', 0)
        }

    def generate_report(self):
        """Создать подробный отчёт о прогрессе"""
        stats = self.calculate_statistics()

        lines = []
        lines.append("# 📚 Прогресс чтения\n\n")

        # Основная статистика
        lines.append("## Статистика\n\n")
        lines.append(f"**Всего статей**: {stats['total']}\n\n")
        lines.append(f"- ✅ **Прочитано**: {stats['read']}\n")
        lines.append(f"- 📖 **В процессе**: {stats['in_progress']}\n")
        lines.append(f"- ⬜ **Не прочитано**: {stats['unread']}\n\n")

        if stats['total'] > 0:
            progress_pct = (stats['read'] / stats['total']) * 100
            lines.append(f"**Прогресс**: {progress_pct:.1f}%\n\n")

            # Progress bar
            bar_length = 20
            filled = int(bar_length * stats['read'] / stats['total'])
            bar = '█' * filled + '░' * (bar_length - filled)
            lines.append(f"`{bar}` {progress_pct:.1f}%\n\n")

        # Время чтения
        lines.append("## ⏱️ Время чтения\n\n")
        lines.append(f"- **Всего времени**: {stats['total_time_hours']} часов ({stats['total_time_min']} мин)\n")
        if stats['read'] > 0:
            avg_time = stats['total_time_min'] / stats['read']
            lines.append(f"- **Среднее время на статью**: {avg_time:.1f} мин\n")
        lines.append("\n")

        # Streaks
        lines.append("## 🔥 Reading Streak\n\n")
        lines.append(f"- **Текущий streak**: {stats['current_streak']} дней\n")
        lines.append(f"- **Лучший streak**: {stats['longest_streak']} дней\n\n")

        # Достижения
        if self.progress.get('achievements'):
            lines.append("## 🏆 Достижения\n\n")
            for ach in self.progress['achievements']:
                lines.append(f"- {ach['name']}\n")
            lines.append("\n")

        # По категориям
        if stats['category_stats']:
            lines.append("## 📁 По категориям\n\n")

            for category, cat_stats in sorted(stats['category_stats'].items(), key=lambda x: -x[1]['read']):
                read_cat = cat_stats['read']
                total_cat = cat_stats['total']
                pct = (read_cat / total_cat * 100) if total_cat > 0 else 0

                lines.append(f"- **{category}**: {read_cat}/{total_cat} ({pct:.0f}%)\n")

            lines.append("\n")

        # По тегам (топ-10)
        if stats['tag_stats']:
            lines.append("## 🏷️ Топ-10 тегов\n\n")

            for tag, count in Counter(stats['tag_stats']).most_common(10):
                lines.append(f"- {tag}: {count}\n")

            lines.append("\n")

        output_file = self.root_dir / "READING_PROGRESS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

        # Показать статистику
        print(f"\n📊 Статистика:")
        print(f"   Прочитано: {stats['read']}/{stats['total']} ({progress_pct:.1f}%)")
        print(f"   Время: {stats['total_time_hours']} часов")
        print(f"   Streak: {stats['current_streak']} дней")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='📚 Reading Progress Tracker - Продвинутый трекер прогресса чтения',
        epilog='''Примеры:
  reading_progress.py --mark-read knowledge/ai/transformers.md      # Отметить как прочитанное
  reading_progress.py --stats                                       # Показать детальную статистику
  reading_progress.py --badges                                      # Показать достижения
  reading_progress.py --recommendations                             # Что читать дальше
  reading_progress.py --html progress.html                          # HTML dashboard
  reading_progress.py --all                                         # Всё вместе
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--mark-read', metavar='FILE',
                       help='Пометить статью как прочитанную')
    parser.add_argument('--mark-progress', metavar='FILE',
                       help='Пометить статью как в процессе')
    parser.add_argument('--time', type=float, metavar='MIN',
                       help='Фактическое время чтения (минут)')
    parser.add_argument('--report', action='store_true',
                       help='Создать markdown отчёт')
    parser.add_argument('--stats', action='store_true',
                       help='Показать детальную статистику')
    parser.add_argument('--badges', action='store_true',
                       help='Показать достижения и badges')
    parser.add_argument('--recommendations', action='store_true',
                       help='Рекомендации: что читать дальше')
    parser.add_argument('--html', metavar='FILE',
                       help='Генерировать HTML dashboard')
    parser.add_argument('--all', action='store_true',
                       help='Все анализы + все форматы экспорта')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tracker = AdvancedReadingProgressTracker(root_dir)

    # Отметить как прочитанное
    if args.mark_read:
        tracker.mark_as_read(args.mark_read, reading_time_min=args.time)

    # Отметить как в процессе
    if args.mark_progress:
        tracker.mark_in_progress(args.mark_progress)

    # Markdown отчёт
    if args.report or (not args.mark_read and not args.mark_progress and not any([args.stats, args.badges, args.recommendations, args.html, args.all])):
        tracker.generate_report()

    # Детальная статистика
    if args.stats or args.all:
        print("\n📊 Детальная статистика:\n")

        progress_tracker = ProgressTracker(tracker)

        # Velocity
        velocity = progress_tracker.calculate_reading_velocity()
        print(f"📈 Скорость чтения:")
        print(f"   {velocity['articles_per_day']} статей/день")
        print(f"   {velocity['articles_per_week']} статей/неделю")

        if velocity['estimated_days_to_completion']:
            print(f"   Estimated completion: {velocity['estimated_days_to_completion']} дней")

        # Progress by category
        print(f"\n📁 Прогресс по категориям:")
        category_progress = progress_tracker.calculate_category_progress()

        for category, stats in sorted(category_progress.items(), key=lambda x: -x[1]['completion_pct'])[:10]:
            pct = stats['completion_pct']
            read = stats['read']
            total = stats['total']
            print(f"   {category}: {read}/{total} ({pct:.0f}%)")

        # Goals
        print(f"\n🎯 Прогресс к целям:")
        goal_progress = progress_tracker.calculate_goal_progress()

        for period, data in goal_progress.items():
            icon = '✅' if data['achieved'] else '⏳'
            print(f"   {icon} {period.capitalize()}: {data['current']}/{data['goal']}")

    # Достижения
    if args.badges or args.all:
        print("\n🏆 Достижения:\n")

        achievement_system = AchievementSystem(tracker)
        unlocked = achievement_system.get_unlocked_achievements()

        if unlocked:
            print(f"   Разблокировано: {len(unlocked)}\n")
            for ach in unlocked[:15]:
                print(f"   {ach['icon']} {ach['name']}")
        else:
            print("   Пока нет разблокированных достижений. Начните читать!")

        # Следующие достижения
        print(f"\n   Ближайшие к разблокировке:")
        next_achievements = achievement_system.get_next_achievements(5)

        for ach in next_achievements:
            progress_pct = (ach['progress'] / ach['required']) * 100
            print(f"   {ach['icon']} {ach['name']}: {ach['progress']}/{ach['required']} ({progress_pct:.0f}%)")

    # Рекомендации
    if args.recommendations or args.all:
        print("\n💡 Рекомендации:\n")

        recommender = ReadingRecommendations(tracker)

        # Continue
        continue_suggestions = recommender.suggest_continue()
        if continue_suggestions:
            print("   📖 Продолжить чтение:")
            for sug in continue_suggestions[:3]:
                print(f"      - {sug['path']} (~{sug['estimated_time_min']} мин)")

        # Related
        related_suggestions = recommender.suggest_related_to_recent(5)
        if related_suggestions:
            print("\n   🔗 Связанные с недавно прочитанными:")
            for sug in related_suggestions[:5]:
                print(f"      - {sug['path']}")
                print(f"        Причина: {sug['reason']}")

        # Fill gaps
        gap_suggestions = recommender.suggest_fill_gaps(5)
        if gap_suggestions:
            print("\n   🎯 Заполнить пробелы:")
            for sug in gap_suggestions[:5]:
                print(f"      - {sug['path']}")
                print(f"        {sug['reason']}")

    # HTML dashboard
    if args.html or args.all:
        html_file = args.html if args.html else root_dir / "reading_progress_dashboard.html"
        print(f"\n🎨 Генерация HTML dashboard...\n")

        visualizer = VisualizationGenerator(tracker)
        visualizer.save_html(html_file)

    # Итоговое сообщение
    if not any([args.mark_read, args.mark_progress, args.report, args.stats, args.badges, args.recommendations, args.html, args.all]):
        print("\n💡 Дополнительные опции:")
        print("   --stats                  # Детальная статистика")
        print("   --badges                 # Достижения")
        print("   --recommendations        # Что читать дальше")
        print("   --html dashboard.html    # HTML визуализация")
        print("   --all                    # Всё вместе")


if __name__ == "__main__":
    main()
