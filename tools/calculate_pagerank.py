#!/usr/bin/env python3
"""
PageRank для базы знаний
Вдохновлено: Google PageRank (Larry Page & Sergey Brin, 1996)

Вычисляет важность статей на основе структуры ссылок между ними.
Статьи, на которые ссылаются другие важные статьи, получают более высокий ранг.
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class ArticlePageRank:
    """
    PageRank для статей базы знаний
    """

    def __init__(self, root_dir=".", damping=0.85, iterations=20):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Параметры PageRank
        self.damping = damping  # Коэффициент затухания (обычно 0.85)
        self.iterations = iterations  # Количество итераций

        # Граф статей
        self.articles = {}  # file_path -> metadata
        self.outlinks = defaultdict(list)  # from_file -> [to_file1, to_file2, ...]
        self.inlinks = defaultdict(list)   # to_file -> [from_file1, from_file2, ...]

        # Результаты
        self.pagerank = {}  # file_path -> score

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                return fm
        except:
            pass
        return None

    def resolve_link(self, from_file, link):
        """
        Разрешить относительную ссылку в абсолютный путь

        from_file: knowledge/computers/articles/ai/llm.md
        link: ../programming/python.md
        -> knowledge/computers/articles/programming/python.md
        """
        from_path = Path(from_file)

        # Если ссылка абсолютная (начинается с /)
        if link.startswith('/'):
            target = self.root_dir / link.lstrip('/')
        else:
            # Относительная ссылка
            target = (from_path.parent / link).resolve()

        # Нормализовать путь
        try:
            relative = target.relative_to(self.root_dir)
            return str(relative)
        except:
            return None

    def build_graph(self):
        """Построить граф ссылок между статьями"""
        print("🔗 Построение графа ссылок...\n")

        # Первый проход - собрать все статьи
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            file_path = str(md_file.relative_to(self.root_dir))
            frontmatter = self.extract_frontmatter(md_file)

            if not frontmatter:
                continue

            self.articles[file_path] = {
                'title': frontmatter.get('title', md_file.stem),
                'category': frontmatter.get('category', ''),
                'subcategory': frontmatter.get('subcategory', ''),
                'related': frontmatter.get('related', [])
            }

        # Второй проход - построить ссылки
        for file_path, metadata in self.articles.items():
            related = metadata['related']

            if not related or not isinstance(related, list):
                continue

            for link in related:
                # Разрешить относительную ссылку
                target = self.resolve_link(file_path, link)

                if target and target in self.articles:
                    # Добавить ребро графа
                    self.outlinks[file_path].append(target)
                    self.inlinks[target].append(file_path)

        print(f"   Статей: {len(self.articles)}")
        print(f"   Ссылок: {sum(len(links) for links in self.outlinks.values())}")

        # Статистика
        articles_with_outlinks = len([f for f in self.articles if self.outlinks[f]])
        articles_with_inlinks = len([f for f in self.articles if self.inlinks[f]])

        print(f"   Статей с исходящими ссылками: {articles_with_outlinks}")
        print(f"   Статей с входящими ссылками: {articles_with_inlinks}\n")

    def calculate(self):
        """Вычислить PageRank"""
        print(f"📊 Вычисление PageRank (damping={self.damping}, iterations={self.iterations})...\n")

        N = len(self.articles)

        if N == 0:
            print("⚠️  Нет статей для ранжирования")
            return

        # Инициализация: все статьи имеют одинаковый начальный ранг
        for file_path in self.articles:
            self.pagerank[file_path] = 1.0 / N

        # Итеративный расчёт PageRank
        for iteration in range(self.iterations):
            new_pagerank = {}

            for file_path in self.articles:
                # Базовое значение (вероятность случайного перехода)
                rank = (1 - self.damping) / N

                # Сумма вкладов от входящих ссылок
                for incoming_file in self.inlinks[file_path]:
                    # Вклад = PageRank источника / количество его исходящих ссылок
                    num_outlinks = len(self.outlinks[incoming_file])

                    if num_outlinks > 0:
                        rank += self.damping * (self.pagerank[incoming_file] / num_outlinks)

                new_pagerank[file_path] = rank

            # Обновить значения
            self.pagerank = new_pagerank

            # Прогресс
            if (iteration + 1) % 5 == 0:
                print(f"   Итерация {iteration + 1}/{self.iterations}")

        print()

    def get_rankings(self):
        """Получить отсортированный список статей по PageRank"""
        rankings = []

        for file_path, score in self.pagerank.items():
            metadata = self.articles[file_path]

            rankings.append({
                'file': file_path,
                'title': metadata['title'],
                'category': metadata['category'],
                'subcategory': metadata['subcategory'],
                'pagerank': score,
                'inlinks_count': len(self.inlinks[file_path]),
                'outlinks_count': len(self.outlinks[file_path])
            })

        # Сортировать по PageRank (убывание)
        rankings.sort(key=lambda x: x['pagerank'], reverse=True)

        return rankings

    def print_rankings(self):
        """Вывести рейтинг статей"""
        rankings = self.get_rankings()

        print("🏆 Рейтинг статей по PageRank:\n")
        print(f"{'Ранг':<6} {'Score':<12} {'→':<4} {'←':<4} {'Заголовок'}")
        print("=" * 80)

        for i, article in enumerate(rankings, 1):
            score = article['pagerank']
            inlinks = article['inlinks_count']
            outlinks = article['outlinks_count']
            title = article['title'][:50]

            print(f"{i:<6} {score:<12.6f} {outlinks:<4} {inlinks:<4} {title}")

        print()

    def save_rankings(self, output_file):
        """Сохранить рейтинг в JSON"""
        rankings = self.get_rankings()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)

        print(f"✅ Рейтинг сохранён: {output_file}")

    def save_markdown_report(self, output_file):
        """Сохранить отчёт в markdown"""
        rankings = self.get_rankings()

        lines = []
        lines.append("# 🏆 PageRank для базы знаний\n\n")
        lines.append(f"> Вычислено по алгоритму Google PageRank (1996)\n\n")

        lines.append("## Параметры\n\n")
        lines.append(f"- **Damping factor**: {self.damping}\n")
        lines.append(f"- **Iterations**: {self.iterations}\n")
        lines.append(f"- **Всего статей**: {len(self.articles)}\n")
        lines.append(f"- **Всего ссылок**: {sum(len(links) for links in self.outlinks.values())}\n\n")

        lines.append("## Рейтинг статей\n\n")
        lines.append("| Ранг | PageRank | ← | → | Статья | Категория |\n")
        lines.append("|------|----------|---|------|--------|----------|\n")

        for i, article in enumerate(rankings, 1):
            score = f"{article['pagerank']:.6f}"
            inlinks = article['inlinks_count']
            outlinks = article['outlinks_count']
            title = article['title']
            category = f"{article['category']}/{article['subcategory']}"
            file_path = article['file']

            lines.append(f"| {i} | {score} | {inlinks} | {outlinks} | [{title}]({file_path}) | {category} |\n")

        lines.append("\n## Топ-10 самых влиятельных статей\n\n")
        lines.append("Статьи с наивысшим PageRank (на них больше всего ссылаются другие важные статьи):\n\n")

        for i, article in enumerate(rankings[:10], 1):
            lines.append(f"### {i}. {article['title']}\n\n")
            lines.append(f"- **PageRank**: {article['pagerank']:.6f}\n")
            lines.append(f"- **Входящих ссылок**: {article['inlinks_count']}\n")
            lines.append(f"- **Исходящих ссылок**: {article['outlinks_count']}\n")
            lines.append(f"- **Файл**: `{article['file']}`\n")
            lines.append(f"- **Категория**: {article['category']}/{article['subcategory']}\n\n")

            # Показать, кто ссылается
            if self.inlinks[article['file']]:
                lines.append("**Ссылаются на эту статью:**\n\n")
                for ref_file in self.inlinks[article['file']][:5]:
                    ref_title = self.articles[ref_file]['title']
                    lines.append(f"- [{ref_title}]({ref_file})\n")
                lines.append("\n")

        lines.append("\n## Статьи без ссылок\n\n")
        orphans = [a for a in rankings if a['inlinks_count'] == 0 and a['outlinks_count'] == 0]

        if orphans:
            lines.append(f"Найдено {len(orphans)} изолированных статей (нет ни входящих, ни исходящих ссылок):\n\n")
            for article in orphans[:10]:
                lines.append(f"- **{article['title']}** — `{article['file']}`\n")
        else:
            lines.append("Все статьи связаны между собой. Отлично! 🎉\n")

        lines.append("\n## Интерпретация\n\n")
        lines.append("- **PageRank** — важность статьи в базе знаний\n")
        lines.append("- **← (Входящие)** — сколько статей ссылается на эту\n")
        lines.append("- **→ (Исходящие)** — на сколько статей ссылается эта\n\n")
        lines.append("Высокий PageRank означает, что статья является ключевой/центральной в базе знаний.\n")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown отчёт: {output_file}")

    def add_pagerank_to_articles(self):
        """Добавить PageRank в метаданные статей"""
        print("\n📝 Добавление PageRank в метаданные статей...\n")

        count = 0

        for file_path, score in self.pagerank.items():
            full_path = self.root_dir / file_path

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Извлечь frontmatter
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                if not match:
                    continue

                fm = yaml.safe_load(match.group(1))
                body = match.group(2)

                # Добавить или обновить PageRank
                old_rank = fm.get('pagerank')

                fm['pagerank'] = round(score, 6)
                fm['pagerank_inlinks'] = len(self.inlinks[file_path])
                fm['pagerank_outlinks'] = len(self.outlinks[file_path])

                # Записать обратно
                new_content = "---\n"
                new_content += yaml.dump(fm, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += body

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                if old_rank != fm['pagerank']:
                    count += 1
                    print(f"✅ {file_path}")

            except Exception as e:
                print(f"⚠️  Ошибка в {file_path}: {e}")

        print(f"\n✅ Обновлено статей: {count}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Создать PageRank калькулятор
    pr = ArticlePageRank(root_dir, damping=0.85, iterations=20)

    # Построить граф
    pr.build_graph()

    # Вычислить PageRank
    pr.calculate()

    # Вывести результаты
    pr.print_rankings()

    # Сохранить
    pr.save_rankings(root_dir / "pagerank.json")
    pr.save_markdown_report(root_dir / "PAGERANK.md")

    # Добавить в метаданные
    pr.add_pagerank_to_articles()

    print("\n✨ PageRank готов!")
    print("\n💡 Использование:")
    print("   - Просмотр рейтинга: cat PAGERANK.md")
    print("   - JSON данные: cat pagerank.json")


if __name__ == "__main__":
    main()
