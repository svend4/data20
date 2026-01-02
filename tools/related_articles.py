#!/usr/bin/env python3
"""
Related Articles - Рекомендации статей
Умная система рекомендаций на основе контента, тегов и связей

Вдохновлено: рекомендательными системами Amazon, YouTube
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json
import math


class RelatedArticlesEngine:
    """Движок рекомендаций"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Данные статей
        self.articles = {}
        self.links = defaultdict(lambda: {'outgoing': [], 'incoming': []})

        # TF-IDF для контента
        self.word_counts = defaultdict(lambda: defaultdict(int))
        self.document_freq = defaultdict(int)

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
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
        """Простая токенизация"""
        # Удалить markdown синтаксис
        text = re.sub(r'[#*`\[\]()]', ' ', text)
        # Разбить на слова
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())
        return words

    def build_index(self):
        """Построить индекс"""
        print("🎯 Построение индекса рекомендаций...\n")

        # Собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            self.articles[article_path] = {
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'tags': frontmatter.get('tags', []) if frontmatter else [],
                'category': frontmatter.get('category', '') if frontmatter else '',
                'subcategory': frontmatter.get('subcategory', '') if frontmatter else '',
                'difficulty': frontmatter.get('difficulty', 'средний') if frontmatter else 'средний'
            }

            # Токенизация контента
            words = self.tokenize(content)
            unique_words = set(words)

            for word in words:
                self.word_counts[article_path][word] += 1

            for word in unique_words:
                self.document_freq[word] += 1

            # Извлечь ссылки
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

            for text, link in links:
                if link.startswith('http'):
                    continue

                try:
                    target = (md_file.parent / link.split('#')[0]).resolve()

                    if target.exists() and target.is_relative_to(self.root_dir):
                        target_path = str(target.relative_to(self.root_dir))

                        if target_path not in self.links[article_path]['outgoing']:
                            self.links[article_path]['outgoing'].append(target_path)

                        if article_path not in self.links[target_path]['incoming']:
                            self.links[target_path]['incoming'].append(article_path)
                except:
                    pass

        print(f"   Статей проиндексировано: {len(self.articles)}\n")

    def calculate_tf_idf_similarity(self, article1, article2):
        """Вычислить TF-IDF сходство"""
        if article1 not in self.word_counts or article2 not in self.word_counts:
            return 0.0

        words1 = self.word_counts[article1]
        words2 = self.word_counts[article2]

        # Все уникальные слова
        all_words = set(words1.keys()) | set(words2.keys())

        # TF-IDF векторы
        vector1 = []
        vector2 = []

        total_docs = len(self.articles)

        for word in all_words:
            # TF-IDF для article1
            tf1 = words1.get(word, 0)
            idf = math.log(total_docs / (1 + self.document_freq[word]))
            vector1.append(tf1 * idf)

            # TF-IDF для article2
            tf2 = words2.get(word, 0)
            vector2.append(tf2 * idf)

        # Косинусное сходство
        dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
        magnitude1 = math.sqrt(sum(v ** 2 for v in vector1))
        magnitude2 = math.sqrt(sum(v ** 2 for v in vector2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def calculate_tag_similarity(self, article1, article2):
        """Вычислить сходство тегов (Jaccard)"""
        tags1 = set(self.articles[article1]['tags'])
        tags2 = set(self.articles[article2]['tags'])

        if not tags1 or not tags2:
            return 0.0

        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)

        return intersection / union if union > 0 else 0.0

    def calculate_link_score(self, article1, article2):
        """Вычислить оценку связей"""
        score = 0.0

        # Прямая ссылка
        if article2 in self.links[article1]['outgoing']:
            score += 1.0

        # Обратная ссылка
        if article2 in self.links[article1]['incoming']:
            score += 0.5

        # Общие входящие ссылки
        incoming1 = set(self.links[article1]['incoming'])
        incoming2 = set(self.links[article2]['incoming'])
        common_incoming = len(incoming1 & incoming2)
        if common_incoming > 0:
            score += 0.3 * common_incoming

        # Общие исходящие ссылки
        outgoing1 = set(self.links[article1]['outgoing'])
        outgoing2 = set(self.links[article2]['outgoing'])
        common_outgoing = len(outgoing1 & outgoing2)
        if common_outgoing > 0:
            score += 0.2 * common_outgoing

        return score

    def calculate_similarity(self, article1, article2):
        """Вычислить общее сходство"""
        if article1 == article2:
            return 0.0

        # Взвешенная комбинация метрик
        content_sim = self.calculate_tf_idf_similarity(article1, article2)
        tag_sim = self.calculate_tag_similarity(article1, article2)
        link_score = self.calculate_link_score(article1, article2)

        # Бонус за одинаковую категорию
        category_bonus = 0.0
        if self.articles[article1]['category'] == self.articles[article2]['category']:
            category_bonus = 0.2

        # Бонус за одинаковую подкатегорию
        subcategory_bonus = 0.0
        if (self.articles[article1]['subcategory'] and
            self.articles[article1]['subcategory'] == self.articles[article2]['subcategory']):
            subcategory_bonus = 0.3

        # Итоговая оценка
        total = (
            content_sim * 0.3 +
            tag_sim * 0.4 +
            link_score * 0.2 +
            category_bonus +
            subcategory_bonus
        )

        return total

    def get_recommendations(self, article_path, limit=5):
        """Получить рекомендации для статьи"""
        if article_path not in self.articles:
            return []

        similarities = []

        for other_article in self.articles:
            if other_article == article_path:
                continue

            score = self.calculate_similarity(article_path, other_article)
            similarities.append((other_article, score))

        # Сортировать по убыванию
        similarities.sort(key=lambda x: -x[1])

        return similarities[:limit]

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🎯 Рекомендации статей\n\n")
        lines.append("> Умная система рекомендаций на основе контента, тегов и связей\n\n")

        # Для каждой статьи - топ рекомендаций
        for article_path in sorted(self.articles.keys()):
            title = self.articles[article_path]['title']
            recommendations = self.get_recommendations(article_path, limit=5)

            if not recommendations:
                continue

            lines.append(f"## {title}\n\n")
            lines.append(f"`{article_path}`\n\n")
            lines.append("**Рекомендуем прочитать:**\n\n")

            for i, (rec_path, score) in enumerate(recommendations, 1):
                rec_title = self.articles[rec_path]['title']
                lines.append(f"{i}. [{rec_title}]({rec_path}) — *оценка: {score:.2f}*\n")

                # Показать почему рекомендуем
                reasons = []
                tag_sim = self.calculate_tag_similarity(article_path, rec_path)
                if tag_sim > 0.3:
                    reasons.append(f"похожие теги ({tag_sim:.0%})")

                if rec_path in self.links[article_path]['outgoing']:
                    reasons.append("вы ссылаетесь на эту статью")

                if rec_path in self.links[article_path]['incoming']:
                    reasons.append("эта статья ссылается на вас")

                if self.articles[article_path]['category'] == self.articles[rec_path]['category']:
                    reasons.append("та же категория")

                if reasons:
                    lines.append(f"   *{', '.join(reasons)}*\n")

            lines.append("\n")

        output_file = self.root_dir / "RELATED_ARTICLES.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить рекомендации в JSON"""
        data = {}

        for article_path in self.articles:
            recommendations = self.get_recommendations(article_path, limit=10)

            data[article_path] = {
                'title': self.articles[article_path]['title'],
                'recommendations': [
                    {
                        'article': rec_path,
                        'title': self.articles[rec_path]['title'],
                        'score': score
                    }
                    for rec_path, score in recommendations
                ]
            }

        output_file = self.root_dir / "related_articles.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON рекомендации: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    engine = RelatedArticlesEngine(root_dir)
    engine.build_index()
    engine.generate_report()
    engine.save_json()


if __name__ == "__main__":
    main()
