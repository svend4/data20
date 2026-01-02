---
title: "Паттерны проектирования в Python"
date: 2026-01-02
tags: [Python, паттерны-проектирования, ООП, архитектура, best-practices]
category: computers
subcategory: programming
status: published
source: "Коллекция примеров и best practices"
related: [../software/dev-tools.md, ../ai/llm-overview-2026.md]
---

# Паттерны проектирования в Python

## Краткое описание
Обзор основных паттернов проектирования и их реализация в Python. Рассматриваются классические паттерны Gang of Four (GoF) и современные Python-специфичные подходы.

## Порождающие паттерны (Creational Patterns)

### 1. Singleton (Одиночка)

**Назначение:** Гарантировать, что у класса есть только один экземпляр, и предоставить глобальную точку доступа к нему.

**Реализация через метакласс:**
```python
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
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

**Современная альтернатива - декоратор:**
```python
from functools import wraps

def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class Config:
    def __init__(self):
        self.settings = {}
```

**Когда использовать:**
- Конфигурация приложения
- Логгер
- Пул соединений с БД
- Кеш

### 2. Factory Method (Фабричный метод)

**Назначение:** Определить интерфейс для создания объекта, но оставить подклассам решение о том, какой класс инстанцировать.

**Реализация:**
```python
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

**Современная реализация с использованием dict:**
```python
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

**Назначение:** Отделить конструирование сложного объекта от его представления.

**Реализация с использованием fluent interface:**
```python
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

**Современная Python-идиома с dataclass:**
```python
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

**Назначение:** Динамически добавлять объекту новые обязанности.

**Python декораторы - нативная поддержка паттерна:**
```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

def cache_decorator(func):
    cache = {}

    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

@timing_decorator
@cache_decorator
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

**Декоратор класса:**
```python
def add_logging(cls):
    original_init = cls.__init__

    def new_init(self, *args, **kwargs):
        print(f"Creating instance of {cls.__name__}")
        original_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls

@add_logging
class MyClass:
    def __init__(self, value):
        self.value = value
```

### 5. Adapter (Адаптер)

**Назначение:** Преобразовать интерфейс класса к другому интерфейсу, ожидаемому клиентами.

**Реализация:**
```python
class EuropeanSocket:
    def provide_220v(self):
        return 220

class USASocket:
    def provide_110v(self):
        return 110

class SocketAdapter:
    def __init__(self, socket):
        self.socket = socket

    def provide_220v(self):
        if hasattr(self.socket, 'provide_220v'):
            return self.socket.provide_220v()
        elif hasattr(self.socket, 'provide_110v'):
            return self.socket.provide_110v() * 2
        else:
            raise ValueError("Unknown socket type")

# Использование
usa_socket = USASocket()
adapter = SocketAdapter(usa_socket)
print(adapter.provide_220v())  # 220
```

### 6. Facade (Фасад)

**Назначение:** Предоставить унифицированный интерфейс к набору интерфейсов подсистемы.

**Реализация:**
```python
class CPU:
    def freeze(self):
        print("CPU: Freezing")

    def jump(self, position):
        print(f"CPU: Jumping to {position}")

    def execute(self):
        print("CPU: Executing")

class Memory:
    def load(self, position, data):
        print(f"Memory: Loading {data} to {position}")

class HardDrive:
    def read(self, lba, size):
        return f"Data from sector {lba}"

class ComputerFacade:
    def __init__(self):
        self.cpu = CPU()
        self.memory = Memory()
        self.hard_drive = HardDrive()

    def start(self):
        self.cpu.freeze()
        boot_data = self.hard_drive.read(0, 1024)
        self.memory.load(0, boot_data)
        self.cpu.jump(0)
        self.cpu.execute()

# Использование - простой интерфейс
computer = ComputerFacade()
computer.start()
```

## Поведенческие паттерны (Behavioral Patterns)

### 7. Observer (Наблюдатель)

**Назначение:** Определить зависимость один-ко-многим между объектами так, что при изменении состояния одного объекта все зависящие от него оповещаются об этом.

**Реализация:**
```python
from abc import ABC, abstractmethod
from typing import List

class Observer(ABC):
    @abstractmethod
    def update(self, message: str):
        pass

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    def notify(self, message: str):
        for observer in self._observers:
            observer.update(message)

class EmailNotifier(Observer):
    def update(self, message: str):
        print(f"Email: {message}")

class SMSNotifier(Observer):
    def update(self, message: str):
        print(f"SMS: {message}")

class NewsPublisher(Subject):
    def publish_news(self, news: str):
        print(f"Publishing: {news}")
        self.notify(news)

# Использование
publisher = NewsPublisher()
publisher.attach(EmailNotifier())
publisher.attach(SMSNotifier())
publisher.publish_news("Breaking news!")
```

