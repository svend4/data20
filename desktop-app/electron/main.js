const { app, BrowserWindow, ipcMain, Menu, dialog, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');
const axios = require('axios');

// Initialize electron-store for persistent settings
const store = new Store();

let mainWindow;
let backendProcess = null;

// Check if running in development
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// Backend configuration
const BACKEND_PORT = store.get('backend.port', 8001);
const BACKEND_HOST = store.get('backend.host', 'localhost');
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

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
    icon: path.join(__dirname, '../build/icon.png'),
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
          label: 'Start Backend',
          click: () => {
            startBackend();
          },
        },
        {
          label: 'Stop Backend',
          click: () => {
            stopBackend();
          },
        },
        {
          label: 'Check Backend Status',
          click: async () => {
            const status = await checkBackendStatus();
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Backend Status',
              message: status.running ? 'Backend is running' : 'Backend is not running',
              detail: status.running ? `URL: ${BACKEND_URL}` : 'Please start the backend',
            });
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
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Data20 Knowledge Base',
              message: 'Data20 Knowledge Base v1.0.0',
              detail: 'Desktop application for managing data tools and workflows.',
            });
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Show settings dialog
 */
function showSettingsDialog() {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Settings',
    message: 'Backend Configuration',
    detail: `Host: ${BACKEND_HOST}\nPort: ${BACKEND_PORT}\n\nYou can modify these in the electron-store.`,
    buttons: ['OK'],
  });
}

/**
 * Check backend status
 */
async function checkBackendStatus() {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/tools`, {
      timeout: 2000,
    });
    return { running: true, data: response.data };
  } catch (error) {
    return { running: false, error: error.message };
  }
}

/**
 * Start backend server (if bundled)
 */
function startBackend() {
  // This would spawn the Python backend process
  // For now, show a message
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Start Backend',
    message: 'Backend Server',
    detail: 'Please start the backend manually:\n\npython run_standalone.py',
  });
}

/**
 * Stop backend server
 */
function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

/**
 * IPC Handlers
 */

// Get backend URL
ipcMain.handle('get-backend-url', () => {
  return BACKEND_URL;
});

// Check backend status
ipcMain.handle('check-backend-status', async () => {
  return await checkBackendStatus();
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

/**
 * App lifecycle
 */

app.whenReady().then(async () => {
  createWindow();

  // Check backend on startup
  const status = await checkBackendStatus();
  if (!status.running && !isDev) {
    dialog.showMessageBox(mainWindow, {
      type: 'warning',
      title: 'Backend Not Running',
      message: 'The backend server is not running.',
      detail: 'Please start the backend server to use the application.',
      buttons: ['OK'],
    });
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

app.on('before-quit', () => {
  stopBackend();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  dialog.showErrorBox('Error', `An error occurred: ${error.message}`);
});
