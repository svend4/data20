/**
 * Platform-Specific Integrations
 * Phase 8.3.2: Native platform integrations
 *
 * Features:
 * - macOS Dock Menu
 * - Windows Jump List
 * - Linux Desktop Integration
 */

const { app, Menu } = require('electron');
const log = require('electron-log');
const path = require('path');

class PlatformIntegrations {
  constructor(options = {}) {
    this.mainWindow = options.mainWindow || null;
    this.backendLauncher = options.backendLauncher || null;
    this.createWindow = options.createWindow || null;

    this.init();
  }

  /**
   * Initialize platform-specific features
   */
  init() {
    const platform = process.platform;

    if (platform === 'darwin') {
      this.setupMacOSDock();
    } else if (platform === 'win32') {
      this.setupWindowsJumpList();
    } else if (platform === 'linux') {
      this.setupLinuxDesktop();
    }

    log.info(`Platform integrations initialized for ${platform}`);
  }

  /**
   * Set main window reference
   */
  setMainWindow(window) {
    this.mainWindow = window;
  }

  /**
   * Set backend launcher reference
   */
  setBackendLauncher(launcher) {
    this.backendLauncher = launcher;
  }

  /**
   * Set window creation function
   */
  setCreateWindow(fn) {
    this.createWindow = fn;
  }

  /**
   * Setup macOS Dock Menu
   */
  setupMacOSDock() {
    if (process.platform !== 'darwin') return;

    const dockMenu = Menu.buildFromTemplate([
      {
        label: 'New Window',
        click: () => {
          if (this.createWindow) {
            this.createWindow();
          }
        },
      },
      { type: 'separator' },
      {
        label: 'Backend',
        submenu: [
          {
            label: 'Check Status',
            click: async () => {
              if (this.backendLauncher && this.mainWindow) {
                const status = await this.backendLauncher.checkHealth();
                const { dialog } = require('electron');

                dialog.showMessageBox(this.mainWindow, {
                  type: status.ready ? 'info' : 'warning',
                  title: 'Backend Status',
                  message: status.ready ? 'Backend is running' : 'Backend is offline',
                  detail: `URL: ${this.backendLauncher.getUrl()}\nStatus: ${status.status}`,
                });
              }
            },
          },
          {
            label: 'Restart Backend',
            click: async () => {
              if (this.backendLauncher) {
                try {
                  await this.backendLauncher.restart();

                  if (this.mainWindow) {
                    const { dialog } = require('electron');
                    dialog.showMessageBox(this.mainWindow, {
                      type: 'info',
                      title: 'Backend Restarted',
                      message: 'The backend server has been restarted successfully.',
                    });
                  }
                } catch (error) {
                  log.error('Failed to restart backend from dock:', error);
                }
              }
            },
          },
        ],
      },
      { type: 'separator' },
      {
        label: 'Show All Windows',
        click: () => {
          const { BrowserWindow } = require('electron');
          BrowserWindow.getAllWindows().forEach(win => {
            win.show();
          });
        },
      },
    ]);

    app.dock.setMenu(dockMenu);
    log.info('macOS Dock menu configured');
  }

  /**
   * Setup Windows Jump List
   */
  setupWindowsJumpList() {
    if (process.platform !== 'win32') return;

    const jumpList = [
      {
        type: 'custom',
        name: 'Quick Actions',
        items: [
          {
            type: 'task',
            title: 'New Window',
            description: 'Open a new window',
            program: process.execPath,
            args: '--new-window',
            iconPath: process.execPath,
            iconIndex: 0,
          },
          {
            type: 'task',
            title: 'Check Backend',
            description: 'Check backend server status',
            program: process.execPath,
            args: '--check-backend',
            iconPath: process.execPath,
            iconIndex: 0,
          },
          {
            type: 'task',
            title: 'Restart Backend',
            description: 'Restart the backend server',
            program: process.execPath,
            args: '--restart-backend',
            iconPath: process.execPath,
            iconIndex: 0,
          },
        ],
      },
      {
        type: 'custom',
        name: 'Recent',
        items: [
          // This could be populated with recently accessed items
          // For now, we'll leave it empty
        ],
      },
    ];

    app.setUserTasks(jumpList[0].items);
    log.info('Windows Jump List configured');
  }

