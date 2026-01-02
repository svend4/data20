#!/usr/bin/env python3
"""
Система рубрикаторов - цветовое и визуальное кодирование категорий
Вдохновлено: Illuminated Manuscripts (средневековые иллюминированные рукописи)
"""

from pathlib import Path
import yaml
import re
import json
import argparse
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# Цветовая схема категорий (как средневековые рубрики)
CATEGORY_COLORS = {
    'computers': {
        'emoji': '💻',
        'color': 'blue',
        'hex': '#3498db',
        'ansi': '\033[94m',
        'importance': 'high',
        'style': 'modern'
    },
    'household': {
        'emoji': '🏠',
        'color': 'green',
        'hex': '#2ecc71',
        'ansi': '\033[92m',
        'importance': 'medium',
        'style': 'practical'
    },
    'cooking': {
        'emoji': '🍳',
        'color': 'orange',
        'hex': '#e67e22',
        'ansi': '\033[93m',
        'importance': 'medium',
        'style': 'creative'
    }
}

# Подкатегории с иконками
SUBCATEGORY_ICONS = {
    # Computers
    'hardware': '🔧',
    'software': '📦',
    'programming': '⌨️',
    'ai': '🤖',
    'networking': '🌐',
    'databases': '🗄️',
    'security': '🔒',
    'devops': '⚙️',

    # Household
    'appliances': '🔌',
    'maintenance': '🛠️',
    'electronics': '📺',
    'furniture': '🪑',
    'cleaning': '🧹',
    'energy': '⚡',

    # Cooking
    'breakfast': '🌅',
    'lunch': '🍱',
    'dinner': '🍽️',
    'desserts': '🍰',
    'drinks': '☕'
}

# Статусы с визуальными индикаторами
STATUS_INDICATORS = {
    'draft': {'emoji': '📝', 'color': 'yellow'},
    'published': {'emoji': '✅', 'color': 'green'},
    'archived': {'emoji': '📦', 'color': 'gray'},
    'reviewed': {'emoji': '👁️', 'color': 'blue'}
}

# Уровни важности (как размер буквиц в манускриптах)
IMPORTANCE_LEVELS = {
    'critical': {'emoji': '🔴', 'size': 'XXL'},
    'high': {'emoji': '🟠', 'size': 'XL'},
    'medium': {'emoji': '🟡', 'size': 'L'},
    'low': {'emoji': '🟢', 'size': 'M'},
    'minimal': {'emoji': '⚪', 'size': 'S'}
}


