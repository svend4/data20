# 📖 Commonplace Book — Книга выписок

> Собрание ключевых мыслей, цитат и идей из базы знаний

*Вдохновлено традицией Renaissance commonplace books*

## Статистика

- **Всего выписок**: 155
- **Категорий**: 2

**По типам:**

- **Важные мысли**: 138
- **Принципы**: 17

---

## computers

*48 выписок*

### Важные мысли

> Гарантировать, что у класса есть только один экземпляр, и предоставить глобальную точку доступа к нему.

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self):
        self.connection = None

    def connect(self):
        if not self.connection:
            self.connection = "Connected to DB"
        return self.connection

# Использование
db1 = DatabaseConnection()
db2 = DatabaseConnection()
print(db1 is db2)  # True
```

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> kwargs)
        return instances[cls]

    return get_instance

@singleton
class Config:
    def __init__(self):
        self.settings = {}
```

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> - Конфигурация приложения
- Логгер
- Пул соединений с БД
- Кеш

### 2. Factory Method (Фабричный метод)

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> Определить интерфейс для создания объекта, но оставить подклассам решение о том, какой класс инстанцировать.

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> ```python
from abc import ABC, abstractmethod

class Document(ABC):
    @abstractmethod
    def open(self):
        pass

class PDFDocument(Document):
    def open(self):
        return "Opening PDF document"

class WordDocument(Document):
    def open(self):
        return "Opening Word document"

class DocumentFactory:
    @staticmethod
    def create_document(doc_type: str) -> Document:
        if doc_type == "pdf":
            return PDFDocument()
        elif doc_type == "word":
            return WordDocument()
        else:
            raise ValueError(f"Unknown document type: {doc_type}")

# Использование
factory = DocumentFactory()
doc = factory.create_document("pdf")
print(doc.open())
```

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> ```python
class DocumentFactory:
    _creators = {
        "pdf": PDFDocument,
        "word": WordDocument,
    }

    @classmethod
    def register(cls, name: str, creator):
        cls._creators[name] = creator

    @classmethod
    def create(cls, name: str) -> Document:
        creator = cls._creators.get(name)
        if not creator:
            raise ValueError(f"Unknown document type: {name}")
        return creator()
```

### 3. Builder (Строитель)

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> Отделить конструирование сложного объекта от его представления.

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> ```python
class Pizza:
    def __init__(self):
        self.size = None
        self.cheese = False
        self.pepperoni = False
        self.mushrooms = False

    def __str__(self):
        return f"Pizza(size={self.size}, cheese={self.cheese}, " \
               f"pepperoni={self.pepperoni}, mushrooms={self.mushrooms})"

class PizzaBuilder:
    def __init__(self):
        self.pizza = Pizza()

    def set_size(self, size: str):
        self.pizza.size = size
        return self

    def add_cheese(self):
        self.pizza.cheese = True
        return self

    def add_pepperoni(self):
        self.pizza.pepperoni = True
        return self

    def add_mushrooms(self):
        self.pizza.mushrooms = True
        return self

    def build(self) -> Pizza:
        return self.pizza

# Использование
pizza = (PizzaBuilder()
         .set_size("large")
         .add_cheese()
         .add_pepperoni()
         .build())
```

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

> ```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Pizza:
    size: str
    toppings: List[str] = field(default_factory=list)

    def add_topping(self, topping: str):
        self.toppings.append(topping)
        return self

# Использование
pizza = Pizza("large").add_topping("cheese").add_topping("pepperoni")
```

## Структурные паттерны (Structural Patterns)

### 4. Decorator (Декоратор)

— *[Паттерны проектирования в Python](knowledge/computers/articles/programming/python-patterns.md)*

*...и ещё 32*

### Принципы

> Claude Opus 4.5: самая продвинутая модель на начало 2026 года

— *[Обзор больших языковых моделей 2026 года](knowledge/computers/articles/ai/llm-overview-2026.md)*

> Claude Sonnet 4.5: баланс скорости и качества

— *[Обзор больших языковых моделей 2026 года](knowledge/computers/articles/ai/llm-overview-2026.md)*

> Claude Haiku: быстрая модель для простых задач

— *[Обзор больших языковых моделей 2026 года](knowledge/computers/articles/ai/llm-overview-2026.md)*

> GPT-5: анонсирована в конце 2025

— *[Обзор больших языковых моделей 2026 года](knowledge/computers/articles/ai/llm-overview-2026.md)*

> GPT-4 Turbo: улучшенная версия GPT-4

— *[Обзор больших языковых моделей 2026 года](knowledge/computers/articles/ai/llm-overview-2026.md)*

> Gemini Pro: для коммерческого использования

— *[Обзор больших языковых моделей 2026 года](knowledge/computers/articles/ai/llm-overview-2026.md)*


## household

*107 выписок*

### Важные мысли

> Холодильник с одной дверью, морозильная камера находится внутри

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Компактные размеры
- Низкая цена
- Подходят для малогабаритных кухонь
- Низкое энергопотребление

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Маленький объем морозильной камеры
- Ограниченная функциональность
- Не подходят для больших семей

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> Студенты, одиночки, дачи

### 2. Двухкамерные холодильники

#### С верхней морозильной камерой

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Морозилка сверху
- Холодильная камера снизу
- Компактная высота (140-180 см)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Доступная цена
- Компактность
- Простота обслуживания

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Неудобный доступ к холодильной камере (нужно наклоняться)
- Ограниченный объем

#### С нижней морозильной камерой

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Морозилка внизу
- Холодильная камера сверху
- Высота 170-210 см

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Удобный доступ к холодильной камере (на уровне глаз)
- Больший полезный объем
- Современный дизайн

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> - Выше цена
- Нужно наклоняться к морозилке

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

*...и ещё 86*

### Принципы

> A+++: самый экономичный (потребление <30% базового уровня)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> A++: очень экономичный (30-42%)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> A: средний уровень (55-75%)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> B, C, D: устаревшие, не рекомендуются

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> 30-35 дБ: очень тихий (как шелест листвы)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> 36-40 дБ: тихий (нормальный уровень)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> 41-45 дБ: средний (может быть заметен)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> 46+ дБ: шумный (не рекомендуется для студии)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> Расположение:: Не ставить рядом с плитой, батареей

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

> Температура:: Холодильник: +2°C...+5°C (оптимально +4°C)

— *[Руководство по выбору холодильника в 2026 году](knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md)*

*...и ещё 1*


