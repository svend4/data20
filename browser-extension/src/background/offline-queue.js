/**
 * Offline Queue Manager
 * Phase 9.2.4: Automatic job execution when connection is restored
 *
 * Features:
 * - Background sync monitoring
 * - Priority-based job execution
 * - Automatic retry with exponential backoff
 * - Queue persistence via IndexedDB
 * - Network status monitoring
 */

export class OfflineQueue {
  constructor(smartRouter, storageManager) {
    this.router = smartRouter;
    this.storage = storageManager;

    // Queue state
    this.isProcessing = false;
    this.processingJobId = null;
    this.syncInterval = null;

    // Configuration
    this.config = {
      syncIntervalMs: 30000,        // Check every 30 seconds
      maxRetries: 3,
      retryDelayMs: 2000,           // Base delay for retries
      maxConcurrentJobs: 1,         // Process one job at a time
      enableBackgroundSync: true    // Use Background Sync API if available
    };

    // Statistics
    this.stats = {
      jobsProcessed: 0,
      jobsSucceeded: 0,
      jobsFailed: 0,
      lastSyncAttempt: null,
      lastSuccessfulSync: null
    };
  }

  /**
   * Initialize offline queue
   */
  async initialize() {
    console.log('[OfflineQueue] Initializing...');

    // Start monitoring network status
    this.setupNetworkMonitoring();

    // Register background sync if available
    if (this.config.enableBackgroundSync && 'serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
      await this.registerBackgroundSync();
    }

    // Start periodic sync check
    this.startPeriodicSync();

    // Process any existing queued jobs if online
    if (navigator.onLine) {
      await this.processQueue();
    }

    console.log('[OfflineQueue] Initialized successfully');
  }

  /**
   * Setup network status monitoring
   */
  setupNetworkMonitoring() {
    // Listen for online event
    self.addEventListener('online', async () => {
      console.log('[OfflineQueue] Connection restored, processing queue...');
      this.stats.lastSyncAttempt = Date.now();

      await this.processQueue();
    });

    // Listen for offline event
    self.addEventListener('offline', () => {
      console.log('[OfflineQueue] Connection lost');
      this.stopProcessing();
    });
  }

