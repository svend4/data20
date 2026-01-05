/**
 * React Hook for Service Worker Integration
 * Phase 8.1.4: Service Worker Integration
 *
 * Custom React hooks for service worker management and communication.
 * Provides easy-to-use hooks for React components.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  registerServiceWorker,
  unregisterServiceWorker,
  updateServiceWorker,
  skipWaiting,
  syncQueue,
  syncTools,
  syncJobs,
  getQueueStats as getQueueStatsUtil,
  clearCache as clearCacheUtil,
  getServiceWorkerState as getServiceWorkerStateUtil,
  isServiceWorkerSupported,
  addServiceWorkerListener,
} from '../utils/serviceWorker.js';

/**
 * Hook: useServiceWorker
 * Main service worker hook with registration and status
 *
 * @returns {object} Service worker state and controls
 *
 * @example
 * const { isRegistered, isActive, register, update } = useServiceWorker();
 */
export function useServiceWorker() {
  const [isRegistered, setIsRegistered] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkStatus = useCallback(async () => {
    try {
      const state = await getServiceWorkerStateUtil();
      setIsRegistered(state.registered);
      setIsActive(state.active);
      setLoading(false);
    } catch (err) {
      console.error('[useServiceWorker] Error checking status:', err);
      setError(err);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();

    // Listen for update available
    const removeListener = addServiceWorkerListener('sw-update-available', () => {
      setUpdateAvailable(true);
    });

    return removeListener;
  }, [checkStatus]);

  const register = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      await registerServiceWorker();
      await checkStatus();
      return true;
    } catch (err) {
      console.error('[useServiceWorker] Registration failed:', err);
      setError(err);
      setLoading(false);
      return false;
    }
  }, [checkStatus]);

  const unregister = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const success = await unregisterServiceWorker();
      await checkStatus();
      return success;
    } catch (err) {
      console.error('[useServiceWorker] Unregistration failed:', err);
      setError(err);
      setLoading(false);
      return false;
    }
  }, [checkStatus]);

  const update = useCallback(async () => {
    try {
      await updateServiceWorker();
      return true;
    } catch (err) {
      console.error('[useServiceWorker] Update failed:', err);
      setError(err);
      return false;
    }
  }, []);

  const applyUpdate = useCallback(() => {
    skipWaiting();
    setUpdateAvailable(false);
    // Reload page to activate new worker
    window.location.reload();
  }, []);

  return {
    isSupported: isServiceWorkerSupported(),
    isRegistered,
    isActive,
    updateAvailable,
    loading,
    error,
    register,
    unregister,
    update,
    applyUpdate,
    refresh: checkStatus,
  };
}

/**
 * Hook: useServiceWorkerSync
 * Handle service worker background sync
 *
 * @returns {object} Sync functions and state
 *
 * @example
 * const { syncAllData, syncing, lastSync } = useServiceWorkerSync();
 */
export function useServiceWorkerSync() {
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [error, setError] = useState(null);

  const syncAllData = useCallback(async () => {
    setSyncing(true);
    setError(null);

    try {
      await Promise.all([
        syncQueue(),
        syncTools(),
        syncJobs(),
      ]);

      setLastSync(new Date());
      console.log('[useServiceWorkerSync] All data synced successfully');
    } catch (err) {
      console.error('[useServiceWorkerSync] Sync failed:', err);
      setError(err);
    } finally {
      setSyncing(false);
    }
  }, []);

  const syncQueueOnly = useCallback(async () => {
    setSyncing(true);
    setError(null);

    try {
      await syncQueue();
      setLastSync(new Date());
    } catch (err) {
      console.error('[useServiceWorkerSync] Queue sync failed:', err);
      setError(err);
    } finally {
      setSyncing(false);
    }
  }, []);

  const syncToolsOnly = useCallback(async () => {
    setSyncing(true);
    setError(null);

    try {
      await syncTools();
      setLastSync(new Date());
    } catch (err) {
      console.error('[useServiceWorkerSync] Tools sync failed:', err);
      setError(err);
    } finally {
      setSyncing(false);
    }
  }, []);

  const syncJobsOnly = useCallback(async () => {
    setSyncing(true);
    setError(null);

    try {
      await syncJobs();
      setLastSync(new Date());
    } catch (err) {
      console.error('[useServiceWorkerSync] Jobs sync failed:', err);
      setError(err);
    } finally {
      setSyncing(false);
    }
  }, []);

  // Listen for sync completion events
  useEffect(() => {
    const removeListener = addServiceWorkerListener('queue-sync-completed', () => {
      setLastSync(new Date());
      setSyncing(false);
    });

    return removeListener;
  }, []);

  return {
    syncAllData,
    syncQueue: syncQueueOnly,
    syncTools: syncToolsOnly,
    syncJobs: syncJobsOnly,
    syncing,
    lastSync,
    error,
  };
}

