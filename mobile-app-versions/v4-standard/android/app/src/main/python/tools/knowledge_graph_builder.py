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
from collections import defaultdict, Counter
import json
import argparse
from typing import Dict, List, Tuple, Set
import math


class EntityLinker:
    """Линковка и объединение похожих сущностей"""

    def __init__(self, entities: Dict):
        self.entities = entities

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Расстояние Левенштейна"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def find_similar_entities(self, threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """Найти похожие сущности (кандидаты на объединение)"""
        similar_pairs = []
        entity_names = list(self.entities.keys())

        for i, name1 in enumerate(entity_names):
            for name2 in entity_names[i+1:]:
                # Нормализовать
                norm1 = name1.lower().strip()
                norm2 = name2.lower().strip()

                if norm1 == norm2:
                    continue

                # Расчёт схожести
                distance = self.levenshtein_distance(norm1, norm2)
                max_len = max(len(norm1), len(norm2))
                similarity = 1 - (distance / max_len)

                if similarity >= threshold:
                    similar_pairs.append((name1, name2, similarity))

        return sorted(similar_pairs, key=lambda x: -x[2])

    def merge_entities(self, entity1: str, entity2: str, target_name: str = None):
        """Объединить две сущности"""
        if entity1 not in self.entities or entity2 not in self.entities:
            return

        target = target_name or entity1

        # Объединить упоминания
        self.entities[target]['mentions'].extend(self.entities[entity2]['mentions'])

        # Объединить алиасы
        self.entities[target]['aliases'].add(entity2)
        self.entities[target]['aliases'].update(self.entities[entity2].get('aliases', set()))

        # Удалить вторую сущность
        del self.entities[entity2]


class GraphAnalyzer:
    """Анализ структуры графа знаний"""

    def __init__(self, entities: Dict, relations: List[Dict]):
        self.entities = entities
        self.relations = relations

        # Построить adjacency list
        self.adjacency = defaultdict(set)
        for rel in relations:
            self.adjacency[rel['subject']].add(rel['object'])

    def calculate_degree_centrality(self) -> Dict[str, int]:
        """Вычислить степень вершин (degree centrality)"""
        degree = Counter()

        for rel in self.relations:
            degree[rel['subject']] += 1  # Исходящая степень
            degree[rel['object']] += 1   # Входящая степень

        return dict(degree)

    def calculate_betweenness_centrality_approx(self) -> Dict[str, float]:
        """Приблизительная betweenness centrality (упрощённая версия)"""
        # Подсчитать, сколько раз сущность встречается в отношениях
        betweenness = Counter()

        # Простая эвристика: сущности с большим количеством связей = высокий betweenness
        for entity in self.entities:
            incoming = sum(1 for r in self.relations if r['object'] == entity)
            outgoing = sum(1 for r in self.relations if r['subject'] == entity)

            # Betweenness approximation
            betweenness[entity] = incoming * outgoing

        # Нормализация
        max_val = max(betweenness.values()) if betweenness else 1
        return {k: v / max_val for k, v in betweenness.items()}

    def find_hubs(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Найти хабы (сущности с наибольшим количеством связей)"""
        degree = self.calculate_degree_centrality()
        return sorted(degree.items(), key=lambda x: -x[1])[:top_n]

    def calculate_clustering_coefficient(self, entity: str) -> float:
        """Коэффициент кластеризации для сущности"""
        neighbors = list(self.adjacency.get(entity, set()))

        if len(neighbors) < 2:
            return 0.0

        # Подсчитать связи между соседями
        neighbor_connections = 0
        for i, n1 in enumerate(neighbors):
            for n2 in neighbors[i+1:]:
                if n2 in self.adjacency.get(n1, set()):
                    neighbor_connections += 1

        # Максимально возможное количество связей
        max_connections = len(neighbors) * (len(neighbors) - 1) / 2

        return neighbor_connections / max_connections if max_connections > 0 else 0.0

    def detect_communities_simple(self) -> Dict[str, Set[str]]:
        """Простое обнаружение сообществ (по типам сущностей)"""
        communities = defaultdict(set)

        for entity_name, entity_data in self.entities.items():
            entity_type = entity_data.get('type', 'Unknown')
            communities[entity_type].add(entity_name)

        return dict(communities)


