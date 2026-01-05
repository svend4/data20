/**
 * Electron Main Process
 * Phase 7.1: Desktop Embedded Backend Integration
 *
 * This is the main entry point for the Electron desktop application.
 * It manages:
 * - Backend process lifecycle (automatic start/stop)
 * - Application window creation
 * - Menu and IPC handlers
 * - Settings and configuration
 */

const { app, BrowserWindow, ipcMain, Menu, dialog, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');
const BackendLauncher = require('./backend-launcher');
const AutoUpdater = require('./auto-updater');
const TrayManager = require('./tray-manager');
const PlatformIntegrations = require('./platform-integrations');

// Initialize electron-store for persistent settings
const store = new Store();

let mainWindow;
let backendLauncher;
let splashWindow;
let updater;
let trayManager;
let platformIntegrations;

// Check if running in development
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// Backend configuration
const BACKEND_PORT = store.get('backend.port', 8001);
const BACKEND_HOST = store.get('backend.host', '127.0.0.1');

/**
 * Create splash screen window
 */
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 300,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: true,
    },
  });

  // Create simple splash HTML
  const splashHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {
          margin: 0;
          padding: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
        }
        .container {
          text-align: center;
          padding: 40px;
        }
        h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 300;
        }
        .subtitle {
          margin-top: 10px;
          font-size: 14px;
          opacity: 0.9;
        }
        .loader {
          margin: 30px auto;
          width: 40px;
          height: 40px;
          border: 4px solid rgba(255,255,255,0.3);
          border-top: 4px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .status {
          margin-top: 20px;
          font-size: 12px;
          opacity: 0.8;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Data20 Knowledge Base</h1>
        <div class="subtitle">Desktop Application</div>
        <div class="loader"></div>
        <div class="status">Starting backend server...</div>
      </div>
    </body>
    </html>
  `;

  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHtml)}`);
}

/**
 * Close splash screen
 */
function closeSplashWindow() {
  if (splashWindow) {
    splashWindow.close();
    splashWindow = null;
  }
}

/**
 * Create main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: '#667eea',
    icon: path.join(__dirname, '../resources/icons/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
    },
    show: false, // Don't show until ready
  });

  // Load React app
  if (isDev) {
    // Development: load from Vite dev server
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load from built files
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    closeSplashWindow();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Create application menu
  createMenu();
}

/**
 * Create application menu
 */
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            showSettingsDialog();
          },
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Backend',
      submenu: [
        {
          label: 'Restart Backend',
          click: async () => {
            try {
              await backendLauncher.restart();
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Backend Restarted',
                message: 'The backend server has been restarted successfully.',
              });
            } catch (error) {
              dialog.showErrorBox('Backend Error', `Failed to restart backend: ${error.message}`);
            }
          },
        },
        {
          label: 'Check Backend Status',
          click: async () => {
            const status = await backendLauncher.checkHealth();
            const info = backendLauncher.getInfo();

            dialog.showMessageBox(mainWindow, {
              type: status.ready ? 'info' : 'warning',
              title: 'Backend Status',
              message: status.ready ? 'Backend is running' : 'Backend is offline',
              detail: [
                `Status: ${status.status}`,
                `URL: ${info.url}`,
                `Uptime: ${Math.floor(info.uptime / 1000)}s`,
                `Database: ${info.database}`,
                status.error ? `Error: ${status.error}` : ''
              ].filter(Boolean).join('\n'),
            });
          },
        },
        {
          label: 'View Backend Logs',
          click: () => {
            showBackendLogs();
          },
        },
        { type: 'separator' },
        {
          label: 'Open Database Location',
          click: () => {
            const info = backendLauncher.getInfo();
            shell.showItemInFolder(info.database);
          },
        },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/data20/docs');
          },
        },
        { type: 'separator' },
        {
          label: 'Check for Updates',
          click: () => {
            if (updater) {
              updater.checkForUpdatesAndNotify();
            } else {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Auto-Update',
                message: 'Auto-update is not available in development mode.',
              });
            }
          },
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => {
            const info = backendLauncher.getInfo();
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Data20 Knowledge Base',
              message: 'Data20 Knowledge Base v1.0.0',
              detail: [
                'Desktop application for managing data tools and workflows.',
                '',
                'Backend Information:',
                `URL: ${info.url}`,
                `Database: ${info.database}`,
                `Mode: ${isDev ? 'Development' : 'Production'}`,
              ].join('\n'),
            });
          },
        },
      ],
    },
  ];

  // macOS specific menu
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Show settings dialog
 */
function showSettingsDialog() {
  const info = backendLauncher.getInfo();

  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Settings',
    message: 'Backend Configuration',
    detail: [
      `Host: ${BACKEND_HOST}`,
      `Port: ${BACKEND_PORT}`,
      `Database: ${info.database}`,
      '',
      'To change settings, restart the application with different configuration.',
    ].join('\n'),
    buttons: ['OK'],
  });
}

/**
 * Show backend logs window
 */
function showBackendLogs() {
  const logs = backendLauncher.getLogs(100);

  const logsWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: false,
    title: 'Backend Logs',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  const logsHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {
          margin: 0;
          padding: 20px;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          background: #1e1e1e;
          color: #d4d4d4;
        }
        .log-entry {
          margin: 5px 0;
          padding: 5px;
          border-left: 3px solid #444;
        }
        .log-entry.stdout {
          border-left-color: #4caf50;
        }
        .log-entry.stderr {
          border-left-color: #f44336;
          color: #ff9999;
        }
        .log-entry.error {
          border-left-color: #ff5722;
          background: rgba(255, 87, 34, 0.1);
        }
        .timestamp {
          color: #888;
          margin-right: 10px;
        }
      </style>
    </head>
    <body>
      <h2>Backend Logs (Last 100 entries)</h2>
      ${logs.map(log => `
        <div class="log-entry ${log.source}">
          <span class="timestamp">${new Date(log.timestamp).toLocaleTimeString()}</span>
          <span>${log.message}</span>
        </div>
      `).join('')}
    </body>
    </html>
  `;

  logsWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(logsHtml)}`);
}

