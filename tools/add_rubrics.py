#!/usr/bin/env python3
"""
Система рубрикаторов - цветовое и визуальное кодирование категорий
Вдохновлено: Illuminated Manuscripts (средневековые иллюминированные рукописи)
"""

from pathlib import Path
import yaml
import re


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


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    rubricator = Rubricator(root_dir)

    print("🎨 Система рубрикаторов (Illuminated Manuscripts)\n")

    # Показать легенду
    legend_file = root_dir / "docs" / "VISUAL_LEGEND.md"
    legend = rubricator.generate_legend()

    with open(legend_file, 'w', encoding='utf-8') as f:
        f.write(legend)

    print(f"✅ Легенда создана: {legend_file}\n")

    # Показать статьи с цветами
    rubricator.list_articles_by_color()

    # Добавить рубрики ко всем статьям
    print("\n📝 Добавление рубрик к статьям...")
    count = 0

    for md_file in root_dir.glob("knowledge/**/*.md"):
        if md_file.name == "INDEX.md":
            continue

        if rubricator.add_rubrics_to_article(md_file):
            count += 1

    print(f"✅ Рубрики добавлены к {count} статьям")


if __name__ == "__main__":
    main()
