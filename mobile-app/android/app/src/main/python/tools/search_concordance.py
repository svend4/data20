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
from collections import Counter, defaultdict
import math


class QueryParser:
    """Парсинг и оптимизация поисковых запросов"""

    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been'
        }

    def tokenize(self, query):
        """
        Токенизировать запрос

        Args:
            query: строка запроса

        Returns:
            list: токены
        """
        # Удалить спецсимволы, сохранить wildcards
        tokens = re.findall(r'\w+[\*\?]*|\*|\?', query.lower())
        return tokens

    def remove_stop_words(self, tokens):
        """
        Удалить stop words

        Args:
            tokens: список токенов

        Returns:
            list: токены без stop words
        """
        return [t for t in tokens if t not in self.stop_words]

    def apply_stemming(self, word):
        """
        Простой стемминг (удаление окончаний)

        Args:
            word: слово

        Returns:
            str: основа слова
        """
        # Простые правила для английского
        if word.endswith('ing'):
            return word[:-3]
        elif word.endswith('ed'):
            return word[:-2]
        elif word.endswith('s') and len(word) > 3:
            return word[:-1]
        elif word.endswith('ly'):
            return word[:-2]

        return word

    def expand_query(self, query, synonyms=None):
        """
        Расширить запрос синонимами

        Args:
            query: исходный запрос
            synonyms: словарь синонимов

        Returns:
            list: расширенные термины
        """
        if not synonyms:
            # Базовые синонимы для примера
            synonyms = {
                'docker': ['container', 'containerization'],
                'kubernetes': ['k8s', 'orchestration'],
                'python': ['py', 'python3'],
                'javascript': ['js', 'ecmascript'],
                'database': ['db', 'storage']
            }

        tokens = self.tokenize(query)
        expanded = set(tokens)

        for token in tokens:
            if token in synonyms:
                expanded.update(synonyms[token])

        return list(expanded)

    def parse_boolean_query(self, query):
        """
        Распарсить boolean запрос в AST

        Args:
            query: запрос с AND/OR/NOT

        Returns:
            dict: AST запроса
        """
        # Простой парсер для AND/OR/NOT
        query = query.strip()

        # Проверить на операторы
        if ' AND ' in query.upper():
            parts = re.split(r'\s+AND\s+', query, maxsplit=1, flags=re.IGNORECASE)
            return {
                'op': 'AND',
                'left': self.parse_boolean_query(parts[0]),
                'right': self.parse_boolean_query(parts[1])
            }
        elif ' OR ' in query.upper():
            parts = re.split(r'\s+OR\s+', query, maxsplit=1, flags=re.IGNORECASE)
            return {
                'op': 'OR',
                'left': self.parse_boolean_query(parts[0]),
                'right': self.parse_boolean_query(parts[1])
            }
        elif query.upper().startswith('NOT '):
            return {
                'op': 'NOT',
                'term': self.parse_boolean_query(query[4:])
            }
        else:
            return {
                'op': 'TERM',
                'value': query.strip().lower()
            }

    def optimize_query(self, query):
        """
        Оптимизировать запрос

        Args:
            query: исходный запрос

        Returns:
            str: оптимизированный запрос
        """
        # Токенизировать
        tokens = self.tokenize(query)

        # Удалить дубликаты
        tokens = list(dict.fromkeys(tokens))

        # Удалить stop words (если не boolean запрос)
        if not any(op in query.upper() for op in [' AND ', ' OR ', ' NOT ']):
            tokens = self.remove_stop_words(tokens)

        # Применить стемминг
        tokens = [self.apply_stemming(t) for t in tokens]

        return ' '.join(tokens)

    def suggest_corrections(self, query, concordance_words, max_suggestions=5):
        """
        Предложить исправления для опечаток

        Args:
            query: запрос
            concordance_words: список слов из конкорданса
            max_suggestions: максимум предложений

        Returns:
            list: предложенные исправления
        """
        from difflib import get_close_matches

        tokens = self.tokenize(query)
        suggestions = []

        for token in tokens:
            if token not in concordance_words:
                matches = get_close_matches(token, concordance_words, n=max_suggestions, cutoff=0.6)
                if matches:
                    suggestions.append({
                        'original': token,
                        'suggestions': matches
                    })

        return suggestions


