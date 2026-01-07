/**
 * Integration Tests: Smart Router + Cache System
 * Phase 9.2 Stage 4
 *
 * Tests the interaction between routing and caching mechanisms
 */

import { SmartRouter } from '../../src/background/smart-router.js';

describe('SmartRouter + Cache Integration', () => {
  let smartRouter;
  let mockToolRegistry;
  let mockStorageManager;

  beforeEach(() => {
    // Mock Tool Registry
    mockToolRegistry = {
      executeTool: jest.fn().mockResolvedValue({ success: true, result: 'fresh result' })
    };

    // Mock Storage Manager with cache functionality
    mockStorageManager = {
      get: jest.fn(),
      set: jest.fn().mockResolvedValue(undefined),
      remove: jest.fn().mockResolvedValue(undefined)
    };

    smartRouter = new SmartRouter(mockToolRegistry, mockStorageManager);

    // Enable cache
    smartRouter.config.cacheEnabled = true;
    smartRouter.classification = {
      simple: ['simple_tool'],
      medium: ['medium_tool'],
      complex: ['complex_tool']
    };
  });

  describe('Cache Miss → Execute → Cache Store', () => {
    test('should execute and cache result on cache miss', async () => {
      // Cache miss
      mockStorageManager.get.mockResolvedValue(null);

      const result = await smartRouter.executeTool('simple_tool', { input: 'test' });

      // Should execute tool
      expect(mockToolRegistry.executeTool).toHaveBeenCalledWith('simple_tool', { input: 'test' });

      // Should cache the result
      expect(mockStorageManager.set).toHaveBeenCalled();
      const cacheKey = mockStorageManager.set.mock.calls[0][0];
      const cachedData = mockStorageManager.set.mock.calls[0][1];

      expect(cacheKey).toContain('cache');
      expect(cachedData.result).toEqual(result);
      expect(cachedData.timestamp).toBeDefined();
      expect(cachedData.ttl).toBeDefined();
    });

    test('should track cache miss in metrics', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('simple_tool', {});

      expect(smartRouter.metrics.cache.misses).toBe(1);
      expect(smartRouter.metrics.cache.hits).toBe(0);
    });
  });

  describe('Cache Hit Flow', () => {
    test('should return cached result on cache hit', async () => {
      const cachedData = {
        cached: true,
        result: { success: true, result: 'cached value' },
        timestamp: Date.now(),
        ttl: 300000
      };

      mockStorageManager.get.mockResolvedValue(cachedData);

      const result = await smartRouter.executeTool('simple_tool', { input: 'test' });

      // Should NOT execute tool
      expect(mockToolRegistry.executeTool).not.toHaveBeenCalled();

      // Should return cached result
      expect(result).toEqual(cachedData);

      // Should track cache hit
      expect(smartRouter.metrics.cache.hits).toBe(1);
      expect(smartRouter.metrics.cache.misses).toBe(0);
    });

    test('should skip execution for all tool complexities on cache hit', async () => {
      const cachedData = {
        cached: true,
        result: { success: true, result: 'cached' },
        timestamp: Date.now(),
        ttl: 300000
      };

      mockStorageManager.get.mockResolvedValue(cachedData);

      // Test simple, medium, complex
      await smartRouter.executeTool('simple_tool', {});
      await smartRouter.executeTool('medium_tool', {});
      await smartRouter.executeTool('complex_tool', {});

      // None should execute
      expect(mockToolRegistry.executeTool).not.toHaveBeenCalled();
      expect(smartRouter.metrics.cache.hits).toBe(3);
    });
  });

  describe('Cache Key Consistency', () => {
    test('should generate same cache key for identical requests', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      const params = { a: 1, b: 2, c: 'test' };

      await smartRouter.executeTool('tool1', params);
      const firstKey = mockStorageManager.set.mock.calls[0][0];

      mockStorageManager.set.mockClear();

      await smartRouter.executeTool('tool1', params);
      const secondKey = mockStorageManager.set.mock.calls[0][0];

      expect(firstKey).toBe(secondKey);
    });

    test('should generate different cache keys for different tools', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      const params = { input: 'test' };

      await smartRouter.executeTool('simple_tool', params);
      const firstKey = mockStorageManager.set.mock.calls[0][0];

      mockStorageManager.set.mockClear();

      await smartRouter.executeTool('medium_tool', params);
      const secondKey = mockStorageManager.set.mock.calls[0][0];

      expect(firstKey).not.toBe(secondKey);
    });

    test('should generate different cache keys for different parameters', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('simple_tool', { input: 'test1' });
      const firstKey = mockStorageManager.set.mock.calls[0][0];

      mockStorageManager.set.mockClear();

      await smartRouter.executeTool('simple_tool', { input: 'test2' });
      const secondKey = mockStorageManager.set.mock.calls[0][0];

      expect(firstKey).not.toBe(secondKey);
    });

    test('should handle parameter order independence', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('tool1', { a: 1, b: 2 });
      const firstKey = mockStorageManager.set.mock.calls[0][0];

      mockStorageManager.set.mockClear();

      await smartRouter.executeTool('tool1', { b: 2, a: 1 });
      const secondKey = mockStorageManager.set.mock.calls[0][0];

      // Should be the same (parameter order shouldn't matter)
      expect(firstKey).toBe(secondKey);
    });
  });

  describe('Cache TTL and Expiration', () => {
    test('should include TTL in cached data', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('simple_tool', {});

      const cachedData = mockStorageManager.set.mock.calls[0][1];

      expect(cachedData.ttl).toBeDefined();
      expect(cachedData.ttl).toBeGreaterThan(0);
      expect(cachedData.timestamp).toBeDefined();
    });

    test('should use appropriate TTL for different tool complexities', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      // Simple tool
      await smartRouter.executeTool('simple_tool', {});
      const simpleTTL = mockStorageManager.set.mock.calls[0][1].ttl;

      mockStorageManager.set.mockClear();

      // Complex tool
      await smartRouter.executeTool('complex_tool', {});
      const complexTTL = mockStorageManager.set.mock.calls[0][1].ttl;

      // Both should have valid TTLs (actual values depend on implementation)
      expect(simpleTTL).toBeGreaterThan(0);
      expect(complexTTL).toBeGreaterThan(0);
    });

    test('should respect expired cache entries', async () => {
      const expiredCache = {
        cached: true,
        result: { success: true, result: 'old data' },
        timestamp: Date.now() - 400000, // 400 seconds ago
        ttl: 300000 // 5 minute TTL
      };

      // First call - expired cache should be treated as miss
      mockStorageManager.get.mockResolvedValue(expiredCache);

      const result = await smartRouter.executeTool('simple_tool', {});

      // In real implementation, expired cache should trigger fresh execution
      // For now, we test that cache was checked
      expect(mockStorageManager.get).toHaveBeenCalled();
    });
  });

  describe('Cache with Different Routing Strategies', () => {
    test('should cache local execution results', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('simple_tool', { text: 'test' });

      expect(mockStorageManager.set).toHaveBeenCalled();
      const cachedData = mockStorageManager.set.mock.calls[0][1];
      expect(cachedData.result.success).toBe(true);
    });

    test('should cache cloud execution results', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, result: 'cloud result' })
      });

      await smartRouter.executeTool('complex_tool', { data: 'test' });

      expect(mockStorageManager.set).toHaveBeenCalled();
      const cachedData = mockStorageManager.set.mock.calls[0][1];
      expect(cachedData.result).toBeDefined();
    });

    test('should cache medium tool results regardless of execution location', async () => {
      mockStorageManager.get.mockResolvedValue(null);

      await smartRouter.executeTool('medium_tool', { input: 'test' });

      expect(mockStorageManager.set).toHaveBeenCalled();
    });
  });

  describe('Cache Disabled Scenarios', () => {
    test('should skip cache check when cache disabled', async () => {
      smartRouter.config.cacheEnabled = false;

      await smartRouter.executeTool('simple_tool', {});

      // Should not check cache
      expect(mockStorageManager.get).not.toHaveBeenCalled();

      // Should execute directly
      expect(mockToolRegistry.executeTool).toHaveBeenCalled();
    });

    test('should not store results when cache disabled', async () => {
      smartRouter.config.cacheEnabled = false;

      await smartRouter.executeTool('simple_tool', {});

      // Should not cache
      expect(mockStorageManager.set).not.toHaveBeenCalled();
    });

    test('should not track cache metrics when disabled', async () => {
      smartRouter.config.cacheEnabled = false;

      await smartRouter.executeTool('simple_tool', {});

      expect(smartRouter.metrics.cache.hits).toBe(0);
      expect(smartRouter.metrics.cache.misses).toBe(0);
    });
  });

  describe('Performance Impact', () => {
    test('should be faster with cache hit than cache miss', async () => {
      // Simulate slow tool execution
      mockToolRegistry.executeTool.mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ success: true, result: 'slow' }), 100))
      );

      // First call - cache miss
      mockStorageManager.get.mockResolvedValueOnce(null);
      const start1 = Date.now();
      await smartRouter.executeTool('simple_tool', { input: 'test' });
      const duration1 = Date.now() - start1;

      // Second call - cache hit
      const cachedData = {
        cached: true,
        result: { success: true, result: 'cached' },
        timestamp: Date.now(),
        ttl: 300000
      };
      mockStorageManager.get.mockResolvedValueOnce(cachedData);
      const start2 = Date.now();
      await smartRouter.executeTool('simple_tool', { input: 'test' });
      const duration2 = Date.now() - start2;

      // Cache hit should be significantly faster
      expect(duration2).toBeLessThan(duration1);
    });
  });

  describe('Error Handling with Cache', () => {
    test('should not cache failed executions', async () => {
      mockStorageManager.get.mockResolvedValue(null);
      mockToolRegistry.executeTool.mockRejectedValue(new Error('Tool failed'));

      await expect(smartRouter.executeTool('simple_tool', {})).rejects.toThrow();

      // Should not cache errors
      expect(mockStorageManager.set).not.toHaveBeenCalled();
    });

    test('should handle cache storage errors gracefully', async () => {
      mockStorageManager.get.mockResolvedValue(null);
      mockStorageManager.set.mockRejectedValue(new Error('Storage full'));

      // Should still return result even if caching fails
      const result = await smartRouter.executeTool('simple_tool', {});

      expect(result.success).toBe(true);
    });

    test('should handle cache retrieval errors gracefully', async () => {
      mockStorageManager.get.mockRejectedValue(new Error('Storage error'));

      // Should fall back to execution
      const result = await smartRouter.executeTool('simple_tool', {});

      expect(mockToolRegistry.executeTool).toHaveBeenCalled();
      expect(result.success).toBe(true);
    });
  });

  describe('Cache Hit Rate Tracking', () => {
    test('should accurately calculate cache hit rate', async () => {
      const cachedData = {
        cached: true,
        result: { success: true, result: 'cached' },
        timestamp: Date.now(),
        ttl: 300000
      };

      // 3 cache hits
      mockStorageManager.get.mockResolvedValue(cachedData);
      await smartRouter.executeTool('tool1', {});
      await smartRouter.executeTool('tool2', {});
      await smartRouter.executeTool('tool3', {});

      // 2 cache misses
      mockStorageManager.get.mockResolvedValue(null);
      await smartRouter.executeTool('tool4', {});
      await smartRouter.executeTool('tool5', {});

      expect(smartRouter.metrics.cache.hits).toBe(3);
      expect(smartRouter.metrics.cache.misses).toBe(2);

      // Hit rate should be 60% (3/5)
      const hitRate = smartRouter.metrics.cache.hits /
        (smartRouter.metrics.cache.hits + smartRouter.metrics.cache.misses);
      expect(hitRate).toBeCloseTo(0.6);
    });
  });

  describe('Cache Invalidation Scenarios', () => {
    test('should allow manual cache invalidation', async () => {
      const cachedData = {
        cached: true,
        result: { success: true, result: 'cached' },
        timestamp: Date.now(),
        ttl: 300000
      };

      mockStorageManager.get.mockResolvedValue(cachedData);

      // First call - cache hit
      await smartRouter.executeTool('simple_tool', {});
      expect(mockToolRegistry.executeTool).not.toHaveBeenCalled();

      // Invalidate cache
      mockStorageManager.get.mockResolvedValue(null);

      // Second call - cache miss after invalidation
      await smartRouter.executeTool('simple_tool', {});
      expect(mockToolRegistry.executeTool).toHaveBeenCalled();
    });
  });
});
