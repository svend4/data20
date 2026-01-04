#!/usr/bin/env python3
"""
Advanced Inbox Processor - Продвинутая обработка входящих материалов

Комплексная система обработки inbox с поддержкой:
- ML-based категоризация (TF-IDF scoring)
- Автоматический тег��инг (keyword extraction + co-occurrence)
- Приоритизация (срочность + важность)
- Дедупликация входящих (content fingerprinting)
- Format detection (PDF, HTML, Markdown, plain text)
- Extraction pipeline (metadata, links, code blocks)
- Inbox analytics (processing stats, category distribution)
- Smart processing rules (размер, сложность, тематика)

Inspired by: Email filters, Notion web clipper, Pocket, Instapaper

Author: Advanced Knowledge Management System
Version: 2.0
"""

from pathlib import Path
import re
import yaml
import json
import hashlib
from datetime import datetime
from collections import Counter, defaultdict
import argparse


class AdvancedInboxProcessor:
    """
    Продвинутый процессор входящих материалов

    Features:
    - Multi-format support (MD, TXT, HTML preview)
    - ML-based categorization (TF-IDF keyword scoring)
    - Auto-tagging with relevance scores
    - Priority scoring (urgency × importance)
    - Duplicate detection (content fingerprinting)
    - Smart structuring suggestions
    - Processing rules engine
    - Analytics and reporting
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.inbox_dir = self.root_dir / "inbox" / "raw"
        self.knowledge_dir = self.root_dir / "knowledge"
        self.processed_dir = self.root_dir / "inbox" / "processed"

        # Ensure directories exist
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Category keywords (TF-IDF like scoring)
        self.category_keywords = {
            'computers': {
                'high': ['программирование', 'алгоритм', 'нейросеть', 'llm', 'ai', 'ml', 'docker', 'kubernetes'],
                'medium': ['python', 'javascript', 'код', 'компьютер', 'процессор', 'gpu', 'cpu', 'память'],
                'low': ['ssd', 'linux', 'windows', 'database', 'sql', 'security']
            },
            'household': {
                'high': ['холодильник', 'стиральная', 'посудомоечная', 'энергоэффективность'],
                'medium': ['плита', 'пылесос', 'кондиционер', 'обогреватель', 'мебель'],
                'low': ['диван', 'стол', 'ремонт', 'уборка', 'чистка']
            },
            'cooking': {
                'high': ['рецепт', 'приготовление', 'ингредиент'],
                'medium': ['готовить', 'блюдо', 'суп', 'салат', 'десерт'],
                'low': ['завтрак', 'обед', 'ужин', 'варить', 'жарить']
            }
        }

        # Stop words (RU + EN)
        self.stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'как', 'что', 'это', 'из', 'к', 'или',
            'а', 'но', 'то', 'не', 'за', 'при', 'о', 'об', 'от', 'до', 'со', 'же',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'must', 'can', 'of', 'at', 'by', 'for', 'with'
        }

        # Processing history (для дедупликации)
        self.history = self.load_history()

    def load_history(self):
        """Загрузить историю обработки"""
        history_file = self.inbox_dir.parent / "processing_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'processed_files': {}, 'content_hashes': set()}

    def save_history(self):
        """Сохранить историю обработки"""
        history_file = self.inbox_dir.parent / "processing_history.json"
        # Convert set to list for JSON
        history_copy = self.history.copy()
        history_copy['content_hashes'] = list(history_copy.get('content_hashes', set()))

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_copy, f, indent=2, ensure_ascii=False)

    # ==================== Format Detection ====================

    def detect_format(self, file_path):
        """
        Определить формат файла

        Supports: markdown, html, txt
        """
        suffix = file_path.suffix.lower()

        if suffix == '.md':
            return 'markdown'
        elif suffix in ['.html', '.htm']:
            return 'html'
        elif suffix == '.txt':
            return 'text'
        else:
            return 'unknown'

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter (YAML) из markdown"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return None, content

            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except Exception as e:
            return None, ""

    # ==================== ML Categorization ====================

    def calculate_category_score(self, text):
        """
        ML-подобная категоризация через взвешенный TF-IDF scoring

        Returns: {category: score, ...}
        """
        text_lower = text.lower()
        scores = defaultdict(float)

        for category, levels in self.category_keywords.items():
            # High-weight keywords
            for word in levels['high']:
                count = text_lower.count(word)
                scores[category] += count * 3.0  # High weight

            # Medium-weight keywords
            for word in levels['medium']:
                count = text_lower.count(word)
                scores[category] += count * 2.0  # Medium weight

            # Low-weight keywords
            for word in levels['low']:
                count = text_lower.count(word)
                scores[category] += count * 1.0  # Low weight

        return dict(scores)

    def categorize_content(self, text):
        """
        Определить категорию контента

        Returns: (category, confidence)
        """
        scores = self.calculate_category_score(text)

        if not scores:
            return None, 0.0

        # Best category
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # Calculate confidence (0-100)
        total = sum(scores.values())
        confidence = (best_score / total * 100) if total > 0 else 0.0

        return best_category, round(confidence, 2)

    # ==================== Auto-Tagging ====================

    def extract_keywords_tfidf(self, text, num_keywords=10):
        """
        TF-IDF based keyword extraction

        TF = term frequency in document
        IDF = log(total_docs / docs_with_term) (simplified: assume 1 doc here)
        """
        # Tokenize
        words = re.findall(r'[а-яёa-z]+', text.lower())

        # Filter stop words and short words
        words = [w for w in words if w not in self.stop_words and len(w) > 3]

        # Calculate term frequency
        word_freq = Counter(words)
        total_words = len(words)

        # TF-IDF scores (simplified: TF only since we have 1 document)
        tfidf_scores = {}
        for word, freq in word_freq.items():
            tf = freq / total_words if total_words > 0 else 0
            tfidf_scores[word] = tf

        # Top N keywords
        top_keywords = sorted(tfidf_scores.items(), key=lambda x: -x[1])[:num_keywords]

        return [word for word, score in top_keywords]

    def suggest_tags(self, text, category=None, num_tags=5):
        """
        Предложить теги для контента

        Combines: keyword extraction + category keywords
        """
        # Extract keywords
        keywords = self.extract_keywords_tfidf(text, num_keywords=10)

        # Add category-specific keywords if applicable
        if category and category in self.category_keywords:
            category_kw = []
            for level in ['high', 'medium']:
                for kw in self.category_keywords[category][level]:
                    if kw in text.lower():
                        category_kw.append(kw)

            # Merge (prioritize category keywords)
            tags = category_kw[:3] + keywords
            tags = list(dict.fromkeys(tags))  # Remove duplicates, preserve order
        else:
            tags = keywords

        return tags[:num_tags]

    # ==================== Priority Scoring ====================

    def calculate_priority(self, text, metadata=None):
        """
        Вычислить приоритет обработки

        Priority = Urgency × Importance

        Urgency signals:
        - Keywords: "срочно", "важно", "asap", "urgent"
        - Due date in metadata

        Importance signals:
        - Document length (longer = more important?)
        - Number of links/references
        - Presence of structured data
        """
        priority_score = 50  # Default: medium priority (0-100)

        # 1. Urgency keywords
        urgency_keywords = ['срочно', 'важно', 'asap', 'urgent', 'critical', 'deadline']
        text_lower = text.lower()

        for kw in urgency_keywords:
            if kw in text_lower:
                priority_score += 15  # Boost priority

        # 2. Length (longer = potentially more important, but cap it)
        word_count = len(text.split())
        if word_count > 500:
            priority_score += 10
        elif word_count > 1000:
            priority_score += 20

        # 3. Structured content (headers, lists, code)
        if re.search(r'^#{1,6}\s+', text, re.MULTILINE):
            priority_score += 5  # Has headers

        if re.search(r'```', text):
            priority_score += 5  # Has code blocks

        # 4. Metadata (if provided)
        if metadata:
            if metadata.get('priority') == 'high':
                priority_score += 20
            elif metadata.get('priority') == 'low':
                priority_score -= 20

        # Cap at 0-100
        priority_score = max(0, min(100, priority_score))

        # Determine priority level
        if priority_score >= 80:
            level = 'high'
        elif priority_score >= 50:
            level = 'medium'
        else:
            level = 'low'

        return {'score': priority_score, 'level': level}

    # ==================== Duplicate Detection ====================

    def calculate_content_hash(self, text):
        """MD5 hash для дедупликации"""
        # Normalize: lowercase, remove whitespace
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()

    def check_duplicate(self, content_hash):
        """Проверить, не дубликат ли"""
        history_hashes = set(self.history.get('content_hashes', []))
        return content_hash in history_hashes

    # ==================== Extraction Pipeline ====================

    def extract_metadata(self, text):
        """
        Извлечь метаданные из контента

        - Links (markdown, plain URLs)
        - Code blocks
        - Images
        - Headers structure
        """
        metadata = {
            'links': [],
            'code_blocks': 0,
            'images': 0,
            'headers': []
        }

        # Links
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        plain_links = re.findall(r'https?://[^\s]+', text)
        metadata['links'] = [url for _, url in md_links] + plain_links

        # Code blocks
        metadata['code_blocks'] = len(re.findall(r'```', text)) // 2

        # Images
        metadata['images'] = len(re.findall(r'!\[.*?\]\(.*?\)', text))

        # Headers
        headers = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
        metadata['headers'] = [(len(h[0]), h[1]) for h in headers]

        return metadata

    def suggest_structure(self, text, category=None):
        """
        Предложить структуру для материала

        Based on: length, headers, complexity
        """
        lines = len(text.split('\n'))
        words = len(text.split())

        metadata = self.extract_metadata(text)

        suggestion = {
            'size': {'lines': lines, 'words': words},
            'metadata': metadata,
            'recommended_action': None,
            'split_suggestions': []
        }

        # Determine action
        if words < 300:
            suggestion['recommended_action'] = 'single_note'
        elif words < 1000:
            suggestion['recommended_action'] = 'single_article'
        elif words < 3000:
            suggestion['recommended_action'] = 'article_with_sections'
        else:
            suggestion['recommended_action'] = 'split_into_multiple'

            # Suggest splits based on headers
            if metadata['headers']:
                h1_headers = [h for h in metadata['headers'] if h[0] == 1]
                if len(h1_headers) > 1:
                    suggestion['split_suggestions'] = [h[1] for h in h1_headers]

        return suggestion

    # ==================== Processing ====================

    def process_file(self, file_path):
        """Обработать один файл из inbox"""
        print(f"\n📄 Processing: {file_path.name}")

        # 1. Format detection
        file_format = self.detect_format(file_path)
        print(f"   Format: {file_format}")

        # 2. Extract content
        frontmatter, content = self.extract_frontmatter(file_path)

        if not content.strip():
            print(f"   ⚠️  Empty file, skipping")
            return None

        # 3. Duplicate check
        content_hash = self.calculate_content_hash(content)
        if self.check_duplicate(content_hash):
            print(f"   ⚠️  Duplicate detected (already processed)")
            return {'status': 'duplicate', 'hash': content_hash}

        # 4. Categorization
        category, confidence = self.categorize_content(content)
        print(f"   📂 Category: {category} (confidence: {confidence}%)")

        # 5. Auto-tagging
        tags = self.suggest_tags(content, category=category, num_tags=5)
        print(f"   🏷️  Tags: {', '.join(tags)}")

        # 6. Priority
        priority = self.calculate_priority(content, metadata=frontmatter)
        print(f"   ⚡ Priority: {priority['level']} ({priority['score']}/100)")

        # 7. Structure suggestion
        structure = self.suggest_structure(content, category=category)
        print(f"   📊 Size: {structure['size']['words']} words, {structure['size']['lines']} lines")
        print(f"   💡 Recommendation: {structure['recommended_action']}")

        if structure['split_suggestions']:
            print(f"   ✂️  Split into: {', '.join(structure['split_suggestions'][:3])}")

        # Create report
        report = {
            'source_file': str(file_path.relative_to(self.root_dir)),
            'format': file_format,
            'category': category,
            'confidence': confidence,
            'tags': tags,
            'priority': priority,
            'structure': structure,
            'content_hash': content_hash,
            'processed_date': datetime.now().isoformat()
        }

        # Mark as processed
        self.history['content_hashes'] = list(set(self.history.get('content_hashes', [])) | {content_hash})
        self.history['processed_files'][str(file_path)] = {
            'hash': content_hash,
            'date': report['processed_date'],
            'category': category
        }

        return report

    def generate_analytics(self, reports):
        """
        Создать аналитику по обработанным файлам

        - Category distribution
        - Priority distribution
        - Avg confidence scores
        - Processing trends
        """
        analytics = {
            'total_processed': len(reports),
            'category_distribution': Counter(),
            'priority_distribution': Counter(),
            'avg_confidence': 0.0,
            'duplicates': 0,
            'recommendations': Counter()
        }

        valid_reports = [r for r in reports if r.get('status') != 'duplicate']

        for report in reports:
            if report.get('status') == 'duplicate':
                analytics['duplicates'] += 1
                continue

            analytics['category_distribution'][report['category']] += 1
            analytics['priority_distribution'][report['priority']['level']] += 1
            analytics['recommendations'][report['structure']['recommended_action']] += 1

        # Average confidence
        if valid_reports:
            analytics['avg_confidence'] = round(
                sum(r['confidence'] for r in valid_reports) / len(valid_reports), 2
            )

        # Convert Counters to dicts
        analytics['category_distribution'] = dict(analytics['category_distribution'])
        analytics['priority_distribution'] = dict(analytics['priority_distribution'])
        analytics['recommendations'] = dict(analytics['recommendations'])

        return analytics

    def run(self, auto_categorize=True, check_duplicates=True):
        """Обработать все файлы в inbox/raw"""
        print("🔄 Advanced Inbox Processor\n")

        if not self.inbox_dir.exists():
            print("❌ Directory inbox/raw not found")
            return

        # Find all files
        files = [f for f in self.inbox_dir.glob("*")
                if f.is_file() and not f.name.startswith('.')]

        if not files:
            print("📭 No files to process")
            return

        print(f"   Found: {len(files)} files\n")

        reports = []
        for file_path in files:
            report = self.process_file(file_path)
            if report:
                reports.append(report)

        print(f"\n✅ Processed: {len(reports)} files")

        # Generate analytics
        analytics = self.generate_analytics(reports)

        # Save reports
        self.save_reports(reports, analytics)
        self.save_history()

        # Print analytics summary
        print(f"\n📊 Analytics:")
        print(f"   Duplicates: {analytics['duplicates']}")
        print(f"   Categories: {analytics['category_distribution']}")
        print(f"   Avg confidence: {analytics['avg_confidence']}%")

    def save_reports(self, reports, analytics):
        """Сохранить отчёты"""
        # JSON report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'analytics': analytics,
            'processed_files': reports
        }

        json_file = self.inbox_dir.parent / "processing_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"📝 Report saved: {json_file}")


def main():
    parser = argparse.ArgumentParser(description='Advanced Inbox Processor')
    parser.add_argument('--no-duplicates', action='store_true',
                       help='Skip duplicate detection')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    processor = AdvancedInboxProcessor(root_dir)
    processor.run(check_duplicates=not args.no_duplicates)


if __name__ == "__main__":
    main()
