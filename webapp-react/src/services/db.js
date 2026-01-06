/**
 * IndexedDB Service for Data20 PWA
 * Phase 8.1.1: IndexedDB Caching Infrastructure
 *
 * This module provides a clean API for IndexedDB operations:
 * - Tools catalog caching
 * - Jobs history caching
 * - Offline queue management
 * - User preferences storage
 *
 * Database Schema:
 * - tools: Tool definitions and metadata
 * - jobs: Job execution history and results
 * - offlineQueue: Pending operations to sync when online
 * - cache: Generic key-value cache
 * - preferences: User settings and preferences
 *
 * Version: 1.0.0
 * Created: 2026-01-05
 */

const DB_NAME = 'data20-offline-db';
const DB_VERSION = 1;

/**
 * Object Store Names
 */
export const STORES = {
  TOOLS: 'tools',
  JOBS: 'jobs',
  OFFLINE_QUEUE: 'offlineQueue',
  CACHE: 'cache',
  PREFERENCES: 'preferences',
};

/**
 * IndexedDB wrapper class
 * Provides promise-based API for all database operations
 */
class Database {
  constructor() {
    this.db = null;
    this.opening = null; // Track open promise to avoid multiple opens
  }

  /**
   * Open database connection
   * Creates object stores if needed
   */
  async open() {
    // Return existing connection if already open
    if (this.db) {
      return this.db;
    }

    // Return pending open promise if already opening
    if (this.opening) {
      return this.opening;
    }

    // Start opening database
    this.opening = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        this.opening = null;
        reject(new Error(`Failed to open database: ${request.error}`));
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.opening = null;
        console.log('[DB] Database opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        console.log('[DB] Upgrading database schema...');

        // Create object stores if they don't exist

        // Tools store - indexed by tool name
        if (!db.objectStoreNames.contains(STORES.TOOLS)) {
          const toolsStore = db.createObjectStore(STORES.TOOLS, { keyPath: 'name' });
          toolsStore.createIndex('category', 'category', { unique: false });
          toolsStore.createIndex('updatedAt', 'updatedAt', { unique: false });
          console.log('[DB] Created tools store');
        }

        // Jobs store - indexed by job ID
        if (!db.objectStoreNames.contains(STORES.JOBS)) {
          const jobsStore = db.createObjectStore(STORES.JOBS, { keyPath: 'id' });
          jobsStore.createIndex('status', 'status', { unique: false });
          jobsStore.createIndex('toolName', 'toolName', { unique: false });
          jobsStore.createIndex('createdAt', 'createdAt', { unique: false });
          jobsStore.createIndex('completedAt', 'completedAt', { unique: false });
          console.log('[DB] Created jobs store');
        }

        // Offline queue store - for pending operations
        if (!db.objectStoreNames.contains(STORES.OFFLINE_QUEUE)) {
          const queueStore = db.createObjectStore(STORES.OFFLINE_QUEUE, {
            keyPath: 'id',
            autoIncrement: true,
          });
          queueStore.createIndex('type', 'type', { unique: false });
          queueStore.createIndex('status', 'status', { unique: false });
          queueStore.createIndex('createdAt', 'createdAt', { unique: false });
          queueStore.createIndex('priority', 'priority', { unique: false });
          console.log('[DB] Created offline queue store');
        }

        // Generic cache store - key-value pairs
        if (!db.objectStoreNames.contains(STORES.CACHE)) {
          db.createObjectStore(STORES.CACHE, { keyPath: 'key' });
          console.log('[DB] Created cache store');
        }

        // Preferences store - user settings
        if (!db.objectStoreNames.contains(STORES.PREFERENCES)) {
          db.createObjectStore(STORES.PREFERENCES, { keyPath: 'key' });
          console.log('[DB] Created preferences store');
        }

        console.log('[DB] Database schema upgraded to version', DB_VERSION);
      };
    });

    return this.opening;
  }

  /**
   * Close database connection
   */
  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log('[DB] Database closed');
    }
  }

  /**
   * Delete entire database (for debugging/reset)
   */
  async deleteDatabase() {
    this.close();
    return new Promise((resolve, reject) => {
      const request = indexedDB.deleteDatabase(DB_NAME);
      request.onsuccess = () => {
        console.log('[DB] Database deleted');
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generic get operation
   */
  async get(storeName, key) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(key);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generic put operation (insert or update)
   */
  async put(storeName, value) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.put(value);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generic delete operation
   */
  async delete(storeName, key) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(key);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all records from store
   */
  async getAll(storeName) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get records by index
   */
  async getAllByIndex(storeName, indexName, indexValue) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.getAll(indexValue);

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Clear all records from store
   */
  async clear(storeName) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Count records in store
   */
  async count(storeName, query) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = query ? store.count(query) : store.count();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Bulk put operation (insert/update multiple records)
   */
  async bulkPut(storeName, values) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);

      let completed = 0;
      let errors = [];

      values.forEach((value, index) => {
        const request = store.put(value);

        request.onsuccess = () => {
          completed++;
          if (completed === values.length) {
            if (errors.length > 0) {
              reject(new Error(`Failed to insert ${errors.length} records`));
            } else {
              resolve(completed);
            }
          }
        };

        request.onerror = () => {
          errors.push({ index, error: request.error });
          completed++;
          if (completed === values.length) {
            reject(new Error(`Failed to insert ${errors.length} records`));
          }
        };
      });

      // Handle empty array case
      if (values.length === 0) {
        resolve(0);
      }
    });
  }

  /**
   * Get database size estimate
   */
  async getStorageEstimate() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage,
        quota: estimate.quota,
        usagePercent: ((estimate.usage / estimate.quota) * 100).toFixed(2),
        usageMB: (estimate.usage / (1024 * 1024)).toFixed(2),
        quotaMB: (estimate.quota / (1024 * 1024)).toFixed(2),
      };
    }
    return null;
  }
}

