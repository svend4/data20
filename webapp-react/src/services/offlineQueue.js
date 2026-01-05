/**
 * Offline Queue Service for Data20 PWA
 * Phase 8.1.1: IndexedDB Caching Infrastructure
 *
 * This service manages offline operations queue:
 * - Add operations to queue when offline
 * - Automatically sync when network is back
 * - Retry failed operations
 * - Priority-based execution
 * - Event-based notifications
 *
 * Queue Item Structure:
 * {
 *   id: number (auto-incremented)
 *   type: string ('execute_tool', 'update_job', etc.)
 *   data: object (operation-specific data)
 *   status: string ('pending', 'processing', 'completed', 'failed')
 *   priority: number (higher = more important)
 *   createdAt: timestamp
 *   updatedAt: timestamp
 *   completedAt: timestamp
 *   error: string (error message if failed)
 *   retries: number
 *   maxRetries: number
 * }
 *
 * Version: 1.0.0
 * Created: 2026-01-05
 */

import {
  addToOfflineQueue,
  getPendingQueueItems,
  getAllQueueItems,
  updateQueueItemStatus,
  removeFromQueue,
  clearCompletedQueue,
  getQueueStats,
} from './db.js';

import { apiRequest, API } from '../utils/api.js';

/**
 * Queue operation types
 */
export const QUEUE_TYPES = {
  EXECUTE_TOOL: 'execute_tool',
  UPDATE_JOB: 'update_job',
  DELETE_JOB: 'delete_job',
  CACHE_TOOL: 'cache_tool',
  CUSTOM: 'custom',
};

/**
 * Queue priorities
 */
export const QUEUE_PRIORITIES = {
  LOW: 0,
  NORMAL: 1,
  HIGH: 2,
  CRITICAL: 3,
};

/**
 * Queue statuses
 */
export const QUEUE_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

/**
 * Event types for queue notifications
 */
export const QUEUE_EVENTS = {
  ITEM_ADDED: 'queue:item_added',
  ITEM_PROCESSING: 'queue:item_processing',
  ITEM_COMPLETED: 'queue:item_completed',
  ITEM_FAILED: 'queue:item_failed',
  SYNC_STARTED: 'queue:sync_started',
  SYNC_COMPLETED: 'queue:sync_completed',
  SYNC_FAILED: 'queue:sync_failed',
};

/**
 * Offline Queue Manager
 */
class OfflineQueueManager {
  constructor() {
    this.syncing = false;
    this.eventListeners = new Map();
    this.syncInterval = null;

    // Bind methods
    this.handleOnline = this.handleOnline.bind(this);
    this.handleOffline = this.handleOffline.bind(this);

    // Auto-initialize
    this.initialize();
  }

  /**
   * Initialize queue manager
   * - Setup event listeners
   * - Start auto-sync if online
   */
  initialize() {
    console.log('[OfflineQueue] Initializing...');

    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);

    // Start auto-sync if currently online
    if (navigator.onLine) {
      this.startAutoSync();
    }

