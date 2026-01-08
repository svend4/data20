#!/bin/bash
# 🔄 Sync improvements across all versions
# Синхронизация улучшений между всеми версиями
#
# Usage:
#   ./sync-versions.sh [component] [source_version] [--dry-run]
#
# Examples:
#   ./sync-versions.sh backend_main hybrid        # Sync backend_main from hybrid
#   ./sync-versions.sh gradle v5-full             # Sync gradle configs from v5-full
#   ./sync-versions.sh all hybrid --dry-run       # Preview all changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSIONS_DIR="mobile-app-versions"
SANDBOXES_DIR="mobile-app-sandboxes"
MAIN_APP="mobile-app"

# All version directories
ALL_VERSIONS=(
    "v1-original"
    "v2-hybrid"
    "v3-lite"
    "v4-standard"
    "v5-full"
    "v6-experimental"
    "v7-debug"
)

# All sandboxes
ALL_SANDBOXES=(
    "original-ca458ea"
    "current-324dd58"
    "hybrid-best-of-both"
)

# Component mappings
declare -A COMPONENTS=(
    # Android Gradle configuration
    ["gradle_root"]="android/build.gradle"
    ["gradle_settings"]="android/settings.gradle"
    ["gradle_properties"]="android/gradle.properties"
    ["gradle_app"]="android/app/build.gradle"
    ["gradle_wrapper"]="android/gradle/wrapper/gradle-wrapper.properties"

    # Python backend
    ["backend_main"]="android/app/src/main/python/backend_main.py"
    ["mobile_server"]="android/app/src/main/python/mobile_server.py"
    ["mobile_auth"]="android/app/src/main/python/mobile_auth.py"
    ["mobile_database"]="android/app/src/main/python/mobile_database.py"
    ["mobile_models"]="android/app/src/main/python/mobile_models.py"
    ["mobile_tool_registry"]="android/app/src/main/python/mobile_tool_registry.py"
    ["mobile_tool_runner"]="android/app/src/main/python/mobile_tool_runner.py"

    # Android resources
    ["android_res"]="android/app/src/main/res"
    ["android_manifest"]="android/app/src/main/AndroidManifest.xml"
    ["proguard"]="android/app/proguard-rules.pro"

    # Flutter/Dart code
    ["pubspec"]="pubspec.yaml"
    ["app_variant"]="lib/config/app_variant.dart"
    ["storage_service"]="lib/services/storage_service.dart"
    ["home_screen"]="lib/screens/home_screen.dart"
    ["analysis_options"]="analysis_options.yaml"

    # Documentation
    ["readme"]="README.md"
    ["build_doc"]="BUILD_MOBILE_EMBEDDED.md"
)

# Print usage
usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 [component] [source_version] [--dry-run]"
    echo ""
    echo -e "${BLUE}Components:${NC}"
    echo "  gradle              - All Gradle configs"
    echo "  backend             - All Python backend files"
    echo "  flutter             - All Flutter/Dart files"
    echo "  android_res         - Android resources"
    echo "  all                 - Everything"
    echo "  [specific]          - Specific component (see list)"
    echo ""
    echo -e "${BLUE}Available specific components:${NC}"
    for comp in "${!COMPONENTS[@]}"; do
        echo "  - $comp"
    done | sort
    echo ""
    echo -e "${BLUE}Source versions:${NC}"
    echo "  v1-original, v2-hybrid, v3-lite, v4-standard, v5-full, v6-experimental, v7-debug"
    echo "  hybrid (hybrid-best-of-both sandbox)"
    echo "  current (current-324dd58 sandbox)"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo "  --dry-run          - Preview changes without applying"
    echo "  --force            - Overwrite without confirmation"
}

# Get source directory
get_source_dir() {
    local source=$1

    case $source in
        hybrid)
            echo "$SANDBOXES_DIR/hybrid-best-of-both"
            ;;
        current)
            echo "$SANDBOXES_DIR/current-324dd58"
            ;;
        original)
            echo "$SANDBOXES_DIR/original-ca458ea"
            ;;
        main)
            echo "$MAIN_APP"
            ;;
        v*)
            echo "$VERSIONS_DIR/$source"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Check if file exists in source
check_source_file() {
    local source_dir=$1
    local file_path=$2

    if [ -f "$source_dir/$file_path" ]; then
        return 0
    elif [ -d "$source_dir/$file_path" ]; then
        return 0
    else
        return 1
    fi
}