// Create singleton instance
const db = new Database();

// Export singleton instance and class
export default db;
export { Database };

/**
 * High-level API functions for common operations
 */

// ============= TOOLS OPERATIONS =============

/**
 * Cache tools catalog
 */
export async function cacheTools(tools) {
  const toolsWithTimestamp = tools.map((tool) => ({
    ...tool,
    cachedAt: Date.now(),
    updatedAt: tool.updatedAt || Date.now(),
  }));

  await db.bulkPut(STORES.TOOLS, toolsWithTimestamp);
  console.log(`[DB] Cached ${tools.length} tools`);
  return toolsWithTimestamp.length;
}

/**
 * Get all cached tools
 */
export async function getCachedTools() {
  const tools = await db.getAll(STORES.TOOLS);
  console.log(`[DB] Retrieved ${tools.length} cached tools`);
  return tools;
}

/**
 * Get single tool by name
 */
export async function getCachedTool(toolName) {
  const tool = await db.get(STORES.TOOLS, toolName);
  return tool || null;
}

/**
 * Get tools by category
 */
export async function getToolsByCategory(category) {
  const tools = await db.getAllByIndex(STORES.TOOLS, 'category', category);
  return tools;
}

/**
 * Clear tools cache
 */
export async function clearToolsCache() {
  await db.clear(STORES.TOOLS);
  console.log('[DB] Tools cache cleared');
}

// ============= JOBS OPERATIONS =============

/**
 * Cache job result
 */
export async function cacheJob(job) {
  const jobWithTimestamp = {
    ...job,
    cachedAt: Date.now(),
  };

  await db.put(STORES.JOBS, jobWithTimestamp);
  console.log(`[DB] Cached job ${job.id}`);
  return jobWithTimestamp;
}

/**
 * Get all cached jobs
 */
export async function getCachedJobs() {
  const jobs = await db.getAll(STORES.JOBS);
  console.log(`[DB] Retrieved ${jobs.length} cached jobs`);
  return jobs.sort((a, b) => b.createdAt - a.createdAt); // Sort by newest first
}

/**
 * Get single job by ID
 */
export async function getCachedJob(jobId) {
  const job = await db.get(STORES.JOBS, jobId);
  return job || null;
}

/**
 * Get jobs by status
 */
export async function getJobsByStatus(status) {
  const jobs = await db.getAllByIndex(STORES.JOBS, 'status', status);
  return jobs.sort((a, b) => b.createdAt - a.createdAt);
}

