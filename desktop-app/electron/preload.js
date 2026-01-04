const { contextBridge, ipcRenderer } = require('electron');

/**
 * Preload script
 * Exposes safe APIs to the renderer process
 */

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Backend operations
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  checkBackendStatus: () => ipcRenderer.invoke('check-backend-status'),

  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // Store operations (electron-store)
  store: {
    get: (key) => ipcRenderer.invoke('store-get', key),
    set: (key, value) => ipcRenderer.invoke('store-set', key, value),
    delete: (key) => ipcRenderer.invoke('store-delete', key),
  },

  // Platform info (read-only)
  platform: process.platform,
  isElectron: true,
});

// Log that preload script has loaded
console.log('Electron preload script loaded');
