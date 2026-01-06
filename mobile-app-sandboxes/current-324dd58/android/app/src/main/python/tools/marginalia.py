#!/usr/bin/env python3
"""
Marginalia - Заметки на полях
Вдохновлено: Средневековые рукописи с маргиналиями

Позволяет добавлять комментарии, заметки и аннотации к статьям,
как монахи делали на полях манускриптов.
"""

from pathlib import Path
import yaml
import re
import json
from datetime import datetime
import argparse
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter


class AnnotationExtractor:
    """
    Извлечение аннотаций из текста markdown файлов
    Поиск inline комментариев, highlights, TODO, FIXME и т.д.
    """

    def __init__(self):
        # Паттерны для различных типов аннотаций
        self.patterns = {
            'html_comment': re.compile(r'<!--\s*(.*?)\s*-->', re.DOTALL),
            'todo': re.compile(r'<!--?\s*TODO:?\s*(.*?)(?:-->)?', re.IGNORECASE),
            'fixme': re.compile(r'<!--?\s*FIXME:?\s*(.*?)(?:-->)?', re.IGNORECASE),
            'note': re.compile(r'<!--?\s*NOTE:?\s*(.*?)(?:-->)?', re.IGNORECASE),
            'warning': re.compile(r'<!--?\s*WARNING:?\s*(.*?)(?:-->)?', re.IGNORECASE),
            'highlight': re.compile(r'==([^=]+)=='),  # ==highlighted text==
            'question': re.compile(r'<!--?\s*\?:?\s*(.*?)(?:-->)?', re.IGNORECASE),
        }

    def extract_from_text(self, text: str, file_path: str = None) -> List[Dict]:
        """
        Извлечь все аннотации из текста

        Returns:
            List of annotations with type, text, line_number, context
        """
        annotations = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            for ann_type, pattern in self.patterns.items():
                matches = pattern.finditer(line)

                for match in matches:
                    annotation = {
                        'type': ann_type,
                        'text': match.group(1 if match.lastindex else 0).strip(),
                        'line': line_num,
                        'context': line.strip(),
                        'file': file_path or 'unknown'
                    }

                    annotations.append(annotation)

        return annotations

    def extract_from_file(self, file_path: Path) -> List[Dict]:
        """Извлечь аннотации из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            return self.extract_from_text(text, str(file_path))

        except Exception as e:
            return []

    def scan_directory(self, directory: Path, pattern: str = "**/*.md") -> Dict[str, List[Dict]]:
        """
        Сканировать директорию и извлечь все аннотации

        Returns:
            {file_path: [annotations]}
        """
        results = {}

        for file_path in directory.glob(pattern):
            if file_path.is_file():
                annotations = self.extract_from_file(file_path)

                if annotations:
                    results[str(file_path)] = annotations

        return results

    def get_statistics(self, annotations_by_file: Dict[str, List[Dict]]) -> Dict:
        """Получить статистику по аннотациям"""
        total = sum(len(anns) for anns in annotations_by_file.values())

        by_type = Counter()
        by_file = {}

        for file_path, annotations in annotations_by_file.items():
            by_file[file_path] = len(annotations)

            for ann in annotations:
                by_type[ann['type']] += 1

        return {
            'total': total,
            'files_with_annotations': len(annotations_by_file),
            'by_type': dict(by_type),
            'by_file': by_file
        }


class CrossReferenceBuilder:
    """
    Построение сети cross-references между заметками
    Анализ связей и зависимостей
    """

    def __init__(self, notes_db: Dict):
        self.notes = notes_db
        self.references = defaultdict(list)  # note_id -> [referenced_note_ids]
        self.backlinks = defaultdict(list)   # note_id -> [notes that reference this]

    def extract_references(self) -> Dict:
        """
        Извлечь все cross-references из заметок

        Паттерны:
        - #123 - ссылка на заметку по ID
        - @article_name - ссылка на другую статью
        - [[term]] - ссылка на концепт/термин
        """
        ref_patterns = {
            'note_id': re.compile(r'#(\d+)'),
            'article': re.compile(r'@([\w/.-]+)'),
            'concept': re.compile(r'\[\[([^\]]+)\]\]')
        }

        for article_path, notes in self.notes.items():
            for note in notes:
                note_key = f"{article_path}#{note['id']}"
                refs = []

                # Извлечь все типы референсов
                for ref_type, pattern in ref_patterns.items():
                    matches = pattern.findall(note['text'])

                    for match in matches:
                        refs.append({
                            'type': ref_type,
                            'target': match
                        })

                if refs:
                    self.references[note_key] = refs

                    # Построить backlinks
                    for ref in refs:
                        if ref['type'] == 'note_id':
                            # Найти целевую заметку
                            target_key = f"{article_path}#{ref['target']}"
                            self.backlinks[target_key].append(note_key)

        return {
            'references': dict(self.references),
            'backlinks': dict(self.backlinks)
        }

    def build_reference_graph(self) -> Dict:
        """
        Построить граф референсов

        Returns:
            {
                'nodes': [note_keys],
                'edges': [(from, to)],
                'clusters': [connected_components]
            }
        """
        self.extract_references()

        # Nodes
        nodes = set()
        for note_key in self.references.keys():
            nodes.add(note_key)
        for note_key in self.backlinks.keys():
            nodes.add(note_key)

        # Edges
        edges = []
        for from_note, refs in self.references.items():
            for ref in refs:
                if ref['type'] == 'note_id':
                    # Определить article_path из from_note
                    article_path = '#'.join(from_note.split('#')[:-1])
                    to_note = f"{article_path}#{ref['target']}"
                    edges.append((from_note, to_note))

        # Find connected components (простой DFS)
        visited = set()
        clusters = []

        def dfs(node, cluster):
            visited.add(node)
            cluster.add(node)

            # Исходящие
            for ref in self.references.get(node, []):
                if ref['type'] == 'note_id':
                    article_path = '#'.join(node.split('#')[:-1])
                    target = f"{article_path}#{ref['target']}"
                    if target not in visited:
                        dfs(target, cluster)

            # Входящие
            for backlink in self.backlinks.get(node, []):
                if backlink not in visited:
                    dfs(backlink, cluster)

        for node in nodes:
            if node not in visited:
                cluster = set()
                dfs(node, cluster)
                if cluster:
                    clusters.append(list(cluster))

        return {
            'nodes': list(nodes),
            'edges': edges,
            'clusters': clusters,
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'total_clusters': len(clusters)
        }

    def find_orphaned_notes(self) -> List[str]:
        """Найти изолированные заметки (без референсов)"""
        graph = self.build_reference_graph()
        all_notes = set()

        for article_path, notes in self.notes.items():
            for note in notes:
                all_notes.add(f"{article_path}#{note['id']}")

        orphaned = all_notes - set(graph['nodes'])

        return list(orphaned)


class ContextAnalyzer:
    """
    Анализ контекста аннотаций
    Определение тематики, sentiment, важности
    """

    def __init__(self):
        # Ключевые слова для определения тематики
        self.topic_keywords = {
            'technical': ['algorithm', 'implementation', 'code', 'function', 'class', 'API', 'database'],
            'conceptual': ['theory', 'concept', 'principle', 'philosophy', 'idea', 'paradigm'],
            'practical': ['example', 'tutorial', 'guide', 'howto', 'demo', 'practice'],
            'research': ['paper', 'study', 'research', 'analysis', 'experiment', 'findings'],
            'reference': ['see', 'related', 'link', 'source', 'citation', 'reference']
        }

        # Sentiment keywords
        self.sentiment_keywords = {
            'positive': ['good', 'excellent', 'useful', 'helpful', 'important', 'great', 'best'],
            'negative': ['bad', 'wrong', 'error', 'issue', 'problem', 'bug', 'broken'],
            'neutral': ['note', 'remark', 'comment', 'mention', 'see', 'check']
        }

    def analyze_note(self, note: Dict) -> Dict:
        """
        Анализировать одну заметку

        Returns:
            {
                'topics': [detected_topics],
                'sentiment': 'positive'/'negative'/'neutral',
                'importance': 0-10,
                'keywords': [extracted_keywords]
            }
        """
        text = note['text'].lower()

        # Определить темы
        topics = []
        for topic, keywords in self.topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)

        # Определить sentiment
        sentiment_scores = {}
        for sentiment, keywords in self.sentiment_keywords.items():
            sentiment_scores[sentiment] = sum(1 for kw in keywords if kw in text)

        sentiment = max(sentiment_scores.items(), key=lambda x: x[1])[0] if any(sentiment_scores.values()) else 'neutral'

        # Определить важность
        importance = 5  # baseline

        # Факторы важности
        if note['type'] in ['warning', 'fixme']:
            importance += 3
        elif note['type'] in ['todo', 'question']:
            importance += 2
        elif note['type'] in ['idea']:
            importance += 1

        if len(text) > 100:
            importance += 1  # длинная заметка = важная

        if any(marker in text for marker in ['important', 'critical', 'urgent', 'must']):
            importance += 2

        importance = min(10, importance)  # cap at 10

        # Извлечь ключевые слова (простой подход)
        words = re.findall(r'\b\w+\b', text)
        word_freq = Counter(w for w in words if len(w) > 4)  # слова длиннее 4 символов
        keywords = [word for word, count in word_freq.most_common(5)]

        return {
            'topics': topics,
            'sentiment': sentiment,
            'importance': importance,
            'keywords': keywords
        }

    def analyze_all_notes(self, notes_db: Dict) -> Dict:
        """Анализировать все заметки в базе"""
        analysis = {
            'by_article': {},
            'overall': {
                'topics': Counter(),
                'sentiment': Counter(),
                'avg_importance': 0,
                'all_keywords': Counter()
            }
        }

        total_importance = 0
        total_notes = 0

        for article_path, notes in notes_db.items():
            article_analysis = []

            for note in notes:
                note_analysis = self.analyze_note(note)
                article_analysis.append({
                    'note_id': note['id'],
                    **note_analysis
                })

                # Aggregate
                for topic in note_analysis['topics']:
                    analysis['overall']['topics'][topic] += 1

                analysis['overall']['sentiment'][note_analysis['sentiment']] += 1
                total_importance += note_analysis['importance']
                total_notes += 1

                for keyword in note_analysis['keywords']:
                    analysis['overall']['all_keywords'][keyword] += 1

            analysis['by_article'][article_path] = article_analysis

        if total_notes > 0:
            analysis['overall']['avg_importance'] = total_importance / total_notes

        # Convert Counters to dicts
        analysis['overall']['topics'] = dict(analysis['overall']['topics'])
        analysis['overall']['sentiment'] = dict(analysis['overall']['sentiment'])
        analysis['overall']['top_keywords'] = dict(analysis['overall']['all_keywords'].most_common(20))

        return analysis


class VisualizationGenerator:
    """
    Генератор визуализаций для маргиналий
    HTML с интерактивными элементами
    """

    def __init__(self, notes_db: Dict):
        self.notes = notes_db

    def generate_html_overview(self, output_file: Path, include_analysis: bool = True):
        """Генерировать HTML overview всех маргиналий"""

        # Статистика
        total_notes = sum(len(notes) for notes in self.notes.values())
        total_articles = len(self.notes)

        unresolved_count = 0
        for notes in self.notes.values():
            unresolved_count += sum(1 for note in notes if not note.get('resolved', False))

        # Type distribution
        type_counts = Counter()
        for notes in self.notes.values():
            for note in notes:
                type_counts[note['type']] += 1

        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marginalia Overview</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
        }
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .article-section {
            margin-bottom: 30px;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 20px;
            background: #f8f9fa;
        }
        .article-title {
            color: #333;
            font-size: 1.2em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .note-card {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }
        .note-card.comment { border-left-color: #667eea; }
        .note-card.warning { border-left-color: #ffc107; }
        .note-card.idea { border-left-color: #28a745; }
        .note-card.question { border-left-color: #17a2b8; }
        .note-card.todo { border-left-color: #ff5722; }
        .note-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.85em;
            color: #666;
        }
        .note-text {
            color: #333;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: bold;
        }
        .badge.comment { background: #667eea; color: white; }
        .badge.warning { background: #ffc107; color: #333; }
        .badge.idea { background: #28a745; color: white; }
        .badge.question { background: #17a2b8; color: white; }
        .badge.todo { background: #ff5722; color: white; }
        .resolved {
            opacity: 0.6;
        }
        .chart {
            margin: 20px 0;
        }
        .chart-bar {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .chart-label {
            width: 120px;
            font-size: 0.9em;
        }
        .chart-bar-fill {
            height: 24px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
            color: white;
            padding: 0 10px;
            font-size: 0.85em;
            display: flex;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Marginalia Overview</h1>
        <p class="subtitle">Заметки на полях базы знаний</p>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Notes</h3>
                <div class="value">""" + str(total_notes) + """</div>
            </div>
            <div class="stat-card">
                <h3>Articles</h3>
                <div class="value">""" + str(total_articles) + """</div>
            </div>
            <div class="stat-card">
                <h3>Unresolved</h3>
                <div class="value">""" + str(unresolved_count) + """</div>
            </div>
            <div class="stat-card">
                <h3>Avg per Article</h3>
                <div class="value">""" + f"{total_notes/total_articles:.1f}" if total_articles > 0 else "0" + """</div>
            </div>
        </div>

        <h2 style="margin-bottom: 20px;">Distribution by Type</h2>
        <div class="chart">
"""

        max_count = max(type_counts.values()) if type_counts else 1

        for note_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            width_pct = (count / max_count) * 100

            html += f"""            <div class="chart-bar">
                <div class="chart-label">{note_type}</div>
                <div class="chart-bar-fill" style="width: {width_pct}%;">{count}</div>
            </div>
"""

        html += """        </div>

        <h2 style="margin: 40px 0 20px;">Notes by Article</h2>
"""

        # Сортировать статьи по количеству заметок
        sorted_articles = sorted(self.notes.items(), key=lambda x: -len(x[1]))

        for article_path, notes in sorted_articles[:10]:  # Top 10
            html += f"""        <div class="article-section">
            <div class="article-title">{article_path} ({len(notes)} notes)</div>
"""

            for note in notes[:5]:  # Show first 5 notes
                resolved_class = "resolved" if note.get('resolved') else ""

                html += f"""            <div class="note-card {note['type']} {resolved_class}">
                <div class="note-header">
                    <span>
                        <span class="badge {note['type']}">{note['type']}</span>
                        #{note['id']} @ {note['position']}
                    </span>
                    <span>{note['author']} · {note['date'][:10]}</span>
                </div>
                <div class="note-text">{note['text'][:150]}{'...' if len(note['text']) > 150 else ''}</div>
            </div>
"""

            html += """        </div>
"""

        html += """    </div>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)


class MarginaliaManager:
    """
    Менеджер маргиналий - заметок на полях статей
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.marginalia_db = self.root_dir / ".marginalia" / "notes.json"

        # Создать директорию для хранения
        self.marginalia_db.parent.mkdir(exist_ok=True)

        # Загрузить существующие маргиналии
        self.notes = self.load_notes()

    def load_notes(self):
        """Загрузить все маргиналии"""
        if self.marginalia_db.exists():
            with open(self.marginalia_db, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_notes(self):
        """Сохранить маргиналии"""
        with open(self.marginalia_db, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def add_note(self, article_file, note_text, position=None, note_type="comment", author="User"):
        """
        Добавить заметку к статье

        position может быть:
        - "line:42" - конкретная строка
        - "section:Introduction" - секция
        - "paragraph:3" - параграф
        - None - общая заметка к статье
        """
        # Нормализовать путь
        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path not in self.notes:
            self.notes[article_path] = []

        note = {
            'id': len(self.notes[article_path]) + 1,
            'text': note_text,
            'position': position or "general",
            'type': note_type,  # comment, warning, idea, question, cross-reference
            'author': author,
            'date': datetime.now().isoformat(),
            'resolved': False
        }

        self.notes[article_path].append(note)
        self.save_notes()

        return note

    def get_notes(self, article_file):
        """Получить все заметки для статьи"""
        article_path = str(Path(article_file).relative_to(self.root_dir))
        return self.notes.get(article_path, [])

    def update_note(self, article_file, note_id, **updates):
        """Обновить заметку"""
        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path not in self.notes:
            return None

        for note in self.notes[article_path]:
            if note['id'] == note_id:
                note.update(updates)
                note['modified'] = datetime.now().isoformat()
                self.save_notes()
                return note

        return None

    def delete_note(self, article_file, note_id):
        """Удалить заметку"""
        article_path = str(Path(article_file).relative_to(self.root_dir))

        if article_path not in self.notes:
            return False

        self.notes[article_path] = [
            note for note in self.notes[article_path]
            if note['id'] != note_id
        ]

        self.save_notes()
        return True

    def mark_resolved(self, article_file, note_id):
        """Отметить заметку как разрешённую"""
        return self.update_note(article_file, note_id, resolved=True)

    def get_all_notes_by_type(self, note_type=None):
        """Получить все заметки определённого типа"""
        all_notes = []

        for article_path, notes in self.notes.items():
            for note in notes:
                if note_type is None or note['type'] == note_type:
                    all_notes.append({
                        'article': article_path,
                        **note
                    })

        return all_notes

    def get_unresolved_notes(self):
        """Получить все неразрешённые заметки"""
        unresolved = []

        for article_path, notes in self.notes.items():
            for note in notes:
                if not note.get('resolved', False):
                    unresolved.append({
                        'article': article_path,
                        **note
                    })

        return unresolved

    def export_to_markdown(self, article_file, output_file=None):
        """Экспортировать маргиналии статьи в markdown"""
        notes = self.get_notes(article_file)

        if not notes:
            return None

        lines = []
        lines.append(f"# 📝 Маргиналии: {Path(article_file).name}\n\n")
        lines.append(f"> Заметки на полях для статьи `{article_file}`\n\n")

        # Группировать по типу
        by_type = {}
        for note in notes:
            note_type = note['type']
            if note_type not in by_type:
                by_type[note_type] = []
            by_type[note_type].append(note)

        # Иконки для типов
        type_icons = {
            'comment': '💬',
            'warning': '⚠️',
            'idea': '💡',
            'question': '❓',
            'cross-reference': '🔗',
            'todo': '✅'
        }

        for note_type, type_notes in sorted(by_type.items()):
            icon = type_icons.get(note_type, '📌')
            lines.append(f"## {icon} {note_type.title()}\n\n")

            for note in type_notes:
                status = "✓" if note.get('resolved') else "○"
                lines.append(f"### {status} Заметка #{note['id']}\n\n")
                lines.append(f"**Позиция**: {note['position']}  \n")
                lines.append(f"**Автор**: {note['author']}  \n")
                lines.append(f"**Дата**: {note['date'][:10]}  \n")
                if note.get('resolved'):
                    lines.append(f"**Статус**: Разрешено ✓  \n")
                lines.append(f"\n{note['text']}\n\n")
                lines.append("---\n\n")

        content = ''.join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    def generate_report(self):
        """Создать общий отчёт по всем маргиналиям"""
        lines = []
        lines.append("# 📝 Отчёт по маргиналиям\n\n")

        total_notes = sum(len(notes) for notes in self.notes.values())
        total_articles = len(self.notes)
        unresolved = len(self.get_unresolved_notes())

        lines.append("## Статистика\n\n")
        lines.append(f"- **Всего заметок**: {total_notes}\n")
        lines.append(f"- **Статей с заметками**: {total_articles}\n")
        lines.append(f"- **Неразрешённых заметок**: {unresolved}\n\n")

        # По типам
        by_type = {}
        for notes in self.notes.values():
            for note in notes:
                note_type = note['type']
                by_type[note_type] = by_type.get(note_type, 0) + 1

        lines.append("## По типам\n\n")
        for note_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"- **{note_type}**: {count}\n")

        lines.append("\n## Неразрешённые заметки\n\n")
        unresolved_notes = self.get_unresolved_notes()

        if unresolved_notes:
            for note in unresolved_notes[:20]:
                lines.append(f"### {note['article']}\n\n")
                lines.append(f"- **ID**: #{note['id']}\n")
                lines.append(f"- **Тип**: {note['type']}\n")
                lines.append(f"- **Позиция**: {note['position']}\n")
                lines.append(f"- **Текст**: {note['text'][:100]}...\n\n")
        else:
            lines.append("Все заметки разрешены! 🎉\n\n")

        # Топ статей с наибольшим количеством заметок
        lines.append("\n## Статьи с наибольшим количеством заметок\n\n")

        article_counts = [(article, len(notes)) for article, notes in self.notes.items()]
        article_counts.sort(key=lambda x: -x[1])

        for article, count in article_counts[:10]:
            lines.append(f"- **{article}**: {count} заметок\n")

        return ''.join(lines)

    def print_notes(self, article_file=None):
        """Вывести заметки в консоль"""
        if article_file:
            notes = self.get_notes(article_file)
            print(f"\n📝 Маргиналии для {article_file}:\n")

            if not notes:
                print("   Заметок нет\n")
                return

            for note in notes:
                status = "✓" if note.get('resolved') else "○"
                print(f"{status} #{note['id']} [{note['type']}] @ {note['position']}")
                print(f"   {note['text']}")
                print(f"   — {note['author']}, {note['date'][:10]}\n")
        else:
            # Вывести статистику по всем заметкам
            total = sum(len(notes) for notes in self.notes.values())
            unresolved = len(self.get_unresolved_notes())

            print(f"\n📝 Всего маргиналий: {total}")
            print(f"   Неразрешённых: {unresolved}")
            print(f"   Статей с заметками: {len(self.notes)}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Marginalia - Управление заметками на полях статей'
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # add - добавить заметку
    add_parser = subparsers.add_parser('add', help='Добавить заметку')
    add_parser.add_argument('article', help='Путь к статье')
    add_parser.add_argument('text', help='Текст заметки')
    add_parser.add_argument('-p', '--position', help='Позиция (line:N, section:Name)')
    add_parser.add_argument('-t', '--type', default='comment',
                           choices=['comment', 'warning', 'idea', 'question', 'cross-reference', 'todo'],
                           help='Тип заметки')
    add_parser.add_argument('-a', '--author', default='User', help='Автор')

    # list - показать заметки
    list_parser = subparsers.add_parser('list', help='Показать заметки')
    list_parser.add_argument('article', nargs='?', help='Путь к статье (опционально)')
    list_parser.add_argument('-t', '--type', help='Фильтр по типу')
    list_parser.add_argument('-u', '--unresolved', action='store_true', help='Только неразрешённые')

    # resolve - отметить как разрешённую
    resolve_parser = subparsers.add_parser('resolve', help='Отметить заметку как разрешённую')
    resolve_parser.add_argument('article', help='Путь к статье')
    resolve_parser.add_argument('note_id', type=int, help='ID заметки')

    # delete - удалить заметку
    delete_parser = subparsers.add_parser('delete', help='Удалить заметку')
    delete_parser.add_argument('article', help='Путь к статье')
    delete_parser.add_argument('note_id', type=int, help='ID заметки')

    # export - экспортировать
    export_parser = subparsers.add_parser('export', help='Экспортировать заметки')
    export_parser.add_argument('article', help='Путь к статье')
    export_parser.add_argument('-o', '--output', help='Выходной файл')

    # report - отчёт
    subparsers.add_parser('report', help='Создать общий отчёт')

    # scan - сканировать файлы на inline аннотации
    scan_parser = subparsers.add_parser('scan', help='Сканировать файлы на inline аннотации')
    scan_parser.add_argument('-d', '--directory', default='knowledge', help='Директория для сканирования')
    scan_parser.add_argument('--stats', action='store_true', help='Показать статистику')

    # cross-ref - построить граф cross-references
    crossref_parser = subparsers.add_parser('cross-ref', help='Анализ cross-references между заметками')
    crossref_parser.add_argument('--orphaned', action='store_true', help='Показать изолированные заметки')
    crossref_parser.add_argument('--graph', action='store_true', help='Построить граф референсов')

    # analyze - анализ контекста
    analyze_parser = subparsers.add_parser('analyze', help='Анализ контекста заметок')
    analyze_parser.add_argument('-t', '--topics', action='store_true', help='Показать темы')
    analyze_parser.add_argument('-s', '--sentiment', action='store_true', help='Показать sentiment')
    analyze_parser.add_argument('--importance', action='store_true', help='Сортировать по важности')

    # visualize - HTML визуализация
    visualize_parser = subparsers.add_parser('visualize', help='Создать HTML визуализацию')
    visualize_parser.add_argument('-o', '--output', default='marginalia_overview.html', help='Выходной файл')

    # all - комплексный анализ
    all_parser = subparsers.add_parser('all', help='Комплексный анализ + все экспорты')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    manager = MarginaliaManager(root_dir)

    if args.command == 'add':
        article_path = root_dir / args.article
        note = manager.add_note(
            article_path,
            args.text,
            position=args.position,
            note_type=args.type,
            author=args.author
        )
        print(f"✅ Заметка #{note['id']} добавлена к {args.article}")

    elif args.command == 'list':
        if args.article:
            article_path = root_dir / args.article
            manager.print_notes(article_path)
        elif args.unresolved:
            notes = manager.get_unresolved_notes()
            print(f"\n⚠️  Неразрешённых заметок: {len(notes)}\n")
            for note in notes:
                print(f"#{note['id']} {note['article']} @ {note['position']}")
                print(f"   {note['text'][:80]}...\n")
        elif args.type:
            notes = manager.get_all_notes_by_type(args.type)
            print(f"\n📝 Заметок типа '{args.type}': {len(notes)}\n")
            for note in notes:
                print(f"#{note['id']} {note['article']}")
                print(f"   {note['text'][:80]}...\n")
        else:
            manager.print_notes()

    elif args.command == 'resolve':
        article_path = root_dir / args.article
        if manager.mark_resolved(article_path, args.note_id):
            print(f"✅ Заметка #{args.note_id} отмечена как разрешённая")
        else:
            print(f"❌ Заметка не найдена")

    elif args.command == 'delete':
        article_path = root_dir / args.article
        if manager.delete_note(article_path, args.note_id):
            print(f"✅ Заметка #{args.note_id} удалена")
        else:
            print(f"❌ Заметка не найдена")

    elif args.command == 'export':
        article_path = root_dir / args.article
        output = args.output or f"{article_path.stem}_marginalia.md"
        content = manager.export_to_markdown(article_path, output)
        if content:
            print(f"✅ Маргиналии экспортированы в {output}")
        else:
            print(f"⚠️  Нет заметок для экспорта")

    elif args.command == 'report':
        report = manager.generate_report()
        output_file = root_dir / "MARGINALIA_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Отчёт создан: {output_file}")
        print(report)

    elif args.command == 'scan':
        print(f"\n🔍 Сканирование директории {args.directory}...\n")

        extractor = AnnotationExtractor()
        scan_dir = root_dir / args.directory
        results = extractor.scan_directory(scan_dir)

        if args.stats:
            stats = extractor.get_statistics(results)

            print(f"Всего аннотаций: {stats['total']}")
            print(f"Файлов с аннотациями: {stats['files_with_annotations']}\n")

            print("По типам:")
            for ann_type, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
                print(f"  {ann_type:15s}: {count}")

            print("\nТоп файлов:")
            top_files = sorted(stats['by_file'].items(), key=lambda x: -x[1])[:10]
            for file_path, count in top_files:
                print(f"  {count:3d} - {file_path}")

        else:
            # Вывести все найденные аннотации
            for file_path, annotations in results.items():
                print(f"\n📄 {file_path}:")
                for ann in annotations:
                    print(f"  Line {ann['line']}: [{ann['type']}] {ann['text'][:80]}")

        print(f"\n✅ Найдено аннотаций: {sum(len(anns) for anns in results.values())}")

    elif args.command == 'cross-ref':
        print("\n🔗 Анализ cross-references...\n")

        builder = CrossReferenceBuilder(manager.notes)
        graph = builder.build_reference_graph()

        if args.orphaned:
            orphaned = builder.find_orphaned_notes()
            print(f"Изолированных заметок: {len(orphaned)}\n")

            for note_key in orphaned[:20]:
                print(f"  {note_key}")

        elif args.graph:
            print(f"Граф референсов:")
            print(f"  Узлов: {graph['total_nodes']}")
            print(f"  Рёбер: {graph['total_edges']}")
            print(f"  Кластеров: {graph['total_clusters']}\n")

            print("Кластеры:")
            for i, cluster in enumerate(graph['clusters'][:5], 1):
                print(f"\n  Кластер {i} ({len(cluster)} заметок):")
                for note in cluster[:5]:
                    print(f"    - {note}")

        else:
            refs = builder.extract_references()
            print(f"References: {len(refs['references'])}")
            print(f"Backlinks: {len(refs['backlinks'])}\n")

            print("Заметки с наибольшим количеством референсов:")
            top_refs = sorted(
                [(k, len(v)) for k, v in refs['references'].items()],
                key=lambda x: -x[1]
            )[:10]

            for note_key, ref_count in top_refs:
                print(f"  {note_key}: {ref_count} refs")

    elif args.command == 'analyze':
        print("\n📊 Анализ контекста заметок...\n")

        analyzer = ContextAnalyzer()
        analysis = analyzer.analyze_all_notes(manager.notes)

        if args.topics:
            print("Темы:")
            for topic, count in sorted(analysis['overall']['topics'].items(), key=lambda x: -x[1]):
                print(f"  {topic:15s}: {count}")

        elif args.sentiment:
            print("Sentiment:")
            for sentiment, count in sorted(analysis['overall']['sentiment'].items(), key=lambda x: -x[1]):
                print(f"  {sentiment:10s}: {count}")

        elif args.importance:
            print(f"Средняя важность: {analysis['overall']['avg_importance']:.1f}/10\n")

            # Найти самые важные заметки
            all_notes_with_importance = []

            for article_path, notes in manager.notes.items():
                for note in notes:
                    note_analysis = analyzer.analyze_note(note)
                    all_notes_with_importance.append({
                        'article': article_path,
                        'id': note['id'],
                        'importance': note_analysis['importance'],
                        'text': note['text']
                    })

            all_notes_with_importance.sort(key=lambda x: -x['importance'])

            print("Топ-10 самых важных заметок:\n")
            for i, note in enumerate(all_notes_with_importance[:10], 1):
                print(f"{i}. {note['article']}#{note['id']} (важность: {note['importance']}/10)")
                print(f"   {note['text'][:100]}...\n")

        else:
            # Полный анализ
            print(f"Средняя важность: {analysis['overall']['avg_importance']:.1f}/10\n")

            print("Топ темы:")
            for topic, count in sorted(analysis['overall']['topics'].items(), key=lambda x: -x[1])[:5]:
                print(f"  {topic}: {count}")

            print("\nSentiment:")
            for sentiment, count in sorted(analysis['overall']['sentiment'].items(), key=lambda x: -x[1]):
                print(f"  {sentiment}: {count}")

            print("\nТоп ключевые слова:")
            for keyword, count in list(analysis['overall']['top_keywords'].items())[:10]:
                print(f"  {keyword}: {count}")

    elif args.command == 'visualize':
        print(f"\n🎨 Создание HTML визуализации...\n")

        visualizer = VisualizationGenerator(manager.notes)
        output_path = root_dir / args.output
        visualizer.generate_html_overview(output_path)

        print(f"✅ Визуализация создана: {output_path}")

    elif args.command == 'all':
        print("\n" + "="*60)
        print("КОМПЛЕКСНЫЙ АНАЛИЗ МАРГИНАЛИЙ")
        print("="*60)

        # 1. Scan inline annotations
        print("\n🔍 1. Сканирование inline аннотаций...")
        extractor = AnnotationExtractor()
        scan_dir = root_dir / "knowledge"
        results = extractor.scan_directory(scan_dir)
        stats = extractor.get_statistics(results)
        print(f"   Найдено: {stats['total']} аннотаций в {stats['files_with_annotations']} файлах")

        # 2. Cross-reference analysis
        print("\n🔗 2. Анализ cross-references...")
        builder = CrossReferenceBuilder(manager.notes)
        graph = builder.build_reference_graph()
        orphaned = builder.find_orphaned_notes()
        print(f"   Граф: {graph['total_nodes']} узлов, {graph['total_edges']} рёбер, {graph['total_clusters']} кластеров")
        print(f"   Изолированных: {len(orphaned)}")

        # 3. Context analysis
        print("\n📊 3. Анализ контекста...")
        analyzer = ContextAnalyzer()
        analysis = analyzer.analyze_all_notes(manager.notes)
        print(f"   Средняя важность: {analysis['overall']['avg_importance']:.1f}/10")
        print(f"   Темы: {len(analysis['overall']['topics'])}")
        print(f"   Ключевые слова: {len(analysis['overall']['top_keywords'])}")

        # 4. Generate reports
        print("\n📝 4. Создание отчётов...")

        # Markdown report
        report = manager.generate_report()
        report_file = root_dir / "MARGINALIA_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"   ✅ Markdown: {report_file}")

        # HTML visualization
        visualizer = VisualizationGenerator(manager.notes)
        html_file = root_dir / "marginalia_overview.html"
        visualizer.generate_html_overview(html_file)
        print(f"   ✅ HTML: {html_file}")

        print("\n✨ Все операции завершены!")
        print("\n💡 Созданные файлы:")
        print(f"   - {report_file}")
        print(f"   - {html_file}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
