#!/usr/bin/env python3
"""
Reading Progress - Трекинг прогресса чтения
Отслеживает, какие статьи прочитаны

Вдохновлено: Kindle reading progress, Pocket
"""

from pathlib import Path
import json
from datetime import datetime


class ReadingProgressTracker:
    """Трекер прогресса чтения"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.progress_file = self.root_dir / ".reading_progress.json"

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
            'articles': {},
            'statistics': {
                'total_read': 0,
                'total_in_progress': 0,
                'total_unread': 0
            }
        }

    def save_progress(self):
        """Сохранить прогресс в файл"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def mark_as_read(self, article_path):
        """Пометить статью как прочитанную"""
        self.progress['articles'][article_path] = {
            'status': 'read',
            'completed_at': datetime.now().isoformat()
        }
        self.save_progress()
        print(f"✅ Отмечено как прочитанное: {article_path}")

    def mark_in_progress(self, article_path):
        """Пометить статью как в процессе"""
        self.progress['articles'][article_path] = {
            'status': 'in_progress',
            'started_at': datetime.now().isoformat()
        }
        self.save_progress()
        print(f"📖 В процессе: {article_path}")

    def generate_report(self):
        """Создать отчёт о прогрессе"""
        from pathlib import Path

        knowledge_dir = self.root_dir / "knowledge"
        all_articles = []

        for md_file in knowledge_dir.rglob("*.md"):
            if md_file.name != "INDEX.md":
                article_path = str(md_file.relative_to(self.root_dir))
                all_articles.append(article_path)

        read = [a for a, d in self.progress['articles'].items() if d['status'] == 'read']
        in_progress = [a for a, d in self.progress['articles'].items() if d['status'] == 'in_progress']
        unread = [a for a in all_articles if a not in self.progress['articles']]

        lines = []
        lines.append("# 📚 Прогресс чтения\n\n")
        lines.append(f"**Всего статей**: {len(all_articles)}\n\n")
        lines.append(f"- ✅ Прочитано: {len(read)}\n")
        lines.append(f"- 📖 В процессе: {len(in_progress)}\n")
        lines.append(f"- ⬜ Не прочитано: {len(unread)}\n\n")

        if len(all_articles) > 0:
            progress_pct = (len(read) / len(all_articles)) * 100
            lines.append(f"**Прогресс**: {progress_pct:.1f}%\n\n")

        output_file = self.root_dir / "READING_PROGRESS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Reading Progress Tracker')
    parser.add_argument('--mark-read', help='Пометить статью как прочитанную')
    parser.add_argument('--mark-progress', help='Пометить статью как в процессе')
    parser.add_argument('--report', action='store_true', help='Создать отчёт')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tracker = ReadingProgressTracker(root_dir)

    if args.mark_read:
        tracker.mark_as_read(args.mark_read)

    if args.mark_progress:
        tracker.mark_in_progress(args.mark_progress)

    if args.report or (not args.mark_read and not args.mark_progress):
        tracker.generate_report()


if __name__ == "__main__":
    main()
