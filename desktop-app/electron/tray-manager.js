/**
 * System Tray Manager
 * Phase 8.3.2: Native platform integrations
 *
 * Features:
 * - System tray icon with context menu
 * - Minimize to tray
 * - Quick actions
 * - Status indicator
 * - Cross-platform support (Windows, macOS, Linux)
 */

const { Tray, Menu, nativeImage, app } = require('electron');
const path = require('path');
const log = require('electron-log');

class TrayManager {
  constructor(options = {}) {
    this.mainWindow = options.mainWindow || null;
    this.backendLauncher = options.backendLauncher || null;
    this.tray = null;
    this.contextMenu = null;
    this.iconPath = options.iconPath || this.getDefaultIconPath();
    this.minimizeToTray = options.minimizeToTray !== false;

    this.init();
  }

  /**
   * Get default icon path based on platform
   */
  getDefaultIconPath() {
    const platform = process.platform;

    if (platform === 'darwin') {
      // macOS uses Template images (monochrome)
      return path.join(__dirname, '../resources/icons/tray-iconTemplate.png');
    } else if (platform === 'win32') {
      // Windows uses .ico files
      return path.join(__dirname, '../resources/icons/tray-icon.ico');
    } else {
      // Linux uses PNG
      return path.join(__dirname, '../resources/icons/tray-icon.png');
    }
  }

  /**
   * Initialize system tray
   */
  init() {
    try {
      // Create tray icon
      const icon = nativeImage.createFromPath(this.iconPath);

      // Resize icon for proper display (16x16 for most platforms)
      const resizedIcon = icon.resize({ width: 16, height: 16 });

      this.tray = new Tray(resizedIcon);

      // Set tooltip
      this.tray.setToolTip('Data20 Knowledge Base');

      // Set initial context menu
      this.updateContextMenu();

      // Handle tray click (Windows/Linux - shows menu, macOS - custom behavior)
      this.tray.on('click', () => {
        this.handleTrayClick();
      });

      // Handle double-click (all platforms)
      this.tray.on('double-click', () => {
        this.showWindow();
      });

      log.info('System tray initialized successfully');
    } catch (error) {
      log.error('Failed to initialize system tray:', error);
    }
  }

  /**
   * Set main window reference
   */
  setMainWindow(window) {
    this.mainWindow = window;

    if (this.mainWindow && this.minimizeToTray) {
      // Handle minimize event
      this.mainWindow.on('minimize', (event) => {
        if (this.minimizeToTray) {
          event.preventDefault();
          this.mainWindow.hide();

          // Show notification on first minimize (only once per session)
          if (!this._minimizeNotificationShown) {
            this.tray.displayBalloon({
              title: 'Data20 Knowledge Base',
              content: 'App minimized to tray. Click the tray icon to restore.',
            });
            this._minimizeNotificationShown = true;
          }
        }
      });

      // Handle close event (hide instead of quit on some platforms)
      this.mainWindow.on('close', (event) => {
        if (!app.isQuitting && this.minimizeToTray && process.platform === 'darwin') {
          event.preventDefault();
          this.mainWindow.hide();
        }
      });
    }

    this.updateContextMenu();
  }

  /**
   * Set backend launcher reference
   */
  setBackendLauncher(launcher) {
    this.backendLauncher = launcher;
    this.updateContextMenu();
  }

  /**
   * Handle tray click
   */
  handleTrayClick() {
    if (process.platform === 'darwin') {
      // On macOS, clicking tray icon shows/hides window
      if (this.mainWindow) {
        if (this.mainWindow.isVisible()) {
          this.mainWindow.hide();
        } else {
          this.showWindow();
        }
      }
    } else {
      // On Windows/Linux, clicking shows the context menu
      // This is handled automatically by Electron
    }
  }

  /**
   * Show main window
   */
  showWindow() {
    if (this.mainWindow) {
      if (this.mainWindow.isMinimized()) {
        this.mainWindow.restore();
      }
      this.mainWindow.show();
      this.mainWindow.focus();
    }
  }

  /**
   * Hide main window
   */
  hideWindow() {
    if (this.mainWindow) {
      this.mainWindow.hide();
    }
  }

  /**
   * Update context menu
   */
  updateContextMenu() {
    const menuTemplate = [
      {
        label: 'Show Data20',
        click: () => {
          this.showWindow();
        },
        enabled: this.mainWindow !== null,
      },
      {
        label: 'Hide Data20',
        click: () => {
          this.hideWindow();
        },
        enabled: this.mainWindow !== null && this.mainWindow.isVisible(),
      },
      { type: 'separator' },
      {
        label: 'Backend',
        submenu: [
          {
            label: 'Check Status',
            click: async () => {
              if (this.backendLauncher) {
                const status = await this.backendLauncher.checkHealth();
                const statusText = status.ready ? '✅ Running' : '❌ Offline';
                this.tray.displayBalloon({
                  title: 'Backend Status',
                  content: `Status: ${statusText}\nURL: ${this.backendLauncher.getUrl()}`,
                });
              }
            },
            enabled: this.backendLauncher !== null,
          },
          {
            label: 'Restart Backend',
            click: async () => {
              if (this.backendLauncher) {
                try {
                  await this.backendLauncher.restart();
                  this.tray.displayBalloon({
                    title: 'Backend Restarted',
                    content: 'Backend server has been restarted successfully.',
                  });
                } catch (error) {
                  this.tray.displayBalloon({
                    title: 'Backend Error',
                    content: `Failed to restart: ${error.message}`,
                  });
                }
              }
            },
            enabled: this.backendLauncher !== null,
          },
        ],
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => {
          app.isQuitting = true;
          app.quit();
        },
      },
    ];

    this.contextMenu = Menu.buildFromTemplate(menuTemplate);
    this.tray.setContextMenu(this.contextMenu);
  }

  /**
   * Update tray icon
   */
  setIcon(iconPath) {
    if (this.tray) {
      const icon = nativeImage.createFromPath(iconPath);
      const resizedIcon = icon.resize({ width: 16, height: 16 });
      this.tray.setImage(resizedIcon);
    }
  }

  /**
   * Update tray tooltip
   */
  setTooltip(text) {
    if (this.tray) {
      this.tray.setToolTip(text);
    }
  }

  /**
   * Show balloon notification (Windows/Linux)
   */
  showBalloon(title, content) {
    if (this.tray && process.platform !== 'darwin') {
      this.tray.displayBalloon({
        title,
        content,
      });
    }
  }

  /**
   * Destroy tray
   */
  destroy() {
    if (this.tray) {
      this.tray.destroy();
      this.tray = null;
      log.info('System tray destroyed');
    }
  }
}

module.exports = TrayManager;
