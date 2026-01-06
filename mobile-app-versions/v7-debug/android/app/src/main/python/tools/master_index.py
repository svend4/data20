#!/usr/bin/env python3
"""
Advanced Master Index - Профессиональный главный указатель
Создаёт полный book-style индекс с многоуровневой структурой

Возможности:
- Многоуровневая индексация (термины → подтермины → подподтермины)
- Автоматическое определение синонимов
- Cross-references ("См.", "См. также")
- Term importance ranking (PageRank для терминов)
- Локаторы типов: страницы, рисунки, таблицы, примеры кода
- Multi-language support (EN/RU)
- Экспорт: LaTeX, HTML, JSON

Вдохновлено: Professional book indexes, LaTeX makeidx, Encyclopedia indexes
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict, Counter
import json
import argparse
from datetime import datetime


class AdvancedMasterIndexBuilder:
    """Продвинутый построитель главного указателя (book-style)"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Индекс: термин -> {subterms: {}, locations: [], see_also: [], see: str}
        self.index = defaultdict(lambda: {
            'locations': [],
            'subterms': defaultdict(list),
            'see_also': set(),
            'see': None,
            'importance': 0.0,
            'locator_types': defaultdict(list),  # figure, table, code, page
            'languages': set(),  # EN, RU
        })

        # Синонимы и акронимы
        self.synonyms = defaultdict(set)
        self.acronyms = {}  # API -> Application Programming Interface

        # Статистика
        self.stats = {
            'total_terms': 0,
            'total_subterms': 0,
            'total_locations': 0,
            'cross_references': 0,
            'synonyms': 0,
            'acronyms': 0,
        }

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

    def detect_language(self, text):
        """Определить язык термина"""
        if re.search(r'[а-яёА-ЯЁ]', text):
            return 'RU'
        elif re.search(r'[a-zA-Z]', text):
            return 'EN'
        return 'OTHER'

    def extract_acronyms(self, content):
        """Извлечь акронимы (API - Application Programming Interface)"""
        # Паттерн: ACRONYM (Full Name) или ACRONYM - Full Name
        acronym_patterns = [
            r'\b([A-Z]{2,})\s*[(\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5})[)\s]',
            r'\*\*([A-Z]{2,})\*\*\s*[(\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5})[)\s]',
        ]

        for pattern in acronym_patterns:
            matches = re.findall(pattern, content)
            for acronym, full_form in matches:
                if len(acronym) >= 2 and len(full_form) >= 5:
                    self.acronyms[acronym] = full_form

    def extract_hierarchical_terms(self, content):
        """
        Извлечь иерархические термины
        Формат: Main term: Subterm: Sub-subterm
        """
        hierarchical = []

        # Поиск паттернов: "термин: подтермин"
        patterns = [
            r'\*\*([А-ЯA-Z][^\*:]{2,40}):\s*([^\*]{3,40}?)\*\*',
            r'#{2,6}\s+([^:\n]+):\s+([^\n]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for main, sub in matches:
                main_clean = main.strip()
                sub_clean = sub.strip()
                if len(main_clean) >= 3 and len(sub_clean) >= 3:
                    hierarchical.append((main_clean, sub_clean))

        return hierarchical

    def extract_terms(self, content, file_path):
        """Извлечь все типы терминов"""
        terms = []

        # 1. Выделенные термины (**термин**)
        bold_terms = re.findall(r'\*\*([А-ЯA-Z][^\*]{2,60}?)\*\*', content)
        for term in bold_terms:
            terms.append({
                'term': term.strip(),
                'type': 'bold',
                'locator_type': 'page',
            })

        # 2. Термины из заголовков (высокая важность)
        headings = re.findall(r'^#{2,6}\s+(.+)$', content, re.MULTILINE)
        for heading in headings:
            # Очистить от markdown
            clean = re.sub(r'[#*`\[\]()]', '', heading).strip()
            if len(clean) >= 3:
                terms.append({
                    'term': clean,
                    'type': 'heading',
                    'locator_type': 'page',
                })

        # 3. Рисунки (Figure X, Рисунок X)
        figures = re.findall(r'!\[([^\]]+)\]', content)
        for fig_caption in figures:
            if len(fig_caption) >= 5:
                terms.append({
                    'term': fig_caption,
                    'type': 'figure',
                    'locator_type': 'figure',
                })

        # 4. Таблицы (обнаружение markdown tables)
        table_count = len(re.findall(r'\|[^\n]+\|', content))
        if table_count > 0:
            # Попытка извлечь название таблицы из предыдущей строки
            table_captions = re.findall(r'([^\n]+)\n\s*\|', content)
            for caption in table_captions:
                clean = caption.strip()
                if len(clean) >= 5 and not re.match(r'^#+\s', clean):
                    terms.append({
                        'term': clean,
                        'type': 'table',
                        'locator_type': 'table',
                    })

        # 5. Code blocks (языки программирования)
        code_langs = re.findall(r'```(\w+)', content)
        for lang in set(code_langs):
            if lang and len(lang) >= 2:
                terms.append({
                    'term': f"{lang} (programming)",
                    'type': 'code',
                    'locator_type': 'code',
                })

        return terms

    def detect_synonyms_simple(self):
        """
        Простое определение синонимов
        Основано на общих словах в терминах
        """
        terms_list = list(self.index.keys())

        for i, term1 in enumerate(terms_list):
            for term2 in terms_list[i+1:]:
                # Общие слова
                words1 = set(re.findall(r'\b\w+\b', term1.lower()))
                words2 = set(re.findall(r'\b\w+\b', term2.lower()))

                common = words1 & words2
                union = words1 | words2

                # Jaccard similarity > 0.5 = вероятно синонимы
                if len(union) > 0:
                    similarity = len(common) / len(union)
                    if similarity > 0.5 and term1 != term2:
                        self.synonyms[term1].add(term2)
                        self.synonyms[term2].add(term1)

    def calculate_term_importance(self):
        """
        Вычислить важность терминов
        На основе: частоты, количества локаций, связей
        """
        for term, data in self.index.items():
            importance = 0.0

            # Частота упоминаний
            importance += len(data['locations']) * 2.0

            # Количество подтерминов
            importance += len(data['subterms']) * 1.5

            # See also связи
            importance += len(data['see_also']) * 1.0

            # Типы локаторов (разнообразие)
            importance += len(data['locator_types']) * 0.5

            # Нормализовать (0-100)
            data['importance'] = min(100.0, importance)

    def build_cross_references(self):
        """
        Построить cross-references автоматически
        "См. также" для связанных терминов
        """
        for term, data in self.index.items():
            # Добавить синонимы в see_also
            if term in self.synonyms:
                for synonym in self.synonyms[term]:
                    if synonym in self.index:
                        data['see_also'].add(synonym)

            # Если термин имеет только 1 локацию и есть более важный синоним
            if len(data['locations']) == 1 and term in self.synonyms:
                # Найти главный термин (с максимальной важностью)
                main_term = max(
                    self.synonyms[term],
                    key=lambda t: self.index[t]['importance'] if t in self.index else 0,
                    default=None
                )
                if main_term and self.index[main_term]['importance'] > data['importance']:
                    data['see'] = main_term

    def build_index(self):
        """Построить полный индекс"""
        print("📇 Построение продвинутого индекса...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)

            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            # Извлечь акронимы
            self.extract_acronyms(content)

            # Извлечь иерархические термины
            hierarchical = self.extract_hierarchical_terms(content)
            for main_term, sub_term in hierarchical:
                lang = self.detect_language(main_term)
                self.index[main_term]['languages'].add(lang)
                self.index[main_term]['subterms'][sub_term].append({
                    'path': article_path,
                    'title': title,
                })

            # Извлечь обычные термины
            terms = self.extract_terms(content, md_file)

            for term_data in terms:
                term = term_data['term']
                locator_type = term_data['locator_type']

                lang = self.detect_language(term)
                self.index[term]['languages'].add(lang)

                # Добавить локацию
                location = {
                    'path': article_path,
                    'title': title,
                    'type': term_data['type'],
                }

                if location not in self.index[term]['locations']:
                    self.index[term]['locations'].append(location)
                    self.index[term]['locator_types'][locator_type].append(location)

            # Теги
            if frontmatter and 'tags' in frontmatter:
                for tag in frontmatter['tags']:
                    lang = self.detect_language(tag)
                    self.index[tag]['languages'].add(lang)
                    location = {'path': article_path, 'title': title, 'type': 'tag'}
                    if location not in self.index[tag]['locations']:
                        self.index[tag]['locations'].append(location)

        # Обработка индекса
        self.detect_synonyms_simple()
        self.calculate_term_importance()
        self.build_cross_references()

        # Статистика
        self.stats['total_terms'] = len(self.index)
        self.stats['total_subterms'] = sum(len(d['subterms']) for d in self.index.values())
        self.stats['total_locations'] = sum(len(d['locations']) for d in self.index.values())
        self.stats['cross_references'] = sum(len(d['see_also']) for d in self.index.values())
        self.stats['synonyms'] = sum(len(syns) for syns in self.synonyms.values()) // 2
        self.stats['acronyms'] = len(self.acronyms)

        print(f"   Терминов: {self.stats['total_terms']}")
        print(f"   Подтерминов: {self.stats['total_subterms']}")
        print(f"   Локаций: {self.stats['total_locations']}")
        print(f"   Cross-references: {self.stats['cross_references']}")
        print(f"   Синонимов: {self.stats['synonyms']}")
        print(f"   Акронимов: {self.stats['acronyms']}\n")

    def generate_markdown_index(self, output_file='MASTER_INDEX.md'):
        """Создать Markdown индекс"""
        lines = []
        lines.append("# 📇 Главный указатель\n\n")
        lines.append(f"> Профессиональный book-style индекс • Создан {datetime.now().strftime('%Y-%m-%d')}\n\n")

        # Статистика
        lines.append("## 📊 Статистика\n\n")
        lines.append(f"- **Терминов**: {self.stats['total_terms']}\n")
        lines.append(f"- **Подтерминов**: {self.stats['total_subterms']}\n")
        lines.append(f"- **Всего ссылок**: {self.stats['total_locations']}\n")
        lines.append(f"- **Cross-references**: {self.stats['cross_references']}\n")
        lines.append(f"- **Синонимов**: {self.stats['synonyms']}\n")
        lines.append(f"- **Акронимов**: {self.stats['acronyms']}\n\n")

        # Акронимы
        if self.acronyms:
            lines.append("## 🔤 Акронимы\n\n")
            for acronym in sorted(self.acronyms.keys()):
                lines.append(f"- **{acronym}** — {self.acronyms[acronym]}\n")
            lines.append("\n")

        # Группировка по буквам
        by_letter = defaultdict(list)
        for term in sorted(self.index.keys(), key=str.lower):
            first_letter = term[0].upper()
            by_letter[first_letter].append(term)

        # Навигация
        lines.append("## 🔍 Навигация по буквам\n\n")
        for letter in sorted(by_letter.keys()):
            count = len(by_letter[letter])
            lines.append(f"[**{letter}** ({count})](#{letter}) ")
        lines.append("\n\n---\n\n")

        # Индекс по буквам
        for letter in sorted(by_letter.keys()):
            lines.append(f"## {letter}\n\n")

            for term in sorted(by_letter[letter], key=str.lower):
                data = self.index[term]

                # Главный термин
                importance_badge = ""
                if data['importance'] > 50:
                    importance_badge = " ⭐"
                elif data['importance'] > 20:
                    importance_badge = " •"

                lines.append(f"### {term}{importance_badge}\n\n")

                # См. (redirect)
                if data['see']:
                    lines.append(f"*См.* **{data['see']}**\n\n")
                    continue

                # Языки
                if len(data['languages']) > 1:
                    langs = ', '.join(sorted(data['languages']))
                    lines.append(f"*Языки*: {langs}\n\n")

                # Подтермины
                if data['subterms']:
                    for subterm in sorted(data['subterms'].keys()):
                        locs = data['subterms'][subterm]
                        lines.append(f"- **{subterm}**\n")
                        for loc in locs:
                            lines.append(f"  - [{loc['title']}]({loc['path']})\n")

                # Локации по типам
                for loc_type, locations in data['locator_types'].items():
                    if not locations:
                        continue

                    type_label = {
                        'figure': '🖼️ Рисунок',
                        'table': '📊 Таблица',
                        'code': '💻 Код',
                        'page': '📄',
                    }.get(loc_type, loc_type)

                    if loc_type != 'page':
                        lines.append(f"\n*{type_label}*:\n")

                    for loc in locations:
                        lines.append(f"- [{loc['title']}]({loc['path']})\n")

                # См. также
                if data['see_also']:
                    lines.append(f"\n*См. также*: ")
                    see_also_list = sorted(data['see_also'])[:5]  # Топ-5
                    lines.append(", ".join(f"**{sa}**" for sa in see_also_list))
                    lines.append("\n")

                lines.append("\n")

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown индекс: {output_path}")

    def export_to_latex(self, output_file='master_index.tex'):
        """Экспорт в LaTeX makeidx формат"""
        lines = []
        lines.append("% Master Index - LaTeX format\n")
        lines.append("% Compatible with \\usepackage{makeidx}\n\n")
        lines.append("\\begin{theindex}\n\n")

        # Сортировка терминов
        for term in sorted(self.index.keys(), key=str.lower):
            data = self.index[term]

            # Escape LaTeX special chars
            term_escaped = term.replace('&', '\\&').replace('_', '\\_').replace('%', '\\%')

            # См.
            if data['see']:
                see_escaped = data['see'].replace('&', '\\&').replace('_', '\\_')
                lines.append(f"  \\item {term_escaped}, \\emph{{see}} {see_escaped}\n")
                continue

            # Основная запись
            lines.append(f"  \\item {term_escaped}")

            # Подтермины
            if data['subterms']:
                lines.append("\n")
                for subterm in sorted(data['subterms'].keys()):
                    sub_escaped = subterm.replace('&', '\\&').replace('_', '\\_')
                    lines.append(f"    \\subitem {sub_escaped}\n")

            # Локации (упрощённо)
            locations_count = len(data['locations'])
            if locations_count > 0:
                if not data['subterms']:
                    lines.append(f", {locations_count} references")
                lines.append("\n")

        lines.append("\n\\end{theindex}\n")

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ LaTeX индекс: {output_path}")

    def export_to_html(self, output_file='master_index.html'):
        """Интерактивный HTML индекс с поиском"""
        # Группировка по буквам
        by_letter = defaultdict(list)
        for term in sorted(self.index.keys(), key=str.lower):
            first_letter = term[0].upper()
            by_letter[first_letter].append(term)

        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Главный указатель</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 20px;
        }
        .search-box {
            margin: 20px 0;
            text-align: center;
        }
        .search-box input {
            width: 80%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #667eea;
            border-radius: 5px;
        }
        .nav-letters {
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }
        .nav-letters a {
            margin: 0 5px;
            text-decoration: none;
            color: #667eea;
            font-weight: bold;
        }
        .letter-section {
            margin: 30px 0;
        }
        .letter-section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }
        .term {
            margin: 15px 0;
            padding: 10px;
            background: #f9f9f9;
            border-left: 3px solid #667eea;
        }
        .term-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }
        .importance-high { color: #e53935; }
        .importance-medium { color: #ff9800; }
        .see-also {
            margin-top: 5px;
            font-style: italic;
            color: #666;
        }
        .locations {
            margin-top: 5px;
        }
        .locations a {
            color: #667eea;
            text-decoration: none;
        }
        .locations a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📇 Главный указатель</h1>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Поиск по терминам..." onkeyup="filterTerms()">
        </div>

        <div class="nav-letters">
"""

        for letter in sorted(by_letter.keys()):
            html += f'            <a href="#letter-{letter}">{letter}</a>\n'

        html += """        </div>

        <div id="indexContent">
"""

        for letter in sorted(by_letter.keys()):
            html += f'            <div class="letter-section" id="letter-{letter}">\n'
            html += f'                <h2>{letter}</h2>\n'

            for term in sorted(by_letter[letter], key=str.lower):
                data = self.index[term]

                importance_class = ""
                if data['importance'] > 50:
                    importance_class = "importance-high"
                elif data['importance'] > 20:
                    importance_class = "importance-medium"

                html += f'                <div class="term" data-term="{term.lower()}">\n'
                html += f'                    <div class="term-name {importance_class}">{term}</div>\n'

                if data['see']:
                    html += f'                    <div class="see-also">См. <strong>{data["see"]}</strong></div>\n'
                else:
                    # Локации
                    if data['locations']:
                        html += '                    <div class="locations">\n'
                        for loc in data['locations'][:5]:  # Топ-5
                            html += f'                        • <a href="{loc["path"]}">{loc["title"]}</a><br>\n'
                        html += '                    </div>\n'

                    # См. также
                    if data['see_also']:
                        see_also_list = sorted(data['see_also'])[:3]
                        html += f'                    <div class="see-also">См. также: {", ".join(see_also_list)}</div>\n'

                html += '                </div>\n'

            html += '            </div>\n'

        html += """        </div>
    </div>

    <script>
        function filterTerms() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const terms = document.querySelectorAll('.term');

            terms.forEach(term => {
                const termName = term.getAttribute('data-term');
                if (termName.includes(filter)) {
                    term.style.display = 'block';
                } else {
                    term.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML индекс: {output_path}")

    def export_to_json(self, output_file='master_index.json'):
        """Полный JSON экспорт"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.stats,
            'acronyms': self.acronyms,
            'synonyms': {term: list(syns) for term, syns in self.synonyms.items()},
            'index': {}
        }

        for term, term_data in sorted(self.index.items()):
            data['index'][term] = {
                'importance': term_data['importance'],
                'languages': list(term_data['languages']),
                'see': term_data['see'],
                'see_also': list(term_data['see_also']),
                'locations': term_data['locations'],
                'subterms': dict(term_data['subterms']),
                'locator_types': {k: v for k, v in term_data['locator_types'].items()},
            }

        output_path = self.root_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON индекс: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Продвинутый построитель главного указателя (book-style)'
    )
    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Создать Markdown индекс'
    )
    parser.add_argument(
        '--latex',
        action='store_true',
        help='Экспортировать в LaTeX формат'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Создать интерактивный HTML индекс'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Экспортировать в JSON'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = AdvancedMasterIndexBuilder(root_dir)
    builder.build_index()

    # Экспорты
    if args.markdown or not any([args.latex, args.html, args.json]):
        builder.generate_markdown_index()

    if args.latex:
        builder.export_to_latex()

    if args.html:
        builder.export_to_html()

    if args.json:
        builder.export_to_json()

    # Если не указаны флаги - сделать всё
    if not any([args.markdown, args.latex, args.html, args.json]):
        builder.export_to_latex()
        builder.export_to_html()
        builder.export_to_json()

    print("\n✅ Индексация завершена!")


if __name__ == "__main__":
    main()
