# 🚀 Быстрый старт с инструментами

## Основные инструменты (в порядке использования)

### 1. Обработка входящих материалов

```bash
# Поместить файл в inbox/raw/
echo "# Статья про Docker" > inbox/raw/2026-01-02-docker.md

# Обработать автоматически
python tools/process_inbox.py
```

**Результат:** Система предложит категорию, теги и структуру

---

### 2. Создание статьи

```bash
# Использовать шаблон
cat docs/TEMPLATES.md

# Создать статью с метаданными
nano knowledge/computers/articles/programming/docker-guide.md
```

---

### 3. Поиск связанных статей

```bash
# Найти похожие статьи для перекрестных ссылок
python tools/find_related.py knowledge/computers/articles/programming/docker-guide.md
```

**Результат:** Топ-5 связанных статей с объяснением почему

---

### 4. Обновление индексов

```bash
# Автоматически обновить все индексы
python tools/update_indexes.py
```

**Результат:** Обновлены INDEX.md во всех категориях

---

### 5. Валидация

```bash
# Проверить корректность
python tools/validate.py
```

**Результат:** Отчёт об ошибках и предупреждениях

---

## Инструменты поиска

### Concordance (Средневековый индекс)

```bash
# Построить индекс всех слов
python tools/build_concordance.py

# Найти слово в конкордансе
python tools/search_concordance.py docker
python tools/search_concordance.py python
python tools/search_concordance.py холодильник
```

**Что это:** Алфавитный указатель ВСЕХ значимых слов с местоположением

**Преимущества:**
- Мгновенный поиск любого слова
- Видно контекст использования
- Средневековая техника работает в 2026!

---

### Advanced Search (TF-IDF + Boolean)

```bash
# Простой поиск
python tools/advanced_search.py docker

# Boolean операторы
python tools/advanced_search.py "docker AND kubernetes"
python tools/advanced_search.py "python OR javascript"
python tools/advanced_search.py "programming NOT java"
python tools/advanced_search.py "(docker OR kubernetes) AND NOT windows"

# Точная фраза
python tools/advanced_search.py '"design patterns"'
```

**Что это:** Умный поиск с ранжированием по релевантности

**Преимущества:**
- Boolean логика (AND, OR, NOT)
- TF-IDF ранжирование
- Поиск фраз
- Показывает контекст

---

## Аналитические инструменты

### Статистика

```bash
python tools/generate_statistics.py
```

**Результат:**
- Общая статистика (статьи, слова, теги)
- По категориям
- Метрики качества
- Топ статей
- Экспорт в JSON

---

### Граф знаний

```bash
python tools/build_graph.py
```

**Результат:**
- knowledge_graph.json - данные
- knowledge_graph.dot - для Graphviz
- knowledge_graph.mmd - для Mermaid
- Анализ hub'ов и связности

**Визуализация:**
```bash
# Установить Graphviz
sudo apt install graphviz  # Linux
brew install graphviz      # macOS

# Создать PNG
dot -Tpng knowledge_graph.dot -o graph.png

# Создать SVG (интерактивный)
dot -Tsvg knowledge_graph.dot -o graph.svg
```

---

### Поиск дубликатов

```bash
python tools/find_duplicates.py
```

**Результат:**
- Статьи с общими тегами
- Похожие заголовки
- Дубликаты по содержимому (>70% схожести)

---

## Типичные сценарии

### Сценарий 1: Добавление новости

```bash
# 1. Сохранить в inbox
echo "Новость про AI..." > inbox/raw/2026-01-02-ai-news.md

# 2. Обработать
python tools/process_inbox.py

# 3. Создать статью на основе рекомендаций
nano knowledge/computers/articles/ai/новость.md

# 4. Найти связанные
python tools/find_related.py knowledge/computers/articles/ai/новость.md

# 5. Добавить ссылки в "См. также"

# 6. Обновить индексы
python tools/update_indexes.py

# 7. Коммит
git add . && git commit -m "[computers] Добавлена новость про AI"
```

---

### Сценарий 2: Поиск информации

```bash
# Вариант 1: Через индексы
cat INDEX.md
cat knowledge/computers/index/INDEX.md

# Вариант 2: Concordance
python tools/build_concordance.py  # Один раз
python tools/search_concordance.py docker

# Вариант 3: Advanced search
python tools/advanced_search.py "docker AND kubernetes"

# Вариант 4: Grep (классика)
grep -r "docker" knowledge/ --include="*.md"
```

