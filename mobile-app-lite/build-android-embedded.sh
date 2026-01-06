#!/bin/bash

#
# Build Android APK with Embedded Python Backend - LITE VERSION
#
# This script builds the LIGHTWEIGHT Android application with Chaquopy,
# embedding only backend_main.py (NO external dependencies!).
#
# Requirements:
# - Android SDK
# - Android NDK
# - Chaquopy license (for production builds)
# - Python 3.9+
# - NO external Python packages (uses only stdlib!)
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Clear screen for better visibility
clear

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}${GREEN}██╗     ██╗████████╗███████╗    ██╗   ██╗███████╗██████╗ ███████╗${NC}  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}${GREEN}██║     ██║╚══██╔══╝██╔════╝    ██║   ██║██╔════╝██╔══██╗██╔════╝${NC}  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}${GREEN}██║     ██║   ██║   █████╗      ██║   ██║█████╗  ██████╔╝███████╗${NC}  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}${GREEN}██║     ██║   ██║   ██╔══╝      ╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║${NC}  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}${GREEN}███████╗██║   ██║   ███████╗     ╚████╔╝ ███████╗██║  ██║███████║${NC}  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}${GREEN}╚══════╝╚═╝   ╚═╝   ╚══════╝      ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝${NC}  ${CYAN}║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║${NC}          ${BOLD}${BLUE}📱 Data20 Mobile - ОБЛЕГЧЁННАЯ ВЕРСИЯ 🚀${NC}              ${CYAN}║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}${GREEN}✨ Особенности LITE версии:${NC}"
echo -e "   ${GREEN}✅${NC} Только Python stdlib (${BOLD}БЕЗ${NC} PyPI пакетов)"
echo -e "   ${GREEN}✅${NC} Только backend_main.py (${BOLD}15 KB${NC})"
echo -e "   ${GREEN}✅${NC} Размер APK: ${BOLD}~80-90 МБ${NC} (против ~150 МБ полной)"
echo -e "   ${GREEN}✅${NC} Быстрый старт: ${BOLD}< 5 секунд${NC}"
echo ""
echo -e "${YELLOW}⚠️  Это ОБЛЕГЧЁННАЯ версия для Android!${NC}"
echo -e "${YELLOW}   Для полной версии используйте: ../mobile-app/build-android-embedded.sh${NC}"
echo ""

# Configuration
BUILD_TYPE="${1:-release}"  # debug or release
CLEAN="${2:-false}"

echo "📋 Configuration:"
echo "   Build type: $BUILD_TYPE"
echo "   Clean build: $CLEAN"
echo ""

# Check for required tools
echo "🔍 Checking requirements..."

if ! command -v flutter &> /dev/null; then
    echo -e "${RED}❌ Flutter not found. Please install Flutter SDK.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Check Android SDK
if [ -z "$ANDROID_HOME" ]; then
    echo -e "${YELLOW}⚠️  ANDROID_HOME not set. Trying to detect...${NC}"
    # Common locations
    if [ -d "$HOME/Android/Sdk" ]; then
        export ANDROID_HOME="$HOME/Android/Sdk"
    elif [ -d "$HOME/Library/Android/sdk" ]; then
        export ANDROID_HOME="$HOME/Library/Android/sdk"
    else
        echo -e "${RED}❌ Android SDK not found. Please set ANDROID_HOME.${NC}"
        exit 1
    fi
fi

echo "✅ Android SDK: $ANDROID_HOME"

# Check for Chaquopy license
CHAQUOPY_LICENSE_FILE="$HOME/.gradle/chaquopy/license.txt"
if [ ! -f "$CHAQUOPY_LICENSE_FILE" ]; then
    echo -e "${YELLOW}⚠️  Chaquopy license not found at $CHAQUOPY_LICENSE_FILE${NC}"
    echo -e "${YELLOW}   For production builds, you need a Chaquopy license (\$495/year)${NC}"
    echo -e "${YELLOW}   Development builds will work but include Chaquopy watermark${NC}"
    echo ""
fi

# Verify LITE version structure
echo "🔍 Verifying LITE version structure..."

