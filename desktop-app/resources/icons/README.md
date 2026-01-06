# Desktop App Icons

This directory contains icon resources for the Data20 desktop application.

## Required Icons

### Application Icon

**icon.png** - Main application icon (512x512 or 1024x1024)
- Used for app icon on all platforms
- Should be high resolution PNG

**icon.ico** - Windows application icon
- Multi-resolution ICO file (16x16, 32x32, 48x48, 256x256)
- Used for Windows executable and taskbar

**icon.icns** - macOS application icon
- Multi-resolution ICNS file
- Used for macOS app bundle

### System Tray Icons

**tray-icon.png** - Linux tray icon (16x16 or 32x32)
- Simple, monochrome design works best
- PNG format

**tray-icon.ico** - Windows tray icon (16x16 or 32x32)
- ICO format
- Simple design for small size

**tray-iconTemplate.png** - macOS tray icon (16x16 or 32x32)
- Template image (monochrome black on transparent)
- Must have "Template" suffix for macOS to apply theme colors
- Should be simple and recognizable at small sizes

### DMG Background (macOS)

**dmg-background.png** - DMG installer background (540x380)
- Used in macOS disk image installer
- Should include visual instructions for drag-to-install

## Icon Design Guidelines

### Application Icon
- Use the Data20 logo or brand colors
- Make it distinctive and recognizable
- Test at multiple sizes (512px down to 16px)
- Ensure it looks good in both light and dark modes

### Tray Icons
- **Simple and minimal** - they appear at 16x16 or 32x32 pixels
- **Monochrome for macOS** - use single color (black) on transparent background
- **Clear at small sizes** - avoid complex details
- **Recognizable** - should be identifiable as Data20 at a glance

### Best Practices
1. Use vector graphics (SVG) as source, export to required formats
2. Test icons at actual display sizes
3. Ensure good contrast for visibility
4. Test on both light and dark backgrounds
5. Keep designs consistent across platforms

## Generating Icons

### From PNG to ICO (Windows)
```bash
# Using ImageMagick
convert icon.png -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico
```

### From PNG to ICNS (macOS)
```bash
# Create iconset directory
mkdir icon.iconset

# Generate multiple sizes
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png

# Convert to icns
iconutil -c icns icon.iconset
```

### Automated with electron-builder
electron-builder can automatically generate icons from a single source file:
- Place `icon.png` (1024x1024) in the build directory
- electron-builder will generate all platform-specific icons

## Current Status

⚠️ **Placeholder icons needed** - Please add the following files:
- [ ] icon.png (1024x1024)
- [ ] icon.ico
- [ ] icon.icns
- [ ] tray-icon.png (32x32)
- [ ] tray-icon.ico (32x32)
- [ ] tray-iconTemplate.png (32x32)
- [ ] dmg-background.png (540x380)

## References

- [Electron Icon Requirements](https://www.electron.build/icons)
- [macOS Human Interface Guidelines - App Icons](https://developer.apple.com/design/human-interface-guidelines/macos/icons-and-images/app-icon/)
- [Windows Icon Guidelines](https://docs.microsoft.com/en-us/windows/win32/uxguide/vis-icons)
- [GNOME Icon Guidelines](https://developer.gnome.org/hig/guidelines/icons-and-artwork.html)
