# Building Desktop App with Embedded Backend

## Phase 7.1: Desktop Embedded Backend

This guide explains how to build the Data20 Desktop Application with an embedded Python backend.

## Prerequisites

### Required Software

1. **Python 3.9+**
   ```bash
   python --version
   # Should show 3.9 or higher
   ```

2. **Node.js 18+**
   ```bash
   node --version
   npm --version
   ```

3. **PyInstaller**
   ```bash
   pip install pyinstaller
   ```

4. **Build Tools** (platform-specific)

   **Windows:**
   - Visual Studio Build Tools or Visual Studio 2019+
   - Windows SDK

   **macOS:**
   - Xcode Command Line Tools
   ```bash
   xcode-select --install
   ```

   **Linux:**
   ```bash
   sudo apt install build-essential  # Debian/Ubuntu
   sudo yum groupinstall "Development Tools"  # RHEL/CentOS
   ```

## Quick Start

### Option 1: Automatic Build (Recommended)

**Linux/macOS:**
```bash
cd desktop-app
chmod +x build-embedded.sh
./build-embedded.sh
```

**Windows:**
```cmd
cd desktop-app
build-embedded.bat
```

### Option 2: Manual Build

#### Step 1: Build Python Backend

```bash
# From project root
pyinstaller backend.spec
```

This creates `dist/data20-backend` (or `data20-backend.exe` on Windows).

#### Step 2: Build React Frontend

```bash
cd webapp-react
npm install
npm run build
cp -r build ../desktop-app/
```

#### Step 3: Build Electron App

```bash
cd desktop-app
npm install
npm run build
```

## Build Options

### Clean Build

Remove all previous build artifacts:

**Linux/macOS:**
```bash
./build-embedded.sh --clean
```

**Windows:**
```cmd
build-embedded.bat clean
```

### Platform-Specific Builds

**Windows only:**
```bash
./build-embedded.sh win
```

**macOS only:**
```bash
./build-embedded.sh mac
```

**Linux only:**
```bash
./build-embedded.sh linux
```

**All platforms** (requires all platform build tools):
```bash
./build-embedded.sh all
```

## Build Output

After successful build, you'll find installers in `desktop-app/dist/`:

### Windows

- `Data20 Knowledge Base-1.0.0-win-x64.exe` - NSIS installer
- `Data20 Knowledge Base-1.0.0-portable.exe` - Portable version

**Size:** ~180-220 MB

### macOS

- `Data20 Knowledge Base-1.0.0.dmg` - DMG installer
- `Data20 Knowledge Base-1.0.0-mac.zip` - ZIP archive

**Size:** ~170-200 MB

### Linux

- `Data20 Knowledge Base-1.0.0.AppImage` - AppImage (portable)
- `data20-knowledge-base_1.0.0_amd64.deb` - Debian package
- `data20-knowledge-base-1.0.0.x86_64.rpm` - RPM package

**Size:** ~160-190 MB

## Testing the Build

### 1. Test Backend Executable

```bash
# Test backend runs
./dist/data20-backend

# Should output:
# INFO:     Started server process
# INFO:     Uvicorn running on http://127.0.0.1:8001
```

### 2. Test Desktop App

**Development mode** (without building):
```bash
cd desktop-app
npm run dev
```

**Production build:**
- Install the generated installer
- Launch the application
- Verify backend starts automatically
- Check "Backend" menu → "Check Backend Status"

## Troubleshooting

### Backend Build Fails

**Problem:** `ModuleNotFoundError` during PyInstaller build

**Solution:**
```bash
# Make sure all dependencies are installed
pip install -r backend/requirements.txt
pip install -r requirements-standalone.txt

# Add missing modules to backend.spec hiddenimports
```

**Problem:** Backend exe is too large (>200MB)

**Solution:** Exclude unnecessary dependencies in `backend.spec`:
```python
excludes=[
    'celery',  # Not needed in standalone
    'redis',
    'matplotlib',  # Visualization libs
    'tk inter',
]
```

