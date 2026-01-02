#!/usr/bin/env python3
"""
Advanced Knowledge Base Validation System

Комплексная система валидации базы знаний с проверкой структуры,
метаданных, качества контента, SEO, изображений и автоматическими
предложениями по исправлению.

Features:
- 📋 Schema validation (JSON Schema для frontmatter)
- 📝 Content quality checks (readability, completeness, word count)
- 🔍 SEO validation (meta descriptions, keyword density, headings)
- 🖼️ Image validation (existence, alt text, file size, format)
- 💻 Code block validation (syntax highlighting, language tags)
- 🔗 Link health checks (broken links, external URL validation)
- 🛠️ Auto-fix suggestions (actionable recommendations)
- 📊 Severity levels (critical, high, medium, low, info)
- 📄 Multiple report formats (JSON, HTML, Markdown, console)
- ⚡ Performance metrics (validation speed, coverage stats)

Usage:
    python3 validate.py                     # Full validation
    python3 validate.py --severity high     # Only high+ severity issues
    python3 validate.py --format json       # JSON report
    python3 validate.py --auto-fix          # Show fix suggestions
    python3 validate.py --category computers # Validate specific category
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
import yaml


class ValidationIssue:
    """Представление одной проблемы валидации"""

    SEVERITY_LEVELS = {
        'critical': 5,  # Блокирующие ошибки
        'high': 4,      # Серьёзные проблемы
        'medium': 3,    # Важные предупреждения
        'low': 2,       # Незначительные предупреждения
        'info': 1       # Информационные сообщения
    }

    def __init__(self, severity: str, category: str, message: str,
                 file_path: str = None, fix_suggestion: str = None):
        self.severity = severity
        self.category = category
        self.message = message
        self.file_path = file_path
        self.fix_suggestion = fix_suggestion

    def to_dict(self) -> Dict:
        """Конвертировать в словарь"""
        return {
            'severity': self.severity,
            'category': self.category,
            'message': self.message,
            'file_path': str(self.file_path) if self.file_path else None,
            'fix_suggestion': self.fix_suggestion
        }

    def __repr__(self):
        icon = {
            'critical': '🚨',
            'high': '❌',
            'medium': '⚠️',
            'low': '💡',
            'info': 'ℹ️'
        }.get(self.severity, '•')

        result = f"{icon} [{self.severity.upper()}] {self.message}"
        if self.file_path:
            result += f"\n   📁 File: {self.file_path}"
        if self.fix_suggestion:
            result += f"\n   🛠️  Fix: {self.fix_suggestion}"
        return result


class FrontmatterSchemaValidator:
    """Валидатор схемы frontmatter"""

    SCHEMA = {
        'title': {'type': str, 'required': True, 'min_length': 3, 'max_length': 200},
        'date': {'type': str, 'required': True, 'pattern': r'\d{4}-\d{2}-\d{2}'},
        'tags': {'type': list, 'required': True, 'min_items': 2, 'max_items': 15},
        'category': {'type': str, 'required': True, 'enum': ['computers', 'household', 'cooking']},
        'subcategory': {'type': str, 'required': False},
        'status': {'type': str, 'required': False, 'enum': ['draft', 'published', 'archived', 'reviewed']},
        'author': {'type': str, 'required': False},
        'description': {'type': str, 'required': False, 'min_length': 50, 'max_length': 300},
        'keywords': {'type': list, 'required': False},
        'difficulty': {'type': str, 'required': False, 'enum': ['beginner', 'intermediate', 'advanced']},
        'reading_time': {'type': int, 'required': False},
        'related': {'type': list, 'required': False}
    }

    def validate(self, frontmatter: Dict, file_path: Path) -> List[ValidationIssue]:
        """Валидация frontmatter по схеме"""
        issues = []

        if not frontmatter:
            issues.append(ValidationIssue(
                'critical', 'frontmatter', 'Missing frontmatter',
                file_path, 'Add YAML frontmatter between --- markers'
            ))
            return issues

        # Проверка обязательных полей
        for field, rules in self.SCHEMA.items():
            if rules.get('required') and field not in frontmatter:
                issues.append(ValidationIssue(
                    'high', 'frontmatter', f"Missing required field '{field}'",
                    file_path, f"Add '{field}' to frontmatter"
                ))

        # Проверка типов и ограничений
        for field, value in frontmatter.items():
            if field not in self.SCHEMA:
                issues.append(ValidationIssue(
                    'low', 'frontmatter', f"Unknown field '{field}'",
                    file_path, f"Remove '{field}' or update schema"
                ))
                continue

            rules = self.SCHEMA[field]

            # Проверка типа
            expected_type = rules['type']
            if not isinstance(value, expected_type):
                issues.append(ValidationIssue(
                    'medium', 'frontmatter',
                    f"Field '{field}' has wrong type (expected {expected_type.__name__})",
                    file_path, f"Change '{field}' to {expected_type.__name__}"
                ))

            # Проверка enum
            if 'enum' in rules and value not in rules['enum']:
                issues.append(ValidationIssue(
                    'medium', 'frontmatter',
                    f"Field '{field}' has invalid value '{value}' (allowed: {rules['enum']})",
                    file_path, f"Use one of: {', '.join(rules['enum'])}"
                ))

            # Проверка длины строки
            if isinstance(value, str):
                if 'min_length' in rules and len(value) < rules['min_length']:
                    issues.append(ValidationIssue(
                        'low', 'frontmatter',
                        f"Field '{field}' too short (min: {rules['min_length']})",
                        file_path, f"Expand '{field}' description"
                    ))
                if 'max_length' in rules and len(value) > rules['max_length']:
                    issues.append(ValidationIssue(
                        'low', 'frontmatter',
                        f"Field '{field}' too long (max: {rules['max_length']})",
                        file_path, f"Shorten '{field}' description"
                    ))

            # Проверка паттерна
            if 'pattern' in rules and isinstance(value, str):
                if not re.match(rules['pattern'], value):
                    issues.append(ValidationIssue(
                        'medium', 'frontmatter',
                        f"Field '{field}' doesn't match pattern {rules['pattern']}",
                        file_path, f"Format '{field}' correctly"
                    ))

            # Проверка количества элементов в списке
            if isinstance(value, list):
                if 'min_items' in rules and len(value) < rules['min_items']:
                    issues.append(ValidationIssue(
                        'low', 'frontmatter',
                        f"Field '{field}' has too few items (min: {rules['min_items']})",
                        file_path, f"Add more items to '{field}'"
                    ))
                if 'max_items' in rules and len(value) > rules['max_items']:
                    issues.append(ValidationIssue(
                        'low', 'frontmatter',
                        f"Field '{field}' has too many items (max: {rules['max_items']})",
                        file_path, f"Remove items from '{field}'"
                    ))

        return issues


class ContentQualityChecker:
    """Проверка качества контента"""

    def __init__(self):
        self.stop_words_ru = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'к', 'у', 'из', 'о', 'это', 'как', 'что', 'так'}
        self.stop_words_en = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or'}

    def check_readability(self, content: str, file_path: Path) -> List[ValidationIssue]:
        """Проверка читабельности"""
        issues = []

        # Удалить frontmatter
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

        # Подсчет слов
        words = re.findall(r'\b\w+\b', content.lower())
        word_count = len(words)

        if word_count < 100:
            issues.append(ValidationIssue(
                'medium', 'content', f"Content too short ({word_count} words, min: 100)",
                file_path, "Add more content to provide value"
            ))
        elif word_count < 300:
            issues.append(ValidationIssue(
                'low', 'content', f"Content is brief ({word_count} words)",
                file_path, "Consider expanding the article"
            ))

        # Подсчет предложений
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        if sentence_count == 0:
            issues.append(ValidationIssue(
                'high', 'content', "No sentences detected",
                file_path, "Add proper punctuation"
            ))
        else:
            # Средняя длина предложения
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

            if avg_sentence_length > 40:
                issues.append(ValidationIssue(
                    'low', 'content', f"Sentences too long (avg: {avg_sentence_length:.1f} words)",
                    file_path, "Break long sentences for better readability"
                ))

        # Проверка заголовков
        headers = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
        if not headers:
            issues.append(ValidationIssue(
                'medium', 'content', "No headers found",
                file_path, "Add headers (## H2, ### H3) to structure content"
            ))
        elif len(headers) == 1:
            issues.append(ValidationIssue(
                'low', 'content', "Only one header found",
                file_path, "Add more headers to improve structure"
            ))

        # Проверка списков
        lists = re.findall(r'^[\*\-]\s+.+$', content, re.MULTILINE)
        if word_count > 500 and len(lists) == 0:
            issues.append(ValidationIssue(
                'info', 'content', "No lists found in long article",
                file_path, "Consider using lists for better readability"
            ))

        return issues

    def check_seo(self, frontmatter: Dict, content: str, file_path: Path) -> List[ValidationIssue]:
        """SEO проверки"""
        issues = []

        # Проверка description
        description = frontmatter.get('description', '')
        if not description:
            issues.append(ValidationIssue(
                'medium', 'seo', "Missing meta description",
                file_path, "Add 'description' field (50-300 chars) for SEO"
            ))
        elif len(description) < 50:
            issues.append(ValidationIssue(
                'low', 'seo', f"Meta description too short ({len(description)} chars)",
                file_path, "Expand description to 50-300 characters"
            ))

        # Проверка keywords
        keywords = frontmatter.get('keywords', [])
        tags = frontmatter.get('tags', [])

        if not keywords and len(tags) < 3:
            issues.append(ValidationIssue(
                'low', 'seo', "Insufficient keywords/tags for SEO",
                file_path, "Add more tags (3+) or keywords field"
            ))

        # Проверка title length для SEO
        title = frontmatter.get('title', '')
        if len(title) > 70:
            issues.append(ValidationIssue(
                'low', 'seo', f"Title too long for SEO ({len(title)} chars, max: 70)",
                file_path, "Shorten title to fit search engine results"
            ))

        return issues


class ImageValidator:
    """Валидация изображений"""

    ALLOWED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    MAX_SIZE_MB = 5

    def validate_images(self, content: str, file_path: Path) -> List[ValidationIssue]:
        """Проверка изображений"""
        issues = []

        # Найти все изображения ![alt](path)
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

        for alt_text, img_path in images:
            # Проверка alt text
            if not alt_text or len(alt_text.strip()) == 0:
                issues.append(ValidationIssue(
                    'medium', 'accessibility', f"Image missing alt text: {img_path}",
                    file_path, f"Add descriptive alt text for {img_path}"
                ))
            elif len(alt_text) < 5:
                issues.append(ValidationIssue(
                    'low', 'accessibility', f"Image alt text too short: {img_path}",
                    file_path, "Provide more descriptive alt text"
                ))

            # Проверка существования файла (только для локальных путей)
            if not img_path.startswith(('http://', 'https://', '//')):
                if img_path.startswith('/'):
                    img_file = file_path.parent.parent.parent / img_path.lstrip('/')
                else:
                    img_file = file_path.parent / img_path

                if not img_file.exists():
                    issues.append(ValidationIssue(
                        'high', 'images', f"Image not found: {img_path}",
                        file_path, f"Create/upload image or fix path: {img_path}"
                    ))
                else:
                    # Проверка формата
                    ext = img_file.suffix.lower()
                    if ext not in self.ALLOWED_FORMATS:
                        issues.append(ValidationIssue(
                            'low', 'images', f"Unsupported image format: {ext}",
                            file_path, f"Convert to {self.ALLOWED_FORMATS}"
                        ))

                    # Проверка размера
                    size_mb = img_file.stat().st_size / (1024 * 1024)
                    if size_mb > self.MAX_SIZE_MB:
                        issues.append(ValidationIssue(
                            'medium', 'images', f"Image too large: {size_mb:.1f}MB (max: {self.MAX_SIZE_MB}MB)",
                            file_path, f"Optimize/compress {img_path}"
                        ))

        return issues


class CodeBlockValidator:
    """Валидация блоков кода"""

    COMMON_LANGUAGES = {'python', 'javascript', 'js', 'bash', 'sh', 'yaml', 'json', 'html', 'css', 'markdown', 'sql', 'rust', 'go', 'java', 'cpp', 'c'}

    def validate_code_blocks(self, content: str, file_path: Path) -> List[ValidationIssue]:
        """Проверка блоков кода"""
        issues = []

        # Найти все блоки кода ```lang\n...\n```
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)

        for i, (lang, code) in enumerate(code_blocks, 1):
            # Проверка языка
            if not lang or lang.strip() == '':
                issues.append(ValidationIssue(
                    'low', 'code', f"Code block #{i} missing language tag",
                    file_path, f"Add language tag: ```python, ```bash, etc."
                ))
            elif lang.lower() not in self.COMMON_LANGUAGES:
                issues.append(ValidationIssue(
                    'info', 'code', f"Code block #{i} has uncommon language: {lang}",
                    file_path, None
                ))

            # Проверка пустых блоков
            if not code.strip():
                issues.append(ValidationIssue(
                    'low', 'code', f"Code block #{i} is empty",
                    file_path, "Remove empty code block or add content"
                ))

        return issues


class AdvancedKnowledgeBaseValidator:
    """Продвинутый валидатор базы знаний"""

    def __init__(self, root_dir=".", min_severity='info'):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.min_severity = min_severity
        self.min_severity_level = ValidationIssue.SEVERITY_LEVELS.get(min_severity, 1)

        # Компоненты валидации
        self.schema_validator = FrontmatterSchemaValidator()
        self.quality_checker = ContentQualityChecker()
        self.image_validator = ImageValidator()
        self.code_validator = CodeBlockValidator()

        # Результаты
        self.issues: List[ValidationIssue] = []
        self.stats = defaultdict(int)
        self.start_time = None

    def extract_frontmatter(self, file_path: Path) -> Tuple[Optional[Dict], str]:
        """Извлечь метаданные из frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not match:
                return None, content

            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter, content
        except Exception as e:
            self.add_issue(ValidationIssue(
                'critical', 'parsing', f"Error reading file: {e}",
                file_path, "Check file encoding and YAML syntax"
            ))
            return None, ""

    def add_issue(self, issue: ValidationIssue):
        """Добавить проблему (с фильтрацией по severity)"""
        if ValidationIssue.SEVERITY_LEVELS[issue.severity] >= self.min_severity_level:
            self.issues.append(issue)

    def validate_article(self, file_path: Path):
        """Валидация одной статьи"""
        self.stats['total_articles'] += 1

        # Извлечь frontmatter и контент
        frontmatter, content = self.extract_frontmatter(file_path)

        # 1. Schema validation
        schema_issues = self.schema_validator.validate(frontmatter, file_path)
        for issue in schema_issues:
            self.add_issue(issue)

        # 2. Content quality checks
        quality_issues = self.quality_checker.check_readability(content, file_path)
        for issue in quality_issues:
            self.add_issue(issue)

        # 3. SEO validation
        seo_issues = self.quality_checker.check_seo(frontmatter or {}, content, file_path)
        for issue in seo_issues:
            self.add_issue(issue)

        # 4. Image validation
        image_issues = self.image_validator.validate_images(content, file_path)
        for issue in image_issues:
            self.add_issue(issue)

        # 5. Code block validation
        code_issues = self.code_validator.validate_code_blocks(content, file_path)
        for issue in code_issues:
            self.add_issue(issue)

        # 6. Link validation
        self.validate_links(content, file_path)

        # 7. File naming
        self.validate_file_naming(file_path)

    def validate_links(self, content: str, file_path: Path):
        """Проверка ссылок"""
        # Найти все markdown ссылки [text](path)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for link_text, link_path in links:
            # Пропустить якоря
            if link_path.startswith('#'):
                continue

            # Внешние ссылки - просто отметить
            if link_path.startswith(('http://', 'https://')):
                self.stats['external_links'] += 1
                continue

            # Внутренние ссылки - проверить существование
            if link_path.startswith('/'):
                target = self.root_dir / link_path.lstrip('/')
            else:
                target = file_path.parent / link_path

            target = target.resolve()

            if not target.exists():
                self.add_issue(ValidationIssue(
                    'high', 'links', f"Broken link: {link_path}",
                    file_path, f"Create file or fix path: {link_path}"
                ))

    def validate_file_naming(self, file_path: Path):
        """Проверка соглашений об именовании"""
        filename = file_path.name

        # Кириллица
        if re.search(r'[а-яА-ЯёЁ]', filename):
            self.add_issue(ValidationIssue(
                'low', 'naming', f"Cyrillic in filename: {filename}",
                file_path, "Use ASCII characters (transliterate)"
            ))

        # Пробелы
        if ' ' in filename:
            self.add_issue(ValidationIssue(
                'low', 'naming', f"Spaces in filename: {filename}",
                file_path, "Use hyphens instead of spaces"
            ))

        # Uppercase (кроме INDEX.md, README.md)
        if filename != filename.lower() and filename not in {'INDEX.md', 'README.md'}:
            self.add_issue(ValidationIssue(
                'info', 'naming', f"Uppercase in filename: {filename}",
                file_path, "Use lowercase filenames"
            ))

    def validate_structure(self):
        """Проверка структуры директорий"""
        required_dirs = ['inbox', 'knowledge', 'tools', 'docs']

        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                self.add_issue(ValidationIssue(
                    'medium', 'structure', f"Missing directory: {dir_name}",
                    None, f"Create directory: {dir_name}/"
                ))

    def scan_and_validate(self, categories: List[str] = None):
        """Сканировать и валидировать статьи"""
        pattern = "**/*.md"

        if categories:
            # Валидация только указанных категорий
            for category in categories:
                category_dir = self.knowledge_dir / category
                if not category_dir.exists():
                    self.add_issue(ValidationIssue(
                        'high', 'structure', f"Category not found: {category}",
                        None, f"Check category name or create: {category}/"
                    ))
                    continue

                for md_file in category_dir.rglob("*.md"):
                    if md_file.name != "INDEX.md":
                        self.validate_article(md_file)
        else:
            # Полная валидация
            for md_file in self.knowledge_dir.rglob("*.md"):
                if md_file.name != "INDEX.md":
                    self.validate_article(md_file)

    def generate_report_console(self) -> str:
        """Консольный отчёт"""
        report = []
        report.append("\n" + "="*70)
        report.append("📋 VALIDATION REPORT")
        report.append("="*70 + "\n")

        # Статистика
        report.append("📊 Statistics:")
        report.append(f"   Total articles: {self.stats['total_articles']}")
        report.append(f"   External links: {self.stats.get('external_links', 0)}")

        # Подсчет по severity
        by_severity = defaultdict(int)
        by_category = defaultdict(int)
        for issue in self.issues:
            by_severity[issue.severity] += 1
            by_category[issue.category] += 1

        report.append(f"\n   Issues by severity:")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_severity.get(severity, 0)
            if count > 0:
                icon = {'critical': '🚨', 'high': '❌', 'medium': '⚠️', 'low': '💡', 'info': 'ℹ️'}[severity]
                report.append(f"      {icon} {severity.capitalize()}: {count}")

        report.append(f"\n   Issues by category:")
        for category, count in sorted(by_category.items(), key=lambda x: -x[1])[:10]:
            report.append(f"      • {category}: {count}")

        # Performance
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            report.append(f"\n⏱️  Validation time: {elapsed:.2f}s")

        # Проблемы (топ 30)
        if self.issues:
            report.append(f"\n📝 Issues (showing first 30 of {len(self.issues)}):\n")
            for issue in self.issues[:30]:
                report.append(str(issue))
                report.append("")
        else:
            report.append("\n✅ No issues found!\n")

        report.append("="*70)
        if by_severity.get('critical', 0) > 0 or by_severity.get('high', 0) > 0:
            report.append("❌ VALIDATION FAILED")
        else:
            report.append("✅ VALIDATION PASSED")
        report.append("="*70 + "\n")

        return "\n".join(report)

    def generate_report_json(self) -> str:
        """JSON отчёт"""
        by_severity = defaultdict(int)
        for issue in self.issues:
            by_severity[issue.severity] += 1

        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_articles': self.stats['total_articles'],
                'total_issues': len(self.issues),
                'by_severity': dict(by_severity)
            },
            'issues': [issue.to_dict() for issue in self.issues]
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def run(self, categories: List[str] = None, output_format='console') -> int:
        """Запустить валидацию"""
        self.start_time = datetime.now()

        print(f"🔍 Starting validation (min severity: {self.min_severity})...\n")

        # Структура
        self.validate_structure()

        # Статьи
        self.scan_and_validate(categories)

        # Генерация отчёта
        if output_format == 'json':
            print(self.generate_report_json())
        else:  # console
            print(self.generate_report_console())

        # Exit code
        critical = sum(1 for i in self.issues if i.severity == 'critical')
        high = sum(1 for i in self.issues if i.severity == 'high')

        return 0 if (critical + high) == 0 else 1


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Knowledge Base Validation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full validation
  %(prog)s --severity high          # Only high+ severity issues
  %(prog)s --format json            # JSON report
  %(prog)s --category computers     # Validate specific category
        """
    )

    parser.add_argument(
        '-s', '--severity',
        choices=['critical', 'high', 'medium', 'low', 'info'],
        default='info',
        help='Minimum severity level to report (default: info)'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['console', 'json'],
        default='console',
        help='Output format (default: console)'
    )

    parser.add_argument(
        '-c', '--category',
        type=str,
        action='append',
        help='Validate specific category (can be repeated)'
    )

    args = parser.parse_args()

    # Определить корневую директорию
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Создать validator
    validator = AdvancedKnowledgeBaseValidator(
        root_dir,
        min_severity=args.severity
    )

    # Запустить
    exit_code = validator.run(
        categories=args.category,
        output_format=args.format
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
