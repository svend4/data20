#!/bin/bash
# ============================================================================
# CLEAN OUTPUTS - Очистка всех сгенерированных файлов
# ============================================================================
# Удаляет все HTML/JSON/CSV файлы и отчёты
# Использование: ./scripts/clean_outputs.sh [--force]
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Файлы для удаления
PATTERNS=(
    "*.html"
    "*.json"
    "*.csv"
    "*_REPORT.md"
    "*_SUMMARY.md"
    "*.tex"
    "*.svg"
    ".index_cache.json"
    ".link_health_cache.json"
    ".inbox_history.json"
)

echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  CLEAN OUTPUTS${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
echo ""

# Подсчёт файлов
TOTAL_FILES=0
for pattern in "${PATTERNS[@]}"; do
    COUNT=$(find "$ROOT_DIR" -maxdepth 1 -name "$pattern" -type f 2>/dev/null | wc -l)
    TOTAL_FILES=$((TOTAL_FILES + COUNT))
done

if [ $TOTAL_FILES -eq 0 ]; then
    echo -e "${GREEN}Нечего удалять - директория уже чиста!${NC}"
    exit 0
fi

echo -e "Найдено файлов для удаления: ${RED}$TOTAL_FILES${NC}"
echo ""

# Показать примеры
echo -e "${YELLOW}Примеры файлов:${NC}"
for pattern in "${PATTERNS[@]}"; do
    find "$ROOT_DIR" -maxdepth 1 -name "$pattern" -type f 2>/dev/null | head -3 | xargs -n1 basename 2>/dev/null || true
done | head -10

echo ""

if [ "$1" != "--force" ]; then
    echo -e "${RED}ВНИМАНИЕ: Это удалит все сгенерированные файлы!${NC}"
    read -p "Продолжить? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Отменено"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}Удаление файлов...${NC}"

DELETED=0
for pattern in "${PATTERNS[@]}"; do
    while IFS= read -r file; do
        if rm "$file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Удалён: $(basename "$file")"
            DELETED=$((DELETED + 1))
        fi
    done < <(find "$ROOT_DIR" -maxdepth 1 -name "$pattern" -type f 2>/dev/null)
done

echo ""
echo -e "${GREEN}Удалено файлов: $DELETED${NC}"
echo -e "${GREEN}✓ Очистка завершена!${NC}"