class SearchRanker:
    """Ранжирование результатов поиска"""

    def __init__(self, concordance, all_articles=None):
        self.concordance = concordance
        self.all_articles = all_articles or []

        # Вычислить IDF
        self.idf_scores = self._calculate_idf()

    def _calculate_idf(self):
        """
        Вычислить IDF (Inverse Document Frequency) для всех терминов

        Returns:
            dict: IDF scores
        """
        if not self.concordance:
            return {}

        # Количество документов
        all_files = set()
        for entries in self.concordance.values():
            for entry in entries:
                all_files.add(entry['file'])

        total_docs = len(all_files)

        idf_scores = {}

        for word, entries in self.concordance.items():
            # Количество документов, содержащих слово
            docs_with_word = len(set(entry['file'] for entry in entries))

            # IDF = log(N / df)
            idf = math.log(total_docs / (1 + docs_with_word))
            idf_scores[word] = idf

        return idf_scores

    def calculate_tf_idf(self, word, file_path):
        """
        Вычислить TF-IDF для слова в документе

        Args:
            word: слово
            file_path: путь к файлу

        Returns:
            float: TF-IDF score
        """
        if word not in self.concordance:
            return 0.0

        # TF: частота слова в документе
        term_freq = sum(1 for entry in self.concordance[word] if entry['file'] == file_path)

        # IDF
        idf = self.idf_scores.get(word, 0.0)

        return term_freq * idf

    def calculate_bm25(self, query_terms, document, k1=1.5, b=0.75):
        """
        Вычислить BM25 score для документа

        BM25 - более продвинутая версия TF-IDF.

        Args:
            query_terms: термины запроса
            document: путь к документу
            k1: параметр насыщения TF
            b: параметр нормализации длины

        Returns:
            float: BM25 score
        """
        # Средняя длина документа (упрощённо)
        avg_doc_length = 1000  # Предполагаем среднюю длину

        # Длина текущего документа (по количеству слов)
        doc_length = sum(
            len(entries)
            for entries in self.concordance.values()
            if any(e['file'] == document for e in entries)
        )

        score = 0.0

        for term in query_terms:
            if term not in self.concordance:
                continue

            # TF для термина в документе
            tf = sum(1 for entry in self.concordance[term] if entry['file'] == document)

            # IDF
            idf = self.idf_scores.get(term, 0.0)

            # BM25 формула
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))

            score += idf * (numerator / denominator)

        return score

    def rank_results(self, results, query_terms, method='tfidf'):
        """
        Ранжировать результаты поиска

        Args:
            results: результаты поиска
            query_terms: термины запроса
            method: метод ранжирования (tfidf, bm25, frequency)

        Returns:
            list: ранжированные результаты
        """
        scored_results = []

        for word, entry in results:
            if method == 'tfidf':
                score = self.calculate_tf_idf(word, entry['file'])
            elif method == 'bm25':
                score = self.calculate_bm25(query_terms, entry['file'])
            elif method == 'frequency':
                # Простая частота
                score = sum(1 for e in self.concordance.get(word, []) if e['file'] == entry['file'])
            else:
                score = 0.0

            scored_results.append((score, word, entry))

        # Сортировать по score (descending)
        scored_results.sort(key=lambda x: -x[0])

        # Вернуть без score
        return [(word, entry) for score, word, entry in scored_results]


