#!/usr/bin/env python3
"""
Advanced Concordance Search - Продвинутый поиск в конкордансе
Функции:
- Fuzzy search с Levenshtein distance
- Regex search
- Boolean operators (AND, OR, NOT)
- Wildcard search (*, ?)
- Phrase search ("...")
- KWIC (Key Word In Context)
- Context highlighting
- Export results (JSON, TXT, CSV)
- Search statistics

Вдохновлено: grep, ack, ag, ripgrep, Elasticsearch
"""

import json
import sys
from pathlib import Path
import re
from collections import Counter


class AdvancedConcordanceSearch:
    """Продвинутый поиск в конкордансе"""

    def __init__(self, concordance_file):
        self.concordance_file = concordance_file
        self.concordance = None
        self.load_concordance()

    def load_concordance(self):
        """Загрузить конкорданс"""
        if not self.concordance_file.exists():
            print("❌ Конкорданс не найден. Запустите сначала:")
            print("   python tools/build_concordance.py")
            return False

        with open(self.concordance_file, 'r', encoding='utf-8') as f:
            self.concordance = json.load(f)

        return True

    def levenshtein_distance(self, s1, s2):
        """Вычислить расстояние Левенштейна"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # Стоимость вставки, удаления, замены
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]

    def fuzzy_search(self, word, max_distance=2):
        """Нечёткий поиск с Levenshtein distance"""
        if not self.concordance:
            return []

        word_lower = word.lower()
        matches = []

        for concordance_word in self.concordance.keys():
            distance = self.levenshtein_distance(word_lower, concordance_word)

            if distance <= max_distance:
                matches.append((concordance_word, distance))

        # Сортировать по distance
        matches.sort(key=lambda x: x[1])

        return matches

    def regex_search(self, pattern):
        """Поиск по регулярному выражению"""
        if not self.concordance:
            return []

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            print(f"❌ Ошибка в regex: {e}")
            return []

        matches = []

        for word, entries in self.concordance.items():
            if regex.search(word):
                matches.append((word, entries))

        return matches

    def wildcard_search(self, pattern):
        """Поиск с wildcards (* и ?)"""
        # Преобразовать wildcard в regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex_pattern = '^' + regex_pattern + '$'

        return self.regex_search(regex_pattern)

    def boolean_search(self, query):
        """Boolean поиск (AND, OR, NOT)"""
        # Простая реализация: разделить по AND/OR/NOT
        # Пример: "docker AND python" или "docker OR kubernetes"

        if ' AND ' in query.upper():
            words = [w.strip().lower() for w in re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)]
            return self._search_and(words)

        elif ' OR ' in query.upper():
            words = [w.strip().lower() for w in re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)]
            return self._search_or(words)

        elif ' NOT ' in query.upper():
            parts = re.split(r'\s+NOT\s+', query, flags=re.IGNORECASE)
            if len(parts) == 2:
                include = parts[0].strip().lower()
                exclude = parts[1].strip().lower()
                return self._search_not(include, exclude)

        # Обычный поиск
        return self.exact_search(query)

    def _search_and(self, words):
        """Поиск с AND - все слова должны присутствовать"""
        if not self.concordance:
            return []

        # Найти общие файлы для всех слов
        file_sets = []

        for word in words:
            if word in self.concordance:
                files = set(entry['file'] for entry in self.concordance[word])
                file_sets.append(files)

        if not file_sets:
            return []

        # Пересечение всех множеств
        common_files = file_sets[0]
        for file_set in file_sets[1:]:
            common_files &= file_set

        # Собрать записи из общих файлов
        results = []
        for word in words:
            if word in self.concordance:
                for entry in self.concordance[word]:
                    if entry['file'] in common_files:
                        results.append((word, entry))

        return results

    def _search_or(self, words):
        """Поиск с OR - любое слово"""
        if not self.concordance:
            return []

        results = []

        for word in words:
            if word in self.concordance:
                for entry in self.concordance[word]:
                    results.append((word, entry))

        return results

    def _search_not(self, include_word, exclude_word):
        """Поиск с NOT - исключить слово"""
        if not self.concordance:
            return []

        # Файлы с exclude_word
        exclude_files = set()
        if exclude_word in self.concordance:
            exclude_files = set(entry['file'] for entry in self.concordance[exclude_word])

        # Искать include_word, но не в exclude_files
        results = []
        if include_word in self.concordance:
            for entry in self.concordance[include_word]:
                if entry['file'] not in exclude_files:
                    results.append((include_word, entry))

        return results

    def exact_search(self, word):
        """Точный поиск слова"""
        if not self.concordance:
            return []

        word_lower = word.lower()

        if word_lower not in self.concordance:
            return []

        entries = self.concordance[word_lower]
        return [(word_lower, entry) for entry in entries]

    def highlight_context(self, context, word):
        """Подсветить слово в контексте"""
        # Использовать ANSI escape codes для цвета
        highlighted = re.sub(
            f'({re.escape(word)})',
            r'\033[1;31m\1\033[0m',  # Красный цвет
            context,
            flags=re.IGNORECASE
        )
        return highlighted

    def kwic_display(self, results, context_width=40):
        """KWIC (Key Word In Context) отображение"""
        print("\n" + "=" * 80)
        print("KWIC Display".center(80))
        print("=" * 80 + "\n")

        for word, entry in results[:50]:
            context = entry['context']

            # Найти позицию слова в контексте
            match = re.search(re.escape(word), context, re.IGNORECASE)

            if match:
                start = match.start()
                end = match.end()

                # Вырезать контекст слева и справа
                left_context = context[max(0, start - context_width):start]
                keyword = context[start:end]
                right_context = context[end:min(len(context), end + context_width)]

                # Выровнять
                print(f"{left_context:>{context_width}} ", end='')
                print(f"\033[1;31m{keyword}\033[0m", end='')
                print(f" {right_context:<{context_width}}")
                print(f"  → {entry['file']}:{entry['line']}\n")

    def generate_statistics(self, results):
        """Статистика по результатам поиска"""
        if not results:
            return

        # Подсчитать файлы
        files = Counter(entry['file'] for _, entry in results)

        # Подсчитать слова
        words = Counter(word for word, _ in results)

        print("\n📊 Статистика поиска:\n")
        print(f"   Всего совпадений: {len(results)}")
        print(f"   Уникальных файлов: {len(files)}")
        print(f"   Уникальных слов: {len(words)}\n")

        print("   Топ-5 файлов:")
        for file, count in files.most_common(5):
            print(f"      {file}: {count}")

        if len(words) > 1:
            print("\n   Топ-5 слов:")
            for word, count in words.most_common(5):
                print(f"      {word}: {count}")

    def export_results(self, results, output_format='txt', output_file=None):
        """Экспорт результатов"""
        if not results:
            print("   Нечего экспортировать")
            return

        if output_format == 'json':
            data = [
                {'word': word, **entry}
                for word, entry in results
            ]

            output = json.dumps(data, ensure_ascii=False, indent=2)

        elif output_format == 'csv':
            lines = ['word,file,line,context']
            for word, entry in results:
                context = entry['context'].replace('"', '""')
                lines.append(f'"{word}","{entry["file"]}",{entry["line"]},"{context}"')

            output = '\n'.join(lines)

        else:  # txt
            lines = []
            for word, entry in results:
                lines.append(f"Word: {word}")
                lines.append(f"File: {entry['file']}:{entry['line']}")
                lines.append(f"Context: {entry['context']}")
                lines.append("")

            output = '\n'.join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ Результаты экспортированы: {output_file}")
        else:
            print(output)

    def search(self, query, mode='exact', max_results=50, display='list', export=None):
        """Универсальный поиск"""
        if not self.concordance:
            return

        # Выбрать режим поиска
        if mode == 'fuzzy':
            matches = self.fuzzy_search(query)
            results = []
            for word, distance in matches:
                for entry in self.concordance[word]:
                    results.append((word, entry))
                    if len(results) >= max_results:
                        break

        elif mode == 'regex':
            matches = self.regex_search(query)
            results = []
            for word, entries in matches:
                for entry in entries:
                    results.append((word, entry))

        elif mode == 'wildcard':
            matches = self.wildcard_search(query)
            results = []
            for word, entries in matches:
                for entry in entries:
                    results.append((word, entry))

        elif mode == 'boolean':
            results = self.boolean_search(query)

        else:  # exact
            results = self.exact_search(query)

        if not results:
            print(f"❌ Ничего не найдено для '{query}'")

            # Предложить похожие слова
            fuzzy_matches = self.fuzzy_search(query, max_distance=2)
            if fuzzy_matches:
                print(f"\nПохожие слова:")
                for word, distance in fuzzy_matches[:10]:
                    print(f"  - {word} (distance: {distance})")

            return

        print(f"\n📖 Найдено: {len(results)} совпадений\n")

        # Отобразить результаты
        if display == 'kwic':
            self.kwic_display(results)
        else:
            for i, (word, entry) in enumerate(results[:max_results], 1):
                print(f"{i}. {entry['file']}:{entry['line']}")
                highlighted = self.highlight_context(entry['context'], word)
                print(f"   {highlighted}\n")

            if len(results) > max_results:
                print(f"   ...и ещё {len(results) - max_results} совпадений")

        # Статистика
        self.generate_statistics(results)

        # Экспорт
        if export:
            self.export_results(results, export_format=export['format'], output_file=export.get('file'))


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Concordance Search')
    parser.add_argument('query', nargs='?', help='Слово или запрос для поиска')
    parser.add_argument('-m', '--mode', choices=['exact', 'fuzzy', 'regex', 'wildcard', 'boolean'],
                       default='exact', help='Режим поиска')
    parser.add_argument('-d', '--display', choices=['list', 'kwic'], default='list',
                       help='Формат отображения')
    parser.add_argument('-n', '--max-results', type=int, default=50,
                       help='Максимум результатов')
    parser.add_argument('-e', '--export', choices=['txt', 'json', 'csv'],
                       help='Экспорт результатов')
    parser.add_argument('-o', '--output', help='Файл для экспорта')

    args = parser.parse_args()

    if not args.query:
        print("Использование: python search_concordance.py <слово> [опции]")
        print("\nПримеры:")
        print("  python tools/search_concordance.py docker")
        print("  python tools/search_concordance.py 'docker*' -m wildcard")
        print("  python tools/search_concordance.py 'doc.*' -m regex")
        print("  python tools/search_concordance.py 'docker AND python' -m boolean")
        print("  python tools/search_concordance.py холодильник -m fuzzy")
        print("  python tools/search_concordance.py docker -d kwic")
        print("  python tools/search_concordance.py docker -e json -o results.json")
        return

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    concordance_file = root_dir / "concordance.json"

    searcher = AdvancedConcordanceSearch(concordance_file)

    export_config = None
    if args.export:
        export_config = {
            'format': args.export,
            'file': args.output
        }

    searcher.search(
        args.query,
        mode=args.mode,
        max_results=args.max_results,
        display=args.display,
        export=export_config
    )


if __name__ == "__main__":
    main()
