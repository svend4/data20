#!/usr/bin/env python3
"""
Reading Time Calculator - Оценка времени чтения
Вычисляет примерное время, необходимое для чтения статьи

На основе исследований:
- Средняя скорость чтения: 200-250 слов/минута (русский язык)
- Технические тексты: 150-200 слов/минута
- Код: считается медленнее (примерно 50 строк/минута)
"""

from pathlib import Path
import yaml
import re
import math
import argparse
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import json


class ReadingSpeedAnalyzer:
    """
    Анализатор скорости чтения
    Вычисляет различные метрики скорости для разных типов контента
    """

    def __init__(self, base_wpm=200):
        self.base_wpm = base_wpm

    def calculate_adjusted_wpm(self, content_type: str, complexity: float = 1.0) -> int:
        """
        Вычислить скорректированную скорость чтения

        Args:
            content_type: тип контента (technical, narrative, reference, etc.)
            complexity: коэффициент сложности (0.5 - простой, 2.0 - очень сложный)
        """
        base_adjustments = {
            'technical': 0.65,      # Технические тексты - медленнее
            'programming': 0.60,     # Код и программирование - еще медленнее
            'academic': 0.70,        # Научные статьи
            'narrative': 1.0,        # Обычные тексты
            'reference': 0.80,       # Справочные материалы
            'tutorial': 0.75,        # Обучающие материалы
        }

        adjustment = base_adjustments.get(content_type, 1.0)

        # Применить коэффициент сложности
        final_adjustment = adjustment / complexity

        return int(self.base_wpm * final_adjustment)

    def estimate_comprehension_time(self, words: int, wpm: int, comprehension_level: float = 0.8) -> float:
        """
        Оценить время с учетом понимания

        Args:
            words: количество слов
            wpm: слов в минуту
            comprehension_level: уровень понимания (0.5 - поверхностное, 1.0 - глубокое)
        """
        base_time = words / wpm if wpm > 0 else 0

        # Глубокое понимание требует больше времени
        comprehension_multiplier = 0.5 + (comprehension_level * 0.5)

        return base_time * comprehension_multiplier

    def calculate_reading_fatigue(self, total_minutes: float) -> Dict[str, any]:
        """
        Вычислить влияние усталости при чтении

        Исследования показывают, что после 20-30 минут непрерывного чтения
        скорость снижается на 10-15%
        """
        if total_minutes <= 20:
            fatigue_factor = 1.0
            breaks_needed = 0
        elif total_minutes <= 40:
            fatigue_factor = 1.1
            breaks_needed = 1
        elif total_minutes <= 60:
            fatigue_factor = 1.15
            breaks_needed = 2
        else:
            fatigue_factor = 1.2
            breaks_needed = math.ceil(total_minutes / 30)

        adjusted_time = total_minutes * fatigue_factor

        return {
            'original_time': total_minutes,
            'adjusted_time': adjusted_time,
            'fatigue_factor': fatigue_factor,
            'breaks_recommended': breaks_needed,
            'break_duration_minutes': 5 * breaks_needed
        }


