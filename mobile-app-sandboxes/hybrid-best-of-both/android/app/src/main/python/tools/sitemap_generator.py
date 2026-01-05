#!/usr/bin/env python3
"""
Advanced Sitemap Generator - Продвинутый генератор sitemap.xml
Функции:
- Dynamic priority calculation (based on importance)
- Change frequency detection
- Multi-sitemap support (50,000 URLs per file)
- Sitemap index generation
- Ping search engines (Google, Bing)
- Image sitemap support
- Validation
- Compression (.gz)
- robots.txt generation
- Statistics and reporting

Вдохновлено: Google Search Console, Yoast SEO, XML Sitemap generators
"""

from pathlib import Path
import yaml
import re
from datetime import datetime, timedelta
import gzip
import urllib.request
import urllib.parse
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET
import subprocess
import json
import time


class SEOAnalyzer:
    """
    SEO анализатор для статей
    Проверка title, meta description, H1, keyword density, SEO score
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def analyze_article(self, file_path, frontmatter, content):
        """
        Анализ SEO метрик одной статьи

        Returns: dict с SEO метриками и score (0-100)
        """
        seo_score = 0
        issues = []
        recommendations = []

        # 1. Title analysis (20 баллов)
        title = frontmatter.get('title', '') if frontmatter else ''
        title_length = len(title)

        if 50 <= title_length <= 60:
            seo_score += 20
        elif 40 <= title_length <= 70:
            seo_score += 15
            recommendations.append(f"Title length {title_length} chars (optimal: 50-60)")
        elif title_length > 0:
            seo_score += 10
            issues.append(f"Title too {'long' if title_length > 70 else 'short'} ({title_length} chars)")
        else:
            issues.append("Missing title")

        # 2. H1 heading analysis (15 баллов)
        h1_headings = re.findall(r'^# ([^\n]+)', content, re.MULTILINE)

        if len(h1_headings) == 1:
            seo_score += 15
        elif len(h1_headings) == 0:
            issues.append("No H1 heading found")
        else:
            seo_score += 5
            issues.append(f"Multiple H1 headings ({len(h1_headings)}) - should be 1")

        # 3. Meta description (15 баллов)
        description = frontmatter.get('description', '') if frontmatter else ''
        desc_length = len(description)

        if 150 <= desc_length <= 160:
            seo_score += 15
        elif 120 <= desc_length <= 180:
            seo_score += 10
            recommendations.append(f"Description length {desc_length} chars (optimal: 150-160)")
        elif desc_length > 0:
            seo_score += 5
            issues.append(f"Description too {'long' if desc_length > 180 else 'short'} ({desc_length} chars)")
        else:
            issues.append("Missing meta description")

        # 4. Content length (15 баллов)
        word_count = len(re.findall(r'\b[а-яёa-z]+\b', content.lower()))

        if word_count >= 1000:
            seo_score += 15
        elif word_count >= 500:
            seo_score += 10
        elif word_count >= 300:
            seo_score += 5
        else:
            issues.append(f"Content too short ({word_count} words, recommended: 500+)")

        # 5. Headings structure (10 баллов)
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))

        if h2_count >= 3 and h3_count >= 2:
            seo_score += 10
        elif h2_count >= 2:
            seo_score += 7
        elif h2_count >= 1:
            seo_score += 4
        else:
            issues.append("Poor heading structure (need H2, H3)")

        # 6. Internal links (10 баллов)
        all_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        internal_links = [l for l in all_links if not l[1].startswith('http')]

        if len(internal_links) >= 3:
            seo_score += 10
        elif len(internal_links) >= 1:
            seo_score += 5
        else:
            recommendations.append("Add internal links to improve SEO")

        # 7. External links (5 баллов)
        external_links = [l for l in all_links if l[1].startswith('http')]

        if len(external_links) >= 2:
            seo_score += 5
        elif len(external_links) >= 1:
            seo_score += 3

        # 8. Images (5 баллов)
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

        if len(images) >= 1:
            seo_score += 5
            # Check alt text
            images_without_alt = [img for img in images if not img[0]]
            if images_without_alt:
                recommendations.append(f"{len(images_without_alt)} images missing alt text")

        # 9. Keyword density (5 баллов)
        if title:
            # Проверить упоминание ключевых слов из title в контенте
            title_words = set(re.findall(r'\b[а-яёa-z]{4,}\b', title.lower()))
            content_words = re.findall(r'\b[а-яёa-z]+\b', content.lower())
            content_word_count = Counter(content_words)

            keywords_mentioned = 0
            for keyword in title_words:
                if keyword in content_word_count:
                    keywords_mentioned += 1

            if keywords_mentioned >= len(title_words) * 0.7:
                seo_score += 5
            elif keywords_mentioned >= len(title_words) * 0.5:
                seo_score += 3
            else:
                recommendations.append("Use more keywords from title in content")

        return {
            'score': min(seo_score, 100),
            'title_length': title_length,
            'description_length': desc_length,
            'word_count': word_count,
            'h1_count': len(h1_headings),
            'h2_count': h2_count,
            'internal_links': len(internal_links),
            'external_links': len(external_links),
            'images': len(images),
            'issues': issues,
            'recommendations': recommendations
        }

    def analyze_all(self):
        """Проанализировать все статьи"""
        results = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    article_content = match.group(2)
                else:
                    fm = None
                    article_content = content

                seo_analysis = self.analyze_article(md_file, fm, article_content)
                seo_analysis['file'] = str(md_file.relative_to(self.root_dir))
                seo_analysis['title'] = fm.get('title', md_file.stem) if fm else md_file.stem

                results.append(seo_analysis)
            except:
                continue

        # Сортировать по score
        results.sort(key=lambda x: x['score'], reverse=True)

        return results

    def generate_seo_report_html(self, output_file):
        """Генерировать HTML отчёт по SEO"""
        results = self.analyze_all()

        if not results:
            return

        avg_score = sum(r['score'] for r in results) / len(results)

        # Категоризация
        excellent = [r for r in results if r['score'] >= 80]
        good = [r for r in results if 60 <= r['score'] < 80]
        fair = [r for r in results if 40 <= r['score'] < 60]
        poor = [r for r in results if r['score'] < 40]

        html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 SEO Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{ color: #667eea; margin-bottom: 10px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-card h3 {{ margin: 0; font-size: 0.9em; color: #666; }}
        .stat-card .value {{ font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .article-card {{
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 5px solid #ddd;
        }}
        .score-excellent {{ border-left-color: #4CAF50; }}
        .score-good {{ border-left-color: #2196F3; }}
        .score-fair {{ border-left-color: #FF9800; }}
        .score-poor {{ border-left-color: #f44336; }}
        .score-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
            font-size: 0.9em;
        }}
        .badge-excellent {{ background: #4CAF50; }}
        .badge-good {{ background: #2196F3; }}
        .badge-fair {{ background: #FF9800; }}
        .badge-poor {{ background: #f44336; }}
        .issues {{ color: #d32f2f; margin-top: 10px; }}
        .recommendations {{ color: #ff9800; margin-top: 10px; }}
        .metrics {{ display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SEO Analysis Report</h1>
        <p>Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

        <div class="summary">
            <div class="stat-card">
                <h3>Средний SEO Score</h3>
                <div class="value">{avg_score:.1f}/100</div>
            </div>
            <div class="stat-card">
                <h3>Отлично (80+)</h3>
                <div class="value">{len(excellent)}</div>
            </div>
            <div class="stat-card">
                <h3>Хорошо (60-79)</h3>
                <div class="value">{len(good)}</div>
            </div>
            <div class="stat-card">
                <h3>Требуют улучшения</h3>
                <div class="value">{len(fair) + len(poor)}</div>
            </div>
        </div>

        <h2>🔴 Требуют срочного улучшения (Score < 40)</h2>
'''

        for article in poor[:10]:
            score_class = 'score-poor'
            badge_class = 'badge-poor'

            html += f'''
        <div class="article-card {score_class}">
            <h3>{article['title']}</h3>
            <span class="{badge_class} score-badge">Score: {article['score']}/100</span>
            <div class="metrics">
                <span>📝 {article['word_count']} words</span>
                <span>🔗 {article['internal_links']} internal links</span>
                <span>🖼️ {article['images']} images</span>
            </div>
'''
            if article['issues']:
                html += '<div class="issues">❌ Issues:<ul>'
                for issue in article['issues']:
                    html += f'<li>{issue}</li>'
                html += '</ul></div>'

            if article['recommendations']:
                html += '<div class="recommendations">💡 Recommendations:<ul>'
                for rec in article['recommendations']:
                    html += f'<li>{rec}</li>'
                html += '</ul></div>'

            html += f'<div style="margin-top:10px;"><code>{article["file"]}</code></div></div>'

        html += '''
    </div>
</body>
</html>
'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)


class SitemapValidator:
    """
    Валидатор sitemap.xml
    Проверка XML schema, URL structure, дубликаты, размер
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.errors = []
        self.warnings = []

    def validate_file(self, sitemap_file):
        """Валидировать sitemap файл"""
        print(f"🔍 Валидация: {sitemap_file.name}")

        # 1. Check file exists
        if not sitemap_file.exists():
            self.errors.append(f"File not found: {sitemap_file}")
            return False

        # 2. Check file size (max 50MB uncompressed)
        file_size = sitemap_file.stat().st_size

        if sitemap_file.suffix == '.gz':
            # Для gzip файла проверить после распаковки
            try:
                with gzip.open(sitemap_file, 'rt', encoding='utf-8') as f:
                    content = f.read()
                    file_size = len(content.encode('utf-8'))
            except Exception as e:
                self.errors.append(f"Failed to decompress: {e}")
                return False
        else:
            with open(sitemap_file, 'r', encoding='utf-8') as f:
                content = f.read()

        max_size = 50 * 1024 * 1024
        if file_size > max_size:
            self.errors.append(f"File too large: {file_size / (1024*1024):.1f}MB (max 50MB)")

        # 3. Parse XML
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.errors.append(f"XML parse error: {e}")
            return False

        # 4. Validate namespace
        expected_ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        if expected_ns not in root.tag:
            self.errors.append(f"Invalid namespace: {root.tag}")

        # 5. Check URL count (max 50,000)
        urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        url_count = len(urls)

        if url_count > 50000:
            self.errors.append(f"Too many URLs: {url_count} (max 50,000)")
        elif url_count == 0:
            self.warnings.append("No URLs found in sitemap")

        print(f"   URLs: {url_count}")

        # 6. Check for duplicates
        locs = [url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                for url in urls if url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc') is not None]

        duplicates = [loc for loc in set(locs) if locs.count(loc) > 1]
        if duplicates:
            self.errors.append(f"Duplicate URLs found: {len(duplicates)}")
            for dup in duplicates[:5]:
                self.warnings.append(f"  Duplicate: {dup}")

        # 7. Validate URL format
        invalid_urls = []
        for loc_text in locs[:100]:  # Check first 100
            if not loc_text.startswith(('http://', 'https://')):
                invalid_urls.append(loc_text)

        if invalid_urls:
            self.errors.append(f"Invalid URL format found: {len(invalid_urls)}")

        # 8. Check priority values
        priorities = [url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
                     for url in urls]
        for priority in priorities:
            if priority is not None:
                try:
                    val = float(priority.text)
                    if not (0.0 <= val <= 1.0):
                        self.warnings.append(f"Priority out of range: {val}")
                except:
                    self.warnings.append(f"Invalid priority value: {priority.text}")

        return len(self.errors) == 0

    def print_report(self):
        """Вывести отчёт валидации"""
        print("\n📋 Отчёт валидации:\n")

        if not self.errors and not self.warnings:
            print("✅ Sitemap валиден! Ошибок не найдено.\n")
            return

        if self.errors:
            print(f"❌ Ошибок: {len(self.errors)}\n")
            for error in self.errors:
                print(f"   • {error}")
            print()

        if self.warnings:
            print(f"⚠️  Предупреждений: {len(self.warnings)}\n")
            for warning in self.warnings[:10]:
                print(f"   • {warning}")
            if len(self.warnings) > 10:
                print(f"   ... и ещё {len(self.warnings) - 10}")
            print()


class ChangeDetector:
    """
    Детектор изменений с последнего sitemap
    Использует git для определения modified/new/deleted файлов
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def get_changed_files_from_git(self, since_days=7):
        """Получить изменённые файлы из git"""
        try:
            since_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')

            # Modified files
            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--name-only',
                 '--pretty=format:', '--', 'knowledge/'],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                return set()

            changed_files = set()
            for line in result.stdout.strip().split('\n'):
                if line and line.endswith('.md'):
                    file_path = self.root_dir / line
                    if file_path.exists():
                        changed_files.add(str(file_path.relative_to(self.root_dir)))

            return changed_files
        except:
            return set()

    def get_intelligent_changefreq(self, file_path):
        """
        Умное определение changefreq на основе истории git

        Returns: changefreq (always/hourly/daily/weekly/monthly/yearly/never)
        """
        try:
            # Получить даты последних коммитов для файла
            result = subprocess.run(
                ['git', 'log', '--format=%ai', '--', str(file_path)],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                return 'monthly'  # Default

            dates = []
            for line in result.stdout.strip().split('\n'):
                try:
                    date = datetime.strptime(line.split()[0], '%Y-%m-%d')
                    dates.append(date)
                except:
                    continue

            if len(dates) < 2:
                return 'monthly'

            # Вычислить среднюю частоту изменений
            dates.sort(reverse=True)
            intervals = []

            for i in range(min(5, len(dates) - 1)):
                delta = (dates[i] - dates[i + 1]).days
                intervals.append(delta)

            avg_interval = sum(intervals) / len(intervals) if intervals else 365

            # Определить changefreq
            if avg_interval < 1:
                return 'always'
            elif avg_interval < 7:
                return 'daily'
            elif avg_interval < 30:
                return 'weekly'
            elif avg_interval < 90:
                return 'monthly'
            elif avg_interval < 365:
                return 'yearly'
            else:
                return 'never'

        except:
            return 'monthly'

    def get_change_summary(self):
        """Получить сводку изменений"""
        changed_30d = self.get_changed_files_from_git(since_days=30)
        changed_7d = self.get_changed_files_from_git(since_days=7)

        return {
            'changed_last_30_days': len(changed_30d),
            'changed_last_7_days': len(changed_7d),
            'files_30d': list(changed_30d),
            'files_7d': list(changed_7d)
        }


class SearchEngineNotifier:
    """
    Расширенный notifier для поисковых систем
    Ping Google, Bing, Yandex, DuckDuckGo с retry и rate limiting
    """

    def __init__(self, base_url):
        self.base_url = base_url
        self.ping_history_file = Path(".sitemap_ping_history.json")
        self.ping_history = self.load_history()

    def load_history(self):
        """Загрузить историю пингов"""
        if self.ping_history_file.exists():
            try:
                with open(self.ping_history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_history(self):
        """Сохранить историю пингов"""
        with open(self.ping_history_file, 'w') as f:
            json.dump(self.ping_history, f, indent=2)

    def should_ping(self, engine, min_interval_hours=24):
        """Проверить, можно ли пинговать (rate limiting)"""
        if engine not in self.ping_history:
            return True

        last_ping = self.ping_history[engine].get('last_ping')
        if not last_ping:
            return True

        try:
            last_ping_time = datetime.fromisoformat(last_ping)
            elapsed_hours = (datetime.now() - last_ping_time).total_seconds() / 3600

            return elapsed_hours >= min_interval_hours
        except:
            return True

    def ping_engine(self, engine, ping_url, retries=3):
        """Пинговать один поисковик с retry logic"""
        for attempt in range(retries):
            try:
                response = urllib.request.urlopen(ping_url, timeout=10)
                status = response.status

                # Записать историю
                self.ping_history[engine] = {
                    'last_ping': datetime.now().isoformat(),
                    'status': status,
                    'success': status == 200
                }
                self.save_history()

                return status == 200, status
            except Exception as e:
                if attempt == retries - 1:
                    # Last attempt failed
                    self.ping_history[engine] = {
                        'last_ping': datetime.now().isoformat(),
                        'error': str(e),
                        'success': False
                    }
                    self.save_history()
                    return False, str(e)

                # Wait before retry (exponential backoff)
                time.sleep(2 ** attempt)

        return False, "Max retries exceeded"

    def ping_all(self, sitemap_url):
        """Пинговать все поисковые системы"""
        print("\n📡 Уведомление поисковых систем...\n")

        engines = {
            'Google': f'http://www.google.com/ping?sitemap={urllib.parse.quote(sitemap_url)}',
            'Bing': f'http://www.bing.com/ping?sitemap={urllib.parse.quote(sitemap_url)}',
            'Yandex': f'http://webmaster.yandex.com/ping?sitemap={urllib.parse.quote(sitemap_url)}',
        }

        for engine, ping_url in engines.items():
            # Check rate limiting
            if not self.should_ping(engine):
                last_ping = self.ping_history[engine]['last_ping']
                print(f"   ⏭️  {engine}: пропущен (последний ping: {last_ping})")
                continue

            success, result = self.ping_engine(engine, ping_url)

            if success:
                print(f"   ✅ {engine}: успешно (status {result})")
            else:
                print(f"   ❌ {engine}: ошибка ({result})")

        print()


class AdvancedSitemapGenerator:
    """Продвинутый генератор sitemap"""

    def __init__(self, root_dir=".", base_url="https://example.com"):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.base_url = base_url.rstrip('/')

        # Ограничения sitemap (Google spec)
        self.max_urls_per_sitemap = 50000
        self.max_sitemap_size = 50 * 1024 * 1024  # 50 MB

        # Статистика
        self.stats = {
            'total_urls': 0,
            'total_images': 0,
            'sitemaps_created': 0
        }

    def extract_frontmatter_and_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)), match.group(2)
        except:
            pass
        return None, None

    def calculate_priority(self, file_path, frontmatter, content):
        """Вычислить динамический priority (0.0 - 1.0)"""
        priority = 0.5  # Базовый приоритет

        # Приоритет из frontmatter
        if frontmatter and 'priority' in frontmatter:
            return float(frontmatter['priority'])

        # Глубина вложенности (меньше = важнее)
        depth = len(file_path.relative_to(self.knowledge_dir).parts) - 1
        if depth == 0:
            priority += 0.3
        elif depth == 1:
            priority += 0.2
        elif depth == 2:
            priority += 0.1

        # Длина контента (больше = важнее)
        if content:
            content_length = len(content)
            if content_length > 5000:
                priority += 0.15
            elif content_length > 2000:
                priority += 0.1
            elif content_length > 1000:
                priority += 0.05

        # Количество ссылок (больше = важнее)
        if content:
            links_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
            if links_count > 20:
                priority += 0.1
            elif links_count > 10:
                priority += 0.05

        # Наличие изображений
        if content and re.search(r'!\[.*?\]\(.*?\)', content):
            priority += 0.05

        # Ограничить до 1.0
        return min(priority, 1.0)

    def calculate_changefreq(self, file_path, frontmatter):
        """Вычислить частоту изменений"""
        # Если указано в frontmatter
        if frontmatter and 'changefreq' in frontmatter:
            return frontmatter['changefreq']

        # Проверить последнюю модификацию
        mtime = file_path.stat().st_mtime
        last_modified = datetime.fromtimestamp(mtime)
        days_since_modified = (datetime.now() - last_modified).days

        if days_since_modified < 7:
            return 'daily'
        elif days_since_modified < 30:
            return 'weekly'
        elif days_since_modified < 90:
            return 'monthly'
        elif days_since_modified < 365:
            return 'yearly'
        else:
            return 'never'

    def get_lastmod(self, file_path, frontmatter):
        """Получить дату последней модификации"""
        # Из frontmatter
        if frontmatter and 'date' in frontmatter:
            try:
                date = frontmatter['date']
                if isinstance(date, str):
                    return date
                else:
                    return date.strftime('%Y-%m-%d')
            except:
                pass

        # Из файловой системы
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

    def extract_images(self, content):
        """Извлечь изображения из контента"""
        if not content:
            return []

        images = []

        # Markdown изображения: ![alt](url)
        md_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

        for alt, url in md_images:
            # Пропустить внешние URL
            if url.startswith('http'):
                continue

            images.append({
                'loc': url,
                'caption': alt if alt else None
            })

        return images

    def collect_urls(self):
        """Собрать все URLs"""
        urls = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            # Относительный путь
            article_path = str(md_file.relative_to(self.root_dir))

            # URL
            # Преобразовать .md в .html
            html_path = article_path.replace('.md', '.html')
            url = f"{self.base_url}/{html_path}"

            # Вычислить метрики
            priority = self.calculate_priority(md_file, frontmatter, content)
            changefreq = self.calculate_changefreq(md_file, frontmatter)
            lastmod = self.get_lastmod(md_file, frontmatter)

            # Извлечь изображения
            images = self.extract_images(content)

            url_data = {
                'loc': url,
                'lastmod': lastmod,
                'changefreq': changefreq,
                'priority': f'{priority:.2f}',
                'images': images
            }

            urls.append(url_data)
            self.stats['total_images'] += len(images)

        self.stats['total_urls'] = len(urls)
        return urls

    def generate_sitemap_xml(self, urls, sitemap_index=0):
        """Создать XML sitemap"""
        xml_lines = []
        xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')

        # Добавить namespace для изображений
        if any(url.get('images') for url in urls):
            xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n')
            xml_lines.append('        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n')
        else:
            xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        for url_data in urls:
            xml_lines.append('  <url>\n')
            xml_lines.append(f'    <loc>{url_data["loc"]}</loc>\n')
            xml_lines.append(f'    <lastmod>{url_data["lastmod"]}</lastmod>\n')
            xml_lines.append(f'    <changefreq>{url_data["changefreq"]}</changefreq>\n')
            xml_lines.append(f'    <priority>{url_data["priority"]}</priority>\n')

            # Добавить изображения
            for image in url_data.get('images', []):
                xml_lines.append('    <image:image>\n')
                xml_lines.append(f'      <image:loc>{self.base_url}/{image["loc"]}</image:loc>\n')
                if image.get('caption'):
                    xml_lines.append(f'      <image:caption>{image["caption"]}</image:caption>\n')
                xml_lines.append('    </image:image>\n')

            xml_lines.append('  </url>\n')

        xml_lines.append('</urlset>\n')

        return ''.join(xml_lines)

    def generate_sitemap_index_xml(self, sitemap_files):
        """Создать sitemap index"""
        xml_lines = []
        xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_lines.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        for sitemap_file in sitemap_files:
            xml_lines.append('  <sitemap>\n')
            xml_lines.append(f'    <loc>{self.base_url}/{sitemap_file.name}</loc>\n')
            xml_lines.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n')
            xml_lines.append('  </sitemap>\n')

        xml_lines.append('</sitemapindex>\n')

        return ''.join(xml_lines)

    def generate_sitemaps(self, compress=False):
        """Генерировать sitemap(s)"""
        print("🗺️  Генерация sitemap...\n")

        # Собрать URLs
        all_urls = self.collect_urls()

        if not all_urls:
            print("⚠️  Нет URLs для sitemap")
            return []

        print(f"   Найдено URLs: {len(all_urls)}")
        print(f"   Изображений: {self.stats['total_images']}\n")

        # Разделить на несколько sitemap если нужно
        sitemap_files = []

        # Сортировать по priority (важные первыми)
        all_urls.sort(key=lambda x: float(x['priority']), reverse=True)

        for i in range(0, len(all_urls), self.max_urls_per_sitemap):
            urls_chunk = all_urls[i:i + self.max_urls_per_sitemap]

            # Имя файла
            if len(all_urls) > self.max_urls_per_sitemap:
                sitemap_index = i // self.max_urls_per_sitemap + 1
                sitemap_name = f"sitemap{sitemap_index}.xml"
            else:
                sitemap_name = "sitemap.xml"

            sitemap_path = self.root_dir / sitemap_name

            # Создать XML
            xml_content = self.generate_sitemap_xml(urls_chunk)

            # Сохранить
            if compress:
                gz_path = sitemap_path.with_suffix('.xml.gz')
                with gzip.open(gz_path, 'wt', encoding='utf-8') as f:
                    f.write(xml_content)
                sitemap_files.append(gz_path)
                print(f"✅ Sitemap: {gz_path.name} ({len(urls_chunk)} URLs)")
            else:
                with open(sitemap_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                sitemap_files.append(sitemap_path)
                print(f"✅ Sitemap: {sitemap_name} ({len(urls_chunk)} URLs)")

            self.stats['sitemaps_created'] += 1

        # Создать sitemap index если несколько файлов
        if len(sitemap_files) > 1:
            index_xml = self.generate_sitemap_index_xml(sitemap_files)
            index_path = self.root_dir / "sitemap_index.xml"

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_xml)

            print(f"\n✅ Sitemap Index: sitemap_index.xml ({len(sitemap_files)} sitemaps)")

        return sitemap_files

    def generate_robots_txt(self):
        """Создать robots.txt"""
        robots_path = self.root_dir / "robots.txt"

        lines = []
        lines.append("# Robots.txt\n")
        lines.append("# Generated by Advanced Sitemap Generator\n\n")
        lines.append("User-agent: *\n")
        lines.append("Allow: /\n\n")

        # Указать sitemap
        if self.stats['sitemaps_created'] > 1:
            lines.append(f"Sitemap: {self.base_url}/sitemap_index.xml\n")
        else:
            lines.append(f"Sitemap: {self.base_url}/sitemap.xml\n")

        with open(robots_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Robots.txt: {robots_path}")

    def ping_search_engines(self, sitemap_url):
        """Ping поисковых систем"""
        print("\n📡 Ping поисковых систем...\n")

        search_engines = {
            'Google': f'http://www.google.com/ping?sitemap={urllib.parse.quote(sitemap_url)}',
            'Bing': f'http://www.bing.com/ping?sitemap={urllib.parse.quote(sitemap_url)}'
        }

        for engine, ping_url in search_engines.items():
            try:
                response = urllib.request.urlopen(ping_url, timeout=10)
                if response.status == 200:
                    print(f"   ✅ {engine}: успешно")
                else:
                    print(f"   ⚠️  {engine}: статус {response.status}")
            except Exception as e:
                print(f"   ❌ {engine}: {e}")

    def print_statistics(self):
        """Вывести статистику"""
        print("\n📊 Статистика:\n")
        print(f"   URLs: {self.stats['total_urls']}")
        print(f"   Изображений: {self.stats['total_images']}")
        print(f"   Sitemaps: {self.stats['sitemaps_created']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Advanced Sitemap Generator - Продвинутый генератор sitemap с SEO анализом',
        epilog='''Примеры использования:
  %(prog)s --base-url https://example.com            # Базовый sitemap
  %(prog)s --validate                                # Валидация существующего sitemap.xml
  %(prog)s --seo-check --html seo_report.html        # SEO анализ + HTML отчёт
  %(prog)s --compress --robots --notify              # Sitemap + gzip + robots.txt + ping
  %(prog)s --all                                     # Всё вместе: sitemap + SEO + валидация
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--base-url', default='https://example.com',
                       help='Base URL сайта (по умолчанию: https://example.com)')
    parser.add_argument('--compress', action='store_true',
                       help='Сжать sitemap в .gz формат')
    parser.add_argument('--robots', action='store_true',
                       help='Создать robots.txt')
    parser.add_argument('--validate', action='store_true',
                       help='Валидировать существующий sitemap.xml')
    parser.add_argument('--seo-check', action='store_true',
                       help='Запустить SEO анализ всех статей')
    parser.add_argument('--html', metavar='FILE',
                       help='Сгенерировать HTML отчёт по SEO')
    parser.add_argument('--notify', action='store_true',
                       help='Уведомить поисковые системы (Google, Bing, Yandex)')
    parser.add_argument('--all', action='store_true',
                       help='Генерировать sitemap + SEO анализ + валидация + notify')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # SEO анализ
    if args.seo_check or args.all:
        print("📊 SEO Анализ...\n")
        seo_analyzer = SEOAnalyzer(root_dir)
        results = seo_analyzer.analyze_all()

        if results:
            avg_score = sum(r['score'] for r in results) / len(results)
            excellent = len([r for r in results if r['score'] >= 80])
            needs_improvement = len([r for r in results if r['score'] < 60])

            print(f"   Проанализировано статей: {len(results)}")
            print(f"   Средний SEO score: {avg_score:.1f}/100")
            print(f"   Отличный SEO (80+): {excellent}")
            print(f"   Требуют улучшения (<60): {needs_improvement}\n")

        # HTML отчёт
        if args.html or args.all:
            html_file = args.html if args.html else root_dir / "SEO_REPORT.html"
            seo_analyzer.generate_seo_report_html(html_file)
            print(f"✅ SEO HTML отчёт: {html_file}\n")

    # Генерация sitemap
    if not args.validate and not (args.seo_check and not args.all):
        generator = AdvancedSitemapGenerator(root_dir, args.base_url)

        # Детектор изменений
        change_detector = ChangeDetector(root_dir)
        change_summary = change_detector.get_change_summary()

        if change_summary['changed_last_7_days'] > 0:
            print(f"🔄 Изменений за последние 7 дней: {change_summary['changed_last_7_days']}")
            print(f"🔄 Изменений за последние 30 дней: {change_summary['changed_last_30_days']}\n")

        # Генерировать sitemaps
        sitemap_files = generator.generate_sitemaps(compress=args.compress)

        # Robots.txt
        if args.robots or args.all:
            generator.generate_robots_txt()

        # Статистика
        generator.print_statistics()

        # Определить URL sitemap
        if generator.stats['sitemaps_created'] > 1:
            sitemap_url = f"{args.base_url}/sitemap_index.xml"
            sitemap_file = root_dir / "sitemap_index.xml"
        else:
            sitemap_url = f"{args.base_url}/sitemap.xml"
            sitemap_file = root_dir / "sitemap.xml"

        # Валидация
        if args.validate or args.all:
            if sitemap_file.exists():
                print()
                validator = SitemapValidator(root_dir)
                is_valid = validator.validate_file(sitemap_file)
                validator.print_report()

        # Notification
        if (args.notify or args.all) and sitemap_files:
            notifier = SearchEngineNotifier(args.base_url)
            notifier.ping_all(sitemap_url)

    # Только валидация
    elif args.validate:
        sitemap_file = root_dir / "sitemap.xml"
        if sitemap_file.exists():
            validator = SitemapValidator(root_dir)
            is_valid = validator.validate_file(sitemap_file)
            validator.print_report()
        else:
            print(f"❌ Sitemap не найден: {sitemap_file}")


if __name__ == "__main__":
    main()
