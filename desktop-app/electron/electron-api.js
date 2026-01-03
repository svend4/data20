/**
 * Electron API wrapper for React app
 * This file can be imported in the React app to access Electron features
 */

/**
 * Check if running in Electron
 */
export const isElectron = () => {
  return window.electron && window.electron.isElectron;
};

/**
 * Get backend URL from Electron configuration
 */
export const getBackendUrl = async () => {
  if (!isElectron()) {
    return window.location.origin;
  }
  return await window.electron.getBackendUrl();
};

/**
 * Check backend status
 */
export const checkBackendStatus = async () => {
  if (!isElectron()) {
    return { running: true };
  }
  return await window.electron.checkBackendStatus();
};

/**
 * Get app version
 */
export const getAppVersion = async () => {
  if (!isElectron()) {
    return 'web';
  }
  return await window.electron.getAppVersion();
};

/**
 * Get platform info
 */
export const getPlatform = async () => {
  if (!isElectron()) {
    return {
      platform: navigator.platform,
      userAgent: navigator.userAgent,
    };
  }
  return await window.electron.getPlatform();
};

/**
 * Electron store operations
 */
export const store = {
  get: async (key) => {
    if (!isElectron()) {
      return localStorage.getItem(key);
    }
    return await window.electron.store.get(key);
  },

  set: async (key, value) => {
    if (!isElectron()) {
      localStorage.setItem(key, value);
      return true;
    }
    return await window.electron.store.set(key, value);
  },

  delete: async (key) => {
    if (!isElectron()) {
      localStorage.removeItem(key);
      return true;
    }
    return await window.electron.store.delete(key);
  },
};

/**
 * Get platform name
 */
export const getPlatformName = () => {
  if (!isElectron()) {
    return 'web';
  }
  return window.electron.platform;
};

export default {
  isElectron,
  getBackendUrl,
  checkBackendStatus,
  getAppVersion,
  getPlatform,
  getPlatformName,
  store,
};