class ComplexityScorer:
    """
    Оценка сложности текста
    Анализирует различные метрики для определения сложности контента
    """

    def __init__(self):
        pass

    def calculate_sentence_complexity(self, text: str) -> Dict[str, float]:
        """Анализ сложности предложений"""
        # Разбить на предложения
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return {'avg_length': 0, 'max_length': 0, 'complexity_score': 0}

        # Длина предложений
        lengths = [len(s.split()) for s in sentences]

        avg_length = sum(lengths) / len(lengths) if lengths else 0
        max_length = max(lengths) if lengths else 0

        # Оценка сложности на основе длины предложений
        # Простые предложения: 5-15 слов
        # Средние: 15-25 слов
        # Сложные: 25+ слов
        if avg_length < 15:
            complexity = 1.0
        elif avg_length < 25:
            complexity = 1.5
        else:
            complexity = 2.0

        return {
            'avg_sentence_length': round(avg_length, 1),
            'max_sentence_length': max_length,
            'total_sentences': len(sentences),
            'complexity_score': complexity
        }

    def calculate_vocabulary_richness(self, text: str) -> Dict[str, float]:
        """Анализ богатства словаря (Type-Token Ratio)"""
        # Извлечь слова
        words = re.findall(r'\b[а-яёa-z]+\b', text.lower())

        if not words:
            return {'ttr': 0, 'unique_words': 0, 'total_words': 0}

        unique_words = set(words)

        # Type-Token Ratio
        ttr = len(unique_words) / len(words) if words else 0

        return {
            'total_words': len(words),
            'unique_words': len(unique_words),
            'type_token_ratio': round(ttr, 3),
            'vocabulary_richness': 'high' if ttr > 0.6 else 'medium' if ttr > 0.4 else 'low'
        }

    def detect_technical_terms(self, text: str) -> Dict[str, any]:
        """Обнаружить технические термины"""
        # Паттерны для технических терминов
        patterns = {
            'code_mentions': len(re.findall(r'`[^`]+`', text)),
            'abbreviations': len(re.findall(r'\b[A-Z]{2,}\b', text)),
            'camelCase': len(re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', text)),
            'technical_words': len(re.findall(r'\b(API|HTTP|JSON|XML|SQL|HTML|CSS|JavaScript|Python|function|class|method|algorithm|database)\b', text, re.IGNORECASE)),
        }

        total_technical = sum(patterns.values())

        # Оценка технической сложности
        if total_technical > 50:
            technical_level = 'very_high'
        elif total_technical > 20:
            technical_level = 'high'
        elif total_technical > 10:
            technical_level = 'medium'
        else:
            technical_level = 'low'

        return {
            **patterns,
            'total_technical_indicators': total_technical,
            'technical_level': technical_level
        }

    def calculate_overall_complexity(self, text: str) -> Dict[str, any]:
        """Комплексная оценка сложности"""
        sentence_metrics = self.calculate_sentence_complexity(text)
        vocab_metrics = self.calculate_vocabulary_richness(text)
        technical_metrics = self.detect_technical_terms(text)

        # Вычислить общую оценку сложности (1.0 - простой, 3.0 - очень сложный)
        complexity_factors = []

        # Фактор длины предложений
        complexity_factors.append(sentence_metrics['complexity_score'])

        # Фактор технической терминологии
        tech_level_scores = {'low': 1.0, 'medium': 1.5, 'high': 2.0, 'very_high': 2.5}
        complexity_factors.append(tech_level_scores[technical_metrics['technical_level']])

        # Фактор богатства словаря (высокий TTR = сложнее)
        ttr = vocab_metrics['type_token_ratio']
        if ttr > 0.6:
            complexity_factors.append(1.8)
        elif ttr > 0.4:
            complexity_factors.append(1.3)
        else:
            complexity_factors.append(1.0)

        overall_score = sum(complexity_factors) / len(complexity_factors)

        return {
            'sentence_metrics': sentence_metrics,
            'vocabulary_metrics': vocab_metrics,
            'technical_metrics': technical_metrics,
            'overall_complexity_score': round(overall_score, 2),
            'difficulty_level': self._get_difficulty_label(overall_score)
        }

    def _get_difficulty_label(self, score: float) -> str:
        """Получить метку сложности"""
        if score >= 2.5:
            return 'very_difficult'
        elif score >= 2.0:
            return 'difficult'
        elif score >= 1.5:
            return 'moderate'
        elif score >= 1.0:
            return 'easy'
        else:
            return 'very_easy'


class ReadabilityMetrics:
    """
    Метрики читаемости
    Реализует классические индексы читаемости
    """

    def __init__(self):
        pass

    def count_syllables_russian(self, word: str) -> int:
        """
        Приблизительный подсчет слогов в русском слове
        Основано на количестве гласных
        """
        vowels = 'аеёиоуыэюяaeiouy'
        word = word.lower()
        syllable_count = sum(1 for char in word if char in vowels)
        return max(1, syllable_count)

    def flesch_reading_ease_adapted(self, text: str) -> Dict[str, any]:
        """
        Адаптированный индекс Флеша для русского языка

        Формула (адаптированная):
        206.835 - 1.015 × (слова/предложения) - 84.6 × (слоги/слова)

        Результат:
        90-100: очень легко
        60-70: стандартный текст
        0-30: очень сложно
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = re.findall(r'\b[а-яёa-z]+\b', text.lower())

        if not sentences or not words:
            return {'score': 0, 'level': 'unknown'}

        # Подсчитать слоги
        total_syllables = sum(self.count_syllables_russian(word) for word in words)

        # Вычислить метрики
        words_per_sentence = len(words) / len(sentences)
        syllables_per_word = total_syllables / len(words)

        # Формула Флеша (адаптированная)
        score = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)

        # Ограничить диапазон
        score = max(0, min(100, score))

        return {
            'flesch_score': round(score, 1),
            'level': self._flesch_level(score),
            'words_per_sentence': round(words_per_sentence, 1),
            'syllables_per_word': round(syllables_per_word, 2),
            'total_sentences': len(sentences),
            'total_words': len(words),
            'total_syllables': total_syllables
        }

    def _flesch_level(self, score: float) -> str:
        """Определить уровень читаемости по шкале Флеша"""
        if score >= 90:
            return 'very_easy'
        elif score >= 80:
            return 'easy'
        elif score >= 70:
            return 'fairly_easy'
        elif score >= 60:
            return 'standard'
        elif score >= 50:
            return 'fairly_difficult'
        elif score >= 30:
            return 'difficult'
        else:
            return 'very_difficult'

    def automated_readability_index(self, text: str) -> Dict[str, any]:
        """
        ARI (Automated Readability Index)

        Формула:
        4.71 × (символы/слова) + 0.5 × (слова/предложения) - 21.43

        Результат показывает примерный класс образования для понимания текста
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = re.findall(r'\b[а-яёa-z]+\b', text.lower())
        chars = sum(len(word) for word in words)

        if not sentences or not words:
            return {'ari_score': 0, 'grade_level': 0}

        chars_per_word = chars / len(words)
        words_per_sentence = len(words) / len(sentences)

        ari = (4.71 * chars_per_word) + (0.5 * words_per_sentence) - 21.43

        # Ограничить диапазон
        ari = max(1, min(14, ari))

        return {
            'ari_score': round(ari, 1),
            'grade_level': math.ceil(ari),
            'chars_per_word': round(chars_per_word, 1),
            'words_per_sentence': round(words_per_sentence, 1),
            'interpretation': self._ari_interpretation(ari)
        }

    def _ari_interpretation(self, ari: float) -> str:
        """Интерпретация ARI"""
        if ari <= 6:
            return 'elementary_school'
        elif ari <= 9:
            return 'middle_school'
        elif ari <= 12:
            return 'high_school'
        else:
            return 'college_level'


class ReadingTimeCalculator:
    """
    Калькулятор времени чтения
    """

    def __init__(self, root_dir=".", wpm=200):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.wpm = wpm  # words per minute (слов в минуту)

        # Инициализация анализаторов
        self.speed_analyzer = ReadingSpeedAnalyzer(wpm)
        self.complexity_scorer = ComplexityScorer()
        self.readability_metrics = ReadabilityMetrics()

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

    def count_words(self, text):
        """Подсчитать слова в тексте"""
        # Удалить markdown разметку
        # Удалить заголовки
        text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
        # Удалить код
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)
        # Удалить ссылки
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Удалить изображения
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

        # Подсчитать слова (кириллица + латиница)
        words = re.findall(r'\b[а-яёa-z]+\b', text.lower())

        return len(words)

    def count_code_blocks(self, text):
        """Подсчитать блоки кода"""
        code_blocks = re.findall(r'```.*?```', text, re.DOTALL)
        total_lines = 0

        for block in code_blocks:
            lines = block.split('\n')
            # Минус первая и последняя строка (```)
            total_lines += max(0, len(lines) - 2)

        return total_lines

    def calculate_reading_time(self, file_path):
        """
        Вычислить время чтения для файла

        Возвращает:
        {
            'words': количество слов,
            'code_lines': строк кода,
            'reading_minutes': минут для чтения текста,
            'code_minutes': минут для чтения кода,
            'total_minutes': общее время,
            'formatted': '5 мин чтения'
        }
        """
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        # Подсчитать слова
        words = self.count_words(content)

        # Подсчитать код
        code_lines = self.count_code_blocks(content)

        # Определить тип контента для корректировки скорости
        category = frontmatter.get('category', '') if frontmatter else ''

        # Для технических текстов - медленнее
        wpm = self.wpm
        if category in ['computers', 'programming']:
            wpm = int(self.wpm * 0.75)  # 25% медленнее

        # Время чтения текста
        reading_minutes = words / wpm if wpm > 0 else 0

        # Время чтения кода (примерно 50 строк/минута)
        code_minutes = code_lines / 50 if code_lines > 0 else 0

        # Общее время
        total_minutes = reading_minutes + code_minutes

        # Округлить до ближайшей минуты
        total_minutes_rounded = max(1, math.ceil(total_minutes))

        return {
            'words': words,
            'code_lines': code_lines,
            'reading_minutes': round(reading_minutes, 2),
            'code_minutes': round(code_minutes, 2),
            'total_minutes': round(total_minutes, 2),
            'total_minutes_rounded': total_minutes_rounded,
            'formatted': self.format_time(total_minutes_rounded)
        }

    def format_time(self, minutes):
        """Отформатировать время в читаемый вид"""
        if minutes < 1:
            return "< 1 мин"
        elif minutes == 1:
            return "1 мин"
        elif minutes < 60:
            return f"{int(minutes)} мин"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            if mins == 0:
                return f"{hours} ч"
            return f"{hours} ч {mins} мин"

    def add_reading_time_to_articles(self):
        """Добавить время чтения ко всем статьям"""
        print("⏱️  Вычисление времени чтения...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            reading_time = self.calculate_reading_time(md_file)

            if not reading_time:
                continue

            # Обновить frontmatter
            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not frontmatter:
                continue

            # Добавить время чтения
            old_time = frontmatter.get('reading_time')

            frontmatter['reading_time'] = reading_time['formatted']
            frontmatter['reading_time_minutes'] = reading_time['total_minutes_rounded']
            frontmatter['word_count'] = reading_time['words']

            if reading_time['code_lines'] > 0:
                frontmatter['code_lines'] = reading_time['code_lines']

            # Записать обратно
            try:
                new_content = "---\n"
                new_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += content

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                if old_time != reading_time['formatted']:
                    count += 1
                    print(f"✅ {md_file.relative_to(self.root_dir)} — {reading_time['formatted']}")

            except Exception as e:
                print(f"⚠️  Ошибка в {md_file}: {e}")

        print(f"\n✅ Обновлено статей: {count}")

    def analyze_complexity(self, file_path):
        """
        Полный анализ сложности текста
        """
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        # Базовый анализ времени чтения
        reading_time = self.calculate_reading_time(file_path)

        # Анализ сложности
        complexity = self.complexity_scorer.calculate_overall_complexity(content)

        # Метрики читаемости
        flesch = self.readability_metrics.flesch_reading_ease_adapted(content)
        ari = self.readability_metrics.automated_readability_index(content)

        # Анализ усталости
        fatigue = self.speed_analyzer.calculate_reading_fatigue(reading_time['total_minutes'])

        return {
            'file': str(file_path),
            'reading_time': reading_time,
            'complexity': complexity,
            'flesch_reading_ease': flesch,
            'automated_readability_index': ari,
            'fatigue_analysis': fatigue
        }

    def export_analysis_json(self, analysis_results: List[Dict], output_file: str):
        """Экспорт анализа в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON экспорт: {output_file}")

    def export_analysis_html(self, analysis_results: List[Dict], output_file: str):
        """Экспорт анализа в HTML с красивым оформлением"""
        html = []
        html.append('<!DOCTYPE html>\n<html lang="ru">\n<head>\n')
        html.append('<meta charset="UTF-8">\n')
        html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        html.append('<title>Анализ времени чтения и сложности текста</title>\n')
        html.append('<style>\n')
        html.append('body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; ')
        html.append('max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }\n')
        html.append('h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }\n')
        html.append('h2 { color: #34495e; margin-top: 30px; }\n')
        html.append('.article-card { background: white; border-radius: 8px; padding: 20px; ')
        html.append('margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n')
        html.append('.article-title { font-size: 1.4em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }\n')
        html.append('.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); ')
        html.append('gap: 15px; margin-top: 15px; }\n')
        html.append('.metric-box { background: #ecf0f1; padding: 15px; border-radius: 5px; }\n')
        html.append('.metric-label { font-size: 0.85em; color: #7f8c8d; text-transform: uppercase; ')
        html.append('letter-spacing: 0.5px; }\n')
        html.append('.metric-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; margin-top: 5px; }\n')
        html.append('.difficulty-very_easy { background: #d4edda; color: #155724; }\n')
        html.append('.difficulty-easy { background: #d1ecf1; color: #0c5460; }\n')
        html.append('.difficulty-moderate { background: #fff3cd; color: #856404; }\n')
        html.append('.difficulty-difficult { background: #f8d7da; color: #721c24; }\n')
        html.append('.difficulty-very_difficult { background: #f5c6cb; color: #491217; }\n')
        html.append('.complexity-section { margin-top: 20px; padding: 15px; background: #f8f9fa; ')
        html.append('border-left: 4px solid #3498db; border-radius: 4px; }\n')
        html.append('.summary { background: #3498db; color: white; padding: 20px; border-radius: 8px; ')
        html.append('margin-bottom: 30px; }\n')
        html.append('.summary h2 { color: white; margin-top: 0; border: none; }\n')
        html.append('</style>\n</head>\n<body>\n')

        html.append('<h1>⏱️ Анализ времени чтения и сложности текста</h1>\n')

        # Общая статистика
        total_articles = len(analysis_results)
        total_time = sum(a['reading_time']['total_minutes'] for a in analysis_results)
        total_words = sum(a['reading_time']['words'] for a in analysis_results)
        avg_complexity = sum(a['complexity']['overall_complexity_score'] for a in analysis_results) / total_articles if total_articles > 0 else 0

        html.append('<div class="summary">\n')
        html.append('<h2>Общая статистика</h2>\n')
        html.append(f'<p><strong>Всего статей:</strong> {total_articles}</p>\n')
        html.append(f'<p><strong>Общее время чтения:</strong> {self.format_time(total_time)}</p>\n')
        html.append(f'<p><strong>Всего слов:</strong> {total_words:,}</p>\n')
        html.append(f'<p><strong>Средняя сложность:</strong> {avg_complexity:.2f} / 3.0</p>\n')
        html.append('</div>\n')

        # Каждая статья
        for analysis in sorted(analysis_results, key=lambda x: x['reading_time']['total_minutes'], reverse=True):
            rt = analysis['reading_time']
            comp = analysis['complexity']
            flesch = analysis['flesch_reading_ease']
            ari = analysis['automated_readability_index']
            fatigue = analysis['fatigue_analysis']

            html.append('<div class="article-card">\n')
            html.append(f'<div class="article-title">{Path(analysis["file"]).stem}</div>\n')
            html.append(f'<div style="color: #7f8c8d; font-size: 0.9em;">{analysis["file"]}</div>\n')

            html.append('<div class="metrics">\n')

            # Время чтения
            html.append('<div class="metric-box">\n')
            html.append('<div class="metric-label">Время чтения</div>\n')
            html.append(f'<div class="metric-value">{rt["formatted"]}</div>\n')
            html.append(f'<div style="font-size: 0.85em; color: #7f8c8d; margin-top: 5px;">{rt["words"]:,} слов</div>\n')
            html.append('</div>\n')

            # Сложность
            difficulty_class = f'difficulty-{comp["difficulty_level"]}'
            html.append(f'<div class="metric-box {difficulty_class}">\n')
            html.append('<div class="metric-label">Сложность</div>\n')
            html.append(f'<div class="metric-value">{comp["overall_complexity_score"]:.2f}</div>\n')
            html.append(f'<div style="font-size: 0.85em; margin-top: 5px;">{comp["difficulty_level"].replace("_", " ").title()}</div>\n')
            html.append('</div>\n')

            # Flesch Reading Ease
            html.append('<div class="metric-box">\n')
            html.append('<div class="metric-label">Flesch Score</div>\n')
            html.append(f'<div class="metric-value">{flesch["flesch_score"]:.1f}</div>\n')
            html.append(f'<div style="font-size: 0.85em; margin-top: 5px;">{flesch["level"].replace("_", " ").title()}</div>\n')
            html.append('</div>\n')

            # ARI Grade Level
            html.append('<div class="metric-box">\n')
            html.append('<div class="metric-label">ARI Grade</div>\n')
            html.append(f'<div class="metric-value">{ari["grade_level"]}</div>\n')
            html.append(f'<div style="font-size: 0.85em; margin-top: 5px;">{ari["interpretation"].replace("_", " ").title()}</div>\n')
            html.append('</div>\n')

            html.append('</div>\n')

            # Детальная информация о сложности
            html.append('<div class="complexity-section">\n')
            html.append('<strong>Детальный анализ сложности:</strong><br>\n')
            html.append(f'• Средняя длина предложения: {comp["sentence_metrics"]["avg_sentence_length"]} слов<br>\n')
            html.append(f'• Уникальных слов: {comp["vocabulary_metrics"]["unique_words"]} из {comp["vocabulary_metrics"]["total_words"]}<br>\n')
            html.append(f'• Type-Token Ratio: {comp["vocabulary_metrics"]["type_token_ratio"]:.3f}<br>\n')
            html.append(f'• Технический уровень: {comp["technical_metrics"]["technical_level"].replace("_", " ").title()}<br>\n')

            if fatigue['breaks_recommended'] > 0:
                html.append(f'<br><strong>⚠️ Рекомендуется {fatigue["breaks_recommended"]} перерыв(ов) по 5 минут</strong><br>\n')
                html.append(f'Скорректированное время с перерывами: {self.format_time(fatigue["adjusted_time"])}\n')

            html.append('</div>\n')

            html.append('</div>\n')

        html.append('</body>\n</html>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(html))

        print(f"✅ HTML экспорт: {output_file}")

    def analyze_all_articles(self) -> List[Dict]:
        """Анализ всех статей с полной информацией"""
        results = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            analysis = self.analyze_complexity(md_file)

            if analysis:
                results.append(analysis)

        return results

    def generate_report(self):
        """Создать отчёт по времени чтения"""
        print("\n📊 Анализ времени чтения...\n")

        articles = []
        total_time = 0
        total_words = 0
        total_code = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            reading_time = self.calculate_reading_time(md_file)

            if not reading_time:
                continue

            frontmatter, _ = self.extract_frontmatter_and_content(md_file)

            articles.append({
                'file': str(md_file.relative_to(self.root_dir)),
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'category': frontmatter.get('category', '') if frontmatter else '',
                **reading_time
            })

            total_time += reading_time['total_minutes']
            total_words += reading_time['words']
            total_code += reading_time['code_lines']

        lines = []
        lines.append("# ⏱️  Отчёт: Время чтения\n\n")

        lines.append("## Общая статистика\n\n")
        lines.append(f"- **Всего статей**: {len(articles)}\n")
        lines.append(f"- **Общее время чтения**: {self.format_time(total_time)}\n")
        lines.append(f"- **Всего слов**: {total_words:,}\n")
        lines.append(f"- **Строк кода**: {total_code:,}\n")

        if articles:
            avg_time = total_time / len(articles)
            lines.append(f"- **Среднее время**: {self.format_time(avg_time)}\n\n")

        # Топ самых длинных статей
        lines.append("## Топ-10 самых длинных статей\n\n")
        sorted_articles = sorted(articles, key=lambda x: x['total_minutes'], reverse=True)

        for i, article in enumerate(sorted_articles[:10], 1):
            lines.append(f"{i}. **{article['title']}** — {article['formatted']}\n")
            lines.append(f"   - {article['words']:,} слов")
            if article['code_lines'] > 0:
                lines.append(f", {article['code_lines']} строк кода")
            lines.append(f"\n   - `{article['file']}`\n\n")

        # Топ самых коротких
        lines.append("\n## Топ-10 самых коротких статей\n\n")
        sorted_articles = sorted(articles, key=lambda x: x['total_minutes'])

        for i, article in enumerate(sorted_articles[:10], 1):
            lines.append(f"{i}. **{article['title']}** — {article['formatted']}\n")
            lines.append(f"   - {article['words']:,} слов\n")
            lines.append(f"   - `{article['file']}`\n\n")

        # По категориям
        lines.append("\n## По категориям\n\n")

        by_category = {}
        for article in articles:
            cat = article['category'] or 'Без категории'
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'time': 0, 'words': 0}

            by_category[cat]['count'] += 1
            by_category[cat]['time'] += article['total_minutes']
            by_category[cat]['words'] += article['words']

        for cat, stats in sorted(by_category.items()):
            lines.append(f"### {cat}\n\n")
            lines.append(f"- Статей: {stats['count']}\n")
            lines.append(f"- Общее время: {self.format_time(stats['time'])}\n")
            lines.append(f"- Всего слов: {stats['words']:,}\n")
            lines.append(f"- Среднее время: {self.format_time(stats['time'] / stats['count'])}\n\n")

        return ''.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='⏱️  Reading Time Calculator - Расширенный анализ времени чтения и сложности текста',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s -f knowledge/article.md              # Время чтения для файла
  %(prog)s -f knowledge/article.md --analyze    # Полный анализ сложности
  %(prog)s -u                                   # Обновить время во всех статьях
  %(prog)s -r                                   # Создать отчёт
  %(prog)s --complexity                         # Анализ сложности всех статей
  %(prog)s --json complexity.json               # Экспорт в JSON
  %(prog)s --html complexity.html               # Экспорт в HTML
  %(prog)s --all                                # Полный анализ + все экспорты
        """
    )

    # Основные операции
    parser.add_argument(
        '-f', '--file',
        help='Вычислить время для конкретного файла'
    )

    parser.add_argument(
        '-u', '--update',
        action='store_true',
        help='Обновить время чтения во всех статьях (добавить в frontmatter)'
    )

    parser.add_argument(
        '-r', '--report',
        action='store_true',
        help='Создать отчёт по времени чтения (markdown)'
    )

    # Расширенный анализ
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Полный анализ сложности (с файлом -f или для всех статей)'
    )

    parser.add_argument(
        '--complexity',
        action='store_true',
        help='Анализ сложности всех статей'
    )

    parser.add_argument(
        '--readability',
        action='store_true',
        help='Метрики читаемости (Flesch, ARI)'
    )

    # Экспорт
    parser.add_argument(
        '--json',
        metavar='FILE',
        help='Экспортировать результаты анализа в JSON'
    )

    parser.add_argument(
        '--html',
        metavar='FILE',
        help='Экспортировать результаты анализа в HTML с красивым оформлением'
    )

    # Параметры
    parser.add_argument(
        '-w', '--wpm',
        type=int,
        default=200,
        help='Слов в минуту (по умолчанию: 200)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Выполнить все виды анализа и экспорта'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    calc = ReadingTimeCalculator(root_dir, wpm=args.wpm)

    # Обработка --all
    if args.all:
        args.complexity = True
        args.readability = True
        if not args.json:
            args.json = str(root_dir / "reading_complexity_analysis.json")
        if not args.html:
            args.html = str(root_dir / "reading_complexity_analysis.html")

    # Анализ конкретного файла
    if args.file:
        file_path = root_dir / args.file

        if args.analyze or args.complexity or args.readability:
            # Полный анализ
            analysis = calc.analyze_complexity(file_path)

            if analysis:
                print(f"\n⏱️  Анализ файла: {args.file}\n")
                print("=" * 70)

                # Время чтения
                rt = analysis['reading_time']
                print(f"\n📖 Время чтения: {rt['formatted']}")
                print(f"   • Слов: {rt['words']:,}")
                print(f"   • Строк кода: {rt['code_lines']}")
                print(f"   • Время на текст: {rt['reading_minutes']:.1f} мин")
                print(f"   • Время на код: {rt['code_minutes']:.1f} мин")

                # Сложность
                comp = analysis['complexity']
                print(f"\n🔍 Сложность: {comp['overall_complexity_score']:.2f} / 3.0")
                print(f"   • Уровень: {comp['difficulty_level'].replace('_', ' ').title()}")
                print(f"   • Средняя длина предложения: {comp['sentence_metrics']['avg_sentence_length']} слов")
                print(f"   • Уникальных слов: {comp['vocabulary_metrics']['unique_words']} из {comp['vocabulary_metrics']['total_words']}")
                print(f"   • Type-Token Ratio: {comp['vocabulary_metrics']['type_token_ratio']:.3f}")
                print(f"   • Технический уровень: {comp['technical_metrics']['technical_level'].replace('_', ' ').title()}")

                # Читаемость
                flesch = analysis['flesch_reading_ease']
                ari = analysis['automated_readability_index']
                print(f"\n📊 Метрики читаемости:")
                print(f"   • Flesch Reading Ease: {flesch['flesch_score']:.1f} ({flesch['level'].replace('_', ' ').title()})")
                print(f"   • ARI Grade Level: {ari['grade_level']} ({ari['interpretation'].replace('_', ' ').title()})")
                print(f"   • Слов в предложении: {flesch['words_per_sentence']:.1f}")
                print(f"   • Символов в слове: {ari['chars_per_word']:.1f}")

                # Усталость
                fatigue = analysis['fatigue_analysis']
                if fatigue['breaks_recommended'] > 0:
                    print(f"\n⚠️  Рекомендации:")
                    print(f"   • Перерывов: {fatigue['breaks_recommended']} × 5 мин")
                    print(f"   • Время с перерывами: {calc.format_time(fatigue['adjusted_time'])}")

                print("\n" + "=" * 70 + "\n")
            else:
                print("❌ Не удалось обработать файл")

        else:
            # Простой расчёт времени
            reading_time = calc.calculate_reading_time(file_path)

            if reading_time:
                print(f"\n⏱️  Время чтения: {reading_time['formatted']}\n")
                print(f"   Слов: {reading_time['words']:,}")
                print(f"   Строк кода: {reading_time['code_lines']}")
                print(f"   Время на текст: {reading_time['reading_minutes']:.1f} мин")
                print(f"   Время на код: {reading_time['code_minutes']:.1f} мин")
                print(f"   Общее время: {reading_time['total_minutes']:.1f} мин\n")
            else:
                print("❌ Не удалось обработать файл")

    # Обновить frontmatter
    elif args.update:
        calc.add_reading_time_to_articles()

    # Создать отчёт
    elif args.report:
        report = calc.generate_report()
        output_file = root_dir / "READING_TIME_REPORT.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    # Анализ сложности всех статей
    elif args.complexity or args.readability or args.json or args.html:
        print("\n🔍 Анализ всех статей...\n")
        results = calc.analyze_all_articles()

        if not results:
            print("❌ Нет статей для анализа")
            return

        print(f"✅ Проанализировано статей: {len(results)}\n")

        # Статистика
        avg_time = sum(r['reading_time']['total_minutes'] for r in results) / len(results)
        avg_complexity = sum(r['complexity']['overall_complexity_score'] for r in results) / len(results)
        avg_flesch = sum(r['flesch_reading_ease']['flesch_score'] for r in results) / len(results)

        print("📊 Общая статистика:")
        print(f"   • Среднее время чтения: {calc.format_time(avg_time)}")
        print(f"   • Средняя сложность: {avg_complexity:.2f} / 3.0")
        print(f"   • Средний Flesch Score: {avg_flesch:.1f}")

        # Распределение по сложности
        difficulty_dist = Counter(r['complexity']['difficulty_level'] for r in results)
        print(f"\n📈 Распределение по сложности:")
        for level, count in sorted(difficulty_dist.items()):
            print(f"   • {level.replace('_', ' ').title()}: {count}")

        # Топ самых сложных
        print(f"\n🔥 Топ-5 самых сложных статей:")
        sorted_by_complexity = sorted(results, key=lambda x: x['complexity']['overall_complexity_score'], reverse=True)
        for i, r in enumerate(sorted_by_complexity[:5], 1):
            filename = Path(r['file']).stem
            score = r['complexity']['overall_complexity_score']
            level = r['complexity']['difficulty_level'].replace('_', ' ').title()
            print(f"   {i}. {filename}: {score:.2f} ({level})")

        # Топ самых простых
        print(f"\n✅ Топ-5 самых простых статей:")
        sorted_by_complexity_asc = sorted(results, key=lambda x: x['complexity']['overall_complexity_score'])
        for i, r in enumerate(sorted_by_complexity_asc[:5], 1):
            filename = Path(r['file']).stem
            score = r['complexity']['overall_complexity_score']
            level = r['complexity']['difficulty_level'].replace('_', ' ').title()
            print(f"   {i}. {filename}: {score:.2f} ({level})")

        # Экспорты
        if args.json:
            json_path = root_dir / args.json if not Path(args.json).is_absolute() else Path(args.json)
            calc.export_analysis_json(results, str(json_path))

        if args.html:
            html_path = root_dir / args.html if not Path(args.html).is_absolute() else Path(args.html)
            calc.export_analysis_html(results, str(html_path))

        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
