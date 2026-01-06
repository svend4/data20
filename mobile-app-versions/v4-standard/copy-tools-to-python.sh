#!/bin/bash

#
# Copy tools directory to Python source for embedding in APK
#
# This script copies all tool files from the main tools/ directory
# to the Android Python source directory so they are included in the APK.
#

set -e

echo "========================================="
echo "Copying Tools to Python Source"
echo "========================================="
echo ""

# Source and destination
TOOLS_SRC="../tools"
TOOLS_DEST="android/app/src/main/python/tools"

# Check if source exists
if [ ! -d "$TOOLS_SRC" ]; then
    echo "❌ Tools directory not found: $TOOLS_SRC"
    echo "   Please run this script from mobile-app/ directory"
    exit 1
fi

# Create destination directory
mkdir -p "$TOOLS_DEST"

# Copy all Python tools
echo "📦 Copying tool files..."
cp -v "$TOOLS_SRC"/*.py "$TOOLS_DEST/" 2>/dev/null || echo "  (no .py files found)"

# Count copied files
TOOL_COUNT=$(ls -1 "$TOOLS_DEST"/*.py 2>/dev/null | wc -l)

echo ""
echo "========================================="
echo "✅ Done!"
echo "========================================="
echo ""
echo "📊 Copied $TOOL_COUNT tool files to:"
echo "   $TOOLS_DEST/"
echo ""
echo "These tools will be embedded in the APK during build."
echo ""
