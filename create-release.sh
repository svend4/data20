#!/bin/bash

#
# Автоматическое создание GitHub Release для Data20 Mobile
#
# Этот скрипт автоматически создает GitHub Release с APK файлом
# одной командой без необходимости ручной работы в веб-интерфейсе.
#
# Требования:
# - GitHub CLI (gh) установлен и авторизован
# - Или переменная окружения GITHUB_TOKEN
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "🚀 Автоматическое создание GitHub Release"
echo "========================================="
echo ""

# Проверка параметров
VERSION="${1:-v1.0.0}"
echo -e "${BLUE}📌 Версия релиза: ${VERSION}${NC}"
echo ""

# Проверка GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) не найден${NC}"
    echo ""
    echo "Есть два варианта:"
    echo ""
    echo "Вариант 1: Установить GitHub CLI (рекомендуется)"
    echo "  - macOS: brew install gh"
    echo "  - Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "  - Windows: https://github.com/cli/cli/releases"
    echo ""
    echo "Вариант 2: Создать Release вручную"
    echo "  1. Откройте: https://github.com/svend4/data20/releases/new"
    echo "  2. Tag: ${VERSION}"
    echo "  3. Title: 📱 Data20 Mobile ${VERSION} - Full Offline Edition"
    echo "  4. Description: Скопируйте из RELEASE_NOTES.md"
    echo "  5. Нажмите 'Publish release'"
    echo ""
    echo "GitHub Actions автоматически соберет и загрузит APK (~20 минут)"
    echo ""
    exit 1
fi

# Проверка авторизации GitHub CLI
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI не авторизован${NC}"
    echo ""
    echo "Запустите: gh auth login"
    echo ""
    exit 1
fi

# Проверка что мы в правильном репозитории
REPO_NAME=$(git remote get-url origin 2>/dev/null | sed -E 's/.*github\.com[:/](.+)\.git/\1/' || echo "")
if [ -z "$REPO_NAME" ]; then
    echo -e "${RED}❌ Не найден GitHub репозиторий${NC}"
    echo "Убедитесь что вы в директории data20"
    exit 1
fi

echo -e "${GREEN}✅ Репозиторий: ${REPO_NAME}${NC}"
echo ""

# Проверка что tag еще не существует
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Tag ${VERSION} уже существует${NC}"
    echo ""
    read -p "Удалить существующий tag и пересоздать? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Удаление tag..."
        git tag -d "$VERSION" 2>/dev/null || true
        git push origin ":refs/tags/$VERSION" 2>/dev/null || true
        echo -e "${GREEN}✅ Tag удален${NC}"
        echo ""
    else
        echo "Используйте другую версию: ./create-release.sh v1.0.1"
        exit 1
    fi
fi

# Подготовка release notes
echo "📝 Подготовка release notes..."
RELEASE_NOTES_FILE="RELEASE_NOTES.md"

if [ ! -f "$RELEASE_NOTES_FILE" ]; then
    echo -e "${RED}❌ Файл ${RELEASE_NOTES_FILE} не найден${NC}"
    exit 1
fi

# Создание Release на GitHub
echo ""
echo "🎯 Создание GitHub Release..."
echo ""

RELEASE_TITLE="📱 Data20 Mobile ${VERSION} - Full Offline Edition"

gh release create "$VERSION" \
    --title "$RELEASE_TITLE" \
    --notes-file "$RELEASE_NOTES_FILE" \
    --latest

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo -e "${GREEN}✅ Release создан успешно!${NC}"
    echo "========================================="
    echo ""
    echo "📦 Release: ${VERSION}"
    echo "🔗 URL: https://github.com/${REPO_NAME}/releases/tag/${VERSION}"
    echo ""
    echo "🤖 GitHub Actions автоматически:"
    echo "   1. Соберет APK (~20 минут)"
    echo "   2. Загрузит в Release assets"
    echo "   3. APK будет доступен для скачивания"
    echo ""
    echo "📊 Проверить статус сборки:"
    echo "   https://github.com/${REPO_NAME}/actions"
    echo ""
    echo "📥 После сборки пользователи смогут скачать APK:"
    echo "   https://github.com/${REPO_NAME}/releases/latest"
    echo ""
    echo -e "${BLUE}💡 Совет: Добавьте описание изменений в release после сборки${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Ошибка при создании Release${NC}"
    echo ""
    echo "Попробуйте создать вручную:"
    echo "  https://github.com/${REPO_NAME}/releases/new"
    echo ""
    exit 1
fi