    console.log('[OfflineQueue] Initialized');
  }

  /**
   * Cleanup
   */
  destroy() {
    console.log('[OfflineQueue] Destroying...');

    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    this.stopAutoSync();

    console.log('[OfflineQueue] Destroyed');
  }

  /**
   * Handle online event
   */
  handleOnline() {
    console.log('[OfflineQueue] Network is back online');
    this.emit(QUEUE_EVENTS.SYNC_STARTED);
    this.syncQueue();
    this.startAutoSync();
  }

  /**
   * Handle offline event
   */
  handleOffline() {
    console.log('[OfflineQueue] Network went offline');
    this.stopAutoSync();
  }

  /**
   * Start auto-sync interval
   */
  startAutoSync(intervalMs = 30000) {
    // 30 seconds
    if (this.syncInterval) {
      return; // Already running
    }

    this.syncInterval = setInterval(() => {
      if (navigator.onLine && !this.syncing) {
        this.syncQueue();
      }
    }, intervalMs);

    console.log('[OfflineQueue] Auto-sync started');
  }

  /**
   * Stop auto-sync interval
   */
  stopAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
      console.log('[OfflineQueue] Auto-sync stopped');
    }
  }

  /**
   * Add item to queue
   */
  async addItem(type, data, options = {}) {
    const item = {
      type,
      data,
      priority: options.priority || QUEUE_PRIORITIES.NORMAL,
      maxRetries: options.maxRetries || 3,
      ...options,
    };

    const id = await addToOfflineQueue(item);
    this.emit(QUEUE_EVENTS.ITEM_ADDED, { id, ...item });

    console.log(`[OfflineQueue] Added item to queue:`, { id, type });

    // Try to sync immediately if online
    if (navigator.onLine && !this.syncing) {
      this.syncQueue();
    }

    return id;
  }

  /**
   * Add tool execution to queue
   */
  async queueToolExecution(toolName, parameters, priority = QUEUE_PRIORITIES.NORMAL) {
    return this.addItem(
      QUEUE_TYPES.EXECUTE_TOOL,
      { toolName, parameters },
      { priority }
    );
  }

  /**
   * Get all queue items
   */
  async getAll() {
    return getAllQueueItems();
  }

  /**
   * Get pending queue items
   */
  async getPending() {
    return getPendingQueueItems();
  }

  /**
   * Get queue statistics
   */
  async getStats() {
    return getQueueStats();
  }

  /**
   * Remove item from queue
   */
  async removeItem(id) {
    await removeFromQueue(id);
    console.log(`[OfflineQueue] Removed item ${id}`);
  }

  /**
   * Clear completed items
   */
  async clearCompleted() {
    const count = await clearCompletedQueue();
    console.log(`[OfflineQueue] Cleared ${count} completed items`);
    return count;
  }

  /**
   * Sync queue - process all pending items
   */
  async syncQueue() {
    if (this.syncing) {
      console.log('[OfflineQueue] Sync already in progress');
      return;
    }

    if (!navigator.onLine) {
      console.log('[OfflineQueue] Cannot sync while offline');
      return;
    }

    this.syncing = true;
    this.emit(QUEUE_EVENTS.SYNC_STARTED);

    try {
      const pendingItems = await getPendingQueueItems();

      if (pendingItems.length === 0) {
        console.log('[OfflineQueue] No pending items to sync');
        this.syncing = false;
        return;
      }

      console.log(`[OfflineQueue] Syncing ${pendingItems.length} items...`);

      let completed = 0;
      let failed = 0;

      for (const item of pendingItems) {
        try {
          await this.processItem(item);
          completed++;
        } catch (error) {
          console.error(`[OfflineQueue] Failed to process item ${item.id}:`, error);
          failed++;
        }
      }

      console.log(
        `[OfflineQueue] Sync completed: ${completed} succeeded, ${failed} failed`
      );

      this.emit(QUEUE_EVENTS.SYNC_COMPLETED, { completed, failed });
    } catch (error) {
      console.error('[OfflineQueue] Sync failed:', error);
      this.emit(QUEUE_EVENTS.SYNC_FAILED, { error });
    } finally {
      this.syncing = false;
    }
  }

  /**
   * Process single queue item
   */
  async processItem(item) {
    console.log(`[OfflineQueue] Processing item ${item.id} (${item.type})`);

    // Update status to processing
    await updateQueueItemStatus(item.id, QUEUE_STATUS.PROCESSING);
    this.emit(QUEUE_EVENTS.ITEM_PROCESSING, item);

    try {
      // Execute operation based on type
      let result;

      switch (item.type) {
        case QUEUE_TYPES.EXECUTE_TOOL:
          result = await this.executeToolOperation(item);
          break;

        case QUEUE_TYPES.UPDATE_JOB:
          result = await this.updateJobOperation(item);
          break;

        case QUEUE_TYPES.DELETE_JOB:
          result = await this.deleteJobOperation(item);
          break;

        case QUEUE_TYPES.CACHE_TOOL:
          result = await this.cacheToolOperation(item);
          break;

        case QUEUE_TYPES.CUSTOM:
          result = await this.customOperation(item);
          break;

        default:
          throw new Error(`Unknown queue type: ${item.type}`);
      }

      // Mark as completed
      await updateQueueItemStatus(item.id, QUEUE_STATUS.COMPLETED);
      this.emit(QUEUE_EVENTS.ITEM_COMPLETED, { item, result });

      console.log(`[OfflineQueue] Item ${item.id} completed successfully`);
      return result;
    } catch (error) {
      console.error(`[OfflineQueue] Item ${item.id} failed:`, error);

      // Check if should retry
      if (item.retries < item.maxRetries) {
        // Update with error, keep as pending for retry
        await updateQueueItemStatus(item.id, QUEUE_STATUS.PENDING, error.message);
        console.log(
          `[OfflineQueue] Will retry item ${item.id} (attempt ${item.retries + 1}/${
            item.maxRetries
          })`
        );
      } else {
        // Max retries exceeded, mark as failed
        await updateQueueItemStatus(item.id, QUEUE_STATUS.FAILED, error.message);
        this.emit(QUEUE_EVENTS.ITEM_FAILED, { item, error });
        console.log(`[OfflineQueue] Item ${item.id} failed after max retries`);
      }

      throw error;
    }
  }

  /**
   * Execute tool operation
   */
  async executeToolOperation(item) {
    const { toolName, parameters } = item.data;

    const response = await apiRequest(API.runTool, {
      method: 'POST',
      body: JSON.stringify({
        tool_name: toolName,
        parameters: parameters || {},
      }),
    });

    return response;
  }

  /**
   * Update job operation
   */
  async updateJobOperation(item) {
    const { jobId, updates } = item.data;

    const response = await apiRequest(API.jobDetail(jobId), {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });

    return response;
  }

  /**
   * Delete job operation
   */
  async deleteJobOperation(item) {
    const { jobId } = item.data;

    await apiRequest(API.jobDetail(jobId), {
      method: 'DELETE',
    });

    return { deleted: true };
  }

  /**
   * Cache tool operation
   */
  async cacheToolOperation(item) {
    const { toolName } = item.data;

    const tool = await apiRequest(API.toolDetail(toolName));

    // Cache would be handled by service worker or other caching layer
    return tool;
  }

  /**
   * Custom operation (user-defined)
   */
  async customOperation(item) {
    const { handler } = item.data;

    if (typeof handler === 'function') {
      return await handler(item.data);
    }

    throw new Error('Custom operation requires a handler function');
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
        console.error(`[OfflineQueue] Event listener error (${event}):`, error);
      }
    });
  }

  /**
   * Check if currently syncing
   */
  isSyncing() {
    return this.syncing;
  }

  /**
   * Check if online
   */
  isOnline() {
    return navigator.onLine;
  }
}

