#!/usr/bin/env python3
"""
Difficulty Level Calculator - Определение уровня сложности статей

Оценивает сложность на основе:
- Технических терминов
- Сложности предложений
- Наличия кода
- Требуемых знаний (prerequisites)
"""

from pathlib import Path
import yaml
import re


class DifficultyCalculator:
    """Калькулятор уровня сложности"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Технические термины (указывают на сложность)
        self.technical_terms = {
            'advanced': 3,
            'algorithm': 2,
            'architecture': 2,
            'async': 2,
            'closure': 2,
            'concurrency': 3,
            'decorator': 2,
            'dependency': 1,
            'design pattern': 2,
            'generator': 2,
            'inheritance': 1,
            'metaclass': 3,
            'multithreading': 3,
            'optimization': 2,
            'polymorphism': 2,
            'recursion': 2,
            'алгоритм': 2,
            'архитектура': 2,
            'наследование': 1,
            'полиморфизм': 2,
            'рекурсия': 2,
        }

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

    def calculate_difficulty(self, file_path):
        """Вычислить уровень сложности (0-100)"""
        frontmatter, content = self.extract_frontmatter_and_content(file_path)

        if not content:
            return None

        score = 0

        # 1. Наличие кода (0-30)
        code_blocks = len(re.findall(r'```', content)) // 2
        score += min(30, code_blocks * 10)

        # 2. Технические термины (0-25)
        content_lower = content.lower()
        term_score = 0
        for term, weight in self.technical_terms.items():
            if term in content_lower:
                term_score += weight
        score += min(25, term_score)

        # 3. Сложность предложений (0-20)
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            words_per_sentence = []
            for sent in sentences:
                words = re.findall(r'\b[а-яёa-z]+\b', sent.lower())
                if words:
                    words_per_sentence.append(len(words))

            if words_per_sentence:
                avg_words = sum(words_per_sentence) / len(words_per_sentence)
                # Длинные предложения = сложнее
                if avg_words > 30:
                    score += 20
                elif avg_words > 20:
                    score += 10
                elif avg_words > 15:
                    score += 5

        # 4. Prerequisites (0-15)
        if frontmatter:
            prerequisites = frontmatter.get('prerequisites', [])
            if isinstance(prerequisites, list):
                score += min(15, len(prerequisites) * 5)

        # 5. Математические формулы (0-10)
        math_indicators = len(re.findall(r'\$.*?\$|\\\(.*?\\\)', content))
        score += min(10, math_indicators * 2)

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
            'score': score,
            'level': level,
            'difficulty': difficulty,  # 1-5
            'file': str(file_path.relative_to(self.root_dir)),
            'title': frontmatter.get('title', file_path.stem) if frontmatter else file_path.stem
        }

    def add_difficulty_to_articles(self):
        """Добавить уровень сложности ко всем статьям"""
        print("📊 Вычисление уровня сложности...\n")

        count = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.calculate_difficulty(md_file)
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
                print(f"✅ {md_file.relative_to(self.root_dir)} — {result['level']} ({result['score']}/100)")

            except Exception as e:
                print(f"⚠️  Ошибка: {e}")

        print(f"\n✅ Обработано статей: {count}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    calc = DifficultyCalculator(root_dir)
    calc.add_difficulty_to_articles()


if __name__ == "__main__":
    main()