/**
 * Hook: useServiceWorkerQueue
 * Monitor service worker queue status
 *
 * @param {number} pollInterval - Polling interval in ms (default: 5000)
 * @returns {object} Queue stats
 *
 * @example
 * const { queueStats, loading, refresh } = useServiceWorkerQueue();
 */
export function useServiceWorkerQueue(pollInterval = 5000) {
  const [queueStats, setQueueStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pollIntervalRef = useRef(null);

  const loadQueueStats = useCallback(async () => {
    try {
      const result = await getQueueStatsUtil();
      if (result.success) {
        setQueueStats(result.stats);
      } else {
        setError(new Error(result.error));
      }
      setLoading(false);
    } catch (err) {
      console.error('[useServiceWorkerQueue] Error loading stats:', err);
      setError(err);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueueStats();

    // Poll for updates
    if (pollInterval > 0) {
      pollIntervalRef.current = setInterval(loadQueueStats, pollInterval);
    }

    // Listen for queue sync events
    const removeListener = addServiceWorkerListener('queue-sync-completed', (event) => {
      loadQueueStats();
    });

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      removeListener();
    };
  }, [pollInterval, loadQueueStats]);

  return {
    queueStats,
    loading,
    error,
    refresh: loadQueueStats,
  };
}

/**
 * Hook: useServiceWorkerEvents
 * Listen to service worker events
 *
 * @param {string} eventType - Event type to listen for
 * @param {function} handler - Event handler
 *
 * @example
 * useServiceWorkerEvents('tools-synced', (event) => {
 *   console.log('Tools synced:', event.detail);
 * });
 */
export function useServiceWorkerEvents(eventType, handler) {
  useEffect(() => {
    if (!handler || !eventType) {
      return;
    }

    return addServiceWorkerListener(eventType, handler);
  }, [eventType, handler]);
}

/**
 * Hook: useServiceWorkerCache
 * Manage service worker cache
 *
 * @returns {object} Cache management functions
 *
 * @example
 * const { clearCache, clearing } = useServiceWorkerCache();
 */
export function useServiceWorkerCache() {
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState(null);

  const clearCache = useCallback(async () => {
    setClearing(true);
    setError(null);

    try {
      const result = await clearCacheUtil();
      if (!result.success) {
        throw new Error(result.error);
      }
      console.log('[useServiceWorkerCache] Cache cleared successfully');
    } catch (err) {
      console.error('[useServiceWorkerCache] Clear cache failed:', err);
      setError(err);
    } finally {
      setClearing(false);
    }
  }, []);

  return {
    clearCache,
    clearing,
    error,
  };
}

/**
 * Hook: useServiceWorkerStatus
 * Get detailed service worker status
 *
 * @param {number} refreshInterval - Auto-refresh interval in ms (0 = disabled)
 * @returns {object} Service worker state
 *
 * @example
 * const { state, refresh } = useServiceWorkerStatus();
 */
export function useServiceWorkerStatus(refreshInterval = 0) {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadState = useCallback(async () => {
    try {
      const swState = await getServiceWorkerStateUtil();
      setState(swState);
      setLoading(false);
    } catch (err) {
      console.error('[useServiceWorkerStatus] Error loading state:', err);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadState();

    if (refreshInterval > 0) {
      const intervalId = setInterval(loadState, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [refreshInterval, loadState]);

  return {
    state,
    loading,
    refresh: loadState,
  };
}

/**
 * Hook: useAutoSync
 * Automatically sync data when coming back online
 *
 * @param {boolean} enabled - Enable/disable auto-sync
 * @param {number} interval - Sync interval in ms when online
 *
 * @example
 * useAutoSync(true, 60000); // Sync every minute when online
 */
export function useAutoSync(enabled = true, interval = 60000) {
  const { isOnline } = useOnlineStatus();
  const lastSyncRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!enabled || !isOnline) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const doSync = async () => {
      try {
        await Promise.all([
          syncQueue(),
          syncTools(),
          syncJobs(),
        ]);
        lastSyncRef.current = new Date();
        console.log('[useAutoSync] Auto-sync completed');
      } catch (err) {
        console.error('[useAutoSync] Auto-sync failed:', err);
      }
    };

    // Sync immediately when coming online
    doSync();

    // Setup interval
    if (interval > 0) {
      intervalRef.current = setInterval(doSync, interval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, isOnline, interval]);

  return {
    lastSync: lastSyncRef.current,
  };
}

/**
 * Hook: useOnlineStatus
 * Track online/offline status
 *
 * @returns {object} Online status
 *
 * @example
 * const { isOnline, isOffline } = useOnlineStatus();
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    isOnline,
    isOffline: !isOnline,
  };
}

console.log('[useServiceWorker] Service worker hooks loaded');