  /**
   * Setup Linux Desktop Integration
   */
  setupLinuxDesktop() {
    if (process.platform !== 'linux') return;

    // Linux desktop integration is handled by the .desktop file
    // which is created during installation by electron-builder

    // We can set app user model ID for better integration
    app.setAppUserModelId('com.data20.knowledgebase');

    // Set badge count (shows in dock/taskbar on some Linux desktop environments)
    // This can be used to show notification count
    if (app.setBadgeCount) {
      app.setBadgeCount(0);
    }

    log.info('Linux desktop integration configured');
  }

  /**
   * Update macOS Dock badge
   */
  setDockBadge(text) {
    if (process.platform === 'darwin' && app.dock) {
      app.dock.setBadge(text);
    }
  }

  /**
   * Set macOS Dock icon bounce
   */
  bounceDock(type = 'informational') {
    if (process.platform === 'darwin' && app.dock) {
      // type can be 'critical' or 'informational'
      app.dock.bounce(type);
    }
  }

  /**
   * Show/hide macOS Dock icon
   */
  setDockVisible(visible) {
    if (process.platform === 'darwin' && app.dock) {
      if (visible) {
        app.dock.show();
      } else {
        app.dock.hide();
      }
    }
  }

  /**
   * Set Windows taskbar progress bar
   */
  setProgressBar(progress) {
    if (this.mainWindow) {
      // progress should be between 0 and 1
      // -1 removes the progress bar
      this.mainWindow.setProgressBar(progress);
    }
  }

  /**
   * Flash Windows taskbar
   */
  flashFrame(flag = true) {
    if (this.mainWindow) {
      this.mainWindow.flashFrame(flag);
    }
  }

  /**
   * Set Windows overlay icon
   */
  setOverlayIcon(icon, description = '') {
    if (process.platform === 'win32' && this.mainWindow) {
      // icon should be a NativeImage or path to icon file
      // Pass null to remove overlay icon
      this.mainWindow.setOverlayIcon(icon, description);
    }
  }

  /**
   * Set Linux badge count
   */
  setBadgeCount(count) {
    if (process.platform === 'linux' && app.setBadgeCount) {
      app.setBadgeCount(count);
    }
  }

  /**
   * Handle command-line arguments for Windows Jump List
   */
  handleJumpListArgs(argv) {
    if (process.platform !== 'win32') return;

    // Check for custom arguments from Jump List
    if (argv.includes('--new-window')) {
      log.info('Opening new window from Jump List');
      if (this.createWindow) {
        this.createWindow();
      }
    }

    if (argv.includes('--check-backend')) {
      log.info('Checking backend from Jump List');
      if (this.backendLauncher && this.mainWindow) {
        setTimeout(async () => {
          const status = await this.backendLauncher.checkHealth();
          const { dialog } = require('electron');

          dialog.showMessageBox(this.mainWindow, {
            type: status.ready ? 'info' : 'warning',
            title: 'Backend Status',
            message: status.ready ? 'Backend is running' : 'Backend is offline',
            detail: `URL: ${this.backendLauncher.getUrl()}\nStatus: ${status.status}`,
          });
        }, 1000);
      }
    }

    if (argv.includes('--restart-backend')) {
      log.info('Restarting backend from Jump List');
      if (this.backendLauncher) {
        setTimeout(async () => {
          try {
            await this.backendLauncher.restart();

            if (this.mainWindow) {
              const { dialog } = require('electron');
              dialog.showMessageBox(this.mainWindow, {
                type: 'info',
                title: 'Backend Restarted',
                message: 'The backend server has been restarted successfully.',
              });
            }
          } catch (error) {
            log.error('Failed to restart backend from Jump List:', error);
          }
        }, 1000);
      }
    }
  }
}

module.exports = PlatformIntegrations;
