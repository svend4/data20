#!/bin/bash
# ============================================================================
# GENERATE ALL OUTPUTS - Запуск всех 55 инструментов
# ============================================================================
# Этот скрипт генерирует все выходные файлы (HTML/JSON/CSV) из всех tools
# Использование: ./scripts/generate_all.sh [--quick|--full|--validate-only]
# ============================================================================

set -e  # Остановиться при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="$ROOT_DIR/tools"
OUTPUT_DIR="$ROOT_DIR/outputs"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/generate_$(date +%Y%m%d_%H%M%S).log"

# Создать необходимые директории
mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

# Счётчики
TOTAL_TOOLS=0
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0
START_TIME=$(date +%s)

# Массив для failed tools
declare -a FAILED_TOOLS

# Функция логирования
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Функция для красивого вывода
print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    print_header "Проверка зависимостей"

    # Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не найден!"
        exit 1
    fi
    print_success "Python 3: $(python3 --version)"

    # Проверка Python модулей
    local required_modules=("yaml" "pathlib")
    for module in "${required_modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            print_success "Python модуль: $module"
        else
            print_warning "Python модуль отсутствует: $module (может быть нужен для некоторых tools)"
        fi
    done

    echo ""
}

# Группы инструментов по приоритету
# Tier 1: Критичные (индексация, поиск, валидация)
TIER1_TOOLS=(
    "update_indexes.py"
    "validate.py"
    "metadata_validator.py"
)

# Tier 2: Важные (граф, статистика, поиск)
TIER2_TOOLS=(
    "build_graph.py"
    "graph_visualizer.py"
    "search_index.py"
    "statistics_dashboard.py"
    "generate_statistics.py"
)

# Tier 3: Контент (export, bibliography, TOC)
TIER3_TOOLS=(
    "master_index.py"
    "generate_toc.py"
    "generate_bibliography.py"
    "export_manager.py"
    "archive_builder.py"
)

# Tier 4: Анализ (дубликаты, ссылки, качество)
TIER4_TOOLS=(
    "duplicate_detector.py"
    "find_duplicates.py"
    "check_links.py"
    "quality_metrics.py"
    "cross_references.py"
)

# Tier 5: Визуализация (облака тегов, графики)
TIER5_TOOLS=(
    "tags_cloud.py"
    "weighted_tags.py"
    "timeline_generator.py"
    "network_analyzer.py"
)

# Функция запуска инструмента
run_tool() {
    local tool_path=$1
    local tool_name=$(basename "$tool_path")
    local tier=$2

    TOTAL_TOOLS=$((TOTAL_TOOLS + 1))

    echo -e "\n${BLUE}[$TOTAL_TOOLS]${NC} Запуск: ${YELLOW}$tool_name${NC} (Tier $tier)"
    log "INFO" "Starting tool: $tool_name"

    # Таймаут для каждого инструмента (5 минут)
    local timeout=300

    # Запуск с логированием
    if timeout $timeout python3 "$tool_path" >> "$LOG_FILE" 2>&1; then
        print_success "$tool_name завершён успешно"
        log "SUCCESS" "$tool_name completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            print_error "$tool_name превысил таймаут ($timeout сек)"
            log "ERROR" "$tool_name timeout after ${timeout}s"
        else
            print_error "$tool_name завершился с ошибкой (код: $exit_code)"
            log "ERROR" "$tool_name failed with exit code: $exit_code"
        fi
        FAILED_TOOLS+=("$tool_name")
        FAILED_COUNT=$((FAILED_COUNT + 1))
        return 1
    fi
}

# Функция запуска tier'а
run_tier() {
    local tier_num=$1
    shift
    local tools=("$@")

    print_header "TIER $tier_num: ${#tools[@]} инструментов"

    for tool in "${tools[@]}"; do
        local tool_path="$TOOLS_DIR/$tool"
        if [ -f "$tool_path" ]; then
            run_tool "$tool_path" "$tier_num"
        else
            print_warning "$tool не найден, пропускаем"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        fi
    done
}

