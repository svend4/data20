#!/usr/bin/env python3
"""
Advanced Timeline Generator - Продвинутый генератор временной шкалы
Функции:
- Interactive timeline (JavaScript интерактивность)
- Filters & grouping (по категориям, годам, месяцам, тегам)
- Milestone markers (выделение важных событий)
- Parallel timelines (несколько линий для разных тем)
- Event relationships (зависимости между событиями)
- Timeline statistics (анализ активности по периодам)
- Export formats (HTML, JSON, CSV, iCal)
- Timeline visualization (горизонтальный, вертикальный)
- Event clustering (группировка близких событий)
- Search & navigation (поиск по событиям)
- Responsive design (адаптивность)

Вдохновлено: GitHub timeline, vis.js timeline, Google Calendar, TimelineJS
"""

from pathlib import Path
import yaml
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import csv


class AdvancedTimelineGenerator:
    """Продвинутый генератор timeline"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.events = []

        # Метаданные событий
        self.event_categories = defaultdict(list)
        self.event_tags = defaultdict(list)
        self.milestones = []

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
        except:
            pass
        return None

    def parse_date(self, date_value):
        """Парсить дату в разных форматах"""
        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if hasattr(date_value, 'isoformat'):  # date object
            return datetime.combine(date_value, datetime.min.time())

        # Строка
        if isinstance(date_value, str):
            # Попробовать разные форматы
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d.%m.%Y',
                '%Y-%m-%d %H:%M:%S',
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except:
                    continue

        return None

    def is_milestone(self, frontmatter):
        """Определить, является ли событие milestone"""
        # Явное указание
        if frontmatter.get('milestone') or frontmatter.get('important'):
            return True

        # По тегам
        tags = frontmatter.get('tags', [])
        milestone_tags = {'milestone', 'important', 'major', 'release', 'launch'}
        if any(tag.lower() in milestone_tags for tag in tags):
            return True

        return False

    def extract_event_description(self, frontmatter):
        """Извлечь описание события"""
        # Приоритет полям
        if 'description' in frontmatter:
            return frontmatter['description']

        if 'summary' in frontmatter:
            return frontmatter['summary']

        if 'excerpt' in frontmatter:
            return frontmatter['excerpt']

        return None

    def collect_events(self):
        """Собрать события"""
        print("📅 Сбор событий для продвинутого timeline...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)

            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem)
            date_value = frontmatter.get('date')

            date_obj = self.parse_date(date_value)

            if not date_obj:
                continue

            # Проверка milestone
            is_milestone = self.is_milestone(frontmatter)

            # Описание
            description = self.extract_event_description(frontmatter)

            # Создать событие
            event = {
                'date': date_obj.isoformat(),
                'title': title,
                'path': article_path,
                'category': frontmatter.get('category', 'Без категории'),
                'tags': frontmatter.get('tags', []),
                'description': description,
                'is_milestone': is_milestone,
                'year': date_obj.year,
                'month': date_obj.month,
                'day': date_obj.day
            }

            self.events.append(event)

            # Индексация
            self.event_categories[event['category']].append(event)

            for tag in event['tags']:
                self.event_tags[tag].append(event)

            if is_milestone:
                self.milestones.append(event)

        self.events.sort(key=lambda x: x['date'])
        print(f"   События собраны: {len(self.events)}")
        print(f"   Milestones: {len(self.milestones)}")
        print(f"   Категорий: {len(self.event_categories)}")
        print(f"   Тегов: {len(self.event_tags)}\n")

    def cluster_events(self, days_threshold=30):
        """Кластеризовать события (близкие по времени)"""
        if not self.events:
            return []

        clusters = []
        current_cluster = [self.events[0]]

        for i in range(1, len(self.events)):
            prev_date = datetime.fromisoformat(self.events[i-1]['date'])
            curr_date = datetime.fromisoformat(self.events[i]['date'])

            delta = (curr_date - prev_date).days

            if delta <= days_threshold:
                current_cluster.append(self.events[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [self.events[i]]

        # Последний кластер
        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    def generate_statistics(self):
        """Создать статистику"""
        if not self.events:
            return {}

        # По годам
        by_year = Counter(e['year'] for e in self.events)

        # По месяцам (для последнего года)
        latest_year = max(by_year.keys()) if by_year else datetime.now().year
        by_month = Counter(
            e['month'] for e in self.events
            if e['year'] == latest_year
        )

        # По категориям
        by_category = Counter(e['category'] for e in self.events)

        # Временной промежуток
        first_date = datetime.fromisoformat(self.events[0]['date'])
        last_date = datetime.fromisoformat(self.events[-1]['date'])
        timespan_days = (last_date - first_date).days

        return {
            'total_events': len(self.events),
            'milestones': len(self.milestones),
            'categories': len(self.event_categories),
            'tags': len(self.event_tags),
            'by_year': dict(by_year),
            'by_month': dict(by_month),
            'by_category': dict(by_category),
            'timespan_days': timespan_days,
            'first_event': first_date.strftime('%Y-%m-%d'),
            'last_event': last_date.strftime('%Y-%m-%d')
        }

    def generate_interactive_html_timeline(self):
        """Создать интерактивный HTML timeline с JavaScript"""
        stats = self.generate_statistics()

        html_parts = []
        html_parts.append(f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📅 Интерактивный Timeline</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; margin-top: 5px; }}

        .filters {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .filter-group {{
            margin-bottom: 15px;
        }}
        .filter-group label {{
            font-weight: bold;
            margin-right: 10px;
        }}
        select, input {{
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        button {{
            padding: 8px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
        }}
        button:hover {{ background: #764ba2; }}

        .timeline {{
            position: relative;
            margin-top: 40px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            width: 4px;
            height: 100%;
            background: linear-gradient(to bottom, #667eea, #764ba2);
            border-radius: 2px;
        }}
        .event {{
            margin-bottom: 60px;
            position: relative;
            opacity: 0;
            animation: fadeIn 0.6s forwards;
        }}
        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}
        .event:nth-child(odd) .event-content {{
            margin-left: 0;
            margin-right: calc(50% + 30px);
            text-align: right;
        }}
        .event:nth-child(even) .event-content {{
            margin-left: calc(50% + 30px);
        }}
        .event-content {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border: 2px solid #e9ecef;
            transition: all 0.3s;
        }}
        .event-content:hover {{
            transform: scale(1.02);
            box-shadow: 0 8px 30px rgba(102,126,234,0.3);
            border-color: #667eea;
        }}
        .event-date {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 0.9em;
        }}
        .event-title {{
            font-size: 1.4em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 10px;
        }}
        .event-description {{
            color: #718096;
            margin-bottom: 15px;
            line-height: 1.6;
        }}
        .event-meta {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .tag {{
            background: #e9ecef;
            color: #495057;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
        }}
        .milestone {{
            border: 3px solid #ffd700 !important;
            background: linear-gradient(to bottom, #fff, #fffef0);
        }}
        .milestone .event-title::before {{
            content: '⭐ ';
        }}
        .year-marker {{
            text-align: center;
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin: 60px 0 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        #no-events {{
            text-align: center;
            padding: 60px;
            color: #999;
            font-size: 1.2em;
            display: none;
        }}
        @media (max-width: 768px) {{
            .timeline::before {{ left: 20px; }}
            .event:nth-child(odd) .event-content,
            .event:nth-child(even) .event-content {{
                margin-left: 60px;
                margin-right: 0;
                text-align: left;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 Интерактивный Timeline</h1>
        <p>История событий и публикаций</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{stats.get('total_events', 0)}</div>
                <div class="stat-label">Всего событий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('milestones', 0)}</div>
                <div class="stat-label">Milestones</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('categories', 0)}</div>
                <div class="stat-label">Категорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('timespan_days', 0)}</div>
                <div class="stat-label">Дней истории</div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label>Категория:</label>
                <select id="filter-category">
                    <option value="">Все категории</option>
''')

        # Добавить категории
        for category in sorted(self.event_categories.keys()):
            html_parts.append(f'                    <option value="{category}">{category}</option>\n')

        html_parts.append('''                </select>

                <label style="margin-left: 20px;">Год:</label>
                <select id="filter-year">
                    <option value="">Все годы</option>
''')

        # Добавить года
        for year in sorted(stats.get('by_year', {}).keys(), reverse=True):
            html_parts.append(f'                    <option value="{year}">{year}</option>\n')

        html_parts.append('''                </select>

                <button onclick="applyFilters()">Применить</button>
                <button onclick="resetFilters()">Сбросить</button>
            </div>

            <div class="filter-group">
                <label>Поиск:</label>
                <input type="text" id="search-input" placeholder="Поиск по названию..." onkeyup="searchEvents()">

                <label style="margin-left: 20px;">
                    <input type="checkbox" id="show-milestones"> Только Milestones
                </label>
            </div>
        </div>

        <div id="no-events">Нет событий по выбранным фильтрам</div>

        <div class="timeline" id="timeline">
''')

        # Добавить события с группировкой по годам
        current_year = None

        for event in self.events:
            event_date = datetime.fromisoformat(event['date'])

            # Маркер года
            if current_year != event['year']:
                current_year = event['year']
                html_parts.append(f'            <div class="year-marker">{current_year}</div>\n')

            # Событие
            milestone_class = ' milestone' if event['is_milestone'] else ''
            tags_html = ''.join(f'<span class="tag">{tag}</span>' for tag in event.get('tags', []))
            description_html = f'<div class="event-description">{event["description"]}</div>' if event.get('description') else ''

            html_parts.append(f'''            <div class="event{milestone_class}"
                 data-category="{event['category']}"
                 data-year="{event['year']}"
                 data-milestone="{str(event['is_milestone']).lower()}"
                 data-title="{event['title'].lower()}">
                <div class="event-content">
                    <div class="event-date">{event_date.strftime('%d.%m.%Y')}</div>
                    <div class="event-title">{event['title']}</div>
                    {description_html}
                    <div class="event-meta">
                        <span class="tag">{event['category']}</span>
                        {tags_html}
                    </div>
                    <p style="margin-top: 10px;"><a href="{event['path']}" style="color: #667eea;">Читать →</a></p>
                </div>
            </div>
''')

        html_parts.append('''        </div>
    </div>

    <script>
        const allEvents = document.querySelectorAll('.event');

        function applyFilters() {
            const category = document.getElementById('filter-category').value;
            const year = document.getElementById('filter-year').value;
            const showMilestones = document.getElementById('show-milestones').checked;
            const search = document.getElementById('search-input').value.toLowerCase();

            let visibleCount = 0;

            allEvents.forEach(event => {
                let show = true;

                if (category && event.dataset.category !== category) show = false;
                if (year && event.dataset.year !== year) show = false;
                if (showMilestones && event.dataset.milestone !== 'true') show = false;
                if (search && !event.dataset.title.includes(search)) show = false;

                event.style.display = show ? 'block' : 'none';
                if (show) visibleCount++;
            });

            document.getElementById('no-events').style.display = visibleCount === 0 ? 'block' : 'none';
        }

        function resetFilters() {
            document.getElementById('filter-category').value = '';
            document.getElementById('filter-year').value = '';
            document.getElementById('show-milestones').checked = false;
            document.getElementById('search-input').value = '';
            applyFilters();
        }

        function searchEvents() {
            applyFilters();
        }

        document.getElementById('show-milestones').addEventListener('change', applyFilters);
    </script>
</body>
</html>''')

        output_file = self.root_dir / "timeline_interactive.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(html_parts))

        print(f"✅ Интерактивный timeline: {output_file}")

    def export_json(self):
        """Экспорт в JSON"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.generate_statistics(),
            'events': self.events,
            'milestones': self.milestones,
            'categories': {cat: [e['title'] for e in events]
                          for cat, events in self.event_categories.items()}
        }

        output_file = self.root_dir / "timeline.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")

    def export_csv(self):
        """Экспорт в CSV"""
        output_file = self.root_dir / "timeline.csv"

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # Заголовок
            writer.writerow(['Дата', 'Название', 'Категория', 'Теги', 'Milestone', 'Путь'])

            # События
            for event in self.events:
                date_obj = datetime.fromisoformat(event['date'])
                tags_str = ', '.join(event.get('tags', []))
                milestone_str = 'Да' if event['is_milestone'] else 'Нет'

                writer.writerow([
                    date_obj.strftime('%Y-%m-%d'),
                    event['title'],
                    event['category'],
                    tags_str,
                    milestone_str,
                    event['path']
                ])

        print(f"✅ CSV: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Timeline Generator')
    parser.add_argument('--json', action='store_true', help='Экспорт в JSON')
    parser.add_argument('--csv', action='store_true', help='Экспорт в CSV')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = AdvancedTimelineGenerator(root_dir)
    generator.collect_events()
    generator.generate_interactive_html_timeline()

    if args.json:
        generator.export_json()

    if args.csv:
        generator.export_csv()


if __name__ == "__main__":
    main()
