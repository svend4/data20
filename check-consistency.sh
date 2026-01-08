#!/bin/bash
# 🔍 Check consistency across all versions
# Проверка консистентности всех версий

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSIONS_DIR="mobile-app-versions"
ALL_VERSIONS=("v1-original" "v2-hybrid" "v3-lite" "v4-standard" "v5-full" "v6-experimental" "v7-debug")

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🔍 Проверка консистентности всех версий${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check backend_main.py functions
echo -e "${BLUE}📝 Проверка функций в backend_main.py${NC}"
echo ""

declare -A function_counts

for version in "${ALL_VERSIONS[@]}"; do
    file="$VERSIONS_DIR/$version/android/app/src/main/python/backend_main.py"
    if [ -f "$file" ]; then
        count=$(grep -c "^def " "$file" 2>/dev/null || echo "0")
        function_counts["$version"]=$count

        if [ "$count" -ge 8 ]; then
            echo -e "${GREEN}  ✅ $version: $count функций${NC}"
        elif [ "$count" -ge 4 ]; then
            echo -e "${YELLOW}  ⚠️  $version: $count функций (ожидается 8)${NC}"
        else
            echo -e "${RED}  ❌ $version: $count функций (критически мало!)${NC}"
        fi
    else
        echo -e "${RED}  ❌ $version: файл не найден${NC}"
        function_counts["$version"]=0
    fi
done

echo ""

# Check Gradle plugin versions
echo -e "${BLUE}🔧 Проверка версий Gradle плагинов${NC}"
echo ""

for version in "${ALL_VERSIONS[@]}"; do
    file="$VERSIONS_DIR/$version/android/build.gradle"
    if [ -f "$file" ]; then
        chaquopy=$(grep "com.chaquo.python:gradle:" "$file" 2>/dev/null | grep -oP "gradle:\K[0-9.]+" || echo "не найдено")
        agp=$(grep "com.android.tools.build:gradle:" "$file" 2>/dev/null | grep -oP "gradle:\K[0-9.]+" || echo "не найдено")
        kotlin=$(grep "ext.kotlin_version" "$file" 2>/dev/null | grep -oP "= '\K[0-9.]+'" || echo "не найдено")

        if [ "$chaquopy" = "15.0.1" ] && [ "$agp" = "8.2.1" ]; then
            echo -e "${GREEN}  ✅ $version: Chaquopy=$chaquopy, AGP=$agp, Kotlin=$kotlin${NC}"
        else
            echo -e "${YELLOW}  ⚠️  $version: Chaquopy=$chaquopy (ожидается 15.0.1), AGP=$agp (ожидается 8.2.1)${NC}"
        fi
    else
        echo -e "${RED}  ❌ $version: android/build.gradle не найден${NC}"
    fi
done

echo ""

# Check settings.gradle
echo -e "${BLUE}⚙️  Проверка settings.gradle${NC}"
echo ""

for version in "${ALL_VERSIONS[@]}"; do
    file="$VERSIONS_DIR/$version/android/settings.gradle"
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $version: settings.gradle существует${NC}"
    else
        echo -e "${YELLOW}  ⚠️  $version: settings.gradle отсутствует${NC}"
    fi
done

echo ""

# Check Android resources
echo -e "${BLUE}📦 Проверка Android ресурсов${NC}"
echo ""

for version in "${ALL_VERSIONS[@]}"; do
    dir="$VERSIONS_DIR/$version/android/app/src/main/res"
    if [ -d "$dir" ]; then
        res_count=$(find "$dir" -type f | wc -l)
        echo -e "${GREEN}  ✅ $version: $res_count файлов ресурсов${NC}"
    else
        echo -e "${YELLOW}  ⚠️  $version: res/ директория отсутствует${NC}"
    fi
done

echo ""

# Check Flutter dependencies
echo -e "${BLUE}📚 Проверка Flutter зависимостей${NC}"
echo ""

for version in "${ALL_VERSIONS[@]}"; do
    file="$VERSIONS_DIR/$version/pubspec.yaml"
    if [ -f "$file" ]; then
        deps=$(grep -c "  [a-z_]*:" "$file" 2>/dev/null || echo "0")
        echo -e "${GREEN}  ✅ $version: $deps зависимостей в pubspec.yaml${NC}"
    else
        echo -e "${RED}  ❌ $version: pubspec.yaml не найден${NC}"
    fi
done

echo ""

# Summary
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📊 Сводка${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Count fully synced versions
fully_synced=0
partially_synced=0
not_synced=0

for version in "${ALL_VERSIONS[@]}"; do
    funcs="${function_counts[$version]}"
    has_settings=false
    has_res=false

    [ -f "$VERSIONS_DIR/$version/android/settings.gradle" ] && has_settings=true
    [ -d "$VERSIONS_DIR/$version/android/app/src/main/res" ] && has_res=true

    if [ "$funcs" -ge 8 ] && [ "$has_settings" = true ] && [ "$has_res" = true ]; then
        ((fully_synced++))
    elif [ "$funcs" -ge 4 ] || [ "$has_settings" = true ]; then
        ((partially_synced++))
    else
        ((not_synced++))
    fi
done

echo -e "${GREEN}✅ Полностью синхронизировано: $fully_synced версий${NC}"
if [ $partially_synced -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Частично синхронизировано: $partially_synced версий${NC}"
fi
if [ $not_synced -gt 0 ]; then
    echo -e "${RED}❌ Не синхронизировано: $not_synced версий${NC}"
fi

echo ""

# Recommendations
if [ $fully_synced -lt 7 ]; then
    echo -e "${BLUE}💡 Рекомендации:${NC}"
    echo ""
    echo "  Для полной синхронизации запустите:"
    echo -e "  ${YELLOW}./sync-versions.sh all v5-full --force${NC}"
    echo ""
fi

echo -e "${BLUE}============================================================${NC}"
