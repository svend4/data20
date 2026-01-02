#!/usr/bin/env python3
"""
Marginalia - Заметки на полях
Вдохновлено: Средневековые рукописи с маргиналиями

Позволяет добавлять комментарии, заметки и аннотации к статьям,
как монахи делали на полях манускриптов.
"""

from pathlib import Path
import yaml
import re
import json
from datetime import datetime
import argparse


class MarginaliaManager:
    """
    Менеджер маргиналий - заметок на полях статей
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.marginalia_db = self.root_dir / ".marginalia" / "notes.json"

        # Создать директорию для хранения
        self.marginalia_db.parent.mkdir(exist_ok=True)

        # Загрузить существующие маргиналии
        self.notes = self.load_notes()

    def load_notes(self):
        """Загрузить все маргиналии"""
        if self.marginalia_db.exists():
            with open(self.marginalia_db, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_notes(self):
        """Сохранить маргиналии"""
        with open(self.marginalia_db, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def add_note(self, article_file, note_text, position=None, note_type="comment", author="User"):
        """
        Добавить заметку к статье

        position может быть:
        - "line:42" - конкретная строка
        - "section:Introduction" - секция
        - "paragraph:3" - параграф
        - None - общая заметка к статье
        """
        # Нормализовать путь
        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path not in self.notes:
            self.notes[article_path] = []

        note = {
            'id': len(self.notes[article_path]) + 1,
            'text': note_text,
            'position': position or "general",
            'type': note_type,  # comment, warning, idea, question, cross-reference
            'author': author,
            'date': datetime.now().isoformat(),
            'resolved': False
        }

        self.notes[article_path].append(note)
        self.save_notes()

        return note

    def get_notes(self, article_file):
        """Получить все заметки для статьи"""
        article_path = str(Path(article_file).relative_to(self.root_dir))
        return self.notes.get(article_path, [])

    def update_note(self, article_file, note_id, **updates):
        """Обновить заметку"""
        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path not in self.notes:
            return None

        for note in self.notes[article_path]:
            if note['id'] == note_id:
                note.update(updates)
                note['modified'] = datetime.now().isoformat()
                self.save_notes()
                return note

        return None

    def delete_note(self, article_file, note_id):
        """Удалить заметку"""
        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path not in self.notes:
            return False

        self.notes[article_path] = [
            note for note in self.notes[article_path]
            if note['id'] != note_id
        ]

        self.save_notes()
        return True

    def mark_resolved(self, article_file, note_id):
        """Отметить заметку как разрешённую"""
        return self.update_note(article_file, note_id, resolved=True)

    def get_all_notes_by_type(self, note_type=None):
        """Получить все заметки определённого типа"""
        all_notes = []

        for article_path, notes in self.notes.items():
            for note in notes:
                if note_type is None or note['type'] == note_type:
                    all_notes.append({
                        'article': article_path,
                        **note
                    })

        return all_notes

    def get_unresolved_notes(self):
        """Получить все неразрешённые заметки"""
        unresolved = []

        for article_path, notes in self.notes.items():
            for note in notes:
                if not note.get('resolved', False):
                    unresolved.append({
                        'article': article_path,
                        **note
                    })

        return unresolved

    def export_to_markdown(self, article_file, output_file=None):
        """Экспортировать маргиналии статьи в markdown"""
        notes = self.get_notes(article_file)

        if not notes:
            return None

        lines = []
        lines.append(f"# 📝 Маргиналии: {Path(article_file).name}\n\n")
        lines.append(f"> Заметки на полях для статьи `{article_file}`\n\n")

        # Группировать по типу
        by_type = {}
        for note in notes:
            note_type = note['type']
            if note_type not in by_type:
                by_type[note_type] = []
            by_type[note_type].append(note)

        # Иконки для типов
        type_icons = {
            'comment': '💬',
            'warning': '⚠️',
            'idea': '💡',
            'question': '❓',
            'cross-reference': '🔗',
            'todo': '✅'
        }

        for note_type, type_notes in sorted(by_type.items()):
            icon = type_icons.get(note_type, '📌')
            lines.append(f"## {icon} {note_type.title()}\n\n")

            for note in type_notes:
                status = "✓" if note.get('resolved') else "○"
                lines.append(f"### {status} Заметка #{note['id']}\n\n")
                lines.append(f"**Позиция**: {note['position']}  \n")
                lines.append(f"**Автор**: {note['author']}  \n")
                lines.append(f"**Дата**: {note['date'][:10]}  \n")
                if note.get('resolved'):
                    lines.append(f"**Статус**: Разрешено ✓  \n")
                lines.append(f"\n{note['text']}\n\n")
                lines.append("---\n\n")

        content = ''.join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    def generate_report(self):
        """Создать общий отчёт по всем маргиналиям"""
        lines = []
        lines.append("# 📝 Отчёт по маргиналиям\n\n")

        total_notes = sum(len(notes) for notes in self.notes.values())
        total_articles = len(self.notes)
        unresolved = len(self.get_unresolved_notes())

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего заметок**: {total_notes}\n")
        lines.append(f"- **Статей с заметками**: {total_articles}\n")
        lines.append(f"- **Неразрешённых заметок**: {unresolved}\n\n")

        # По типам
        by_type = {}
        for notes in self.notes.values():
            for note in notes:
                note_type = note['type']
                by_type[note_type] = by_type.get(note_type, 0) + 1

        lines.append("## По типам\n\n")
        for note_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"- **{note_type}**: {count}\n")

        lines.append("\n## Неразрешённые заметки\n\n")
        unresolved_notes = self.get_unresolved_notes()

        if unresolved_notes:
            for note in unresolved_notes[:20]:
                lines.append(f"### {note['article']}\n\n")
                lines.append(f"- **ID**: #{note['id']}\n")
                lines.append(f"- **Тип**: {note['type']}\n")
                lines.append(f"- **Позиция**: {note['position']}\n")
                lines.append(f"- **Текст**: {note['text'][:100]}...\n\n")
        else:
            lines.append("Все заметки разрешены! 🎉\n\n")

        # Топ статей с наибольшим количеством заметок
        lines.append("\n## Статьи с наибольшим количеством заметок\n\n")

        article_counts = [(article, len(notes)) for article, notes in self.notes.items()]
        article_counts.sort(key=lambda x: -x[1])

        for article, count in article_counts[:10]:
            lines.append(f"- **{article}**: {count} заметок\n")

        return ''.join(lines)

    def print_notes(self, article_file=None):
        """Вывести заметки в консоль"""
        if article_file:
            notes = self.get_notes(article_file)
            print(f"\n📝 Маргиналии для {article_file}:\n")

            if not notes:
                print("   Заметок нет\n")
                return

            for note in notes:
                status = "✓" if note.get('resolved') else "○"
                print(f"{status} #{note['id']} [{note['type']}] @ {note['position']}")
                print(f"   {note['text']}")
                print(f"   — {note['author']}, {note['date'][:10]}\n")
        else:
            # Вывести статистику по всем заметкам
            total = sum(len(notes) for notes in self.notes.values())
            unresolved = len(self.get_unresolved_notes())

            print(f"\n📝 Всего маргиналий: {total}")
            print(f"   Неразрешённых: {unresolved}")
            print(f"   Статей с заметками: {len(self.notes)}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Marginalia - Управление заметками на полях статей'
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # add - добавить заметку
    add_parser = subparsers.add_parser('add', help='Добавить заметку')
    add_parser.add_argument('article', help='Путь к статье')
    add_parser.add_argument('text', help='Текст заметки')
    add_parser.add_argument('-p', '--position', help='Позиция (line:N, section:Name)')
    add_parser.add_argument('-t', '--type', default='comment',
                           choices=['comment', 'warning', 'idea', 'question', 'cross-reference', 'todo'],
                           help='Тип заметки')
    add_parser.add_argument('-a', '--author', default='User', help='Автор')

    # list - показать заметки
    list_parser = subparsers.add_parser('list', help='Показать заметки')
    list_parser.add_argument('article', nargs='?', help='Путь к статье (опционально)')
    list_parser.add_argument('-t', '--type', help='Фильтр по типу')
    list_parser.add_argument('-u', '--unresolved', action='store_true', help='Только неразрешённые')

    # resolve - отметить как разрешённую
    resolve_parser = subparsers.add_parser('resolve', help='Отметить заметку как разрешённую')
    resolve_parser.add_argument('article', help='Путь к статье')
    resolve_parser.add_argument('note_id', type=int, help='ID заметки')

    # delete - удалить заметку
    delete_parser = subparsers.add_parser('delete', help='Удалить заметку')
    delete_parser.add_argument('article', help='Путь к статье')
    delete_parser.add_argument('note_id', type=int, help='ID заметки')

    # export - экспортировать
    export_parser = subparsers.add_parser('export', help='Экспортировать заметки')
    export_parser.add_argument('article', help='Путь к статье')
    export_parser.add_argument('-o', '--output', help='Выходной файл')

    # report - отчёт
    subparsers.add_parser('report', help='Создать общий отчёт')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    manager = MarginaliaManager(root_dir)

    if args.command == 'add':
        article_path = root_dir / args.article
        note = manager.add_note(
            article_path,
            args.text,
            position=args.position,
            note_type=args.type,
            author=args.author
        )
        print(f"✅ Заметка #{note['id']} добавлена к {args.article}")

    elif args.command == 'list':
        if args.article:
            article_path = root_dir / args.article
            manager.print_notes(article_path)
        elif args.unresolved:
            notes = manager.get_unresolved_notes()
            print(f"\n⚠️  Неразрешённых заметок: {len(notes)}\n")
            for note in notes:
                print(f"#{note['id']} {note['article']} @ {note['position']}")
                print(f"   {note['text'][:80]}...\n")
        elif args.type:
            notes = manager.get_all_notes_by_type(args.type)
            print(f"\n📝 Заметок типа '{args.type}': {len(notes)}\n")
            for note in notes:
                print(f"#{note['id']} {note['article']}")
                print(f"   {note['text'][:80]}...\n")
        else:
            manager.print_notes()

    elif args.command == 'resolve':
        article_path = root_dir / args.article
        if manager.mark_resolved(article_path, args.note_id):
            print(f"✅ Заметка #{args.note_id} отмечена как разрешённая")
        else:
            print(f"❌ Заметка не найдена")

    elif args.command == 'delete':
        article_path = root_dir / args.article
        if manager.delete_note(article_path, args.note_id):
            print(f"✅ Заметка #{args.note_id} удалена")
        else:
            print(f"❌ Заметка не найдена")

    elif args.command == 'export':
        article_path = root_dir / args.article
        output = args.output or f"{article_path.stem}_marginalia.md"
        content = manager.export_to_markdown(article_path, output)
        if content:
            print(f"✅ Маргиналии экспортированы в {output}")
        else:
            print(f"⚠️  Нет заметок для экспорта")

    elif args.command == 'report':
        report = manager.generate_report()
        output_file = root_dir / "MARGINALIA_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
