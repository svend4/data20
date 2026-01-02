#!/usr/bin/env python3
"""
Dewey Decimal Classification (DDC) - система десятичной классификации
Разработана Мелвилом Дьюи в 1876 году для библиотек

Применяем к нашей базе знаний для стандартизированной классификации
"""

from pathlib import Path
import yaml
import re


# Dewey Decimal Classification для нашей базы знаний
DEWEY_CLASSIFICATION = {
    # 000 - Computer science, information & general works
    'computers': {
        'base': '000',
        'subcategories': {
            'hardware': '621.39',       # Computer engineering
            'software': '005',          # Computer programming
            'programming': '005.1',     # Programming
            'ai': '006.3',             # Artificial intelligence
            'networking': '004.6',      # Interfacing & communications
            'databases': '005.74',      # Database management
            'security': '005.8',        # Data security
            'devops': '005.1',         # Systems programming
        }
    },

    # 600 - Technology (Applied sciences)
    'household': {
        'base': '640',  # Home & family management
        'subcategories': {
            'appliances': '643',        # Housing & household equipment
            'maintenance': '643.7',     # Maintenance & repair
            'electronics': '621.381',   # Electronics
            'furniture': '645',         # Household furnishings
            'cleaning': '648',          # Housekeeping
            'energy': '644',           # Household utilities
        }
    },

    # 600 - Technology (Applied sciences) - Food & cooking
    'cooking': {
        'base': '641',  # Food & drink
        'subcategories': {
            'breakfast': '641.52',      # Breakfast foods
            'lunch': '641.53',          # Lunch
            'dinner': '641.54',         # Dinner
            'desserts': '641.86',       # Desserts
            'drinks': '641.87',        # Beverages
        }
    }
}

# Library of Congress Classification (альтернативная система)
LOC_CLASSIFICATION = {
    'computers': {
        'base': 'QA76',
        'subcategories': {
            'programming': 'QA76.6',
            'ai': 'Q335',
            'networking': 'TK5105.5',
            'databases': 'QA76.9.D3',
        }
    },
    'household': {
        'base': 'TX',
        'subcategories': {
            'appliances': 'TX298',
            'cooking': 'TX',
        }
    },
    'cooking': {
        'base': 'TX',
        'subcategories': {
            'recipes': 'TX714-717',
        }
    }
}


class DeweyClassifier:
    """
    Классификатор статей по системе Дьюи
    """

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def get_dewey_number(self, category, subcategory=None):
        """Получить номер Дьюи для категории/подкатегории"""
        if category not in DEWEY_CLASSIFICATION:
            return None

        cat_data = DEWEY_CLASSIFICATION[category]

        if subcategory and subcategory in cat_data['subcategories']:
            return cat_data['subcategories'][subcategory]

        return cat_data['base']

    def get_loc_number(self, category, subcategory=None):
        """Получить номер Library of Congress"""
        if category not in LOC_CLASSIFICATION:
            return None

        cat_data = LOC_CLASSIFICATION[category]

        if subcategory and subcategory in cat_data['subcategories']:
            return cat_data['subcategories'][subcategory]

        return cat_data['base']

    def classify_article(self, article_path):
        """Добавить классификационные номера к статье"""
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Извлечь frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return None

            fm = yaml.safe_load(match.group(1))
            body = match.group(2)

            category = fm.get('category')
            subcategory = fm.get('subcategory')

            if not category:
                return None

            # Добавить классификационные номера
            modified = False

            if 'dewey' not in fm:
                dewey = self.get_dewey_number(category, subcategory)
                if dewey:
                    fm['dewey'] = dewey
                    modified = True

            if 'lcc' not in fm:  # Library of Congress Classification
                lcc = self.get_loc_number(category, subcategory)
                if lcc:
                    fm['lcc'] = lcc
                    modified = True

            if modified:
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

    def generate_dewey_index(self):
        """Создать индекс по номерам Дьюи"""
        index = {}

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))

                    dewey = fm.get('dewey')
                    if dewey:
                        if dewey not in index:
                            index[dewey] = []

                        index[dewey].append({
                            'file': str(md_file.relative_to(self.root_dir)),
                            'title': fm.get('title', md_file.stem)
                        })

            except:
                pass

        return index

    def print_classification_table(self):
        """Вывести таблицу классификации"""
        print("\n📚 Dewey Decimal Classification для базы знаний\n")
        print("="*80)

        for category, data in DEWEY_CLASSIFICATION.items():
            print(f"\n🔹 {category.upper()} - {data['base']}")
            print("-"*80)

            for subcat, number in data['subcategories'].items():
                print(f"   {number:10s} - {subcat}")

        print("\n" + "="*80)


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    classifier = DeweyClassifier(root_dir)

    # Показать таблицу классификации
    classifier.print_classification_table()

    # Классифицировать все статьи
    print("\n📝 Классификация статей по системе Дьюи...\n")

    count = 0
    for md_file in root_dir.glob("knowledge/**/*.md"):
        if md_file.name == "INDEX.md":
            continue

        if classifier.classify_article(md_file):
            count += 1
            print(f"✅ {md_file.relative_to(root_dir)}")

    print(f"\n✅ Классифицировано статей: {count}")

    # Создать индекс по Дьюи
    dewey_index = classifier.generate_dewey_index()

    print(f"\n📊 Индекс по номерам Дьюи:\n")
    for dewey_num in sorted(dewey_index.keys()):
        articles = dewey_index[dewey_num]
        print(f"{dewey_num}: {len(articles)} статей")
        for article in articles[:3]:
            print(f"   - {article['title']}")
        if len(articles) > 3:
            print(f"   ...и ещё {len(articles) - 3}")


if __name__ == "__main__":
    main()
