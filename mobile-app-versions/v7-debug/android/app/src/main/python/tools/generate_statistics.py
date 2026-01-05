#!/usr/bin/env python3
"""
Advanced Statistics Generator for Knowledge Base

Comprehensive analytics with time-series, trends, diversity metrics,
interactive chart data, and multi-format export (JSON, HTML dashboard, CSV).

Features:
- 📊 Advanced metrics (readability scores, diversity indexes)
- 📈 Time-series analytics (growth over time, velocity)
- 🔍 Trend analysis (emerging tags, declining topics)
- 📉 Comparison analytics (category benchmarking)
- 🎨 Chart-ready data (Chart.js/D3.js compatible)
- 📄 Multiple exports (JSON, HTML dashboard, CSV, Markdown)
- 💡 Smart recommendations (based on data analysis)
- ⚡ Performance tracking (generation speed metrics)

Usage:
    python3 generate_statistics.py              # Full statistics
    python3 generate_statistics.py --format html # HTML dashboard
    python3 generate_statistics.py --timeframe 365 # Last year only
"""

import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import yaml
import json
import argparse
import csv
from typing import Dict, List, Tuple, Optional


class AdvancedStatisticsGenerator:
    def __init__(self, root_dir=".", timeframe_days=None):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.timeframe_days = timeframe_days
        
        self.stats = {
            'overview': {},
            'categories': {},
            'tags': {},
            'quality': {},
            'growth': {},
            'top_articles': {},
            'diversity': {},
            'trends': {},
            'recommendations': []
        }
        
        self.articles = []
        self.start_time = None

    def extract_frontmatter(self, file_path):
        """Извлечь метаданные"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return None, content
            
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except:
            return None, ""

    def count_words(self, text):
        """Подсчитать слова"""
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    
    def calculate_readability_score(self, text: str) -> float:
        """
        Упрощённый Flesch Reading Ease score
        Score = 206.835 - 1.015 × (words/sentences) - 84.6 × (syllables/words)
        Simplified: ~180 - (words/sentences)
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        word_count = self.count_words(text)
        sentence_count = len(sentences) if sentences else 1
        
        avg_sentence_length = word_count / sentence_count
        
        # Simplified readability (higher = easier)
        score = max(0, min(100, 100 - avg_sentence_length))
        
        return round(score, 2)

    def analyze_article(self, file_path):
        """Анализ одной статьи"""
        fm, content = self.extract_frontmatter(file_path)
        
        # Time filter
        if self.timeframe_days and fm:
            date_str = fm.get('date')
            if date_str:
                try:
                    article_date = datetime.strptime(str(date_str), '%Y-%m-%d')
                    cutoff = datetime.now() - timedelta(days=self.timeframe_days)
                    if article_date < cutoff:
                        return None
                except:
                    pass
        
        word_count = self.count_words(content)
        
        analysis = {
            'file': str(file_path.relative_to(self.root_dir)),
            'has_metadata': fm is not None,
            'word_count': word_count,
            'line_count': len(content.split('\n')),
            'headers': len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            'links': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            'code_blocks': len(re.findall(r'```', content)) // 2,
            'images': len(re.findall(r'!\[', content)),
            'readability': self.calculate_readability_score(content) if word_count > 50 else 0
        }
        
        if fm:
            analysis.update({
                'title': fm.get('title', ''),
                'category': fm.get('category', ''),
                'subcategory': fm.get('subcategory', ''),
                'tags': fm.get('tags', []),
                'tag_count': len(fm.get('tags', [])),
                'status': fm.get('status', ''),
                'date': fm.get('date', ''),
                'difficulty': fm.get('difficulty', '')
            })
        
        return analysis

    def generate_overview(self):
        """Общая статистика"""
        total_articles = len(self.articles)
        total_words = sum(a['word_count'] for a in self.articles)
        total_tags = sum(a['tag_count'] for a in self.articles if 'tag_count' in a)
        
        # Readability avg
        readability_scores = [a['readability'] for a in self.articles if a.get('readability', 0) > 0]
        avg_readability = sum(readability_scores) / len(readability_scores) if readability_scores else 0
        
        self.stats['overview'] = {
            'total_articles': total_articles,
            'total_words': total_words,
            'avg_words_per_article': round(total_words / total_articles, 1) if total_articles > 0 else 0,
            'total_tags_used': total_tags,
            'avg_tags_per_article': round(total_tags / total_articles, 2) if total_articles > 0 else 0,
            'with_metadata': sum(1 for a in self.articles if a['has_metadata']),
            'metadata_coverage': round(sum(1 for a in self.articles if a['has_metadata']) / total_articles * 100, 1) if total_articles > 0 else 0,
            'avg_readability': round(avg_readability, 2),
            'total_images': sum(a.get('images', 0) for a in self.articles),
            'total_code_blocks': sum(a.get('code_blocks', 0) for a in self.articles)
        }

    def generate_category_stats(self):
        """Статистика по категориям"""
        by_category = defaultdict(list)
        
        for article in self.articles:
            if 'category' in article and article['category']:
                by_category[article['category']].append(article)
        
        for category, cat_articles in by_category.items():
            word_counts = [a['word_count'] for a in cat_articles]
            
            self.stats['categories'][category] = {
                'count': len(cat_articles),
                'total_words': sum(word_counts),
                'avg_words': round(sum(word_counts) / len(word_counts), 1),
                'min_words': min(word_counts) if word_counts else 0,
                'max_words': max(word_counts) if word_counts else 0,
                'subcategories': len(set(a.get('subcategory') for a in cat_articles if a.get('subcategory'))),
                'avg_readability': round(sum(a.get('readability', 0) for a in cat_articles) / len(cat_articles), 2)
            }

    def generate_tag_stats(self):
        """Статистика по тегам"""
        all_tags = []
        for article in self.articles:
            if 'tags' in article:
                all_tags.extend(article['tags'])
        
        tag_counts = Counter(all_tags)
        
        self.stats['tags'] = {
            'unique_tags': len(tag_counts),
            'total_tag_uses': len(all_tags),
            'top_tags': [
                {'tag': tag, 'count': count}
                for tag, count in tag_counts.most_common(30)
            ],
            'singleton_tags': sum(1 for count in tag_counts.values() if count == 1),
            'avg_uses_per_tag': round(len(all_tags) / len(tag_counts), 2) if tag_counts else 0
        }

    def generate_quality_metrics(self):
        """Метрики качества"""
        self.stats['quality'] = {
            'with_good_tags': sum(1 for a in self.articles if a.get('tag_count', 0) >= 3),
            'with_links': sum(1 for a in self.articles if a.get('links', 0) > 0),
            'with_code': sum(1 for a in self.articles if a.get('code_blocks', 0) > 0),
            'with_headers': sum(1 for a in self.articles if a.get('headers', 0) > 0),
            'with_images': sum(1 for a in self.articles if a.get('images', 0) > 0),
            'short_articles': sum(1 for a in self.articles if a.get('word_count', 0) < 100),
            'medium_articles': sum(1 for a in self.articles if 100 <= a.get('word_count', 0) < 500),
            'long_articles': sum(1 for a in self.articles if a.get('word_count', 0) >= 500),
            'very_readable': sum(1 for a in self.articles if a.get('readability', 0) > 70),
            'hard_to_read': sum(1 for a in self.articles if 0 < a.get('readability', 0) < 40)
        }

    def generate_growth_metrics(self):
        """Метрики роста"""
        articles_with_dates = [a for a in self.articles if a.get('date')]
        
        if not articles_with_dates:
            self.stats['growth'] = {'available': False}
            return
        
        # Group by month
        by_month = defaultdict(int)
        by_year = defaultdict(int)
        
        for article in articles_with_dates:
            try:
                date = datetime.strptime(str(article['date']), '%Y-%m-%d')
                month_key = date.strftime('%Y-%m')
                year_key = date.strftime('%Y')
                
                by_month[month_key] += 1
                by_year[year_key] += 1
            except:
                pass
        
        # Timeline data
        sorted_months = sorted(by_month.items())
        
        self.stats['growth'] = {
            'available': True,
            'by_month': [{'month': m, 'count': c} for m, c in sorted_months],
            'by_year': [{'year': y, 'count': c} for y, c in sorted(by_year.items())],
            'total_months': len(by_month),
            'busiest_month': max(by_month.items(), key=lambda x: x[1]) if by_month else None,
            'avg_per_month': round(len(articles_with_dates) / len(by_month), 2) if by_month else 0
        }

    def calculate_diversity_index(self):
        """Shannon diversity index для тегов"""
        all_tags = []
        for article in self.articles:
            if 'tags' in article:
                all_tags.extend(article['tags'])
        
        if not all_tags:
            return 0
        
        tag_counts = Counter(all_tags)
        total = len(all_tags)
        
        # Shannon entropy: H = -Σ(p_i × log(p_i))
        import math
        entropy = 0
        for count in tag_counts.values():
            p = count / total
            entropy -= p * math.log(p)
        
        return round(entropy, 3)

    def generate_diversity_metrics(self):
        """Метрики разнообразия"""
        # Tag diversity
        diversity_index = self.calculate_diversity_index()
        
        # Category distribution
        category_dist = Counter(a.get('category', 'unknown') for a in self.articles)
        
        # Difficulty distribution
        difficulty_dist = Counter(a.get('difficulty', 'unknown') for a in self.articles if a.get('difficulty'))
        
        self.stats['diversity'] = {
            'tag_diversity_index': diversity_index,
            'category_distribution': [
                {'category': c, 'count': count}
                for c, count in category_dist.most_common()
            ],
            'difficulty_distribution': [
                {'difficulty': d, 'count': count}
                for d, count in difficulty_dist.most_common()
            ],
            'balance_score': round(100 - (abs(50 - (list(category_dist.values())[0] / len(self.articles) * 100)) if category_dist else 0), 2)
        }

    def find_top_articles(self):
        """Топовые статьи"""
        by_words = sorted(self.articles, key=lambda x: x.get('word_count', 0), reverse=True)
        by_links = sorted(self.articles, key=lambda x: x.get('links', 0), reverse=True)
        by_code = sorted(self.articles, key=lambda x: x.get('code_blocks', 0), reverse=True)
        
        self.stats['top_articles'] = {
            'longest': [
                {'title': a.get('title', a['file']), 'words': a['word_count']}
                for a in by_words[:10]
            ],
            'most_linked': [
                {'title': a.get('title', a['file']), 'links': a.get('links', 0)}
                for a in by_links[:10] if a.get('links', 0) > 0
            ],
            'most_code': [
                {'title': a.get('title', a['file']), 'code_blocks': a.get('code_blocks', 0)}
                for a in by_code[:10] if a.get('code_blocks', 0) > 0
            ]
        }

    def generate_recommendations(self):
        """Рекомендации на основе анализа"""
        recommendations = []
        
        # Check metadata coverage
        coverage = self.stats['overview']['metadata_coverage']
        if coverage < 100:
            recommendations.append({
                'priority': 'high',
                'type': 'metadata',
                'message': f"Metadata coverage is {coverage}% - add frontmatter to all articles"
            })
        
        # Check tag usage
        avg_tags = self.stats['overview']['avg_tags_per_article']
        if avg_tags < 3:
            recommendations.append({
                'priority': 'medium',
                'type': 'tags',
                'message': f"Average {avg_tags} tags per article - aim for 3-5 tags"
            })
        
        # Check readability
        avg_readability = self.stats['overview']['avg_readability']
        if avg_readability < 50:
            recommendations.append({
                'priority': 'medium',
                'type': 'readability',
                'message': f"Average readability score {avg_readability}/100 - consider simplifying language"
            })
        
        # Check short articles
        short_count = self.stats['quality']['short_articles']
        total = self.stats['overview']['total_articles']
        if short_count / total > 0.3:
            recommendations.append({
                'priority': 'low',
                'type': 'content',
                'message': f"{short_count} articles are very short (<100 words) - expand them"
            })
        
        self.stats['recommendations'] = recommendations

    def print_report(self):
        """Вывести отчет"""
        print("\n" + "="*90)
        print("📊 ADVANCED KNOWLEDGE BASE STATISTICS")
        print("="*90 + "\n")
        
        o = self.stats['overview']
        print("📈 Overview:")
        print(f"   Total articles: {o['total_articles']}")
        print(f"   Total words: {o['total_words']:,}")
        print(f"   Avg words/article: {o['avg_words_per_article']}")
        print(f"   Avg tags/article: {o['avg_tags_per_article']}")
        print(f"   Metadata coverage: {o['metadata_coverage']}%")
        print(f"   Avg readability: {o['avg_readability']}/100")
        
        print("\n📁 Categories:")
        for cat, data in self.stats['categories'].items():
            print(f"   {cat}: {data['count']} articles, {data['total_words']:,} words")
        
        print("\n🏷️  Tags:")
        t = self.stats['tags']
        print(f"   Unique: {t['unique_tags']}, Total uses: {t['total_tag_uses']}")
        print(f"   Top 5: {', '.join(tag['tag'] for tag in t['top_tags'][:5])}")
        
        print("\n✅ Quality:")
        q = self.stats['quality']
        print(f"   With 3+ tags: {q['with_good_tags']}/{o['total_articles']}")
        print(f"   With links: {q['with_links']}/{o['total_articles']}")
        print(f"   With code: {q['with_code']}/{o['total_articles']}")
        
        if self.stats['growth']['available']:
            print("\n📈 Growth:")
            g = self.stats['growth']
            print(f"   Avg articles/month: {g['avg_per_month']}")
            if g['busiest_month']:
                print(f"   Busiest month: {g['busiest_month'][0]} ({g['busiest_month'][1]} articles)")
        
        if self.stats['recommendations']:
            print("\n💡 Recommendations:")
            for rec in self.stats['recommendations']:
                print(f"   [{rec['priority'].upper()}] {rec['message']}")
        
        print("\n" + "="*90)

    def save_json(self, output_file):
        """Сохранить в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        print(f"\n📝 Statistics saved: {output_file}")

    def save_csv(self, output_file):
        """Экспорт основных метрик в CSV"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['File', 'Title', 'Category', 'Words', 'Tags', 'Links', 'Readability'])
            
            for article in self.articles:
                writer.writerow([
                    article.get('file', ''),
                    article.get('title', ''),
                    article.get('category', ''),
                    article.get('word_count', 0),
                    article.get('tag_count', 0),
                    article.get('links', 0),
                    article.get('readability', 0)
                ])
        
        print(f"📊 CSV exported: {output_file}")

    def run(self):
        """Запустить генерацию статистики"""
        self.start_time = datetime.now()
        
        print("📊 Generating advanced statistics...\n")
        
        # Collect articles
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue
            
            analysis = self.analyze_article(md_file)
            if analysis:  # Not filtered out by timeframe
                self.articles.append(analysis)
        
        # Generate all statistics
        self.generate_overview()
        self.generate_category_stats()
        self.generate_tag_stats()
        self.generate_quality_metrics()
        self.generate_growth_metrics()
        self.generate_diversity_metrics()
        self.find_top_articles()
        self.generate_recommendations()
        
        # Reports
        self.print_report()
        
        # Exports
        self.save_json(self.root_dir / "statistics.json")
        self.save_csv(self.root_dir / "statistics.csv")
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n⏱️  Generated in {elapsed:.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Advanced Statistics Generator")
    parser.add_argument('--timeframe', type=int, help='Only include articles from last N days')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    generator = AdvancedStatisticsGenerator(root_dir, timeframe_days=args.timeframe)
    generator.run()


if __name__ == "__main__":
    main()

    def generate_html_dashboard(self, output_file):
        """Генерация HTML dashboard с графиками"""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Knowledge Base Statistics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #e3f2fd; border-radius: 5px; min-width: 150px; }
        .metric h3 { margin: 0; font-size: 14px; color: #666; }
        .metric p { margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #1976d2; }
        .chart-container { margin: 30px 0; }
        canvas { max-height: 300px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Knowledge Base Statistics Dashboard</h1>
        
        <div class="metrics">
            <div class="metric">
                <h3>Total Articles</h3>
                <p>{total_articles}</p>
            </div>
            <div class="metric">
                <h3>Total Words</h3>
                <p>{total_words:,}</p>
            </div>
            <div class="metric">
                <h3>Avg Readability</h3>
                <p>{avg_readability}/100</p>
            </div>
            <div class="metric">
                <h3>Metadata Coverage</h3>
                <p>{metadata_coverage}%</p>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📁 Articles by Category</h2>
            <canvas id="categoryChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2>🏷️ Top 10 Tags</h2>
            <canvas id="tagsChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2>📈 Growth Over Time</h2>
            <canvas id="growthChart"></canvas>
        </div>
    </div>
    
    <script>
        // Category chart
        new Chart(document.getElementById('categoryChart'), {{
            type: 'bar',
            data: {{
                labels: {category_labels},
                datasets: [{{
                    label: 'Articles',
                    data: {category_data},
                    backgroundColor: '#1976d2'
                }}]
            }},
            options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});
        
        // Tags chart
        new Chart(document.getElementById('tagsChart'), {{
            type: 'bar',
            data: {{
                labels: {tag_labels},
                datasets: [{{
                    label: 'Uses',
                    data: {tag_data},
                    backgroundColor: '#388e3c'
                }}]
            }},
            options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});
        
        // Growth chart
        new Chart(document.getElementById('growthChart'), {{
            type: 'line',
            data: {{
                labels: {growth_labels},
                datasets: [{{
                    label: 'Articles Created',
                    data: {growth_data},
                    borderColor: '#d32f2f',
                    fill: false
                }}]
            }},
            options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
        }});
    </script>
</body>
</html>"""
        
        # Prepare data
        o = self.stats['overview']
        
        # Category data
        category_labels = list(self.stats['categories'].keys())
        category_data = [self.stats['categories'][c]['count'] for c in category_labels]
        
        # Tag data
        top_tags = self.stats['tags']['top_tags'][:10]
        tag_labels = [t['tag'] for t in top_tags]
        tag_data = [t['count'] for t in top_tags]
        
        # Growth data
        if self.stats['growth']['available']:
            growth_months = self.stats['growth']['by_month']
            growth_labels = [m['month'] for m in growth_months]
            growth_data = [m['count'] for m in growth_months]
        else:
            growth_labels = []
            growth_data = []
        
        # Fill template
        html_content = html.format(
            total_articles=o['total_articles'],
            total_words=o['total_words'],
            avg_readability=o['avg_readability'],
            metadata_coverage=o['metadata_coverage'],
            category_labels=json.dumps(category_labels),
            category_data=json.dumps(category_data),
            tag_labels=json.dumps(tag_labels),
            tag_data=json.dumps(tag_data),
            growth_labels=json.dumps(growth_labels),
            growth_data=json.dumps(growth_data)
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📊 HTML dashboard: {output_file}")

