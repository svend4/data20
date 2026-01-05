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
from collections import defaultdict, Counter
import math


class TermExtractor:
    """Извлечение терминов из контента"""

    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def extract_ngrams(self, text, n=2, min_freq=2):
        """
        Извлечь n-граммы (биграммы, триграммы) из текста

        Args:
            text: текст
            n: размер n-грамм
            min_freq: минимальная частота

        Returns:
            list: n-граммы
        """
        # Токенизация
        words = re.findall(r'\b\w+\b', text.lower())

        # Генерация n-грамм
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)

        # Подсчёт частоты
        ngram_freq = Counter(ngrams)

        # Фильтрация
        return [(ng, freq) for ng, freq in ngram_freq.most_common() if freq >= min_freq]

    def extract_multiword_terms(self):
        """
        Извлечь многословные термины из всех статей

        Returns:
            dict: термины с частотой
        """
        all_text = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Удалить frontmatter
                content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
                all_text.append(content)
            except:
                pass

        combined_text = '\n'.join(all_text)

        # Биграммы
        bigrams = self.extract_ngrams(combined_text, n=2, min_freq=3)

        # Триграммы
        trigrams = self.extract_ngrams(combined_text, n=3, min_freq=2)

        multiword_terms = {}
        for term, freq in bigrams + trigrams:
            multiword_terms[term] = freq

        return multiword_terms

    def calculate_tf_idf(self):
        """
        Вычислить TF-IDF для терминов

        Returns:
            dict: термины с TF-IDF scores
        """
        # Документы
        documents = []
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
                    documents.append(content)
            except:
                pass

        if not documents:
            return {}

        # TF
        term_doc_freq = defaultdict(lambda: defaultdict(int))

        for doc_id, doc in enumerate(documents):
            words = re.findall(r'\b\w+\b', doc.lower())
            word_freq = Counter(words)

            for word, freq in word_freq.items():
                term_doc_freq[word][doc_id] = freq

        # IDF
        num_docs = len(documents)
        idf = {}

        for term, doc_freqs in term_doc_freq.items():
            docs_with_term = len(doc_freqs)
            idf[term] = math.log(num_docs / (1 + docs_with_term))

        # TF-IDF
        tf_idf_scores = {}

        for term, doc_freqs in term_doc_freq.items():
            # Средний TF-IDF по всем документам
            scores = []
            for doc_id, tf in doc_freqs.items():
                scores.append(tf * idf[term])

            if scores:
                tf_idf_scores[term] = sum(scores) / len(scores)

        # Топ термины
        top_terms = sorted(tf_idf_scores.items(), key=lambda x: -x[1])[:100]

        return dict(top_terms)


class RelationshipMiner:
    """Извлечение семантических отношений"""

    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def mine_cooccurrence_relationships(self, window_size=10):
        """
        Найти связанные термины на основе co-occurrence

        Args:
            window_size: размер окна для совместного появления

        Returns:
            dict: термины и их связи
        """
        cooccurrence = defaultdict(lambda: Counter())

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

                words = re.findall(r'\b\w+\b', content.lower())

                # Скользящее окно
                for i in range(len(words)):
                    term = words[i]

                    # Окно вокруг термина
                    start = max(0, i - window_size)
                    end = min(len(words), i + window_size + 1)

                    for j in range(start, end):
                        if i != j:
                            cooccurrence[term][words[j]] += 1
            except:
                pass

        # Топ связи для каждого термина
        relationships = {}

        for term, related_counts in cooccurrence.items():
            # Топ-10 связанных
            top_related = related_counts.most_common(10)
            if top_related:
                relationships[term] = [r[0] for r in top_related]

        return relationships

    def detect_abbreviations(self, terms):
        """
        Обнаружить аббревиатуры

        Args:
            terms: список терминов

        Returns:
            dict: аббревиатура -> полная форма
        """
        abbreviations = {}

        for term in terms:
            # Проверить, является ли термин аббревиатурой (все заглавные)
            if term.isupper() and len(term) >= 2:
                # Найти потенциальные полные формы
                for full_term in terms:
                    if term.lower() != full_term.lower():
                        # Проверить, соответствует ли аббревиатура
                        words = full_term.split()
                        if len(words) >= len(term):
                            initials = ''.join([w[0].upper() for w in words if w])
                            if initials == term:
                                abbreviations[term] = full_term
                                break

        return abbreviations

    def find_compound_terms(self, terms):
        """
        Найти составные термины

        Args:
            terms: список терминов

        Returns:
            dict: составной термин -> компоненты
        """
        compounds = {}

        for term in terms:
            if ' ' in term:  # Составной термин
                words = term.split()
                if len(words) >= 2:
                    # Проверить, есть ли отдельные слова в списке терминов
                    components = [w for w in words if w in terms]
                    if components:
                        compounds[term] = components

        return compounds


