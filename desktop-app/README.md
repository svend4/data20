# Data20 Desktop Application

Cross-platform desktop application for Data20 Knowledge Base built with Electron + React.

## Features

✅ **Native Desktop App**:
- Windows (exe, portable)
- macOS (dmg, app)
- Linux (AppImage, deb, rpm)

✅ **Integrated Backend**:
- Automatic backend status checking
- Settings management
- Persistent configuration

✅ **Modern UI**:
- React-based interface
- Native menus and dialogs
- System notifications
- Auto-updates (future)

✅ **Offline Capable**:
- Works without internet
- Local data storage
- Embedded backend option

## Architecture

```
desktop-app/
├── electron/
│   ├── main.js          # Main process (Node.js)
│   ├── preload.js       # Preload script (secure bridge)
│   └── electron-api.js  # API wrapper for React
├── build/               # Build resources
│   ├── icon.icns        # macOS icon
│   ├── icon.ico         # Windows icon
│   └── icon.png         # Linux icon
├── package.json         # Electron dependencies
└── README.md            # This file
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (for backend)
- React webapp already built (from ../webapp-react)

## Installation

```bash
cd desktop-app
npm install
```

## Development

### Option 1: With Separate Backend

```bash
# Terminal 1: Start backend
cd ..
python run_standalone.py

# Terminal 2: Start React dev server
cd webapp-react
npm run dev

# Terminal 3: Start Electron
cd desktop-app
npm run dev:electron
```

### Option 2: All-in-One

```bash
# Starts React dev server AND Electron
npm run dev
```

This will:
1. Start React dev server on `localhost:3000`
2. Wait for it to be ready
3. Launch Electron pointing to dev server
4. Enable hot reload for both React and Electron

## Building

### Build React App First

```bash
cd ../webapp-react
npm run build
```

This creates `dist/` folder with optimized React build.

### Copy to Desktop App

```bash
cd ../desktop-app
npm run build:react
```

This copies `webapp-react/dist/` to `desktop-app/build/`.

### Package Desktop App

```bash
# Package for current platform
npm run build:electron

# Or build for all platforms
npm run build:all

# Or specific platform
npm run build:mac     # macOS
npm run build:win     # Windows
npm run build:linux   # Linux
```

### Output

```
desktop-app/dist/
├── Data20 Knowledge Base-1.0.0.dmg          # macOS installer
├── Data20 Knowledge Base-1.0.0-mac.zip      # macOS zip
├── Data20 Knowledge Base Setup 1.0.0.exe    # Windows installer
├── Data20 Knowledge Base 1.0.0.exe          # Windows portable
├── Data20 Knowledge Base-1.0.0.AppImage     # Linux AppImage
├── data20-knowledge-base_1.0.0_amd64.deb    # Debian package
└── data20-knowledge-base-1.0.0.x86_64.rpm   # Red Hat package
```

## Distribution

### macOS

**DMG Installer** (~150 MB):
- Drag-and-drop installation
- Code signing (requires Apple Developer account)
- Notarization (for Gatekeeper)

**ZIP Archive** (~150 MB):
- Portable version
- No installer needed

### Windows

**NSIS Installer** (~140 MB):
- Traditional Windows installer
- Desktop and Start Menu shortcuts
- Add/Remove Programs integration
- Custom installation directory

**Portable EXE** (~140 MB):
- No installation required
- Run from USB drive
- Suitable for restricted environments

### Linux

**AppImage** (~160 MB):
- Universal Linux package
- No installation required
- Run on any Linux distribution
- Sandboxed execution

**Debian (.deb)** (~140 MB):
- For Ubuntu, Debian, Linux Mint
- APT package manager integration
- Install with: `sudo dpkg -i *.deb`

**Red Hat (.rpm)** (~140 MB):
- For Fedora, RHEL, CentOS
- YUM/DNF package manager integration
- Install with: `sudo rpm -i *.rpm`

## Configuration

### Backend Configuration

The app uses `electron-store` for persistent settings:

```javascript
// Default settings
{
  "backend": {
    "host": "localhost",
    "port": 8001
  }
}
```

**Location**:
- macOS: `~/Library/Application Support/data20-desktop/config.json`
- Windows: `%APPDATA%/data20-desktop/config.json`
- Linux: `~/.config/data20-desktop/config.json`

### Changing Backend URL

```javascript
// In Electron DevTools console or preload script
await window.electron.store.set('backend.host', '192.168.1.100');
await window.electron.store.set('backend.port', 8080);
```

Then restart the app.

## Menu Features

### File Menu

- **Settings** (Cmd/Ctrl+,) - View backend configuration
- **Quit** (Cmd/Ctrl+Q) - Exit application

### Edit Menu

Standard editing commands (undo, redo, cut, copy, paste, select all)

### View Menu

- **Reload** - Reload current page
- **Force Reload** - Clear cache and reload
- **Toggle DevTools** - Open developer tools
- **Zoom In/Out/Reset** - Adjust zoom level
- **Toggle Fullscreen** - Enter/exit fullscreen

### Backend Menu

- **Start Backend** - Start backend server (shows instructions)
- **Stop Backend** - Stop backend server
- **Check Backend Status** - Verify backend connection

### Help Menu

- **Documentation** - Open online documentation
- **About** - Show app version and info

## IPC Communication

The app uses Electron's IPC for secure communication between React and Electron:

### Available APIs

```javascript
// Get backend URL
const url = await window.electron.getBackendUrl();
// → "http://localhost:8001"

