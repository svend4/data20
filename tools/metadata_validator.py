#!/usr/bin/env python3
"""
Metadata Validator - Валидатор метаданных
Проверяет корректность и полноту frontmatter

Вдохновлено: Schema.org validation, JSON Schema
"""

from pathlib import Path
import yaml
import re
from datetime import datetime
import json


class MetadataValidator:
    """Валидатор метаданных"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Схема валидации
        self.schema = {
            'title': {'required': True, 'type': str},
            'date': {'required': False, 'type': str, 'format': 'date'},
            'author': {'required': False, 'type': str},
            'tags': {'required': True, 'type': list, 'min_items': 1},
            'category': {'required': True, 'type': str},
            'subcategory': {'required': False, 'type': str},
            'difficulty': {'required': False, 'type': str, 'enum': ['легкий', 'средний', 'сложный']},
            'source': {'required': False, 'type': str},
            'related': {'required': False, 'type': list}
        }

        # Результаты валидации
        self.results = []

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
        except Exception as e:
            return None
        return None

    def validate_field(self, field_name, value, rules):
        """Валидировать поле"""
        errors = []

        # Проверка типа
        if 'type' in rules and value is not None:
            if not isinstance(value, rules['type']):
                errors.append(f"Неверный тип (ожидается {rules['type'].__name__})")

        # Проверка формата даты
        if 'format' in rules and rules['format'] == 'date' and value:
            try:
                datetime.strptime(str(value), '%Y-%m-%d')
            except:
                errors.append(f"Неверный формат даты (ожидается YYYY-MM-DD)")

        # Проверка enum
        if 'enum' in rules and value:
            if value not in rules['enum']:
                errors.append(f"Недопустимое значение (разрешены: {', '.join(rules['enum'])})")

        # Проверка мин. элементов для списков
        if 'min_items' in rules and isinstance(value, list):
            if len(value) < rules['min_items']:
                errors.append(f"Минимум {rules['min_items']} элементов")

        return errors

    def validate_article(self, file_path):
        """Валидировать статью"""
        article_path = str(file_path.relative_to(self.root_dir))

        # Извлечь frontmatter
        frontmatter = self.extract_frontmatter(file_path)

        result = {
            'path': article_path,
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_fields': [],
            'invalid_fields': {}
        }

        # Нет frontmatter вообще
        if frontmatter is None:
            result['valid'] = False
            result['errors'].append("Frontmatter отсутствует или поврежден")
            return result

        # Проверка каждого поля
        for field_name, rules in self.schema.items():
            value = frontmatter.get(field_name)

            # Проверка обязательных полей
            if rules.get('required') and value is None:
                result['valid'] = False
                result['missing_fields'].append(field_name)
                result['errors'].append(f"Обязательное поле '{field_name}' отсутствует")
                continue

            # Валидация значения
            if value is not None:
                field_errors = self.validate_field(field_name, value, rules)

                if field_errors:
                    result['valid'] = False
                    result['invalid_fields'][field_name] = field_errors
                    for error in field_errors:
                        result['errors'].append(f"{field_name}: {error}")

        # Проверка дополнительных полей (не в схеме)
        extra_fields = set(frontmatter.keys()) - set(self.schema.keys())

        if extra_fields:
            result['warnings'].append(f"Дополнительные поля: {', '.join(extra_fields)}")

        # Проверка пустых значений
        for field_name, value in frontmatter.items():
            if isinstance(value, str) and not value.strip():
                result['warnings'].append(f"Поле '{field_name}' пустое")
            elif isinstance(value, list) and len(value) == 0:
                result['warnings'].append(f"Поле '{field_name}' - пустой список")

        return result

    def validate_all(self):
        """Валидировать все статьи"""
        print("✓ Валидация метаданных...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.validate_article(md_file)
            self.results.append(result)

        valid_count = sum(1 for r in self.results if r['valid'])
        invalid_count = len(self.results) - valid_count

        print(f"   Проверено статей: {len(self.results)}")
        print(f"   ✅ Валидные: {valid_count}")
        print(f"   ❌ С ошибками: {invalid_count}\n")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# ✓ Отчёт: Валидация метаданных\n\n")
        lines.append("> Проверка корректности frontmatter\n\n")

        # Статистика
        valid_count = sum(1 for r in self.results if r['valid'])
        invalid_count = len(self.results) - valid_count

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей**: {len(self.results)}\n")
        lines.append(f"- **✅ Валидных**: {valid_count}\n")
        lines.append(f"- **❌ С ошибками**: {invalid_count}\n")

        if invalid_count == 0:
            lines.append(f"- **Успешность**: 100% 🎉\n\n")
        else:
            success_rate = (valid_count / len(self.results)) * 100 if self.results else 0
            lines.append(f"- **Успешность**: {success_rate:.1f}%\n\n")

        # Список проблем
        invalid_results = [r for r in self.results if not r['valid']]

        if invalid_results:
            lines.append("## ❌ Статьи с ошибками\n\n")

            for result in invalid_results:
                lines.append(f"### {result['path']}\n\n")

                if result['errors']:
                    lines.append("**Ошибки:**\n")
                    for error in result['errors']:
                        lines.append(f"- ❌ {error}\n")
                    lines.append("\n")

                if result['warnings']:
                    lines.append("**Предупреждения:**\n")
                    for warning in result['warnings']:
                        lines.append(f"- ⚠️  {warning}\n")
                    lines.append("\n")

        # Предупреждения для валидных статей
        valid_with_warnings = [r for r in self.results if r['valid'] and r['warnings']]

        if valid_with_warnings:
            lines.append("## ⚠️  Предупреждения\n\n")

            for result in valid_with_warnings:
                lines.append(f"### {result['path']}\n\n")

                for warning in result['warnings']:
                    lines.append(f"- ⚠️  {warning}\n")

                lines.append("\n")

        # Рекомендации
        if invalid_count > 0:
            lines.append("## 💡 Рекомендации\n\n")
            lines.append("1. Убедитесь, что все обязательные поля присутствуют: `title`, `tags`, `category`\n")
            lines.append("2. Проверьте формат даты (должен быть YYYY-MM-DD)\n")
            lines.append("3. Difficulty должен быть: легкий, средний или сложный\n")
            lines.append("4. Tags должен содержать минимум 1 тег\n")

        output_file = self.root_dir / "METADATA_VALIDATION.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить результаты в JSON"""
        output_file = self.root_dir / "metadata_validation.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    validator = MetadataValidator(root_dir)
    validator.validate_all()
    validator.generate_report()
    validator.save_json()


if __name__ == "__main__":
    main()
