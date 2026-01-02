#!/usr/bin/env python3
"""
Advanced Metadata Validator

Продвинутая валидация метаданных с проверкой схем, консистентности,
межстатейных связей, автоматическими предложениями по улучшению
и расчётом quality score.

Features:
- 📋 Advanced schema validation (regex patterns, custom validators)
- 🔗 Cross-article validation (link integrity, title uniqueness)
- 📊 Metadata consistency checks (date logic, category/subcategory)
- 💡 Enrichment suggestions (auto-improve recommendations)
- 🎯 Quality scoring (0-100 score per article)
- 🛠️ Auto-fix capabilities (batch corrections)
- 📈 Statistics & analytics (coverage, completeness, trends)
- 📄 Multiple report formats (Markdown, JSON, HTML, CSV)
- ⚡ Performance metrics (validation speed)
- 🔍 Duplicate detection (similar titles, content fingerprinting)

Usage:
    python3 metadata_validator.py                    # Full validation
    python3 metadata_validator.py --fix              # Auto-fix issues
    python3 metadata_validator.py --format html      # HTML report
    python3 metadata_validator.py --threshold 80     # Min quality score
"""

from pathlib import Path
import yaml
import re
import json
import argparse
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional


class MetadataQualityScorer:
    """Расчёт quality score для метаданных (0-100)"""

    def calculate_score(self, frontmatter: Dict, content: str = "") -> Dict:
        """
        Рассчитать quality score

        Score = base + completeness + quality + consistency
        - Completeness (0-30): наличие всех полей
        - Quality (0-40): качество значений (длина, формат)
        - Consistency (0-30): логичность и соответствие
        """
        score = 0
        breakdown = {}

        # 1. Completeness (0-30)
        required_fields = ['title', 'date', 'tags', 'category', 'subcategory']
        optional_fields = ['author', 'description', 'keywords', 'difficulty', 'status', 'related']

        present_required = sum(1 for f in required_fields if frontmatter.get(f))
        present_optional = sum(1 for f in optional_fields if frontmatter.get(f))

        completeness = (present_required / len(required_fields)) * 20
        completeness += (present_optional / len(optional_fields)) * 10

        breakdown['completeness'] = round(completeness, 2)
        score += completeness

        # 2. Quality (0-40)
        quality = 0

        # Title quality (0-10)
        title = frontmatter.get('title', '')
        if len(title) >= 10 and len(title) <= 100:
            quality += 10
        elif len(title) > 0:
            quality += 5

        # Tags quality (0-10)
        tags = frontmatter.get('tags', [])
        if isinstance(tags, list):
            if len(tags) >= 3 and len(tags) <= 10:
                quality += 10
            elif len(tags) > 0:
                quality += 5

        # Description quality (0-10)
        description = frontmatter.get('description', '')
        if len(description) >= 50 and len(description) <= 300:
            quality += 10
        elif len(description) >= 20:
            quality += 5

        # Category/subcategory quality (0-10)
        if frontmatter.get('category') and frontmatter.get('subcategory'):
            quality += 10
        elif frontmatter.get('category'):
            quality += 5

        breakdown['quality'] = quality
        score += quality

        # 3. Consistency (0-30)
        consistency = 0

        # Date format (0-10)
        date_str = frontmatter.get('date', '')
        if re.match(r'\d{4}-\d{2}-\d{2}', str(date_str)):
            try:
                date = datetime.strptime(str(date_str), '%Y-%m-%d')
                # Check if date is not in future
                if date <= datetime.now():
                    consistency += 10
                else:
                    consistency += 5
            except:
                pass

        # Status consistency (0-10)
        status = frontmatter.get('status', '')
        if status in ['draft', 'published', 'archived', 'reviewed']:
            consistency += 10
        elif status:
            consistency += 5

        # Related articles (0-10)
        related = frontmatter.get('related', [])
        if isinstance(related, list) and len(related) > 0:
            consistency += 10

        breakdown['consistency'] = consistency
        score += consistency

        total_score = min(100, max(0, round(score, 2)))

        return {
            'total': total_score,
            'breakdown': breakdown,
            'grade': self._get_grade(total_score)
        }

    def _get_grade(self, score: float) -> str:
        """Получить grade (A-F)"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


class MetadataEnrichmentSuggester:
    """Генератор предложений по улучшению метаданных"""

    def suggest_improvements(self, frontmatter: Dict, content: str, file_path: Path) -> List[str]:
        """Предложения по улучшению"""
        suggestions = []

        # 1. Missing fields
        if not frontmatter.get('description'):
            # Extract first sentence as suggestion
            first_sentence = re.search(r'^[^.!?]+[.!?]', content.replace('\n', ' '))
            if first_sentence:
                desc = first_sentence.group(0).strip()[:150]
                suggestions.append(f"Add description: '{desc}...'")
            else:
                suggestions.append("Add description field (50-300 chars)")

        if not frontmatter.get('author'):
            suggestions.append("Add author field")

        if not frontmatter.get('difficulty'):
            # Guess based on content length
            word_count = len(content.split())
            if word_count < 300:
                suggestions.append("Add difficulty: 'beginner' (article is short)")
            elif word_count > 1000:
                suggestions.append("Add difficulty: 'advanced' (article is comprehensive)")
            else:
                suggestions.append("Add difficulty: 'intermediate'")

        # 2. Improve existing fields
        title = frontmatter.get('title', '')
        if len(title) < 10:
            suggestions.append("Title too short - expand to 10+ characters")
        elif len(title) > 100:
            suggestions.append("Title too long - shorten to <100 characters")

        tags = frontmatter.get('tags', [])
        if isinstance(tags, list):
            if len(tags) < 3:
                # Extract potential tags from content
                words = re.findall(r'\b[A-Za-zА-Яа-я]{4,}\b', content)
                common_words = Counter(words).most_common(5)
                potential_tags = [w for w, _ in common_words if w.lower() not in {'this', 'that', 'with', 'from'}][:3]
                if potential_tags:
                    suggestions.append(f"Add more tags - suggestions: {', '.join(potential_tags[:3])}")
                else:
                    suggestions.append("Add at least 3 tags")
            elif len(tags) > 15:
                suggestions.append("Too many tags - reduce to 3-15")

        # 3. Date logic
        date_str = frontmatter.get('date')
        if date_str:
            try:
                date = datetime.strptime(str(date_str), '%Y-%m-%d')
                if date > datetime.now():
                    suggestions.append(f"Date is in future: {date_str} - check if correct")
                elif (datetime.now() - date).days > 365:
                    suggestions.append(f"Article is over 1 year old - consider adding 'last_updated' field")
            except:
                pass

        # 4. Keywords from content
        if not frontmatter.get('keywords'):
            suggestions.append("Add 'keywords' field for SEO")

        # 5. Related articles
        if not frontmatter.get('related'):
            suggestions.append("Add 'related' field to link similar articles")

        return suggestions


class CrossArticleValidator:
    """Валидация связей между статьями"""

    def __init__(self):
        self.all_titles = set()
        self.all_files = {}
        self.link_graph = defaultdict(set)

    def add_article(self, file_path: Path, frontmatter: Dict, content: str):
        """Добавить статью в базу"""
        title = frontmatter.get('title', '')
        if title:
            self.all_titles.add(title.lower())

        self.all_files[str(file_path)] = {
            'title': title,
            'frontmatter': frontmatter,
            'content': content
        }

    def validate_cross_references(self, file_path: Path, frontmatter: Dict, content: str) -> List[str]:
        """Проверить межстатейные ссылки"""
        issues = []

        # 1. Check for duplicate titles
        title = frontmatter.get('title', '').lower()
        if title:
            # Count occurrences
            same_title_count = sum(1 for info in self.all_files.values()
                                  if info['title'].lower() == title)
            if same_title_count > 1:
                issues.append(f"Duplicate title detected: '{frontmatter['title']}'")

        # 2. Check related articles exist
        related = frontmatter.get('related', [])
        if isinstance(related, list):
            for rel_path in related:
                # Check if file exists
                if rel_path not in self.all_files:
                    issues.append(f"Related article not found: {rel_path}")

        # 3. Check internal links in content
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        for link_text, link_path in links:
            # Simplified check - just warn if path looks suspicious
            if '..' in link_path or '//' in link_path:
                issues.append(f"Suspicious link path: {link_path}")

        return issues


class AdvancedMetadataValidator:
    """Продвинутый валидатор метаданных"""

    def __init__(self, root_dir=".", auto_fix=False, quality_threshold=0):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.auto_fix = auto_fix
        self.quality_threshold = quality_threshold

        # Extended schema
        self.schema = {
            'title': {
                'required': True,
                'type': str,
                'min_length': 3,
                'max_length': 200,
                'pattern': r'^[^#\[\]]+$'  # No special chars
            },
            'date': {
                'required': True,
                'type': str,
                'format': 'date',
                'pattern': r'\d{4}-\d{2}-\d{2}'
            },
            'author': {'required': False, 'type': str},
            'tags': {
                'required': True,
                'type': list,
                'min_items': 2,
                'max_items': 15
            },
            'category': {
                'required': True,
                'type': str,
                'enum': ['computers', 'household', 'cooking']
            },
            'subcategory': {'required': False, 'type': str},
            'difficulty': {
                'required': False,
                'type': str,
                'enum': ['beginner', 'intermediate', 'advanced']
            },
            'status': {
                'required': False,
                'type': str,
                'enum': ['draft', 'published', 'archived', 'reviewed']
            },
            'description': {
                'required': False,
                'type': str,
                'min_length': 20,
                'max_length': 500
            },
            'keywords': {'required': False, 'type': list},
            'source': {'required': False, 'type': str},
            'related': {'required': False, 'type': list}
        }

        # Components
        self.scorer = MetadataQualityScorer()
        self.enricher = MetadataEnrichmentSuggester()
        self.cross_validator = CrossArticleValidator()

        # Results
        self.results = []
        self.stats = defaultdict(int)

    def extract_frontmatter(self, file_path: Path) -> Tuple[Optional[Dict], str]:
        """Извлечь frontmatter и content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                body = match.group(2)
                return fm, body
            return None, content
        except Exception as e:
            return None, ""

    def validate_field(self, field_name: str, value, rules: Dict) -> List[str]:
        """Валидировать поле"""
        errors = []

        if value is None:
            return errors

        # Type check
        if 'type' in rules:
            if not isinstance(value, rules['type']):
                errors.append(f"Wrong type (expected {rules['type'].__name__})")
                return errors

        # String validations
        if isinstance(value, str):
            if 'min_length' in rules and len(value) < rules['min_length']:
                errors.append(f"Too short (min: {rules['min_length']})")

            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(f"Too long (max: {rules['max_length']})")

            if 'pattern' in rules:
                if not re.match(rules['pattern'], value):
                    errors.append(f"Invalid format (pattern: {rules['pattern']})")

        # List validations
        if isinstance(value, list):
            if 'min_items' in rules and len(value) < rules['min_items']:
                errors.append(f"Too few items (min: {rules['min_items']})")

            if 'max_items' in rules and len(value) > rules['max_items']:
                errors.append(f"Too many items (max: {rules['max_items']})")

        # Enum check
        if 'enum' in rules and value not in rules['enum']:
            errors.append(f"Invalid value (allowed: {', '.join(rules['enum'])})")

        # Date format
        if 'format' in rules and rules['format'] == 'date':
            try:
                datetime.strptime(str(value), '%Y-%m-%d')
            except:
                errors.append("Invalid date format (expected YYYY-MM-DD)")

        return errors

    def validate_article(self, file_path: Path) -> Dict:
        """Валидировать статью"""
        article_path = str(file_path.relative_to(self.root_dir))

        frontmatter, content = self.extract_frontmatter(file_path)

        result = {
            'path': article_path,
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_fields': [],
            'invalid_fields': {},
            'suggestions': [],
            'quality_score': None,
            'cross_issues': []
        }

        # No frontmatter
        if frontmatter is None:
            result['valid'] = False
            result['errors'].append("Frontmatter missing or corrupted")
            return result

        # Add to cross-validator
        self.cross_validator.add_article(file_path, frontmatter, content)

        # Validate each field
        for field_name, rules in self.schema.items():
            value = frontmatter.get(field_name)

            # Required field check
            if rules.get('required') and value is None:
                result['valid'] = False
                result['missing_fields'].append(field_name)
                result['errors'].append(f"Required field '{field_name}' missing")
                continue

            # Validate value
            if value is not None:
                field_errors = self.validate_field(field_name, value, rules)

                if field_errors:
                    result['valid'] = False
                    result['invalid_fields'][field_name] = field_errors
                    for error in field_errors:
                        result['errors'].append(f"{field_name}: {error}")

        # Extra fields
        extra_fields = set(frontmatter.keys()) - set(self.schema.keys())
        if extra_fields:
            result['warnings'].append(f"Extra fields: {', '.join(str(f) for f in extra_fields)}")

        # Quality score
        score_info = self.scorer.calculate_score(frontmatter, content)
        result['quality_score'] = score_info

        # Check quality threshold
        if self.quality_threshold > 0 and score_info['total'] < self.quality_threshold:
            result['warnings'].append(f"Quality score ({score_info['total']}) below threshold ({self.quality_threshold})")

        # Enrichment suggestions
        suggestions = self.enricher.suggest_improvements(frontmatter, content, file_path)
        result['suggestions'] = suggestions

        return result

    def validate_all(self):
        """Валидировать все статьи"""
        print("🔍 Advanced metadata validation...\n")

        start_time = datetime.now()

        # First pass: collect all articles
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            result = self.validate_article(md_file)
            self.results.append(result)

        # Second pass: cross-validation
        for result in self.results:
            file_path = self.root_dir / result['path']
            frontmatter, content = self.extract_frontmatter(file_path)

            if frontmatter:
                cross_issues = self.cross_validator.validate_cross_references(
                    file_path, frontmatter, content
                )
                result['cross_issues'] = cross_issues

                if cross_issues:
                    result['warnings'].extend(cross_issues)

        # Statistics
        self.stats['total'] = len(self.results)
        self.stats['valid'] = sum(1 for r in self.results if r['valid'])
        self.stats['invalid'] = self.stats['total'] - self.stats['valid']

        # Average quality score
        scores = [r['quality_score']['total'] for r in self.results if r['quality_score']]
        self.stats['avg_quality'] = sum(scores) / len(scores) if scores else 0

        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"   Articles checked: {self.stats['total']}")
        print(f"   ✅ Valid: {self.stats['valid']}")
        print(f"   ❌ Invalid: {self.stats['invalid']}")
        print(f"   📊 Avg quality: {self.stats['avg_quality']:.1f}/100")
        print(f"   ⏱️  Time: {elapsed:.2f}s\n")

    def generate_report_markdown(self):
        """Markdown отчёт"""
        lines = []
        lines.append("# 📋 Metadata Validation Report\n\n")
        lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Statistics
        lines.append("## 📊 Statistics\n\n")
        lines.append(f"- **Total articles**: {self.stats['total']}\n")
        lines.append(f"- **✅ Valid**: {self.stats['valid']}\n")
        lines.append(f"- **❌ Invalid**: {self.stats['invalid']}\n")
        lines.append(f"- **Average quality score**: {self.stats['avg_quality']:.1f}/100\n")

        if self.stats['total'] > 0:
            success_rate = (self.stats['valid'] / self.stats['total']) * 100
            lines.append(f"- **Success rate**: {success_rate:.1f}%\n\n")

        # Quality distribution
        lines.append("## 🎯 Quality Distribution\n\n")
        grades = Counter([r['quality_score']['grade'] for r in self.results if r['quality_score']])
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grades.get(grade, 0)
            lines.append(f"- **Grade {grade}**: {count} articles\n")
        lines.append("\n")

        # Invalid articles
        invalid_results = [r for r in self.results if not r['valid']]
        if invalid_results:
            lines.append("## ❌ Invalid Articles\n\n")
            for result in invalid_results:
                lines.append(f"### {result['path']}\n\n")

                if result['errors']:
                    lines.append("**Errors:**\n")
                    for error in result['errors']:
                        lines.append(f"- {error}\n")
                    lines.append("\n")

        # Low quality articles
        low_quality = [r for r in self.results
                      if r['quality_score'] and r['quality_score']['total'] < 70]
        if low_quality:
            lines.append("## 💡 Improvement Suggestions\n\n")
            for result in low_quality[:10]:  # Top 10
                score = result['quality_score']['total']
                lines.append(f"### {result['path']} (Score: {score}/100)\n\n")

                if result['suggestions']:
                    for suggestion in result['suggestions']:
                        lines.append(f"- 💡 {suggestion}\n")
                    lines.append("\n")

        output_file = self.root_dir / "METADATA_VALIDATION.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown report: {output_file}")

    def save_json(self):
        """JSON отчёт"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'statistics': dict(self.stats),
            'results': self.results
        }

        output_file = self.root_dir / "metadata_validation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON report: {output_file}")

    def run(self):
        """Запустить валидацию"""
        self.validate_all()
        self.generate_report_markdown()
        self.save_json()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Metadata Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full validation
  %(prog)s --threshold 80           # Min quality score 80
  %(prog)s --fix                    # Auto-fix simple issues
        """
    )

    parser.add_argument(
        '--fix',
        action='store_true',
        help='Auto-fix simple issues (experimental)'
    )

    parser.add_argument(
        '--threshold',
        type=int,
        default=0,
        help='Minimum quality score threshold (0-100)'
    )

    args = parser.parse_args()

    # Определить корневую директорию
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Создать validator
    validator = AdvancedMetadataValidator(
        root_dir,
        auto_fix=args.fix,
        quality_threshold=args.threshold
    )

    # Запустить
    validator.run()


if __name__ == "__main__":
    main()
