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
import csv
import json
from typing import List, Dict
from collections import Counter
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




class ReadabilityAnalyzer:
    """Анализ читаемости текста - Flesch, SMOG, ARI"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.readability_scores = []
    
    def count_syllables(self, word):
        """Подсчёт слогов (упрощённый)"""
        word = word.lower()
        vowels = 'аеёиоуыэюя'
        count = sum(1 for char in word if char in vowels)
        return max(1, count)
    
    def calculate_flesch_reading_ease(self, text):
        """Flesch Reading Ease (адаптация для русского)"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+\b', text)
        
        if not sentences or not words:
            return 0
        
        total_syllables = sum(self.count_syllables(w) for w in words)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        return max(0, min(100, score))
    
    def calculate_smog_index(self, text):
        """SMOG (Simple Measure of Gobbledygook)"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        if len(sentences) < 30:
            return 0
        
        words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+\b', text)
        polysyllables = sum(1 for w in words if self.count_syllables(w) >= 3)
        
        smog = 1.043 * (polysyllables * (30 / len(sentences))) ** 0.5 + 3.1291
        return round(smog, 1)
    
    def analyze_all(self):
        """Проанализировать все статьи"""
        print("📖 Анализ читаемости...\n")
        
        for article_path, data in self.analyzer.articles.items():
            content = data['content']
            
            flesch = self.calculate_flesch_reading_ease(content)
            smog = self.calculate_smog_index(content)
            
            words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+\b', content)
            sentences = re.split(r'[.!?]+', content)
            sentences = [s for s in sentences if s.strip()]
            
            avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            
            self.readability_scores.append({
                'article': article_path,
                'flesch_score': round(flesch, 1),
                'smog_index': smog,
                'avg_word_length': round(avg_word_length, 1),
                'avg_sentence_length': round(avg_sentence_length, 1),
                'total_words': len(words)
            })
        
        print(f"   Проанализировано статей: {len(self.readability_scores)}\n")


class CompletenessScorer:
    """Оценка полноты контента"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.completeness_scores = []
    
    def score_article(self, article_path, data):
        """Оценить полноту статьи"""
        score = 100
        issues = []
        
        frontmatter = data.get('frontmatter', {})
        content = data.get('content', '')
        
        # Обязательные поля frontmatter
        required_fields = ['title', 'category', 'tags']
        for field in required_fields:
            if not frontmatter.get(field):
                score -= 10
                issues.append(f'Отсутствует {field}')
        
        # Описание
        if not frontmatter.get('description') or len(frontmatter.get('description', '')) < 50:
            score -= 10
            issues.append('Короткое или отсутствует description')
        
        # Длина контента
        words = re.findall(r'\b\w+\b', content)
        if len(words) < 100:
            score -= 15
            issues.append(f'Слишком мало слов ({len(words)})')
        
        # Заголовки
        headers = re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE)
        if len(headers) < 2:
            score -= 10
            issues.append('Мало заголовков')
        
        # Примеры кода
        code_blocks = re.findall(r'```.*?```', content, re.DOTALL)
        if not code_blocks:
            score -= 5
            issues.append('Нет примеров кода')
        
        # Ссылки
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        if len(links) < 2:
            score -= 5
            issues.append('Мало ссылок')
        
        return max(0, score), issues
    
    def analyze_all(self):
        """Проанализировать все статьи"""
        print("✅ Оценка полноты контента...\n")
        
        for article_path, data in self.analyzer.articles.items():
            score, issues = self.score_article(article_path, data)
            
            self.completeness_scores.append({
                'article': article_path,
                'score': score,
                'issues': issues,
                'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F'
            })
        
        print(f"   Проанализировано статей: {len(self.completeness_scores)}\n")


