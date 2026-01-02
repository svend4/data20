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

    parser = argparse.ArgumentParser(description='Advanced Reading Progress Tracker')
    parser.add_argument('--mark-read', help='Пометить статью как прочитанную')
    parser.add_argument('--mark-progress', help='Пометить статью как в процессе')
    parser.add_argument('--time', type=float, help='Фактическое время чтения (минут)')
    parser.add_argument('--report', action='store_true', help='Создать отчёт')
    parser.add_argument('--stats', action='store_true', help='Показать статистику')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tracker = AdvancedReadingProgressTracker(root_dir)

    if args.mark_read:
        tracker.mark_as_read(args.mark_read, reading_time_min=args.time)

    if args.mark_progress:
        tracker.mark_in_progress(args.mark_progress)

    if args.report or args.stats or (not args.mark_read and not args.mark_progress):
        tracker.generate_report()


if __name__ == "__main__":
    main()