// Create singleton instance
const offlineQueue = new OfflineQueueManager();

// Export singleton and class
export default offlineQueue;
export { OfflineQueueManager };

// Convenience functions

/**
 * Add tool execution to queue
 */
export async function queueToolExecution(toolName, parameters, priority) {
  return offlineQueue.queueToolExecution(toolName, parameters, priority);
}

/**
 * Get queue statistics
 */
export async function getOfflineQueueStats() {
  return offlineQueue.getStats();
}

/**
 * Manually trigger queue sync
 */
export async function syncOfflineQueue() {
  return offlineQueue.syncQueue();
}

/**
 * Get all queue items
 */
export async function getOfflineQueueItems() {
  return offlineQueue.getAll();
}

/**
 * Get pending queue items
 */
export async function getPendingOfflineItems() {
  return offlineQueue.getPending();
}

/**
 * Clear completed queue items
 */
export async function clearCompletedOfflineQueue() {
  return offlineQueue.clearCompleted();
}

/**
 * Listen to queue events
 */
export function onQueueEvent(event, callback) {
  offlineQueue.on(event, callback);
}

/**
 * Stop listening to queue events
 */
export function offQueueEvent(event, callback) {
  offlineQueue.off(event, callback);
}

console.log('[OfflineQueue] Service loaded');