// Check backend status
const status = await window.electron.checkBackendStatus();
// → { running: true, data: [...] }

// Get app version
const version = await window.electron.getAppVersion();
// → "1.0.0"

// Get platform info
const platform = await window.electron.getPlatform();
// → { platform: 'darwin', arch: 'x64', version: '...' }

// Store operations
await window.electron.store.set('myKey', 'myValue');
const value = await window.electron.store.get('myKey');
await window.electron.store.delete('myKey');
```

### Using in React

```jsx
import { useEffect, useState } from 'react';

function App() {
  const [backendUrl, setBackendUrl] = useState('');

  useEffect(() => {
    // Check if running in Electron
    if (window.electron) {
      window.electron.getBackendUrl().then(setBackendUrl);
    }
  }, []);

  return <div>Backend: {backendUrl}</div>;
}
```

## Security

The app implements Electron security best practices:

✅ **Context Isolation**: Renderer process is isolated from Node.js
✅ **No Node Integration**: `nodeIntegration: false`
✅ **Preload Script**: Secure bridge between renderer and main
✅ **Content Security Policy**: Restricts script execution
✅ **Web Security**: Prevents loading remote content
✅ **External Links**: Opens in default browser, not in app

## Performance

### Bundle Size

- **macOS DMG**: ~150 MB
- **Windows Installer**: ~140 MB
- **Linux AppImage**: ~160 MB

**Breakdown**:
- Electron runtime: ~100 MB
- React app: ~1 MB (gzipped)
- Dependencies: ~39 MB
- Resources: ~10 MB

### Startup Time

- **Cold start**: ~2-3 seconds
- **Warm start**: ~1 second
- **To interactive**: ~500ms after window shows

### Memory Usage

- **Idle**: ~150 MB
- **Active**: ~200-300 MB
- **Multiple tools**: ~400-500 MB

## Troubleshooting

### "Backend Not Running"

The desktop app requires the backend server to be running.

**Solution**:
```bash
# Start backend manually
cd /path/to/data20
python run_standalone.py
```

Or configure to use remote backend:
```javascript
await window.electron.store.set('backend.host', 'your-server.com');
```

### "App Won't Open" (macOS)

macOS Gatekeeper blocks unsigned apps.

**Solution**:
1. Right-click app → Open
2. Click "Open" in dialog
3. Or: `xattr -cr "Data20 Knowledge Base.app"`

### "Missing DLL" (Windows)

Missing Visual C++ Redistributable.

**Solution**:
Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### DevTools Not Opening

**Solution**:
- Press `Cmd+Alt+I` (macOS) or `Ctrl+Shift+I` (Windows/Linux)
- Or: View → Toggle DevTools

### Build Fails

**Clear cache and rebuild**:
```bash
rm -rf node_modules dist build/dist
npm install
npm run build
```

## Auto-Updates (Future)

Planned features:
- Automatic update checking
- Background download
- Install on restart
- Update notifications

Using `electron-updater` with GitHub Releases.

## Code Signing (Production)

### macOS

Requires Apple Developer account ($99/year):

```bash
# Sign app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/mac/Data20 Knowledge Base.app"

# Notarize (for Gatekeeper)
xcrun altool --notarize-app \
  --primary-bundle-id "com.data20.knowledgebase" \
  --username "your@email.com" \
  --password "@keychain:AC_PASSWORD" \
  --file "dist/Data20 Knowledge Base-1.0.0.dmg"
```

### Windows

Requires Code Signing Certificate:

```bash
# Sign with SignTool
signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com /td sha256 "dist/Data20 Knowledge Base Setup 1.0.0.exe"
```

## Advanced

### Custom Electron Main Process

Edit `electron/main.js` to add custom functionality:

```javascript
// Add custom IPC handler
ipcMain.handle('my-custom-action', async (event, arg) => {
  // Your logic here
  return result;
});
```

Then use in React:
```javascript
const result = await window.electron.myCustomAction(arg);
```

### Bundling Backend

To bundle Python backend with Electron:

1. Use PyInstaller to create standalone executable
2. Include in `build/` directory
3. Spawn process in `electron/main.js`:

```javascript
const { spawn } = require('child_process');
const backendPath = path.join(__dirname, '../build/backend.exe');
const backend = spawn(backendPath);
```

## Contributing

See main project README for contribution guidelines.

## License

Same as Data20 Knowledge Base project.

## Support

- GitHub Issues: https://github.com/data20/issues
- Documentation: https://github.com/data20/docs
- Email: support@data20.com
