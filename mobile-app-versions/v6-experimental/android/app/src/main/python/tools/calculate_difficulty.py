#!/usr/bin/env python3
"""
Advanced Difficulty Level Calculator - Продвинутый анализатор уровня сложности

Оценивает сложность на основе:
- Формул читаемости (Flesch-Kincaid, Coleman-Liau, ARI, SMOG, Gunning Fog)
- Лексического разнообразия и словарного запаса
- Технических терминов и концептуальной плотности
- Сложности кода и математических формул
- Prerequisites и learning paths
- Генерирует визуализацию сложности и рекомендации
"""

from pathlib import Path
import yaml
import re
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
import argparse


class AdvancedDifficultyCalculator:
    """Продвинутый калькулятор уровня сложности с формулами читаемости"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Технические термины (указывают на сложность)
        self.technical_terms = {
            'advanced': 3, 'algorithm': 2, 'architecture': 2, 'async': 2,
            'closure': 2, 'concurrency': 3, 'decorator': 2, 'dependency': 1,
            'design pattern': 2, 'generator': 2, 'inheritance': 1,
            'metaclass': 3, 'multithreading': 3, 'optimization': 2,
            'polymorphism': 2, 'recursion': 2, 'refactoring': 2,
            'алгоритм': 2, 'архитектура': 2, 'наследование': 1,
            'полиморфизм': 2, 'рекурсия': 2, 'оптимизация': 2,
        }

        # Кэш для результатов
        self.difficulty_cache = {}
        self.syllable_cache = {}

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

    def count_syllables(self, word):
        """Подсчитать количество слогов в слове (упрощённая версия)"""
        if word in self.syllable_cache:
            return self.syllable_cache[word]

        word = word.lower()
        syllables = 0
        vowels = 'aeiouyаеёиоуыэюя'
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllables += 1
            previous_was_vowel = is_vowel

        # Минимум 1 слог
        if syllables == 0:
            syllables = 1

        self.syllable_cache[word] = syllables
        return syllables

    def flesch_reading_ease(self, sentences, words, syllables):
        """
        Flesch Reading Ease Score
        100-90: Very Easy
        90-80: Easy
        80-70: Fairly Easy
        70-60: Standard
        60-50: Fairly Difficult
        50-30: Difficult
        30-0: Very Confusing
        """
        if not sentences or not words:
            return None

        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return max(0, min(100, score))

    def flesch_kincaid_grade(self, sentences, words, syllables):
        """
        Flesch-Kincaid Grade Level
        Возвращает уровень образования (класс школы)
        """
        if not sentences or not words:
            return None

        grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
        return max(0, grade)

    def coleman_liau_index(self, sentences, words, characters):
        """
        Coleman-Liau Index
        CLI = 0.0588 * L - 0.296 * S - 15.8
        L = average number of letters per 100 words
        S = average number of sentences per 100 words
        """
        if not words:
            return None

        L = (characters / words) * 100
        S = (sentences / words) * 100

        cli = 0.0588 * L - 0.296 * S - 15.8
        return max(0, cli)

    def automated_readability_index(self, sentences, words, characters):
        """
        Automated Readability Index (ARI)
        ARI = 4.71 * (characters/words) + 0.5 * (words/sentences) - 21.43
        """
        if not sentences or not words:
            return None

        ari = 4.71 * (characters / words) + 0.5 * (words / sentences) - 21.43
        return max(0, ari)

    def smog_index(self, sentences, polysyllables):
        """
        SMOG (Simple Measure of Gobbledygook) Index
        SMOG = 1.043 * sqrt(polysyllables * (30 / sentences)) + 3.1291
        """
        if not sentences or sentences < 3:
            return None

        smog = 1.043 * math.sqrt(polysyllables * (30 / sentences)) + 3.1291
        return max(0, smog)

    def gunning_fog_index(self, sentences, words, complex_words):
        """
        Gunning Fog Index
        Grade level = 0.4 * ((words/sentences) + 100 * (complex_words/words))
        Complex words = words with 3+ syllables
        """
        if not sentences or not words:
            return None

        fog = 0.4 * ((words / sentences) + 100 * (complex_words / words))
        return max(0, fog)

    def calculate_lexical_diversity(self, tokens):
        """
        Лексическое разнообразие (Type-Token Ratio)
        Unique words / Total words
        Выше = больше разнообразие = сложнее
        """
        if not tokens:
            return 0.0

        unique = len(set(tokens))
        total = len(tokens)
        return unique / total if total > 0 else 0.0

    def calculate_vocabulary_metrics(self, tokens):
        """Вычислить метрики словарного запаса"""
        if not tokens:
            return {}

        word_lengths = [len(word) for word in tokens]
        syllable_counts = [self.count_syllables(word) for word in tokens]

        # Сложные слова (3+ слогов)
        complex_words = sum(1 for s in syllable_counts if s >= 3)

        # Редкие слова (длинные, нечастые)
        freq = Counter(tokens)
        rare_words = sum(1 for word, count in freq.items() if count == 1 and len(word) > 8)

        return {
            'avg_word_length': sum(word_lengths) / len(word_lengths) if word_lengths else 0,
            'avg_syllables': sum(syllable_counts) / len(syllable_counts) if syllable_counts else 0,
            'complex_words': complex_words,
            'complex_words_pct': (complex_words / len(tokens) * 100) if tokens else 0,
            'rare_words': rare_words,
            'rare_words_pct': (rare_words / len(tokens) * 100) if tokens else 0,
            'lexical_diversity': self.calculate_lexical_diversity(tokens),
        }

    def analyze_code_complexity(self, content):
        """Анализ сложности кода"""
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)

        if not code_blocks:
            return {'count': 0, 'total_lines': 0, 'avg_lines': 0, 'complexity_score': 0}

        total_lines = 0
        complexity_indicators = 0

        for code in code_blocks:
            lines = code.strip().split('\n')
            total_lines += len(lines)

            # Индикаторы сложности: циклы, условия, функции
            complexity_indicators += len(re.findall(r'\b(for|while|if|else|elif|def|class|async|await|try|except)\b', code))

        return {
            'count': len(code_blocks),
            'total_lines': total_lines,
            'avg_lines': total_lines / len(code_blocks) if code_blocks else 0,
            'complexity_score': complexity_indicators,
        }

    def calculate_comprehensive_difficulty(self, file_path):
        """Комплексное вычисление сложности с всеми метриками"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        # Базовые метрики текста
        sentences = [s for s in re.split(r'[.!?]+', content) if s.strip()]
        tokens = re.findall(r'\b[а-яёa-z]+\b', content.lower())
        characters = sum(len(word) for word in tokens)

        # Подсчёт слогов
        total_syllables = sum(self.count_syllables(word) for word in tokens)
        polysyllables = sum(1 for word in tokens if self.count_syllables(word) >= 3)

        num_sentences = len(sentences)
        num_words = len(tokens)

        # Формулы читаемости
        flesch_ease = self.flesch_reading_ease(num_sentences, num_words, total_syllables)
        flesch_grade = self.flesch_kincaid_grade(num_sentences, num_words, total_syllables)
        coleman_liau = self.coleman_liau_index(num_sentences, num_words, characters)
        ari = self.automated_readability_index(num_sentences, num_words, characters)
        smog = self.smog_index(num_sentences, polysyllables)

        vocab_metrics = self.calculate_vocabulary_metrics(tokens)
        gunning_fog = self.gunning_fog_index(num_sentences, num_words, vocab_metrics['complex_words'])

        # Анализ кода
        code_metrics = self.analyze_code_complexity(content)

        # Технические термины
        content_lower = content.lower()
        term_score = 0
        found_terms = []
        for term, weight in self.technical_terms.items():
            if term in content_lower:
                term_score += weight
                found_terms.append(term)

        # Математические формулы
        math_count = len(re.findall(r'\$.*?\$|\\\(.*?\\\)', content))

        # Prerequisites
        prerequisites = []
        if frontmatter:
            prerequisites = frontmatter.get('prerequisites', [])
            if not isinstance(prerequisites, list):
                prerequisites = []

        # Комплексная оценка (0-100)
        score = 0

        # 1. Формулы читаемости (0-30)
        # Flesch Reading Ease: инвертируем (100=легко → 0=сложно)
        if flesch_ease is not None:
            score += (100 - flesch_ease) * 0.15  # max 15

        # Flesch-Kincaid Grade Level
        if flesch_grade is not None:
            score += min(15, flesch_grade * 1.5)  # max 15

        # 2. Лексическое разнообразие (0-15)
        score += vocab_metrics['lexical_diversity'] * 20  # max ~20, cap at 15
        score += vocab_metrics['complex_words_pct'] * 0.3  # max ~10

        # 3. Код (0-25)
        score += min(20, code_metrics['count'] * 5)
        score += min(5, code_metrics['complexity_score'] * 0.5)

        # 4. Технические термины (0-15)
        score += min(15, term_score)

        # 5. Prerequisites (0-10)
        score += min(10, len(prerequisites) * 3)

        # 6. Математика (0-5)
        score += min(5, math_count * 1)

        score = min(100, max(0, score))

        # Определить уровень
        if score >= 80:
            level = 'Expert'
            difficulty = 5
        elif score >= 60:
            level = 'Advanced'
            difficulty = 4
        elif score >= 40:
            level = 'Intermediate'
            difficulty = 3
        elif score >= 20:
            level = 'Beginner'
            difficulty = 2
        else:
            level = 'Novice'
            difficulty = 1

        return {
            'file': str(file_path.relative_to(self.root_dir)),
            'title': frontmatter.get('title', file_path.stem) if frontmatter else file_path.stem,
            'score': round(score, 2),
            'level': level,
            'difficulty': difficulty,
            'readability': {
                'flesch_reading_ease': round(flesch_ease, 2) if flesch_ease else None,
                'flesch_kincaid_grade': round(flesch_grade, 2) if flesch_grade else None,
                'coleman_liau_index': round(coleman_liau, 2) if coleman_liau else None,
                'automated_readability_index': round(ari, 2) if ari else None,
                'smog_index': round(smog, 2) if smog else None,
                'gunning_fog_index': round(gunning_fog, 2) if gunning_fog else None,
            },
            'vocabulary': vocab_metrics,
            'code': code_metrics,
            'technical_terms': {
                'count': len(found_terms),
                'score': term_score,
                'terms': found_terms[:10],  # Топ-10
            },
            'math_formulas': math_count,
            'prerequisites': prerequisites,
            'text_stats': {
                'sentences': num_sentences,
                'words': num_words,
                'characters': characters,
                'syllables': total_syllables,
            }
        }

    def generate_learning_path(self, all_results):
        """
        Генерация learning path на основе сложности и prerequisites
        Возвращает рекомендованный порядок изучения
        """
        # Сортировка по сложности
        sorted_by_difficulty = sorted(all_results, key=lambda x: x['score'])

        learning_path = []
        for i, result in enumerate(sorted_by_difficulty, 1):
            learning_path.append({
                'order': i,
                'file': result['file'],
                'title': result['title'],
                'level': result['level'],
                'score': result['score'],
                'prerequisites': result.get('prerequisites', []),
            })

        return learning_path

    def generate_difficulty_distribution(self, all_results):
        """Генерация распределения сложности"""
        distribution = defaultdict(list)

        for result in all_results:
            distribution[result['level']].append({
                'file': result['file'],
                'title': result['title'],
                'score': result['score'],
            })

        return dict(distribution)

    def export_to_json(self, all_results, output_file='difficulty_analysis.json'):
        """Экспорт в JSON"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'total_articles': len(all_results),
            'results': all_results,
            'learning_path': self.generate_learning_path(all_results),
            'distribution': self.generate_difficulty_distribution(all_results),
            'statistics': {
                'avg_score': sum(r['score'] for r in all_results) / len(all_results) if all_results else 0,
                'min_score': min(r['score'] for r in all_results) if all_results else 0,
                'max_score': max(r['score'] for r in all_results) if all_results else 0,
                'by_level': {
                    'Novice': sum(1 for r in all_results if r['level'] == 'Novice'),
                    'Beginner': sum(1 for r in all_results if r['level'] == 'Beginner'),
                    'Intermediate': sum(1 for r in all_results if r['level'] == 'Intermediate'),
                    'Advanced': sum(1 for r in all_results if r['level'] == 'Advanced'),
                    'Expert': sum(1 for r in all_results if r['level'] == 'Expert'),
                }
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"📄 JSON экспортирован: {output_file}")

    def export_to_markdown(self, all_results, output_file='DIFFICULTY_REPORT.md'):
        """Экспорт в Markdown с красивым форматированием"""
        lines = ["# 📊 Отчёт об анализе сложности статей\n"]
        lines.append(f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append(f"**Всего статей**: {len(all_results)}\n")

        # Статистика
        if all_results:
            avg_score = sum(r['score'] for r in all_results) / len(all_results)
            lines.append(f"**Средняя сложность**: {avg_score:.2f}/100\n")

        # Распределение по уровням
        lines.append("\n## Распределение по уровням\n")
        distribution = self.generate_difficulty_distribution(all_results)

        for level in ['Novice', 'Beginner', 'Intermediate', 'Advanced', 'Expert']:
            if level in distribution:
                count = len(distribution[level])
                lines.append(f"- **{level}**: {count} статей\n")

        # Learning Path
        lines.append("\n## 📚 Рекомендованный порядок изучения\n")
        learning_path = self.generate_learning_path(all_results)

        for item in learning_path:
            lines.append(f"{item['order']}. **{item['title']}** — {item['level']} ({item['score']:.1f}/100)\n")
            if item['prerequisites']:
                lines.append(f"   - *Prerequisites*: {', '.join(item['prerequisites'])}\n")

        # Детальный анализ
        lines.append("\n## 📖 Детальный анализ\n")

        for result in sorted(all_results, key=lambda x: -x['score']):
            lines.append(f"\n### {result['title']} ({result['level']} — {result['score']:.1f}/100)\n")
            lines.append(f"**Файл**: `{result['file']}`\n\n")

            # Формулы читаемости
            r = result['readability']
            lines.append("**Читаемость**:\n")
            if r['flesch_reading_ease']:
                lines.append(f"- Flesch Reading Ease: {r['flesch_reading_ease']:.1f}\n")
            if r['flesch_kincaid_grade']:
                lines.append(f"- Flesch-Kincaid Grade: {r['flesch_kincaid_grade']:.1f}\n")
            if r['gunning_fog_index']:
                lines.append(f"- Gunning Fog Index: {r['gunning_fog_index']:.1f}\n")

            # Код
            if result['code']['count'] > 0:
                lines.append(f"\n**Код**: {result['code']['count']} блоков, {result['code']['total_lines']} строк\n")

            # Технические термины
            if result['technical_terms']['count'] > 0:
                lines.append(f"\n**Технические термины**: {result['technical_terms']['count']} найдено\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"📄 Markdown отчёт: {output_file}")

    def generate_html_visualization(self, all_results, output_file='difficulty_visualization.html'):
        """Генерация HTML визуализации с интерактивными графиками"""
        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Визуализация сложности статей</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 40px 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .stat-card p {
            opacity: 0.9;
        }
        .article-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .article-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .article-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .level-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .level-Novice { background: #e0e0e0; color: #333; }
        .level-Beginner { background: #81c784; color: white; }
        .level-Intermediate { background: #64b5f6; color: white; }
        .level-Advanced { background: #ff9800; color: white; }
        .level-Expert { background: #e53935; color: white; }
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
        }
        .filters {
            margin-bottom: 30px;
            text-align: center;
        }
        .filters button {
            margin: 5px;
            padding: 10px 20px;
            border: none;
            background: #667eea;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .filters button:hover {
            background: #764ba2;
        }
        .filters button.active {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Визуализация сложности статей</h1>

        <div class="stats">
            <div class="stat-card">
                <h3>""" + str(len(all_results)) + """</h3>
                <p>Всего статей</p>
            </div>
            <div class="stat-card">
                <h3>""" + f"{sum(r['score'] for r in all_results) / len(all_results):.1f}" + """</h3>
                <p>Средняя сложность</p>
            </div>
            <div class="stat-card">
                <h3>""" + str(sum(1 for r in all_results if r['level'] == 'Expert')) + """</h3>
                <p>Expert статей</p>
            </div>
        </div>

        <div class="filters">
            <button class="filter-btn active" data-level="all">Все</button>
            <button class="filter-btn" data-level="Novice">Novice</button>
            <button class="filter-btn" data-level="Beginner">Beginner</button>
            <button class="filter-btn" data-level="Intermediate">Intermediate</button>
            <button class="filter-btn" data-level="Advanced">Advanced</button>
            <button class="filter-btn" data-level="Expert">Expert</button>
        </div>

        <div class="article-grid" id="articleGrid">
"""

        for result in sorted(all_results, key=lambda x: -x['score']):
            html += f"""
            <div class="article-card" data-level="{result['level']}">
                <span class="level-badge level-{result['level']}">{result['level']}</span>
                <h3>{result['title']}</h3>
                <p><small>{result['file']}</small></p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result['score']}%"></div>
                </div>
                <p style="margin-top: 10px;">Сложность: {result['score']:.1f}/100</p>
"""
            if result['readability']['flesch_reading_ease']:
                html += f"<p><small>Flesch: {result['readability']['flesch_reading_ease']:.1f}</small></p>"

            html += """
            </div>
"""

        html += """
        </div>
    </div>

    <script>
        const filterButtons = document.querySelectorAll('.filter-btn');
        const articleCards = document.querySelectorAll('.article-card');

        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Обновить активную кнопку
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                const level = button.dataset.level;

                // Фильтровать карточки
                articleCards.forEach(card => {
                    if (level === 'all' || card.dataset.level === level) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"🌐 HTML визуализация: {output_file}")

    def analyze_all_articles(self):
        """Анализ всех статей в knowledge base"""
        print("📊 Комплексный анализ сложности...\n")

        results = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.calculate_comprehensive_difficulty(md_file)
            if result:
                results.append(result)
                print(f"✅ {result['file']} — {result['level']} ({result['score']:.1f}/100)")

        print(f"\n✅ Проанализировано статей: {len(results)}")
        return results

    def add_difficulty_to_articles(self):
        """Добавить уровень сложности ко всем статьям в frontmatter"""
        print("📊 Вычисление и добавление сложности...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.calculate_comprehensive_difficulty(md_file)
            if not result:
                continue

            # Обновить frontmatter
            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not frontmatter:
                continue

            frontmatter['difficulty'] = result['level']
            frontmatter['difficulty_score'] = result['score']

            # Записать обратно
            try:
                new_content = "---\n"
                new_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += content

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                count += 1
                print(f"✅ {md_file.relative_to(self.root_dir)} — {result['level']} ({result['score']:.1f}/100)")

            except Exception as e:
                print(f"⚠️  Ошибка: {e}")

        print(f"\n✅ Обработано статей: {count}")


def main():
    parser = argparse.ArgumentParser(
        description='Продвинутый анализатор сложности статей с формулами читаемости'
    )
    parser.add_argument(
        'target_file',
        nargs='?',
        help='Целевая статья для анализа (опционально)'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Анализировать все статьи без изменения файлов'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Добавить difficulty в frontmatter всех статей'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Экспортировать в JSON'
    )
    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Экспортировать в Markdown отчёт'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Создать HTML визуализацию'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    calc = AdvancedDifficultyCalculator(root_dir)

    # Если указан конкретный файл
    if args.target_file:
        file_path = Path(args.target_file)
        result = calc.calculate_comprehensive_difficulty(file_path)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Анализ всех статей
    if args.analyze or args.json or args.markdown or args.html:
        results = calc.analyze_all_articles()

        if args.json:
            calc.export_to_json(results)

        if args.markdown:
            calc.export_to_markdown(results)

        if args.html:
            calc.generate_html_visualization(results)

    # Обновление frontmatter
    elif args.update:
        calc.add_difficulty_to_articles()

    else:
        # По умолчанию: анализ + все экспорты
        results = calc.analyze_all_articles()
        calc.export_to_json(results)
        calc.export_to_markdown(results)
        calc.generate_html_visualization(results)


if __name__ == "__main__":
    main()
