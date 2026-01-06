/**
 * Offline Queue Unit Tests - Phase 9.2 Stage 2
 * Comprehensive test suite for offline queue management system
 */

import { OfflineQueue } from '../../src/background/offline-queue.js';

describe('OfflineQueue', () => {
  let offlineQueue;
  let mockSmartRouter;
  let mockStorageManager;

  beforeEach(() => {
    // Mock Smart Router
    mockSmartRouter = {
      executeTool: jest.fn().mockResolvedValue({
        success: true,
        result: 'execution result',
        execution: { local: true, time: 100 }
      })
    };

    // Mock Storage Manager
    mockStorageManager = {
      getQueuedJobs: jest.fn().mockResolvedValue([]),
      updateQueueJob: jest.fn().mockResolvedValue(undefined),
      addToQueue: jest.fn().mockResolvedValue('job-id-123'),
      removeFromQueue: jest.fn().mockResolvedValue(undefined),
      getQueueStats: jest.fn().mockResolvedValue({
        queued: 0,
        processing: 0,
        completed: 0,
        failed: 0
      })
    };

    offlineQueue = new OfflineQueue(mockSmartRouter, mockStorageManager);

    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true
    });
  });

  afterEach(() => {
    // Clean up intervals
    if (offlineQueue.syncInterval) {
      clearInterval(offlineQueue.syncInterval);
    }
  });

  describe('Constructor', () => {
    test('should initialize with correct dependencies', () => {
      expect(offlineQueue.router).toBe(mockSmartRouter);
      expect(offlineQueue.storage).toBe(mockStorageManager);
    });

    test('should initialize with correct default configuration', () => {
      expect(offlineQueue.config).toEqual({
        syncIntervalMs: 30000,
        maxRetries: 3,
        retryDelayMs: 2000,
        maxConcurrentJobs: 1,
        enableBackgroundSync: true
      });
    });

    test('should initialize processing state as false', () => {
      expect(offlineQueue.isProcessing).toBe(false);
      expect(offlineQueue.processingJobId).toBeNull();
      expect(offlineQueue.syncInterval).toBeNull();
    });

    test('should initialize statistics', () => {
      expect(offlineQueue.stats).toEqual({
        jobsProcessed: 0,
        jobsSucceeded: 0,
        jobsFailed: 0,
        lastSyncAttempt: null,
        lastSuccessfulSync: null
      });
    });
  });

  describe('initialize()', () => {
    beforeEach(() => {
      offlineQueue.setupNetworkMonitoring = jest.fn();
      offlineQueue.registerBackgroundSync = jest.fn().mockResolvedValue(undefined);
      offlineQueue.startPeriodicSync = jest.fn();
      offlineQueue.processQueue = jest.fn().mockResolvedValue(undefined);
    });

    test('should call all initialization methods', async () => {
      await offlineQueue.initialize();

      expect(offlineQueue.setupNetworkMonitoring).toHaveBeenCalled();
      expect(offlineQueue.startPeriodicSync).toHaveBeenCalled();
    });

    test('should process queue if online', async () => {
      navigator.onLine = true;

      await offlineQueue.initialize();

      expect(offlineQueue.processQueue).toHaveBeenCalled();
    });

    test('should not process queue if offline', async () => {
      navigator.onLine = false;

      await offlineQueue.initialize();

      expect(offlineQueue.processQueue).not.toHaveBeenCalled();
    });

    test('should register background sync if available', async () => {
      offlineQueue.config.enableBackgroundSync = true;

      await offlineQueue.initialize();

      expect(offlineQueue.registerBackgroundSync).toHaveBeenCalled();
    });

    test('should skip background sync if disabled', async () => {
      offlineQueue.config.enableBackgroundSync = false;

      await offlineQueue.initialize();

      expect(offlineQueue.registerBackgroundSync).not.toHaveBeenCalled();
    });
  });

  describe('startPeriodicSync()', () => {
    test('should start interval with correct timing', () => {
      jest.useFakeTimers();

      offlineQueue.startPeriodicSync();

      expect(offlineQueue.syncInterval).not.toBeNull();

      jest.useRealTimers();
    });

    test('should clear existing interval before starting new one', () => {
      const firstInterval = setInterval(() => {}, 1000);
      offlineQueue.syncInterval = firstInterval;

      offlineQueue.startPeriodicSync();

      expect(offlineQueue.syncInterval).not.toBe(firstInterval);
    });

    test('should process queue when interval fires and jobs exist', async () => {
      jest.useFakeTimers();
      mockStorageManager.getQueuedJobs.mockResolvedValue([{ id: 1 }]);
      offlineQueue.processQueue = jest.fn().mockResolvedValue(undefined);

      offlineQueue.startPeriodicSync();

      await jest.advanceTimersByTimeAsync(30000);

      expect(mockStorageManager.getQueuedJobs).toHaveBeenCalled();

      jest.useRealTimers();
    });

    test('should not process if already processing', async () => {
      jest.useFakeTimers();
      offlineQueue.isProcessing = true;
      offlineQueue.processQueue = jest.fn();

      offlineQueue.startPeriodicSync();

      await jest.advanceTimersByTimeAsync(30000);

      expect(offlineQueue.processQueue).not.toHaveBeenCalled();

      jest.useRealTimers();
    });
  });

  describe('stopPeriodicSync()', () => {
    test('should clear interval', () => {
      offlineQueue.syncInterval = setInterval(() => {}, 1000);

      offlineQueue.stopPeriodicSync();

      expect(offlineQueue.syncInterval).toBeNull();
    });

    test('should do nothing if no interval exists', () => {
      offlineQueue.syncInterval = null;

      expect(() => offlineQueue.stopPeriodicSync()).not.toThrow();
    });
  });

  describe('processQueue()', () => {
    test('should not process if already processing', async () => {
      offlineQueue.isProcessing = true;

      await offlineQueue.processQueue();

      expect(mockStorageManager.getQueuedJobs).not.toHaveBeenCalled();
    });

    test('should not process if offline', async () => {
      navigator.onLine = false;

      await offlineQueue.processQueue();

      expect(mockStorageManager.getQueuedJobs).not.toHaveBeenCalled();
    });

    test('should get queued jobs from storage', async () => {
      mockStorageManager.getQueuedJobs.mockResolvedValue([]);

      await offlineQueue.processQueue();

      expect(mockStorageManager.getQueuedJobs).toHaveBeenCalledWith('queued');
    });

    test('should return early if queue is empty', async () => {
      mockStorageManager.getQueuedJobs.mockResolvedValue([]);

      await offlineQueue.processQueue();

      expect(offlineQueue.isProcessing).toBe(false);
    });

    test('should sort jobs by priority (descending) then createdAt (ascending)', async () => {
      const jobs = [
        { id: 1, priority: 1, createdAt: 300, toolName: 'tool1' },
        { id: 2, priority: 2, createdAt: 100, toolName: 'tool2' },
        { id: 3, priority: 2, createdAt: 200, toolName: 'tool3' },
        { id: 4, priority: 0, createdAt: 400, toolName: 'tool4' }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);
      offlineQueue.processJob = jest.fn().mockResolvedValue(undefined);

      await offlineQueue.processQueue();

      // Should process in order: id 2 (p2, t100), id 3 (p2, t200), id 1 (p1, t300), id 4 (p0, t400)
      expect(offlineQueue.processJob).toHaveBeenNthCalledWith(1, jobs[1]); // id 2
      expect(offlineQueue.processJob).toHaveBeenNthCalledWith(2, jobs[2]); // id 3
      expect(offlineQueue.processJob).toHaveBeenNthCalledWith(3, jobs[0]); // id 1
      expect(offlineQueue.processJob).toHaveBeenNthCalledWith(4, jobs[3]); // id 4
    });

    test('should process all jobs sequentially', async () => {
      const jobs = [
        { id: 1, priority: 1, createdAt: 100, toolName: 'tool1' },
        { id: 2, priority: 1, createdAt: 200, toolName: 'tool2' }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);
      offlineQueue.processJob = jest.fn().mockResolvedValue(undefined);

      await offlineQueue.processQueue();

      expect(offlineQueue.processJob).toHaveBeenCalledTimes(2);
    });

    test('should stop processing if connection is lost mid-queue', async () => {
      const jobs = [
        { id: 1, priority: 1, createdAt: 100, toolName: 'tool1' },
        { id: 2, priority: 1, createdAt: 200, toolName: 'tool2' }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);
      offlineQueue.processJob = jest.fn().mockImplementation(async () => {
        navigator.onLine = false; // Simulate going offline
      });

      await offlineQueue.processQueue();

      expect(offlineQueue.processJob).toHaveBeenCalledTimes(1); // Only first job
    });

    test('should update lastSuccessfulSync on completion', async () => {
      const jobs = [{ id: 1, priority: 1, createdAt: 100, toolName: 'tool1' }];
      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);
      offlineQueue.processJob = jest.fn().mockResolvedValue(undefined);

      const beforeTime = Date.now();
      await offlineQueue.processQueue();
      const afterTime = Date.now();

      expect(offlineQueue.stats.lastSuccessfulSync).toBeGreaterThanOrEqual(beforeTime);
      expect(offlineQueue.stats.lastSuccessfulSync).toBeLessThanOrEqual(afterTime);
    });

    test('should reset processing state after completion', async () => {
      mockStorageManager.getQueuedJobs.mockResolvedValue([]);

      await offlineQueue.processQueue();

      expect(offlineQueue.isProcessing).toBe(false);
      expect(offlineQueue.processingJobId).toBeNull();
    });

    test('should reset processing state even on error', async () => {
      mockStorageManager.getQueuedJobs.mockRejectedValue(new Error('Storage error'));

      await offlineQueue.processQueue();

      expect(offlineQueue.isProcessing).toBe(false);
      expect(offlineQueue.processingJobId).toBeNull();
    });
  });

  describe('processJob()', () => {
    const mockJob = {
      id: 'job-123',
      toolName: 'test_tool',
      parameters: { text: 'test' },
      priority: 1,
      createdAt: Date.now()
    };

    test('should update job status to processing', async () => {
      await offlineQueue.processJob(mockJob);

      expect(mockStorageManager.updateQueueJob).toHaveBeenCalledWith(
        mockJob.id,
        expect.objectContaining({
          status: 'processing',
          startedAt: expect.any(Number)
        })
      );
    });

    test('should execute tool via router', async () => {
      await offlineQueue.processJob(mockJob);

      expect(mockSmartRouter.executeTool).toHaveBeenCalledWith(
        mockJob.toolName,
        mockJob.parameters
      );
    });

    test('should mark job as completed on success', async () => {
      await offlineQueue.processJob(mockJob);

      expect(mockStorageManager.updateQueueJob).toHaveBeenCalledWith(
        mockJob.id,
        expect.objectContaining({
          status: 'completed',
          completedAt: expect.any(Number)
        })
      );
    });

    test('should increment success statistics', async () => {
      await offlineQueue.processJob(mockJob);

      expect(offlineQueue.stats.jobsProcessed).toBe(1);
      expect(offlineQueue.stats.jobsSucceeded).toBe(1);
      expect(offlineQueue.stats.jobsFailed).toBe(0);
    });

    test('should retry job on failure if retries available', async () => {
      mockSmartRouter.executeTool.mockRejectedValue(new Error('Execution failed'));

      await offlineQueue.processJob(mockJob);

      expect(mockStorageManager.updateQueueJob).toHaveBeenCalledWith(
        mockJob.id,
        expect.objectContaining({
          status: 'queued',
          retryCount: 1,
          lastError: 'Execution failed'
        })
      );
    });

    test('should use exponential backoff for retries', async () => {
      jest.useFakeTimers();
      mockSmartRouter.executeTool.mockRejectedValue(new Error('Execution failed'));

      const jobWithRetry = { ...mockJob, retryCount: 1 };
      const promise = offlineQueue.processJob(jobWithRetry);

      await jest.advanceTimersByTimeAsync(4000); // 2000 * 2^1 = 4000ms
      await promise;

      jest.useRealTimers();
    });

    test('should mark job as failed after max retries', async () => {
      mockSmartRouter.executeTool.mockRejectedValue(new Error('Execution failed'));

      const jobWithMaxRetries = { ...mockJob, retryCount: 2 }; // Will be 3 after increment

      await offlineQueue.processJob(jobWithMaxRetries);

      expect(mockStorageManager.updateQueueJob).toHaveBeenCalledWith(
        mockJob.id,
        expect.objectContaining({
          status: 'failed',
          failedAt: expect.any(Number),
          error: 'Execution failed'
        })
      );
    });

    test('should increment failure statistics when job fails permanently', async () => {
      mockSmartRouter.executeTool.mockRejectedValue(new Error('Execution failed'));

      const jobWithMaxRetries = { ...mockJob, retryCount: 2 };

      await offlineQueue.processJob(jobWithMaxRetries);

      expect(offlineQueue.stats.jobsProcessed).toBe(1);
      expect(offlineQueue.stats.jobsFailed).toBe(1);
      expect(offlineQueue.stats.jobsSucceeded).toBe(0);
    });

    test('should call notification on success', async () => {
      offlineQueue.notifyJobCompleted = jest.fn();

      await offlineQueue.processJob(mockJob);

      expect(offlineQueue.notifyJobCompleted).toHaveBeenCalledWith(
        mockJob,
        expect.any(Object)
      );
    });

    test('should call notification on permanent failure', async () => {
      mockSmartRouter.executeTool.mockRejectedValue(new Error('Execution failed'));
      offlineQueue.notifyJobFailed = jest.fn();

      const jobWithMaxRetries = { ...mockJob, retryCount: 2 };

      await offlineQueue.processJob(jobWithMaxRetries);

      expect(offlineQueue.notifyJobFailed).toHaveBeenCalled();
    });
  });

  describe('stopProcessing()', () => {
    test('should reset processing state', () => {
      offlineQueue.isProcessing = true;
      offlineQueue.processingJobId = 'job-123';

      offlineQueue.stopProcessing();

      expect(offlineQueue.isProcessing).toBe(false);
      expect(offlineQueue.processingJobId).toBeNull();
    });

    test('should reset current job to queued status', async () => {
      offlineQueue.processingJobId = 'job-123';

      offlineQueue.stopProcessing();

      // Wait for async operation
      await new Promise(resolve => setTimeout(resolve, 10));

      expect(mockStorageManager.updateQueueJob).toHaveBeenCalledWith(
        'job-123',
        { status: 'queued' }
      );
    });

    test('should handle storage error gracefully', async () => {
      offlineQueue.processingJobId = 'job-123';
      mockStorageManager.updateQueueJob.mockRejectedValue(new Error('Storage error'));

      expect(() => offlineQueue.stopProcessing()).not.toThrow();
    });
  });

  describe('Network Monitoring', () => {
    test('should setup online event listener', () => {
      const addEventListenerSpy = jest.spyOn(self, 'addEventListener');

      offlineQueue.setupNetworkMonitoring();

      expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    });
  });

  describe('Notifications', () => {
    const mockJob = {
      id: 'job-123',
      toolName: 'test_tool',
      parameters: { text: 'test' }
    };

    test('should create notification on job completion', () => {
      chrome.notifications.create = jest.fn();

      offlineQueue.notifyJobCompleted(mockJob, { result: 'success' });

      expect(chrome.notifications.create).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'basic',
          title: expect.stringContaining('Completed')
        })
      );
    });

    test('should create notification on job failure', () => {
      chrome.notifications.create = jest.fn();

      offlineQueue.notifyJobFailed(mockJob, new Error('Test error'));

      expect(chrome.notifications.create).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'basic',
          title: expect.stringContaining('Failed')
        })
      );
    });
  });

  describe('Statistics', () => {
    test('should track processed jobs correctly', async () => {
      const jobs = [
        { id: 1, priority: 1, createdAt: 100, toolName: 'tool1' },
        { id: 2, priority: 1, createdAt: 200, toolName: 'tool2' }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);

      await offlineQueue.processQueue();

      expect(offlineQueue.stats.jobsProcessed).toBe(2);
      expect(offlineQueue.stats.jobsSucceeded).toBe(2);
    });

    test('should track failed jobs correctly', async () => {
      mockSmartRouter.executeTool.mockRejectedValue(new Error('Failed'));

      const job = {
        id: 'job-123',
        toolName: 'test_tool',
        parameters: {},
        retryCount: 2 // Will exceed max retries
      };

      await offlineQueue.processJob(job);

      expect(offlineQueue.stats.jobsProcessed).toBe(1);
      expect(offlineQueue.stats.jobsFailed).toBe(1);
    });
  });

  describe('Configuration', () => {
    test('should allow updating sync interval', () => {
      offlineQueue.config.syncIntervalMs = 60000;

      expect(offlineQueue.config.syncIntervalMs).toBe(60000);
    });

    test('should allow updating max retries', () => {
      offlineQueue.config.maxRetries = 5;

      expect(offlineQueue.config.maxRetries).toBe(5);
    });

    test('should allow disabling background sync', () => {
      offlineQueue.config.enableBackgroundSync = false;

      expect(offlineQueue.config.enableBackgroundSync).toBe(false);
    });
  });
});
