/**
 * Auto-Updater Module
 * Phase 8.3.1: Automatic update checking and installation
 *
 * Features:
 * - Check for updates on startup
 * - Download updates in background
 * - Notify user when update is ready
 * - Seamless update installation
 * - Update progress tracking
 */

const { autoUpdater } = require('electron-updater');
const { dialog, BrowserWindow, Notification } = require('electron');
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

class AutoUpdater {
  constructor(options = {}) {
    this.mainWindow = null;
    this.enabled = options.enabled !== false;
    this.checkOnStart = options.checkOnStart !== false;
    this.notifyUser = options.notifyUser !== false;
    this.autoDownload = options.autoDownload !== false;
    this.autoInstallOnAppQuit = options.autoInstallOnAppQuit !== false;

    // Update status
    this.updateAvailable = false;
    this.updateDownloaded = false;
    this.updateInfo = null;
    this.downloadProgress = 0;

    this.init();
  }

  /**
   * Initialize auto-updater
   */
  init() {
    if (!this.enabled) {
      log.info('Auto-updater disabled');
      return;
    }

    log.info('Auto-updater initialized');

    // Configure auto-updater
    autoUpdater.autoDownload = this.autoDownload;
    autoUpdater.autoInstallOnAppQuit = this.autoInstallOnAppQuit;

    // Set up event listeners
    this.setupEventListeners();
  }

  /**
   * Set main window reference
   */
  setMainWindow(window) {
    this.mainWindow = window;
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Checking for update
    autoUpdater.on('checking-for-update', () => {
      log.info('Checking for update...');
      this.sendStatusToRenderer('checking-for-update');
    });

    // Update available
    autoUpdater.on('update-available', (info) => {
      log.info('Update available:', info);
      this.updateAvailable = true;
      this.updateInfo = info;
      this.sendStatusToRenderer('update-available', info);

      if (this.notifyUser) {
        this.notifyUpdateAvailable(info);
      }
    });

    // Update not available
    autoUpdater.on('update-not-available', (info) => {
      log.info('Update not available');
      this.sendStatusToRenderer('update-not-available', info);
    });

    // Error occurred
    autoUpdater.on('error', (error) => {
      log.error('Auto-updater error:', error);
      this.sendStatusToRenderer('error', { message: error.message });

      if (this.notifyUser) {
        this.notifyUpdateError(error);
      }
    });

    // Download progress
    autoUpdater.on('download-progress', (progressInfo) => {
      this.downloadProgress = progressInfo.percent;
      log.info(`Download progress: ${progressInfo.percent.toFixed(2)}%`);
      this.sendStatusToRenderer('download-progress', progressInfo);
    });

    // Update downloaded
    autoUpdater.on('update-downloaded', (info) => {
      log.info('Update downloaded');
      this.updateDownloaded = true;
      this.sendStatusToRenderer('update-downloaded', info);

      if (this.notifyUser) {
        this.notifyUpdateDownloaded(info);
      }
    });
  }

  /**
   * Check for updates
   */
  async checkForUpdates() {
    if (!this.enabled) {
      log.warn('Auto-updater is disabled');
      return false;
    }

    try {
      log.info('Manually checking for updates...');
      const result = await autoUpdater.checkForUpdates();
      return result != null;
    } catch (error) {
      log.error('Failed to check for updates:', error);
      return false;
    }
  }

  /**
   * Check for updates and notify
   */
  async checkForUpdatesAndNotify() {
    if (!this.enabled) {
      return;
    }

    try {
      await autoUpdater.checkForUpdatesAndNotify();
    } catch (error) {
      log.error('Failed to check for updates:', error);
    }
  }

  /**
   * Download update
   */
  async downloadUpdate() {
    if (!this.updateAvailable) {
      log.warn('No update available to download');
      return false;
    }

    try {
      log.info('Starting update download...');
      await autoUpdater.downloadUpdate();
      return true;
    } catch (error) {
      log.error('Failed to download update:', error);
      return false;
    }
  }

  /**
   * Install update and restart
   */
  quitAndInstall() {
    if (!this.updateDownloaded) {
      log.warn('No update downloaded to install');
      return false;
    }

    log.info('Installing update and restarting...');
    autoUpdater.quitAndInstall(false, true);
    return true;
  }

