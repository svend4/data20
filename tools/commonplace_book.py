#!/usr/bin/env python3
"""
Commonplace Book - Книга выписок
Извлекает ключевые цитаты, важные мысли и памятные отрывки

Вдохновлено: Renaissance commonplace books (15-17 века)
Традиция: John Locke, Marcus Aurelius, Thomas Jefferson

Features:
- Smart pattern matching для извлечения
- Sentiment analysis (positive/negative/neutral)
- Ranking по важности
- Spaced repetition для повторения
- HTML visualization
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import argparse
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import hashlib


class SentimentAnalyzer:
    """Простой анализатор тональности"""

    POSITIVE_WORDS = {'хорошо', 'отлично', 'прекрасно', 'успешно', 'эффективно', 'полезно',
                      'важно', 'ценно', 'преимущество', 'улучшение', 'развитие'}
    NEGATIVE_WORDS = {'плохо', 'ошибка', 'проблема', 'недостаток', 'сложность', 'риск',
                      'опасность', 'угроза', 'слабость', 'недочёт'}

    @staticmethod
    def analyze(text: str) -> str:
        """
        Определить тональность текста
        Returns: 'positive', 'negative', 'neutral'
        """
        words = set(text.lower().split())

        positive_count = len(words & SentimentAnalyzer.POSITIVE_WORDS)
        negative_count = len(words & SentimentAnalyzer.NEGATIVE_WORDS)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'


class ExcerptRanker:
    """Ранжирование выписок по важности"""

    @staticmethod
    def calculate_importance(excerpt: Dict) -> float:
        """
        Вычислить важность выписки (0-1)

        Факторы:
        - Длина (оптимум 50-200 символов)
        - Тип (quote > principle > key_idea > important > definition > example)
        - Sentiment (positive/neutral > negative)
        """
        score = 0.0
        text = excerpt['text']

        # Length score (optimal 50-200 chars)
        length = len(text)
        if 50 <= length <= 200:
            score += 0.4
        elif 30 <= length <= 300:
            score += 0.2

        # Type score
        type_scores = {
            'quote': 0.3,
            'principle': 0.25,
            'key_idea': 0.2,
            'important': 0.15,
            'definition': 0.1,
            'example': 0.05
        }
        score += type_scores.get(excerpt.get('type', 'quote'), 0.1)

        # Sentiment score
        sentiment = excerpt.get('sentiment', 'neutral')
        if sentiment == 'positive':
            score += 0.2
        elif sentiment == 'neutral':
            score += 0.1

        # Has tags bonus
        if excerpt.get('tags'):
            score += 0.1

        return min(score, 1.0)


class SpacedRepetitionScheduler:
    """Система интервальных повторений (Spaced Repetition)"""

    INTERVALS = [1, 3, 7, 14, 30, 60, 120]  # days

    def __init__(self):
        self.review_schedule = {}

    def schedule_excerpt(self, excerpt_id: str, level: int = 0) -> datetime:
        """
        Запланировать следующее повторение

        level: текущий уровень (0-6)
        Returns: дата следующего повторения
        """
        if level >= len(self.INTERVALS):
            level = len(self.INTERVALS) - 1

        days = self.INTERVALS[level]
        next_review = datetime.now() + timedelta(days=days)

        self.review_schedule[excerpt_id] = {
            'level': level,
            'next_review': next_review,
            'last_reviewed': datetime.now()
        }

        return next_review

    def get_due_excerpts(self, all_excerpts: List[Dict]) -> List[Dict]:
        """Получить выписки, которые пора повторить"""
        now = datetime.now()
        due = []

        for excerpt in all_excerpts:
            excerpt_id = excerpt.get('id', '')
            schedule = self.review_schedule.get(excerpt_id)

            if schedule and schedule['next_review'] <= now:
                excerpt['review_info'] = schedule
                due.append(excerpt)

        return due


class CommonplaceBookBuilder:
    """Построитель книги выписок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Выписки по категориям
        self.excerpts = defaultdict(list)

        # Статистика
        self.total_excerpts = 0

        # Analyzers
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ranker = ExcerptRanker()
        self.scheduler = SpacedRepetitionScheduler()

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

    def extract_excerpts(self, content, source_file):
        """Извлечь выписки из контента"""
        excerpts = []

        # 1. Блочные цитаты (> текст)
        blockquotes = re.findall(r'^>\s+(.+)$', content, re.MULTILINE)
        for quote in blockquotes:
            if len(quote) > 20:  # Минимальная длина
                excerpts.append({
                    'text': quote.strip(),
                    'type': 'quote',
                    'source': source_file
                })

        # 2. Выделенный текст (**важно**, *важно*)
        important = re.findall(r'\*\*([^*]{20,}?)\*\*', content)
        for text in important:
            # Исключить заголовки
            if not text.isupper() and ':' not in text[:20]:
                excerpts.append({
                    'text': text.strip(),
                    'type': 'important',
                    'source': source_file
                })

        # 3. Ключевые фразы (паттерны)
        key_patterns = [
            r'Важно понимать[,:]\s*(.{30,200}?)[.!]',
            r'Ключевая идея[,:]\s*(.{30,200}?)[.!]',
            r'Главное[,:]\s*(.{30,200}?)[.!]',
            r'Необходимо помнить[,:]\s*(.{30,200}?)[.!]',
            r'Следует отметить[,:]\s*(.{30,200}?)[.!]'
        ]

        for pattern in key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                excerpts.append({
                    'text': match.strip(),
                    'type': 'key_idea',
                    'source': source_file
                })

        # 4. Списки принципов/правил
        principle_patterns = [
            r'^[-*]\s+\*\*(.+?)\*\*\s*[-—–]\s*(.+)$',
            r'^\d+\.\s+\*\*(.+?)\*\*\s*[-—–]\s*(.+)$'
        ]

        for pattern in principle_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for title, description in matches:
                if len(description) > 20:
                    excerpts.append({
                        'text': f"{title}: {description}",
                        'type': 'principle',
                        'source': source_file
                    })

        # 5. Определения терминов
        definitions = re.findall(r'\*\*([А-ЯA-Z][^*]+?)\*\*\s*[-—–]\s*([^.\n]{20,200}?)[.]', content)
        for term, definition in definitions:
            excerpts.append({
                'text': f"{term} — {definition}",
                'type': 'definition',
                'source': source_file
            })

        # 6. Примеры (Example:, Пример:)
        examples = re.findall(r'(?:Example|Пример)[:\s]+(.{50,300}?)(?:\n\n|\n(?=[A-ZА-Я]))', content, re.IGNORECASE)
        for example in examples:
            excerpts.append({
                'text': example.strip(),
                'type': 'example',
                'source': source_file
            })

        return excerpts

    def build_commonplace_book(self):
        """Построить книгу выписок"""
        print("📖 Построение книги выписок...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem
            category = frontmatter.get('category', 'Общее') if frontmatter else 'Общее'
            tags = frontmatter.get('tags', []) if frontmatter else []

            # Извлечь выписки
            excerpts = self.extract_excerpts(content, article_path)

            for excerpt in excerpts:
                excerpt['article_title'] = title
                excerpt['category'] = category
                excerpt['tags'] = tags

                # Generate ID
                excerpt_text = excerpt['text']
                excerpt['id'] = hashlib.md5(excerpt_text.encode()).hexdigest()[:12]

                # Sentiment analysis
                excerpt['sentiment'] = self.sentiment_analyzer.analyze(excerpt_text)

                # Calculate importance
                excerpt['importance'] = self.ranker.calculate_importance(excerpt)

                # Schedule for spaced repetition
                self.scheduler.schedule_excerpt(excerpt['id'], level=0)

                # Группировать по категориям
                self.excerpts[category].append(excerpt)
                self.total_excerpts += 1

        print(f"   Выписок собрано: {self.total_excerpts}")
        print(f"   Категорий: {len(self.excerpts)}\n")

    def generate_report(self):
        """Создать книгу выписок"""
        lines = []
        lines.append("# 📖 Commonplace Book — Книга выписок\n\n")
        lines.append("> Собрание ключевых мыслей, цитат и идей из базы знаний\n\n")
        lines.append("*Вдохновлено традицией Renaissance commonplace books*\n\n")

        # Статистика
        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего выписок**: {self.total_excerpts}\n")
        lines.append(f"- **Категорий**: {len(self.excerpts)}\n\n")

        # Типы выписок
        type_counts = defaultdict(int)
        for category_excerpts in self.excerpts.values():
            for excerpt in category_excerpts:
                type_counts[excerpt['type']] += 1

        lines.append("**По типам:**\n\n")
        type_names = {
            'quote': 'Цитаты',
            'important': 'Важные мысли',
            'key_idea': 'Ключевые идеи',
            'principle': 'Принципы',
            'definition': 'Определения',
            'example': 'Примеры'
        }

        for excerpt_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            name = type_names.get(excerpt_type, excerpt_type)
            lines.append(f"- **{name}**: {count}\n")

        lines.append("\n---\n\n")

        # Выписки по категориям
        for category in sorted(self.excerpts.keys()):
            excerpts = self.excerpts[category]

            lines.append(f"## {category}\n\n")
            lines.append(f"*{len(excerpts)} выписок*\n\n")

            # Группировать по типам
            by_type = defaultdict(list)
            for excerpt in excerpts:
                by_type[excerpt['type']].append(excerpt)

            for excerpt_type in ['quote', 'key_idea', 'important', 'principle', 'definition', 'example']:
                if excerpt_type not in by_type:
                    continue

                type_name = type_names.get(excerpt_type, excerpt_type)
                lines.append(f"### {type_name}\n\n")

                for excerpt in by_type[excerpt_type][:10]:  # Топ-10 по типу
                    lines.append(f"> {excerpt['text']}\n\n")
                    lines.append(f"— *[{excerpt['article_title']}]({excerpt['source']})*\n\n")

                if len(by_type[excerpt_type]) > 10:
                    lines.append(f"*...и ещё {len(by_type[excerpt_type]) - 10}*\n\n")

            lines.append("\n")

        output_file = self.root_dir / "COMMONPLACE_BOOK.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Книга выписок: {output_file}")

    def generate_by_topic(self):
        """Создать указатель по темам"""
        lines = []
        lines.append("# 📚 Выписки по темам\n\n")

        # Собрать все теги
        all_tags = defaultdict(list)

        for category_excerpts in self.excerpts.values():
            for excerpt in category_excerpts:
                for tag in excerpt['tags']:
                    all_tags[tag].append(excerpt)

        # Вывести по тегам
        for tag in sorted(all_tags.keys()):
            excerpts = all_tags[tag]

            lines.append(f"## {tag}\n\n")
            lines.append(f"*{len(excerpts)} выписок*\n\n")

            for excerpt in excerpts[:15]:
                lines.append(f"> {excerpt['text'][:150]}{'...' if len(excerpt['text']) > 150 else ''}\n\n")
                lines.append(f"— *[{excerpt['article_title']}]({excerpt['source']})*\n\n")

            if len(excerpts) > 15:
                lines.append(f"*...и ещё {len(excerpts) - 15}*\n\n")

            lines.append("\n")

        output_file = self.root_dir / "EXCERPTS_BY_TOPIC.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Выписки по темам: {output_file}")

    def save_json(self):
        """Сохранить выписки в JSON"""
        data = {
            'total': self.total_excerpts,
            'categories': {}
        }

        for category, excerpts in self.excerpts.items():
            data['categories'][category] = [
                {
                    'text': e['text'],
                    'type': e['type'],
                    'source': e['source'],
                    'article_title': e['article_title'],
                    'tags': e['tags']
                }
                for e in excerpts
            ]

        output_file = self.root_dir / "commonplace_book.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")

    def generate_top_excerpts(self, limit: int = 50):
        """Создать топ выписок по важности"""
        all_excerpts = []
        for category_excerpts in self.excerpts.values():
            all_excerpts.extend(category_excerpts)

        # Sort by importance
        all_excerpts.sort(key=lambda x: x.get('importance', 0), reverse=True)

        lines = []
        lines.append("# 🌟 Топ выписок по важности\n\n")

        for i, excerpt in enumerate(all_excerpts[:limit], 1):
            importance = excerpt.get('importance', 0)
            sentiment = excerpt.get('sentiment', 'neutral')

            sentiment_emoji = {'positive': '😊', 'negative': '😟', 'neutral': '😐'}
            emoji = sentiment_emoji.get(sentiment, '😐')

            lines.append(f"## {i}. {emoji} [{excerpt['article_title']}]({excerpt['source']})\n\n")
            lines.append(f"> {excerpt['text']}\n\n")
            lines.append(f"**Важность**: {importance:.2f} | **Тип**: {excerpt['type']} | **Тональность**: {sentiment}\n\n")

        output_file = self.root_dir / "TOP_EXCERPTS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Топ выписок: {output_file}")

    def generate_html_visualization(self):
        """Создать HTML визуализацию"""
        all_excerpts = []
        for category_excerpts in self.excerpts.values():
            all_excerpts.extend(category_excerpts)

        all_excerpts.sort(key=lambda x: x.get('importance', 0), reverse=True)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Commonplace Book</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Georgia', serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f9f7f4; }}
        h1 {{ color: #5a4a42; border-bottom: 3px solid #8b7355; padding-bottom: 10px; }}
        .excerpt {{ background: white; padding: 20px; margin: 20px 0; border-left: 4px solid #8b7355; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .excerpt-text {{ font-size: 1.1em; line-height: 1.6; color: #333; font-style: italic; margin: 15px 0; }}
        .excerpt-meta {{ font-size: 0.9em; color: #666; }}
        .importance-bar {{ height: 6px; background: #ddd; margin: 10px 0; }}
        .importance-fill {{ height: 100%; background: linear-gradient(90deg, #8b7355, #d4a574); }}
        .sentiment-positive {{ border-left-color: #4caf50; }}
        .sentiment-negative {{ border-left-color: #f44336; }}
        .sentiment-neutral {{ border-left-color: #8b7355; }}
    </style>
</head>
<body>
    <h1>📖 Commonplace Book</h1>
    <p><em>Собрание {len(all_excerpts)} ценных мыслей из базы знаний</em></p>
"""

        for i, excerpt in enumerate(all_excerpts[:100], 1):
            importance = excerpt.get('importance', 0) * 100
            sentiment = excerpt.get('sentiment', 'neutral')

            html += f"""
    <div class="excerpt sentiment-{sentiment}">
        <div class="excerpt-text">"{excerpt['text']}"</div>
        <div class="excerpt-meta">
            — <strong>{excerpt['article_title']}</strong> • {excerpt['type']}
        </div>
        <div class="importance-bar">
            <div class="importance-fill" style="width: {importance}%"></div>
        </div>
    </div>
"""

        html += """
</body>
</html>"""

        output_file = self.root_dir / "commonplace_book.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML визуализация: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Commonplace Book - Книга выписок',
        epilog="""
Примеры:
  %(prog)s                  # Полная генерация
  %(prog)s --top 50         # Топ-50 по важности
  %(prog)s --html           # HTML визуализация
  %(prog)s --sentiment      # Статистика по тональности
        """
    )

    parser.add_argument('--top', type=int, metavar='N',
                       help='Создать топ-N выписок по важности')
    parser.add_argument('--html', action='store_true',
                       help='Создать HTML визуализацию')
    parser.add_argument('--sentiment', action='store_true',
                       help='Показать статистику по тональности')
    parser.add_argument('--by-topic', action='store_true',
                       help='Группировать по темам')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = CommonplaceBookBuilder(root_dir)
    builder.build_commonplace_book()

    if args.sentiment:
        print("\n📊 Статистика по тональности:\n")
        sentiment_counts = Counter()
        for category_excerpts in builder.excerpts.values():
            for excerpt in category_excerpts:
                sentiment_counts[excerpt.get('sentiment', 'neutral')] += 1

        total = sum(sentiment_counts.values())
        for sentiment, count in sentiment_counts.most_common():
            percent = (count / total * 100) if total > 0 else 0
            emoji = {'positive': '😊', 'negative': '😟', 'neutral': '😐'}
            print(f"{emoji.get(sentiment, '😐')} {sentiment}: {count} ({percent:.1f}%)")
        print()

    if args.top:
        builder.generate_top_excerpts(limit=args.top)

    if args.html:
        builder.generate_html_visualization()

    if args.by_topic:
        builder.generate_by_topic()

    if not any([args.top, args.html, args.sentiment, args.by_topic]):
        # По умолчанию - полная генерация
        builder.generate_report()
        builder.generate_by_topic()
        builder.generate_top_excerpts()
        builder.generate_html_visualization()
        builder.save_json()


if __name__ == "__main__":
    main()
