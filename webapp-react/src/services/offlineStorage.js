/**
 * Offline Storage Service for Data20 PWA
 * Phase 8.1.1: IndexedDB Caching Infrastructure
 *
 * High-level API for offline data management:
 * - Tools catalog caching and sync
 * - Jobs history caching and sync
 * - Smart cache-first with background sync strategy
 * - Automatic cache invalidation
 * - Network-aware operations
 *
 * This service acts as the main interface between React components
 * and the underlying IndexedDB/Queue infrastructure.
 *
 * Version: 1.0.0
 * Created: 2026-01-05
 */

import {
  cacheTools,
  getCachedTools,
  getCachedTool,
  getToolsByCategory,
  clearToolsCache,
  cacheJob,
  getCachedJobs,
  getCachedJob,
  getJobsByStatus,
  getJobsByTool,
  clearJobsCache,
  deleteOldJobs,
  setCache,
  getCache,
  setPreference,
  getPreference,
  getAllPreferences,
  getDatabaseStats,
} from './db.js';

import { queueToolExecution, offlineQueue, QUEUE_EVENTS } from './offlineQueue.js';

import { apiRequest, API } from '../utils/api.js';

/**
 * Cache strategies
 */
export const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache_first', // Use cache, update in background
  NETWORK_FIRST: 'network_first', // Try network, fallback to cache
  CACHE_ONLY: 'cache_only', // Only use cache
  NETWORK_ONLY: 'network_only', // Only use network
};

/**
 * Cache TTL (time to live) defaults
 */
export const CACHE_TTL = {
  TOOLS: 24 * 60 * 60 * 1000, // 24 hours
  JOBS: 7 * 24 * 60 * 60 * 1000, // 7 days
  CATEGORIES: 24 * 60 * 60 * 1000, // 24 hours
};

/**
 * Offline Storage Manager
 */
class OfflineStorageManager {
  constructor() {
    this.syncInProgress = false;
    this.eventListeners = new Map();

    // Initialize
    this.initialize();
  }

  /**
   * Initialize storage manager
   */
  async initialize() {
    console.log('[OfflineStorage] Initializing...');

    try {
      // Get initial stats
      const stats = await getDatabaseStats();
      console.log('[OfflineStorage] Database stats:', stats);

      // Setup queue event listeners
      this.setupQueueListeners();

      // Trigger initial sync if online
      if (navigator.onLine) {
        this.backgroundSync();
      }

      console.log('[OfflineStorage] Initialized successfully');
    } catch (error) {
      console.error('[OfflineStorage] Initialization failed:', error);
    }
  }

  /**
   * Setup queue event listeners
   */
  setupQueueListeners() {
    offlineQueue.on(QUEUE_EVENTS.ITEM_COMPLETED, (data) => {
      this.emit('queue:completed', data);
    });

    offlineQueue.on(QUEUE_EVENTS.ITEM_FAILED, (data) => {
      this.emit('queue:failed', data);
    });

    offlineQueue.on(QUEUE_EVENTS.SYNC_COMPLETED, (data) => {
      this.emit('sync:completed', data);
    });
  }

  // ============= TOOLS OPERATIONS =============

  /**
   * Get tools catalog
   * Uses cache-first strategy with background sync
   */
  async getTools(strategy = CACHE_STRATEGIES.CACHE_FIRST) {
    console.log(`[OfflineStorage] Getting tools with strategy: ${strategy}`);

    switch (strategy) {
      case CACHE_STRATEGIES.CACHE_FIRST:
        return this.getToolsCacheFirst();

      case CACHE_STRATEGIES.NETWORK_FIRST:
        return this.getToolsNetworkFirst();

      case CACHE_STRATEGIES.CACHE_ONLY:
        return getCachedTools();

      case CACHE_STRATEGIES.NETWORK_ONLY:
        return this.fetchToolsFromNetwork();

      default:
        return this.getToolsCacheFirst();
    }
  }

