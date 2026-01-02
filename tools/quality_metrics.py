#!/usr/bin/env python3
"""
Quality Metrics - Метрики качества статей
Оценивает качество статей по множеству критериев

Метрики:
- Completeness (полнота): наличие всех обязательных полей
- Structure (структура): заголовки, параграфы, списки
- Links (ссылки): внутренние и внешние ссылки
- Examples (примеры): код, таблицы, изображения
- Readability (читаемость): длина предложений, сложность
- Freshness (свежесть): дата последнего обновления
"""

from pathlib import Path
import yaml
import re
from datetime import datetime, timedelta
from collections import defaultdict


class QualityAnalyzer:
    """
    Анализатор качества статей
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Обязательные поля в frontmatter
        self.required_fields = ['title', 'date', 'category', 'tags', 'status']

        # Рекомендуемые поля
        self.recommended_fields = ['author', 'source', 'subcategory', 'related']

    def extract_frontmatter_and_content(self, file_path):
        """Извлечь frontmatter и содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                body = match.group(2)
                return fm, body
        except:
            pass

        return None, None

    def analyze_completeness(self, frontmatter):
        """
        Оценить полноту метаданных (0-100)
        """
        if not frontmatter:
            return 0

        score = 0
        total_points = 100

        # Обязательные поля (60 баллов)
        required_points = 60
        field_points = required_points / len(self.required_fields)

        for field in self.required_fields:
            if field in frontmatter and frontmatter[field]:
                score += field_points

        # Рекомендуемые поля (30 баллов)
        recommended_points = 30
        field_points = recommended_points / len(self.recommended_fields)

        for field in self.recommended_fields:
            if field in frontmatter and frontmatter[field]:
                score += field_points

        # Дополнительные метаданные (10 баллов)
        bonus_fields = ['dewey', 'pagerank', 'reading_time', 'difficulty']
        bonus_count = sum(1 for f in bonus_fields if f in frontmatter)
        score += min(10, bonus_count * 2.5)

        return min(100, round(score))

    def analyze_structure(self, content):
        """
        Оценить структуру документа (0-100)
        """
        if not content:
            return 0

        score = 0

        # Заголовки (30 баллов)
        h1_count = len(re.findall(r'^# ', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))

        # Хорошо: нет h1 (он в заголовке), есть h2 и h3
        if h1_count == 0 and h2_count >= 2:
            score += 30
        elif h2_count >= 1:
            score += 15

        # Списки (20 баллов)
        lists = re.findall(r'^\s*[\*\-\+] ', content, re.MULTILINE)
        if len(lists) >= 5:
            score += 20
        elif len(lists) >= 2:
            score += 10

        # Параграфы (разумная длина) (20 баллов)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            avg_para_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            # Оптимально: 40-100 слов в параграфе
            if 40 <= avg_para_length <= 100:
                score += 20
            elif 20 <= avg_para_length <= 150:
                score += 10

        # Таблицы (15 баллов)
        tables = re.findall(r'^\|', content, re.MULTILINE)
        if tables:
            score += 15

        # Цитаты (15 баллов)
        quotes = re.findall(r'^> ', content, re.MULTILINE)
        if quotes:
            score += 15

        return min(100, score)

    def analyze_links(self, content):
        """
        Оценить качество ссылок (0-100)
        """
        if not content:
            return 0

        score = 0

        # Внутренние ссылки (40 баллов)
        internal_links = re.findall(r'\[([^\]]+)\]\(([^h][^\)]+)\)', content)
        if len(internal_links) >= 3:
            score += 40
        elif len(internal_links) >= 1:
            score += 20

        # Внешние ссылки (30 баллов)
        external_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
        if len(external_links) >= 2:
            score += 30
        elif len(external_links) >= 1:
            score += 15

        # Якорные ссылки (15 баллов)
        anchors = re.findall(r'\[([^\]]+)\]\(#[^\)]+\)', content)
        if anchors:
            score += 15

        # Ссылки на изображения (15 баллов)
        images = re.findall(r'!\[([^\]]*)\]\([^\)]+\)', content)
        if images:
            score += 15

        return min(100, score)

    def analyze_examples(self, content):
        """
        Оценить наличие примеров и иллюстраций (0-100)
        """
        if not content:
            return 0

        score = 0

        # Блоки кода (50 баллов)
        code_blocks = re.findall(r'```.*?```', content, re.DOTALL)
        if len(code_blocks) >= 3:
            score += 50
        elif len(code_blocks) >= 1:
            score += 25

        # Инлайн код (20 баллов)
        inline_code = re.findall(r'`[^`]+`', content)
        if len(inline_code) >= 5:
            score += 20
        elif len(inline_code) >= 2:
            score += 10

        # Таблицы (15 баллов)
        tables = len(re.findall(r'\|.*\|', content))
        if tables >= 3:
            score += 15
        elif tables >= 1:
            score += 7

        # Изображения (15 баллов)
        images = re.findall(r'!\[', content)
        if images:
            score += 15

        return min(100, score)

    def analyze_readability(self, content):
        """
        Оценить читаемость (0-100)
        """
        if not content:
            return 0

        score = 50  # Базовый балл

        # Удалить код и ссылки для анализа
        text = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Предложения
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            # Средняя длина предложения (слов)
            words_per_sentence = []
            for sent in sentences:
                words = re.findall(r'\b[а-яёa-z]+\b', sent.lower())
                words_per_sentence.append(len(words))

            if words_per_sentence:
                avg_words = sum(words_per_sentence) / len(words_per_sentence)

                # Оптимально: 15-25 слов в предложении
                if 15 <= avg_words <= 25:
                    score += 30
                elif 10 <= avg_words <= 30:
                    score += 15
                else:
                    # Штраф за слишком длинные или короткие
                    score -= 10

        # Разнообразие (разные слова vs общее количество)
        words = re.findall(r'\b[а-яёa-z]+\b', text.lower())
        if words:
            unique_ratio = len(set(words)) / len(words)
            # Чем выше разнообразие, тем лучше
            score += int(unique_ratio * 20)

        return min(100, max(0, score))

    def analyze_freshness(self, frontmatter):
        """
        Оценить свежесть статьи (0-100)
        """
        if not frontmatter or 'date' not in frontmatter:
            return 0

        try:
            # Парсинг даты
            date_str = str(frontmatter['date'])
            if isinstance(frontmatter['date'], datetime):
                article_date = frontmatter['date']
            else:
                article_date = datetime.fromisoformat(date_str.split()[0])

            now = datetime.now()
            age = (now - article_date).days

            # Чем новее, тем лучше
            if age <= 30:  # Месяц
                return 100
            elif age <= 90:  # 3 месяца
                return 90
            elif age <= 180:  # 6 месяцев
                return 75
            elif age <= 365:  # Год
                return 60
            elif age <= 730:  # 2 года
                return 40
            else:
                return 20

        except:
            return 50  # Неизвестно

    def calculate_overall_score(self, metrics):
        """
        Вычислить общий балл качества

        Веса:
        - Completeness: 20%
        - Structure: 20%
        - Links: 15%
        - Examples: 15%
        - Readability: 20%
        - Freshness: 10%
        """
        weights = {
            'completeness': 0.20,
            'structure': 0.20,
            'links': 0.15,
            'examples': 0.15,
            'readability': 0.20,
            'freshness': 0.10
        }

        score = sum(metrics[key] * weights[key] for key in weights.keys())

        return round(score)

    def analyze_article(self, file_path):
        """Полный анализ статьи"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        metrics = {
            'completeness': self.analyze_completeness(frontmatter),
            'structure': self.analyze_structure(content),
            'links': self.analyze_links(content),
            'examples': self.analyze_examples(content),
            'readability': self.analyze_readability(content),
            'freshness': self.analyze_freshness(frontmatter)
        }

        overall = self.calculate_overall_score(metrics)

        # Определить уровень качества
        if overall >= 90:
            grade = 'A+'
            quality = 'Excellent'
        elif overall >= 80:
            grade = 'A'
            quality = 'Very Good'
        elif overall >= 70:
            grade = 'B'
            quality = 'Good'
        elif overall >= 60:
            grade = 'C'
            quality = 'Satisfactory'
        elif overall >= 50:
            grade = 'D'
            quality = 'Needs Improvement'
        else:
            grade = 'F'
            quality = 'Poor'

        return {
            **metrics,
            'overall': overall,
            'grade': grade,
            'quality': quality,
            'file': str(file_path.relative_to(self.root_dir)),
            'title': frontmatter.get('title', file_path.stem) if frontmatter else file_path.stem
        }

    def add_quality_scores_to_articles(self):
        """Добавить оценки качества ко всем статьям"""
        print("📊 Анализ качества статей...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            analysis = self.analyze_article(md_file)

            # Обновить frontmatter
            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not frontmatter:
                continue

            # Добавить метрики
            frontmatter['quality_score'] = analysis['overall']
            frontmatter['quality_grade'] = analysis['grade']
            frontmatter['quality_metrics'] = {
                'completeness': analysis['completeness'],
                'structure': analysis['structure'],
                'links': analysis['links'],
                'examples': analysis['examples'],
                'readability': analysis['readability'],
                'freshness': analysis['freshness']
            }

            # Записать обратно
            try:
                new_content = "---\n"
                new_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += content

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                count += 1
                print(f"✅ {md_file.relative_to(self.root_dir)} — {analysis['grade']} ({analysis['overall']}/100)")

            except Exception as e:
                print(f"⚠️  Ошибка в {md_file}: {e}")

        print(f"\n✅ Проанализировано статей: {count}")

    def generate_report(self):
        """Создать отчёт по качеству"""
        print("\n📊 Генерация отчёта по качеству...\n")

        articles = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            analysis = self.analyze_article(md_file)
            articles.append(analysis)

        lines = []
        lines.append("# 📊 Отчёт: Качество статей\n\n")

        # Статистика
        if articles:
            avg_score = sum(a['overall'] for a in articles) / len(articles)

            lines.append("## Общая статистика\n\n")
            lines.append(f"- **Всего статей**: {len(articles)}\n")
            lines.append(f"- **Средний балл**: {avg_score:.1f}/100\n\n")

            # По оценкам
            by_grade = defaultdict(int)
            for article in articles:
                by_grade[article['grade']] += 1

            lines.append("## Распределение по оценкам\n\n")
            for grade in ['A+', 'A', 'B', 'C', 'D', 'F']:
                count = by_grade.get(grade, 0)
                pct = (count / len(articles)) * 100 if articles else 0
                bar = '█' * int(pct / 5)
                lines.append(f"- **{grade}**: {count} ({pct:.1f}%) {bar}\n")

            # Топ статей
            lines.append("\n## Топ-10 лучших статей\n\n")
            sorted_articles = sorted(articles, key=lambda x: x['overall'], reverse=True)

            for i, article in enumerate(sorted_articles[:10], 1):
                lines.append(f"### {i}. {article['title']} — {article['grade']} ({article['overall']}/100)\n\n")
                lines.append(f"📂 `{article['file']}`\n\n")
                lines.append("**Метрики:**\n")
                lines.append(f"- Полнота: {article['completeness']}/100\n")
                lines.append(f"- Структура: {article['structure']}/100\n")
                lines.append(f"- Ссылки: {article['links']}/100\n")
                lines.append(f"- Примеры: {article['examples']}/100\n")
                lines.append(f"- Читаемость: {article['readability']}/100\n")
                lines.append(f"- Свежесть: {article['freshness']}/100\n\n")

            # Статьи требующие улучшения
            lines.append("\n## Статьи, требующие улучшения\n\n")
            needs_improvement = [a for a in sorted_articles if a['overall'] < 70]

            if needs_improvement:
                for article in needs_improvement[-10:]:
                    lines.append(f"### {article['title']} — {article['grade']} ({article['overall']}/100)\n\n")
                    lines.append(f"📂 `{article['file']}`\n\n")

                    # Рекомендации
                    lines.append("**Рекомендации по улучшению:**\n\n")
                    if article['completeness'] < 70:
                        lines.append("- ⚠️  Дополнить метаданные (tags, author, related)\n")
                    if article['structure'] < 70:
                        lines.append("- ⚠️  Улучшить структуру (добавить заголовки, списки)\n")
                    if article['links'] < 70:
                        lines.append("- ⚠️  Добавить ссылки на связанные статьи\n")
                    if article['examples'] < 70:
                        lines.append("- ⚠️  Добавить примеры кода или иллюстрации\n")
                    if article['readability'] < 70:
                        lines.append("- ⚠️  Улучшить читаемость (упростить предложения)\n")
                    if article['freshness'] < 70:
                        lines.append("- ⚠️  Обновить устаревшую информацию\n")

                    lines.append("\n")
            else:
                lines.append("Все статьи имеют хорошее качество! 🎉\n\n")

        return ''.join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Quality Metrics - Анализ качества статей'
    )

    parser.add_argument(
        '-f', '--file',
        help='Анализировать конкретный файл'
    )

    parser.add_argument(
        '-u', '--update',
        action='store_true',
        help='Обновить оценки качества во всех статьях'
    )

    parser.add_argument(
        '-r', '--report',
        action='store_true',
        help='Создать отчёт'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    analyzer = QualityAnalyzer(root_dir)

    if args.file:
        file_path = root_dir / args.file
        analysis = analyzer.analyze_article(file_path)

        print(f"\n📊 Анализ качества: {analysis['title']}\n")
        print(f"   Общий балл: {analysis['overall']}/100 ({analysis['grade']} - {analysis['quality']})\n")
        print("   Детали:")
        print(f"      Полнота метаданных: {analysis['completeness']}/100")
        print(f"      Структура: {analysis['structure']}/100")
        print(f"      Ссылки: {analysis['links']}/100")
        print(f"      Примеры: {analysis['examples']}/100")
        print(f"      Читаемость: {analysis['readability']}/100")
        print(f"      Свежесть: {analysis['freshness']}/100\n")

    elif args.update:
        analyzer.add_quality_scores_to_articles()

    elif args.report:
        report = analyzer.generate_report()
        output_file = root_dir / "QUALITY_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
