#!/usr/bin/env python3
"""
Timeline Generator - Генератор временной шкалы
Создаёт timeline статей по датам

Вдохновлено: GitHub timeline, Google Timeline
"""

from pathlib import Path
import yaml
import re
from datetime import datetime
from collections import defaultdict
import json


class TimelineGenerator:
    """Генератор timeline"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.events = []

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

    def collect_events(self):
        """Собрать события"""
        print("📅 Сбор событий для timeline...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)

            if not frontmatter:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem)
            date = frontmatter.get('date')

            if date:
                try:
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                    else:
                        date_obj = datetime.combine(date, datetime.min.time())

                    self.events.append({
                        'date': date_obj.isoformat(),
                        'title': title,
                        'path': article_path,
                        'category': frontmatter.get('category', '')
                    })
                except:
                    pass

        self.events.sort(key=lambda x: x['date'])
        print(f"   События собраны: {len(self.events)}\n")

    def generate_html_timeline(self):
        """Создать HTML timeline"""
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Timeline</title>
    <style>
        body {{ font-family: Arial; padding: 40px; background: #f5f5f5; }}
        .timeline {{ position: relative; max-width: 800px; margin: 0 auto; }}
        .timeline::before {{ content: ''; position: absolute; left: 50%; width: 2px;
                            height: 100%; background: #ddd; }}
        .event {{ margin-bottom: 40px; position: relative; }}
        .event-content {{ background: white; padding: 20px; border-radius: 8px;
                         box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 45%; }}
        .event:nth-child(odd) .event-content {{ margin-left: 0; }}
        .event:nth-child(even) .event-content {{ margin-left: 55%; }}
        .event-date {{ background: #3498db; color: white; padding: 5px 15px;
                      border-radius: 20px; display: inline-block; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h1 style="text-align: center;">📅 Timeline</h1>
    <div class="timeline">
'''

        for event in self.events:
            date = datetime.fromisoformat(event['date']).strftime('%d.%m.%Y')
            html += f'''
        <div class="event">
            <div class="event-content">
                <div class="event-date">{date}</div>
                <h3>{event['title']}</h3>
                <p><a href="{event['path']}">Читать →</a></p>
            </div>
        </div>'''

        html += '''
    </div>
</body>
</html>'''

        output_file = self.root_dir / "timeline.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Timeline: {output_file}")

    def save_json(self):
        """Сохранить в JSON"""
        output_file = self.root_dir / "timeline.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'events': self.events}, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = TimelineGenerator(root_dir)
    generator.collect_events()
    generator.generate_html_timeline()
    generator.save_json()


if __name__ == "__main__":
    main()