  /**
   * Get tools - Cache First strategy
   * Returns cached data immediately, updates in background
   */
  async getToolsCacheFirst() {
    // Get from cache
    const cached = await getCachedTools();

    // Return cached data immediately
    if (cached && cached.length > 0) {
      console.log(`[OfflineStorage] Returning ${cached.length} cached tools`);

      // Update in background if online
      if (navigator.onLine) {
        this.updateToolsInBackground();
      }

      return cached;
    }

    // No cache, fetch from network
    console.log('[OfflineStorage] No cached tools, fetching from network');
    return this.fetchToolsFromNetwork();
  }

  /**
   * Get tools - Network First strategy
   * Tries network first, fallback to cache
   */
  async getToolsNetworkFirst() {
    if (!navigator.onLine) {
      console.log('[OfflineStorage] Offline, returning cached tools');
      return getCachedTools();
    }

    try {
      return await this.fetchToolsFromNetwork();
    } catch (error) {
      console.error('[OfflineStorage] Network failed, falling back to cache:', error);
      return getCachedTools();
    }
  }

  /**
   * Fetch tools from network and cache
   */
  async fetchToolsFromNetwork() {
    console.log('[OfflineStorage] Fetching tools from network');

    const tools = await apiRequest(API.tools);

    // Cache the results
    await cacheTools(tools);

    console.log(`[OfflineStorage] Fetched and cached ${tools.length} tools`);
    this.emit('tools:updated', tools);

    return tools;
  }

  /**
   * Update tools in background (fire and forget)
   */
  async updateToolsInBackground() {
    try {
      await this.fetchToolsFromNetwork();
    } catch (error) {
      console.error('[OfflineStorage] Background tools update failed:', error);
    }
  }

  /**
   * Get single tool by name
   */
  async getTool(toolName, strategy = CACHE_STRATEGIES.CACHE_FIRST) {
    console.log(`[OfflineStorage] Getting tool ${toolName} with strategy: ${strategy}`);

    switch (strategy) {
      case CACHE_STRATEGIES.CACHE_FIRST: {
        // Try cache first
        const cached = await getCachedTool(toolName);
        if (cached) {
          // Update in background
          if (navigator.onLine) {
            this.updateToolInBackground(toolName);
          }
          return cached;
        }
        // Fall through to network
      }

      case CACHE_STRATEGIES.NETWORK_FIRST:
      case CACHE_STRATEGIES.NETWORK_ONLY:
        if (navigator.onLine) {
          try {
            const tool = await apiRequest(API.toolDetail(toolName));
            // Cache individual tool
            await cacheTools([tool]);
            return tool;
          } catch (error) {
            // If network fails, try cache
            if (strategy === CACHE_STRATEGIES.CACHE_FIRST) {
              return getCachedTool(toolName);
            }
            throw error;
          }
        }
        // Fall through to cache if offline

      case CACHE_STRATEGIES.CACHE_ONLY:
        return getCachedTool(toolName);

      default:
        return getCachedTool(toolName);
    }
  }

  /**
   * Update single tool in background
   */
  async updateToolInBackground(toolName) {
    try {
      const tool = await apiRequest(API.toolDetail(toolName));
      await cacheTools([tool]);
    } catch (error) {
      console.error(`[OfflineStorage] Background tool update failed for ${toolName}:`, error);
    }
  }

  /**
   * Get tools by category
   */
  async getToolsByCategory(category) {
    const tools = await getToolsByCategory(category);
    console.log(`[OfflineStorage] Got ${tools.length} tools for category ${category}`);
    return tools;
  }

  /**
   * Clear tools cache
   */
  async clearToolsCache() {
    await clearToolsCache();
    this.emit('tools:cleared');
    console.log('[OfflineStorage] Tools cache cleared');
  }

  // ============= JOBS OPERATIONS =============

