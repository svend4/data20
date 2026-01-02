#!/usr/bin/env python3
"""
Chain References - Цепные ссылки
Вдохновлено: Книги в средневековых библиотеках приковывались цепями

Создаёт навигационные цепочки между связанными статьями:
- Предыдущая/Следующая статья
- Серии статей
- Учебные треки (последовательное изучение)
"""

from pathlib import Path
import yaml
import re
import json
from collections import defaultdict


class ChainManager:
    """
    Менеджер цепных ссылок между статьями
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.chains_file = self.root_dir / ".chains" / "chains.json"

        # Создать директорию
        self.chains_file.parent.mkdir(exist_ok=True)

        # Загрузить цепочки
        self.chains = self.load_chains()

    def load_chains(self):
        """Загрузить определения цепочек"""
        if self.chains_file.exists():
            with open(self.chains_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_chains(self):
        """Сохранить цепочки"""
        with open(self.chains_file, 'w', encoding='utf-8') as f:
            json.dump(self.chains, f, ensure_ascii=False, indent=2)

    def create_chain(self, chain_id, title, description="", chain_type="series"):
        """
        Создать новую цепочку

        chain_type может быть:
        - series: серия статей
        - tutorial: учебный трек (от простого к сложному)
        - chronological: хронологическая последовательность
        - topic: статьи на одну тему
        """
        self.chains[chain_id] = {
            'title': title,
            'description': description,
            'type': chain_type,
            'articles': [],
            'metadata': {}
        }

        self.save_chains()
        return self.chains[chain_id]

    def add_to_chain(self, chain_id, article_file, position=None):
        """
        Добавить статью в цепочку

        position: None (в конец), или индекс для вставки
        """
        if chain_id not in self.chains:
            return False

        article_path = str(Path(article_file).relative_to(self.root_dir))

        if position is None:
            self.chains[chain_id]['articles'].append(article_path)
        else:
            self.chains[chain_id]['articles'].insert(position, article_path)

        self.save_chains()
        return True

    def remove_from_chain(self, chain_id, article_file):
        """Удалить статью из цепочки"""
        if chain_id not in self.chains:
            return False

        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path in self.chains[chain_id]['articles']:
            self.chains[chain_id]['articles'].remove(article_path)
            self.save_chains()
            return True

        return False

    def get_chain(self, chain_id):
        """Получить цепочку"""
        return self.chains.get(chain_id)

    def get_article_chains(self, article_file):
        """Найти все цепочки, в которых участвует статья"""
        article_path = str(Path(article_file).relative_to(self.root_dir))

        article_chains = []
        for chain_id, chain in self.chains.items():
            if article_path in chain['articles']:
                article_chains.append({
                    'id': chain_id,
                    'title': chain['title'],
                    'position': chain['articles'].index(article_path) + 1,
                    'total': len(chain['articles'])
                })

        return article_chains

    def get_navigation(self, article_file):
        """
        Получить навигацию для статьи (предыдущая/следующая в цепочке)
        """
        article_path = str(Path(article_file).relative_to(self.root_dir))

        navigation = {}

        for chain_id, chain in self.chains.items():
            if article_path not in chain['articles']:
                continue

            articles = chain['articles']
            index = articles.index(article_path)

            nav = {
                'chain_id': chain_id,
                'chain_title': chain['title'],
                'position': index + 1,
                'total': len(articles),
                'previous': None,
                'next': None
            }

            if index > 0:
                nav['previous'] = articles[index - 1]

            if index < len(articles) - 1:
                nav['next'] = articles[index + 1]

            navigation[chain_id] = nav

        return navigation

    def generate_navigation_links(self, article_file):
        """Создать markdown навигацию для статьи"""
        navigation = self.get_navigation(article_file)

        if not navigation:
            return ""

        lines = []
        lines.append("---\n\n")
        lines.append("## 🔗 Навигация по цепочкам\n\n")

        for chain_id, nav in navigation.items():
            lines.append(f"### {nav['chain_title']}\n\n")
            lines.append(f"**Позиция**: {nav['position']} / {nav['total']}\n\n")

            # Навигационные ссылки
            nav_links = []

            if nav['previous']:
                prev_title = self._get_article_title(nav['previous'])
                nav_links.append(f"← [Предыдущая: {prev_title}]({nav['previous']})")

            if nav['next']:
                next_title = self._get_article_title(nav['next'])
                nav_links.append(f"[Следующая: {next_title}]({nav['next']}) →")

            if nav_links:
                lines.append(" | ".join(nav_links) + "\n\n")

        return ''.join(lines)

    def _get_article_title(self, article_path):
        """Получить заголовок статьи"""
        try:
            full_path = self.root_dir / article_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                return fm.get('title', Path(article_path).stem)
        except:
            pass

        return Path(article_path).stem

    def visualize_chain(self, chain_id):
        """Визуализировать цепочку"""
        chain = self.chains.get(chain_id)

        if not chain:
            return None

        lines = []
        lines.append(f"\n🔗 Цепочка: {chain['title']}\n")
        lines.append(f"   Тип: {chain['type']}\n")
        lines.append(f"   Статей: {len(chain['articles'])}\n\n")

        for i, article_path in enumerate(chain['articles'], 1):
            title = self._get_article_title(article_path)
            arrow = "   ⬇\n" if i < len(chain['articles']) else ""
            lines.append(f"{i}. {title}\n")
            lines.append(f"   📂 {article_path}\n")
            lines.append(arrow)

        return ''.join(lines)

    def export_chain_markdown(self, chain_id, output_file=None):
        """Экспортировать цепочку в markdown"""
        chain = self.chains.get(chain_id)

        if not chain:
            return None

        lines = []
        lines.append(f"# 🔗 {chain['title']}\n\n")

        if chain['description']:
            lines.append(f"> {chain['description']}\n\n")

        lines.append(f"**Тип**: {chain['type']}  \n")
        lines.append(f"**Статей в цепочке**: {len(chain['articles'])}  \n\n")

        lines.append("---\n\n")

        # Список статей с навигацией
        for i, article_path in enumerate(chain['articles'], 1):
            title = self._get_article_title(article_path)

            lines.append(f"## {i}. {title}\n\n")
            lines.append(f"📂 [`{article_path}`]({article_path})\n\n")

            # Навигация
            nav = []
            if i > 1:
                prev_title = self._get_article_title(chain['articles'][i-2])
                nav.append(f"← [{prev_title}]({chain['articles'][i-2]})")

            if i < len(chain['articles']):
                next_title = self._get_article_title(chain['articles'][i])
                nav.append(f"[{next_title}]({chain['articles'][i]}) →")

            if nav:
                lines.append(" | ".join(nav) + "\n\n")

            lines.append("---\n\n")

        content = ''.join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    def auto_detect_chains(self):
        """
        Автоматически обнаружить потенциальные цепочки

        На основе:
        - Серий статей (series: X в метаданных)
        - Общих тегов и категорий
        - Ссылок друг на друга
        """
        print("🔍 Автоматическое обнаружение цепочек...\n")

        # Статьи по сериям
        by_series = defaultdict(list)

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    series = fm.get('series')
                    if series:
                        article_path = str(md_file.relative_to(self.root_dir))
                        part = fm.get('part', 0)
                        by_series[series].append((part, article_path))
            except:
                pass

        # Создать цепочки для серий
        detected = 0
        for series_name, articles in by_series.items():
            # Сортировать по номеру части
            articles.sort(key=lambda x: x[0])

            chain_id = f"series_{series_name.lower().replace(' ', '_')}"

            if chain_id not in self.chains:
                self.create_chain(
                    chain_id,
                    f"Серия: {series_name}",
                    description=f"Автоматически обнаруженная серия статей",
                    chain_type="series"
                )

                for _, article_path in articles:
                    self.add_to_chain(chain_id, self.root_dir / article_path)

                detected += 1
                print(f"✅ Обнаружена серия: {series_name} ({len(articles)} статей)")

        print(f"\n✅ Обнаружено новых цепочек: {detected}")

    def generate_report(self):
        """Создать отчёт по всем цепочкам"""
        lines = []
        lines.append("# 🔗 Отчёт по цепочкам статей\n\n")

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего цепочек**: {len(self.chains)}\n")

        total_articles = sum(len(chain['articles']) for chain in self.chains.values())
        lines.append(f"- **Всего статей в цепочках**: {total_articles}\n\n")

        # По типам
        by_type = defaultdict(int)
        for chain in self.chains.values():
            by_type[chain['type']] += 1

        lines.append("## По типам\n\n")
        for chain_type, count in sorted(by_type.items()):
            lines.append(f"- **{chain_type}**: {count}\n")

        lines.append("\n## Все цепочки\n\n")

        for chain_id, chain in sorted(self.chains.items()):
            lines.append(f"### {chain['title']}\n\n")
            lines.append(f"- **ID**: `{chain_id}`\n")
            lines.append(f"- **Тип**: {chain['type']}\n")
            lines.append(f"- **Статей**: {len(chain['articles'])}\n")

            if chain['description']:
                lines.append(f"- **Описание**: {chain['description']}\n")

            lines.append("\n")

        return ''.join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Chain References - Управление цепочками статей'
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # create - создать цепочку
    create_parser = subparsers.add_parser('create', help='Создать цепочку')
    create_parser.add_argument('chain_id', help='ID цепочки')
    create_parser.add_argument('title', help='Название')
    create_parser.add_argument('-d', '--description', default='', help='Описание')
    create_parser.add_argument('-t', '--type', default='series',
                              choices=['series', 'tutorial', 'chronological', 'topic'],
                              help='Тип цепочки')

    # add - добавить статью
    add_parser = subparsers.add_parser('add', help='Добавить статью в цепочку')
    add_parser.add_argument('chain_id', help='ID цепочки')
    add_parser.add_argument('article', help='Путь к статье')
    add_parser.add_argument('-p', '--position', type=int, help='Позиция (опционально)')

    # nav - показать навигацию
    nav_parser = subparsers.add_parser('nav', help='Показать навигацию для статьи')
    nav_parser.add_argument('article', help='Путь к статье')

    # show - показать цепочку
    show_parser = subparsers.add_parser('show', help='Показать цепочку')
    show_parser.add_argument('chain_id', help='ID цепочки')

    # export - экспортировать цепочку
    export_parser = subparsers.add_parser('export', help='Экспортировать цепочку')
    export_parser.add_argument('chain_id', help='ID цепочки')
    export_parser.add_argument('-o', '--output', help='Выходной файл')

    # auto-detect - автоматическое обнаружение
    subparsers.add_parser('auto-detect', help='Автоматически обнаружить цепочки')

    # report - отчёт
    subparsers.add_parser('report', help='Создать отчёт')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    manager = ChainManager(root_dir)

    if args.command == 'create':
        chain = manager.create_chain(
            args.chain_id,
            args.title,
            description=args.description,
            chain_type=args.type
        )
        print(f"✅ Цепочка '{args.chain_id}' создана")

    elif args.command == 'add':
        article_path = root_dir / args.article
        if manager.add_to_chain(args.chain_id, article_path, args.position):
            print(f"✅ Статья добавлена в цепочку '{args.chain_id}'")
        else:
            print(f"❌ Цепочка не найдена")

    elif args.command == 'nav':
        article_path = root_dir / args.article
        nav_md = manager.generate_navigation_links(article_path)
        if nav_md:
            print(nav_md)
        else:
            print("⚠️  Статья не входит ни в одну цепочку")

    elif args.command == 'show':
        viz = manager.visualize_chain(args.chain_id)
        if viz:
            print(viz)
        else:
            print(f"❌ Цепочка '{args.chain_id}' не найдена")

    elif args.command == 'export':
        output = args.output or f"{args.chain_id}.md"
        content = manager.export_chain_markdown(args.chain_id, output)
        if content:
            print(f"✅ Цепочка экспортирована в {output}")
        else:
            print(f"❌ Цепочка не найдена")

    elif args.command == 'auto-detect':
        manager.auto_detect_chains()

    elif args.command == 'report':
        report = manager.generate_report()
        output_file = root_dir / "CHAINS_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
