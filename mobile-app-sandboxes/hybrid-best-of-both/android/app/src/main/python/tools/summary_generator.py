#!/usr/bin/env python3
"""
Summary Generator - Продвинутый генератор резюме
Использует множество алгоритмов для создания качественных резюме

Вдохновлено: TextRank, LexRank, LSA
Методы: TF-IDF, позиционные веса, кластеризация предложений
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import math
import argparse
from typing import Dict, List, Tuple, Set
import hashlib


class SentenceImportanceAnalyzer:
    """
    Анализатор важности предложений
    Использует множество признаков для определения важности
    """

    def __init__(self, stop_words: Set[str]):
        self.stop_words = stop_words

    def analyze_sentence_features(self, sentence: str, position: int, total_sentences: int) -> Dict[str, float]:
        """
        Анализ признаков предложения

        Признаки:
        - Длина предложения
        - Позиция в тексте
        - Наличие числовых данных
        - Наличие ключевых слов (важных понятий)
        - Наличие именованных сущностей (заглавные буквы)
        """
        words = sentence.split()

        # Длина предложения (нормализованная)
        length_score = len(words) / 50.0  # средняя длина ~25 слов
        length_score = min(1.0, length_score)

        # Позиция (первые и последние важнее)
        if position < 3:
            position_score = 1.0
        elif position >= total_sentences - 2:
            position_score = 0.8
        else:
            position_score = 0.5

        # Числовые данные (цифры, проценты, даты)
        has_numbers = bool(re.search(r'\d+', sentence))
        numbers_score = 0.7 if has_numbers else 0.0

        # Именованные сущности (заглавные буквы)
        capitalized = re.findall(r'\b[A-ZА-ЯЁ][a-zа-яё]+\b', sentence)
        entities_score = min(1.0, len(capitalized) / 3.0)

        # Ключевые маркеры
        key_markers = ['важно', 'главное', 'основной', 'ключевой', 'необходимо', 'следует',
                      'важный', 'главный', 'central', 'important', 'key', 'essential', 'main']
        has_markers = any(marker in sentence.lower() for marker in key_markers)
        markers_score = 0.8 if has_markers else 0.0

        # Цитаты и кавычки
        has_quotes = bool(re.search(r'[«»""]', sentence))
        quotes_score = 0.6 if has_quotes else 0.0

        return {
            'length': length_score,
            'position': position_score,
            'numbers': numbers_score,
            'entities': entities_score,
            'markers': markers_score,
            'quotes': quotes_score
        }

    def calculate_importance_score(self, features: Dict[str, float], weights: Dict[str, float] = None) -> float:
        """
        Вычислить общую оценку важности на основе признаков

        По умолчанию веса:
        - position: 0.25
        - entities: 0.20
        - markers: 0.20
        - length: 0.15
        - numbers: 0.10
        - quotes: 0.10
        """
        if weights is None:
            weights = {
                'position': 0.25,
                'entities': 0.20,
                'markers': 0.20,
                'length': 0.15,
                'numbers': 0.10,
                'quotes': 0.10
            }

        score = sum(features.get(key, 0) * weight for key, weight in weights.items())
        return score


class SummaryDiversityScorer:
    """
    Оценка разнообразия резюме
    Проверяет, насколько хорошо резюме покрывает разные части текста
    """

    def __init__(self):
        pass

    def calculate_diversity_metrics(self, selected_sentences: List[str], all_sentences: List[str]) -> Dict[str, any]:
        """
        Метрики разнообразия резюме
        """
        if not selected_sentences or not all_sentences:
            return {'diversity_score': 0, 'coverage': 0}

        # Позиционное разнообразие (покрытие разных частей текста)
        positions = []
        for sel_sent in selected_sentences:
            if sel_sent in all_sentences:
                positions.append(all_sentences.index(sel_sent))

        if not positions:
            return {'diversity_score': 0, 'coverage': 0}

        # Расстояние между выбранными предложениями
        positions_sorted = sorted(positions)
        distances = []
        for i in range(len(positions_sorted) - 1):
            distances.append(positions_sorted[i + 1] - positions_sorted[i])

        # Равномерность распределения
        if distances:
            avg_distance = sum(distances) / len(distances)
            # Идеальное расстояние для равномерного распределения
            ideal_distance = len(all_sentences) / len(selected_sentences)
            uniformity = 1.0 - abs(avg_distance - ideal_distance) / ideal_distance
            uniformity = max(0, min(1, uniformity))
        else:
            uniformity = 1.0

        # Покрытие диапазона (от начала до конца)
        range_coverage = (max(positions) - min(positions)) / len(all_sentences) if len(all_sentences) > 1 else 0

        # Лексическое разнообразие (уникальные слова)
        all_words = []
        for sent in selected_sentences:
            words = re.findall(r'\b[а-яёa-z]+\b', sent.lower())
            all_words.extend(words)

        lexical_diversity = len(set(all_words)) / len(all_words) if all_words else 0

        # Общая оценка разнообразия
        diversity_score = (uniformity * 0.4 + range_coverage * 0.3 + lexical_diversity * 0.3)

        return {
            'diversity_score': round(diversity_score, 3),
            'uniformity': round(uniformity, 3),
            'range_coverage': round(range_coverage, 3),
            'lexical_diversity': round(lexical_diversity, 3),
            'positions': positions
        }

    def calculate_redundancy(self, sentences: List[str]) -> float:
        """
        Вычислить избыточность (повторяемость) в резюме

        Низкая избыточность = хорошо
        """
        if len(sentences) < 2:
            return 0.0

        # Сравнить все пары предложений
        total_similarity = 0.0
        pairs = 0

        for i in range(len(sentences)):
            words_i = set(re.findall(r'\b[а-яёa-z]+\b', sentences[i].lower()))

            for j in range(i + 1, len(sentences)):
                words_j = set(re.findall(r'\b[а-яёa-z]+\b', sentences[j].lower()))

                if words_i and words_j:
                    intersection = len(words_i & words_j)
                    union = len(words_i | words_j)
                    similarity = intersection / union if union > 0 else 0
                    total_similarity += similarity
                    pairs += 1

        avg_similarity = total_similarity / pairs if pairs > 0 else 0
        return round(avg_similarity, 3)


class TopicModelingSummarizer:
    """
    Резюмирование на основе тематического моделирования
    Использует упрощенный подход к выделению тем
    """

    def __init__(self, stop_words: Set[str]):
        self.stop_words = stop_words

    def extract_topics(self, sentences: List[str], num_topics: int = 3) -> Dict[int, List[str]]:
        """
        Извлечь темы из текста

        Простой подход: кластеризация по общим словам
        """
        if not sentences:
            return {}

        # Токенизировать предложения
        tokenized = []
        for sentence in sentences:
            words = re.findall(r'\b[а-яёa-z]{3,}\b', sentence.lower())
            words = [w for w in words if w not in self.stop_words]
            tokenized.append(words)

        # Найти самые частые слова (потенциальные темы)
        all_words = []
        for words in tokenized:
            all_words.extend(words)

        word_freq = Counter(all_words)
        topic_words = [word for word, _ in word_freq.most_common(num_topics * 3)]

        # Сгруппировать предложения по темам
        topics = defaultdict(list)

        for i, words in enumerate(tokenized):
            # Найти доминирующую тему для предложения
            topic_scores = defaultdict(int)

            for word in words:
                if word in topic_words:
                    # Какая тема?
                    topic_id = topic_words.index(word) % num_topics
                    topic_scores[topic_id] += 1

            if topic_scores:
                dominant_topic = max(topic_scores, key=topic_scores.get)
                topics[dominant_topic].append(sentences[i])

        return dict(topics)

    def summarize_by_topics(self, sentences: List[str], max_sentences: int = 3) -> Tuple[str, Dict]:
        """
        Создать резюме, выбирая предложения из разных тем
        """
        num_topics = min(3, len(sentences) // 2)
        topics = self.extract_topics(sentences, num_topics=num_topics)

        if not topics:
            return sentences[0] if sentences else "", {}

        # Выбрать по одному предложению из каждой темы
        selected = []
        sentences_per_topic = max(1, max_sentences // len(topics))

        for topic_id, topic_sentences in sorted(topics.items()):
            # Взять первое предложение из темы (обычно наиболее представительное)
            selected.extend(topic_sentences[:sentences_per_topic])

        # Если не хватает, добавить еще
        if len(selected) < max_sentences:
            remaining = max_sentences - len(selected)
            for topic_id, topic_sentences in sorted(topics.items()):
                if remaining <= 0:
                    break
                additional = topic_sentences[sentences_per_topic:sentences_per_topic + remaining]
                selected.extend(additional)
                remaining -= len(additional)

        # Восстановить порядок
        selected_ordered = []
        for sent in sentences:
            if sent in selected and sent not in selected_ordered:
                selected_ordered.append(sent)
                if len(selected_ordered) >= max_sentences:
                    break

        summary = ' '.join(selected_ordered[:max_sentences]) + '.'

        return summary, {
            'num_topics': len(topics),
            'topics': {k: len(v) for k, v in topics.items()}
        }


class AbstractiveSummarizer:
    """
    Абстрактное резюмирование (упрощенная версия)
    Генерирует новые предложения на основе шаблонов
    """

    def __init__(self, stop_words: Set[str]):
        self.stop_words = stop_words

    def extract_key_phrases(self, text: str, num_phrases: int = 5) -> List[str]:
        """
        Извлечь ключевые фразы (биграммы и триграммы)
        """
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.stop_words]

        # Биграммы
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]

        # Триграммы
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2)]

        # Частотный анализ
        phrase_freq = Counter(bigrams + trigrams)

        return [phrase for phrase, _ in phrase_freq.most_common(num_phrases)]

    def generate_template_summary(self, content: str, keywords: List[str], key_phrases: List[str]) -> str:
        """
        Генерация резюме на основе шаблонов

        Упрощенный подход: использовать ключевые слова и фразы
        """
        if not keywords:
            return "Резюме недоступно."

        # Шаблоны
        templates = [
            "Статья описывает {topic}, включая {aspects}.",
            "Основные темы: {topics}. Рассматриваются {details}.",
            "Документ охватывает {main_topic} и связанные аспекты: {related}.",
        ]

        # Заполнить шаблон
        if key_phrases:
            topic = key_phrases[0] if len(key_phrases) > 0 else keywords[0]
            aspects = ", ".join(key_phrases[1:3]) if len(key_phrases) > 1 else ", ".join(keywords[1:3])
            topics = ", ".join(keywords[:3])
            details = ", ".join(key_phrases[:2]) if key_phrases else ", ".join(keywords[:2])
            main_topic = keywords[0]
            related = ", ".join(keywords[1:4])
        else:
            topic = keywords[0] if keywords else "тема"
            aspects = ", ".join(keywords[1:3]) if len(keywords) > 1 else ""
            topics = ", ".join(keywords[:3])
            details = ", ".join(keywords[:2])
            main_topic = keywords[0] if keywords else "тема"
            related = ", ".join(keywords[1:4]) if len(keywords) > 1 else ""

        # Выбрать шаблон
        template = templates[0]

        summary = template.format(topic=topic, aspects=aspects, topics=topics,
                                 details=details, main_topic=main_topic, related=related)

        return summary

    def create_bullet_summary(self, sentences: List[str], max_points: int = 5) -> List[str]:
        """
        Создать резюме в виде списка ключевых пунктов
        """
        if not sentences:
            return []

        # Выбрать самые короткие и информативные предложения
        # Критерий: длина от 10 до 30 слов
        candidates = []

        for sent in sentences:
            words = sent.split()
            if 10 <= len(words) <= 30:
                candidates.append(sent)

        if not candidates:
            candidates = sentences

        # Взять первые max_points
        return candidates[:max_points]


class AdvancedSummaryGenerator:
    """Продвинутый генератор резюме"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Стоп-слова
        self.stop_words = set([
            'и', 'в', 'на', 'с', 'по', 'для', 'к', 'о', 'от', 'из', 'у', 'за', 'что', 'как',
            'это', 'все', 'еще', 'уже', 'только', 'такой', 'который', 'этот', 'весь', 'свой',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'
        ])

        # Инициализация новых анализаторов
        self.importance_analyzer = SentenceImportanceAnalyzer(self.stop_words)
        self.diversity_scorer = SummaryDiversityScorer()
        self.topic_summarizer = TopicModelingSummarizer(self.stop_words)
        self.abstractive_summarizer = AbstractiveSummarizer(self.stop_words)

    def extract_frontmatter_and_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None

    def tokenize(self, text):
        """Токенизация текста"""
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())
        return [w for w in words if w not in self.stop_words]

    def split_sentences(self, text):
        """Разбить на предложения"""
        # Удалить заголовки markdown
        text = re.sub(r'^#{1,6}\s+.+$', '', text, flags=re.MULTILINE)

        # Разбить на предложения
        sentences = re.split(r'[.!?]+\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

        return sentences

    def calculate_tf_idf(self, sentences):
        """Вычислить TF-IDF для предложений"""
        # Создать словарь слов -> документы
        word_doc_freq = defaultdict(int)
        sentence_words = []

        for sentence in sentences:
            words = self.tokenize(sentence)
            sentence_words.append(words)

            for word in set(words):
                word_doc_freq[word] += 1

        # Вычислить TF-IDF для каждого предложения
        total_sentences = len(sentences)
        sentence_scores = []

        for i, words in enumerate(sentence_words):
            score = 0.0
            word_count = len(words)

            if word_count == 0:
                sentence_scores.append((i, 0.0))
                continue

            word_freq = Counter(words)

            for word, freq in word_freq.items():
                tf = freq / word_count
                idf = math.log(total_sentences / (1 + word_doc_freq[word]))
                score += tf * idf

            sentence_scores.append((i, score))

        return sentence_scores

    def calculate_position_score(self, index, total):
        """Позиционный вес (первые и последние важнее)"""
        if index < 3:  # Первые 3 предложения
            return 2.0
        elif index >= total - 2:  # Последние 2
            return 1.5
        else:
            return 1.0

    def calculate_similarity(self, words1, words2):
        """Косинусное сходство между предложениями"""
        set1 = set(words1)
        set2 = set(words2)

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        denominator = math.sqrt(len(set1) * len(set2))

        return intersection / denominator if denominator > 0 else 0.0

    def textrank_score(self, sentences):
        """TextRank алгоритм для ранжирования предложений"""
        n = len(sentences)

        if n == 0:
            return []

        # Токенизировать предложения
        tokenized = [self.tokenize(s) for s in sentences]

        # Построить граф сходства
        similarity_matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                sim = self.calculate_similarity(tokenized[i], tokenized[j])
                similarity_matrix[i][j] = sim
                similarity_matrix[j][i] = sim

        # PageRank итерации
        scores = [1.0] * n
        damping = 0.85
        iterations = 30

        for _ in range(iterations):
            new_scores = [0.0] * n

            for i in range(n):
                score = (1 - damping)

                for j in range(n):
                    if i != j and similarity_matrix[j][i] > 0:
                        sum_weights = sum(similarity_matrix[j][k] for k in range(n))
                        if sum_weights > 0:
                            score += damping * scores[j] * (similarity_matrix[j][i] / sum_weights)

                new_scores[i] = score

            scores = new_scores

        return [(i, score) for i, score in enumerate(scores)]

    def generate_extractive_summary(self, content, max_sentences=3, method='combined'):
        """Генерация извлекающего резюме"""
        sentences = self.split_sentences(content)

        if not sentences:
            return "Резюме недоступно."

        if len(sentences) <= max_sentences:
            return ' '.join(sentences)

        # Различные методы ранжирования
        if method == 'tfidf':
            scores = self.calculate_tf_idf(sentences)
        elif method == 'textrank':
            scores = self.textrank_score(sentences)
        elif method == 'position':
            scores = [(i, self.calculate_position_score(i, len(sentences)))
                     for i in range(len(sentences))]
        else:  # combined
            tfidf_scores = dict(self.calculate_tf_idf(sentences))
            textrank_scores = dict(self.textrank_score(sentences))

            scores = []
            for i in range(len(sentences)):
                pos_score = self.calculate_position_score(i, len(sentences))
                combined = (
                    tfidf_scores.get(i, 0) * 0.4 +
                    textrank_scores.get(i, 0) * 0.4 +
                    pos_score * 0.2
                )
                scores.append((i, combined))

        # Сортировать по важности
        scores.sort(key=lambda x: -x[1])

        # Взять топ N предложений
        top_indices = sorted([idx for idx, _ in scores[:max_sentences]])

        # Собрать в правильном порядке
        summary_sentences = [sentences[i] for i in top_indices]

        return ' '.join(summary_sentences) + '.'

    def extract_keywords(self, content, num_keywords=10):
        """Извлечь ключевые слова"""
        words = self.tokenize(content)

        if not words:
            return []

        # Частотный анализ
        word_freq = Counter(words)

        # Топ слова
        return [word for word, count in word_freq.most_common(num_keywords)]

    def calculate_summary_quality(self, original, summary):
        """Метрики качества резюме"""
        original_words = set(self.tokenize(original))
        summary_words = set(self.tokenize(summary))

        if not original_words:
            return {'coverage': 0, 'compression_ratio': 0}

        # Coverage - сколько уникальных слов покрыто
        coverage = len(summary_words & original_words) / len(original_words)

        # Compression ratio
        compression = len(summary) / len(original) if len(original) > 0 else 0

        return {
            'coverage': round(coverage, 3),
            'compression_ratio': round(compression, 3)
        }

    def process_all(self):
        """Обработать все статьи"""
        print("📝 Генерация продвинутых резюме...\n")

        summaries = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Генерировать резюме разными методами
            summary_combined = self.generate_extractive_summary(content, max_sentences=3, method='combined')
            summary_textrank = self.generate_extractive_summary(content, max_sentences=3, method='textrank')
            summary_tfidf = self.generate_extractive_summary(content, max_sentences=3, method='tfidf')

            # Ключевые слова
            keywords = self.extract_keywords(content, num_keywords=10)

            # Метрики качества
            quality = self.calculate_summary_quality(content, summary_combined)

            summaries.append({
                'path': article_path,
                'title': title,
                'summary_combined': summary_combined,
                'summary_textrank': summary_textrank,
                'summary_tfidf': summary_tfidf,
                'keywords': keywords,
                'quality': quality,
                'original_length': len(content),
                'summary_length': len(summary_combined)
            })

        print(f"   Резюме создано для {len(summaries)} статей\n")

        return summaries

    def generate_markdown_report(self, summaries):
        """Создать Markdown отчёт"""
        lines = []
        lines.append("# 📝 Продвинутые резюме статей\n\n")
        lines.append("> Созданы с использованием TF-IDF, TextRank и позиционных весов\n\n")

        # Статистика
        lines.append("## Статистика\n\n")
        lines.append(f"- **Статей**: {len(summaries)}\n")
        avg_coverage = sum(s['quality']['coverage'] for s in summaries) / len(summaries) if summaries else 0
        avg_compression = sum(s['quality']['compression_ratio'] for s in summaries) / len(summaries) if summaries else 0
        lines.append(f"- **Средняя полнота**: {avg_coverage:.1%}\n")
        lines.append(f"- **Средняя компрессия**: {avg_compression:.1%}\n\n")

        # Резюме по статьям
        for item in summaries:
            lines.append(f"## {item['title']}\n\n")
            lines.append(f"`{item['path']}`\n\n")

            # Основное резюме
            lines.append("### Резюме (Combined)\n\n")
            lines.append(f"> {item['summary_combined']}\n\n")

            # Ключевые слова
            lines.append("**Ключевые слова**: " + ", ".join(item['keywords'][:5]) + "\n\n")

            # Метрики
            lines.append(f"**Метрики**: Coverage: {item['quality']['coverage']:.1%}, "
                        f"Compression: {item['quality']['compression_ratio']:.1%}\n\n")

            # Альтернативные резюме (в деталях)
            lines.append("<details>\n")
            lines.append("<summary>Альтернативные методы</summary>\n\n")
            lines.append(f"**TextRank**: {item['summary_textrank']}\n\n")
            lines.append(f"**TF-IDF**: {item['summary_tfidf']}\n\n")
            lines.append("</details>\n\n")

        output_file = self.root_dir / "ADVANCED_SUMMARIES.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown отчёт: {output_file}")

    def save_json(self, summaries):
        """Сохранить в JSON"""
        output_file = self.root_dir / "summaries.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'summaries': summaries}, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")

    def comprehensive_analysis(self, content: str, max_sentences: int = 3) -> Dict[str, any]:
        """
        Комплексный анализ и создание резюме

        Возвращает все варианты резюме и метрики
        """
        sentences = self.split_sentences(content)

        if not sentences:
            return {'error': 'No sentences found'}

        # Извлечь ключевые слова
        keywords = self.extract_keywords(content, num_keywords=10)

        # Создать резюме разными методами
        summary_combined = self.generate_extractive_summary(content, max_sentences, 'combined')
        summary_textrank = self.generate_extractive_summary(content, max_sentences, 'textrank')
        summary_tfidf = self.generate_extractive_summary(content, max_sentences, 'tfidf')
        summary_position = self.generate_extractive_summary(content, max_sentences, 'position')

        # Тематическое резюме
        summary_topics, topics_info = self.topic_summarizer.summarize_by_topics(sentences, max_sentences)

        # Абстрактное резюме
        key_phrases = self.abstractive_summarizer.extract_key_phrases(content, num_phrases=5)
        summary_abstractive = self.abstractive_summarizer.generate_template_summary(content, keywords, key_phrases)

        # Bullet points
        bullet_points = self.abstractive_summarizer.create_bullet_summary(sentences, max_points=5)

        # Метрики качества для combined
        quality = self.calculate_summary_quality(content, summary_combined)

        # Diversity метрики
        summary_sents = self.split_sentences(summary_combined)
        diversity = self.diversity_scorer.calculate_diversity_metrics(summary_sents, sentences)
        redundancy = self.diversity_scorer.calculate_redundancy(summary_sents)

        # Анализ важности предложений (топ-5)
        sentence_importance = []
        for i, sent in enumerate(sentences[:10]):  # Анализ первых 10
            features = self.importance_analyzer.analyze_sentence_features(sent, i, len(sentences))
            importance_score = self.importance_analyzer.calculate_importance_score(features)
            sentence_importance.append({
                'sentence': sent[:100] + '...' if len(sent) > 100 else sent,
                'importance_score': round(importance_score, 3),
                'features': features
            })

        # Сортировать по важности
        sentence_importance.sort(key=lambda x: -x['importance_score'])

        return {
            'summaries': {
                'combined': summary_combined,
                'textrank': summary_textrank,
                'tfidf': summary_tfidf,
                'position': summary_position,
                'topics': summary_topics,
                'abstractive': summary_abstractive
            },
            'bullet_points': bullet_points,
            'keywords': keywords,
            'key_phrases': key_phrases,
            'quality_metrics': quality,
            'diversity_metrics': diversity,
            'redundancy': redundancy,
            'topics_info': topics_info,
            'top_sentences': sentence_importance[:5],
            'statistics': {
                'total_sentences': len(sentences),
                'original_length': len(content),
                'summary_length': len(summary_combined)
            }
        }

    def analyze_all_with_metrics(self) -> List[Dict]:
        """Анализ всех статей с полными метриками"""
        results = []

        print("\n📊 Комплексный анализ резюме...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Комплексный анализ
            analysis = self.comprehensive_analysis(content, max_sentences=3)

            results.append({
                'path': article_path,
                'title': title,
                **analysis
            })

        print(f"✅ Проанализировано статей: {len(results)}\n")

        return results

    def export_html_summaries(self, summaries: List[Dict], output_file: str):
        """Экспорт резюме в HTML с красивым оформлением"""
        html = []
        html.append('<!DOCTYPE html>\n<html lang="ru">\n<head>\n')
        html.append('<meta charset="UTF-8">\n')
        html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        html.append('<title>Продвинутые резюме статей</title>\n')
        html.append('<style>\n')
        html.append('body { font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; ')
        html.append('max-width: 1400px; margin: 0 auto; padding: 20px; background: #f8f9fa; }\n')
        html.append('h1 { color: #2c3e50; border-bottom: 4px solid #3498db; padding-bottom: 15px; }\n')
        html.append('h2 { color: #34495e; margin-top: 30px; }\n')
        html.append('.article { background: white; border-radius: 10px; padding: 25px; ')
        html.append('margin-bottom: 25px; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }\n')
        html.append('.title { font-size: 1.6em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }\n')
        html.append('.summary-box { background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; ')
        html.append('margin: 15px 0; border-radius: 5px; }\n')
        html.append('.summary-label { font-weight: bold; color: #7f8c8d; font-size: 0.9em; ')
        html.append('text-transform: uppercase; margin-bottom: 8px; }\n')
        html.append('.summary-text { color: #2c3e50; line-height: 1.6; }\n')
        html.append('.keywords { margin: 15px 0; }\n')
        html.append('.keyword-tag { display: inline-block; background: #3498db; color: white; ')
        html.append('padding: 5px 12px; border-radius: 15px; margin: 3px; font-size: 0.85em; }\n')
        html.append('.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); ')
        html.append('gap: 10px; margin: 15px 0; }\n')
        html.append('.metric { background: #fff; border: 1px solid #ddd; padding: 10px; ')
        html.append('border-radius: 5px; text-align: center; }\n')
        html.append('.metric-value { font-size: 1.4em; font-weight: bold; color: #3498db; }\n')
        html.append('.metric-label { font-size: 0.8em; color: #7f8c8d; margin-top: 5px; }\n')
        html.append('.bullet-list { list-style: none; padding-left: 0; }\n')
        html.append('.bullet-list li { padding: 8px 0; padding-left: 25px; ')
        html.append('border-left: 3px solid #3498db; margin: 5px 0; }\n')
        html.append('.tabs { display: flex; gap: 10px; margin: 15px 0; }\n')
        html.append('.tab { padding: 10px 20px; background: #ecf0f1; border-radius: 5px 5px 0 0; ')
        html.append('cursor: pointer; font-weight: bold; color: #7f8c8d; }\n')
        html.append('.tab.active { background: #3498db; color: white; }\n')
        html.append('</style>\n</head>\n<body>\n')

        html.append('<h1>📝 Продвинутые резюме статей</h1>\n')
        html.append('<p style="color: #7f8c8d;">Созданы с использованием TF-IDF, TextRank, тематического моделирования и абстрактного резюмирования</p>\n')

        # Статистика
        html.append('<div class="article">\n')
        html.append('<h2>Общая статистика</h2>\n')
        total_articles = len(summaries)
        avg_coverage = sum(s.get('quality_metrics', {}).get('coverage', 0) for s in summaries) / total_articles if total_articles > 0 else 0
        avg_diversity = sum(s.get('diversity_metrics', {}).get('diversity_score', 0) for s in summaries) / total_articles if total_articles > 0 else 0

        html.append('<div class="metrics">\n')
        html.append(f'<div class="metric"><div class="metric-value">{total_articles}</div>')
        html.append('<div class="metric-label">Статей</div></div>\n')
        html.append(f'<div class="metric"><div class="metric-value">{avg_coverage:.1%}</div>')
        html.append('<div class="metric-label">Средняя полнота</div></div>\n')
        html.append(f'<div class="metric"><div class="metric-value">{avg_diversity:.2f}</div>')
        html.append('<div class="metric-label">Средняя разнообразность</div></div>\n')
        html.append('</div>\n')
        html.append('</div>\n')

        # Каждая статья
        for item in summaries:
            html.append('<div class="article">\n')
            html.append(f'<div class="title">{item["title"]}</div>\n')
            html.append(f'<div style="color: #7f8c8d; font-size: 0.9em; margin-bottom: 15px;">{item["path"]}</div>\n')

            # Основное резюме
            summary = item.get('summaries', {}).get('combined', '')
            html.append('<div class="summary-box">\n')
            html.append('<div class="summary-label">📌 Комбинированное резюме</div>\n')
            html.append(f'<div class="summary-text">{summary}</div>\n')
            html.append('</div>\n')

            # Bullet points
            bullets = item.get('bullet_points', [])
            if bullets:
                html.append('<div style="margin: 15px 0;">\n')
                html.append('<div class="summary-label">🔸 Ключевые пункты:</div>\n')
                html.append('<ul class="bullet-list">\n')
                for bullet in bullets[:5]:
                    html.append(f'<li>{bullet}</li>\n')
                html.append('</ul>\n')
                html.append('</div>\n')

            # Ключевые слова
            keywords = item.get('keywords', [])[:8]
            if keywords:
                html.append('<div class="keywords">\n')
                html.append('<div class="summary-label">🏷️ Ключевые слова:</div>\n')
                for kw in keywords:
                    html.append(f'<span class="keyword-tag">{kw}</span>\n')
                html.append('</div>\n')

            # Метрики
            quality = item.get('quality_metrics', {})
            diversity = item.get('diversity_metrics', {})
            redundancy = item.get('redundancy', 0)

            html.append('<div class="metrics">\n')
            html.append(f'<div class="metric"><div class="metric-value">{quality.get("coverage", 0):.1%}</div>')
            html.append('<div class="metric-label">Полнота</div></div>\n')
            html.append(f'<div class="metric"><div class="metric-value">{quality.get("compression_ratio", 0):.1%}</div>')
            html.append('<div class="metric-label">Компрессия</div></div>\n')
            html.append(f'<div class="metric"><div class="metric-value">{diversity.get("diversity_score", 0):.2f}</div>')
            html.append('<div class="metric-label">Разнообразие</div></div>\n')
            html.append(f'<div class="metric"><div class="metric-value">{redundancy:.2f}</div>')
            html.append('<div class="metric-label">Избыточность</div></div>\n')
            html.append('</div>\n')

            html.append('</div>\n')

        html.append('</body>\n</html>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(html))

        print(f"✅ HTML экспорт: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='📝 Advanced Summary Generator - Продвинутое резюмирование текстов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                          # Базовое резюмирование всех статей
  %(prog)s --analyze                                # Комплексный анализ с метриками
  %(prog)s --method textrank                        # Использовать только TextRank
  %(prog)s --topics                                 # Тематическое резюмирование
  %(prog)s --abstractive                            # Абстрактное резюмирование
  %(prog)s --json output.json                       # Экспорт в JSON
  %(prog)s --html output.html                       # Экспорт в HTML
  %(prog)s --all                                    # Полный анализ + все экспорты
        """
    )

    # Режимы работы
    parser.add_argument(
        '-m', '--method',
        choices=['combined', 'textrank', 'tfidf', 'position'],
        default='combined',
        help='Метод резюмирования (по умолчанию: combined)'
    )

    parser.add_argument(
        '-n', '--sentences',
        type=int,
        default=3,
        help='Количество предложений в резюме (по умолчанию: 3)'
    )

    # Расширенные опции
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Комплексный анализ с метриками качества и разнообразия'
    )

    parser.add_argument(
        '--topics',
        action='store_true',
        help='Тематическое резюмирование (извлечение тем)'
    )

    parser.add_argument(
        '--abstractive',
        action='store_true',
        help='Абстрактное резюмирование (генерация новых предложений)'
    )

    parser.add_argument(
        '--diversity',
        action='store_true',
        help='Анализ разнообразия резюме'
    )

    parser.add_argument(
        '--importance',
        action='store_true',
        help='Анализ важности предложений'
    )

    # Экспорт
    parser.add_argument(
        '--json',
        metavar='FILE',
        help='Экспортировать результаты в JSON'
    )

    parser.add_argument(
        '--html',
        metavar='FILE',
        help='Экспортировать результаты в HTML с красивым оформлением'
    )

    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Создать Markdown отчёт'
    )

    # Специальные опции
    parser.add_argument(
        '--all',
        action='store_true',
        help='Выполнить все виды анализа и экспорта'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = AdvancedSummaryGenerator(root_dir)

    # Обработка --all
    if args.all:
        args.analyze = True
        args.topics = True
        args.abstractive = True
        args.diversity = True
        args.importance = True
        args.markdown = True
        if not args.json:
            args.json = str(root_dir / "summaries_comprehensive.json")
        if not args.html:
            args.html = str(root_dir / "summaries_comprehensive.html")

    # Комплексный анализ
    if args.analyze or args.topics or args.abstractive or args.diversity or args.importance:
        print("🔍 Комплексный анализ резюме...\n")
        results = generator.analyze_all_with_metrics()

        if not results:
            print("❌ Нет статей для анализа")
            return

        # Статистика
        print("📊 Общая статистика:")
        print(f"   • Проанализировано статей: {len(results)}")

        avg_coverage = sum(r.get('quality_metrics', {}).get('coverage', 0) for r in results) / len(results) if results else 0
        avg_compression = sum(r.get('quality_metrics', {}).get('compression_ratio', 0) for r in results) / len(results) if results else 0
        avg_diversity = sum(r.get('diversity_metrics', {}).get('diversity_score', 0) for r in results) / len(results) if results else 0
        avg_redundancy = sum(r.get('redundancy', 0) for r in results) / len(results) if results else 0

        print(f"   • Средняя полнота резюме: {avg_coverage:.1%}")
        print(f"   • Средняя компрессия: {avg_compression:.1%}")
        print(f"   • Средняя разнообразность: {avg_diversity:.2f}")
        print(f"   • Средняя избыточность: {avg_redundancy:.2f}")

        # Топ по качеству
        print(f"\n🏆 Топ-5 лучших резюме (по полноте):")
        sorted_by_coverage = sorted(results, key=lambda x: x.get('quality_metrics', {}).get('coverage', 0), reverse=True)
        for i, r in enumerate(sorted_by_coverage[:5], 1):
            title = r['title']
            coverage = r.get('quality_metrics', {}).get('coverage', 0)
            diversity = r.get('diversity_metrics', {}).get('diversity_score', 0)
            print(f"   {i}. {title}: {coverage:.1%} (разнообразие: {diversity:.2f})")

        # Экспорты
        if args.json:
            json_path = root_dir / args.json if not Path(args.json).is_absolute() else Path(args.json)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'summaries': results}, f, ensure_ascii=False, indent=2)
            print(f"\n✅ JSON экспорт: {json_path}")

        if args.html:
            html_path = root_dir / args.html if not Path(args.html).is_absolute() else Path(args.html)
            generator.export_html_summaries(results, str(html_path))

        print()

    # Базовая обработка
    elif args.markdown or (not args.json and not args.html):
        summaries = generator.process_all()

        if args.markdown:
            generator.generate_markdown_report(summaries)

        if args.json:
            json_path = root_dir / args.json if not Path(args.json).is_absolute() else Path(args.json)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'summaries': summaries}, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON экспорт: {json_path}")
        else:
            generator.save_json(summaries)

    # Только экспорт
    elif args.json or args.html:
        summaries = generator.process_all()

        if args.json:
            json_path = root_dir / args.json if not Path(args.json).is_absolute() else Path(args.json)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'summaries': summaries}, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON экспорт: {json_path}")

        if args.html:
            # Для HTML нужен полный анализ
            results = generator.analyze_all_with_metrics()
            html_path = root_dir / args.html if not Path(args.html).is_absolute() else Path(args.html)
            generator.export_html_summaries(results, str(html_path))


if __name__ == "__main__":
    main()
