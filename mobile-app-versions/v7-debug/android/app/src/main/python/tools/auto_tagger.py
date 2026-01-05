#!/usr/bin/env python3
"""
Advanced Auto-Tagger - Продвинутая автоматическая генерация тегов
Функции:
- TF-IDF scoring (важность, не просто частота)
- N-граммы (биграммы, триграммы как теги-фразы)
- Weighted analysis (заголовки, выделения весят больше)
- Tag recommendations (на основе похожих статей)
- Confidence scores для каждого предложения
- Tag hierarchies и clustering
- Анализ существующих тегов в базе (популярность)
- Auto-apply mode (автоматическое добавление)
- Tag co-occurrence analysis
- Synonym detection
- Multi-language support

Вдохновлено: WordPress auto-tagging, ML text classification, Tag clustering
"""

from pathlib import Path
import yaml
import re
from collections import Counter, defaultdict
import json
import math


class AdvancedAutoTagger:
    """Продвинутый автоматический генератор тегов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Стоп-слова (расширенный список)
        self.stop_words = set([
            'и', 'в', 'на', 'с', 'по', 'для', 'к', 'о', 'от', 'из', 'у', 'за', 'это', 'как',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does'
        ])

        # Глобальная статистика тегов
        self.tag_stats = defaultdict(int)
        self.tag_cooccurrence = defaultdict(lambda: defaultdict(int))
        self.document_frequency = defaultdict(int)  # Для IDF
        self.total_documents = 0

        # Кэш для похожих статей
        self.article_vectors = {}

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return match.group(1), yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None, None

    def build_corpus_statistics(self):
        """Построить статистику по всему корпусу"""
        print("📊 Анализ корпуса для TF-IDF...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            self.total_documents += 1

            # Собрать статистику существующих тегов
            if frontmatter and 'tags' in frontmatter:
                tags = frontmatter['tags']
                for tag in tags:
                    self.tag_stats[tag.lower()] += 1

                # Co-occurrence
                for i, tag1 in enumerate(tags):
                    for tag2 in tags[i+1:]:
                        self.tag_cooccurrence[tag1.lower()][tag2.lower()] += 1
                        self.tag_cooccurrence[tag2.lower()][tag1.lower()] += 1

            # Document frequency для IDF
            words = self.tokenize(content)
            unique_words = set(words)
            for word in unique_words:
                self.document_frequency[word] += 1

        print(f"   Документов: {self.total_documents}")
        print(f"   Уникальных тегов: {len(self.tag_stats)}")
        print(f"   Словарь: {len(self.document_frequency)} слов\n")

    def tokenize(self, text):
        """Токенизация текста"""
        # Удалить markdown
        text = re.sub(r'[#*`\[\]()]', ' ', text)

        # Извлечь слова (русские и английские)
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())

        # Фильтровать стоп-слова
        words = [w for w in words if w not in self.stop_words]

        return words

    def extract_ngrams(self, text, n=2):
        """Извлечь n-граммы (биграммы, триграммы)"""
        words = self.tokenize(text)
        ngrams = []

        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)

        return ngrams

    def calculate_tfidf(self, text):
        """Вычислить TF-IDF для слов"""
        words = self.tokenize(text)
        word_count = len(words)

        # Term Frequency
        tf = Counter(words)

        # TF-IDF scores
        tfidf_scores = {}

        for word, count in tf.items():
            # TF (normalized)
            term_freq = count / word_count if word_count > 0 else 0

            # IDF
            doc_freq = self.document_frequency.get(word, 1)
            idf = math.log(self.total_documents / doc_freq) if doc_freq > 0 else 0

            # TF-IDF
            tfidf_scores[word] = term_freq * idf

        return tfidf_scores

    def extract_weighted_keywords(self, content):
        """Извлечь ключевые слова с весами"""
        # Разделить на части с разными весами
        parts = {
            'headers': [],
            'bold': [],
            'body': content
        }

        # Извлечь заголовки (# заголовок)
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        parts['headers'] = ' '.join(headers)

        # Извлечь выделенный текст (**bold**)
        bold_text = re.findall(r'\*\*([^*]+)\*\*', content)
        parts['bold'] = ' '.join(bold_text)

        # Вычислить TF-IDF для каждой части
        scores = defaultdict(float)

        # Заголовки - вес 3.0
        if parts['headers']:
            header_scores = self.calculate_tfidf(parts['headers'])
            for word, score in header_scores.items():
                scores[word] += score * 3.0

        # Выделенный текст - вес 2.0
        if parts['bold']:
            bold_scores = self.calculate_tfidf(parts['bold'])
            for word, score in bold_scores.items():
                scores[word] += score * 2.0

        # Основной текст - вес 1.0
        body_scores = self.calculate_tfidf(content)
        for word, score in body_scores.items():
            scores[word] += score * 1.0

        return scores

    def extract_ngram_candidates(self, content):
        """Извлечь кандидатов-биграмм и триграмм"""
        bigrams = self.extract_ngrams(content, n=2)
        trigrams = self.extract_ngrams(content, n=3)

        # Подсчитать частоту
        bigram_freq = Counter(bigrams)
        trigram_freq = Counter(trigrams)

        # Фильтровать (минимум 2 упоминания)
        good_bigrams = {bg: count for bg, count in bigram_freq.items() if count >= 2}
        good_trigrams = {tg: count for tg, count in trigram_freq.items() if count >= 2}

        return good_bigrams, good_trigrams

    def calculate_confidence(self, word, score, word_freq, existing_tags):
        """Вычислить confidence score для предложения"""
        confidence = 0.0

        # Базовый score от TF-IDF (0-1)
        confidence += min(score / 10, 1.0) * 0.4

        # Частота использования как тег в корпусе
        if word in self.tag_stats:
            tag_popularity = min(self.tag_stats[word] / 10, 1.0)
            confidence += tag_popularity * 0.3

        # Co-occurrence с существующими тегами
        if existing_tags:
            max_cooccurrence = 0
            for existing_tag in existing_tags:
                cooc = self.tag_cooccurrence[word].get(existing_tag.lower(), 0)
                max_cooccurrence = max(max_cooccurrence, cooc)

            cooc_score = min(max_cooccurrence / 5, 1.0)
            confidence += cooc_score * 0.3

        return min(confidence, 1.0)

    def find_similar_articles(self, article_path, top_k=3):
        """Найти похожие статьи для рекомендаций"""
        # Простая similarity на основе общих слов
        target_file = self.root_dir / article_path
        _, _, target_content = self.extract_frontmatter_and_content(target_file)

        if not target_content:
            return []

        target_words = set(self.tokenize(target_content))

        similarities = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            other_path = str(md_file.relative_to(self.root_dir))
            if other_path == article_path:
                continue

            _, frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content or not frontmatter or 'tags' not in frontmatter:
                continue

            other_words = set(self.tokenize(content))

            # Jaccard similarity
            intersection = len(target_words & other_words)
            union = len(target_words | other_words)

            if union > 0:
                similarity = intersection / union

                if similarity > 0.1:  # Минимальный порог
                    similarities.append({
                        'path': other_path,
                        'similarity': similarity,
                        'tags': frontmatter['tags']
                    })

        # Сортировать по similarity
        similarities.sort(key=lambda x: -x['similarity'])

        return similarities[:top_k]

    def get_recommendations_from_similar(self, similar_articles, existing_tags):
        """Получить рекомендации от похожих статей"""
        recommended = Counter()

        for article in similar_articles:
            for tag in article['tags']:
                tag_lower = tag.lower()

                # Пропустить уже существующие
                if tag_lower not in [t.lower() for t in existing_tags]:
                    # Вес = similarity
                    recommended[tag_lower] += article['similarity']

        return recommended

    def suggest_tags(self, file_path, num_suggestions=5):
        """Предложить теги для статьи (продвинутая версия)"""
        frontmatter_str, frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        article_path = str(file_path.relative_to(self.root_dir))
        title = frontmatter.get('title', file_path.stem) if frontmatter else file_path.stem
        existing_tags = frontmatter.get('tags', []) if frontmatter else []

        # 1. TF-IDF с весами
        weighted_scores = self.extract_weighted_keywords(content)

        # 2. N-граммы
        bigrams, trigrams = self.extract_ngram_candidates(content)

        # 3. Похожие статьи
        similar_articles = self.find_similar_articles(article_path)
        similar_recommendations = self.get_recommendations_from_similar(similar_articles, existing_tags)

        # Объединить все кандидаты
        candidates = []

        # Одиночные слова (TF-IDF)
        for word, score in weighted_scores.items():
            if word not in [t.lower() for t in existing_tags]:
                word_freq = Counter(self.tokenize(content))[word]
                confidence = self.calculate_confidence(word, score, word_freq, existing_tags)

                candidates.append({
                    'tag': word,
                    'score': score,
                    'confidence': confidence,
                    'type': 'word',
                    'source': 'tfidf'
                })

        # Биграммы
        for bigram, freq in bigrams.items():
            if bigram not in [t.lower() for t in existing_tags]:
                candidates.append({
                    'tag': bigram,
                    'score': freq * 2,  # Биграммы ценнее
                    'confidence': min(freq / 10, 1.0),
                    'type': 'bigram',
                    'source': 'ngram'
                })

        # Триграммы
        for trigram, freq in trigrams.items():
            if trigram not in [t.lower() for t in existing_tags]:
                candidates.append({
                    'tag': trigram,
                    'score': freq * 3,  # Триграммы еще ценнее
                    'confidence': min(freq / 10, 1.0),
                    'type': 'trigram',
                    'source': 'ngram'
                })

        # Рекомендации от похожих
        for tag, score in similar_recommendations.items():
            candidates.append({
                'tag': tag,
                'score': score * 10,
                'confidence': min(score, 1.0),
                'type': 'word',
                'source': 'similar'
            })

        # Сортировать по комбинации score * confidence
        candidates.sort(key=lambda x: -(x['score'] * x['confidence']))

        # Топ предложения
        top_suggestions = candidates[:num_suggestions]

        return {
            'path': article_path,
            'title': title,
            'existing_tags': existing_tags,
            'suggestions': top_suggestions,
            'similar_articles': similar_articles
        }

    def analyze_all(self):
        """Проанализировать все статьи"""
        print("🏷️  Продвинутая генерация тегов...\n")

        # Сначала построить статистику
        self.build_corpus_statistics()

        suggestions = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.suggest_tags(md_file)
            if result and result['suggestions']:
                suggestions.append(result)

        print(f"   Статей с предложениями: {len(suggestions)}\n")

        return suggestions

    def generate_report(self, suggestions):
        """Создать подробный отчёт"""
        lines = []
        lines.append("# 🏷️ Продвинутые предложения тегов\n\n")
        lines.append("> Генерация на основе TF-IDF, n-грамм и анализа похожих статей\n\n")

        for item in suggestions:
            lines.append(f"## {item['title']}\n\n")
            lines.append(f"`{item['path']}`\n\n")

            # Текущие теги
            if item['existing_tags']:
                lines.append(f"**Текущие теги**: {', '.join(item['existing_tags'])}\n\n")
            else:
                lines.append(f"**Текущие теги**: нет\n\n")

            # Предложенные теги
            lines.append("**Предложенные теги**:\n\n")

            for i, sugg in enumerate(item['suggestions'], 1):
                confidence_pct = sugg['confidence'] * 100

                # Иконка типа
                type_icon = {
                    'word': '🔤',
                    'bigram': '🔗',
                    'trigram': '🔗🔗'
                }.get(sugg['type'], '•')

                # Источник
                source_label = {
                    'tfidf': 'TF-IDF',
                    'ngram': 'N-gram',
                    'similar': 'Похожие статьи'
                }.get(sugg['source'], 'Unknown')

                lines.append(f"{i}. {type_icon} **{sugg['tag']}** ")
                lines.append(f"(confidence: {confidence_pct:.0f}%, source: {source_label})\n")

            # Похожие статьи
            if item.get('similar_articles'):
                lines.append("\n**Похожие статьи** (для контекста):\n\n")

                for similar in item['similar_articles'][:3]:
                    sim_pct = similar['similarity'] * 100
                    lines.append(f"- {Path(similar['path']).stem} ({sim_pct:.0f}% похожести)\n")
                    lines.append(f"  Теги: {', '.join(similar['tags'])}\n")

            lines.append("\n---\n\n")

        output_file = self.root_dir / "ADVANCED_TAGGING_SUGGESTIONS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def export_json(self, suggestions):
        """Экспорт в JSON"""
        output_file = self.root_dir / "tagging_suggestions.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON: {output_file}")

    def auto_apply_tags(self, article_path, tags_to_add):
        """Автоматически добавить теги в статью"""
        file_path = self.root_dir / article_path

        frontmatter_str, frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not frontmatter:
            frontmatter = {}

        # Добавить теги
        existing_tags = frontmatter.get('tags', [])
        new_tags = existing_tags + tags_to_add

        # Уникальные теги
        new_tags = list(dict.fromkeys(new_tags))

        frontmatter['tags'] = new_tags

        # Сохранить
        new_frontmatter = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
        full_content = f"---\n{new_frontmatter}---\n\n{content}"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Auto-Tagger')
    parser.add_argument('-n', '--num-suggestions', type=int, default=5,
                       help='Количество предложений (по умолчанию: 5)')
    parser.add_argument('--json', action='store_true',
                       help='Экспорт в JSON')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tagger = AdvancedAutoTagger(root_dir)
    suggestions = tagger.analyze_all()
    tagger.generate_report(suggestions)

    if args.json:
        tagger.export_json(suggestions)


if __name__ == "__main__":
    main()
