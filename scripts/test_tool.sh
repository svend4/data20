#!/bin/bash
# ============================================================================
# TEST TOOL - Тестирование отдельного инструмента
# ============================================================================
# Быстрое тестирование одного инструмента с детальным выводом
# Использование: ./scripts/test_tool.sh <tool_name.py>
# ============================================================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="$ROOT_DIR/tools"

if [ -z "$1" ]; then
    echo -e "${RED}Ошибка: укажите имя инструмента${NC}"
    echo ""
    echo "Использование: $0 <tool_name.py>"
    echo ""
    echo "Примеры:"
    echo "  $0 search_index.py"
    echo "  $0 duplicate_detector.py"
    echo ""
    echo "Доступные инструменты:"
    ls -1 "$TOOLS_DIR"/*.py | xargs -n1 basename | head -10
    echo "  ... и другие"
    exit 1
fi

TOOL_NAME="$1"
TOOL_PATH="$TOOLS_DIR/$TOOL_NAME"

if [ ! -f "$TOOL_PATH" ]; then
    echo -e "${RED}Ошибка: $TOOL_NAME не найден в $TOOLS_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TESTING: $TOOL_NAME${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}[1/3]${NC} Проверка --help..."
if python3 "$TOOL_PATH" --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} --help работает"
else
    echo -e "${YELLOW}⚠${NC} --help не поддерживается (это нормально для некоторых tools)"
fi

echo -e "\n${YELLOW}[2/3]${NC} Запуск инструмента..."
START_TIME=$(date +%s)

# Создать временную директорию для вывода
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

cd "$ROOT_DIR"

if timeout 60 python3 "$TOOL_PATH" 2>&1 | tee "$TMP_DIR/output.log"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo -e "\n${GREEN}✓${NC} Выполнено успешно за ${DURATION}s"
else
    EXIT_CODE=$?
    echo -e "\n${RED}✗${NC} Ошибка (код: $EXIT_CODE)"
    echo ""
    echo -e "${YELLOW}Последние строки лога:${NC}"
    tail -20 "$TMP_DIR/output.log"
    exit $EXIT_CODE
fi

echo -e "\n${YELLOW}[3/3]${NC} Проверка сгенерированных файлов..."

# Искать новые файлы (созданные за последние 2 минуты)
FILES_CREATED=$(find "$ROOT_DIR" -maxdepth 1 \( -name "*.html" -o -name "*.json" -o -name "*.csv" -o -name "*.md" \) -type f -mmin -2 | wc -l)

if [ $FILES_CREATED -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Создано файлов: $FILES_CREATED"
    echo ""
    echo -e "${BLUE}Новые файлы:${NC}"
    find "$ROOT_DIR" -maxdepth 1 \( -name "*.html" -o -name "*.json" -o -name "*.csv" -o -name "*.md" \) -type f -mmin -2 -exec ls -lh {} \; | awk '{print "  " $9 " (" $5 ")"}'
else
    echo -e "${YELLOW}⚠${NC} Новые файлы не обнаружены (возможно, инструмент обновляет существующие)"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ТЕСТ ПРОЙДЕН УСПЕШНО!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