# Функция запуска всех оставшихся инструментов
run_remaining_tools() {
    print_header "Остальные инструменты"

    # Создать список всех уже запущенных
    local processed_tools=(
        "${TIER1_TOOLS[@]}"
        "${TIER2_TOOLS[@]}"
        "${TIER3_TOOLS[@]}"
        "${TIER4_TOOLS[@]}"
        "${TIER5_TOOLS[@]}"
    )

    # Найти все .py файлы в tools/
    for tool_path in "$TOOLS_DIR"/*.py; do
        local tool_name=$(basename "$tool_path")

        # Проверить, не был ли уже обработан
        local already_processed=0
        for processed in "${processed_tools[@]}"; do
            if [ "$tool_name" = "$processed" ]; then
                already_processed=1
                break
            fi
        done

        if [ $already_processed -eq 0 ]; then
            run_tool "$tool_path" "6"
        fi
    done
}

# Функция быстрого запуска (только критичные)
quick_mode() {
    print_header "БЫСТРЫЙ РЕЖИМ - только критичные инструменты"
    run_tier 1 "${TIER1_TOOLS[@]}"
    run_tier 2 "${TIER2_TOOLS[@]}"
}

# Функция полного запуска
full_mode() {
    print_header "ПОЛНЫЙ РЕЖИМ - все инструменты"
    run_tier 1 "${TIER1_TOOLS[@]}"
    run_tier 2 "${TIER2_TOOLS[@]}"
    run_tier 3 "${TIER3_TOOLS[@]}"
    run_tier 4 "${TIER4_TOOLS[@]}"
    run_tier 5 "${TIER5_TOOLS[@]}"
    run_remaining_tools
}

# Функция только валидации
validate_only_mode() {
    print_header "РЕЖИМ ВАЛИДАЦИИ - только проверки"
    local validation_tools=(
        "validate.py"
        "metadata_validator.py"
        "check_links.py"
        "duplicate_detector.py"
    )
    run_tier "V" "${validation_tools[@]}"
}

# Финальный отчёт
print_report() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    print_header "ОТЧЁТ О ВЫПОЛНЕНИИ"

    echo -e "Всего инструментов: ${BLUE}$TOTAL_TOOLS${NC}"
    echo -e "Успешно: ${GREEN}$SUCCESS_COUNT${NC}"
    echo -e "Ошибки: ${RED}$FAILED_COUNT${NC}"
    echo -e "Пропущено: ${YELLOW}$SKIPPED_COUNT${NC}"
    echo -e "Время выполнения: ${BLUE}${minutes}m ${seconds}s${NC}"
    echo -e "Лог файл: ${BLUE}$LOG_FILE${NC}"

    if [ $FAILED_COUNT -gt 0 ]; then
        echo -e "\n${RED}Инструменты с ошибками:${NC}"
        for failed_tool in "${FAILED_TOOLS[@]}"; do
            echo -e "  ${RED}✗${NC} $failed_tool"
        done
    fi

    # Проверить generated outputs
    echo -e "\n${BLUE}Сгенерированные файлы:${NC}"
    local html_count=$(find "$ROOT_DIR" -maxdepth 1 -name "*.html" -type f 2>/dev/null | wc -l)
    local json_count=$(find "$ROOT_DIR" -maxdepth 1 -name "*.json" -type f 2>/dev/null | wc -l)
    local csv_count=$(find "$ROOT_DIR" -maxdepth 1 -name "*.csv" -type f 2>/dev/null | wc -l)
    local md_count=$(find "$ROOT_DIR" -maxdepth 1 -name "*REPORT*.md" -type f 2>/dev/null | wc -l)

    echo -e "  HTML: ${GREEN}$html_count${NC} файлов"
    echo -e "  JSON: ${GREEN}$json_count${NC} файлов"
    echo -e "  CSV: ${GREEN}$csv_count${NC} файлов"
    echo -e "  Markdown: ${GREEN}$md_count${NC} файлов"

    echo ""

    if [ $FAILED_COUNT -eq 0 ]; then
        print_success "Все инструменты выполнены успешно!"
        return 0
    else
        print_error "Некоторые инструменты завершились с ошибками"
        return 1
    fi
}

# Главная функция
main() {
    # Баннер
    cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║   KNOWLEDGE BASE - GENERATOR                               ║
║   55 инструментов для генерации всех outputs              ║
╚════════════════════════════════════════════════════════════╝
EOF

    log "INFO" "=== Generation started ==="
    log "INFO" "Mode: ${MODE:-full}"
    log "INFO" "Root dir: $ROOT_DIR"

    # Проверка зависимостей
    check_dependencies

    # Режим работы
    local mode="${1:-full}"

    case "$mode" in
        --quick)
            quick_mode
            ;;
        --full)
            full_mode
            ;;
        --validate-only)
            validate_only_mode
            ;;
        --help|-h)
            cat << EOF

ИСПОЛЬЗОВАНИЕ: $0 [РЕЖИМ]

РЕЖИМЫ:
  --quick         Быстрый режим (только критичные инструменты)
  --full          Полный режим (все 55 инструментов) [по умолчанию]
  --validate-only Только валидация (без генерации)
  --help, -h      Показать эту справку

ПРИМЕРЫ:
  $0                  # Полная генерация
  $0 --quick          # Быстрая генерация
  $0 --validate-only  # Только проверки

ВЫВОД:
  - HTML файлы → $ROOT_DIR/*.html
  - JSON файлы → $ROOT_DIR/*.json
  - CSV файлы → $ROOT_DIR/*.csv
  - Отчёты → $ROOT_DIR/*REPORT*.md
  - Логи → $LOG_DIR/

EOF
            exit 0
            ;;
        *)
            full_mode
            ;;
    esac

    # Финальный отчёт
    print_report
    local exit_code=$?

    log "INFO" "=== Generation finished ==="
    log "INFO" "Exit code: $exit_code"

    exit $exit_code
}

# Запуск
main "$@"