  /**
   * Register background sync for when connection is restored
   */
  async registerBackgroundSync() {
    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-queue');
      console.log('[OfflineQueue] Background sync registered');
    } catch (error) {
      console.warn('[OfflineQueue] Background sync not available:', error.message);
    }
  }

  /**
   * Start periodic sync checks
   */
  startPeriodicSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    this.syncInterval = setInterval(async () => {
      if (navigator.onLine && !this.isProcessing) {
        const queuedJobs = await this.storage.getQueuedJobs('queued');

        if (queuedJobs.length > 0) {
          console.log(`[OfflineQueue] Periodic sync: ${queuedJobs.length} jobs queued`);
          await this.processQueue();
        }
      }
    }, this.config.syncIntervalMs);

    console.log(`[OfflineQueue] Periodic sync started (interval: ${this.config.syncIntervalMs}ms)`);
  }

  /**
   * Stop periodic sync
   */
  stopPeriodicSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
      console.log('[OfflineQueue] Periodic sync stopped');
    }
  }

  /**
   * Process all queued jobs
   */
  async processQueue() {
    if (this.isProcessing) {
      console.log('[OfflineQueue] Already processing queue');
      return;
    }

    if (!navigator.onLine) {
      console.log('[OfflineQueue] Offline, skipping queue processing');
      return;
    }

    this.isProcessing = true;
    console.log('[OfflineQueue] Starting queue processing...');

    try {
      // Get all queued jobs, sorted by priority (highest first) then createdAt (oldest first)
      const queuedJobs = await this.storage.getQueuedJobs('queued');

      if (queuedJobs.length === 0) {
        console.log('[OfflineQueue] Queue is empty');
        return;
      }

      // Sort by priority (descending) then createdAt (ascending)
      const sortedJobs = queuedJobs.sort((a, b) => {
        if (b.priority !== a.priority) {
          return b.priority - a.priority;
        }
        return a.createdAt - b.createdAt;
      });

      console.log(`[OfflineQueue] Processing ${sortedJobs.length} queued jobs`);

      // Process jobs sequentially
      for (const job of sortedJobs) {
        if (!navigator.onLine) {
          console.log('[OfflineQueue] Connection lost during processing');
          break;
        }

        await this.processJob(job);
      }

      this.stats.lastSuccessfulSync = Date.now();
      console.log('[OfflineQueue] Queue processing complete');

    } catch (error) {
      console.error('[OfflineQueue] Queue processing error:', error);
    } finally {
      this.isProcessing = false;
      this.processingJobId = null;
    }
  }

  /**
   * Process a single job
   */
  async processJob(job) {
    this.processingJobId = job.id;
    console.log(`[OfflineQueue] Processing job ${job.id}: ${job.toolName}`);

    try {
      // Update job status to processing
      await this.storage.updateQueueJob(job.id, {
        status: 'processing',
        startedAt: Date.now()
      });

      // Execute the tool via Smart Router
      const result = await this.router.executeTool(job.toolName, job.parameters);

      // Mark job as completed
      await this.storage.updateQueueJob(job.id, {
        status: 'completed',
        completedAt: Date.now(),
        result: result.result,
        execution: result.execution
      });

      this.stats.jobsProcessed++;
      this.stats.jobsSucceeded++;

      console.log(`[OfflineQueue] Job ${job.id} completed successfully`);

      // Send notification to user
      this.notifyJobCompleted(job, result);

      // Optionally remove completed jobs after notification
      // await this.storage.removeFromQueue(job.id);

    } catch (error) {
      console.error(`[OfflineQueue] Job ${job.id} failed:`, error);

      // Increment retry count
      const retryCount = (job.retryCount || 0) + 1;

      if (retryCount < this.config.maxRetries) {
        // Schedule retry
        console.log(`[OfflineQueue] Job ${job.id} will retry (attempt ${retryCount}/${this.config.maxRetries})`);

        await this.storage.updateQueueJob(job.id, {
          status: 'queued',
          retryCount: retryCount,
          lastError: error.message,
          lastAttemptAt: Date.now()
        });

        // Wait before next retry (exponential backoff)
        const delay = this.config.retryDelayMs * Math.pow(2, retryCount - 1);
        await new Promise(resolve => setTimeout(resolve, delay));

      } else {
        // Max retries reached, mark as failed
        console.error(`[OfflineQueue] Job ${job.id} failed permanently after ${retryCount} attempts`);

        await this.storage.updateQueueJob(job.id, {
          status: 'failed',
          failedAt: Date.now(),
          retryCount: retryCount,
          error: error.message
        });

        this.stats.jobsProcessed++;
        this.stats.jobsFailed++;

        // Notify user of failure
        this.notifyJobFailed(job, error);
      }
    }
  }

  /**
   * Stop processing (when going offline)
   */
  stopProcessing() {
    console.log('[OfflineQueue] Stopping processing');

    // If currently processing a job, mark it back as queued
    if (this.processingJobId) {
      this.storage.updateQueueJob(this.processingJobId, {
        status: 'queued'
      }).catch(err => {
        console.error('[OfflineQueue] Failed to reset job status:', err);
      });
    }

    this.isProcessing = false;
    this.processingJobId = null;
  }

  /**
   * Notify user of completed job
   */
  notifyJobCompleted(job, result) {
    const title = 'Queued Task Completed';
    const message = `${job.toolName} executed successfully`;

    try {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('public/icons/icon-128.png'),
        title: title,
        message: message,
        priority: 1
      });
    } catch (error) {
      console.warn('[OfflineQueue] Notification failed:', error);
    }
  }

  /**
   * Notify user of failed job
   */
  notifyJobFailed(job, error) {
    const title = 'Queued Task Failed';
    const message = `${job.toolName} failed: ${error.message}`;

    try {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('public/icons/icon-128.png'),
        title: title,
        message: message,
        priority: 2
      });
    } catch (error) {
      console.warn('[OfflineQueue] Notification failed:', error);
    }
  }

  /**
   * Manually trigger queue processing
   */
  async triggerSync() {
    console.log('[OfflineQueue] Manual sync triggered');
    this.stats.lastSyncAttempt = Date.now();
    await this.processQueue();
  }

  /**
   * Clear all completed jobs
   */
  async clearCompletedJobs() {
    const completedJobs = await this.storage.getQueuedJobs('completed');

    for (const job of completedJobs) {
      await this.storage.removeFromQueue(job.id);
    }

    console.log(`[OfflineQueue] Cleared ${completedJobs.length} completed jobs`);
    return completedJobs.length;
  }

  /**
   * Clear all failed jobs
   */
  async clearFailedJobs() {
    const failedJobs = await this.storage.getQueuedJobs('failed');

    for (const job of failedJobs) {
      await this.storage.removeFromQueue(job.id);
    }

    console.log(`[OfflineQueue] Cleared ${failedJobs.length} failed jobs`);
    return failedJobs.length;
  }

  /**
   * Retry a specific failed job
   */
  async retryJob(jobId) {
    const job = await this.storage._get('queue', jobId);

    if (!job) {
      throw new Error(`Job ${jobId} not found`);
    }

    if (job.status !== 'failed') {
      throw new Error(`Job ${jobId} is not in failed status`);
    }

    // Reset job to queued with retry count reset
    await this.storage.updateQueueJob(jobId, {
      status: 'queued',
      retryCount: 0,
      lastError: null
    });

    console.log(`[OfflineQueue] Job ${jobId} queued for retry`);

    // Trigger processing if online
    if (navigator.onLine) {
      await this.processQueue();
    }
  }

  /**
   * Retry all failed jobs
   */
  async retryAllFailed() {
    const failedJobs = await this.storage.getQueuedJobs('failed');

    for (const job of failedJobs) {
      await this.storage.updateQueueJob(job.id, {
        status: 'queued',
        retryCount: 0,
        lastError: null
      });
    }

    console.log(`[OfflineQueue] ${failedJobs.length} failed jobs queued for retry`);

    // Trigger processing if online
    if (navigator.onLine) {
      await this.processQueue();
    }

    return failedJobs.length;
  }

  /**
   * Get queue statistics
   */
  async getStats() {
    const queueStats = await this.storage.getQueueStats();

    return {
      queue: queueStats,
      processing: {
        isProcessing: this.isProcessing,
        currentJobId: this.processingJobId
      },
      lifetime: {
        jobsProcessed: this.stats.jobsProcessed,
        jobsSucceeded: this.stats.jobsSucceeded,
        jobsFailed: this.stats.jobsFailed,
        successRate: this.stats.jobsProcessed > 0
          ? ((this.stats.jobsSucceeded / this.stats.jobsProcessed) * 100).toFixed(1)
          : '0.0'
      },
      sync: {
        lastAttempt: this.stats.lastSyncAttempt,
        lastSuccess: this.stats.lastSuccessfulSync,
        intervalMs: this.config.syncIntervalMs
      },
      network: {
        online: navigator.onLine
      }
    };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    console.log('[OfflineQueue] Configuration updated:', this.config);

    // Restart periodic sync if interval changed
    if (newConfig.syncIntervalMs) {
      this.startPeriodicSync();
    }
  }

  /**
   * Get current configuration
   */
  getConfig() {
    return { ...this.config };
  }

  /**
   * Shutdown queue manager
   */
  shutdown() {
    console.log('[OfflineQueue] Shutting down...');
    this.stopPeriodicSync();
    this.stopProcessing();
  }
}

export default OfflineQueue;
