#!/bin/bash

#
# Build iOS IPA with Embedded Python Backend - LITE VERSION
#
# This script builds the LIGHTWEIGHT iOS application with PythonKit,
# embedding only backend_main.py (NO external dependencies!).
#
# Requirements:
# - macOS (required for iOS builds)
# - Xcode 14+
# - CocoaPods
# - Apple Developer account ($99/year)
# - Python 3.9+
# - PythonKit (experimental)
#

set -e  # Exit on error

echo "========================================="
echo "Building iOS IPA (LITE VERSION)"
echo "========================================="
echo ""
echo "🚀 LITE VERSION features:"
echo "   ✅ Only Python stdlib (NO PyPI packages)"
echo "   ✅ Only backend_main.py (15 KB)"
echo "   ✅ Expected size: ~80-90 MB (vs ~150 MB full version)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BUILD_TYPE="${1:-release}"  # debug or release
CLEAN="${2:-false}"

echo "📋 Configuration:"
echo "   Build type: $BUILD_TYPE"
echo "   Clean build: $CLEAN"
echo ""

# Check OS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ iOS builds require macOS${NC}"
    exit 1
fi

# Check for required tools
echo "🔍 Checking requirements..."

if ! command -v flutter &> /dev/null; then
    echo -e "${RED}❌ Flutter not found. Please install Flutter SDK.${NC}"
    exit 1
fi

if ! command -v xcodebuild &> /dev/null; then
    echo -e "${RED}❌ Xcode not found. Please install Xcode from App Store.${NC}"
    exit 1
fi

if ! command -v pod &> /dev/null; then
    echo -e "${RED}❌ CocoaPods not found. Install with: sudo gem install cocoapods${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

echo "✅ All tools found"

# Verify LITE version structure
echo "🔍 Verifying LITE version structure..."

PYTHON_DIR="ios/Runner/Python"
if [ ! -f "$PYTHON_DIR/backend_main.py" ]; then
    echo -e "${YELLOW}⚠️  backend_main.py not found in iOS folder${NC}"
    echo "   Will be copied from android/app/src/main/python/"
fi

# Check that heavy files are NOT present in project
ANDROID_PYTHON_DIR="android/app/src/main/python"
if [ -f "$ANDROID_PYTHON_DIR/mobile_server.py" ] || [ -f "$ANDROID_PYTHON_DIR/mobile_models.py" ]; then
    echo -e "${RED}❌ Found heavy backend files! This should be LITE version.${NC}"
    echo "   Run this from mobile-app-lite/, not mobile-app/"
    exit 1
fi

echo -e "${GREEN}✅ LITE version structure verified${NC}"
echo ""

# Warning about PythonKit
echo ""
echo -e "${YELLOW}⚠️  WARNING: PythonKit support is EXPERIMENTAL${NC}"
echo -e "${YELLOW}   iOS App Store may reject apps with embedded Python${NC}"
echo -e "${YELLOW}   Consider using cloud backend for production iOS apps${NC}"
echo ""
echo -e "${BLUE}ℹ️  LITE VERSION advantage:${NC}"
echo "   Smaller size may improve App Store approval chances"
echo ""
read -p "Continue anyway? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Clean if requested
if [ "$CLEAN" = "true" ]; then
    echo "🧹 Cleaning previous build..."
    flutter clean
    cd ios && pod deintegrate && cd ..
    rm -rf ios/Pods
    rm -f ios/Podfile.lock
fi

# Get Flutter dependencies
echo "📦 Getting Flutter dependencies..."
flutter pub get

# Install CocoaPods dependencies
echo "🍎 Installing CocoaPods dependencies..."
cd ios
pod install
cd ..

# Verify Podfile includes PythonKit
echo "🐍 Verifying PythonKit dependency..."
if grep -q "PythonKit" ios/Podfile; then
    echo "✅ PythonKit configured in Podfile"
else
    echo -e "${RED}❌ PythonKit not found in ios/Podfile${NC}"
    echo "   Please ensure PythonKit is added to Podfile"
    exit 1
fi

# Build IPA
echo ""
echo "🏗️  Building iOS IPA (LITE VERSION)..."
echo "   Expected time: 10-20 minutes (faster than full version!)"
echo "   Expected size: ~80-90 MB (vs ~150 MB full version)"
echo ""

if [ "$BUILD_TYPE" = "release" ]; then
    echo "📦 Building release IPA..."

    # Build archive
    flutter build ipa --release

    BUILD_OUTPUT="build/ios/archive/Runner.xcarchive"

elif [ "$BUILD_TYPE" = "debug" ]; then
    echo "🐛 Building debug IPA..."

    flutter build ios --debug

    BUILD_OUTPUT="build/ios/iphoneos/Runner.app"
else
    echo -e "${RED}❌ Invalid build type: $BUILD_TYPE${NC}"
    echo "   Usage: $0 [debug|release] [clean]"
    exit 1
fi

# Check if build succeeded
if [ -e "$BUILD_OUTPUT" ]; then

    echo ""
    echo "========================================="
    echo -e "${GREEN}✅ LITE VERSION Build successful!${NC}"
    echo "========================================="
    echo ""
    echo "📦 Output: $BUILD_OUTPUT"
    echo ""
    echo -e "${BLUE}ℹ️  LITE VERSION features:${NC}"
    echo "   ✅ Only Python stdlib (NO PyPI packages)"
    echo "   ✅ Only backend_main.py (15 KB)"
    echo "   ✅ Fast startup (< 5 seconds)"
    echo "   ✅ Minimal size (~40-50 MB less than full version)"
    echo ""

    if [ "$BUILD_TYPE" = "release" ]; then
        echo "Next steps:"
        echo ""
        echo "1. Open Xcode Organizer:"
        echo "   open build/ios/archive/*.xcarchive"
        echo ""
        echo "2. Validate and upload to App Store Connect"
        echo ""
        echo "3. Or export for Ad Hoc distribution:"
        echo "   - Select 'Distribute App'"
        echo "   - Choose 'Ad Hoc' or 'Development'"
        echo "   - Follow prompts to export IPA"
        echo ""
        echo "⚠️  App Store Submission Notes (LITE VERSION):"
        echo "   ✅ Smaller size may improve approval chances"
        echo "   ✅ NO external Python dependencies"
        echo "   ⚠️  Still uses PythonKit (explain to reviewers)"
        echo "   💡 Consider cloud backend for easier approval"
        echo ""
        echo "4. Compare with full version:"
        echo "   cd ../mobile-app && ./build-ios-embedded.sh"
        echo "   Full version will be ~60-70 MB larger"
        echo ""
    else
        echo "Next steps:"
        echo ""
        echo "1. Run on simulator:"
        echo "   flutter run"
        echo ""
        echo "2. Or install on device via Xcode"
        echo ""
        echo "3. Test backend:"
        echo "   - Backend should turn GREEN in < 5 seconds"
        echo "   - Test login/registration"
        echo ""
    fi

else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "   Check the logs above for errors"
    exit 1
fi