---

### Сценарий 3: Анализ базы знаний

```bash
# Статистика
python tools/generate_statistics.py

# Граф связей
python tools/build_graph.py
dot -Tpng knowledge_graph.dot -o graph.png

# Проверка дубликатов
python tools/find_duplicates.py

# Валидация
python tools/validate.py
```

---

### Сценарий 4: Еженедельное обслуживание

```bash
# 1. Обработать inbox
python tools/process_inbox.py

# 2. Обновить индексы
python tools/update_indexes.py

# 3. Валидация
python tools/validate.py

# 4. Статистика
python tools/generate_statistics.py

# 5. Коммит
git add . && git commit -m "[maintenance] Еженедельное обслуживание"
```

---

## Горячие клавиши (алиасы)

Добавьте в `.bashrc` или `.zshrc`:

```bash
# Переменная для пути к базе знаний
export KB_PATH="$HOME/data20"

# Алиасы
alias kb-cd="cd $KB_PATH"
alias kb-update="cd $KB_PATH && python tools/update_indexes.py"
alias kb-validate="cd $KB_PATH && python tools/validate.py"
alias kb-stats="cd $KB_PATH && python tools/generate_statistics.py"
alias kb-graph="cd $KB_PATH && python tools/build_graph.py"
alias kb-search="cd $KB_PATH && python tools/advanced_search.py"
alias kb-find="cd $KB_PATH && python tools/search_concordance.py"

# Функция для быстрого добавления
kb-add() {
    cd $KB_PATH
    python tools/process_inbox.py
    python tools/update_indexes.py
    python tools/validate.py
}
```

**Использование:**
```bash
kb-cd              # Перейти в базу знаний
kb-update          # Обновить индексы
kb-validate        # Валидировать
kb-stats           # Статистика
kb-search docker   # Поиск
kb-find python     # Concordance
kb-add             # Полная обработка inbox
```

---

## Шпаргалка команд

| Задача | Команда |
|--------|---------|
| Обработка inbox | `python tools/process_inbox.py` |
| Обновление индексов | `python tools/update_indexes.py` |
| Валидация | `python tools/validate.py` |
| Поиск связанных | `python tools/find_related.py <файл>` |
| Concordance | `python tools/build_concordance.py` |
| Поиск в concordance | `python tools/search_concordance.py <слово>` |
| Advanced search | `python tools/advanced_search.py <запрос>` |
| Статистика | `python tools/generate_statistics.py` |
| Граф знаний | `python tools/build_graph.py` |
| Поиск дубликатов | `python tools/find_duplicates.py` |

---

## Советы и трюки

### 1. Конкорданс для быстрого поиска
```bash
# Построить один раз
python tools/build_concordance.py

# Потом искать мгновенно
python tools/search_concordance.py <любое_слово>
```

### 2. Boolean поиск для точности
```bash
# Найти статьи и про Docker, и про Kubernetes
python tools/advanced_search.py "docker AND kubernetes"

# Найти Python, но не Django
python tools/advanced_search.py "python NOT django"
```

### 3. Граф для визуализации связей
```bash
# Построить граф
python tools/build_graph.py

# Визуализировать
dot -Tsvg knowledge_graph.dot -o graph.svg

# Открыть в браузере
firefox graph.svg
```

### 4. Регулярное обслуживание
```bash
# Создать cron job для еженедельного обновления
# crontab -e
0 0 * * 0 cd $HOME/data20 && python tools/update_indexes.py
```

---

## Что дальше?

1. **Изучите документацию:**
   - `docs/METHODOLOGY.md` - Методология
   - `docs/ADVANCED_IDEAS.md` - Расширенные идеи
   - `docs/FROM_MEDIEVAL_TO_FUTURE.md` - От средневековья до будущего
   - `docs/TOOLS_REFERENCE.md` - Полный справочник

2. **Экспериментируйте:**
   - Попробуйте разные варианты поиска
   - Изучите граф знаний
   - Поиграйте с concordance

3. **Расширяйте:**
   - Добавьте свои категории
   - Создайте новые инструменты
   - Интегрируйте с AI

---

**Happy Knowledge Managing! 📚✨**