# Sync single file
sync_file() {
    local source_dir=$1
    local target_dir=$2
    local file_path=$3
    local dry_run=$4
    local force=$5

    local source_file="$source_dir/$file_path"
    local target_file="$target_dir/$file_path"

    # Check if source exists
    if ! check_source_file "$source_dir" "$file_path"; then
        echo -e "${YELLOW}  ⚠️  Source not found: $file_path${NC}"
        return 1
    fi

    # Check if target directory exists
    local target_parent=$(dirname "$target_file")
    if [ ! -d "$target_parent" ]; then
        if [ "$dry_run" = true ]; then
            echo -e "${BLUE}  📁 Would create directory: $target_parent${NC}"
        else
            mkdir -p "$target_parent"
            echo -e "${GREEN}  📁 Created directory: $target_parent${NC}"
        fi
    fi

    # Check if file is different
    if [ -e "$target_file" ]; then
        if diff -q "$source_file" "$target_file" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Already synced: $file_path${NC}"
            return 0
        fi

        if [ "$force" != true ] && [ "$dry_run" != true ]; then
            echo -e "${YELLOW}  ⚠️  File exists and differs: $file_path${NC}"
            read -p "    Overwrite? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}  ⏭️  Skipped: $file_path${NC}"
                return 0
            fi
        fi
    fi

    # Copy file or directory
    if [ "$dry_run" = true ]; then
        echo -e "${BLUE}  📄 Would sync: $file_path${NC}"
    else
        if [ -d "$source_file" ]; then
            cp -r "$source_file" "$target_file"
            echo -e "${GREEN}  ✅ Synced directory: $file_path${NC}"
        else
            cp "$source_file" "$target_file"
            echo -e "${GREEN}  ✅ Synced file: $file_path${NC}"
        fi
    fi
}

# Sync component group
sync_component_group() {
    local group=$1
    local source_dir=$2
    local target_dir=$3
    local dry_run=$4
    local force=$5

    case $group in
        gradle)
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[gradle_root]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[gradle_settings]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[gradle_properties]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[gradle_app]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[gradle_wrapper]}" "$dry_run" "$force"
            ;;
        backend)
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[backend_main]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[mobile_server]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[mobile_auth]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[mobile_database]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[mobile_models]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[mobile_tool_registry]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[mobile_tool_runner]}" "$dry_run" "$force"
            ;;
        flutter)
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[pubspec]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[app_variant]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[storage_service]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[analysis_options]}" "$dry_run" "$force"
            ;;
        all)
            sync_component_group "gradle" "$source_dir" "$target_dir" "$dry_run" "$force"
            sync_component_group "backend" "$source_dir" "$target_dir" "$dry_run" "$force"
            sync_component_group "flutter" "$source_dir" "$target_dir" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[android_res]}" "$dry_run" "$force"
            sync_file "$source_dir" "$target_dir" "${COMPONENTS[proguard]}" "$dry_run" "$force"
            ;;
        *)
            if [ -n "${COMPONENTS[$group]}" ]; then
                sync_file "$source_dir" "$target_dir" "${COMPONENTS[$group]}" "$dry_run" "$force"
            else
                echo -e "${RED}Unknown component: $group${NC}"
                return 1
            fi
            ;;
    esac
}

# Main sync function
sync_to_targets() {
    local component=$1
    local source=$2
    local dry_run=$3
    local force=$4

    local source_dir=$(get_source_dir "$source")

    if [ -z "$source_dir" ] || [ ! -d "$source_dir" ]; then
        echo -e "${RED}❌ Source not found: $source${NC}"
        return 1
    fi

    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}🔄 Syncing '$component' from $source${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""

    local synced_count=0
    local skipped_count=0

    # Sync to all versions
    for version in "${ALL_VERSIONS[@]}"; do
        local target_dir="$VERSIONS_DIR/$version"

        if [ ! -d "$target_dir" ]; then
            echo -e "${YELLOW}⚠️  Version directory not found: $version${NC}"
            ((skipped_count++))
            continue
        fi

        echo -e "${GREEN}📦 Target: $version${NC}"
        if sync_component_group "$component" "$source_dir" "$target_dir" "$dry_run" "$force"; then
            ((synced_count++))
        else
            ((skipped_count++))
        fi
        echo ""
    done

    # Summary
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${GREEN}✅ Synced: $synced_count versions${NC}"
    if [ $skipped_count -gt 0 ]; then
        echo -e "${YELLOW}⏭️  Skipped: $skipped_count versions${NC}"
    fi
    echo -e "${BLUE}============================================================${NC}"
}

# Parse arguments
COMPONENT=""
SOURCE=""
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            if [ -z "$COMPONENT" ]; then
                COMPONENT=$1
            elif [ -z "$SOURCE" ]; then
                SOURCE=$1
            else
                echo -e "${RED}Too many arguments${NC}"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [ -z "$COMPONENT" ] || [ -z "$SOURCE" ]; then
    echo -e "${RED}❌ Missing required arguments${NC}"
    echo ""
    usage
    exit 1
fi

# Run sync
sync_to_targets "$COMPONENT" "$SOURCE" "$DRY_RUN" "$FORCE"