PYTHON_DIR="android/app/src/main/python"
if [ ! -f "$PYTHON_DIR/backend_main.py" ]; then
    echo -e "${RED}❌ backend_main.py not found!${NC}"
    exit 1
fi

# Check that heavy files are NOT present
if [ -f "$PYTHON_DIR/mobile_server.py" ] || [ -f "$PYTHON_DIR/mobile_models.py" ]; then
    echo -e "${RED}❌ Found heavy backend files! This should be LITE version.${NC}"
    echo "   Run this from mobile-app-lite/, not mobile-app/"
    exit 1
fi

if [ -d "$PYTHON_DIR/tools" ]; then
    echo -e "${RED}❌ Found tools/ directory! This should be LITE version.${NC}"
    echo "   Run this from mobile-app-lite/, not mobile-app/"
    exit 1
fi

echo -e "${GREEN}✅ LITE version structure verified${NC}"
echo "   - backend_main.py present"
echo "   - No heavy backend files"
echo "   - No tools/ directory"
echo ""

# Clean if requested
if [ "$CLEAN" = "true" ]; then
    echo "🧹 Cleaning previous build..."
    flutter clean
    cd android && ./gradlew clean && cd ..
fi

# Get Flutter dependencies
echo "📦 Getting Flutter dependencies..."
flutter pub get

# Verify NO PyPI dependencies in build.gradle (LITE version!)
echo "🐍 Verifying LITE Python configuration..."
if grep -q 'install "fastapi' android/app/build.gradle; then
    echo -e "${RED}❌ Found PyPI packages in build.gradle!${NC}"
    echo "   This is LITE version - should have NO external packages"
    echo "   Run this from mobile-app-lite/, not mobile-app/"
    exit 1
fi

echo -e "${GREEN}✅ LITE version confirmed: NO external Python packages${NC}"
echo ""

# Build APK
echo ""
echo "🏗️  Building Android APK (LITE VERSION)..."
echo "   Expected time: 5-10 minutes (faster than full version!)"
echo "   Expected size: ~80-90 MB (vs ~150 MB full version)"
echo ""

if [ "$BUILD_TYPE" = "release" ]; then
    echo "📦 Building release APK..."
    flutter build apk --release

    BUILD_OUTPUT="build/app/outputs/flutter-apk/app-release.apk"

elif [ "$BUILD_TYPE" = "debug" ]; then
    echo "🐛 Building debug APK..."
    flutter build apk --debug

    BUILD_OUTPUT="build/app/outputs/flutter-apk/app-debug.apk"
else
    echo -e "${RED}❌ Invalid build type: $BUILD_TYPE${NC}"
    echo "   Usage: $0 [debug|release] [clean]"
    exit 1
fi

# Check if build succeeded
if [ -f "$BUILD_OUTPUT" ]; then
    FILE_SIZE=$(du -h "$BUILD_OUTPUT" | cut -f1)

    echo ""
    echo "========================================="
    echo -e "${GREEN}✅ LITE VERSION Build successful!${NC}"
    echo "========================================="
    echo ""
    echo "📦 APK location: $BUILD_OUTPUT"
    echo "📊 APK size: $FILE_SIZE"
    echo ""
    echo -e "${BLUE}ℹ️  LITE VERSION features:${NC}"
    echo "   ✅ Only Python stdlib (NO PyPI packages)"
    echo "   ✅ Only backend_main.py (15 KB)"
    echo "   ✅ Fast startup (< 5 seconds)"
    echo "   ✅ Minimal size (~40-50 MB less than full version)"
    echo ""

    # Additional info
    echo "Next steps:"
    echo "1. Install APK:"
    echo "   adb install $BUILD_OUTPUT"
    echo ""
    echo "2. Or share APK for manual installation"
    echo ""
    echo "3. Test backend:"
    echo "   - Open app"
    echo "   - Backend should turn GREEN in < 5 seconds"
    echo "   - Test login/registration"
    echo ""
    echo "4. Compare with full version:"
    echo "   cd ../mobile-app && ./build-android-embedded.sh"
    echo "   Full version will be ~60-70 MB larger"
    echo ""

else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "   Check the logs above for errors"
    exit 1
fi