class Neo4jExporter:
    """Экспорт в Neo4j Cypher queries"""

    def __init__(self, entities: Dict, relations: List[Dict]):
        self.entities = entities
        self.relations = relations

    def generate_cypher_queries(self) -> List[str]:
        """Сгенерировать Cypher запросы для Neo4j"""
        queries = []

        # CREATE запросы для сущностей
        queries.append("// Создание сущностей")
        queries.append("")

        for entity_name, entity_data in self.entities.items():
            safe_name = re.sub(r'[^\w]', '_', entity_name)
            entity_type = entity_data.get('type', 'Unknown')
            importance = entity_data.get('importance', 0)

            query = f"CREATE (n_{safe_name}:{entity_type} {{"
            query += f"name: \"{entity_name}\", "
            query += f"importance: {importance}"
            query += "})"

            queries.append(query)

        queries.append("")
        queries.append("// Создание отношений")
        queries.append("")

        # CREATE запросы для отношений
        for i, rel in enumerate(self.relations):
            subj_safe = re.sub(r'[^\w]', '_', rel['subject'])
            obj_safe = re.sub(r'[^\w]', '_', rel['object'])
            pred = rel['predicate'].upper()

            query = f"MATCH (a {{name: \"{rel['subject']}\"}}), (b {{name: \"{rel['object']}\"}})"
            query2 = f"CREATE (a)-[:{pred}]->(b)"

            queries.append(query)
            queries.append(query2)

            if i > 50:  # Ограничить для больших графов
                queries.append(f"\n// ... и ещё {len(self.relations) - i} отношений\n")
                break

        return queries

    def save_cypher_file(self, output_path: Path):
        """Сохранить Cypher запросы в файл"""
        queries = self.generate_cypher_queries()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("// Neo4j Cypher Import Script\n")
            f.write("// Импорт графа знаний в Neo4j\n\n")
            f.write('\n'.join(queries))

        print(f"✅ Neo4j Cypher: {output_path}")


