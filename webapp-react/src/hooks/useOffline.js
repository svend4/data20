/**
 * React Hooks for Offline Features
 * Phase 8.1.2: React Hooks for Offline Features
 *
 * Custom hooks for easy integration of offline functionality:
 * - useOfflineStatus: Track online/offline status
 * - useOfflineTools: Get tools with offline caching
 * - useOfflineJobs: Get jobs with offline caching
 * - useOfflineQueue: Manage offline queue
 * - useOfflineStorage: General offline storage operations
 * - useOfflineSync: Handle sync operations
 *
 * Version: 1.0.0
 * Created: 2026-01-05
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import offlineStorage, { CACHE_STRATEGIES } from '../services/offlineStorage.js';
import offlineQueue, { QUEUE_EVENTS } from '../services/offlineQueue.js';
import { getDatabaseStats } from '../services/db.js';

/**
 * Hook: useOfflineStatus
 * Track network online/offline status
 *
 * @returns {object} { isOnline, isOffline }
 *
 * @example
 * const { isOnline, isOffline } = useOfflineStatus();
 */
export function useOfflineStatus() {
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

/**
 * Hook: useOfflineTools
 * Get tools catalog with offline caching
 *
 * @param {string} strategy - Cache strategy (default: CACHE_FIRST)
 * @param {object} options - Additional options
 * @returns {object} { tools, loading, error, refresh, clearCache }
 *
 * @example
 * const { tools, loading, error, refresh } = useOfflineTools();
 */
export function useOfflineTools(strategy = CACHE_STRATEGIES.CACHE_FIRST, options = {}) {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { autoRefresh = true } = options;

  const loadTools = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await offlineStorage.getTools(strategy);
      setTools(data);
    } catch (err) {
      console.error('[useOfflineTools] Error loading tools:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [strategy]);

  // Auto-load on mount
  useEffect(() => {
    loadTools();
  }, [loadTools]);

  // Listen for tools updates
  useEffect(() => {
    if (!autoRefresh) return;

    const handleUpdate = (updatedTools) => {
      setTools(updatedTools);
    };

    offlineStorage.on('tools:updated', handleUpdate);

    return () => {
      offlineStorage.off('tools:updated', handleUpdate);
    };
  }, [autoRefresh]);

  const refresh = useCallback(() => {
    return loadTools();
  }, [loadTools]);

  const clearCache = useCallback(async () => {
    await offlineStorage.clearToolsCache();
    await loadTools();
  }, [loadTools]);

  return {
    tools,
    loading,
    error,
    refresh,
    clearCache,
  };
}

/**
 * Hook: useOfflineTool
 * Get single tool with offline caching
 *
 * @param {string} toolName - Tool name
 * @param {string} strategy - Cache strategy
 * @returns {object} { tool, loading, error, refresh }
 *
 * @example
 * const { tool, loading, error } = useOfflineTool('statistics');
 */
export function useOfflineTool(toolName, strategy = CACHE_STRATEGIES.CACHE_FIRST) {
  const [tool, setTool] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadTool = useCallback(async () => {
    if (!toolName) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await offlineStorage.getTool(toolName, strategy);
      setTool(data);
    } catch (err) {
      console.error(`[useOfflineTool] Error loading tool ${toolName}:`, err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [toolName, strategy]);

  useEffect(() => {
    loadTool();
  }, [loadTool]);

  const refresh = useCallback(() => {
    return loadTool();
  }, [loadTool]);

  return {
    tool,
    loading,
    error,
    refresh,
  };
}

/**
 * Hook: useOfflineJobs
 * Get jobs list with offline caching
 *
 * @param {string} strategy - Cache strategy (default: CACHE_FIRST)
 * @param {object} options - Additional options
 * @returns {object} { jobs, loading, error, refresh, clearCache }
 *
 * @example
 * const { jobs, loading, error, refresh } = useOfflineJobs();
 */
export function useOfflineJobs(strategy = CACHE_STRATEGIES.CACHE_FIRST, options = {}) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { autoRefresh = true } = options;

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await offlineStorage.getJobs(strategy);
      setJobs(data);
    } catch (err) {
      console.error('[useOfflineJobs] Error loading jobs:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [strategy]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  // Listen for job updates
  useEffect(() => {
    if (!autoRefresh) return;

    const handleJobCreated = () => {
      loadJobs();
    };

    const handleJobQueued = () => {
      loadJobs();
    };

    offlineStorage.on('job:created', handleJobCreated);
    offlineStorage.on('job:queued', handleJobQueued);

    return () => {
      offlineStorage.off('job:created', handleJobCreated);
      offlineStorage.off('job:queued', handleJobQueued);
    };
  }, [autoRefresh, loadJobs]);

  const refresh = useCallback(() => {
    return loadJobs();
  }, [loadJobs]);

  const clearCache = useCallback(async () => {
    await offlineStorage.clearJobsCache();
    await loadJobs();
  }, [loadJobs]);

  return {
    jobs,
    loading,
    error,
    refresh,
    clearCache,
  };
}

/**
 * Hook: useOfflineJob
 * Get single job with offline caching
 *
 * @param {string} jobId - Job ID
 * @param {string} strategy - Cache strategy
 * @returns {object} { job, loading, error, refresh }
 *
 * @example
 * const { job, loading, error } = useOfflineJob('job-123');
 */
export function useOfflineJob(jobId, strategy = CACHE_STRATEGIES.CACHE_FIRST) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJob = useCallback(async () => {
    if (!jobId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await offlineStorage.getJob(jobId, strategy);
      setJob(data);
    } catch (err) {
      console.error(`[useOfflineJob] Error loading job ${jobId}:`, err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [jobId, strategy]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  const refresh = useCallback(() => {
    return loadJob();
  }, [loadJob]);

  return {
    job,
    loading,
    error,
    refresh,
  };
}

/**
 * Hook: useOfflineQueue
 * Manage offline queue
 *
 * @returns {object} Queue management functions and state
 *
 * @example
 * const { queueItems, pending, stats, sync, clear } = useOfflineQueue();
 */
export function useOfflineQueue() {
  const [queueItems, setQueueItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadQueue = useCallback(async () => {
    try {
      setLoading(true);

      const [items, queueStats] = await Promise.all([
        offlineQueue.getAll(),
        offlineQueue.getStats(),
      ]);

      setQueueItems(items);
      setStats(queueStats);
    } catch (err) {
      console.error('[useOfflineQueue] Error loading queue:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  // Listen for queue events
  useEffect(() => {
    const handleItemAdded = () => {
      loadQueue();
    };

    const handleItemCompleted = () => {
      loadQueue();
    };

    const handleItemFailed = () => {
      loadQueue();
    };

    const handleSyncStarted = () => {
      setSyncing(true);
    };

    const handleSyncCompleted = () => {
      setSyncing(false);
      loadQueue();
    };

    offlineQueue.on(QUEUE_EVENTS.ITEM_ADDED, handleItemAdded);
    offlineQueue.on(QUEUE_EVENTS.ITEM_COMPLETED, handleItemCompleted);
    offlineQueue.on(QUEUE_EVENTS.ITEM_FAILED, handleItemFailed);
    offlineQueue.on(QUEUE_EVENTS.SYNC_STARTED, handleSyncStarted);
    offlineQueue.on(QUEUE_EVENTS.SYNC_COMPLETED, handleSyncCompleted);

    return () => {
      offlineQueue.off(QUEUE_EVENTS.ITEM_ADDED, handleItemAdded);
      offlineQueue.off(QUEUE_EVENTS.ITEM_COMPLETED, handleItemCompleted);
      offlineQueue.off(QUEUE_EVENTS.ITEM_FAILED, handleItemFailed);
      offlineQueue.off(QUEUE_EVENTS.SYNC_STARTED, handleSyncStarted);
      offlineQueue.off(QUEUE_EVENTS.SYNC_COMPLETED, handleSyncCompleted);
    };
  }, [loadQueue]);

  const sync = useCallback(async () => {
    setSyncing(true);
    try {
      await offlineQueue.syncQueue();
    } finally {
      setSyncing(false);
      await loadQueue();
    }
  }, [loadQueue]);

  const clearCompleted = useCallback(async () => {
    await offlineQueue.clearCompleted();
    await loadQueue();
  }, [loadQueue]);

  const removeItem = useCallback(
    async (id) => {
      await offlineQueue.removeItem(id);
      await loadQueue();
    },
    [loadQueue]
  );

  const pendingItems = queueItems.filter((item) => item.status === 'pending');

  return {
    queueItems,
    pending: pendingItems,
    stats,
    syncing,
    loading,
    sync,
    clearCompleted,
    removeItem,
    refresh: loadQueue,
  };
}

/**
 * Hook: useOfflineStorage
 * General offline storage operations
 *
 * @returns {object} Storage management functions and state
 *
 * @example
 * const { executeTool, syncAll, stats, isOffline } = useOfflineStorage();
 */
export function useOfflineStorage() {
  const { isOnline, isOffline } = useOfflineStatus();
  const [stats, setStats] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const loadStats = useCallback(async () => {
    try {
      const dbStats = await getDatabaseStats();
      setStats(dbStats);
    } catch (err) {
      console.error('[useOfflineStorage] Error loading stats:', err);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const executeTool = useCallback(async (toolName, parameters) => {
    return offlineStorage.executeTool(toolName, parameters);
  }, []);

  const syncAll = useCallback(async () => {
    setSyncing(true);
    try {
      await offlineStorage.forceSync();
      await loadStats();
    } finally {
      setSyncing(false);
    }
  }, [loadStats]);

  const setPreference = useCallback(async (key, value) => {
    return offlineStorage.setPreference(key, value);
  }, []);

  const getPreference = useCallback(async (key, defaultValue) => {
    return offlineStorage.getPreference(key, defaultValue);
  }, []);

  return {
    executeTool,
    syncAll,
    setPreference,
    getPreference,
    stats,
    syncing,
    isOnline,
    isOffline,
    refreshStats: loadStats,
  };
}

/**
 * Hook: useOfflineSync
 * Handle sync operations with progress tracking
 *
 * @returns {object} { sync, syncing, lastSync, error }
 *
 * @example
 * const { sync, syncing, lastSync } = useOfflineSync();
 */
export function useOfflineSync() {
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [error, setError] = useState(null);
  const { isOnline } = useOfflineStatus();

  const sync = useCallback(async () => {
    if (!isOnline) {
      setError(new Error('Cannot sync while offline'));
      return;
    }

    setSyncing(true);
    setError(null);

    try {
      await offlineStorage.forceSync();
      setLastSync(new Date());
    } catch (err) {
      console.error('[useOfflineSync] Sync failed:', err);
      setError(err);
    } finally {
      setSyncing(false);
    }
  }, [isOnline]);

  // Auto-sync on reconnect
  useEffect(() => {
    if (isOnline) {
      sync();
    }
  }, [isOnline, sync]);

  return {
    sync,
    syncing,
    lastSync,
    error,
  };
}

/**
 * Hook: usePeriodicSync
 * Periodically sync data in background
 *
 * @param {number} interval - Sync interval in milliseconds (default: 60000 = 1 minute)
 * @param {boolean} enabled - Enable/disable periodic sync (default: true)
 *
 * @example
 * usePeriodicSync(60000); // Sync every minute
 */
export function usePeriodicSync(interval = 60000, enabled = true) {
  const { isOnline } = useOfflineStatus();
  const lastSyncRef = useRef(null);

  useEffect(() => {
    if (!enabled || !isOnline) {
      return;
    }

    const syncNow = async () => {
      try {
        await offlineStorage.backgroundSync();
        lastSyncRef.current = new Date();
      } catch (err) {
        console.error('[usePeriodicSync] Sync failed:', err);
      }
    };

    // Initial sync
    syncNow();

    // Setup interval
    const intervalId = setInterval(syncNow, interval);

    return () => {
      clearInterval(intervalId);
    };
  }, [interval, enabled, isOnline]);

  return {
    lastSync: lastSyncRef.current,
  };
}

/**
 * Hook: useOfflineToolExecution
 * Execute tool with automatic offline queuing
 *
 * @returns {object} { execute, executing, result, error }
 *
 * @example
 * const { execute, executing, result, error } = useOfflineToolExecution();
 * execute('statistics', { data: [1, 2, 3] });
 */
export function useOfflineToolExecution() {
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const execute = useCallback(async (toolName, parameters) => {
    setExecuting(true);
    setError(null);
    setResult(null);

    try {
      const response = await offlineStorage.executeTool(toolName, parameters);
      setResult(response);
      return response;
    } catch (err) {
      console.error('[useOfflineToolExecution] Execution failed:', err);
      setError(err);
      throw err;
    } finally {
      setExecuting(false);
    }
  }, []);

  return {
    execute,
    executing,
    result,
    error,
  };
}

/**
 * Hook: useNetworkSpeed
 * Monitor network connection speed (experimental)
 *
 * @returns {object} { effectiveType, downlink, rtt }
 *
 * @example
 * const { effectiveType, downlink } = useNetworkSpeed();
 */
export function useNetworkSpeed() {
  const [networkInfo, setNetworkInfo] = useState({
    effectiveType: 'unknown',
    downlink: null,
    rtt: null,
  });

  useEffect(() => {
    // Check if Network Information API is available
    if ('connection' in navigator || 'mozConnection' in navigator || 'webkitConnection' in navigator) {
      const connection =
        navigator.connection || navigator.mozConnection || navigator.webkitConnection;

      const updateNetworkInfo = () => {
        setNetworkInfo({
          effectiveType: connection.effectiveType || 'unknown',
          downlink: connection.downlink || null,
          rtt: connection.rtt || null,
        });
      };

      updateNetworkInfo();

      connection.addEventListener('change', updateNetworkInfo);

      return () => {
        connection.removeEventListener('change', updateNetworkInfo);
      };
    }
  }, []);

  return networkInfo;
}

console.log('[useOffline] Hooks loaded');