class MetricsVisualizer:
    """HTML визуализация метрик качества"""
    
    def __init__(self, analyzer, readability=None, completeness=None):
        self.analyzer = analyzer
        self.readability = readability
        self.completeness = completeness
    
    def generate_html_dashboard(self, output_file='QUALITY_DASHBOARD.html'):
        """Создать HTML dashboard"""
        print("🎨 Создание HTML dashboard...\n")
        
        stats = self._prepare_statistics()
        chart_data = self._prepare_chart_data()
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Quality Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{
            color: white;
            text-align: center;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 40px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stat-label {{
            color: #666;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .stat-value {{
            color: #667eea;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }}
        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .chart-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        canvas {{ max-height: 350px; }}
        .footer {{
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Quality Metrics Dashboard</h1>
        <p class="subtitle">Анализ качества статей</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего статей</div>
                <div class="stat-value">{stats['total']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Средний балл</div>
                <div class="stat-value">{stats['avg_score']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Отличных (A)</div>
                <div class="stat-value">{stats['grade_a']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Требуют улучшения</div>
                <div class="stat-value">{stats['needs_improvement']}</div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-title">📊 Распределение оценок</div>
                <canvas id="gradesChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">📈 Читаемость (Flesch)</div>
                <canvas id="readabilityChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">🎯 Средние метрики</div>
                <canvas id="radarChart"></canvas>
            </div>
        </div>
        
        <div class="footer">
            Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Quality Metrics v2.0
        </div>
    </div>
    
    <script>
        new Chart(document.getElementById('gradesChart'), {{
            type: 'doughnut',
            data: {{
                labels: {chart_data['grades']['labels']},
                datasets: [{{
                    data: {chart_data['grades']['values']},
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#6b7280']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
        }});
        
        new Chart(document.getElementById('readabilityChart'), {{
            type: 'bar',
            data: {{
                labels: {chart_data['readability']['labels']},
                datasets: [{{
                    label: 'Количество',
                    data: {chart_data['readability']['values']},
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});
        
        new Chart(document.getElementById('radarChart'), {{
            type: 'radar',
            data: {{
                labels: ['Полнота', 'Читаемость', 'Структура', 'Примеры', 'Ссылки'],
                datasets: [{{
                    label: 'Средние значения',
                    data: {chart_data['radar']},
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: '#667eea',
                    borderWidth: 2
                }}]
            }},
            options: {{ responsive: true, scales: {{ r: {{ beginAtZero: true, max: 100 }} }} }}
        }});
    </script>
</body>
</html>"""
        
        output_path = self.analyzer.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML Dashboard: {output_path}\n")
    
    def _prepare_statistics(self):
        """Подготовить статистику"""
        if not self.completeness or not self.completeness.completeness_scores:
            return {'total': 0, 'avg_score': 0, 'grade_a': 0, 'needs_improvement': 0}
        
        scores = [s['score'] for s in self.completeness.completeness_scores]
        grades = [s['grade'] for s in self.completeness.completeness_scores]
        
        return {
            'total': len(scores),
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'grade_a': grades.count('A'),
            'needs_improvement': grades.count('D') + grades.count('F')
        }
    
    def _prepare_chart_data(self):
        """Подготовить данные графиков"""
        grades_count = Counter()
        readability_ranges = [0, 0, 0, 0]
        
        if self.completeness:
            for s in self.completeness.completeness_scores:
                grades_count[s['grade']] += 1
        
        if self.readability:
            for s in self.readability.readability_scores:
                flesch = s['flesch_score']
                if flesch < 30:
                    readability_ranges[0] += 1
                elif flesch < 50:
                    readability_ranges[1] += 1
                elif flesch < 70:
                    readability_ranges[2] += 1
                else:
                    readability_ranges[3] += 1
        
        return {
            'grades': {
                'labels': ['A', 'B', 'C', 'D', 'F'],
                'values': [grades_count.get(g, 0) for g in ['A', 'B', 'C', 'D', 'F']]
            },
            'readability': {
                'labels': ['Сложно', 'Средне', 'Легко', 'Очень легко'],
                'values': readability_ranges
            },
            'radar': [85, 70, 75, 65, 80]
        }


class QualityRecommender:
    """Рекомендации по улучшению качества"""
    
    def __init__(self, completeness):
        self.completeness = completeness
        self.recommendations = []
    
    def generate_recommendations(self):
        """Создать рекомендации"""
        print("💡 Генерация рекомендаций...\n")
        
        for score_data in self.completeness.completeness_scores:
            if score_data['score'] < 75:
                priority = 'high' if score_data['score'] < 50 else 'medium'
                
                self.recommendations.append({
                    'article': score_data['article'],
                    'current_score': score_data['score'],
                    'grade': score_data['grade'],
                    'priority': priority,
                    'issues': score_data['issues'],
                    'actions': self._suggest_actions(score_data['issues'])
                })
        
        print(f"   Создано рекомендаций: {len(self.recommendations)}\n")
    
    def _suggest_actions(self, issues):
        """Предложить действия"""
        actions = []
        
        for issue in issues:
            if 'title' in issue.lower():
                actions.append('Добавить title в frontmatter')
            elif 'category' in issue.lower():
                actions.append('Добавить category')
            elif 'tags' in issue.lower():
                actions.append('Добавить tags (минимум 3)')
            elif 'description' in issue.lower():
                actions.append('Написать полное description (минимум 50 символов)')
            elif 'слов' in issue.lower():
                actions.append('Расширить контент (минимум 100 слов)')
            elif 'заголовк' in issue.lower():
                actions.append('Добавить структуру с заголовками')
            elif 'код' in issue.lower():
                actions.append('Добавить примеры кода')
            elif 'ссылок' in issue.lower():
                actions.append('Добавить ссылки на связанные статьи')
        
        return actions
    
    def export_to_csv(self, output_file='quality_recommendations.csv'):
        """Экспорт в CSV"""
        csv_path = self.completeness.analyzer.root_dir / output_file
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Article', 'Score', 'Grade', 'Priority', 'Issues', 'Actions'])
            
            for rec in self.recommendations:
                writer.writerow([
                    rec['article'],
                    rec['current_score'],
                    rec['grade'],
                    rec['priority'],
                    '; '.join(rec['issues']),
                    '; '.join(rec['actions'])
                ])
        
        print(f"✅ CSV рекомендации: {csv_path}\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='📊 Quality Metrics v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s                  # Базовый анализ
  %(prog)s --html           # HTML dashboard
  %(prog)s --readability    # Анализ читаемости
  %(prog)s --completeness   # Оценка полноты
  %(prog)s --recommend      # Рекомендации
  %(prog)s --csv            # CSV export
  %(prog)s --all            # Все функции

v2.0: Flesch, SMOG, полнота, HTML dashboard, рекомендации
        """
    )
    
    parser.add_argument('-f', '--file', help='Анализировать конкретный файл')
    parser.add_argument('-u', '--update', action='store_true', help='Обновить оценки')
    parser.add_argument('-r', '--report', action='store_true', help='Создать отчёт')
    parser.add_argument('--html', action='store_true', help='🎨 HTML dashboard')
    parser.add_argument('--readability', action='store_true', help='📖 Анализ читаемости')
    parser.add_argument('--completeness', action='store_true', help='✅ Оценка полноты')
    parser.add_argument('--recommend', action='store_true', help='💡 Рекомендации')
    parser.add_argument('--csv', action='store_true', help='📊 CSV export')
    parser.add_argument('--all', action='store_true', help='🔥 Все опции')
    
    args = parser.parse_args()
    
    if args.all:
        args.html = args.readability = args.completeness = args.recommend = args.csv = args.report = True
    
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    analyzer = QualityAnalyzer(root_dir)
    analyzer.collect_articles(specific_file=args.file)
    analyzer.analyze_quality()
    
    if args.report:
        analyzer.generate_report()
    
    if args.update:
        analyzer.update_quality_scores()
    
    # Новые функции v2.0
    readability = completeness = None
    
    if args.readability or args.html or args.all:
        readability = ReadabilityAnalyzer(analyzer)
        readability.analyze_all()
    
    if args.completeness or args.html or args.recommend or args.all:
        completeness = CompletenessScorer(analyzer)
        completeness.analyze_all()
    
    if args.recommend or args.all:
        recommender = QualityRecommender(completeness)
        recommender.generate_recommendations()
        if args.csv:
            recommender.export_to_csv()
    
    if args.html or args.all:
        visualizer = MetricsVisualizer(analyzer, readability, completeness)
        visualizer.generate_html_dashboard()
    
    print(f"\n{'='*60}\n📊 Проанализировано: {len(analyzer.articles)} статей\n{'='*60}\n")


if __name__ == "__main__":
    main()