  /**
   * Execute tool
   * Queues for offline execution if network unavailable
   */
  async executeTool(toolName, parameters) {
    console.log(`[OfflineStorage] Executing tool: ${toolName}`);

    // If online, execute immediately
    if (navigator.onLine) {
      try {
        const response = await apiRequest(API.runTool, {
          method: 'POST',
          body: JSON.stringify({
            tool_name: toolName,
            parameters: parameters || {},
          }),
        });

        // Cache the job
        if (response.job_id) {
          await cacheJob({
            id: response.job_id,
            toolName,
            parameters,
            status: 'pending',
            createdAt: Date.now(),
          });
        }

        this.emit('job:created', response);
        return response;
      } catch (error) {
        console.error('[OfflineStorage] Tool execution failed:', error);

        // If it's a network error, queue for offline
        if (error.message === 'Failed to fetch') {
          console.log('[OfflineStorage] Queuing tool for offline execution');
          const queueId = await queueToolExecution(toolName, parameters);

          this.emit('job:queued', { queueId, toolName, parameters });

          return {
            queued: true,
            queueId,
            message: 'Tool queued for execution when online',
          };
        }

        throw error;
      }
    }

    // If offline, queue immediately
    console.log('[OfflineStorage] Offline - queuing tool for execution');
    const queueId = await queueToolExecution(toolName, parameters);

    this.emit('job:queued', { queueId, toolName, parameters });

    return {
      queued: true,
      queueId,
      message: 'Tool queued for execution when online',
    };
  }

  /**
   * Get jobs list
   */
  async getJobs(strategy = CACHE_STRATEGIES.CACHE_FIRST) {
    console.log(`[OfflineStorage] Getting jobs with strategy: ${strategy}`);

    switch (strategy) {
      case CACHE_STRATEGIES.CACHE_FIRST: {
        const cached = await getCachedJobs();
        if (cached && cached.length > 0) {
          // Update in background
          if (navigator.onLine) {
            this.updateJobsInBackground();
          }
          return cached;
        }
        // Fall through to network
      }

      case CACHE_STRATEGIES.NETWORK_FIRST:
      case CACHE_STRATEGIES.NETWORK_ONLY:
        if (navigator.onLine) {
          try {
            const jobs = await apiRequest(API.jobs);
            // Cache jobs
            for (const job of jobs) {
              await cacheJob(job);
            }
            return jobs;
          } catch (error) {
            if (strategy === CACHE_STRATEGIES.CACHE_FIRST) {
              return getCachedJobs();
            }
            throw error;
          }
        }
        // Fall through to cache if offline

      case CACHE_STRATEGIES.CACHE_ONLY:
        return getCachedJobs();

      default:
        return getCachedJobs();
    }
  }

  /**
   * Update jobs in background
   */
  async updateJobsInBackground() {
    try {
      const jobs = await apiRequest(API.jobs);
      for (const job of jobs) {
        await cacheJob(job);
      }
    } catch (error) {
      console.error('[OfflineStorage] Background jobs update failed:', error);
    }
  }

  /**
   * Get single job by ID
   */
  async getJob(jobId, strategy = CACHE_STRATEGIES.CACHE_FIRST) {
    console.log(`[OfflineStorage] Getting job ${jobId} with strategy: ${strategy}`);

    switch (strategy) {
      case CACHE_STRATEGIES.CACHE_FIRST: {
        const cached = await getCachedJob(jobId);
        if (cached) {
          // Update in background
          if (navigator.onLine) {
            this.updateJobInBackground(jobId);
          }
          return cached;
        }
        // Fall through to network
      }

      case CACHE_STRATEGIES.NETWORK_FIRST:
      case CACHE_STRATEGIES.NETWORK_ONLY:
        if (navigator.onLine) {
          try {
            const job = await apiRequest(API.jobDetail(jobId));
            await cacheJob(job);
            return job;
          } catch (error) {
            if (strategy === CACHE_STRATEGIES.CACHE_FIRST) {
              return getCachedJob(jobId);
            }
            throw error;
          }
        }
        // Fall through to cache if offline

      case CACHE_STRATEGIES.CACHE_ONLY:
        return getCachedJob(jobId);

      default:
        return getCachedJob(jobId);
    }
  }

  /**
   * Update single job in background
   */
  async updateJobInBackground(jobId) {
    try {
      const job = await apiRequest(API.jobDetail(jobId));
      await cacheJob(job);
    } catch (error) {
      console.error(`[OfflineStorage] Background job update failed for ${jobId}:`, error);
    }
  }

