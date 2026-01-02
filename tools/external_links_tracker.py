#!/usr/bin/env python3
"""
External Links Tracker - Трекинг внешних ссылок
Анализирует и каталогизирует все внешние ссылки

Вдохновлено: Web archives, Internet Archive
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
from urllib.parse import urlparse
import json


class ExternalLinksTracker:
    """Трекер внешних ссылок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Статистика ссылок
        self.links = defaultdict(lambda: {
            'url': '',
            'domain': '',
            'count': 0,
            'articles': []
        })

        self.articles_with_links = {}

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

    def extract_external_links(self, content):
        """Извлечь внешние ссылки"""
        links = []

        # Markdown ссылки
        markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', content)

        for text, url in markdown_links:
            # Очистить URL от якорей и query params (опционально)
            clean_url = url.split('#')[0]

            links.append({
                'url': url,
                'clean_url': clean_url,
                'text': text
            })

        # Голые URL
        bare_urls = re.findall(r'(?<!\()(https?://[^\s<>)\]]+)', content)

        for url in bare_urls:
            clean_url = url.split('#')[0]
            links.append({
                'url': url,
                'clean_url': clean_url,
                'text': ''
            })

        return links

    def analyze_all(self):
        """Анализировать все статьи"""
        print("🔗 Анализ внешних ссылок...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Извлечь ссылки
            external_links = self.extract_external_links(content)

            if external_links:
                self.articles_with_links[article_path] = {
                    'title': title,
                    'links': external_links
                }

                # Каталогизировать ссылки
                for link in external_links:
                    url = link['clean_url']

                    # Парсинг домена
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc
                    except:
                        domain = 'unknown'

                    self.links[url]['url'] = url
                    self.links[url]['domain'] = domain
                    self.links[url]['count'] += 1
                    self.links[url]['articles'].append({
                        'path': article_path,
                        'title': title,
                        'context': link['text']
                    })

        print(f"   Статей с внешними ссылками: {len(self.articles_with_links)}")
        print(f"   Уникальных внешних ссылок: {len(self.links)}\n")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Внешние ссылки\n\n")
        lines.append("> Каталог всех внешних ссылок в базе знаний\n\n")

        # Статистика
        total_links = sum(link['count'] for link in self.links.values())

        # Группировка по доменам
        by_domain = defaultdict(list)
        for url, data in self.links.items():
            by_domain[data['domain']].append((url, data))

        lines.append("## Статистика\n\n")
        lines.append(f"- **Уникальных ссылок**: {len(self.links)}\n")
        lines.append(f"- **Всего использований**: {total_links}\n")
        lines.append(f"- **Доменов**: {len(by_domain)}\n\n")

        # Топ доменов
        lines.append("## Топ-10 доменов\n\n")

        domain_stats = [
            (domain, sum(link['count'] for _, link in links))
            for domain, links in by_domain.items()
        ]
        domain_stats.sort(key=lambda x: -x[1])

        for i, (domain, count) in enumerate(domain_stats[:10], 1):
            lines.append(f"{i}. **{domain}** — {count} ссылок\n")

        lines.append("\n")

        # По доменам
        lines.append("## По доменам\n\n")

        for domain in sorted(by_domain.keys()):
            links = by_domain[domain]

            lines.append(f"### {domain} ({len(links)} ссылок)\n\n")

            for url, data in sorted(links, key=lambda x: -x[1]['count'])[:10]:
                lines.append(f"#### [{url}]({url})\n\n")
                lines.append(f"**Использований**: {data['count']}\n\n")
                lines.append("**Статьи:**\n")

                for article in data['articles']:
                    lines.append(f"- [{article['title']}]({article['path']})")
                    if article['context']:
                        lines.append(f" — *\"{article['context']}\"*")
                    lines.append("\n")

                lines.append("\n")

            if len(links) > 10:
                lines.append(f"*...и ещё {len(links) - 10} ссылок*\n\n")

        output_file = self.root_dir / "EXTERNAL_LINKS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")

    def save_json(self):
        """Сохранить данные в JSON"""
        data = {
            'total_unique_links': len(self.links),
            'total_uses': sum(link['count'] for link in self.links.values()),
            'links': {
                url: {
                    'domain': link['domain'],
                    'count': link['count'],
                    'articles': link['articles']
                }
                for url, link in self.links.items()
            }
        }

        output_file = self.root_dir / "external_links.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON данные: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    tracker = ExternalLinksTracker(root_dir)
    tracker.analyze_all()
    tracker.generate_report()
    tracker.save_json()


if __name__ == "__main__":
    main()
