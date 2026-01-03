#!/bin/bash
# Convert SVG icons to PNG using ImageMagick or Inkscape
# Usage: ./convert_icons_to_png.sh

ICONS_DIR="public/assets/icons"
SIZES=(72 96 128 144 152 192 384 512)

echo "🎨 Converting SVG icons to PNG..."

# Check for ImageMagick
if command -v convert &> /dev/null; then
    echo "Using ImageMagick..."
    for size in "${SIZES[@]}"; do
        convert "$ICONS_DIR/icon-${size}x${size}.svg"                 -resize ${size}x${size}                 "$ICONS_DIR/icon-${size}x${size}.png"
        echo "  ✅ Created icon-${size}x${size}.png"
    done

# Check for Inkscape
elif command -v inkscape &> /dev/null; then
    echo "Using Inkscape..."
    for size in "${SIZES[@]}"; do
        inkscape "$ICONS_DIR/icon-${size}x${size}.svg"                  --export-filename="$ICONS_DIR/icon-${size}x${size}.png"                  --export-width=$size                  --export-height=$size
        echo "  ✅ Created icon-${size}x${size}.png"
    done

else
    echo "❌ Neither ImageMagick nor Inkscape found"
    echo "Please install one of them:"
    echo "  - Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "  - macOS: brew install imagemagick"
    echo "  - Or use online converter: https://cloudconvert.com/svg-to-png"
    exit 1
fi

echo "✨ PNG icons generated successfully!"
