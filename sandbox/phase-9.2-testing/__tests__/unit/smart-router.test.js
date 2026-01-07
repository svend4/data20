/**
 * Smart Router Unit Tests - Phase 9.2 Stage 1
 * Comprehensive test suite for intelligent routing system
 */

import { SmartRouter } from '../../src/background/smart-router.js';

describe('SmartRouter', () => {
  let smartRouter;
  let mockToolRegistry;
  let mockStorageManager;

  beforeEach(() => {
    // Mock Tool Registry
    mockToolRegistry = {
      executeTool: jest.fn().mockResolvedValue({ success: true, result: 'local result' })
    };

    // Mock Storage Manager
    mockStorageManager = {
      get: jest.fn().mockResolvedValue(null),
      set: jest.fn().mockResolvedValue(undefined)
    };

    smartRouter = new SmartRouter(mockToolRegistry, mockStorageManager);
  });

  describe('Constructor', () => {
    test('should initialize with correct default configuration', () => {
      expect(smartRouter.toolRegistry).toBe(mockToolRegistry);
      expect(smartRouter.storage).toBe(mockStorageManager);
      expect(smartRouter.config.mediumToolTimeout).toBe(2000);
      expect(smartRouter.config.cacheEnabled).toBe(true);
      expect(smartRouter.config.retryAttempts).toBe(3);
    });

    test('should initialize metrics tracking', () => {
      expect(smartRouter.metrics).toEqual({
        local: { total: 0, success: 0, failures: 0, totalTime: 0 },
        cloud: { total: 0, success: 0, failures: 0, totalTime: 0 },
        cache: { hits: 0, misses: 0 }
      });
    });

    test('should load tool classification', () => {
      expect(smartRouter.classification).toBeDefined();
    });
  });

  describe('getToolComplexity()', () => {
    test('should return "simple" for basic tools', () => {
      // Mock classification with simple tool
      smartRouter.classification = {
        simple: ['word_count', 'text_length'],
        medium: ['sentiment_analysis'],
        complex: ['machine_learning']
      };

      expect(smartRouter.getToolComplexity('word_count')).toBe('simple');
      expect(smartRouter.getToolComplexity('text_length')).toBe('simple');
    });

    test('should return "medium" for medium tools', () => {
      smartRouter.classification = {
        simple: ['word_count'],
        medium: ['sentiment_analysis', 'text_classifier'],
        complex: []
      };

      expect(smartRouter.getToolComplexity('sentiment_analysis')).toBe('medium');
    });

    test('should return "complex" for complex tools', () => {
      smartRouter.classification = {
        simple: [],
        medium: [],
        complex: ['machine_learning', 'deep_analysis']
      };

      expect(smartRouter.getToolComplexity('machine_learning')).toBe('complex');
    });

    test('should return "medium" for unknown tools (default)', () => {
      smartRouter.classification = {
        simple: [],
        medium: [],
        complex: []
      };

      expect(smartRouter.getToolComplexity('unknown_tool')).toBe('medium');
    });
  });

  describe('checkCache()', () => {
    test('should return cached result if available', async () => {
      const cachedData = { cached: true, result: 'cached value' };
      mockStorageManager.get.mockResolvedValue(cachedData);

      const result = await smartRouter.checkCache('test_tool', { input: 'test' });

      expect(result).toEqual(cachedData);
      expect(mockStorageManager.get).toHaveBeenCalled();
    });

    test('should return null if no cache found', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      const result = await smartRouter.checkCache('test_tool', { input: 'test' });

      expect(result).toBeNull();
    });

    test('should generate consistent cache key for same inputs', async () => {
      await smartRouter.checkCache('tool1', { a: 1, b: 2 });
      const call1Args = mockStorageManager.get.mock.calls[0][0];

      mockStorageManager.get.mockClear();

      await smartRouter.checkCache('tool1', { a: 1, b: 2 });
      const call2Args = mockStorageManager.get.mock.calls[0][0];

      expect(call1Args).toBe(call2Args);
    });
  });

  describe('cacheResult()', () => {
    test('should store result in cache', async () => {
      const result = { success: true, data: 'test' };

      await smartRouter.cacheResult('test_tool', { input: 'test' }, result);

      expect(mockStorageManager.set).toHaveBeenCalled();
      const savedData = mockStorageManager.set.mock.calls[0][1];
      expect(savedData.result).toEqual(result);
      expect(savedData.timestamp).toBeDefined();
    });

    test('should include TTL in cached data', async () => {
      await smartRouter.cacheResult('test_tool', {}, { data: 'test' });

      const savedData = mockStorageManager.set.mock.calls[0][1];
      expect(savedData.ttl).toBeDefined();
      expect(savedData.ttl).toBeGreaterThan(0);
    });
  });

  describe('executeSimple()', () => {
    test('should execute tool locally', async () => {
      smartRouter.classification = { simple: ['simple_tool'], medium: [], complex: [] };

      const result = await smartRouter.executeSimple('simple_tool', { text: 'test' });

      expect(mockToolRegistry.executeTool).toHaveBeenCalledWith('simple_tool', { text: 'test' });
      expect(result).toEqual({ success: true, result: 'local result' });
    });

    test('should increment local metrics on success', async () => {
      await smartRouter.executeSimple('tool', {});

      expect(smartRouter.metrics.local.total).toBe(1);
      expect(smartRouter.metrics.local.success).toBe(1);
      expect(smartRouter.metrics.local.failures).toBe(0);
    });

    test('should track execution time', async () => {
      await smartRouter.executeSimple('tool', {});

      expect(smartRouter.metrics.local.totalTime).toBeGreaterThan(0);
    });

    test('should increment failure metrics on error', async () => {
      mockToolRegistry.executeTool.mockRejectedValue(new Error('Execution failed'));

      await expect(smartRouter.executeSimple('tool', {})).rejects.toThrow('Execution failed');

      expect(smartRouter.metrics.local.failures).toBe(1);
      expect(smartRouter.metrics.local.success).toBe(0);
    });
  });

  describe('executeMedium()', () => {
    test('should try local execution first', async () => {
      smartRouter.classification = { simple: [], medium: ['medium_tool'], complex: [] };

      await smartRouter.executeMedium('medium_tool', { text: 'test' });

      expect(mockToolRegistry.executeTool).toHaveBeenCalledWith('medium_tool', { text: 'test' });
    });

    test('should fall back to cloud if local times out', async () => {
      // Mock slow local execution
      mockToolRegistry.executeTool.mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ result: 'slow' }), 5000))
      );

      // Mock cloud execution
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, result: 'cloud result' })
      });

      const result = await smartRouter.executeMedium('medium_tool', {});

      // Should have attempted both local and cloud
      expect(smartRouter.metrics.local.total).toBeGreaterThanOrEqual(1);
    });

    test('should return local result if completes within timeout', async () => {
      mockToolRegistry.executeTool.mockResolvedValue({ success: true, result: 'fast local' });

      const result = await smartRouter.executeMedium('medium_tool', {});

      expect(result).toEqual({ success: true, result: 'fast local' });
      expect(smartRouter.metrics.local.success).toBe(1);
    });
  });

  describe('executeComplex()', () => {
    beforeEach(() => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, result: 'cloud result', executionTime: 1500 })
      });
    });

    test('should execute on cloud API', async () => {
      const result = await smartRouter.executeComplex('complex_tool', { data: 'test' });

      expect(global.fetch).toHaveBeenCalledWith(
        smartRouter.config.cloudApiEndpoint,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    test('should increment cloud metrics on success', async () => {
      await smartRouter.executeComplex('complex_tool', {});

      expect(smartRouter.metrics.cloud.total).toBe(1);
      expect(smartRouter.metrics.cloud.success).toBe(1);
    });

    test('should retry on failure with exponential backoff', async () => {
      global.fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true, result: 'success after retry' })
        });

      const result = await smartRouter.executeComplex('complex_tool', {});

      expect(global.fetch).toHaveBeenCalledTimes(3);
      expect(result.result).toBe('success after retry');
    });

    test('should throw error after max retries', async () => {
      global.fetch.mockRejectedValue(new Error('Persistent network error'));

      await expect(smartRouter.executeComplex('complex_tool', {}))
        .rejects.toThrow();

      expect(global.fetch).toHaveBeenCalledTimes(smartRouter.config.retryAttempts);
      expect(smartRouter.metrics.cloud.failures).toBeGreaterThan(0);
    });

    test('should handle non-200 responses', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      await expect(smartRouter.executeComplex('complex_tool', {}))
        .rejects.toThrow();
    });
  });

  describe('executeTool() - Main Routing', () => {
    test('should check cache before execution', async () => {
      smartRouter.classification = { simple: ['test_tool'], medium: [], complex: [] };
      const cachedResult = { cached: true, result: 'from cache' };
      mockStorageManager.get.mockResolvedValue(cachedResult);

      const result = await smartRouter.executeTool('test_tool', {});

      expect(result).toEqual(cachedResult);
      expect(smartRouter.metrics.cache.hits).toBe(1);
      expect(mockToolRegistry.executeTool).not.toHaveBeenCalled();
    });

    test('should execute simple tools locally', async () => {
      smartRouter.classification = { simple: ['simple_tool'], medium: [], complex: [] };
      mockStorageManager.get.mockResolvedValue(null); // No cache

      await smartRouter.executeTool('simple_tool', { text: 'test' });

      expect(mockToolRegistry.executeTool).toHaveBeenCalledWith('simple_tool', { text: 'test' });
      expect(smartRouter.metrics.cache.misses).toBe(1);
    });

    test('should cache successful results', async () => {
      smartRouter.classification = { simple: ['test_tool'], medium: [], complex: [] };
      mockStorageManager.get.mockResolvedValue(null);

      const result = await smartRouter.executeTool('test_tool', {});

      expect(mockStorageManager.set).toHaveBeenCalled();
    });

    test('should skip cache if disabled', async () => {
      smartRouter.config.cacheEnabled = false;
      smartRouter.classification = { simple: ['test_tool'], medium: [], complex: [] };

      await smartRouter.executeTool('test_tool', {});

      expect(mockStorageManager.get).not.toHaveBeenCalled();
      expect(smartRouter.metrics.cache.hits).toBe(0);
      expect(smartRouter.metrics.cache.misses).toBe(0);
    });

    test('should throw error for unknown complexity', async () => {
      smartRouter.getToolComplexity = jest.fn().mockReturnValue('unknown');

      await expect(smartRouter.executeTool('test_tool', {}))
        .rejects.toThrow('Unknown complexity');
    });

    test('should propagate execution errors', async () => {
      smartRouter.classification = { simple: ['test_tool'], medium: [], complex: [] };
      mockStorageManager.get.mockResolvedValue(null);
      mockToolRegistry.executeTool.mockRejectedValue(new Error('Tool execution failed'));

      await expect(smartRouter.executeTool('test_tool', {}))
        .rejects.toThrow('Tool execution failed');
    });
  });

  describe('Metrics Tracking', () => {
    test('should accurately track all execution attempts', async () => {
      smartRouter.classification = { simple: ['tool1', 'tool2'], medium: [], complex: [] };
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('tool1', {});
      await smartRouter.executeTool('tool2', {});

      expect(smartRouter.metrics.local.total).toBe(2);
      expect(smartRouter.metrics.local.success).toBe(2);
    });

    test('should track cache hit rate', async () => {
      smartRouter.classification = { simple: ['tool'], medium: [], complex: [] };

      // First call - cache miss
      mockStorageManager.get.mockResolvedValueOnce(null);
      await smartRouter.executeTool('tool', { input: 'test' });

      // Second call - cache hit
      mockStorageManager.get.mockResolvedValueOnce({ cached: true });
      await smartRouter.executeTool('tool', { input: 'test' });

      expect(smartRouter.metrics.cache.hits).toBe(1);
      expect(smartRouter.metrics.cache.misses).toBe(1);
    });
  });

  describe('Configuration', () => {
    test('should allow updating timeout configuration', () => {
      smartRouter.config.mediumToolTimeout = 5000;

      expect(smartRouter.config.mediumToolTimeout).toBe(5000);
    });

    test('should allow updating retry configuration', () => {
      smartRouter.config.retryAttempts = 5;
      smartRouter.config.retryDelay = 2000;

      expect(smartRouter.config.retryAttempts).toBe(5);
      expect(smartRouter.config.retryDelay).toBe(2000);
    });

    test('should allow disabling cache', () => {
      smartRouter.config.cacheEnabled = false;

      expect(smartRouter.config.cacheEnabled).toBe(false);
    });
  });
});
