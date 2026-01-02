# ✓ Отчёт: Валидация метаданных

> Проверка корректности frontmatter

## Статистика

- **Всего статей**: 3
- **✅ Валидных**: 0
- **❌ С ошибками**: 3
- **Успешность**: 0.0%

## ❌ Статьи с ошибками

### knowledge/household/articles/appliances/refrigerator-buying-guide-2026.md

**Ошибки:**
- ❌ date: Неверный тип (ожидается str)
- ❌ difficulty: Недопустимое значение (разрешены: легкий, средний, сложный)

**Предупреждения:**
- ⚠️  Дополнительные поля: difficulty_score, pagerank_inlinks, reading_time_minutes, pagerank_outlinks, status, reading_time, quality_score, pagerank, quality_metrics, word_count, quality_grade

### knowledge/computers/articles/programming/python-patterns.md

**Ошибки:**
- ❌ date: Неверный тип (ожидается str)
- ❌ difficulty: Недопустимое значение (разрешены: легкий, средний, сложный)

**Предупреждения:**
- ⚠️  Дополнительные поля: difficulty_score, pagerank_inlinks, reading_time_minutes, pagerank_outlinks, code_lines, status, reading_time, quality_score, pagerank, quality_metrics, word_count, quality_grade

### knowledge/computers/articles/ai/llm-overview-2026.md

**Ошибки:**
- ❌ date: Неверный тип (ожидается str)
- ❌ difficulty: Недопустимое значение (разрешены: легкий, средний, сложный)

**Предупреждения:**
- ⚠️  Дополнительные поля: difficulty_score, pagerank_inlinks, reading_time_minutes, pagerank_outlinks, status, reading_time, quality_score, pagerank, quality_metrics, word_count, quality_grade

## 💡 Рекомендации

1. Убедитесь, что все обязательные поля присутствуют: `title`, `tags`, `category`
2. Проверьте формат даты (должен быть YYYY-MM-DD)
3. Difficulty должен быть: легкий, средний или сложный
4. Tags должен содержать минимум 1 тег