class SPARQLQueryGenerator:
    """Генератор SPARQL запросов"""

    @staticmethod
    def generate_sample_queries() -> List[Tuple[str, str]]:
        """Сгенерировать примеры SPARQL запросов"""
        queries = []

        # 1. Все сущности определённого типа
        queries.append((
            "Все технологии",
            """
PREFIX kg: <http://example.org/kg#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?entity ?label
WHERE {
    ?entity rdf:type kg:Technology .
    ?entity rdfs:label ?label .
}
ORDER BY ?label
            """.strip()
        ))

        # 2. Топ сущностей по важности
        queries.append((
            "Топ-10 по важности",
            """
PREFIX kg: <http://example.org/kg#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entity ?label ?importance
WHERE {
    ?entity rdfs:label ?label .
    ?entity kg:importance ?importance .
}
ORDER BY DESC(?importance)
LIMIT 10
            """.strip()
        ))

        # 3. Отношения между сущностями
        queries.append((
            "Все отношения 'uses'",
            """
PREFIX kg: <http://example.org/kg#>

SELECT ?subject ?object
WHERE {
    ?subject kg:uses ?object .
}
            """.strip()
        ))

        return queries

    @staticmethod
    def save_sparql_queries(output_path: Path):
        """Сохранить примеры SPARQL запросов"""
        queries = SPARQLQueryGenerator.generate_sample_queries()

        lines = []
        lines.append("# SPARQL Query Examples\n\n")
        lines.append("Примеры SPARQL запросов для графа знаний.\n\n")

        for title, query in queries:
            lines.append(f"## {title}\n\n")
            lines.append("```sparql\n")
            lines.append(query)
            lines.append("\n```\n\n")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ SPARQL примеры: {output_path}")


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

        # Анализаторы
        self.entity_linker = None
        self.graph_analyzer = None
        self.neo4j_exporter = None

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

        # Инициализировать анализаторы
        self.entity_linker = EntityLinker(self.entities)
        self.graph_analyzer = GraphAnalyzer(self.entities, self.relations)
        self.neo4j_exporter = Neo4jExporter(self.entities, self.relations)

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

    def run_entity_linking(self, threshold: float = 0.8):
        """Провести линковку похожих сущностей"""
        if not self.entity_linker:
            print("⚠️  Сначала постройте граф (build_graph)")
            return

        print(f"\n🔗 Линковка похожих сущностей (порог: {threshold})\n")

        similar = self.entity_linker.find_similar_entities(threshold)

        if not similar:
            print("   Похожих сущностей не найдено")
            return

        print(f"Найдено {len(similar)} пар похожих сущностей:")
        for entity1, entity2, similarity in similar[:10]:
            print(f"   • {entity1} ≈ {entity2} ({similarity:.2%})")

        if len(similar) > 10:
            print(f"   ... и ещё {len(similar) - 10}")

    def run_graph_analysis(self):
        """Провести анализ структуры графа"""
        if not self.graph_analyzer:
            print("⚠️  Сначала постройте граф (build_graph)")
            return

        print("\n📊 Анализ структуры графа\n")

        # Хабы
        hubs = self.graph_analyzer.find_hubs(top_n=10)
        if hubs:
            print("Топ-10 хабов (по степени связности):")
            for entity, degree in hubs:
                print(f"   • {entity}: {degree} связей")

        # Сообщества
        communities = self.graph_analyzer.detect_communities_simple()
        print(f"\nСообщества (по типам):")
        for comm_type, members in sorted(communities.items(), key=lambda x: -len(x[1])):
            print(f"   {comm_type}: {len(members)} сущностей")

        # Centrality (топ-5)
        betweenness = self.graph_analyzer.calculate_betweenness_centrality_approx()
        top_betweenness = sorted(betweenness.items(), key=lambda x: -x[1])[:5]
        if top_betweenness:
            print(f"\nТоп-5 по betweenness centrality:")
            for entity, score in top_betweenness:
                if score > 0:
                    print(f"   • {entity}: {score:.2f}")

    def export_neo4j(self):
        """Экспортировать в Neo4j Cypher"""
        if not self.neo4j_exporter:
            print("⚠️  Сначала постройте граф (build_graph)")
            return

        output_path = self.root_dir / "knowledge_graph_neo4j.cypher"
        self.neo4j_exporter.save_cypher_file(output_path)

    def export_sparql_queries(self):
        """Экспортировать примеры SPARQL запросов"""
        output_path = self.root_dir / "SPARQL_QUERIES.md"
        SPARQLQueryGenerator.save_sparql_queries(output_path)

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
    parser = argparse.ArgumentParser(
        description='🕸️ Knowledge Graph Builder - Построитель графа знаний',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                    # Построить граф и создать все отчёты
  %(prog)s --analyze          # Анализ структуры графа
  %(prog)s --link             # Поиск похожих сущностей
  %(prog)s --neo4j            # Экспорт в Neo4j Cypher
  %(prog)s --sparql           # Генерация SPARQL запросов
  %(prog)s --all              # Всё: граф + анализы + экспорты
        """
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Провести анализ структуры графа (хабы, centrality, сообщества)'
    )

    parser.add_argument(
        '--link',
        action='store_true',
        help='Провести линковку похожих сущностей'
    )

    parser.add_argument(
        '--link-threshold',
        type=float,
        default=0.8,
        metavar='THRESHOLD',
        help='Порог схожести для линковки (0.0-1.0, по умолчанию: 0.8)'
    )

    parser.add_argument(
        '--neo4j',
        action='store_true',
        help='Экспортировать в Neo4j Cypher формат'
    )

    parser.add_argument(
        '--sparql',
        action='store_true',
        help='Сгенерировать примеры SPARQL запросов'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Выполнить все анализы и экспорты'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Не создавать markdown отчёт'
    )

    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Не создавать JSON файл'
    )

    parser.add_argument(
        '--no-rdf',
        action='store_true',
        help='Не создавать RDF Turtle файл'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = AdvancedKnowledgeGraphBuilder(root_dir)

    # Построить граф
    builder.build_graph()

    # Режим --all
    if args.all:
        builder.run_graph_analysis()
        builder.run_entity_linking(args.link_threshold)
        if not args.no_report:
            builder.generate_markdown_report()
        if not args.no_json:
            builder.save_json()
        if not args.no_rdf:
            builder.export_rdf()
        builder.export_neo4j()
        builder.export_sparql_queries()
        return

    # Отдельные анализы
    if args.analyze:
        builder.run_graph_analysis()

    if args.link:
        builder.run_entity_linking(args.link_threshold)

    # Экспорты
    if args.neo4j:
        builder.export_neo4j()

    if args.sparql:
        builder.export_sparql_queries()

    # Действия по умолчанию (если не указаны специфичные флаги)
    if not any([args.analyze, args.link, args.neo4j, args.sparql]):
        if not args.no_report:
            builder.generate_markdown_report()
        if not args.no_json:
            builder.save_json()
        if not args.no_rdf:
            builder.export_rdf()


if __name__ == "__main__":
    main()