class Rubricator:
    """
    Рубрикатор - система визуального кодирования документов
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def get_category_info(self, category):
        """Получить информацию о категории"""
        return CATEGORY_COLORS.get(category, {
            'emoji': '📄',
            'color': 'gray',
            'hex': '#95a5a6',
            'ansi': '\033[90m'
        })

    def get_visual_header(self, article_meta):
        """
        Создать визуальный заголовок для статьи
        (как иллюминированная буквица в манускрипте)
        """
        category = article_meta.get('category', 'unknown')
        subcategory = article_meta.get('subcategory', '')
        status = article_meta.get('status', 'draft')
        title = article_meta.get('title', 'Untitled')

        cat_info = self.get_category_info(category)
        cat_emoji = cat_info['emoji']

        subcat_emoji = SUBCATEGORY_ICONS.get(subcategory, '📌')
        status_emoji = STATUS_INDICATORS.get(status, {}).get('emoji', '❓')

        # Создать визуальный заголовок
        header = f"{cat_emoji} {subcat_emoji} {status_emoji} {title}"

        return header

    def colorize_terminal(self, text, category):
        """Раскрасить текст для терминала"""
        cat_info = self.get_category_info(category)
        ansi_color = cat_info['ansi']
        reset = '\033[0m'

        return f"{ansi_color}{text}{reset}"

    def generate_legend(self):
        """Создать легенду (ключ) визуальных обозначений"""
        lines = []
        lines.append("# 🎨 Визуальная легенда (Rubricator)\n")
        lines.append("## Категории\n")

        for cat, info in CATEGORY_COLORS.items():
            lines.append(f"- {info['emoji']} **{cat}** - {info['color']}")
            lines.append(f"  - Важность: {info['importance']}")
            lines.append(f"  - Стиль: {info['style']}\n")

        lines.append("\n## Подкатегории\n")

        # Группировать по основной категории
        lines.append("### 💻 Computers\n")
        for subcat in ['hardware', 'software', 'programming', 'ai', 'networking', 'databases', 'security', 'devops']:
            icon = SUBCATEGORY_ICONS.get(subcat, '📌')
            lines.append(f"- {icon} {subcat}\n")

        lines.append("\n### 🏠 Household\n")
        for subcat in ['appliances', 'maintenance', 'electronics', 'furniture', 'cleaning', 'energy']:
            icon = SUBCATEGORY_ICONS.get(subcat, '📌')
            lines.append(f"- {icon} {subcat}\n")

        lines.append("\n### 🍳 Cooking\n")
        for subcat in ['breakfast', 'lunch', 'dinner', 'desserts', 'drinks']:
            icon = SUBCATEGORY_ICONS.get(subcat, '📌')
            lines.append(f"- {icon} {subcat}\n")

        lines.append("\n## Статусы\n")
        for status, info in STATUS_INDICATORS.items():
            lines.append(f"- {info['emoji']} **{status}** - {info['color']}\n")

        lines.append("\n## Уровни важности\n")
        for level, info in IMPORTANCE_LEVELS.items():
            lines.append(f"- {info['emoji']} **{level}** - размер {info['size']}\n")

        return ''.join(lines)

    def add_rubrics_to_article(self, article_path):
        """Добавить рубрики к статье"""
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Извлечь frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return None

            fm = yaml.safe_load(match.group(1))
            body = match.group(2)

            # Добавить рубрики в метаданные
            if 'rubrics' not in fm:
                category = fm.get('category', 'unknown')
                subcategory = fm.get('subcategory', '')
                status = fm.get('status', 'draft')

                cat_info = self.get_category_info(category)

                fm['rubrics'] = {
                    'color': cat_info['color'],
                    'emoji': cat_info['emoji'],
                    'category_icon': cat_info['emoji'],
                    'subcategory_icon': SUBCATEGORY_ICONS.get(subcategory, '📌'),
                    'status_icon': STATUS_INDICATORS.get(status, {}).get('emoji', '❓')
                }

                # Записать обратно
                new_content = "---\n"
                new_content += yaml.dump(fm, allow_unicode=True, sort_keys=False)
                new_content += "---\n\n"
                new_content += body

                with open(article_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return True

            return False

        except Exception as e:
            print(f"⚠️  Ошибка: {e}")
            return None

    def colorize_index(self, index_content, category):
        """Добавить цветовые коды в индекс"""
        cat_info = self.get_category_info(category)
        emoji = cat_info['emoji']

        # Добавить эмодзи к заголовку
        index_content = index_content.replace(
            '# Индекс:',
            f'# {emoji} Индекс:'
        )

        return index_content

    def list_articles_by_color(self):
        """Показать все статьи с цветовым кодированием"""
        print("🎨 Список статей с визуальным кодированием:\n")

        for md_file in sorted(self.knowledge_dir.rglob("*.md")):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    category = fm.get('category', 'unknown')
                    subcategory = fm.get('subcategory', '')
                    status = fm.get('status', 'draft')
                    title = fm.get('title', md_file.stem)

                    # Создать визуальный заголовок
                    header = self.get_visual_header(fm)

                    # Раскрасить для терминала
                    colored = self.colorize_terminal(header, category)

                    relative_path = md_file.relative_to(self.root_dir)
                    print(f"{colored}")
                    print(f"  📂 {relative_path}\n")

            except:
                pass


class RubricStatistics:
    """Статистика использования рубрик"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.knowledge_dir = root_dir / "knowledge"
        self.stats = defaultdict(lambda: defaultdict(int))

    def collect_statistics(self) -> Dict:
        """Собрать статистику по рубрикам"""
        category_count = Counter()
        subcategory_count = Counter()
        status_count = Counter()
        importance_count = Counter()
        color_usage = Counter()

        articles_by_category = defaultdict(list)
        total_articles = 0

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    category = fm.get('category', 'unknown')
                    subcategory = fm.get('subcategory', 'none')
                    status = fm.get('status', 'draft')
                    importance = fm.get('importance', 'medium')

                    category_count[category] += 1
                    subcategory_count[subcategory] += 1
                    status_count[status] += 1
                    importance_count[importance] += 1

                    # Color usage
                    if category in CATEGORY_COLORS:
                        color = CATEGORY_COLORS[category]['color']
                        color_usage[color] += 1

                    articles_by_category[category].append(md_file.stem)
                    total_articles += 1

            except Exception as e:
                pass

        return {
            'total_articles': total_articles,
            'category_count': dict(category_count),
            'subcategory_count': dict(subcategory_count),
            'status_count': dict(status_count),
            'importance_count': dict(importance_count),
            'color_usage': dict(color_usage),
            'articles_by_category': dict(articles_by_category),
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, stats: Dict) -> str:
        """Генерировать отчёт по статистике"""
        lines = []
        lines.append("# 📊 Статистика рубрик\n\n")
        lines.append(f"**Дата**: {stats['timestamp']}\n")
        lines.append(f"**Всего статей**: {stats['total_articles']}\n\n")

        lines.append("## Категории\n\n")
        for cat, count in sorted(stats['category_count'].items(), key=lambda x: x[1], reverse=True):
            cat_info = CATEGORY_COLORS.get(cat, {})
            emoji = cat_info.get('emoji', '📄')
            percentage = (count / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
            lines.append(f"- {emoji} **{cat}**: {count} ({percentage:.1f}%)\n")

        lines.append("\n## Подкатегории (топ-10)\n\n")
        top_subcats = sorted(stats['subcategory_count'].items(), key=lambda x: x[1], reverse=True)[:10]
        for subcat, count in top_subcats:
            icon = SUBCATEGORY_ICONS.get(subcat, '📌')
            lines.append(f"- {icon} **{subcat}**: {count}\n")

        lines.append("\n## Статусы\n\n")
        for status, count in sorted(stats['status_count'].items(), key=lambda x: x[1], reverse=True):
            status_info = STATUS_INDICATORS.get(status, {})
            emoji = status_info.get('emoji', '❓')
            percentage = (count / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
            lines.append(f"- {emoji} **{status}**: {count} ({percentage:.1f}%)\n")

        lines.append("\n## Цветовое распределение\n\n")
        for color, count in sorted(stats['color_usage'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{color}**: {count}\n")

        return ''.join(lines)


class ColorSchemeGenerator:
    """Генератор цветовых схем"""

    # Предопределённые темы
    THEMES = {
        'classic': {
            'computers': {'color': 'blue', 'hex': '#3498db'},
            'household': {'color': 'green', 'hex': '#2ecc71'},
            'cooking': {'color': 'orange', 'hex': '#e67e22'}
        },
        'dark': {
            'computers': {'color': 'cyan', 'hex': '#00bcd4'},
            'household': {'color': 'lime', 'hex': '#8bc34a'},
            'cooking': {'color': 'amber', 'hex': '#ffc107'}
        },
        'pastel': {
            'computers': {'color': 'light-blue', 'hex': '#b3e5fc'},
            'household': {'color': 'light-green', 'hex': '#c8e6c9'},
            'cooking': {'color': 'peach', 'hex': '#ffccbc'}
        },
        'high_contrast': {
            'computers': {'color': 'electric-blue', 'hex': '#0000ff'},
            'household': {'color': 'lime-green', 'hex': '#00ff00'},
            'cooking': {'color': 'red-orange', 'hex': '#ff4500'}
        }
    }

    @staticmethod
    def get_theme(theme_name: str) -> Dict:
        """Получить тему по имени"""
        return ColorSchemeGenerator.THEMES.get(theme_name, ColorSchemeGenerator.THEMES['classic'])

    @staticmethod
    def generate_css(theme_name: str = 'classic') -> str:
        """Генерировать CSS для темы"""
        theme = ColorSchemeGenerator.get_theme(theme_name)

        css = [f"/* Rubric Theme: {theme_name} */\n\n"]

        for category, colors in theme.items():
            css.append(f".rubric-{category} {{\n")
            css.append(f"  color: {colors['hex']};\n")
            css.append(f"  border-left: 4px solid {colors['hex']};\n")
            css.append(f"  padding-left: 12px;\n")
            css.append(f"}}\n\n")

        return ''.join(css)

    @staticmethod
    def list_themes() -> List[str]:
        """Список доступных тем"""
        return list(ColorSchemeGenerator.THEMES.keys())


class RubricValidator:
    """Валидатор рубрик"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.knowledge_dir = root_dir / "knowledge"
        self.issues = []

    def validate(self) -> Dict:
        """Проверить корректность рубрик"""
        self.issues = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if not match:
                    self.issues.append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'type': 'missing_frontmatter',
                        'severity': 'high',
                        'message': 'Отсутствует frontmatter'
                    })
                    continue

                fm = yaml.safe_load(match.group(1))

                # Check required fields
                if 'category' not in fm:
                    self.issues.append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'type': 'missing_category',
                        'severity': 'high',
                        'message': 'Отсутствует категория'
                    })

                # Check category validity
                category = fm.get('category', '')
                if category and category not in CATEGORY_COLORS and category != 'unknown':
                    self.issues.append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'type': 'invalid_category',
                        'severity': 'medium',
                        'message': f'Неизвестная категория: {category}'
                    })

                # Check subcategory validity
                subcategory = fm.get('subcategory', '')
                if subcategory and subcategory not in SUBCATEGORY_ICONS:
                    self.issues.append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'type': 'invalid_subcategory',
                        'severity': 'low',
                        'message': f'Неизвестная подкатегория: {subcategory}'
                    })

                # Check status validity
                status = fm.get('status', '')
                if status and status not in STATUS_INDICATORS:
                    self.issues.append({
                        'file': str(md_file.relative_to(self.root_dir)),
                        'type': 'invalid_status',
                        'severity': 'low',
                        'message': f'Неизвестный статус: {status}'
                    })

            except Exception as e:
                self.issues.append({
                    'file': str(md_file.relative_to(self.root_dir)),
                    'type': 'parse_error',
                    'severity': 'high',
                    'message': f'Ошибка парсинга: {str(e)}'
                })

        # Count by severity
        severity_count = Counter([issue['severity'] for issue in self.issues])

        return {
            'total_issues': len(self.issues),
            'issues': self.issues,
            'severity_count': dict(severity_count),
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, validation: Dict) -> str:
        """Генерировать отчёт о валидации"""
        lines = []
        lines.append("# 🔍 Отчёт валидации рубрик\n\n")
        lines.append(f"**Дата**: {validation['timestamp']}\n")
        lines.append(f"**Всего проблем**: {validation['total_issues']}\n\n")

        if validation['total_issues'] == 0:
            lines.append("✅ **Проблем не обнаружено!**\n")
            return ''.join(lines)

        lines.append("## Статистика по серьёзности\n\n")
        for severity in ['high', 'medium', 'low']:
            count = validation['severity_count'].get(severity, 0)
            if count > 0:
                emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[severity]
                lines.append(f"- {emoji} **{severity}**: {count}\n")

        lines.append("\n## Проблемы\n\n")
        for issue in validation['issues']:
            emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[issue['severity']]
            lines.append(f"### {emoji} {issue['file']}\n\n")
            lines.append(f"- **Тип**: {issue['type']}\n")
            lines.append(f"- **Серьёзность**: {issue['severity']}\n")
            lines.append(f"- **Сообщение**: {issue['message']}\n\n")

        return ''.join(lines)


class VisualRenderer:
    """Продвинутый визуальный рендерер"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.knowledge_dir = root_dir / "knowledge"

    def generate_html_gallery(self, theme: str = 'classic') -> str:
        """Генерировать HTML-галерею статей с рубриками"""
        articles = []

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    articles.append({
                        'path': str(md_file.relative_to(self.root_dir)),
                        'title': fm.get('title', md_file.stem),
                        'category': fm.get('category', 'unknown'),
                        'subcategory': fm.get('subcategory', ''),
                        'status': fm.get('status', 'draft'),
                        'date': fm.get('date', '')
                    })
            except:
                pass

        # Generate HTML
        html = []
        html.append(f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎨 Rubric Gallery</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        .card-header {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .card-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .card-meta {{
            font-size: 14px;
            color: #666;
        }}
        .card-path {{
            font-size: 12px;
            color: #999;
            margin-top: 8px;
            font-family: monospace;
        }}
        {ColorSchemeGenerator.generate_css(theme)}
    </style>
</head>
<body>
    <h1>🎨 Rubric Gallery</h1>
    <p style="text-align: center; color: #666;">Theme: <strong>{theme}</strong></p>
    <div class="gallery">
""")

        for article in sorted(articles, key=lambda x: x['category']):
            cat_info = CATEGORY_COLORS.get(article['category'], {})
            cat_emoji = cat_info.get('emoji', '📄')
            subcat_emoji = SUBCATEGORY_ICONS.get(article['subcategory'], '📌')
            status_emoji = STATUS_INDICATORS.get(article['status'], {}).get('emoji', '❓')

            html.append(f"""        <div class="card rubric-{article['category']}">
            <div class="card-header">{cat_emoji} {subcat_emoji} {status_emoji}</div>
            <div class="card-title">{article['title']}</div>
            <div class="card-meta">
                Категория: {article['category']}<br>
                Статус: {article['status']}
""")
            if article['date']:
                html.append(f"                <br>Дата: {article['date']}\n")

            html.append(f"""            </div>
            <div class="card-path">{article['path']}</div>
        </div>
""")

        html.append("""    </div>
</body>
</html>
""")

        return ''.join(html)

    def generate_svg_legend(self) -> str:
        """Генерировать SVG-легенду"""
        svg = []
        svg.append("""<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
    <rect width="400" height="300" fill="#f9f9f9"/>
    <text x="200" y="30" font-size="20" font-weight="bold" text-anchor="middle">Rubric Legend</text>
""")

        y = 60
        for cat, info in CATEGORY_COLORS.items():
            svg.append(f"""    <rect x="50" y="{y}" width="20" height="20" fill="{info['hex']}"/>
    <text x="80" y="{y + 15}" font-size="14">{info['emoji']} {cat} - {info['color']}</text>
""")
            y += 30

        svg.append("</svg>")
        return ''.join(svg)


def main():
    parser = argparse.ArgumentParser(
        description='🎨 Система рубрикаторов (Illuminated Manuscripts)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --list              # Показать статьи с цветовым кодированием
  %(prog)s --stats             # Статистика использования рубрик
  %(prog)s --validate          # Валидировать рубрики
  %(prog)s --html dark         # Генерировать HTML-галерею с темой dark
  %(prog)s --add               # Добавить рубрики к статьям
  %(prog)s --legend            # Создать легенду визуальных обозначений
  %(prog)s --themes            # Показать доступные темы
        """
    )

    parser.add_argument('--list', action='store_true',
                        help='Показать все статьи с визуальным кодированием')
    parser.add_argument('--stats', action='store_true',
                        help='Показать статистику использования рубрик')
    parser.add_argument('--validate', action='store_true',
                        help='Валидировать рубрики')
    parser.add_argument('--html', type=str, metavar='THEME', nargs='?', const='classic',
                        help='Генерировать HTML-галерею (темы: classic, dark, pastel, high_contrast)')
    parser.add_argument('--svg', action='store_true',
                        help='Генерировать SVG-легенду')
    parser.add_argument('--add', action='store_true',
                        help='Добавить рубрики ко всем статьям')
    parser.add_argument('--legend', action='store_true',
                        help='Создать легенду визуальных обозначений')
    parser.add_argument('--themes', action='store_true',
                        help='Показать доступные цветовые темы')
    parser.add_argument('--output', type=str,
                        help='Выходной файл для экспорта')
    parser.add_argument('--json', action='store_true',
                        help='Экспорт в JSON (для --stats или --validate)')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Если аргументы не указаны, показать help
    if not any(vars(args).values()):
        parser.print_help()
        return

    rubricator = Rubricator(root_dir)

    # --list: показать статьи с цветовым кодированием
    if args.list:
        print("🎨 Список статей с визуальным кодированием:\n")
        rubricator.list_articles_by_color()

    # --stats: статистика рубрик
    if args.stats:
        print("📊 Сбор статистики рубрик...\n")
        stats_analyzer = RubricStatistics(root_dir)
        stats = stats_analyzer.collect_statistics()

        if args.json:
            output = json.dumps(stats, ensure_ascii=False, indent=2)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"✅ Статистика сохранена в {args.output}")
            else:
                print(output)
        else:
            report = stats_analyzer.generate_report(stats)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"✅ Отчёт сохранён в {args.output}")
            else:
                print(report)

    # --validate: валидация рубрик
    if args.validate:
        print("🔍 Валидация рубрик...\n")
        validator = RubricValidator(root_dir)
        validation = validator.validate()

        if args.json:
            output = json.dumps(validation, ensure_ascii=False, indent=2)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"✅ Результаты валидации сохранены в {args.output}")
            else:
                print(output)
        else:
            report = validator.generate_report(validation)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"✅ Отчёт валидации сохранён в {args.output}")
            else:
                print(report)

                # Summary
                total = validation['total_issues']
                if total == 0:
                    print("\n✅ Все рубрики валидны!")
                else:
                    print(f"\n⚠️  Найдено проблем: {total}")
                    for severity in ['high', 'medium', 'low']:
                        count = validation['severity_count'].get(severity, 0)
                        if count > 0:
                            emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[severity]
                            print(f"  {emoji} {severity}: {count}")

    # --html: генерировать HTML-галерею
    if args.html:
        theme = args.html
        if theme not in ColorSchemeGenerator.list_themes():
            print(f"⚠️  Неизвестная тема: {theme}")
            print(f"Доступные темы: {', '.join(ColorSchemeGenerator.list_themes())}")
            return

        print(f"🎨 Генерация HTML-галереи (тема: {theme})...")
        renderer = VisualRenderer(root_dir)
        html = renderer.generate_html_gallery(theme)

        output_file = args.output or root_dir / "docs" / f"rubric_gallery_{theme}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML-галерея создана: {output_file}")

    # --svg: генерировать SVG-легенду
    if args.svg:
        print("🎨 Генерация SVG-легенды...")
        renderer = VisualRenderer(root_dir)
        svg = renderer.generate_svg_legend()

        output_file = args.output or root_dir / "docs" / "rubric_legend.svg"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg)

        print(f"✅ SVG-легенда создана: {output_file}")

    # --add: добавить рубрики к статьям
    if args.add:
        print("📝 Добавление рубрик к статьям...")
        count = 0

        for md_file in root_dir.glob("knowledge/**/*.md"):
            if md_file.name == "INDEX.md":
                continue

            if rubricator.add_rubrics_to_article(md_file):
                count += 1

        print(f"✅ Рубрики добавлены к {count} статьям")

    # --legend: создать легенду
    if args.legend:
        print("📖 Создание легенды...")
        legend = rubricator.generate_legend()

        output_file = args.output or root_dir / "docs" / "VISUAL_LEGEND.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(legend)

        print(f"✅ Легенда создана: {output_file}")

    # --themes: показать доступные темы
    if args.themes:
        print("🎨 Доступные цветовые темы:\n")
        for theme in ColorSchemeGenerator.list_themes():
            print(f"  • {theme}")
            theme_data = ColorSchemeGenerator.get_theme(theme)
            for cat, colors in theme_data.items():
                print(f"    - {cat}: {colors['color']} ({colors['hex']})")
            print()


if __name__ == "__main__":
    main()