### React Build Fails

**Problem:** `npm run build` fails with memory error

**Solution:**
```bash
# Increase Node memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### Electron Build Fails

**Problem:** `electron-builder` fails with code signing error (macOS)

**Solution:** Disable code signing for development:
```yaml
# electron-builder.yml
mac:
  identity: null  # Disable signing
```

**Problem:** Windows Defender blocks the installer

**Solution:** The installer is not signed. Either:
1. Sign the installer with a code signing certificate
2. Add exception in Windows Defender
3. Use `--portable` build which doesn't require installation

### Backend Doesn't Start in App

**Problem:** App shows "Backend offline" error

**Solution:**

1. Check backend logs:
   - Menu → Backend → View Backend Logs

2. Verify backend executable exists:
   ```bash
   ls desktop-app/resources/backend/
   # Should show data20-backend executable
   ```

3. Test backend manually:
   ```bash
   ./desktop-app/resources/backend/data20-backend
   ```

4. Check permissions (Linux/macOS):
   ```bash
   chmod +x desktop-app/resources/backend/data20-backend
   ```

## Development Workflow

### Development Mode

For faster iteration during development:

```bash
# Terminal 1: Run backend directly
python backend/server.py

# Terminal 2: Run React dev server
cd webapp-react
npm run dev

# Terminal 3: Run Electron in dev mode
cd desktop-app
npm run dev
```

This allows hot reload without rebuilding.

### Production Build

Only build production installers when ready to distribute:

```bash
./build-embedded.sh
```

## Customization

### Change App Name/Version

Edit `desktop-app/package.json`:
```json
{
  "name": "data20-knowledge-base",
  "version": "1.0.0",
  "description": "Your description"
}
```

### Change App Icon

Replace icons in `desktop-app/resources/icons/`:
- `icon.ico` (Windows, 256x256)
- `icon.icns` (macOS, 512x512)
- `icon.png` (Linux, 512x512)

### Configure Backend

Edit `desktop-app/electron/backend-launcher.js`:
```javascript
buildEnvironment() {
  return {
    ...process.env,
    PORT: 8001,  // Change port
    LOG_LEVEL: 'DEBUG',  // Change log level
    // ... other settings
  };
}
```

## Distribution

### Windows

Upload to GitHub Releases or your website:
- `*.exe` installer (requires admin rights)
- `*-portable.exe` (no admin, no installation)

### macOS

1. **Notarize** (for Gatekeeper):
   ```bash
   xcrun notarytool submit Data20-1.0.0.dmg --keychain-profile "AC_PASSWORD"
   ```

2. Distribute via:
   - GitHub Releases
   - Website download
   - Mac App Store (requires additional config)

### Linux

Distribute via:
- GitHub Releases (AppImage, deb, rpm)
- Snap Store: `snapcraft`
- Flatpak: `flatpak-builder`

## Size Optimization

Current build sizes are:
- Windows: ~200 MB
- macOS: ~180 MB
- Linux: ~170 MB

To reduce size:

1. **Exclude unused Python packages:**
   ```python
   # backend.spec
   excludes=['matplotlib', 'pandas[test]', ...]
   ```

2. **Enable UPX compression:**
   ```python
   # backend.spec
   upx=True
   ```

3. **Minimize React bundle:**
   ```javascript
   // vite.config.js
   build: {
     minify: 'terser',
     terserOptions: {
       compress: {
         drop_console: true,
       }
     }
   }
   ```

4. **Use electron ASAR:**
   ```yaml
   # electron-builder.yml
   asar: true
   ```

## Next Steps

- **Phase 7.2:** PWA + Service Worker
- **Phase 7.3:** Mobile Embedded Backend
- **Phase 7.4:** Cloud Sync (Hybrid Mode)

## Support

For issues:
1. Check logs: Menu → Backend → View Backend Logs
2. Check GitHub Issues
3. Read full documentation in `PHASE_7_1_EMBEDDED_DESKTOP.md`
