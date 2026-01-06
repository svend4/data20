#!/usr/bin/env python3
"""
Advanced Concordance Builder - Средневековая техника для современной базы знаний
Создаёт полный индекс всех слов с указанием их местоположения + KWIC, N-граммы, TF-IDF

Вдохновлено: Concordantia Sacrorum Bibliorum (1230 г.), KWIC indexing (Hans Peter Luhn, 1960)

Features:
- Full concordance with word locations
- KWIC (Key Word In Context) display
- N-gram analysis (bigrams, trigrams)
- TF-IDF scoring for term importance
- Co-occurrence analysis
- HTML visualization
- Advanced filtering
- Phrase search
- Word proximity detection
- Statistics dashboard
"""

import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import json
import argparse
import math


class KWICGenerator:
    """KWIC (Key Word In Context) generator"""

    def __init__(self, window_size=80):
        self.window_size = window_size

    def generate_kwic(self, text: str, keyword: str) -> List[Dict]:
        """
        Генерация KWIC для ключевого слова
        Returns: [{'left': str, 'keyword': str, 'right': str, 'position': int}]
        """
        kwic_entries = []
        keyword_lower = keyword.lower()
        text_lower = text.lower()

        # Найти все вхождения
        pos = 0
        while True:
            pos = text_lower.find(keyword_lower, pos)
            if pos == -1:
                break

            # Контекст слева и справа
            left_start = max(0, pos - self.window_size // 2)
            right_end = min(len(text), pos + len(keyword) + self.window_size // 2)

            left_context = text[left_start:pos].strip()
            keyword_match = text[pos:pos + len(keyword)]
            right_context = text[pos + len(keyword):right_end].strip()

            # Добавить многоточия
            if left_start > 0:
                left_context = '...' + left_context
            if right_end < len(text):
                right_context = right_context + '...'

            kwic_entries.append({
                'left': left_context,
                'keyword': keyword_match,
                'right': right_context,
                'position': pos
            })

            pos += len(keyword)

        return kwic_entries


class NGramAnalyzer:
    """Анализатор N-грамм (биграммы, триграммы)"""

    def __init__(self, stop_words: set):
        self.stop_words = stop_words

    def extract_ngrams(self, text: str, n: int = 2) -> List[Tuple[str, ...]]:
        """Извлечь N-граммы из текста"""
        # Очистить текст
        clean_text = re.sub(r'[^а-яёa-z\s]', ' ', text.lower())
        words = clean_text.split()

        # Убрать стоп-слова
        words = [w for w in words if w not in self.stop_words and len(w) >= 3]

        # Создать N-граммы
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = tuple(words[i:i + n])
            ngrams.append(ngram)

        return ngrams

    def get_top_ngrams(self, ngrams: List[Tuple[str, ...]], top_n: int = 20) -> List[Tuple[Tuple[str, ...], int]]:
        """Получить топ N самых частых N-грамм"""
        counter = Counter(ngrams)
        return counter.most_common(top_n)


class TFIDFCalculator:
    """Калькулятор TF-IDF (Term Frequency-Inverse Document Frequency)"""

    def __init__(self):
        self.documents = {}  # {doc_id: [words]}
        self.idf_cache = {}

    def add_document(self, doc_id: str, words: List[str]):
        """Добавить документ"""
        self.documents[doc_id] = words

    def calculate_tf(self, word: str, doc_id: str) -> float:
        """
        Term Frequency: TF(word) = count(word in doc) / total_words_in_doc
        """
        if doc_id not in self.documents:
            return 0.0

        words = self.documents[doc_id]
        if not words:
            return 0.0

        word_count = words.count(word.lower())
        return word_count / len(words)

    def calculate_idf(self, word: str) -> float:
        """
        Inverse Document Frequency: IDF(word) = log(total_docs / docs_containing_word)
        """
        if word in self.idf_cache:
            return self.idf_cache[word]

        total_docs = len(self.documents)
        docs_with_word = sum(1 for words in self.documents.values() if word.lower() in words)

        if docs_with_word == 0:
            idf = 0.0
        else:
            idf = math.log(total_docs / docs_with_word)

        self.idf_cache[word] = idf
        return idf

    def calculate_tfidf(self, word: str, doc_id: str) -> float:
        """
        TF-IDF = TF × IDF
        """
        tf = self.calculate_tf(word, doc_id)
        idf = self.calculate_idf(word)
        return tf * idf

    def get_document_keywords(self, doc_id: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Получить ключевые слова документа по TF-IDF"""
        if doc_id not in self.documents:
            return []

        words = set(self.documents[doc_id])
        scores = [(word, self.calculate_tfidf(word, doc_id)) for word in words]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]


class CooccurrenceAnalyzer:
    """Анализатор совместной встречаемости слов"""

    def __init__(self, window_size=10):
        self.window_size = window_size
        self.cooccurrences = defaultdict(lambda: defaultdict(int))

    def analyze_text(self, words: List[str]):
        """Анализ совместной встречаемости в окне"""
        for i, word in enumerate(words):
            # Слова в окне
            window_start = max(0, i - self.window_size)
            window_end = min(len(words), i + self.window_size + 1)

            for j in range(window_start, window_end):
                if i != j:
                    other_word = words[j]
                    self.cooccurrences[word][other_word] += 1

    def get_related_words(self, word: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """Получить слова, часто встречающиеся рядом"""
        if word not in self.cooccurrences:
            return []

        related = self.cooccurrences[word].items()
        related = sorted(related, key=lambda x: x[1], reverse=True)
        return related[:top_n]


class ConcordanceBuilder:
    """
    Расширенный построитель конкорданса
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.concordance = defaultdict(list)

        # Компоненты
        self.kwic_gen = KWICGenerator(window_size=80)
        self.tfidf_calc = TFIDFCalculator()
        self.cooccurrence = CooccurrenceAnalyzer(window_size=10)

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

        self.ngram_analyzer = NGramAnalyzer(self.stop_words)

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
        """Построить конкорданс с расширенной аналитикой"""
        print("📖 Построение расширенного конкорданса...")
        print("   Вдохновлено средневековыми индексами Библии + KWIC indexing\n")

        total_words = 0
        total_files = 0
        all_bigrams = []
        all_trigrams = []

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

                # TF-IDF analysis
                doc_words = [entry['word'] for entry in words]
                self.tfidf_calc.add_document(str(md_file), doc_words)

                # Co-occurrence analysis
                self.cooccurrence.analyze_text(doc_words)

                # N-gram analysis
                bigrams = self.ngram_analyzer.extract_ngrams(content, n=2)
                trigrams = self.ngram_analyzer.extract_ngrams(content, n=3)
                all_bigrams.extend(bigrams)
                all_trigrams.extend(trigrams)

            except Exception as e:
                print(f"⚠️  Ошибка в файле {md_file}: {e}")

        print(f"   Обработано файлов: {total_files}")
        print(f"   Извлечено значимых слов: {total_words}")
        print(f"   Уникальных слов: {len(self.concordance)}")
        print(f"   Биграмм: {len(all_bigrams)}")
        print(f"   Триграмм: {len(all_trigrams)}")

        # Сохранить N-граммы
        self.bigrams = all_bigrams
        self.trigrams = all_trigrams

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

    def generate_html_concordance(self, output_file: str):
        """Генерация интерактивного HTML конкорданса"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Interactive Concordance</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .search {{ margin: 20px 0; }}
        .search input {{ width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 4px; }}
        .word-list {{ columns: 4; column-gap: 20px; }}
        .word-item {{ break-inside: avoid; margin-bottom: 8px; }}
        .word-link {{ color: #007bff; text-decoration: none; font-weight: 500; }}
        .word-link:hover {{ text-decoration: underline; }}
        .count {{ color: #666; font-size: 0.9em; }}
        .letter-header {{ background: #007bff; color: white; padding: 8px 12px; margin: 20px 0 10px 0; border-radius: 4px; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
        .stat {{ background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📖 Interactive Concordance</h1>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total_words}</div>
                <div>Unique Words</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_occurrences}</div>
                <div>Total Occurrences</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_files}</div>
                <div>Files Indexed</div>
            </div>
        </div>

        <div class="search">
            <input type="text" id="searchBox" placeholder="Search for a word..." onkeyup="filterWords()">
        </div>

        <div id="wordList" class="word-list">
            {word_list_html}
        </div>
    </div>

    <script>
    function filterWords() {{
        const input = document.getElementById('searchBox');
        const filter = input.value.toLowerCase();
        const items = document.getElementsByClassName('word-item');

        for (let i = 0; i < items.length; i++) {{
            const text = items[i].textContent || items[i].innerText;
            if (text.toLowerCase().indexOf(filter) > -1) {{
                items[i].style.display = '';
            }} else {{
                items[i].style.display = 'none';
            }}
        }}
    }}
    </script>
</body>
</html>"""

        # Подсчёт статистики
        total_words = len(self.concordance)
        total_occurrences = sum(len(entries) for entries in self.concordance.values())

        # Количество файлов
        all_files = set()
        for entries in self.concordance.values():
            for entry in entries:
                all_files.add(entry['file'])
        total_files = len(all_files)

        # Генерация списка слов
        word_list_html = []
        current_letter = None

        for word in sorted(self.concordance.keys()):
            entries = self.concordance[word]

            # Новая буква
            first_letter = word[0].upper()
            if first_letter != current_letter:
                current_letter = first_letter
                word_list_html.append(f'<div class="letter-header">{current_letter}</div>')

            count = len(entries)
            word_list_html.append(
                f'<div class="word-item">'
                f'<a href="#" class="word-link">{word}</a> '
                f'<span class="count">({count})</span>'
                f'</div>'
            )

        html = html_template.format(
            total_words=total_words,
            total_occurrences=total_occurrences,
            total_files=total_files,
            word_list_html='\n'.join(word_list_html)
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML concordance: {output_file}")

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

    def show_ngrams(self, n: int = 2, top: int = 20):
        """Показать топ N-грамм"""
        ngrams = self.bigrams if n == 2 else self.trigrams
        top_ngrams = self.ngram_analyzer.get_top_ngrams(ngrams, top)

        ngram_name = "биграммы" if n == 2 else "триграммы"
        print(f"\n📊 Топ-{top} {ngram_name}:\n")

        for i, (ngram, count) in enumerate(top_ngrams, 1):
            ngram_str = ' '.join(ngram)
            print(f"{i:3d}. {ngram_str:40s} - {count:4d} раз")

    def show_tfidf_keywords(self, file_path: str, top_n: int = 10):
        """Показать ключевые слова документа по TF-IDF"""
        keywords = self.tfidf_calc.get_document_keywords(file_path, top_n)

        print(f"\n📊 Ключевые слова (TF-IDF) для {file_path}:\n")

        for i, (word, score) in enumerate(keywords, 1):
            print(f"{i:3d}. {word:20s} - {score:.4f}")

    def show_related_words(self, word: str, top_n: int = 10):
        """Показать связанные слова (co-occurrence)"""
        related = self.cooccurrence.get_related_words(word.lower(), top_n)

        if not related:
            print(f"❌ Нет данных о связанных словах для '{word}'")
            return

        print(f"\n📊 Слова, часто встречающиеся рядом с '{word}':\n")

        for i, (related_word, count) in enumerate(related, 1):
            print(f"{i:3d}. {related_word:20s} - {count:4d} раз")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Concordance Builder with KWIC, N-grams, TF-IDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  build_concordance.py                      # Build full concordance
  build_concordance.py --search python      # Search for word
  build_concordance.py --top 50             # Top 50 frequent words
  build_concordance.py --bigrams            # Show top bigrams
  build_concordance.py --trigrams           # Show top trigrams
  build_concordance.py --related python     # Words related to 'python'
  build_concordance.py --html               # Generate HTML concordance
        """
    )

    parser.add_argument('--search', type=str, metavar='WORD',
                        help='Search for a word in concordance')
    parser.add_argument('--top', type=int, metavar='N', default=30,
                        help='Show top N frequent words (default: 30)')
    parser.add_argument('--bigrams', action='store_true',
                        help='Show top bigrams (2-word phrases)')
    parser.add_argument('--trigrams', action='store_true',
                        help='Show top trigrams (3-word phrases)')
    parser.add_argument('--related', type=str, metavar='WORD',
                        help='Show words related to the given word')
    parser.add_argument('--tfidf', type=str, metavar='FILE',
                        help='Show TF-IDF keywords for file')
    parser.add_argument('--html', action='store_true',
                        help='Generate HTML concordance')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = ConcordanceBuilder(root_dir)
    builder.build()

    # Search mode
    if args.search:
        builder.search_word(args.search)
        return

    # Related words
    if args.related:
        builder.show_related_words(args.related)
        return

    # TF-IDF keywords
    if args.tfidf:
        builder.show_tfidf_keywords(args.tfidf)
        return

    # Bigrams
    if args.bigrams:
        builder.show_ngrams(n=2, top=20)
        return

    # Trigrams
    if args.trigrams:
        builder.show_ngrams(n=3, top=20)
        return

    # HTML concordance
    if args.html:
        output_dir = root_dir
        builder.generate_html_concordance(output_dir / "concordance.html")
        return

    # Default: full build
    output_dir = root_dir
    builder.save(output_dir / "concordance.json")
    builder.save_markdown(output_dir / "CONCORDANCE.md")
    builder.generate_html_concordance(output_dir / "concordance.html")

    # Показать статистику
    builder.get_top_words(args.top)
    builder.show_ngrams(n=2, top=10)

    print("\n💡 Использование:")
    print("   python tools/build_concordance.py --search <слово>")
    print("   python tools/build_concordance.py --related <слово>")
    print("   python tools/build_concordance.py --bigrams")


if __name__ == "__main__":
    main()