class ThesaurusVisualizer:
    """Визуализация тезауруса"""

    def __init__(self, thesaurus):
        self.thesaurus = thesaurus

    def generate_html_visualization(self):
        """
        Создать HTML визуализацию тезауруса

        Returns:
            str: HTML
        """
        # Статистика
        total_terms = len(self.thesaurus)
        with_synonyms = sum(1 for t in self.thesaurus.values() if t.get('synonyms'))
        with_related = sum(1 for t in self.thesaurus.values() if t.get('related'))

        # Топ термины по количеству связей
        term_connections = []
        for term, data in self.thesaurus.items():
            connections = len(data.get('synonyms', [])) + len(data.get('related', [])) + len(data.get('broader', [])) + len(data.get('narrower', []))
            if connections > 0:
                term_connections.append((data.get('canonical', term), connections))

        top_terms = sorted(term_connections, key=lambda x: -x[1])[:20]

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔤 Тезаурус</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #666;
            margin-top: 10px;
        }}

        .section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}

        .section-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }}

        .term-cloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}

        .term-tag {{
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: calc(12px + var(--size) * 8px);
        }}

        .term-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}

        .term-item {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .term-name {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}

        .term-connections {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔤 Тезаурус</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_terms}</div>
                <div class="stat-label">Всего терминов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{with_synonyms}</div>
                <div class="stat-label">С синонимами</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{with_related}</div>
                <div class="stat-label">Со связями</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">☁️ Топ термины</div>
            <div class="term-cloud">
                {"".join(f'<span class="term-tag" style="--size: {min(connections/max(t[1] for t in top_terms), 1)}">{term} ({connections})</span>' for term, connections in top_terms[:15])}
            </div>
        </div>

        <div class="section">
            <div class="section-title">📋 Термины с наибольшими связями</div>
            <div class="term-list">
                {"".join(f'''
                <div class="term-item">
                    <div class="term-name">{term}</div>
                    <div class="term-connections">{connections} связей</div>
                </div>
                ''' for term, connections in top_terms[:20])}
            </div>
        </div>
    </div>
</body>
</html>"""

        return html


class ThesaurusValidator:
    """Валидация тезауруса"""

    def __init__(self, thesaurus):
        self.thesaurus = thesaurus

    def validate_consistency(self):
        """
        Проверить консистентность тезауруса

        Returns:
            dict: результаты валидации
        """
        issues = {
            'missing_reverse_relations': [],
            'circular_hierarchies': [],
            'orphaned_references': [],
            'duplicate_synonyms': []
        }

        # Проверка 1: обратные связи синонимов
        for term, data in self.thesaurus.items():
            for syn in data.get('synonyms', []):
                syn_lower = syn.lower()
                if syn_lower in self.thesaurus:
                    if term not in self.thesaurus[syn_lower].get('synonyms', []):
                        issues['missing_reverse_relations'].append((term, syn))

        # Проверка 2: циклические иерархии
        for term, data in self.thesaurus.items():
            broader = data.get('broader', [])
            for b in broader:
                b_lower = b.lower()
                if b_lower in self.thesaurus:
                    # Проверить, не указан ли текущий термин как broader для b
                    if term in self.thesaurus[b_lower].get('broader', []):
                        issues['circular_hierarchies'].append((term, b))

        # Проверка 3: orphaned references
        for term, data in self.thesaurus.items():
            all_refs = list(data.get('synonyms', [])) + list(data.get('related', [])) + list(data.get('broader', [])) + list(data.get('narrower', []))

            for ref in all_refs:
                ref_lower = ref.lower()
                if ref_lower not in self.thesaurus:
                    issues['orphaned_references'].append((term, ref))

        # Проверка 4: дубликаты синонимов
        for term, data in self.thesaurus.items():
            synonyms = list(data.get('synonyms', []))
            if len(synonyms) != len(set(s.lower() for s in synonyms)):
                issues['duplicate_synonyms'].append(term)

        return issues

    def calculate_quality_score(self):
        """
        Вычислить качество тезауруса

        Returns:
            dict: метрики качества
        """
        total_terms = len(self.thesaurus)

        if total_terms == 0:
            return {'quality_score': 0}

        # Метрики
        terms_with_synonyms = sum(1 for t in self.thesaurus.values() if t.get('synonyms'))
        terms_with_related = sum(1 for t in self.thesaurus.values() if t.get('related'))
        terms_with_hierarchy = sum(1 for t in self.thesaurus.values() if t.get('broader') or t.get('narrower'))

        # Score (0-100)
        coverage_score = (terms_with_synonyms / total_terms) * 40
        richness_score = (terms_with_related / total_terms) * 30
        structure_score = (terms_with_hierarchy / total_terms) * 30

        quality_score = coverage_score + richness_score + structure_score

        return {
            'quality_score': round(quality_score, 1),
            'total_terms': total_terms,
            'with_synonyms': terms_with_synonyms,
            'with_related': terms_with_related,
            'with_hierarchy': terms_with_hierarchy,
            'coverage_percent': round((terms_with_synonyms / total_terms) * 100, 1),
            'richness_percent': round((terms_with_related / total_terms) * 100, 1),
            'structure_percent': round((terms_with_hierarchy / total_terms) * 100, 1)
        }


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

    parser.add_argument('--extract-terms', action='store_true',
                       help='Извлечь термины из контента (TF-IDF, n-grams)')
    parser.add_argument('--mine-relations', action='store_true',
                       help='Найти связи через co-occurrence')
    parser.add_argument('--html', action='store_true',
                       help='Создать HTML визуализацию')
    parser.add_argument('--validate', action='store_true',
                       help='Валидация тезауруса')
    parser.add_argument('--quality', action='store_true',
                       help='Вычислить quality score')
    parser.add_argument('--all', action='store_true',
                       help='Запустить все анализы')

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

    elif args.extract_terms or args.mine_relations or args.html or args.validate or args.quality or args.all:
        # Загрузить существующий тезаурус если есть
        if builder.thesaurus_file.exists():
            with open(builder.thesaurus_file, 'r', encoding='utf-8') as f:
                thesaurus_json = json.load(f)

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

        # Extract terms
        if args.extract_terms or args.all:
            print("\n📊 Извлечение терминов из контента...")
            extractor = TermExtractor(root_dir)

            multiword = extractor.extract_multiword_terms()
            print(f"   Многословных терминов: {len(multiword)}")
            if multiword:
                top_multi = sorted(multiword.items(), key=lambda x: -x[1])[:10]
                for term, freq in top_multi:
                    print(f"      {term}: {freq}")

            tf_idf = extractor.calculate_tf_idf()
            print(f"\n   Топ термины по TF-IDF: {len(tf_idf)}")
            for term, score in list(tf_idf.items())[:10]:
                print(f"      {term}: {score:.3f}")

        # Mine relations
        if args.mine_relations or args.all:
            print("\n🔗 Извлечение связей...")
            miner = RelationshipMiner(root_dir)

            relations = miner.mine_cooccurrence_relationships()
            print(f"   Найдено терминов со связями: {len(relations)}")

        # Validate
        if args.validate or args.all:
            print("\n✅ Валидация тезауруса...")
            validator = ThesaurusValidator(builder.thesaurus)
            issues = validator.validate_consistency()

            print(f"   Отсутствуют обратные связи: {len(issues['missing_reverse_relations'])}")
            print(f"   Циклические иерархии: {len(issues['circular_hierarchies'])}")
            print(f"   Orphaned references: {len(issues['orphaned_references'])}")
            print(f"   Дубликаты синонимов: {len(issues['duplicate_synonyms'])}")

        # Quality
        if args.quality or args.all:
            print("\n🏆 Quality Score...")
            validator = ThesaurusValidator(builder.thesaurus)
            quality = validator.calculate_quality_score()

            print(f"   Quality Score: {quality['quality_score']}/100")
            print(f"   Терминов всего: {quality['total_terms']}")
            print(f"   С синонимами: {quality['with_synonyms']} ({quality['coverage_percent']}%)")
            print(f"   Со связями: {quality['with_related']} ({quality['richness_percent']}%)")
            print(f"   С иерархией: {quality['with_hierarchy']} ({quality['structure_percent']}%)")

        # HTML
        if args.html or args.all:
            print("\n🎨 Генерация HTML...")
            visualizer = ThesaurusVisualizer(builder.thesaurus)
            html = visualizer.generate_html_visualization()

            html_file = root_dir / "thesaurus.html"
            html_file.write_text(html, encoding='utf-8')
            print(f"   HTML: {html_file}")

    else:
        # Построить тезаурус
        builder.build()
        builder.save()
        builder.save_markdown()


if __name__ == "__main__":
    main()
