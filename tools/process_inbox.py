#!/usr/bin/env python3
"""
Скрипт для автоматического анализа и обработки входящих материалов
Использует AI для категоризации и структурирования
"""

import os
import re
from pathlib import Path
from datetime import datetime
import yaml


class InboxProcessor:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.inbox_dir = self.root_dir / "inbox" / "raw"
        self.knowledge_dir = self.root_dir / "knowledge"

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные из frontmatter"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return None, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError:
            return None, content

    def analyze_content(self, text):
        """
        Анализ содержимого для определения темы
        В реальной реализации здесь можно использовать AI API
        """
        # Простой keyword-based анализ
        keywords = {
            'computers': [
                'программирование', 'python', 'javascript', 'код', 'алгоритм',
                'компьютер', 'процессор', 'gpu', 'cpu', 'ssd', 'память',
                'ai', 'ml', 'нейросеть', 'llm', 'claude', 'gpt',
                'docker', 'kubernetes', 'linux', 'windows',
                'database', 'sql', 'postgresql', 'mongodb',
                'security', 'encryption', 'vulnerability'
            ],
            'household': [
                'холодильник', 'плита', 'стиральная', 'посудомоечная',
                'пылесос', 'кондиционер', 'обогреватель',
                'мебель', 'диван', 'стол', 'стул',
                'ремонт', 'уборка', 'чистка', 'обслуживание',
                'энергоэффективность', 'электроэнергия'
            ],
            'cooking': [
                'рецепт', 'готовить', 'приготовление', 'ингредиент',
                'блюдо', 'суп', 'салат', 'десерт', 'торт',
                'завтрак', 'обед', 'ужин',
                'варить', 'жарить', 'печь', 'тушить'
            ]
        }

        text_lower = text.lower()
        scores = {category: 0 for category in keywords}

        for category, words in keywords.items():
            for word in words:
                if word in text_lower:
                    scores[category] += text_lower.count(word)

        # Определить категорию с наибольшим счетом
        max_category = max(scores, key=scores.get)
        if scores[max_category] > 0:
            return max_category
        return None

    def extract_keywords(self, text, num_keywords=5):
        """
        Извлечение ключевых слов из текста
        Простая реализация - можно улучшить через TF-IDF или AI
        """
        # Удалить стоп-слова (упрощенно)
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'как', 'что', 'это',
            'из', 'к', 'или', 'а', 'но', 'то', 'не', 'за', 'при'
        }

        # Извлечь слова (только кириллица и латиница)
        words = re.findall(r'[а-яёa-z]+', text.lower())

        # Фильтровать стоп-слова и короткие слова
        words = [w for w in words if w not in stop_words and len(w) > 3]

        # Подсчитать частоту
        from collections import Counter
        word_freq = Counter(words)

        # Вернуть топ N
        return [word for word, count in word_freq.most_common(num_keywords)]

    def suggest_structure(self, category, text):
        """
        Предложить структуру для материала
        """
        # Найти заголовки
        headers = re.findall(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)

        # Оценить размер
        lines = len(text.split('\n'))
        words = len(text.split())

        suggestion = {
            'category': category,
            'size': {
                'lines': lines,
                'words': words
            },
            'headers': headers,
            'recommended_action': None
        }

        # Рекомендации
        if lines < 100:
            suggestion['recommended_action'] = 'single_article'
        elif lines < 500:
            suggestion['recommended_action'] = 'article_with_sections'
        else:
            suggestion['recommended_action'] = 'split_into_multiple'

        return suggestion

    def process_file(self, file_path):
        """Обработать один файл из inbox"""
        print(f"\n📄 Обработка: {file_path.name}")

        frontmatter, content = self.extract_frontmatter(file_path)

        # Определить категорию
        category = self.analyze_content(content)
        if not category:
            print(f"⚠️  Не удалось определить категорию автоматически")
            return None

        print(f"📂 Предложенная категория: {category}")

        # Извлечь ключевые слова
        keywords = self.extract_keywords(content)
        print(f"🏷️  Ключевые слова: {', '.join(keywords)}")

        # Предложить структуру
        structure = self.suggest_structure(category, content)
        print(f"📊 Размер: {structure['size']['lines']} строк, {structure['size']['words']} слов")
        print(f"💡 Рекомендация: {structure['recommended_action']}")

        if structure['headers']:
            print(f"📑 Найденные заголовки:")
            for h in structure['headers'][:5]:
                print(f"   - {h}")

        # Создать отчет
        report = {
            'source_file': str(file_path),
            'category': category,
            'keywords': keywords,
            'structure': structure,
            'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return report

    def run(self):
        """Обработать все файлы в inbox/raw"""
        print("🔄 Начинаю обработку входящих материалов...\n")

        if not self.inbox_dir.exists():
            print("❌ Директория inbox/raw не найдена")
            return

        # Найти все markdown файлы, кроме примеров
        files = [f for f in self.inbox_dir.glob("*.md")
                if not f.name.startswith('.')]

        if not files:
            print("📭 Нет файлов для обработки")
            return

        reports = []
        for file_path in files:
            report = self.process_file(file_path)
            if report:
                reports.append(report)

        print(f"\n✅ Обработано файлов: {len(reports)}")

        # Сохранить отчет
        if reports:
            self.save_report(reports)

    def save_report(self, reports):
        """Сохранить отчет об обработке"""
        report_file = self.root_dir / "inbox" / "processing_report.yaml"

        with open(report_file, 'w', encoding='utf-8') as f:
            yaml.dump(reports, f, allow_unicode=True, sort_keys=False)

        print(f"📝 Отчет сохранен: {report_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    processor = InboxProcessor(root_dir)
    processor.run()


if __name__ == "__main__":
    main()