/**
 * Get jobs by tool name
 */
export async function getJobsByTool(toolName) {
  const jobs = await db.getAllByIndex(STORES.JOBS, 'toolName', toolName);
  return jobs.sort((a, b) => b.createdAt - a.createdAt);
}

/**
 * Clear jobs cache
 */
export async function clearJobsCache() {
  await db.clear(STORES.JOBS);
  console.log('[DB] Jobs cache cleared');
}

/**
 * Delete old jobs (keep last N days)
 */
export async function deleteOldJobs(daysToKeep = 30) {
  const cutoffDate = Date.now() - daysToKeep * 24 * 60 * 60 * 1000;
  const allJobs = await getCachedJobs();
  const oldJobs = allJobs.filter((job) => job.createdAt < cutoffDate);

  for (const job of oldJobs) {
    await db.delete(STORES.JOBS, job.id);
  }

  console.log(`[DB] Deleted ${oldJobs.length} old jobs`);
  return oldJobs.length;
}

// ============= OFFLINE QUEUE OPERATIONS =============

/**
 * Add item to offline queue
 */
export async function addToOfflineQueue(item) {
  const queueItem = {
    ...item,
    status: 'pending',
    createdAt: Date.now(),
    priority: item.priority || 0,
    retries: 0,
    maxRetries: item.maxRetries || 3,
  };

  const id = await db.put(STORES.OFFLINE_QUEUE, queueItem);
  console.log(`[DB] Added item to offline queue:`, id);
  return id;
}

/**
 * Get all pending queue items
 */
export async function getPendingQueueItems() {
  const items = await db.getAllByIndex(STORES.OFFLINE_QUEUE, 'status', 'pending');
  return items.sort((a, b) => b.priority - a.priority || a.createdAt - b.createdAt);
}

/**
 * Get all queue items
 */
export async function getAllQueueItems() {
  const items = await db.getAll(STORES.OFFLINE_QUEUE);
  return items.sort((a, b) => b.createdAt - a.createdAt);
}

/**
 * Update queue item status
 */
export async function updateQueueItemStatus(id, status, error = null) {
  const item = await db.get(STORES.OFFLINE_QUEUE, id);
  if (!item) {
    throw new Error(`Queue item ${id} not found`);
  }

  const updatedItem = {
    ...item,
    status,
    updatedAt: Date.now(),
  };

  if (error) {
    updatedItem.error = error;
    updatedItem.retries = (updatedItem.retries || 0) + 1;
  }

  if (status === 'completed') {
    updatedItem.completedAt = Date.now();
  }

  await db.put(STORES.OFFLINE_QUEUE, updatedItem);
  console.log(`[DB] Updated queue item ${id} status to ${status}`);
  return updatedItem;
}

/**
 * Remove item from queue
 */
export async function removeFromQueue(id) {
  await db.delete(STORES.OFFLINE_QUEUE, id);
  console.log(`[DB] Removed item ${id} from queue`);
}

/**
 * Clear completed queue items
 */
export async function clearCompletedQueue() {
  const items = await db.getAllByIndex(STORES.OFFLINE_QUEUE, 'status', 'completed');
  for (const item of items) {
    await db.delete(STORES.OFFLINE_QUEUE, item.id);
  }
  console.log(`[DB] Cleared ${items.length} completed queue items`);
  return items.length;
}

/**
 * Get queue statistics
 */
export async function getQueueStats() {
  const allItems = await getAllQueueItems();

  const stats = {
    total: allItems.length,
    pending: allItems.filter((i) => i.status === 'pending').length,
    processing: allItems.filter((i) => i.status === 'processing').length,
    completed: allItems.filter((i) => i.status === 'completed').length,
    failed: allItems.filter((i) => i.status === 'failed').length,
  };

  return stats;
}

// ============= CACHE OPERATIONS =============

/**
 * Set cache value
 */
export async function setCache(key, value, ttl = null) {
  const cacheItem = {
    key,
    value,
    createdAt: Date.now(),
    expiresAt: ttl ? Date.now() + ttl : null,
  };

  await db.put(STORES.CACHE, cacheItem);
  return cacheItem;
}

