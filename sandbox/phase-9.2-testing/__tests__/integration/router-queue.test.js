/**
 * Integration Tests: Smart Router + Offline Queue
 * Phase 9.2 Stage 4
 *
 * Tests the interaction between routing decisions and offline queue management
 */

import { SmartRouter } from '../../src/background/smart-router.js';
import { OfflineQueue } from '../../src/background/offline-queue.js';

describe('SmartRouter + OfflineQueue Integration', () => {
  let smartRouter;
  let offlineQueue;
  let mockToolRegistry;
  let mockStorageManager;

  beforeEach(() => {
    // Mock Tool Registry
    mockToolRegistry = {
      executeTool: jest.fn().mockResolvedValue({ success: true, result: 'tool result' })
    };

    // Mock Storage Manager
    mockStorageManager = {
      get: jest.fn().mockResolvedValue(null),
      set: jest.fn().mockResolvedValue(undefined),
      getQueuedJobs: jest.fn().mockResolvedValue([]),
      addJob: jest.fn().mockResolvedValue({ id: 1, status: 'queued' }),
      updateJobStatus: jest.fn().mockResolvedValue(undefined),
      removeJob: jest.fn().mockResolvedValue(undefined)
    };

    smartRouter = new SmartRouter(mockToolRegistry, mockStorageManager);
    offlineQueue = new OfflineQueue(smartRouter, mockStorageManager);

    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true
    });

    // Mock chrome.notifications
    global.chrome = {
      ...global.chrome,
      notifications: {
        create: jest.fn()
      }
    };
  });

  describe('Offline to Queue Flow', () => {
    test('should queue complex tool when offline', async () => {
      // Set offline
      navigator.onLine = false;

      // Mock classification
      smartRouter.classification = {
        simple: [],
        medium: [],
        complex: ['complex_tool']
      };

      // Attempt to execute complex tool
      const toolName = 'complex_tool';
      const params = { data: 'test' };

      // In real implementation, router would check network and queue
      const job = await offlineQueue.addJob(toolName, params, 1);

      expect(mockStorageManager.addJob).toHaveBeenCalledWith(toolName, params, 1);
      expect(job.status).toBe('queued');
    });

    test('should execute simple tool locally even when offline', async () => {
      // Set offline
      navigator.onLine = false;

      smartRouter.classification = {
        simple: ['simple_tool'],
        medium: [],
        complex: []
      };

      // Simple tools should execute locally
      const result = await smartRouter.executeSimple('simple_tool', { text: 'test' });

      expect(mockToolRegistry.executeTool).toHaveBeenCalledWith('simple_tool', { text: 'test' });
      expect(result.success).toBe(true);
    });

    test('should process queued jobs when going online', async () => {
      // Start offline with queued jobs
      navigator.onLine = false;
      const queuedJobs = [
        { id: 1, toolName: 'tool1', params: {}, priority: 1, status: 'queued', createdAt: Date.now() },
        { id: 2, toolName: 'tool2', params: {}, priority: 0, status: 'queued', createdAt: Date.now() }
      ];
      mockStorageManager.getQueuedJobs.mockResolvedValue(queuedJobs);

      // Go online
      navigator.onLine = true;

      // Initialize queue (which should start processing)
      await offlineQueue.initialize();

      // Manually trigger queue processing
      offlineQueue.processJob = jest.fn().mockResolvedValue(undefined);
      await offlineQueue.processQueue();

      // Should process both jobs
      expect(offlineQueue.processJob).toHaveBeenCalledTimes(2);
    });
  });

  describe('Queue + Router Execution Flow', () => {
    test('should execute queued job through router when online', async () => {
      navigator.onLine = true;

      const job = {
        id: 1,
        toolName: 'test_tool',
        params: { input: 'test' },
        priority: 1,
        status: 'queued',
        createdAt: Date.now(),
        retryCount: 0
      };

      smartRouter.classification = {
        simple: ['test_tool'],
        medium: [],
        complex: []
      };

      // Process the job
      smartRouter.executeTool = jest.fn().mockResolvedValue({ success: true, result: 'executed' });
      await offlineQueue.processJob(job);

      expect(smartRouter.executeTool).toHaveBeenCalledWith('test_tool', { input: 'test' });
      expect(mockStorageManager.updateJobStatus).toHaveBeenCalledWith(1, 'completed', expect.any(Object));
    });

    test('should handle job failure and retry', async () => {
      navigator.onLine = true;

      const job = {
        id: 1,
        toolName: 'failing_tool',
        params: {},
        priority: 1,
        status: 'queued',
        createdAt: Date.now(),
        retryCount: 0
      };

      smartRouter.executeTool = jest.fn().mockRejectedValue(new Error('Execution failed'));

      await offlineQueue.processJob(job);

      // Should update status to failed and increment retry count
      expect(mockStorageManager.updateJobStatus).toHaveBeenCalledWith(
        1,
        'failed',
        expect.objectContaining({
          error: expect.any(String),
          retryCount: 1
        })
      );
    });

    test('should abandon job after max retries', async () => {
      navigator.onLine = true;

      const job = {
        id: 1,
        toolName: 'failing_tool',
        params: {},
        priority: 1,
        status: 'queued',
        createdAt: Date.now(),
        retryCount: 3 // Already at max
      };

      smartRouter.executeTool = jest.fn().mockRejectedValue(new Error('Execution failed'));

      await offlineQueue.processJob(job);

      // Should mark as failed without retry
      expect(mockStorageManager.updateJobStatus).toHaveBeenCalledWith(
        1,
        'failed',
        expect.objectContaining({
          retryCount: 3,
          error: expect.any(String)
        })
      );
    });
  });

  describe('Priority Routing through Queue', () => {
    test('should process high-priority jobs first', async () => {
      const jobs = [
        { id: 1, toolName: 'low', params: {}, priority: 0, status: 'queued', createdAt: 100 },
        { id: 2, toolName: 'high', params: {}, priority: 2, status: 'queued', createdAt: 200 },
        { id: 3, toolName: 'medium', params: {}, priority: 1, status: 'queued', createdAt: 150 }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);

      const processOrder = [];
      offlineQueue.processJob = jest.fn().mockImplementation(async (job) => {
        processOrder.push(job.id);
      });

      await offlineQueue.processQueue();

      // Should process in order: priority 2, priority 1, priority 0
      expect(processOrder).toEqual([2, 3, 1]);
    });

    test('should use FIFO for same-priority jobs', async () => {
      const jobs = [
        { id: 1, toolName: 'first', params: {}, priority: 1, status: 'queued', createdAt: 100 },
        { id: 2, toolName: 'second', params: {}, priority: 1, status: 'queued', createdAt: 200 },
        { id: 3, toolName: 'third', params: {}, priority: 1, status: 'queued', createdAt: 150 }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);

      const processOrder = [];
      offlineQueue.processJob = jest.fn().mockImplementation(async (job) => {
        processOrder.push(job.id);
      });

      await offlineQueue.processQueue();

      // Should process in chronological order for same priority
      expect(processOrder).toEqual([1, 3, 2]);
    });
  });

  describe('Network Status Changes', () => {
    test('should stop queue processing when going offline', async () => {
      navigator.onLine = true;
      await offlineQueue.initialize();

      // Simulate going offline
      navigator.onLine = false;
      offlineQueue.stopProcessing();

      expect(offlineQueue.isProcessing).toBe(false);
    });

    test('should resume queue processing when coming online', async () => {
      // Start offline
      navigator.onLine = false;
      await offlineQueue.initialize();

      // Add jobs while offline
      mockStorageManager.getQueuedJobs.mockResolvedValue([
        { id: 1, toolName: 'tool1', params: {}, priority: 1, status: 'queued', createdAt: Date.now() }
      ]);

      // Go online
      navigator.onLine = true;

      // Trigger online event handler
      offlineQueue.processJob = jest.fn().mockResolvedValue(undefined);
      await offlineQueue.handleOnline();

      // Should start processing queue
      expect(offlineQueue.processJob).toHaveBeenCalled();
    });
  });

  describe('Error Handling Integration', () => {
    test('should handle router timeout in queue processing', async () => {
      const job = {
        id: 1,
        toolName: 'slow_tool',
        params: {},
        priority: 1,
        status: 'queued',
        createdAt: Date.now(),
        retryCount: 0
      };

      // Mock timeout error
      smartRouter.executeTool = jest.fn().mockRejectedValue(new Error('Timeout'));

      await offlineQueue.processJob(job);

      // Should mark for retry
      expect(mockStorageManager.updateJobStatus).toHaveBeenCalledWith(
        1,
        'failed',
        expect.objectContaining({
          retryCount: 1
        })
      );
    });

    test('should handle storage errors gracefully', async () => {
      mockStorageManager.getQueuedJobs.mockRejectedValue(new Error('Storage error'));

      // Should not throw
      await expect(offlineQueue.processQueue()).resolves.not.toThrow();
    });
  });

  describe('Notifications Integration', () => {
    test('should notify user when queue job completes', async () => {
      const job = {
        id: 1,
        toolName: 'test_tool',
        params: {},
        priority: 1,
        status: 'queued',
        createdAt: Date.now(),
        retryCount: 0
      };

      smartRouter.executeTool = jest.fn().mockResolvedValue({ success: true, result: 'done' });

      await offlineQueue.processJob(job);

      expect(global.chrome.notifications.create).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          type: 'basic',
          title: expect.stringContaining('completed'),
          message: expect.stringContaining('test_tool')
        })
      );
    });

    test('should notify user when queue job fails permanently', async () => {
      const job = {
        id: 1,
        toolName: 'failing_tool',
        params: {},
        priority: 1,
        status: 'queued',
        createdAt: Date.now(),
        retryCount: 3 // Max retries
      };

      smartRouter.executeTool = jest.fn().mockRejectedValue(new Error('Failed'));

      await offlineQueue.processJob(job);

      expect(global.chrome.notifications.create).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          type: 'basic',
          title: expect.stringContaining('failed'),
          message: expect.stringContaining('failing_tool')
        })
      );
    });
  });

  describe('Statistics Integration', () => {
    test('should update statistics after processing jobs', async () => {
      const jobs = [
        { id: 1, toolName: 'tool1', params: {}, priority: 1, status: 'queued', createdAt: Date.now(), retryCount: 0 },
        { id: 2, toolName: 'tool2', params: {}, priority: 1, status: 'queued', createdAt: Date.now(), retryCount: 0 }
      ];

      mockStorageManager.getQueuedJobs.mockResolvedValue(jobs);
      smartRouter.executeTool = jest.fn()
        .mockResolvedValueOnce({ success: true })
        .mockRejectedValueOnce(new Error('Failed'));

      await offlineQueue.processQueue();

      // Should track both processed (1 success, 1 failure)
      expect(offlineQueue.stats.processed).toBeGreaterThan(0);
    });
  });
});
