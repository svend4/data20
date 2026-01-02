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
from collections import defaultdict


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

    parser = argparse.ArgumentParser(description='Advanced Sitemap Generator')
    parser.add_argument('--base-url', default='https://example.com',
                       help='Base URL сайта')
    parser.add_argument('--compress', action='store_true',
                       help='Сжать sitemap (gzip)')
    parser.add_argument('--robots', action='store_true',
                       help='Создать robots.txt')
    parser.add_argument('--ping', action='store_true',
                       help='Ping поисковых систем')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = AdvancedSitemapGenerator(root_dir, args.base_url)

    # Генерировать sitemaps
    sitemap_files = generator.generate_sitemaps(compress=args.compress)

    # Robots.txt
    if args.robots:
        generator.generate_robots_txt()

    # Статистика
    generator.print_statistics()

    # Ping
    if args.ping and sitemap_files:
        if generator.stats['sitemaps_created'] > 1:
            sitemap_url = f"{args.base_url}/sitemap_index.xml"
        else:
            sitemap_url = f"{args.base_url}/sitemap.xml"

        generator.ping_search_engines(sitemap_url)


if __name__ == "__main__":
    main()
