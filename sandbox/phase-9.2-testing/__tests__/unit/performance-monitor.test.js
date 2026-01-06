/**
 * Performance Monitor Unit Tests - Phase 9.2 Stage 3
 * Comprehensive test suite for performance monitoring and analytics
 */

import { PerformanceMonitor } from '../../src/utils/performance-monitor.js';

describe('PerformanceMonitor', () => {
  let performanceMonitor;
  let mockStorageManager;

  beforeEach(() => {
    // Mock Storage Manager
    mockStorageManager = {
      saveSetting: jest.fn().mockResolvedValue(undefined),
      getSetting: jest.fn().mockResolvedValue(null)
    };

    performanceMonitor = new PerformanceMonitor(mockStorageManager);
  });

  afterEach(() => {
    // Clean up intervals
    if (performanceMonitor.memorySampleInterval) {
      clearInterval(performanceMonitor.memorySampleInterval);
    }
    if (performanceMonitor.persistInterval) {
      clearInterval(performanceMonitor.persistInterval);
    }
  });

  describe('Constructor', () => {
    test('should initialize with storage manager', () => {
      expect(performanceMonitor.storage).toBe(mockStorageManager);
    });

    test('should initialize empty metrics structure', () => {
      expect(performanceMonitor.metrics.tools.executions).toBe(0);
      expect(performanceMonitor.metrics.tools.totalTime).toBe(0);
      expect(performanceMonitor.metrics.tools.byTool).toEqual({});
      expect(performanceMonitor.metrics.errors.total).toBe(0);
    });

    test('should initialize default configuration', () => {
      expect(performanceMonitor.config).toEqual({
        memorySampleInterval: 60000,
        maxRecentErrors: 50,
        persistMetricsInterval: 300000,
        enableDetailedTracking: true
      });
    });

    test('should set session start time', () => {
      const beforeTime = Date.now();
      const monitor = new PerformanceMonitor(mockStorageManager);
      const afterTime = Date.now();

      expect(monitor.metrics.session.startTime).toBeGreaterThanOrEqual(beforeTime);
      expect(monitor.metrics.session.startTime).toBeLessThanOrEqual(afterTime);
    });

    test('should initialize interval references as null', () => {
      expect(performanceMonitor.memorySampleInterval).toBeNull();
      expect(performanceMonitor.persistInterval).toBeNull();
    });
  });

  describe('initialize()', () => {
    beforeEach(() => {
      performanceMonitor.loadHistoricalMetrics = jest.fn().mockResolvedValue(undefined);
      performanceMonitor.startMemorySampling = jest.fn();
      performanceMonitor.startPeriodicPersistence = jest.fn();
    });

    test('should call all initialization methods', async () => {
      await performanceMonitor.initialize();

      expect(performanceMonitor.loadHistoricalMetrics).toHaveBeenCalled();
      expect(performanceMonitor.startMemorySampling).toHaveBeenCalled();
      expect(performanceMonitor.startPeriodicPersistence).toHaveBeenCalled();
    });

    test('should complete successfully', async () => {
      await expect(performanceMonitor.initialize()).resolves.toBeUndefined();
    });
  });

  describe('recordToolExecution()', () => {
    test('should increment total executions', () => {
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 100);

      expect(performanceMonitor.metrics.tools.executions).toBe(1);
    });

    test('should add to total time', () => {
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 150);
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 250);

      expect(performanceMonitor.metrics.tools.totalTime).toBe(400);
    });

    test('should create entry for new tool', () => {
      performanceMonitor.recordToolExecution('new_tool', 'simple', 'local', 100);

      expect(performanceMonitor.metrics.tools.byTool['new_tool']).toBeDefined();
      expect(performanceMonitor.metrics.tools.byTool['new_tool'].count).toBe(1);
      expect(performanceMonitor.metrics.tools.byTool['new_tool'].totalTime).toBe(100);
    });

    test('should update existing tool metrics', () => {
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 100);
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 200);

      const toolMetrics = performanceMonitor.metrics.tools.byTool['test_tool'];
      expect(toolMetrics.count).toBe(2);
      expect(toolMetrics.totalTime).toBe(300);
      expect(toolMetrics.avgTime).toBe(150);
    });

    test('should calculate average time correctly', () => {
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 100);
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 200);
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 300);

      const avgTime = performanceMonitor.metrics.tools.byTool['test_tool'].avgTime;
      expect(avgTime).toBe(200); // (100 + 200 + 300) / 3
    });

    test('should record last execution timestamp', () => {
      const beforeTime = Date.now();
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 100);
      const afterTime = Date.now();

      const lastExecution = performanceMonitor.metrics.tools.byTool['test_tool'].lastExecution;
      expect(lastExecution).toBeGreaterThanOrEqual(beforeTime);
      expect(lastExecution).toBeLessThanOrEqual(afterTime);
    });

    test('should increment error count on failure', () => {
      performanceMonitor.recordToolExecution('test_tool', 'simple', 'local', 100, false);

      expect(performanceMonitor.metrics.tools.byTool['test_tool'].errors).toBe(1);
    });

    test('should update complexity metrics', () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 200);

      expect(performanceMonitor.metrics.tools.byComplexity.simple.count).toBe(2);
      expect(performanceMonitor.metrics.tools.byComplexity.simple.totalTime).toBe(300);
    });

    test('should track complexity errors', () => {
      performanceMonitor.recordToolExecution('tool', 'medium', 'local', 100, false);

      expect(performanceMonitor.metrics.tools.byComplexity.medium.errors).toBe(1);
    });

    test('should update local routing metrics', () => {
      performanceMonitor.recordToolExecution('tool', 'simple', 'local', 150);

      expect(performanceMonitor.metrics.routing.local.count).toBe(1);
      expect(performanceMonitor.metrics.routing.local.totalTime).toBe(150);
    });

    test('should update cloud routing metrics', () => {
      performanceMonitor.recordToolExecution('tool', 'complex', 'cloud', 500);

      expect(performanceMonitor.metrics.routing.cloud.count).toBe(1);
      expect(performanceMonitor.metrics.routing.cloud.totalTime).toBe(500);
    });

    test('should update cache hits for cache location', () => {
      performanceMonitor.recordToolExecution('tool', 'simple', 'cache', 10);

      expect(performanceMonitor.metrics.routing.cache.hits).toBe(1);
    });

    test('should update queued count', () => {
      performanceMonitor.recordToolExecution('tool', 'medium', 'queued', 0);

      expect(performanceMonitor.metrics.routing.queued.count).toBe(1);
    });

    test('should record error if provided', () => {
      performanceMonitor.recordError = jest.fn();
      const error = new Error('Test error');

      performanceMonitor.recordToolExecution('tool', 'simple', 'local', 100, false, error);

      expect(performanceMonitor.recordError).toHaveBeenCalledWith(error, 'tool');
    });

    test('should increment routing errors on failure', () => {
      performanceMonitor.recordToolExecution('tool', 'simple', 'local', 100, false);

      expect(performanceMonitor.metrics.routing.local.errors).toBe(1);
    });
  });

  describe('recordCache()', () => {
    test('should increment cache hits when true', () => {
      performanceMonitor.recordCache(true);

      expect(performanceMonitor.metrics.routing.cache.hits).toBe(1);
    });

    test('should increment cache misses when false', () => {
      performanceMonitor.recordCache(false);

      expect(performanceMonitor.metrics.routing.cache.misses).toBe(1);
    });

    test('should track multiple cache operations', () => {
      performanceMonitor.recordCache(true);
      performanceMonitor.recordCache(true);
      performanceMonitor.recordCache(false);

      expect(performanceMonitor.metrics.routing.cache.hits).toBe(2);
      expect(performanceMonitor.metrics.routing.cache.misses).toBe(1);
    });
  });

  describe('recordError()', () => {
    test('should increment total errors', () => {
      performanceMonitor.recordError(new Error('Test error'));

      expect(performanceMonitor.metrics.errors.total).toBe(1);
    });

    test('should categorize errors by type', () => {
      const error = new Error('Test error');
      error.name = 'TypeError';

      performanceMonitor.recordError(error);

      expect(performanceMonitor.metrics.errors.byType['TypeError']).toBe(1);
    });

    test('should handle errors without name', () => {
      const error = new Error('Test');
      delete error.name;

      performanceMonitor.recordError(error);

      expect(performanceMonitor.metrics.errors.byType['UnknownError']).toBe(1);
    });

    test('should store recent errors with timestamp', () => {
      const error = new Error('Test error');

      performanceMonitor.recordError(error, 'test_context');

      expect(performanceMonitor.metrics.errors.recent.length).toBe(1);
      expect(performanceMonitor.metrics.errors.recent[0]).toMatchObject({
        type: 'Error',
        message: 'Test error',
        context: 'test_context'
      });
    });

    test('should limit recent errors to maxRecentErrors', () => {
      performanceMonitor.config.maxRecentErrors = 3;

      for (let i = 0; i < 5; i++) {
        performanceMonitor.recordError(new Error(`Error ${i}`));
      }

      expect(performanceMonitor.metrics.errors.recent.length).toBe(3);
    });

    test('should keep most recent errors when limiting', () => {
      performanceMonitor.config.maxRecentErrors = 2;

      performanceMonitor.recordError(new Error('Error 1'));
      performanceMonitor.recordError(new Error('Error 2'));
      performanceMonitor.recordError(new Error('Error 3'));

      expect(performanceMonitor.metrics.errors.recent[0].message).toBe('Error 3');
      expect(performanceMonitor.metrics.errors.recent[1].message).toBe('Error 2');
    });

    test('should increment count for duplicate error types', () => {
      performanceMonitor.recordError(new TypeError('Error 1'));
      performanceMonitor.recordError(new TypeError('Error 2'));

      expect(performanceMonitor.metrics.errors.byType['TypeError']).toBe(2);
    });
  });

  describe('sampleMemory()', () => {
    test('should sample memory if performance.memory available', () => {
      global.performance.memory = {
        usedJSHeapSize: 10 * 1024 * 1024 // 10 MB
      };

      performanceMonitor.sampleMemory();

      expect(performanceMonitor.metrics.resources.memorySamples.length).toBe(1);
      expect(performanceMonitor.metrics.resources.memorySamples[0].value).toBeCloseTo(10, 1);
    });

    test('should update peak memory', () => {
      global.performance.memory = {
        usedJSHeapSize: 15 * 1024 * 1024 // 15 MB
      };

      performanceMonitor.sampleMemory();

      expect(performanceMonitor.metrics.resources.peakMemory).toBeCloseTo(15, 1);
    });

    test('should update peak only if higher', () => {
      global.performance.memory = { usedJSHeapSize: 20 * 1024 * 1024 };
      performanceMonitor.sampleMemory();

      global.performance.memory = { usedJSHeapSize: 15 * 1024 * 1024 };
      performanceMonitor.sampleMemory();

      expect(performanceMonitor.metrics.resources.peakMemory).toBeCloseTo(20, 1);
    });

    test('should calculate average memory', () => {
      global.performance.memory = { usedJSHeapSize: 10 * 1024 * 1024 };
      performanceMonitor.sampleMemory();

      global.performance.memory = { usedJSHeapSize: 20 * 1024 * 1024 };
      performanceMonitor.sampleMemory();

      expect(performanceMonitor.metrics.resources.avgMemory).toBeCloseTo(15, 1);
    });

    test('should limit samples to 100', () => {
      global.performance.memory = { usedJSHeapSize: 10 * 1024 * 1024 };

      for (let i = 0; i < 150; i++) {
        performanceMonitor.sampleMemory();
      }

      expect(performanceMonitor.metrics.resources.memorySamples.length).toBe(100);
    });

    test('should do nothing if performance.memory not available', () => {
      global.performance.memory = undefined;

      performanceMonitor.sampleMemory();

      expect(performanceMonitor.metrics.resources.memorySamples.length).toBe(0);
    });
  });

  describe('startMemorySampling()', () => {
    test('should take initial sample', () => {
      performanceMonitor.sampleMemory = jest.fn();

      performanceMonitor.startMemorySampling();

      expect(performanceMonitor.sampleMemory).toHaveBeenCalled();
    });

    test('should start interval', () => {
      performanceMonitor.startMemorySampling();

      expect(performanceMonitor.memorySampleInterval).not.toBeNull();
    });

    test('should sample at configured interval', async () => {
      jest.useFakeTimers();
      performanceMonitor.sampleMemory = jest.fn();

      performanceMonitor.startMemorySampling();

      await jest.advanceTimersByTimeAsync(60000);

      expect(performanceMonitor.sampleMemory).toHaveBeenCalledTimes(2); // Initial + 1 interval

      jest.useRealTimers();
    });
  });

  describe('stopMemorySampling()', () => {
    test('should clear interval', () => {
      performanceMonitor.memorySampleInterval = setInterval(() => {}, 1000);

      performanceMonitor.stopMemorySampling();

      expect(performanceMonitor.memorySampleInterval).toBeNull();
    });

    test('should handle null interval gracefully', () => {
      performanceMonitor.memorySampleInterval = null;

      expect(() => performanceMonitor.stopMemorySampling()).not.toThrow();
    });
  });

  describe('persistMetrics()', () => {
    beforeEach(() => {
      performanceMonitor.getMetrics = jest.fn().mockReturnValue({ summary: { totalExecutions: 10 } });
    });

    test('should save metrics to storage', async () => {
      await performanceMonitor.persistMetrics();

      expect(mockStorageManager.saveSetting).toHaveBeenCalledWith(
        'performance_metrics',
        expect.objectContaining({
          metrics: expect.any(Object),
          timestamp: expect.any(Number)
        })
      );
    });

    test('should include session duration', async () => {
      performanceMonitor.metrics.session.startTime = Date.now() - 5000;

      await performanceMonitor.persistMetrics();

      const savedData = mockStorageManager.saveSetting.mock.calls[0][1];
      expect(savedData.sessionDuration).toBeGreaterThanOrEqual(5000);
    });

    test('should handle storage errors gracefully', async () => {
      mockStorageManager.saveSetting.mockRejectedValue(new Error('Storage error'));

      await expect(performanceMonitor.persistMetrics()).resolves.toBeUndefined();
    });
  });

  describe('loadHistoricalMetrics()', () => {
    test('should load from storage', async () => {
      await performanceMonitor.loadHistoricalMetrics();

      expect(mockStorageManager.getSetting).toHaveBeenCalledWith('performance_metrics');
    });

    test('should handle missing data gracefully', async () => {
      mockStorageManager.getSetting.mockResolvedValue(null);

      await expect(performanceMonitor.loadHistoricalMetrics()).resolves.toBeUndefined();
    });

    test('should handle storage errors gracefully', async () => {
      mockStorageManager.getSetting.mockRejectedValue(new Error('Storage error'));

      await expect(performanceMonitor.loadHistoricalMetrics()).resolves.toBeUndefined();
    });
  });

  describe('getMetrics()', () => {
    beforeEach(() => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'cloud', 200);
      performanceMonitor.recordCache(true);
      performanceMonitor.recordCache(false);
    });

    test('should return summary with total executions', () => {
      const metrics = performanceMonitor.getMetrics();

      expect(metrics.summary.totalExecutions).toBe(2);
    });

    test('should calculate average execution time', () => {
      const metrics = performanceMonitor.getMetrics();

      expect(metrics.summary.avgExecutionTime).toBe(150); // (100 + 200) / 2
    });

    test('should calculate cache hit rate', () => {
      const metrics = performanceMonitor.getMetrics();

      expect(metrics.summary.cacheHitRate).toBe('50.0'); // 1 hit / 2 total
    });

    test('should calculate error rate', () => {
      performanceMonitor.recordToolExecution('tool', 'simple', 'local', 100, false);

      const metrics = performanceMonitor.getMetrics();

      expect(parseFloat(metrics.summary.errorRate)).toBeCloseTo(33.33, 1); // 1 error / 3 executions
    });

    test('should return top tools sorted by count', () => {
      performanceMonitor.recordToolExecution('popular_tool', 'simple', 'local', 50);
      performanceMonitor.recordToolExecution('popular_tool', 'simple', 'local', 50);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.topTools[0].name).toBe('popular_tool');
      expect(metrics.tools.topTools[0].count).toBe(2);
    });

    test('should limit top tools to 10', () => {
      for (let i = 0; i < 15; i++) {
        performanceMonitor.recordToolExecution(`tool${i}`, 'simple', 'local', 100);
      }

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.topTools.length).toBeLessThanOrEqual(10);
    });

    test('should handle zero executions gracefully', () => {
      const emptyMonitor = new PerformanceMonitor(mockStorageManager);
      const metrics = emptyMonitor.getMetrics();

      expect(metrics.summary.avgExecutionTime).toBe(0);
      expect(metrics.summary.errorRate).toBe('0.00');
      expect(metrics.summary.cacheHitRate).toBe('0.0');
    });
  });

  describe('resetMetrics()', () => {
    beforeEach(() => {
      performanceMonitor.recordToolExecution('tool', 'simple', 'local', 100);
      performanceMonitor.recordError(new Error('Test'));
      performanceMonitor.sampleMemory();
    });

    test('should reset all tool metrics', () => {
      performanceMonitor.resetMetrics();

      expect(performanceMonitor.metrics.tools.executions).toBe(0);
      expect(performanceMonitor.metrics.tools.totalTime).toBe(0);
      expect(performanceMonitor.metrics.tools.byTool).toEqual({});
    });

    test('should reset error metrics', () => {
      performanceMonitor.resetMetrics();

      expect(performanceMonitor.metrics.errors.total).toBe(0);
      expect(performanceMonitor.metrics.errors.byType).toEqual({});
      expect(performanceMonitor.metrics.errors.recent).toEqual([]);
    });

    test('should reset routing metrics', () => {
      performanceMonitor.resetMetrics();

      expect(performanceMonitor.metrics.routing.local.count).toBe(0);
      expect(performanceMonitor.metrics.routing.cloud.count).toBe(0);
      expect(performanceMonitor.metrics.routing.cache.hits).toBe(0);
    });

    test('should update session start time', () => {
      const beforeReset = performanceMonitor.metrics.session.startTime;

      await new Promise(resolve => setTimeout(resolve, 10));

      performanceMonitor.resetMetrics();

      expect(performanceMonitor.metrics.session.startTime).toBeGreaterThan(beforeReset);
    });

    test('should preserve configuration', () => {
      const originalConfig = { ...performanceMonitor.config };

      performanceMonitor.resetMetrics();

      expect(performanceMonitor.config).toEqual(originalConfig);
    });
  });

  describe('Configuration', () => {
    test('should allow updating memory sample interval', () => {
      performanceMonitor.config.memorySampleInterval = 30000;

      expect(performanceMonitor.config.memorySampleInterval).toBe(30000);
    });

    test('should allow updating max recent errors', () => {
      performanceMonitor.config.maxRecentErrors = 100;

      expect(performanceMonitor.config.maxRecentErrors).toBe(100);
    });

    test('should allow disabling detailed tracking', () => {
      performanceMonitor.config.enableDetailedTracking = false;

      expect(performanceMonitor.config.enableDetailedTracking).toBe(false);
    });
  });
});