  /**
   * Send status to renderer process
   */
  sendStatusToRenderer(event, data = {}) {
    if (this.mainWindow && this.mainWindow.webContents) {
      this.mainWindow.webContents.send('auto-updater-status', {
        event,
        data,
        timestamp: new Date().toISOString(),
      });
    }
  }

  /**
   * Show notification that update is available
   */
  notifyUpdateAvailable(info) {
    const notification = new Notification({
      title: 'Update Available',
      body: `Version ${info.version} is available. Click to download.`,
      icon: null,
    });

    notification.on('click', () => {
      this.showUpdateDialog(info);
    });

    notification.show();
  }

  /**
   * Show notification that update is downloaded
   */
  notifyUpdateDownloaded(info) {
    const notification = new Notification({
      title: 'Update Ready',
      body: `Version ${info.version} has been downloaded. Click to install and restart.`,
      icon: null,
    });

    notification.on('click', () => {
      this.showInstallDialog(info);
    });

    notification.show();
  }

  /**
   * Show notification for update error
   */
  notifyUpdateError(error) {
    const notification = new Notification({
      title: 'Update Error',
      body: `Failed to check for updates: ${error.message}`,
      icon: null,
    });

    notification.show();
  }

  /**
   * Show dialog for available update
   */
  showUpdateDialog(info) {
    if (!this.mainWindow) return;

    const response = dialog.showMessageBoxSync(this.mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `A new version (${info.version}) is available!`,
      detail: [
        `Current version: ${require('../../package.json').version}`,
        `New version: ${info.version}`,
        '',
        'Release notes:',
        info.releaseNotes || 'No release notes available',
        '',
        'Would you like to download and install this update?',
      ].join('\n'),
      buttons: ['Download and Install', 'Remind Me Later', 'Skip This Version'],
      defaultId: 0,
      cancelId: 1,
    });

    switch (response) {
      case 0: // Download and install
        if (this.autoDownload) {
          // Already downloading
          this.showDownloadProgress();
        } else {
          this.downloadUpdate();
        }
        break;

      case 1: // Remind me later
        log.info('User chose to be reminded later');
        break;

      case 2: // Skip this version
        log.info(`User chose to skip version ${info.version}`);
        // TODO: Store skipped version
        break;
    }
  }

  /**
   * Show dialog for downloaded update
   */
  showInstallDialog(info) {
    if (!this.mainWindow) return;

    const response = dialog.showMessageBoxSync(this.mainWindow, {
      type: 'info',
      title: 'Update Ready to Install',
      message: `Version ${info.version} has been downloaded and is ready to install.`,
      detail: [
        'The application will restart to complete the installation.',
        '',
        'Do you want to install the update now?',
      ].join('\n'),
      buttons: ['Install and Restart', 'Install Later'],
      defaultId: 0,
      cancelId: 1,
    });

    if (response === 0) {
      this.quitAndInstall();
    }
  }

  /**
   * Show download progress window
   */
  showDownloadProgress() {
    if (!this.mainWindow) return;

    const message = `Downloading update... ${this.downloadProgress.toFixed(0)}%`;

    dialog.showMessageBox(this.mainWindow, {
      type: 'info',
      title: 'Downloading Update',
      message: message,
      detail: 'The update will be installed when the download is complete.',
      buttons: ['OK'],
    });
  }

  /**
   * Get update status
   */
  getStatus() {
    return {
      enabled: this.enabled,
      updateAvailable: this.updateAvailable,
      updateDownloaded: this.updateDownloaded,
      updateInfo: this.updateInfo,
      downloadProgress: this.downloadProgress,
    };
  }

  /**
   * Set configuration
   */
  setConfig(config) {
    if (config.enabled !== undefined) {
      this.enabled = config.enabled;
    }
    if (config.checkOnStart !== undefined) {
      this.checkOnStart = config.checkOnStart;
    }
    if (config.notifyUser !== undefined) {
      this.notifyUser = config.notifyUser;
    }
    if (config.autoDownload !== undefined) {
      this.autoDownload = config.autoDownload;
      autoUpdater.autoDownload = config.autoDownload;
    }
    if (config.autoInstallOnAppQuit !== undefined) {
      this.autoInstallOnAppQuit = config.autoInstallOnAppQuit;
      autoUpdater.autoInstallOnAppQuit = config.autoInstallOnAppQuit;
    }

    log.info('Auto-updater configuration updated:', config);
  }
}

module.exports = AutoUpdater;
