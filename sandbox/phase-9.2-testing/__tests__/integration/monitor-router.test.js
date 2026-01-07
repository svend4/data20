/**
 * Integration Tests: Performance Monitor + Smart Router
 * Phase 9.2 Stage 4
 *
 * Tests the interaction between performance monitoring and routing decisions
 */

import { SmartRouter } from '../../src/background/smart-router.js';
import { PerformanceMonitor } from '../../src/utils/performance-monitor.js';

describe('PerformanceMonitor + SmartRouter Integration', () => {
  let smartRouter;
  let performanceMonitor;
  let mockToolRegistry;
  let mockStorageManager;

  beforeEach(() => {
    // Mock Tool Registry
    mockToolRegistry = {
      executeTool: jest.fn().mockResolvedValue({ success: true, result: 'result' })
    };

    // Mock Storage Manager
    mockStorageManager = {
      get: jest.fn().mockResolvedValue(null),
      set: jest.fn().mockResolvedValue(undefined)
    };

    smartRouter = new SmartRouter(mockToolRegistry, mockStorageManager);
    performanceMonitor = new PerformanceMonitor(mockStorageManager);

    smartRouter.classification = {
      simple: ['simple_tool'],
      medium: ['medium_tool'],
      complex: ['complex_tool']
    };

    // Mock performance.now for consistent timing
    let mockTime = 0;
    global.performance.now = jest.fn(() => {
      mockTime += 100; // Each call advances 100ms
      return mockTime;
    });
  });

  describe('Metrics Recording During Routing', () => {
    test('should record metrics for simple tool execution', async () => {
      const toolName = 'simple_tool';
      const params = { text: 'test' };

      const result = await smartRouter.executeTool(toolName, params);

      // Manually record in monitor (in real implementation, router would do this)
      performanceMonitor.recordToolExecution(
        toolName,
        'simple',
        'local',
        100,
        true,
        null
      );

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.executions).toBe(1);
      expect(metrics.tools.byTool[toolName]).toBeDefined();
      expect(metrics.tools.byComplexity.simple).toBeDefined();
      expect(metrics.routing.local.count).toBe(1);
    });

    test('should record metrics for medium tool execution', async () => {
      await smartRouter.executeTool('medium_tool', {});

      performanceMonitor.recordToolExecution(
        'medium_tool',
        'medium',
        'local',
        150,
        true,
        null
      );

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.byComplexity.medium).toBeDefined();
      expect(metrics.routing.local.count).toBe(1);
    });

    test('should record metrics for complex tool cloud execution', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, result: 'cloud result', executionTime: 200 })
      });

      await smartRouter.executeTool('complex_tool', {});

      performanceMonitor.recordToolExecution(
        'complex_tool',
        'complex',
        'cloud',
        200,
        true,
        null
      );

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.byComplexity.complex).toBeDefined();
      expect(metrics.routing.cloud.count).toBe(1);
    });
  });

  describe('Cache Metrics Integration', () => {
    test('should track cache hits in both systems', async () => {
      // Mock cache hit
      const cachedData = {
        cached: true,
        result: { success: true, result: 'cached' },
        timestamp: Date.now(),
        ttl: 300000
      };
      mockStorageManager.get.mockResolvedValue(cachedData);

      await smartRouter.executeTool('simple_tool', {});

      // Record cache hit
      performanceMonitor.recordCache(true);

      expect(smartRouter.metrics.cache.hits).toBe(1);
      expect(performanceMonitor.metrics.routing.cache.hits).toBe(1);
    });

    test('should track cache misses in both systems', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('simple_tool', {});

      // Record cache miss
      performanceMonitor.recordCache(false);

      expect(smartRouter.metrics.cache.misses).toBe(1);
      expect(performanceMonitor.metrics.routing.cache.misses).toBe(1);
    });

    test('should calculate cache hit rate accurately', async () => {
      // 2 hits, 3 misses
      performanceMonitor.recordCache(true);
      performanceMonitor.recordCache(true);
      performanceMonitor.recordCache(false);
      performanceMonitor.recordCache(false);
      performanceMonitor.recordCache(false);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.routing.cache.hits).toBe(2);
      expect(metrics.routing.cache.misses).toBe(3);
      expect(metrics.summary.cacheHitRate).toBeCloseTo(0.4); // 2/5 = 40%
    });
  });

  describe('Error Tracking Integration', () => {
    test('should record tool execution errors', async () => {
      mockToolRegistry.executeTool.mockRejectedValue(new Error('Tool execution failed'));

      try {
        await smartRouter.executeTool('simple_tool', {});
      } catch (error) {
        performanceMonitor.recordError(error, { tool: 'simple_tool', operation: 'execute' });
      }

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.errors.total).toBe(1);
      expect(metrics.errors.byType.Error).toBe(1);
      expect(metrics.errors.recent[0].message).toBe('Tool execution failed');
    });

    test('should track routing errors separately', async () => {
      mockToolRegistry.executeTool.mockRejectedValue(new Error('Network timeout'));

      try {
        await smartRouter.executeTool('complex_tool', {});
      } catch (error) {
        performanceMonitor.recordError(error, { tool: 'complex_tool', operation: 'route' });
      }

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.errors.total).toBe(1);
      expect(metrics.errors.recent[0].context.operation).toBe('route');
    });

    test('should calculate error rate', async () => {
      // 3 successful executions
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool3', 'simple', 'local', 100, true, null);

      // 2 errors
      performanceMonitor.recordError(new Error('Error 1'));
      performanceMonitor.recordError(new Error('Error 2'));

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.summary.errorRate).toBeCloseTo(0.4); // 2/(3+2) = 40%
    });
  });

  describe('Execution Time Tracking', () => {
    test('should track execution time for different routing locations', async () => {
      // Local execution
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 50, true, null);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, true, null);

      // Cloud execution
      performanceMonitor.recordToolExecution('tool3', 'complex', 'cloud', 200, true, null);
      performanceMonitor.recordToolExecution('tool4', 'complex', 'cloud', 300, true, null);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.routing.local.totalTime).toBe(150); // 50 + 100
      expect(metrics.routing.local.avgTime).toBe(75); // (50 + 100) / 2
      expect(metrics.routing.cloud.totalTime).toBe(500); // 200 + 300
      expect(metrics.routing.cloud.avgTime).toBe(250); // (200 + 300) / 2
    });

    test('should track average execution time per tool', async () => {
      performanceMonitor.recordToolExecution('word_count', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('word_count', 'simple', 'local', 200, true, null);
      performanceMonitor.recordToolExecution('sentiment', 'medium', 'local', 300, true, null);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.byTool.word_count.avgTime).toBe(150); // (100 + 200) / 2
      expect(metrics.tools.byTool.sentiment.avgTime).toBe(300);
    });

    test('should calculate overall average execution time', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool2', 'medium', 'local', 200, true, null);
      performanceMonitor.recordToolExecution('tool3', 'complex', 'cloud', 300, true, null);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.summary.avgExecutionTime).toBe(200); // (100 + 200 + 300) / 3
    });
  });

  describe('Routing Distribution Tracking', () => {
    test('should track distribution across routing locations', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool3', 'complex', 'cloud', 200, true, null);
      performanceMonitor.recordToolExecution('tool4', 'medium', 'cache', 10, true, null);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.routing.local.count).toBe(2);
      expect(metrics.routing.cloud.count).toBe(1);
      expect(metrics.routing.cache.count).toBe(1);
    });

    test('should track complexity distribution', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool3', 'medium', 'local', 150, true, null);
      performanceMonitor.recordToolExecution('tool4', 'complex', 'cloud', 200, true, null);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.byComplexity.simple.count).toBe(2);
      expect(metrics.tools.byComplexity.medium.count).toBe(1);
      expect(metrics.tools.byComplexity.complex.count).toBe(1);
    });
  });

  describe('Top Tools Tracking', () => {
    test('should identify most frequently used tools', async () => {
      performanceMonitor.recordToolExecution('word_count', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('word_count', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('word_count', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('sentiment', 'medium', 'local', 150, true, null);
      performanceMonitor.recordToolExecution('sentiment', 'medium', 'local', 150, true, null);
      performanceMonitor.recordToolExecution('tokenize', 'simple', 'local', 80, true, null);

      const metrics = performanceMonitor.getMetrics();
      const topTools = metrics.summary.topTools;

      expect(topTools[0].tool).toBe('word_count');
      expect(topTools[0].count).toBe(3);
      expect(topTools[1].tool).toBe('sentiment');
      expect(topTools[1].count).toBe(2);
    });

    test('should limit top tools list', async () => {
      // Execute 20 different tools
      for (let i = 0; i < 20; i++) {
        performanceMonitor.recordToolExecution(`tool${i}`, 'simple', 'local', 100, true, null);
      }

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.summary.topTools.length).toBeLessThanOrEqual(10);
    });
  });

  describe('Success/Failure Tracking', () => {
    test('should track successful executions', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, true, null);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.executions).toBe(2);
      expect(metrics.routing.local.successCount).toBe(2);
    });

    test('should track failed executions', async () => {
      const error = new Error('Execution failed');

      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, false, error);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, false, error);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.executions).toBe(2);
      expect(metrics.routing.local.failureCount).toBe(2);
    });

    test('should calculate success rate per routing location', async () => {
      // 3 successes, 1 failure in local
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool2', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool3', 'simple', 'local', 100, true, null);
      performanceMonitor.recordToolExecution('tool4', 'simple', 'local', 100, false, new Error('Failed'));

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.routing.local.successRate).toBeCloseTo(0.75); // 3/4 = 75%
    });
  });

  describe('Memory Monitoring During Routing', () => {
    test('should sample memory during tool execution', async () => {
      global.performance.memory = {
        usedJSHeapSize: 10 * 1024 * 1024 // 10MB
      };

      performanceMonitor.sampleMemory();

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.resources.memorySamples.length).toBe(1);
      expect(metrics.resources.peakMemory).toBeGreaterThan(0);
    });

    test('should track peak memory across multiple executions', async () => {
      global.performance.memory = {
        usedJSHeapSize: 10 * 1024 * 1024
      };
      performanceMonitor.sampleMemory();

      global.performance.memory = {
        usedJSHeapSize: 20 * 1024 * 1024
      };
      performanceMonitor.sampleMemory();

      global.performance.memory = {
        usedJSHeapSize: 15 * 1024 * 1024
      };
      performanceMonitor.sampleMemory();

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.resources.peakMemory).toBeCloseTo(20); // 20MB peak
    });
  });

  describe('Session Metrics', () => {
    test('should track session start time', async () => {
      performanceMonitor.sessionStart = Date.now();

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.session.startTime).toBeDefined();
    });

    test('should calculate session duration', async () => {
      const startTime = Date.now() - 60000; // 1 minute ago
      performanceMonitor.sessionStart = startTime;

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.session.duration).toBeGreaterThanOrEqual(60000);
    });
  });

  describe('Metrics Export Integration', () => {
    test('should export complete metrics in JSON format', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordCache(true);
      performanceMonitor.recordError(new Error('Test error'));

      const exported = performanceMonitor.exportAsJSON();
      const parsed = JSON.parse(exported);

      expect(parsed.tools).toBeDefined();
      expect(parsed.routing).toBeDefined();
      expect(parsed.errors).toBeDefined();
      expect(parsed.summary).toBeDefined();
    });

    test('should export complete metrics in CSV format', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);

      const csv = performanceMonitor.exportAsCSV();

      expect(csv).toContain('tool1');
      expect(csv).toContain('simple');
      expect(csv).toContain('local');
      expect(csv).toContain('100');
    });
  });

  describe('Metrics Persistence Integration', () => {
    test('should persist metrics to storage', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);

      await performanceMonitor.persistMetrics();

      expect(mockStorageManager.set).toHaveBeenCalled();
      const savedData = mockStorageManager.set.mock.calls[0][1];

      expect(savedData.metrics).toBeDefined();
      expect(savedData.timestamp).toBeDefined();
    });

    test('should load historical metrics from storage', async () => {
      const historicalData = {
        metrics: {
          tools: { executions: 5, totalTime: 500 }
        },
        timestamp: Date.now() - 3600000
      };

      mockStorageManager.get.mockResolvedValue(historicalData);

      await performanceMonitor.loadHistoricalMetrics();

      // Should have loaded historical data
      expect(performanceMonitor.historicalData).toBeDefined();
    });
  });

  describe('Reset Functionality', () => {
    test('should reset metrics while preserving configuration', async () => {
      performanceMonitor.recordToolExecution('tool1', 'simple', 'local', 100, true, null);
      performanceMonitor.recordCache(true);
      performanceMonitor.recordError(new Error('Test'));

      const originalConfig = { ...performanceMonitor.config };

      performanceMonitor.resetMetrics();

      const metrics = performanceMonitor.getMetrics();

      expect(metrics.tools.executions).toBe(0);
      expect(metrics.routing.cache.hits).toBe(0);
      expect(metrics.errors.total).toBe(0);
      expect(performanceMonitor.config).toEqual(originalConfig);
    });
  });

  describe('Real-world Scenario: Mixed Workload', () => {
    test('should accurately track complex mixed workload', async () => {
      // Simulate real workload
      performanceMonitor.recordToolExecution('word_count', 'simple', 'local', 50, true, null);
      performanceMonitor.recordCache(true);
      performanceMonitor.recordToolExecution('sentiment', 'medium', 'local', 150, true, null);
      performanceMonitor.recordCache(false);
      performanceMonitor.recordToolExecution('ml_classify', 'complex', 'cloud', 300, true, null);
      performanceMonitor.recordToolExecution('tokenize', 'simple', 'local', 40, false, new Error('Failed'));
      performanceMonitor.recordError(new Error('Failed'));
      performanceMonitor.recordCache(true);

      const metrics = performanceMonitor.getMetrics();

      // Verify comprehensive metrics
      expect(metrics.tools.executions).toBe(4);
      expect(metrics.routing.local.count).toBe(3);
      expect(metrics.routing.cloud.count).toBe(1);
      expect(metrics.routing.cache.hits).toBe(2);
      expect(metrics.routing.cache.misses).toBe(1);
      expect(metrics.errors.total).toBe(1);
      expect(metrics.summary.cacheHitRate).toBeCloseTo(0.67, 1); // 2/3
    });
  });
});
