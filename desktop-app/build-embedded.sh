#!/bin/bash

# ============================================================================
# Build Script for Embedded Desktop Application
# Phase 7.1: Desktop Embedded Backend
#
# This script builds the complete Data20 Desktop Application including:
# 1. Python backend (PyInstaller)
# 2. React frontend (Vite)
# 3. Electron wrapper
# 4. Platform-specific installers
#
# Usage:
#   ./build-embedded.sh              # Build for current platform
#   ./build-embedded.sh all          # Build for all platforms
#   ./build-embedded.sh win          # Windows only
#   ./build-embedded.sh mac          # macOS only
#   ./build-embedded.sh linux        # Linux only
#   ./build-embedded.sh --clean      # Clean build (remove all artifacts first)
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_APP_DIR="$PROJECT_ROOT/desktop-app"
BACKEND_DIR="$PROJECT_ROOT/backend"
DIST_DIR="$PROJECT_ROOT/dist"

# Parse arguments
CLEAN_BUILD=false
TARGET_PLATFORM=""

for arg in "$@"; do
  case $arg in
    --clean)
      CLEAN_BUILD=true
      shift
      ;;
    all|win|mac|linux)
      TARGET_PLATFORM=$arg
      shift
      ;;
    *)
      ;;
  esac
done

# Print header
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Data20 Desktop App - Embedded Build${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================================
# Step 0: Clean build (if requested)
# ============================================================================

if [ "$CLEAN_BUILD" = true ]; then
  echo -e "${YELLOW}🧹 Step 0: Clean Build${NC}"
  echo -e "${YELLOW}--------------------------------------${NC}"

  echo "Removing build artifacts..."
  rm -rf "$DIST_DIR"
  rm -rf "$DESKTOP_APP_DIR/dist"
  rm -rf "$DESKTOP_APP_DIR/build"
  rm -rf "$DESKTOP_APP_DIR/node_modules/.cache"

  echo -e "${GREEN}✅ Clean complete${NC}"
  echo ""
fi

# ============================================================================
# Step 1: Build Python Backend with PyInstaller
# ============================================================================

echo -e "${YELLOW}📦 Step 1: Building Python Backend${NC}"
echo -e "${YELLOW}--------------------------------------${NC}"

cd "$PROJECT_ROOT"

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
  echo -e "${RED}❌ PyInstaller not found${NC}"
  echo "Installing PyInstaller..."
  pip install pyinstaller
fi

# Check if backend.spec exists
if [ ! -f "backend.spec" ]; then
  echo -e "${RED}❌ backend.spec not found${NC}"
  echo "Please create backend.spec first"
  exit 1
fi

# Build backend
echo "Building backend executable..."
pyinstaller backend.spec

# Verify build
if [ -f "$DIST_DIR/data20-backend" ] || [ -f "$DIST_DIR/data20-backend.exe" ]; then
  echo -e "${GREEN}✅ Backend built successfully${NC}"
  ls -lh "$DIST_DIR"/data20-backend*
else
  echo -e "${RED}❌ Backend build failed${NC}"
  exit 1
fi

echo ""

# ============================================================================
# Step 2: Install Desktop App Dependencies
# ============================================================================

echo -e "${YELLOW}📥 Step 2: Installing Desktop App Dependencies${NC}"
echo -e "${YELLOW}--------------------------------------${NC}"

cd "$DESKTOP_APP_DIR"

if [ ! -d "node_modules" ]; then
  echo "Installing npm dependencies..."
  npm install
else
  echo "Dependencies already installed"
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ============================================================================
# Step 3: Build React Frontend
# ============================================================================

echo -e "${YELLOW}⚛️  Step 3: Building React Frontend${NC}"
echo -e "${YELLOW}--------------------------------------${NC}"

cd "$DESKTOP_APP_DIR"

# Check if React app directory exists
if [ ! -d "../webapp-react" ]; then
  echo -e "${RED}❌ React app not found at ../webapp-react${NC}"
  exit 1
fi

# Build React app
echo "Building React frontend..."
cd ../webapp-react

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing React dependencies..."
  npm install
fi

# Build
npm run build

# Copy build to desktop-app
echo "Copying React build to desktop-app..."
rm -rf "$DESKTOP_APP_DIR/build"
cp -r build "$DESKTOP_APP_DIR/"

echo -e "${GREEN}✅ React frontend built${NC}"
echo ""

# ============================================================================
# Step 4: Build Electron Application
# ============================================================================

echo -e "${YELLOW}🔌 Step 4: Building Electron Application${NC}"
echo -e "${YELLOW}--------------------------------------${NC}"

cd "$DESKTOP_APP_DIR"

# Determine target platforms
if [ -z "$TARGET_PLATFORM" ]; then
  # Auto-detect current platform
  case "$OSTYPE" in
    linux*)   TARGET_PLATFORM="linux" ;;
    darwin*)  TARGET_PLATFORM="mac" ;;
    msys*|win*) TARGET_PLATFORM="win" ;;
    *)
      echo -e "${RED}❌ Unsupported platform: $OSTYPE${NC}"
      exit 1
      ;;
  esac
  echo "Auto-detected platform: $TARGET_PLATFORM"
fi

# Build command
case "$TARGET_PLATFORM" in
  all)
    echo "Building for all platforms (Windows, macOS, Linux)..."
    npm run build -- -mwl
    ;;
  win)
    echo "Building for Windows..."
    npm run build -- --win
    ;;
  mac)
    echo "Building for macOS..."
    npm run build -- --mac
    ;;
  linux)
    echo "Building for Linux..."
    npm run build -- --linux
    ;;
  *)
    echo -e "${RED}❌ Unknown target platform: $TARGET_PLATFORM${NC}"
    exit 1
    ;;
esac

echo -e "${GREEN}✅ Electron app built${NC}"
echo ""

# ============================================================================
# Step 5: Summary
# ============================================================================

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Build Complete! 🎉${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

echo "📦 Build Artifacts:"
echo "--------------------------------------"

cd "$DESKTOP_APP_DIR/dist"

# List all built artifacts
if ls *.exe >/dev/null 2>&1; then
  echo -e "${GREEN}Windows:${NC}"
  ls -lh *.exe 2>/dev/null || true
  echo ""
fi

if ls *.dmg >/dev/null 2>&1 || ls *.pkg >/dev/null 2>&1; then
  echo -e "${GREEN}macOS:${NC}"
  ls -lh *.dmg *.pkg 2>/dev/null || true
  echo ""
fi

if ls *.AppImage >/dev/null 2>&1 || ls *.deb >/dev/null 2>&1 || ls *.rpm >/dev/null 2>&1; then
  echo -e "${GREEN}Linux:${NC}"
  ls -lh *.AppImage *.deb *.rpm 2>/dev/null || true
  echo ""
fi

# Total size
TOTAL_SIZE=$(du -sh . | cut -f1)
echo "Total build size: $TOTAL_SIZE"
echo ""

echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ All done!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the installer on your platform"
echo "2. Check that backend starts automatically"
echo "3. Verify all features work offline"
echo "4. Distribute the installer to users"
echo -e "${BLUE}============================================${NC}"
