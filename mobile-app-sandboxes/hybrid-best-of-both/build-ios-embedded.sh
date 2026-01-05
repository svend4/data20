#!/bin/bash

#
# Build iOS IPA with Embedded Python Backend
#
# This script builds the iOS application with PythonKit,
# embedding the Python FastAPI backend into the IPA.
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
echo "Building iOS IPA with Embedded Python"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Warning about PythonKit
echo ""
echo -e "${YELLOW}⚠️  WARNING: PythonKit support is EXPERIMENTAL${NC}"
echo -e "${YELLOW}   iOS App Store may reject apps with embedded Python${NC}"
echo -e "${YELLOW}   Consider using cloud backend for production iOS apps${NC}"
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
echo "🏗️  Building iOS IPA..."
echo "   This may take 15-30 minutes..."
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
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo "========================================="
    echo ""
    echo "📦 Output: $BUILD_OUTPUT"
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
        echo "⚠️  App Store Submission Notes:"
        echo "   - Embedded Python may be rejected"
        echo "   - Provide clear explanation in review notes"
        echo "   - Consider cloud backend alternative"
        echo ""
    else
        echo "Next steps:"
        echo ""
        echo "1. Run on simulator:"
        echo "   flutter run"
        echo ""
        echo "2. Or install on device via Xcode"
        echo ""
    fi

else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "   Check the logs above for errors"
    exit 1
fi
