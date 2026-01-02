#!/usr/bin/env python3
"""
Sitemap Generator - Генератор sitemap.xml
Создаёт XML sitemap для поисковых систем
"""

from pathlib import Path
import yaml
import re
from datetime import datetime


class SitemapGenerator:
    """Генератор sitemap"""

    def __init__(self, root_dir=".", base_url="https://example.com"):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.base_url = base_url.rstrip('/')

    def extract_frontmatter(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
        except:
            pass
        return None

    def generate_sitemap(self):
        print("🗺️  Генерация sitemap.xml...\n")

        urls = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)

            article_path = str(md_file.relative_to(self.root_dir))
            url = f"{self.base_url}/{article_path}"

            # Последнее изменение
            lastmod = datetime.now().strftime('%Y-%m-%d')
            if frontmatter and 'date' in frontmatter:
                try:
                    date = frontmatter['date']
                    if isinstance(date, str):
                        lastmod = date
                    else:
                        lastmod = date.strftime('%Y-%m-%d')
                except:
                    pass

            urls.append({
                'loc': url,
                'lastmod': lastmod,
                'priority': '0.8'
            })

        # Создать XML
        xml_lines = []
        xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        for url_data in urls:
            xml_lines.append('  <url>\n')
            xml_lines.append(f'    <loc>{url_data["loc"]}</loc>\n')
            xml_lines.append(f'    <lastmod>{url_data["lastmod"]}</lastmod>\n')
            xml_lines.append(f'    <priority>{url_data["priority"]}</priority>\n')
            xml_lines.append('  </url>\n')

        xml_lines.append('</urlset>\n')

        output_file = self.root_dir / "sitemap.xml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(xml_lines)

        print(f"✅ Sitemap: {output_file} ({len(urls)} URLs)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sitemap Generator')
    parser.add_argument('--base-url', default='https://example.com', help='Base URL')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = SitemapGenerator(root_dir, args.base_url)
    generator.generate_sitemap()


if __name__ == "__main__":
    main()
