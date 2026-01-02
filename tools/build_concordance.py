#!/usr/bin/env python3
"""
Concordance Builder - Средневековая техника для современной базы знаний
Создаёт полный индекс всех слов с указанием их местоположения

Вдохновлено: Concordantia Sacrorum Bibliorum (1230 г.)
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json


class ConcordanceBuilder:
    """
    Построитель конкорданса - алфавитного указателя всех значимых слов
    с указанием, где они встречаются в базе знаний
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.concordance = defaultdict(list)

        # Стоп-слова (пропускаем незначимые слова)
        self.stop_words = {
            # Русские
            'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как',
            'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к',
            'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было',
            'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь',
            'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или',
            'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять',
            'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей',
            'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для',
            'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без',
            'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж',
            'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой',
            'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой',
            'тем', 'чтобы', 'нее', 'были', 'куда', 'зачем', 'всех',
            'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой',
            'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти',
            'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве',
            'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой',
            'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой',
            'им', 'более', 'всегда', 'конечно', 'всю', 'между',

            # English
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one',
            'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out',
            'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when',
            'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
            'take', 'people', 'into', 'year', 'your', 'good', 'some',
            'could', 'them', 'see', 'other', 'than', 'then', 'now',
            'look', 'only', 'come', 'its', 'over', 'think', 'also',
            'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
            'well', 'way', 'even', 'new', 'want', 'because', 'any',
            'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are',
            'been', 'has', 'had', 'were', 'said', 'did', 'having',
            'may', 'should', 'does', 'being'
        }

    def extract_words(self, text, file_path):
        """
        Извлечь значимые слова из текста
        Возвращает: список (слово, номер строки, контекст)
        """
        words = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Удалить markdown разметку
            clean_line = re.sub(r'[#*`\[\]()]', ' ', line)

            # Извлечь слова (кириллица и латиница)
            found_words = re.findall(r'\b[а-яёa-z]{3,}\b', clean_line.lower())

            for word in found_words:
                # Пропустить стоп-слова
                if word in self.stop_words:
                    continue

                # Пропустить числа
                if word.isdigit():
                    continue

                # Получить контекст (слова вокруг)
                context = self.get_context(clean_line, word, window=40)

                words.append({
                    'word': word,
                    'line': line_num,
                    'context': context,
                    'file': str(file_path.relative_to(self.root_dir))
                })

        return words

    def get_context(self, line, word, window=40):
        """Получить контекст вокруг слова"""
        # Найти позицию слова
        pos = line.lower().find(word.lower())
        if pos == -1:
            return line[:window]

        # Взять окно вокруг слова
        start = max(0, pos - window // 2)
        end = min(len(line), pos + len(word) + window // 2)

        context = line[start:end].strip()

        # Добавить многоточия если обрезано
        if start > 0:
            context = '...' + context
        if end < len(line):
            context = context + '...'

        return context

    def build(self):
        """Построить конкорданс"""
        print("📖 Построение конкорданса (concordance)...")
        print("   Вдохновлено средневековыми индексами Библии\n")

        total_words = 0
        total_files = 0

        # Сканировать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            total_files += 1

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Пропустить frontmatter
                content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

                # Извлечь слова
                words = self.extract_words(content, md_file)
                total_words += len(words)

                # Добавить в конкорданс
                for entry in words:
                    word = entry['word']
                    self.concordance[word].append({
                        'file': entry['file'],
                        'line': entry['line'],
                        'context': entry['context']
                    })

            except Exception as e:
                print(f"⚠️  Ошибка в файле {md_file}: {e}")

        print(f"   Обработано файлов: {total_files}")
        print(f"   Извлечено значимых слов: {total_words}")
        print(f"   Уникальных слов: {len(self.concordance)}")

    def save(self, output_file):
        """Сохранить конкорданс в JSON"""
        # Сортировать по алфавиту
        sorted_concordance = dict(sorted(self.concordance.items()))

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_concordance, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Конкорданс сохранён: {output_file}")

    def save_markdown(self, output_file):
        """Сохранить конкорданс в markdown формате"""
        lines = []
        lines.append("# Concordance - Алфавитный указатель слов\n")
        lines.append(f"> Создан автоматически из базы знаний\n")
        lines.append(f"> Всего уникальных слов: {len(self.concordance)}\n\n")

        # Группировать по первой букве
        current_letter = None

        for word in sorted(self.concordance.keys()):
            entries = self.concordance[word]

            # Новая буква - новый раздел
            first_letter = word[0].upper()
            if first_letter != current_letter:
                current_letter = first_letter
                lines.append(f"\n## {current_letter}\n\n")

            # Слово и количество упоминаний
            lines.append(f"### {word} ({len(entries)} упоминаний)\n\n")

            # Показать первые 5 упоминаний
            for entry in entries[:5]:
                lines.append(f"- **{entry['file']}:{entry['line']}**  \n")
                lines.append(f"  _{entry['context']}_\n\n")

            if len(entries) > 5:
                lines.append(f"  _...и ещё {len(entries) - 5} упоминаний_\n\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown версия: {output_file}")

    def search_word(self, word):
        """Поиск слова в конкордансе"""
        word_lower = word.lower()

        if word_lower not in self.concordance:
            print(f"❌ Слово '{word}' не найдено в конкордансе")
            return []

        entries = self.concordance[word_lower]
        print(f"\n📖 Слово '{word}' найдено в {len(entries)} местах:\n")

        for i, entry in enumerate(entries[:20], 1):
            print(f"{i}. {entry['file']}:{entry['line']}")
            print(f"   {entry['context']}\n")

        if len(entries) > 20:
            print(f"   ...и ещё {len(entries) - 20} упоминаний")

        return entries

    def get_top_words(self, n=50):
        """Получить топ N самых частых слов"""
        word_counts = [(word, len(entries))
                      for word, entries in self.concordance.items()]

        word_counts.sort(key=lambda x: x[1], reverse=True)

        print(f"\n📊 Топ-{n} самых частых слов:\n")

        for i, (word, count) in enumerate(word_counts[:n], 1):
            print(f"{i:3d}. {word:20s} - {count:4d} раз")

        return word_counts[:n]


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = ConcordanceBuilder(root_dir)

    # Построить конкорданс
    builder.build()

    # Сохранить
    output_dir = root_dir
    builder.save(output_dir / "concordance.json")
    builder.save_markdown(output_dir / "CONCORDANCE.md")

    # Показать топ слов
    builder.get_top_words(30)

    print("\n💡 Использование:")
    print("   python tools/search_concordance.py <слово>")


if __name__ == "__main__":
    main()
