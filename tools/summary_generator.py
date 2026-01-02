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


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Summary Generator')
    parser.add_argument('-m', '--method', choices=['combined', 'textrank', 'tfidf', 'position'],
                       default='combined', help='Метод резюмирования')
    parser.add_argument('-n', '--sentences', type=int, default=3,
                       help='Количество предложений в резюме')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = AdvancedSummaryGenerator(root_dir)
    summaries = generator.process_all()
    generator.generate_markdown_report(summaries)
    generator.save_json(summaries)


if __name__ == "__main__":
    main()
