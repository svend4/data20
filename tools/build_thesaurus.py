#!/usr/bin/env python3
"""
Thesaurus Builder - Тезаурус синонимов и связанных терминов

Создаёт словарь синонимов, антонимов и связанных терминов
на основе анализа контента базы знаний.
"""

from pathlib import Path
import yaml
import re
import json
from collections import defaultdict


class ThesaurusBuilder:
    """
    Построитель тезауруса для базы знаний
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.thesaurus_file = self.root_dir / "thesaurus.json"

        # Тезаурус: term -> {synonyms, related, antonyms, broader, narrower}
        self.thesaurus = {}

        # Известные синонимы (можно расширить)
        self.known_synonyms = {
            'AI': ['искусственный интеллект', 'ИИ', 'artificial intelligence', 'machine intelligence'],
            'LLM': ['большие языковые модели', 'language models', 'GPT'],
            'Python': ['питон', 'пайтон'],
            'холодильник': ['рефрижератор', 'морозильник', 'fridge', 'refrigerator'],
            'программирование': ['coding', 'разработка', 'development', 'programming'],
            'паттерн': ['шаблон', 'pattern', 'template'],
        }

        # Антонимы
        self.known_antonyms = {
            'hot': ['cold'],
            'большой': ['маленький'],
            'новый': ['старый'],
            'начало': ['конец'],
        }

        # Иерархические отношения (broader/narrower)
        self.hierarchies = {
            'программирование': {
                'narrower': ['Python', 'JavaScript', 'Java', 'C++'],
                'broader': ['компьютерные науки', 'IT']
            },
            'AI': {
                'narrower': ['LLM', 'машинное обучение', 'нейронные сети', 'компьютерное зрение'],
                'broader': ['компьютерные науки']
            },
            'бытовая техника': {
                'narrower': ['холодильник', 'плита', 'стиральная машина'],
                'broader': ['домашнее хозяйство']
            }
        }

    def extract_frontmatter(self, file_path):
        """Извлечь frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
        except:
            pass
        return None

    def add_term(self, term, **relations):
        """
        Добавить термин в тезаурус

        relations может содержать:
        - synonyms: список синонимов
        - related: список связанных терминов
        - antonyms: список антонимов
        - broader: более широкие термины
        - narrower: более узкие термины
        """
        term_lower = term.lower()

        if term_lower not in self.thesaurus:
            self.thesaurus[term_lower] = {
                'canonical': term,  # Каноническая форма
                'synonyms': set(),
                'related': set(),
                'antonyms': set(),
                'broader': set(),
                'narrower': set(),
                'articles': []  # Статьи, где встречается
            }

        # Обновить отношения
        for relation_type, terms in relations.items():
            if relation_type in self.thesaurus[term_lower]:
                if isinstance(terms, (list, set)):
                    self.thesaurus[term_lower][relation_type].update(terms)
                else:
                    self.thesaurus[term_lower][relation_type].add(terms)

    def build_from_tags(self):
        """Построить тезаурус на основе тегов статей"""
        print("🔍 Анализ тегов...\n")

        # Собрать все теги и их совместное появление
        tag_cooccurrence = defaultdict(lambda: defaultdict(int))
        all_tags = set()

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter = self.extract_frontmatter(md_file)

            if not frontmatter:
                continue

            tags = frontmatter.get('tags', [])
            if not isinstance(tags, list):
                continue

            # Добавить теги
            for tag in tags:
                all_tags.add(tag)
                self.add_term(tag)

                # Записать статью
                file_path = str(md_file.relative_to(self.root_dir))
                self.thesaurus[tag.lower()]['articles'].append(file_path)

            # Теги, которые появляются вместе - вероятно связаны
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    tag_cooccurrence[tag1.lower()][tag2.lower()] += 1
                    tag_cooccurrence[tag2.lower()][tag1.lower()] += 1

        # Добавить связанные термины на основе совместного появления
        for tag, related_tags in tag_cooccurrence.items():
            # Топ-5 самых часто встречающихся вместе тегов
            top_related = sorted(related_tags.items(), key=lambda x: -x[1])[:5]

            for related_tag, count in top_related:
                if count >= 2:  # Минимум 2 совместных появления
                    self.add_term(tag, related=[related_tag])

        print(f"   Найдено уникальных тегов: {len(all_tags)}")

    def build_from_known_relations(self):
        """Добавить известные синонимы и отношения"""
        print("📚 Добавление известных отношений...\n")

        # Синонимы
        for term, synonyms in self.known_synonyms.items():
            self.add_term(term, synonyms=synonyms)

            # Обратные связи
            for syn in synonyms:
                self.add_term(syn, synonyms=[term] + [s for s in synonyms if s != syn])

        # Антонимы
        for term, antonyms in self.known_antonyms.items():
            self.add_term(term, antonyms=antonyms)

            for ant in antonyms:
                self.add_term(ant, antonyms=[term])

        # Иерархии
        for term, relations in self.hierarchies.items():
            broader = relations.get('broader', [])
            narrower = relations.get('narrower', [])

            self.add_term(term, broader=broader, narrower=narrower)

            # Обратные связи
            for b in broader:
                self.add_term(b, narrower=[term])

            for n in narrower:
                self.add_term(n, broader=[term])

    def find_similar_terms(self, term1, term2):
        """Определить схожесть двух терминов (0.0 - 1.0)"""
        term1_lower = term1.lower()
        term2_lower = term2.lower()

        # Точное совпадение
        if term1_lower == term2_lower:
            return 1.0

        # Подстрока
        if term1_lower in term2_lower or term2_lower in term1_lower:
            return 0.8

        # Общие буквы (простая метрика)
        common = set(term1_lower) & set(term2_lower)
        union = set(term1_lower) | set(term2_lower)

        if union:
            return len(common) / len(union) * 0.5

        return 0.0

    def build(self):
        """Построить полный тезаурус"""
        print("🔤 Построение тезауруса...\n")

        self.build_from_tags()
        self.build_from_known_relations()

        print(f"\n✅ Тезаурус построен")
        print(f"   Терминов: {len(self.thesaurus)}")

    def save(self):
        """Сохранить тезаурус"""
        # Конвертировать sets в lists для JSON
        thesaurus_json = {}

        for term, data in self.thesaurus.items():
            thesaurus_json[term] = {
                'canonical': data['canonical'],
                'synonyms': list(data['synonyms']),
                'related': list(data['related']),
                'antonyms': list(data['antonyms']),
                'broader': list(data['broader']),
                'narrower': list(data['narrower']),
                'articles': data['articles']
            }

        with open(self.thesaurus_file, 'w', encoding='utf-8') as f:
            json.dump(thesaurus_json, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Тезаурус сохранён: {self.thesaurus_file}")

    def save_markdown(self):
        """Сохранить тезаурус в markdown"""
        lines = []
        lines.append("# 🔤 Тезаурус\n\n")
        lines.append("> Словарь терминов с синонимами, антонимами и связями\n\n")

        lines.append(f"**Всего терминов**: {len(self.thesaurus)}\n\n")

        # Алфавитный указатель
        current_letter = None

        for term in sorted(self.thesaurus.keys()):
            data = self.thesaurus[term]

            # Новая буква - новый раздел
            first_letter = term[0].upper()
            if first_letter != current_letter:
                current_letter = first_letter
                lines.append(f"\n## {current_letter}\n\n")

            # Термин
            canonical = data['canonical']
            lines.append(f"### {canonical}\n\n")

            # Синонимы
            if data['synonyms']:
                syns = ', '.join(sorted(data['synonyms']))
                lines.append(f"**Синонимы**: {syns}  \n")

            # Связанные
            if data['related']:
                related = ', '.join(sorted(data['related']))
                lines.append(f"**Связанные**: {related}  \n")

            # Антонимы
            if data['antonyms']:
                ants = ', '.join(sorted(data['antonyms']))
                lines.append(f"**Антонимы**: {ants}  \n")

            # Иерархия
            if data['broader']:
                broader = ', '.join(sorted(data['broader']))
                lines.append(f"**Более общее**: {broader}  \n")

            if data['narrower']:
                narrower = ', '.join(sorted(data['narrower']))
                lines.append(f"**Более узкое**: {narrower}  \n")

            # Статьи
            if data['articles']:
                lines.append(f"**Встречается в**: {len(data['articles'])} статьях  \n")

            lines.append("\n")

        output_file = self.root_dir / "THESAURUS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown тезаурус: {output_file}")

    def search(self, term):
        """Поиск термина в тезаурусе"""
        term_lower = term.lower()

        if term_lower in self.thesaurus:
            return self.thesaurus[term_lower]

        # Поиск по синонимам
        for t, data in self.thesaurus.items():
            if term_lower in [s.lower() for s in data['synonyms']]:
                return data

        return None

    def expand_query(self, query_terms):
        """
        Расширить поисковый запрос синонимами

        Например: ["AI"] -> ["AI", "ИИ", "искусственный интеллект", ...]
        """
        expanded = set(query_terms)

        for term in query_terms:
            data = self.search(term)
            if data:
                expanded.update(data['synonyms'])
                # Можно также добавить related термины
                # expanded.update(data['related'])

        return list(expanded)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Thesaurus Builder - Построение тезауруса'
    )

    parser.add_argument(
        '-s', '--search',
        help='Поиск термина в тезаурусе'
    )

    parser.add_argument(
        '-e', '--expand',
        nargs='+',
        help='Расширить запрос синонимами'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = ThesaurusBuilder(root_dir)

    if args.search or args.expand:
        # Загрузить существующий тезаурус
        if builder.thesaurus_file.exists():
            with open(builder.thesaurus_file, 'r', encoding='utf-8') as f:
                thesaurus_json = json.load(f)

            # Конвертировать обратно в sets
            for term, data in thesaurus_json.items():
                builder.thesaurus[term] = {
                    'canonical': data['canonical'],
                    'synonyms': set(data['synonyms']),
                    'related': set(data['related']),
                    'antonyms': set(data['antonyms']),
                    'broader': set(data['broader']),
                    'narrower': set(data['narrower']),
                    'articles': data['articles']
                }

        if args.search:
            result = builder.search(args.search)

            if result:
                print(f"\n🔤 Термин: {result['canonical']}\n")

                if result['synonyms']:
                    print(f"   Синонимы: {', '.join(sorted(result['synonyms']))}")

                if result['related']:
                    print(f"   Связанные: {', '.join(sorted(result['related']))}")

                if result['antonyms']:
                    print(f"   Антонимы: {', '.join(sorted(result['antonyms']))}")

                if result['broader']:
                    print(f"   Более общее: {', '.join(sorted(result['broader']))}")

                if result['narrower']:
                    print(f"   Более узкое: {', '.join(sorted(result['narrower']))}")

                if result['articles']:
                    print(f"\n   Встречается в {len(result['articles'])} статьях:")
                    for article in result['articles'][:5]:
                        print(f"      - {article}")
                    if len(result['articles']) > 5:
                        print(f"      ...и ещё {len(result['articles']) - 5}")

                print()
            else:
                print(f"❌ Термин '{args.search}' не найден в тезаурусе")

        elif args.expand:
            expanded = builder.expand_query(args.expand)
            print(f"\n🔍 Расширенный запрос:")
            print(f"   Оригинал: {', '.join(args.expand)}")
            print(f"   Расширен: {', '.join(expanded)}\n")

    else:
        # Построить тезаурус
        builder.build()
        builder.save()
        builder.save_markdown()


if __name__ == "__main__":
    main()