/**
 * IPC Handlers
 */

// Get backend URL
ipcMain.handle('get-backend-url', () => {
  return backendLauncher ? backendLauncher.getUrl() : null;
});

// Check backend status
ipcMain.handle('check-backend-status', async () => {
  return backendLauncher ? await backendLauncher.checkHealth() : { status: 'offline', ready: false };
});

// Get backend info
ipcMain.handle('get-backend-info', () => {
  return backendLauncher ? backendLauncher.getInfo() : null;
});

// Restart backend
ipcMain.handle('restart-backend', async () => {
  try {
    if (backendLauncher) {
      await backendLauncher.restart();
      return { success: true };
    }
    return { success: false, error: 'Backend not initialized' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get backend logs
ipcMain.handle('get-backend-logs', (event, count = 100) => {
  return backendLauncher ? backendLauncher.getLogs(count) : [];
});

// Get app version
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// Get platform info
ipcMain.handle('get-platform', () => {
  return {
    platform: process.platform,
    arch: process.arch,
    version: process.getSystemVersion(),
  };
});

// Store operations
ipcMain.handle('store-get', (event, key) => {
  return store.get(key);
});

ipcMain.handle('store-set', (event, key, value) => {
  store.set(key, value);
  return true;
});

ipcMain.handle('store-delete', (event, key) => {
  store.delete(key);
  return true;
});

// Auto-update handlers
ipcMain.handle('check-for-updates', async () => {
  if (updater) {
    return await updater.checkForUpdates();
  }
  return false;
});

ipcMain.handle('get-update-status', () => {
  if (updater) {
    return updater.getStatus();
  }
  return { enabled: false };
});

ipcMain.handle('install-update', () => {
  if (updater) {
    return updater.quitAndInstall();
  }
  return false;
});

// Tray and platform integration handlers
ipcMain.handle('tray-show-balloon', (event, title, content) => {
  if (trayManager) {
    trayManager.showBalloon(title, content);
    return true;
  }
  return false;
});

ipcMain.handle('platform-set-badge', (event, text) => {
  if (platformIntegrations) {
    platformIntegrations.setDockBadge(text);
    platformIntegrations.setBadgeCount(parseInt(text) || 0);
    return true;
  }
  return false;
});

ipcMain.handle('platform-set-progress', (event, progress) => {
  if (platformIntegrations) {
    platformIntegrations.setProgressBar(progress);
    return true;
  }
  return false;
});

/**
 * App lifecycle
 */

app.whenReady().then(async () => {
  console.log('🚀 Application starting...');
  console.log(`   Mode: ${isDev ? 'Development' : 'Production'}`);
  console.log(`   Platform: ${process.platform}`);

  try {
    // Show splash screen
    createSplashWindow();

    // Initialize auto-updater (only in production)
    if (!isDev) {
      console.log('🔄 Initializing auto-updater...');
      updater = new AutoUpdater({
        enabled: true,
        checkOnStart: true,
        notifyUser: true,
        autoDownload: true,
        autoInstallOnAppQuit: true,
      });
      console.log('✅ Auto-updater initialized');
    }

    // Initialize backend launcher
    console.log('📦 Initializing backend launcher...');
    backendLauncher = new BackendLauncher({
      port: BACKEND_PORT,
      host: BACKEND_HOST,
    });

    // Start backend
    console.log('🔌 Starting backend...');
    await backendLauncher.start();

    console.log('✅ Backend started successfully');

    // Create main window
    console.log('🪟 Creating main window...');
    createWindow();

    // Initialize system tray
    console.log('🔔 Initializing system tray...');
    trayManager = new TrayManager({
      mainWindow: mainWindow,
      backendLauncher: backendLauncher,
      minimizeToTray: store.get('tray.minimizeToTray', true),
    });
    console.log('✅ System tray initialized');

    // Initialize platform integrations
    console.log('🖥️  Initializing platform integrations...');
    platformIntegrations = new PlatformIntegrations({
      mainWindow: mainWindow,
      backendLauncher: backendLauncher,
      createWindow: createWindow,
    });
    console.log('✅ Platform integrations initialized');

    // Set main window reference for auto-updater
    if (updater) {
      updater.setMainWindow(mainWindow);

      // Check for updates after 3 seconds
      setTimeout(() => {
        console.log('🔍 Checking for updates...');
        updater.checkForUpdatesAndNotify();
      }, 3000);
    }

    console.log('✅ Application ready!');

  } catch (error) {
    console.error('❌ Failed to start application:', error);

    closeSplashWindow();

    // Show error dialog
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the application:\n\n${error.message}\n\nPlease check the logs and try again.`
    );

    // Quit app
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', async () => {
  console.log('🛑 Application shutting down...');

  if (backendLauncher) {
    console.log('   Stopping backend...');
    await backendLauncher.stop();
  }

  if (trayManager) {
    console.log('   Destroying system tray...');
    trayManager.destroy();
  }

  console.log('✅ Shutdown complete');
});

// Handle second instance (for Windows Jump List)
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // Someone tried to run a second instance, we should focus our window
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }

    // Handle Windows Jump List arguments
    if (platformIntegrations) {
      platformIntegrations.handleJumpListArgs(commandLine);
    }
  });
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);

  dialog.showErrorBox(
    'Unexpected Error',
    `An unexpected error occurred:\n\n${error.message}\n\nThe application will continue running, but some features may not work properly.`
  );
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});