class SearchIndexer:
    """Индексация для ускорения поиска"""

    def __init__(self):
        self.inverted_index = defaultdict(set)
        self.ngram_index = defaultdict(set)
        self.word_positions = defaultdict(list)

    def build_inverted_index(self, concordance):
        """
        Построить инвертированный индекс

        Args:
            concordance: конкорданс

        Returns:
            dict: инвертированный индекс
        """
        self.inverted_index = defaultdict(set)

        for word, entries in concordance.items():
            for entry in entries:
                self.inverted_index[word].add(entry['file'])

        return dict(self.inverted_index)

    def build_ngram_index(self, concordance, n=3):
        """
        Построить n-gram индекс для быстрого fuzzy search

        Args:
            concordance: конкорданс
            n: размер n-gram

        Returns:
            dict: n-gram индекс
        """
        self.ngram_index = defaultdict(set)

        for word in concordance.keys():
            # Генерировать n-grams
            ngrams = self._generate_ngrams(word, n)

            for ngram in ngrams:
                self.ngram_index[ngram].add(word)

        return dict(self.ngram_index)

    def _generate_ngrams(self, word, n):
        """
        Генерировать n-grams для слова

        Args:
            word: слово
            n: размер n-gram

        Returns:
            list: n-grams
        """
        word = f'${word}$'  # Добавить маркеры начала/конца
        ngrams = []

        for i in range(len(word) - n + 1):
            ngrams.append(word[i:i+n])

        return ngrams

    def fuzzy_search_with_ngrams(self, query, min_similarity=0.5):
        """
        Fuzzy search используя n-gram индекс

        Args:
            query: запрос
            min_similarity: минимальная похожесть

        Returns:
            list: похожие слова
        """
        if not self.ngram_index:
            return []

        query_ngrams = set(self._generate_ngrams(query, 3))

        candidates = defaultdict(int)

        # Найти кандидатов по n-grams
        for ngram in query_ngrams:
            if ngram in self.ngram_index:
                for word in self.ngram_index[ngram]:
                    candidates[word] += 1

        # Вычислить Jaccard similarity
        results = []

        for word, ngram_matches in candidates.items():
            word_ngrams = set(self._generate_ngrams(word, 3))
            similarity = len(query_ngrams & word_ngrams) / len(query_ngrams | word_ngrams)

            if similarity >= min_similarity:
                results.append((word, similarity))

        # Сортировать по similarity
        results.sort(key=lambda x: -x[1])

        return results

    def build_position_index(self, concordance):
        """
        Построить позиционный индекс для phrase search

        Args:
            concordance: конкорданс

        Returns:
            dict: позиционный индекс
        """
        self.word_positions = defaultdict(list)

        for word, entries in concordance.items():
            for entry in entries:
                self.word_positions[word].append({
                    'file': entry['file'],
                    'line': entry['line'],
                    'context': entry['context']
                })

        return dict(self.word_positions)

    def phrase_search(self, phrase):
        """
        Поиск фразы (последовательность слов)

        Args:
            phrase: фраза для поиска

        Returns:
            list: результаты
        """
        words = phrase.lower().split()

        if not words:
            return []

        # Найти документы, содержащие все слова
        if words[0] not in self.word_positions:
            return []

        results = []

        # Для каждой позиции первого слова
        for pos in self.word_positions[words[0]]:
            context = pos['context'].lower()

            # Проверить, содержит ли context всю фразу
            if phrase.lower() in context:
                results.append(pos)

        return results


