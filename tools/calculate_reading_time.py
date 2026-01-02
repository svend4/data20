#!/usr/bin/env python3
"""
Reading Time Calculator - Оценка времени чтения
Вычисляет примерное время, необходимое для чтения статьи

На основе исследований:
- Средняя скорость чтения: 200-250 слов/минута (русский язык)
- Технические тексты: 150-200 слов/минута
- Код: считается медленнее (примерно 50 строк/минута)
"""

from pathlib import Path
import yaml
import re
import math


class ReadingTimeCalculator:
    """
    Калькулятор времени чтения
    """

    def __init__(self, root_dir=".", wpm=200):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.wpm = wpm  # words per minute (слов в минуту)

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                body = match.group(2)
                return fm, body
        except:
            pass

        return None, None

    def count_words(self, text):
        """Подсчитать слова в тексте"""
        # Удалить markdown разметку
        # Удалить заголовки
        text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
        # Удалить код
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)
        # Удалить ссылки
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Удалить изображения
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

        # Подсчитать слова (кириллица + латиница)
        words = re.findall(r'\b[а-яёa-z]+\b', text.lower())

        return len(words)

    def count_code_blocks(self, text):
        """Подсчитать блоки кода"""
        code_blocks = re.findall(r'```.*?```', text, re.DOTALL)
        total_lines = 0

        for block in code_blocks:
            lines = block.split('\n')
            # Минус первая и последняя строка (```)
            total_lines += max(0, len(lines) - 2)

        return total_lines

    def calculate_reading_time(self, file_path):
        """
        Вычислить время чтения для файла

        Возвращает:
        {
            'words': количество слов,
            'code_lines': строк кода,
            'reading_minutes': минут для чтения текста,
            'code_minutes': минут для чтения кода,
            'total_minutes': общее время,
            'formatted': '5 мин чтения'
        }
        """
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        # Подсчитать слова
        words = self.count_words(content)

        # Подсчитать код
        code_lines = self.count_code_blocks(content)

        # Определить тип контента для корректировки скорости
        category = frontmatter.get('category', '') if frontmatter else ''

        # Для технических текстов - медленнее
        wpm = self.wpm
        if category in ['computers', 'programming']:
            wpm = int(self.wpm * 0.75)  # 25% медленнее

        # Время чтения текста
        reading_minutes = words / wpm if wpm > 0 else 0

        # Время чтения кода (примерно 50 строк/минута)
        code_minutes = code_lines / 50 if code_lines > 0 else 0

        # Общее время
        total_minutes = reading_minutes + code_minutes

        # Округлить до ближайшей минуты
        total_minutes_rounded = max(1, math.ceil(total_minutes))

        return {
            'words': words,
            'code_lines': code_lines,
            'reading_minutes': round(reading_minutes, 2),
            'code_minutes': round(code_minutes, 2),
            'total_minutes': round(total_minutes, 2),
            'total_minutes_rounded': total_minutes_rounded,
            'formatted': self.format_time(total_minutes_rounded)
        }

    def format_time(self, minutes):
        """Отформатировать время в читаемый вид"""
        if minutes < 1:
            return "< 1 мин"
        elif minutes == 1:
            return "1 мин"
        elif minutes < 60:
            return f"{int(minutes)} мин"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            if mins == 0:
                return f"{hours} ч"
            return f"{hours} ч {mins} мин"

    def add_reading_time_to_articles(self):
        """Добавить время чтения ко всем статьям"""
        print("⏱️  Вычисление времени чтения...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            reading_time = self.calculate_reading_time(md_file)

            if not reading_time:
                continue

            # Обновить frontmatter
            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not frontmatter:
                continue

            # Добавить время чтения
            old_time = frontmatter.get('reading_time')

            frontmatter['reading_time'] = reading_time['formatted']
            frontmatter['reading_time_minutes'] = reading_time['total_minutes_rounded']
            frontmatter['word_count'] = reading_time['words']

            if reading_time['code_lines'] > 0:
                frontmatter['code_lines'] = reading_time['code_lines']

            # Записать обратно
            try:
                new_content = "---\n"
                new_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += content

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                if old_time != reading_time['formatted']:
                    count += 1
                    print(f"✅ {md_file.relative_to(self.root_dir)} — {reading_time['formatted']}")

            except Exception as e:
                print(f"⚠️  Ошибка в {md_file}: {e}")

        print(f"\n✅ Обновлено статей: {count}")

    def generate_report(self):
        """Создать отчёт по времени чтения"""
        print("\n📊 Анализ времени чтения...\n")

        articles = []
        total_time = 0
        total_words = 0
        total_code = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            reading_time = self.calculate_reading_time(md_file)

            if not reading_time:
                continue

            frontmatter, _ = self.extract_frontmatter_and_content(md_file)

            articles.append({
                'file': str(md_file.relative_to(self.root_dir)),
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'category': frontmatter.get('category', '') if frontmatter else '',
                **reading_time
            })

            total_time += reading_time['total_minutes']
            total_words += reading_time['words']
            total_code += reading_time['code_lines']

        lines = []
        lines.append("# ⏱️  Отчёт: Время чтения\n\n")

        lines.append("## Общая статистика\n\n")
        lines.append(f"- **Всего статей**: {len(articles)}\n")
        lines.append(f"- **Общее время чтения**: {self.format_time(total_time)}\n")
        lines.append(f"- **Всего слов**: {total_words:,}\n")
        lines.append(f"- **Строк кода**: {total_code:,}\n")

        if articles:
            avg_time = total_time / len(articles)
            lines.append(f"- **Среднее время**: {self.format_time(avg_time)}\n\n")

        # Топ самых длинных статей
        lines.append("## Топ-10 самых длинных статей\n\n")
        sorted_articles = sorted(articles, key=lambda x: x['total_minutes'], reverse=True)

        for i, article in enumerate(sorted_articles[:10], 1):
            lines.append(f"{i}. **{article['title']}** — {article['formatted']}\n")
            lines.append(f"   - {article['words']:,} слов")
            if article['code_lines'] > 0:
                lines.append(f", {article['code_lines']} строк кода")
            lines.append(f"\n   - `{article['file']}`\n\n")

        # Топ самых коротких
        lines.append("\n## Топ-10 самых коротких статей\n\n")
        sorted_articles = sorted(articles, key=lambda x: x['total_minutes'])

        for i, article in enumerate(sorted_articles[:10], 1):
            lines.append(f"{i}. **{article['title']}** — {article['formatted']}\n")
            lines.append(f"   - {article['words']:,} слов\n")
            lines.append(f"   - `{article['file']}`\n\n")

        # По категориям
        lines.append("\n## По категориям\n\n")

        by_category = {}
        for article in articles:
            cat = article['category'] or 'Без категории'
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'time': 0, 'words': 0}

            by_category[cat]['count'] += 1
            by_category[cat]['time'] += article['total_minutes']
            by_category[cat]['words'] += article['words']

        for cat, stats in sorted(by_category.items()):
            lines.append(f"### {cat}\n\n")
            lines.append(f"- Статей: {stats['count']}\n")
            lines.append(f"- Общее время: {self.format_time(stats['time'])}\n")
            lines.append(f"- Всего слов: {stats['words']:,}\n")
            lines.append(f"- Среднее время: {self.format_time(stats['time'] / stats['count'])}\n\n")

        return ''.join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Reading Time Calculator - Оценка времени чтения'
    )

    parser.add_argument(
        '-f', '--file',
        help='Вычислить время для конкретного файла'
    )

    parser.add_argument(
        '-u', '--update',
        action='store_true',
        help='Обновить время чтения во всех статьях'
    )

    parser.add_argument(
        '-r', '--report',
        action='store_true',
        help='Создать отчёт'
    )

    parser.add_argument(
        '-w', '--wpm',
        type=int,
        default=200,
        help='Слов в минуту (по умолчанию 200)'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    calc = ReadingTimeCalculator(root_dir, wpm=args.wpm)

    if args.file:
        file_path = root_dir / args.file
        reading_time = calc.calculate_reading_time(file_path)

        if reading_time:
            print(f"\n⏱️  Время чтения: {reading_time['formatted']}\n")
            print(f"   Слов: {reading_time['words']:,}")
            print(f"   Строк кода: {reading_time['code_lines']}")
            print(f"   Время на текст: {reading_time['reading_minutes']:.1f} мин")
            print(f"   Время на код: {reading_time['code_minutes']:.1f} мин")
            print(f"   Общее время: {reading_time['total_minutes']:.1f} мин\n")
        else:
            print("❌ Не удалось обработать файл")

    elif args.update:
        calc.add_reading_time_to_articles()

    elif args.report:
        report = calc.generate_report()
        output_file = root_dir / "READING_TIME_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
