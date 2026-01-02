#!/usr/bin/env python3
"""
Knowledge Graph Builder - Продвинутый построитель графа знаний
Создаёт семантический граф с сущностями, отношениями и типами

Вдохновлено: DBpedia, Wikidata, Google Knowledge Graph
Форматы: RDF, JSON-LD, Neo4j Cypher
"""

from pathlib import Path
import yaml
import re
from collections import defaultdict
import json


class AdvancedKnowledgeGraphBuilder:
    """Продвинутый построитель графа знаний"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

        # Сущности с типами
        self.entities = defaultdict(lambda: {
            'type': 'Unknown',
            'mentions': [],
            'properties': {},
            'aliases': set()
        })

        # Отношения (тройки: subject-predicate-object)
        self.relations = []

        # Словарь типов сущностей
        self.entity_type_patterns = {
            'Technology': r'\b(Python|Docker|Kubernetes|LLM|API|Git|Linux|JavaScript|React)\b',
            'Concept': r'\*\*([А-ЯA-Z][а-яa-z]{3,30}?)\*\*',
            'Organization': r'\b(Google|Microsoft|Apple|Amazon|Facebook|Meta)\b',
            'Product': r'\b(ChatGPT|GPT-4|Claude|Gemini)\b',
            'Method': r'\b([А-Я][а-я]+(?:ация|ние|тор|ка))\b'  # Русские существительные
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

    def detect_entity_type(self, entity_name):
        """Определить тип сущности"""
        for entity_type, pattern in self.entity_type_patterns.items():
            if re.search(pattern, entity_name, re.IGNORECASE):
                return entity_type

        # Дефолтная логика по капитализации
        if entity_name[0].isupper():
            return 'Concept'

        return 'Unknown'

    def extract_entities(self, content, article_path, article_title):
        """Извлечь сущности из контента"""
        found_entities = []

        # 1. Выделенные термины (**термин**)
        bold_terms = re.findall(r'\*\*([А-ЯA-Z][^\*]{2,40}?)\*\*', content)

        for term in bold_terms:
            clean_term = term.strip()
            entity_type = self.detect_entity_type(clean_term)

            self.entities[clean_term]['type'] = entity_type
            self.entities[clean_term]['mentions'].append({
                'article': article_path,
                'article_title': article_title
            })

            found_entities.append(clean_term)

        # 2. Технологии (по паттернам)
        tech_pattern = self.entity_type_patterns['Technology']
        technologies = re.findall(tech_pattern, content)

        for tech in set(technologies):
            self.entities[tech]['type'] = 'Technology'
            if article_path not in [m['article'] for m in self.entities[tech]['mentions']]:
                self.entities[tech]['mentions'].append({
                    'article': article_path,
                    'article_title': article_title
                })

            found_entities.append(tech)

        # 3. Извлечь из заголовков
        headings = re.findall(r'^#{2,6}\s+(.+)$', content, re.MULTILINE)

        for heading in headings:
            clean_heading = re.sub(r'[#*`\[\]()]', '', heading).strip()

            if len(clean_heading) > 3 and clean_heading not in self.entities:
                entity_type = self.detect_entity_type(clean_heading)
                self.entities[clean_heading]['type'] = entity_type
                self.entities[clean_heading]['mentions'].append({
                    'article': article_path,
                    'article_title': article_title
                })

                found_entities.append(clean_heading)

        return found_entities

    def extract_relations(self, content, entities, article_path):
        """Извлечь отношения между сущностями"""
        # Паттерны отношений
        relation_patterns = [
            (r'(\w+)\s+является\s+(\w+)', 'is_a'),
            (r'(\w+)\s+часть\s+(\w+)', 'part_of'),
            (r'(\w+)\s+использует\s+(\w+)', 'uses'),
            (r'(\w+)\s+требует\s+(\w+)', 'requires'),
            (r'(\w+)\s+основан\s+на\s+(\w+)', 'based_on'),
            (r'(\w+)\s+→\s+(\w+)', 'leads_to')
        ]

        for pattern, relation_type in relation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)

            for subject, obj in matches:
                # Проверить, что оба - известные сущности
                if subject in entities and obj in entities:
                    self.relations.append({
                        'subject': subject,
                        'predicate': relation_type,
                        'object': obj,
                        'source': article_path
                    })

        # Анализ co-occurrence (сущности в одном предложении)
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            # Найти все сущности в предложении
            sentence_entities = [e for e in entities if e in sentence]

            # Создать отношения co-occurrence
            if len(sentence_entities) >= 2:
                for i, ent1 in enumerate(sentence_entities):
                    for ent2 in sentence_entities[i+1:]:
                        self.relations.append({
                            'subject': ent1,
                            'predicate': 'co_occurs_with',
                            'object': ent2,
                            'source': article_path
                        })

    def build_graph(self):
        """Построить граф знаний"""
        print("🕸️  Построение продвинутого графа знаний...\n")

        all_entities_by_article = {}

        # Первый проход - извлечь сущности
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            title = frontmatter.get('title', md_file.stem) if frontmatter else md_file.stem

            entities = self.extract_entities(content, article_path, title)
            all_entities_by_article[article_path] = entities

        # Второй проход - извлечь отношения
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            _, content = self.extract_frontmatter_and_content(md_file)
            if not content:
                continue

            article_path = str(md_file.relative_to(self.root_dir))
            entities = all_entities_by_article.get(article_path, [])

            self.extract_relations(content, entities, article_path)

        print(f"   Сущностей: {len(self.entities)}")
        print(f"   Отношений: {len(self.relations)}\n")

    def calculate_entity_importance(self):
        """Вычислить важность сущностей"""
        for entity_name, entity_data in self.entities.items():
            # Важность = количество упоминаний + количество отношений
            mentions_count = len(entity_data['mentions'])

            # Подсчитать отношения
            relations_count = sum(
                1 for r in self.relations
                if r['subject'] == entity_name or r['object'] == entity_name
            )

            entity_data['importance'] = mentions_count + relations_count * 2

    def generate_markdown_report(self):
        """Создать Markdown отчёт"""
        lines = []
        lines.append("# 🕸️ Граф знаний\n\n")
        lines.append("> Семантический граф с сущностями и отношениями\n\n")

        # Статистика
        entity_types = defaultdict(int)
        for entity_data in self.entities.values():
            entity_types[entity_data['type']] += 1

        relation_types = defaultdict(int)
        for rel in self.relations:
            relation_types[rel['predicate']] += 1

        lines.append("## Статистика\n\n")
        lines.append(f"- **Сущностей**: {len(self.entities)}\n")
        lines.append(f"- **Отношений**: {len(self.relations)}\n\n")

        lines.append("### По типам сущностей\n\n")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: -x[1]):
            lines.append(f"- **{entity_type}**: {count}\n")

        lines.append("\n### По типам отношений\n\n")
        for rel_type, count in sorted(relation_types.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"- **{rel_type}**: {count}\n")

        # Самые важные сущности
        self.calculate_entity_importance()

        lines.append("\n## Топ-20 самых важных сущностей\n\n")

        sorted_entities = sorted(
            self.entities.items(),
            key=lambda x: -x[1].get('importance', 0)
        )

        for entity_name, entity_data in sorted_entities[:20]:
            lines.append(f"### {entity_name}\n\n")
            lines.append(f"- **Тип**: {entity_data['type']}\n")
            lines.append(f"- **Важность**: {entity_data.get('importance', 0)}\n")
            lines.append(f"- **Упоминаний**: {len(entity_data['mentions'])}\n")

            if entity_data['mentions']:
                lines.append("\n**Встречается в:**\n")
                for mention in entity_data['mentions'][:5]:
                    lines.append(f"- [{mention['article_title']}]({mention['article']})\n")

                if len(entity_data['mentions']) > 5:
                    lines.append(f"\n...и ещё {len(entity_data['mentions']) - 5}\n")

            lines.append("\n")

        # Примеры отношений
        lines.append("\n## Примеры отношений\n\n")

        for rel in self.relations[:30]:
            lines.append(f"- **{rel['subject']}** `{rel['predicate']}` **{rel['object']}**\n")

        if len(self.relations) > 30:
            lines.append(f"\n*...и ещё {len(self.relations) - 30} отношений*\n")

        output_file = self.root_dir / "KNOWLEDGE_GRAPH.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown отчёт: {output_file}")

    def save_json(self):
        """Сохранить в JSON"""
        data = {
            'entities': {
                name: {
                    'type': entity_data['type'],
                    'mentions': entity_data['mentions'],
                    'importance': entity_data.get('importance', 0)
                }
                for name, entity_data in self.entities.items()
            },
            'relations': self.relations,
            'statistics': {
                'total_entities': len(self.entities),
                'total_relations': len(self.relations)
            }
        }

        output_file = self.root_dir / "knowledge_graph_advanced.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON граф: {output_file}")

    def export_rdf(self):
        """Экспорт в RDF Turtle format"""
        lines = []
        lines.append("@prefix kg: <http://example.org/kg#> .\n")
        lines.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
        lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n")

        # Сущности
        for entity_name, entity_data in self.entities.items():
            safe_name = re.sub(r'[^\w]', '_', entity_name)

            lines.append(f"kg:{safe_name}\n")
            lines.append(f"    rdf:type kg:{entity_data['type']} ;\n")
            lines.append(f"    rdfs:label \"{entity_name}\" ;\n")
            lines.append(f"    kg:importance {entity_data.get('importance', 0)} .\n\n")

        # Отношения
        for rel in self.relations:
            subj = re.sub(r'[^\w]', '_', rel['subject'])
            obj = re.sub(r'[^\w]', '_', rel['object'])
            pred = rel['predicate']

            lines.append(f"kg:{subj} kg:{pred} kg:{obj} .\n")

        output_file = self.root_dir / "knowledge_graph.ttl"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ RDF Turtle: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = AdvancedKnowledgeGraphBuilder(root_dir)
    builder.build_graph()
    builder.generate_markdown_report()
    builder.save_json()
    builder.export_rdf()


if __name__ == "__main__":
    main()