  /**
   * Get jobs by status
   */
  async getJobsByStatus(status) {
    return getJobsByStatus(status);
  }

  /**
   * Get jobs by tool
   */
  async getJobsByTool(toolName) {
    return getJobsByTool(toolName);
  }

  /**
   * Clear jobs cache
   */
  async clearJobsCache() {
    await clearJobsCache();
    this.emit('jobs:cleared');
    console.log('[OfflineStorage] Jobs cache cleared');
  }

  /**
   * Delete old jobs (cleanup)
   */
  async deleteOldJobs(daysToKeep = 30) {
    const count = await deleteOldJobs(daysToKeep);
    this.emit('jobs:cleaned', { count });
    console.log(`[OfflineStorage] Deleted ${count} old jobs`);
    return count;
  }

  // ============= PREFERENCES =============

  /**
   * Set user preference
   */
  async setPreference(key, value) {
    await setPreference(key, value);
    this.emit('preference:updated', { key, value });
  }

  /**
   * Get user preference
   */
  async getPreference(key, defaultValue) {
    return getPreference(key, defaultValue);
  }

  /**
   * Get all preferences
   */
  async getAllPreferences() {
    return getAllPreferences();
  }

  // ============= SYNC OPERATIONS =============

  /**
   * Background sync - update all cached data
   */
  async backgroundSync() {
    if (this.syncInProgress) {
      console.log('[OfflineStorage] Sync already in progress');
      return;
    }

    if (!navigator.onLine) {
      console.log('[OfflineStorage] Cannot sync while offline');
      return;
    }

    this.syncInProgress = true;
    this.emit('sync:started');

    try {
      console.log('[OfflineStorage] Starting background sync...');

      // Sync tools
      await this.fetchToolsFromNetwork();

      // Sync jobs
      await this.updateJobsInBackground();

      // Trigger queue sync
      await offlineQueue.syncQueue();

      console.log('[OfflineStorage] Background sync completed');
      this.emit('sync:completed');
    } catch (error) {
      console.error('[OfflineStorage] Background sync failed:', error);
      this.emit('sync:failed', { error });
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * Force full sync
   */
  async forceSync() {
    console.log('[OfflineStorage] Force sync requested');
    return this.backgroundSync();
  }

  // ============= UTILITIES =============

  /**
   * Get storage statistics
   */
  async getStats() {
    return getDatabaseStats();
  }

  /**
   * Check if offline mode is active
   */
  isOffline() {
    return !navigator.onLine;
  }

  /**
   * Check if sync is in progress
   */
  isSyncing() {
    return this.syncInProgress;
  }

  /**
   * Event emitter - on
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  /**
   * Event emitter - off
   */
  off(event, callback) {
    if (!this.eventListeners.has(event)) {
      return;
    }

    const listeners = this.eventListeners.get(event);
    const index = listeners.indexOf(callback);

    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  /**
   * Event emitter - emit
   */
  emit(event, data) {
    if (!this.eventListeners.has(event)) {
      return;
    }

    const listeners = this.eventListeners.get(event);
    listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[OfflineStorage] Event listener error (${event}):`, error);
      }
    });
  }
}

// Create singleton instance
const offlineStorage = new OfflineStorageManager();

// Export singleton and class
export default offlineStorage;
export { OfflineStorageManager };

// Convenience functions for direct usage

export async function getToolsOffline(strategy) {
  return offlineStorage.getTools(strategy);
}

export async function getToolOffline(toolName, strategy) {
  return offlineStorage.getTool(toolName, strategy);
}

export async function executeToolOffline(toolName, parameters) {
  return offlineStorage.executeTool(toolName, parameters);
}

export async function getJobsOffline(strategy) {
  return offlineStorage.getJobs(strategy);
}

export async function getJobOffline(jobId, strategy) {
  return offlineStorage.getJob(jobId, strategy);
}

export async function syncAllData() {
  return offlineStorage.forceSync();
}

export async function getStorageStats() {
  return offlineStorage.getStats();
}

console.log('[OfflineStorage] Service loaded');
