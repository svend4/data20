#!/usr/bin/env python3
"""
Citation Index - Индекс цитирований
Отслеживает, какие статьи цитируют друг друга

Вдохновлено: Science Citation Index (Eugene Garfield, 1964)
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class CitationIndexer:
    """Индексатор цитирований"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Индекс цитирований
        self.citations = defaultdict(lambda: {'cited_by': [], 'cites': [], 'citation_count': 0})

        # Все статьи
        self.articles = {}

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

    def extract_citations(self, content, source_file):
        """Извлечь цитирования из содержимого"""
        citations = []

        # Markdown ссылки на другие статьи
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for text, link in links:
            # Пропустить внешние ссылки
            if link.startswith('http'):
                continue

            # Разрешить относительный путь
            try:
                target = (Path(source_file).parent / link).resolve()

                # Убрать якорь если есть
                if '#' in str(target):
                    target = Path(str(target).split('#')[0])

                # Проверить, что файл существует
                if target.exists() and target.is_relative_to(self.root_dir):
                    target_path = str(target.relative_to(self.root_dir))
                    citations.append({
                        'target': target_path,
                        'context': text,
                        'type': 'link'
                    })
            except:
                pass

        # Ссылки из frontmatter (related)
        frontmatter, _ = self.extract_frontmatter_and_content(source_file)

        if frontmatter and 'related' in frontmatter:
            related = frontmatter['related']
            if isinstance(related, list):
                for link in related:
                    try:
                        target = (Path(source_file).parent / link).resolve()

                        if target.exists() and target.is_relative_to(self.root_dir):
                            target_path = str(target.relative_to(self.root_dir))
                            citations.append({
                                'target': target_path,
                                'context': 'Related article',
                                'type': 'frontmatter'
                            })
                    except:
                        pass

        return citations

    def build_index(self):
        """Построить индекс цитирований"""
        print("📚 Построение индекса цитирований...\n")

        # Собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))

            self.articles[article_path] = {
                'title': frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem,
                'date': frontmatter.get('date', '') if frontmatter else '',
                'author': frontmatter.get('author', frontmatter.get('source', '')) if frontmatter else ''
            }

        # Построить граф цитирований
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            _, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            # Извлечь цитирования
            citations = self.extract_citations(content, md_file)

            for citation in citations:
                target = citation['target']

                # Добавить в граф
                if target not in self.citations[article_path]['cites']:
                    self.citations[article_path]['cites'].append({
                        'article': target,
                        'context': citation['context'],
                        'type': citation['type']
                    })

                if article_path not in [c['article'] for c in self.citations[target]['cited_by']]:
                    self.citations[target]['cited_by'].append({
                        'article': article_path,
                        'context': citation['context'],
                        'type': citation['type']
                    })

                # Увеличить счётчик
                self.citations[target]['citation_count'] += 1

        print(f"   Статей проиндексировано: {len(self.articles)}")
        print(f"   Связей найдено: {sum(len(c['cites']) for c in self.citations.values())}\n")

    def calculate_h_index(self, article_path):
        """
        Вычислить h-index для статьи
        h-index = максимальное h, при котором статья имеет h цитирований
        от статей, у которых тоже есть хотя бы h цитирований
        """
        citation_counts = []

        for citing in self.citations[article_path]['cited_by']:
            citing_article = citing['article']
            citing_count = self.citations[citing_article]['citation_count']
            citation_counts.append(citing_count)

        citation_counts.sort(reverse=True)

        h = 0
        for i, count in enumerate(citation_counts, 1):
            if count >= i:
                h = i
            else:
                break

        return h

    def get_most_cited(self, limit=10):
        """Получить самые цитируемые статьи"""
        cited = [(article, data['citation_count'])
                 for article, data in self.citations.items()
                 if data['citation_count'] > 0]

        cited.sort(key=lambda x: -x[1])

        return cited[:limit]

    def generate_report(self):
        """Создать отчёт по цитированиям"""
        lines = []
        lines.append("# 📚 Индекс цитирований\n\n")
        lines.append("> Science Citation Index style (Eugene Garfield, 1964)\n\n")

        # Статистика
        total_citations = sum(data['citation_count'] for data in self.citations.values())
        articles_cited = len([a for a, d in self.citations.items() if d['citation_count'] > 0])

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Статей с цитированиями**: {articles_cited}\n")
        lines.append(f"- **Всего цитирований**: {total_citations}\n")

        if self.articles:
            avg = total_citations / len(self.articles)
            lines.append(f"- **Среднее на статью**: {avg:.2f}\n\n")

        # Топ цитируемых
        lines.append("## Топ-10 самых цитируемых статей\n\n")

        most_cited = self.get_most_cited(10)

        for i, (article, count) in enumerate(most_cited, 1):
            title = self.articles.get(article, {}).get('title', article)
            h_index = self.calculate_h_index(article)

            lines.append(f"### {i}. {title}\n\n")
            lines.append(f"- **Цитирований**: {count}\n")
            lines.append(f"- **h-index**: {h_index}\n")
            lines.append(f"- **Файл**: `{article}`\n\n")

            # Кто цитирует
            if self.citations[article]['cited_by']:
                lines.append("**Цитируют:**\n")
                for citing in self.citations[article]['cited_by'][:5]:
                    citing_title = self.articles.get(citing['article'], {}).get('title', citing['article'])
                    lines.append(f"- [{citing_title}]({citing['article']}) — \"{citing['context']}\"\n")

                if len(self.citations[article]['cited_by']) > 5:
                    lines.append(f"\n...и ещё {len(self.citations[article]['cited_by']) - 5}\n")

                lines.append("\n")

        # Статьи без цитирований
        uncited = [a for a, d in self.citations.items() if d['citation_count'] == 0]

        lines.append(f"\n## Статьи без цитирований ({len(uncited)})\n\n")

        if uncited:
            for article in sorted(uncited)[:10]:
                title = self.articles.get(article, {}).get('title', article)
                lines.append(f"- [{title}]({article})\n")

            if len(uncited) > 10:
                lines.append(f"\n...и ещё {len(uncited) - 10}\n")
        else:
            lines.append("Все статьи имеют цитирования! 🎉\n")

        output_file = self.root_dir / "CITATION_INDEX.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Индекс цитирований: {output_file}")

    def save_json(self):
        """Сохранить индекс в JSON"""
        # Конвертировать даты в строки
        articles_serializable = {}
        for path, info in self.articles.items():
            articles_serializable[path] = {
                'title': info['title'],
                'date': str(info['date']) if info['date'] else '',
                'author': info['author']
            }

        data = {
            'articles': articles_serializable,
            'citations': {
                article: {
                    'citation_count': data['citation_count'],
                    'h_index': self.calculate_h_index(article),
                    'cited_by': data['cited_by'],
                    'cites': data['cites']
                }
                for article, data in self.citations.items()
            }
        }

        output_file = self.root_dir / "citation_index.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON индекс: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    indexer = CitationIndexer(root_dir)
    indexer.build_index()
    indexer.generate_report()
    indexer.save_json()


if __name__ == "__main__":
    main()