class SearchVisualizer:
    """Визуализация результатов поиска"""

    def __init__(self, results, query):
        self.results = results
        self.query = query

    def generate_html_results(self):
        """
        Создать HTML визуализацию результатов

        Returns:
            str: HTML контент
        """
        # Подготовить данные
        total_results = len(self.results)

        # Группировать по файлам
        by_file = defaultdict(list)
        for word, entry in self.results:
            by_file[entry['file']].append((word, entry))

        # Топ файлов
        top_files = sorted(by_file.items(), key=lambda x: -len(x[1]))[:10]

        # Частота слов
        word_freq = Counter(word for word, _ in self.results)
        top_words = word_freq.most_common(10)

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Search Results: {self.query}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .query-box {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            text-align: center;
        }}

        .query {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #666;
            margin-top: 10px;
        }}

        .results-section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}

        .section-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }}

        .result-item {{
            padding: 15px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-radius: 5px;
        }}

        .file-path {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .context {{
            color: #333;
            line-height: 1.6;
        }}

        .highlight {{
            background: yellow;
            font-weight: bold;
            padding: 2px 4px;
        }}

        .word-cloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}

        .word-tag {{
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: calc(12px + var(--size) * 8px);
        }}

        .file-list {{
            list-style: none;
        }}

        .file-list li {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }}

        .file-list li:last-child {{
            border-bottom: none;
        }}

        .badge {{
            background: #764ba2;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Search Results</h1>

        <div class="query-box">
            <div class="query">"{self.query}"</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_results}</div>
                <div class="stat-label">Результатов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(by_file)}</div>
                <div class="stat-label">Файлов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(word_freq)}</div>
                <div class="stat-label">Уникальных слов</div>
            </div>
        </div>

        <div class="results-section">
            <div class="section-title">☁️ Частые слова</div>
            <div class="word-cloud">
                {"".join(f'<span class="word-tag" style="--size: {min(count/max(word_freq.values()), 1)}">{word} ({count})</span>' for word, count in top_words)}
            </div>
        </div>

        <div class="results-section">
            <div class="section-title">📁 Топ файлов</div>
            <ul class="file-list">
                {"".join(f'<li><span>{file_path}</span><span class="badge">{len(items)} совпадений</span></li>' for file_path, items in top_files)}
            </ul>
        </div>

        <div class="results-section">
            <div class="section-title">📋 Результаты (первые 20)</div>
            {"".join(f'''
            <div class="result-item">
                <div class="file-path">{entry['file']}:{entry['line']}</div>
                <div class="context">{entry['context'].replace(word, f'<span class="highlight">{word}</span>')}</div>
            </div>
            ''' for word, entry in self.results[:20])}
        </div>
    </div>