### 8. Strategy (Стратегия)

**Назначение:** Определить семейство алгоритмов, инкапсулировать каждый и сделать их взаимозаменяемыми.

**Классическая реализация:**
```python
from abc import ABC, abstractmethod

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list:
        pass

class QuickSort(SortStrategy):
    def sort(self, data: list) -> list:
        print("Using QuickSort")
        return sorted(data)  # упрощенно

class MergeSort(SortStrategy):
    def sort(self, data: list) -> list:
        print("Using MergeSort")
        return sorted(data)  # упрощенно

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy):
        self._strategy = strategy

    def sort(self, data: list) -> list:
        return self._strategy.sort(data)

# Использование
sorter = Sorter(QuickSort())
result = sorter.sort([3, 1, 2])
```

**Python-идиоматическая реализация (функции первого класса):**
```python
def quick_sort(data: list) -> list:
    print("Using QuickSort")
    return sorted(data)

def merge_sort(data: list) -> list:
    print("Using MergeSort")
    return sorted(data)

class Sorter:
    def __init__(self, strategy=quick_sort):
        self.strategy = strategy

    def sort(self, data: list) -> list:
        return self.strategy(data)

# Использование
sorter = Sorter(quick_sort)
result = sorter.sort([3, 1, 2])
```

### 9. Command (Команда)

**Назначение:** Инкапсулировать запрос как объект, позволяя параметризовать клиентов с различными запросами, ставить запросы в очередь, логировать их и поддерживать отмену операций.

**Реализация:**
```python
from abc import ABC, abstractmethod
from typing import List

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

class Light:
    def on(self):
        print("Light is ON")

    def off(self):
        print("Light is OFF")

class LightOnCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.on()

    def undo(self):
        self.light.off()

class LightOffCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.off()

    def undo(self):
        self.light.on()

class RemoteControl:
    def __init__(self):
        self.history: List[Command] = []

    def execute_command(self, command: Command):
        command.execute()
        self.history.append(command)

    def undo_last(self):
        if self.history:
            command = self.history.pop()
            command.undo()

# Использование
light = Light()
remote = RemoteControl()

remote.execute_command(LightOnCommand(light))
remote.execute_command(LightOffCommand(light))
remote.undo_last()  # Light is ON
```

## Python-специфичные паттерны

### 10. Context Manager (Контекстный менеджер)

**Использование протокола `__enter__` и `__exit__`:**
```python
class DatabaseConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None

    def __enter__(self):
        print(f"Connecting to {self.connection_string}")
        self.connection = "Connected"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing connection")
        self.connection = None
        return False  # не подавлять исключения

# Использование
with DatabaseConnection("localhost:5432") as db:
    print(f"Working with {db.connection}")
```

**С использованием contextlib:**
```python
from contextlib import contextmanager

@contextmanager
def database_connection(connection_string):
    print(f"Connecting to {connection_string}")
    connection = "Connected"
    try:
        yield connection
    finally:
        print("Closing connection")

# Использование
with database_connection("localhost:5432") as db:
    print(f"Working with {db}")
```

### 11. Descriptor (Дескриптор)

**Для валидации и контроля доступа к атрибутам:**
```python
class PositiveNumber:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, 0)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"{self.name} must be positive")
        instance.__dict__[self.name] = value

class BankAccount:
    balance = PositiveNumber("balance")

    def __init__(self, initial_balance):
        self.balance = initial_balance

# Использование
account = BankAccount(100)
print(account.balance)  # 100
# account.balance = -50  # ValueError
```

## Ключевые моменты
- Python поддерживает паттерны на уровне языка (декораторы, контекстные менеджеры)
- Не все GoF паттерны нужны в Python - язык уже предоставляет более простые решения
- Используйте паттерны для решения реальных проблем, а не ради самих паттернов
- Современный Python предпочитает композицию наследованию
- Функции первого класса упрощают многие поведенческие паттерны

## Ссылки и источники
1. [Python Design Patterns - RefactoringGuru](https://refactoring.guru/design-patterns/python)
2. [Design Patterns in Python - GitHub](https://github.com/faif/python-patterns)
3. [Fluent Python by Luciano Ramalho](https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/)

## См. также
- [[python-best-practices]] - Лучшие практики Python
- [[clean-code-python]] - Чистый код на Python
- [[async-patterns-python]] - Асинхронные паттерны
- [[testing-patterns]] - Паттерны тестирования
