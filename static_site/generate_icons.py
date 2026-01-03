#!/usr/bin/env python3
"""
PWA Icon Generator for Data20 Knowledge Base
Generates placeholder icons in various sizes for PWA manifest
"""

import os
from pathlib import Path

# SVG template for the icon
ICON_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="512" height="512" rx="80" fill="url(#grad)"/>

  <!-- Icon design: Database/Knowledge symbol -->
  <g transform="translate(256, 256)">
    <!-- Database cylinder (3 layers) -->
    <ellipse cx="0" cy="-80" rx="120" ry="35" fill="white" opacity="0.9"/>
    <rect x="-120" y="-80" width="240" height="60" fill="white" opacity="0.9"/>
    <ellipse cx="0" cy="-20" rx="120" ry="35" fill="white" opacity="0.9"/>

    <ellipse cx="0" cy="20" rx="120" ry="35" fill="white" opacity="0.7"/>
    <rect x="-120" y="20" width="240" height="60" fill="white" opacity="0.7"/>
    <ellipse cx="0" cy="80" rx="120" ry="35" fill="white" opacity="0.7"/>

    <!-- Number "20" overlay -->
    <text x="-50" y="30" font-family="Arial, sans-serif" font-size="80" font-weight="bold" fill="#667eea">20</text>
  </g>

  <!-- Border -->
  <rect width="512" height="512" rx="80" fill="none" stroke="white" stroke-width="8" opacity="0.3"/>
</svg>
"""

# Sizes needed for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def generate_svg_icons():
    """Generate SVG icons in various sizes"""
    # Create icons directory
    icons_dir = Path(__file__).parent / 'public' / 'assets' / 'icons'
    icons_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎨 Generating PWA icons in {icons_dir}")

    for size in ICON_SIZES:
        svg_content = ICON_SVG.format(size=size)
        svg_path = icons_dir / f'icon-{size}x{size}.svg'

        with open(svg_path, 'w') as f:
            f.write(svg_content)

        print(f"  ✅ Created {svg_path.name}")

    # Also create favicon.ico (as SVG for simplicity)
    favicon_path = Path(__file__).parent / 'public' / 'favicon.svg'
    with open(favicon_path, 'w') as f:
        f.write(ICON_SVG.format(size=32))
    print(f"  ✅ Created favicon.svg")

    print(f"\n✨ Generated {len(ICON_SIZES)} icon sizes")
    print("\n📝 Note: SVG icons are used as placeholders.")
    print("   For production, consider converting to PNG using:")
    print("   - Online tools: https://cloudconvert.com/svg-to-png")
    print("   - ImageMagick: convert icon.svg -resize 512x512 icon.png")
    print("   - Inkscape: inkscape icon.svg --export-png=icon.png -w 512 -h 512")

    return icons_dir

def create_png_fallback_script():
    """Create a helper script for PNG conversion"""
    script_path = Path(__file__).parent / 'convert_icons_to_png.sh'

    script_content = """#!/bin/bash
# Convert SVG icons to PNG using ImageMagick or Inkscape
# Usage: ./convert_icons_to_png.sh

ICONS_DIR="public/assets/icons"
SIZES=(72 96 128 144 152 192 384 512)

echo "🎨 Converting SVG icons to PNG..."

# Check for ImageMagick
if command -v convert &> /dev/null; then
    echo "Using ImageMagick..."
    for size in "${SIZES[@]}"; do
        convert "$ICONS_DIR/icon-${size}x${size}.svg" \
                -resize ${size}x${size} \
                "$ICONS_DIR/icon-${size}x${size}.png"
        echo "  ✅ Created icon-${size}x${size}.png"
    done

# Check for Inkscape
elif command -v inkscape &> /dev/null; then
    echo "Using Inkscape..."
    for size in "${SIZES[@]}"; do
        inkscape "$ICONS_DIR/icon-${size}x${size}.svg" \
                 --export-filename="$ICONS_DIR/icon-${size}x${size}.png" \
                 --export-width=$size \
                 --export-height=$size
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
"""

    with open(script_path, 'w') as f:
        f.write(script_content)

    # Make executable
    os.chmod(script_path, 0o755)

    print(f"\n📄 Created conversion script: {script_path}")
    print("   Run with: ./static_site/convert_icons_to_png.sh")

def update_manifest_for_svg():
    """Update manifest.json to use SVG icons as fallback"""
    manifest_path = Path(__file__).parent / 'public' / 'manifest.json'

    if not manifest_path.exists():
        return

    import json

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Update icons to include SVG fallbacks
    for icon in manifest.get('icons', []):
        size = icon['sizes'].split('x')[0]
        # Keep PNG as primary, but note SVG exists
        icon['src_svg'] = f"/assets/icons/icon-{size}x{size}.svg"

    # Add any-purpose SVG icon
    manifest['icons'].append({
        "src": "/assets/icons/icon-512x512.svg",
        "sizes": "any",
        "type": "image/svg+xml",
        "purpose": "any"
    })

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Updated {manifest_path.name} with SVG references")

def main():
    print("=" * 60)
    print("PWA Icon Generator for Data20 Knowledge Base")
    print("=" * 60)

    # Generate SVG icons
    icons_dir = generate_svg_icons()

    # Create PNG conversion helper script
    create_png_fallback_script()

    # Update manifest
    update_manifest_for_svg()

    print("\n" + "=" * 60)
    print("✅ Icon generation complete!")
    print("=" * 60)
    print(f"\nIcons location: {icons_dir}")
    print("\nNext steps:")
    print("  1. [Optional] Convert SVG to PNG for better browser support")
    print("     Run: ./static_site/convert_icons_to_png.sh")
    print("  2. Test PWA installation on your device")
    print("  3. Customize icon design in generate_icons.py if needed")

if __name__ == '__main__':
    main()