</body>
</html>"""

        return html

    def generate_word_cloud_data(self):
        """
        Создать данные для word cloud

        Returns:
            dict: данные для word cloud
        """
        word_freq = Counter(word for word, _ in self.results)

        return {
            'words': [
                {'text': word, 'size': count}
                for word, count in word_freq.most_common(50)
            ]
        }

    def export_to_markdown(self):
        """
        Экспорт результатов в Markdown

        Returns:
            str: Markdown контент
        """
        lines = []

        lines.append(f"# 🔍 Search Results: {self.query}\n\n")
        lines.append(f"**Total Results:** {len(self.results)}\n\n")

        # Группировать по файлам
        by_file = defaultdict(list)
        for word, entry in self.results:
            by_file[entry['file']].append((word, entry))

        lines.append("## 📁 By Files\n\n")

        for file_path, items in sorted(by_file.items(), key=lambda x: -len(x[1]))[:20]:
            lines.append(f"### {file_path} ({len(items)} matches)\n\n")

            for word, entry in items[:5]:
                lines.append(f"- **Line {entry['line']}**: {entry['context']}\n")

            if len(items) > 5:
                lines.append(f"\n_...and {len(items) - 5} more matches_\n")

            lines.append("\n")

        return ''.join(lines)


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

    parser = argparse.ArgumentParser(
        description='🔍 Advanced Concordance Search - Продвинутый поиск в конкордансе',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s docker                        # Точный поиск
  %(prog)s 'docker*' -m wildcard         # Wildcard search
  %(prog)s 'doc.*' -m regex              # Regex search
  %(prog)s 'docker AND python' -m boolean # Boolean search
  %(prog)s холодильник -m fuzzy          # Fuzzy search
  %(prog)s docker -d kwic                # KWIC display
  %(prog)s docker --html                 # HTML visualization
  %(prog)s docker --rank bm25            # Ranked results with BM25
  %(prog)s docker --optimize             # Optimize query
  %(prog)s docker --expand               # Expand with synonyms
  %(prog)s "docker container" --phrase   # Phrase search
  %(prog)s docker --suggest              # Suggest corrections
  %(prog)s docker --all                  # All features

Новые возможности:
  • Query Optimization: stemming, stop words removal
  • Query Expansion: synonym expansion
  • Advanced Ranking: TF-IDF, BM25
  • Fast Indexing: inverted index, n-gram index
  • HTML Visualization: word clouds, interactive results
        """
    )

    # Основные параметры
    parser.add_argument('query', nargs='?', help='Слово или запрос для поиска')
    parser.add_argument('-m', '--mode', choices=['exact', 'fuzzy', 'regex', 'wildcard', 'boolean'],
                       default='exact', help='Режим поиска')
    parser.add_argument('-d', '--display', choices=['list', 'kwic'], default='list',
                       help='Формат отображения')
    parser.add_argument('-n', '--max-results', type=int, default=50,
                       help='Максимум результатов (по умолчанию: 50)')

    # Новые анализы
    parser.add_argument('--html', action='store_true',
                       help='🎨 Создать HTML визуализацию результатов')
    parser.add_argument('--rank', choices=['tfidf', 'bm25', 'frequency'],
                       help='📊 Метод ранжирования результатов')
    parser.add_argument('--optimize', action='store_true',
                       help='⚡ Оптимизировать запрос (stemming, stop words)')
    parser.add_argument('--expand', action='store_true',
                       help='🔄 Расширить запрос синонимами')
    parser.add_argument('--phrase', action='store_true',
                       help='🔍 Phrase search (поиск фразы)')
    parser.add_argument('--suggest', action='store_true',
                       help='💡 Предложить исправления опечаток')
    parser.add_argument('--build-index', action='store_true',
                       help='🏗️ Построить индексы для ускорения поиска')
    parser.add_argument('--ngram-fuzzy', action='store_true',
                       help='🎯 Fuzzy search с n-gram индексом (быстрее)')

    # Экспорт
    parser.add_argument('-e', '--export', choices=['txt', 'json', 'csv', 'md'],
                       help='💾 Формат экспорта')
    parser.add_argument('-o', '--output', help='📁 Файл для экспорта')

    # Специальные
    parser.add_argument('--all', action='store_true',
                       help='🎯 Запустить все доступные анализы')

    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        return

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    concordance_file = root_dir / "concordance.json"

    # Загрузить searcher
    searcher = AdvancedConcordanceSearch(concordance_file)

    if not searcher.concordance:
        return

    print(f"🔍 Поиск: '{args.query}'")
    print(f"📚 Конкорданс: {len(searcher.concordance)} уникальных слов\n")

    # --all активирует все функции
    if args.all:
        args.optimize = True
        args.expand = True
        args.html = True
        args.rank = 'bm25'
        args.suggest = True
        args.build_index = True

    # Query Parser
    query_parser = QueryParser()

    # Optimize query
    original_query = args.query
    if args.optimize:
        optimized = query_parser.optimize_query(args.query)
        print(f"⚡ Оптимизированный запрос: '{optimized}'")
        args.query = optimized

    # Expand query
    expanded_terms = []
    if args.expand:
        expanded_terms = query_parser.expand_query(args.query)
        print(f"🔄 Расширенный запрос: {', '.join(expanded_terms)}")

    # Suggest corrections
    if args.suggest:
        suggestions = query_parser.suggest_corrections(args.query, list(searcher.concordance.keys()))
        if suggestions:
            print("\n💡 Предложения по исправлению:")
            for sug in suggestions:
                print(f"   '{sug['original']}' → {', '.join(sug['suggestions'][:3])}")
        print()

    # Build indexes
    indexer = None
    if args.build_index or args.ngram_fuzzy:
        print("🏗️ Построение индексов...")
        indexer = SearchIndexer()
        indexer.build_inverted_index(searcher.concordance)
        indexer.build_ngram_index(searcher.concordance)
        indexer.build_position_index(searcher.concordance)
        print("✅ Индексы построены\n")

    # Phrase search
    if args.phrase and indexer:
        print(f"🔍 Phrase search: '{original_query}'")
        results_list = indexer.phrase_search(original_query)

        if results_list:
            print(f"✅ Найдено: {len(results_list)} совпадений\n")
            for i, result in enumerate(results_list[:args.max_results], 1):
                print(f"{i}. {result['file']}:{result['line']}")
                print(f"   {result['context']}\n")
        else:
            print("❌ Фраза не найдена\n")

        return

    # N-gram fuzzy search
    if args.ngram_fuzzy and indexer:
        print(f"🎯 N-gram fuzzy search: '{args.query}'")
        similar_words = indexer.fuzzy_search_with_ngrams(args.query)

        if similar_words:
            print(f"✅ Найдено похожих слов: {len(similar_words)}\n")
            results = []
            for word, similarity in similar_words[:20]:
                print(f"   {word} (similarity: {similarity:.2f})")
                if word in searcher.concordance:
                    for entry in searcher.concordance[word]:
                        results.append((word, entry))

            print(f"\n📊 Всего результатов: {len(results)}\n")
        else:
            print("❌ Похожие слова не найдены\n")

        return

    # Выполнить поиск
    if args.mode == 'fuzzy':
        matches = searcher.fuzzy_search(args.query)
        results = []
        for word, distance in matches:
            for entry in searcher.concordance[word]:
                results.append((word, entry))
                if len(results) >= args.max_results * 2:  # Получить больше для ранжирования
                    break

    elif args.mode == 'regex':
        matches = searcher.regex_search(args.query)
        results = []
        for word, entries in matches:
            for entry in entries:
                results.append((word, entry))

    elif args.mode == 'wildcard':
        matches = searcher.wildcard_search(args.query)
        results = []
        for word, entries in matches:
            for entry in entries:
                results.append((word, entry))

    elif args.mode == 'boolean':
        results = searcher.boolean_search(args.query)

    else:  # exact
        results = searcher.exact_search(args.query)

        # Попробовать расширенные термины
        if args.expand and not results:
            for term in expanded_terms:
                term_results = searcher.exact_search(term)
                results.extend(term_results)

    if not results:
        print(f"❌ Ничего не найдено для '{args.query}'")

        # Fuzzy matches как fallback
        fuzzy_matches = searcher.fuzzy_search(args.query, max_distance=2)
        if fuzzy_matches:
            print(f"\n💡 Похожие слова:")
            for word, distance in fuzzy_matches[:10]:
                print(f"   {word} (distance: {distance})")

        return

    print(f"📖 Найдено: {len(results)} совпадений\n")

    # Ranking
    if args.rank:
        print(f"📊 Ранжирование методом: {args.rank.upper()}")
        ranker = SearchRanker(searcher.concordance)
        query_terms = query_parser.tokenize(args.query)
        results = ranker.rank_results(results, query_terms, method=args.rank)
        print("✅ Результаты ранжированы\n")

    # HTML visualization
    if args.html:
        print("🎨 Генерация HTML визуализации...")
        visualizer = SearchVisualizer(results, original_query)
        html_content = visualizer.generate_html_results()

        html_file = root_dir / f"search_results_{original_query.replace(' ', '_')}.html"
        html_file.write_text(html_content, encoding='utf-8')
        print(f"✅ HTML: {html_file}\n")

    # Display results
    if args.display == 'kwic':
        searcher.kwic_display(results)
    else:
        for i, (word, entry) in enumerate(results[:args.max_results], 1):
            print(f"{i}. {entry['file']}:{entry['line']}")
            highlighted = searcher.highlight_context(entry['context'], word)
            print(f"   {highlighted}\n")

        if len(results) > args.max_results:
            print(f"   ...и ещё {len(results) - args.max_results} совпадений")

    # Statistics
    searcher.generate_statistics(results)

    # Export
    if args.export:
        if args.export == 'md':
            # Markdown export через visualizer
            visualizer = SearchVisualizer(results, original_query)
            md_content = visualizer.export_to_markdown()

            if args.output:
                Path(args.output).write_text(md_content, encoding='utf-8')
                print(f"\n✅ Markdown экспорт: {args.output}")
            else:
                print("\n" + md_content)
        else:
            export_config = {
                'format': args.export,
                'file': args.output
            }
            searcher.export_results(results, output_format=args.export, output_file=args.output)


if __name__ == "__main__":
    main()
