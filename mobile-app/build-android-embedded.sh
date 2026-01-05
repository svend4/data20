#!/bin/bash

#
# Build Android APK with Embedded Python Backend
#
# This script builds the Android application with Chaquopy,
# embedding the Python FastAPI backend into the APK.
#
# Requirements:
# - Android SDK
# - Android NDK
# - Chaquopy license (for production builds)
# - Python 3.9+
# - All dependencies from requirements.txt
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
echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║                                                                    ║${NC}"
echo -e "${MAGENTA}║${NC}  ${BOLD}${RED}███████╗██╗   ██╗██╗     ██╗         ██╗   ██╗███████╗██████╗ ███████╗${NC}  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║${NC}  ${BOLD}${RED}██╔════╝██║   ██║██║     ██║         ██║   ██║██╔════╝██╔══██╗██╔════╝${NC}  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║${NC}  ${BOLD}${RED}█████╗  ██║   ██║██║     ██║         ██║   ██║█████╗  ██████╔╝███████╗${NC}  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║${NC}  ${BOLD}${RED}██╔══╝  ██║   ██║██║     ██║         ╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║${NC}  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║${NC}  ${BOLD}${RED}██║     ╚██████╔╝███████╗███████╗     ╚████╔╝ ███████╗██║  ██║███████║${NC}  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║${NC}  ${BOLD}${RED}╚═╝      ╚═════╝ ╚══════╝╚══════╝      ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝${NC}  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║                                                                    ║${NC}"
echo -e "${MAGENTA}║${NC}          ${BOLD}${YELLOW}📱 Data20 Mobile - ПОЛНАЯ ВЕРСИЯ 🔧${NC}                  ${MAGENTA}║${NC}"
echo -e "${MAGENTA}║                                                                    ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}${YELLOW}🔧 Особенности ПОЛНОЙ версии:${NC}"
echo -e "   ${YELLOW}📦${NC} FastAPI + SQLAlchemy + 14 PyPI пакетов"
echo -e "   ${YELLOW}🛠️${NC}  50+ инструментов в tools/"
echo -e "   ${YELLOW}⚙️${NC}  Сложные модели (11 ORM классов)"
echo -e "   ${YELLOW}💾${NC} Размер APK: ${BOLD}~150 МБ${NC}"
echo ""
echo -e "${CYAN}ℹ️  Это ПОЛНАЯ версия для desktop/server!${NC}"
echo -e "${CYAN}   Для облегчённой Android версии: ../mobile-app-lite/build-android-embedded.sh${NC}"
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

# Clean if requested
if [ "$CLEAN" = "true" ]; then
    echo "🧹 Cleaning previous build..."
    flutter clean
    cd android && ./gradlew clean && cd ..
fi

# Get Flutter dependencies
echo "📦 Getting Flutter dependencies..."
flutter pub get

# Verify Python dependencies are listed in build.gradle
echo "🐍 Verifying Python dependencies..."
if grep -q "install \"fastapi" android/app/build.gradle; then
    echo "✅ Python dependencies configured in build.gradle"
else
    echo -e "${RED}❌ Python dependencies not found in android/app/build.gradle${NC}"
    echo "   Please ensure pip dependencies are configured in Chaquopy section"
    exit 1
fi

# Build APK
echo ""
echo "🏗️  Building Android APK..."
echo "   This may take 10-20 minutes (Chaquopy compiles Python)..."
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
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo "========================================="
    echo ""
    echo "📦 APK location: $BUILD_OUTPUT"
    echo "📊 APK size: $FILE_SIZE"
    echo ""
    echo "ℹ️  Note: APK includes embedded Python (~100MB)"
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
    echo "   - Navigate to Backend Status screen"
    echo "   - Verify backend starts successfully"
    echo ""

else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "   Check the logs above for errors"
    exit 1
fi