/**
 * Get cache value
 */
export async function getCache(key) {
  const item = await db.get(STORES.CACHE, key);

  if (!item) {
    return null;
  }

  // Check if expired
  if (item.expiresAt && item.expiresAt < Date.now()) {
    await db.delete(STORES.CACHE, key);
    return null;
  }

  return item.value;
}

/**
 * Delete cache key
 */
export async function deleteCache(key) {
  await db.delete(STORES.CACHE, key);
}

/**
 * Clear all cache
 */
export async function clearCache() {
  await db.clear(STORES.CACHE);
  console.log('[DB] Cache cleared');
}

// ============= PREFERENCES OPERATIONS =============

/**
 * Set user preference
 */
export async function setPreference(key, value) {
  const pref = {
    key,
    value,
    updatedAt: Date.now(),
  };

  await db.put(STORES.PREFERENCES, pref);
  return pref;
}

/**
 * Get user preference
 */
export async function getPreference(key, defaultValue = null) {
  const pref = await db.get(STORES.PREFERENCES, key);
  return pref ? pref.value : defaultValue;
}

/**
 * Get all preferences
 */
export async function getAllPreferences() {
  const prefs = await db.getAll(STORES.PREFERENCES);
  const prefsObj = {};

  prefs.forEach((pref) => {
    prefsObj[pref.key] = pref.value;
  });

  return prefsObj;
}

/**
 * Delete preference
 */
export async function deletePreference(key) {
  await db.delete(STORES.PREFERENCES, key);
}

/**
 * Clear all preferences
 */
export async function clearPreferences() {
  await db.clear(STORES.PREFERENCES);
  console.log('[DB] Preferences cleared');
}

// ============= UTILITY FUNCTIONS =============

/**
 * Get database statistics
 */
export async function getDatabaseStats() {
  const [
    toolsCount,
    jobsCount,
    queueCount,
    cacheCount,
    prefsCount,
    storageEstimate,
  ] = await Promise.all([
    db.count(STORES.TOOLS),
    db.count(STORES.JOBS),
    db.count(STORES.OFFLINE_QUEUE),
    db.count(STORES.CACHE),
    db.count(STORES.PREFERENCES),
    db.getStorageEstimate(),
  ]);

  return {
    stores: {
      tools: toolsCount,
      jobs: jobsCount,
      offlineQueue: queueCount,
      cache: cacheCount,
      preferences: prefsCount,
    },
    storage: storageEstimate,
    version: DB_VERSION,
  };
}

/**
 * Initialize database (call on app startup)
 */
export async function initializeDatabase() {
  try {
    await db.open();
    const stats = await getDatabaseStats();
    console.log('[DB] Database initialized:', stats);
    return stats;
  } catch (error) {
    console.error('[DB] Failed to initialize database:', error);
    throw error;
  }
}

/**
 * Export all data for backup
 */
export async function exportAllData() {
  const [tools, jobs, queue, cache, preferences] = await Promise.all([
    db.getAll(STORES.TOOLS),
    db.getAll(STORES.JOBS),
    db.getAll(STORES.OFFLINE_QUEUE),
    db.getAll(STORES.CACHE),
    db.getAll(STORES.PREFERENCES),
  ]);

  return {
    version: DB_VERSION,
    exportedAt: Date.now(),
    data: {
      tools,
      jobs,
      offlineQueue: queue,
      cache,
      preferences,
    },
  };
}

/**
 * Import data from backup
 */
export async function importAllData(backup) {
  if (backup.version !== DB_VERSION) {
    console.warn('[DB] Backup version mismatch, importing anyway');
  }

  const { data } = backup;

  await Promise.all([
    data.tools && db.bulkPut(STORES.TOOLS, data.tools),
    data.jobs && db.bulkPut(STORES.JOBS, data.jobs),
    data.offlineQueue && db.bulkPut(STORES.OFFLINE_QUEUE, data.offlineQueue),
    data.cache && db.bulkPut(STORES.CACHE, data.cache),
    data.preferences && db.bulkPut(STORES.PREFERENCES, data.preferences),
  ]);

  console.log('[DB] Data imported successfully');
}

console.log('[DB] IndexedDB service loaded');
