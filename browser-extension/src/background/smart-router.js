/**
 * Smart Router
 * Phase 9.2.3: Intelligent routing between local WASM and cloud execution
 *
 * Routes tool execution based on:
 * - Tool complexity classification
 * - Network availability
 * - Performance metrics
 * - Cache availability
 */

import toolClassification from '../../tool-classification.json';

export class SmartRouter {
  constructor(toolRegistry, storageManager) {
    this.toolRegistry = toolRegistry;
    this.storage = storageManager;
    this.classification = toolClassification;

    // Performance tracking
    this.metrics = {
      local: { total: 0, success: 0, failures: 0, totalTime: 0 },
      cloud: { total: 0, success: 0, failures: 0, totalTime: 0 },
      cache: { hits: 0, misses: 0 }
    };

    // Configuration
    this.config = {
      mediumToolTimeout: 2000,      // 2s timeout for medium tools
      cacheEnabled: true,
      retryAttempts: 3,
      retryDelay: 1000,              // 1s base delay (exponential backoff)
      cloudApiEndpoint: 'https://api.data20.example.com/tools'
    };
  }

  /**
   * Main routing method - decides where to execute tool
   */
  async executeTool(toolName, parameters) {
    console.log(`[SmartRouter] Routing tool: ${toolName}`);

    // Get tool classification
    const complexity = this.getToolComplexity(toolName);
    console.log(`[SmartRouter] Tool complexity: ${complexity}`);

    // Check cache first (if enabled)
    if (this.config.cacheEnabled) {
      const cachedResult = await this.checkCache(toolName, parameters);
      if (cachedResult !== null) {
        console.log(`[SmartRouter] Cache hit for ${toolName}`);
        this.metrics.cache.hits++;
        return cachedResult;
      }
      this.metrics.cache.misses++;
    }

    // Route based on complexity
    let result;
    try {
      switch (complexity) {
        case 'simple':
          result = await this.executeSimple(toolName, parameters);
          break;

        case 'medium':
          result = await this.executeMedium(toolName, parameters);
          break;

        case 'complex':
          result = await this.executeComplex(toolName, parameters);
          break;

        default:
          throw new Error(`Unknown complexity: ${complexity}`);
      }

      // Cache successful result
      if (this.config.cacheEnabled && result) {
        await this.cacheResult(toolName, parameters, result);
      }

      return result;

    } catch (error) {
      console.error(`[SmartRouter] Execution failed for ${toolName}:`, error);
      throw error;
    }
  }

  /**
   * Execute simple tool - always local
   */
  async executeSimple(toolName, parameters) {
    console.log(`[SmartRouter] Executing simple tool locally: ${toolName}`);

    const startTime = performance.now();
    this.metrics.local.total++;

    try {
      const result = await this.toolRegistry.executeTool(toolName, parameters);

      const executionTime = performance.now() - startTime;
      this.metrics.local.success++;
      this.metrics.local.totalTime += executionTime;

      console.log(`[SmartRouter] Local execution succeeded in ${executionTime.toFixed(2)}ms`);

      return {
        result,
        execution: {
          location: 'local',
          time: executionTime,
          cached: false
        }
      };

    } catch (error) {
      this.metrics.local.failures++;
      throw new Error(`Local execution failed: ${error.message}`);
    }
  }

  /**
   * Execute medium tool - try local with timeout, fallback to cloud
   */
  async executeMedium(toolName, parameters) {
    console.log(`[SmartRouter] Executing medium tool: ${toolName}`);

    // Try local execution first with timeout
    try {
      const result = await this.executeLocalWithTimeout(
        toolName,
        parameters,
        this.config.mediumToolTimeout
      );

      console.log(`[SmartRouter] Medium tool succeeded locally`);
      return result;

    } catch (timeoutError) {
      console.warn(`[SmartRouter] Local execution timed out or failed:`, timeoutError.message);

      // Check if online
      if (navigator.onLine) {
        console.log(`[SmartRouter] Falling back to cloud execution`);
        return await this.executeCloud(toolName, parameters);
      } else {
        console.warn(`[SmartRouter] Offline - queueing for later`);
        return await this.queueForLater(toolName, parameters);
      }
    }
  }

  /**
   * Execute complex tool - prefer cloud, queue if offline
   */
  async executeComplex(toolName, parameters) {
    console.log(`[SmartRouter] Executing complex tool: ${toolName}`);

    if (navigator.onLine) {
      console.log(`[SmartRouter] Executing on cloud (complex tool)`);
      return await this.executeCloud(toolName, parameters);
    } else {
      console.warn(`[SmartRouter] Offline - queueing complex tool`);
      return await this.queueForLater(toolName, parameters);
    }
  }

  /**
   * Execute tool locally with timeout
   */
  async executeLocalWithTimeout(toolName, parameters, timeout) {
    const startTime = performance.now();
    this.metrics.local.total++;

    return new Promise(async (resolve, reject) => {
      // Timeout timer
      const timeoutId = setTimeout(() => {
        this.metrics.local.failures++;
        reject(new Error(`Local execution timed out after ${timeout}ms`));
      }, timeout);

      try {
        const result = await this.toolRegistry.executeTool(toolName, parameters);
        clearTimeout(timeoutId);

        const executionTime = performance.now() - startTime;
        this.metrics.local.success++;
        this.metrics.local.totalTime += executionTime;

        console.log(`[SmartRouter] Local execution succeeded in ${executionTime.toFixed(2)}ms`);

        resolve({
          result,
          execution: {
            location: 'local',
            time: executionTime,
            cached: false
          }
        });

      } catch (error) {
        clearTimeout(timeoutId);
        this.metrics.local.failures++;
        reject(error);
      }
    });
  }

  /**
   * Execute tool on cloud API
   */
  async executeCloud(toolName, parameters) {
    const startTime = performance.now();
    this.metrics.cloud.total++;

    console.log(`[SmartRouter] Executing on cloud: ${toolName}`);

    try {
      const response = await this.fetchWithRetry(
        `${this.config.cloudApiEndpoint}/${toolName}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(parameters)
        }
      );

      if (!response.ok) {
        throw new Error(`Cloud API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      const executionTime = performance.now() - startTime;
      this.metrics.cloud.success++;
      this.metrics.cloud.totalTime += executionTime;

      console.log(`[SmartRouter] Cloud execution succeeded in ${executionTime.toFixed(2)}ms`);

      return {
        result: data.result,
        execution: {
          location: 'cloud',
          time: executionTime,
          cached: false
        }
      };

    } catch (error) {
      this.metrics.cloud.failures++;
      throw new Error(`Cloud execution failed: ${error.message}`);
    }
  }

  /**
   * Queue tool for later execution (when offline)
   */
  async queueForLater(toolName, parameters) {
    console.log(`[SmartRouter] Queueing tool for later: ${toolName}`);

    const jobId = crypto.randomUUID();
    const job = {
      id: jobId,
      toolName,
      parameters,
      status: 'queued',
      createdAt: Date.now(),
      priority: this.calculatePriority(toolName)
    };

    // Store in queue (will be processed by OfflineQueue in Phase 9.2.4)
    await this.storage.addToQueue(job);

    return {
      result: null,
      execution: {
        location: 'queued',
        jobId,
        message: 'Tool execution queued for when connection is restored'
      }
    };
  }

  /**
   * Fetch with exponential backoff retry
   */
  async fetchWithRetry(url, options, attempt = 1) {
    try {
      return await fetch(url, options);
    } catch (error) {
      if (attempt >= this.config.retryAttempts) {
        throw error;
      }

      // Exponential backoff: 1s, 2s, 4s
      const delay = this.config.retryDelay * Math.pow(2, attempt - 1);
      console.log(`[SmartRouter] Retry attempt ${attempt}/${this.config.retryAttempts} after ${delay}ms`);

      await new Promise(resolve => setTimeout(resolve, delay));
      return this.fetchWithRetry(url, options, attempt + 1);
    }
  }

  /**
   * Get tool complexity from classification
   */
  getToolComplexity(toolName) {
    // Check each complexity category
    for (const [complexity, tools] of Object.entries(this.classification.tools)) {
      const tool = tools.find(t => t.name === toolName);
      if (tool) {
        return complexity;
      }
    }

    // Default to medium if not found
    console.warn(`[SmartRouter] Tool ${toolName} not found in classification, defaulting to medium`);
    return 'medium';
  }

  /**
   * Calculate job priority for queue
   */
  calculatePriority(toolName) {
    const complexity = this.getToolComplexity(toolName);

    // Higher priority for simpler tools
    const priorityMap = {
      'simple': 10,
      'medium': 5,
      'complex': 1
    };

    return priorityMap[complexity] || 5;
  }

  /**
   * Check cache for result
   */
  async checkCache(toolName, parameters) {
    try {
      const cacheKey = this.generateCacheKey(toolName, parameters);
      const cached = await this.storage.getCached(cacheKey);

      if (cached) {
        // Check if expired
        const now = Date.now();
        if (cached.expiresAt && cached.expiresAt < now) {
          console.log(`[SmartRouter] Cache expired for ${toolName}`);
          await this.storage.removeCached(cacheKey);
          return null;
        }

        console.log(`[SmartRouter] Cache hit for ${toolName}`);
        return {
          result: cached.data,
          execution: {
            location: 'cache',
            time: 0,
            cached: true,
            cachedAt: cached.timestamp
          }
        };
      }

      return null;

    } catch (error) {
      console.error(`[SmartRouter] Cache check failed:`, error);
      return null;
    }
  }

  /**
   * Cache execution result
   */
  async cacheResult(toolName, parameters, result) {
    try {
      const cacheKey = this.generateCacheKey(toolName, parameters);
      const complexity = this.getToolComplexity(toolName);

      // Get TTL from routing strategy
      const strategy = this.classification.routing_strategy[complexity];
      const ttl = strategy ? strategy.cache_ttl * 1000 : 3600000; // Default 1 hour

      await this.storage.cacheResult(cacheKey, result, ttl);
      console.log(`[SmartRouter] Cached result for ${toolName} (TTL: ${ttl}ms)`);

    } catch (error) {
      console.error(`[SmartRouter] Cache write failed:`, error);
      // Don't fail the request if caching fails
    }
  }

  /**
   * Generate cache key from tool name and parameters
   */
  generateCacheKey(toolName, parameters) {
    // Create deterministic key from tool name and parameters
    const paramString = JSON.stringify(parameters, Object.keys(parameters).sort());
    return `${toolName}:${this.hashString(paramString)}`;
  }

  /**
   * Simple string hash function
   */
  hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  /**
   * Get performance metrics
   */
  getMetrics() {
    const localAvgTime = this.metrics.local.total > 0
      ? this.metrics.local.totalTime / this.metrics.local.success
      : 0;

    const cloudAvgTime = this.metrics.cloud.total > 0
      ? this.metrics.cloud.totalTime / this.metrics.cloud.success
      : 0;

    const localSuccessRate = this.metrics.local.total > 0
      ? (this.metrics.local.success / this.metrics.local.total) * 100
      : 0;

    const cloudSuccessRate = this.metrics.cloud.total > 0
      ? (this.metrics.cloud.success / this.metrics.cloud.total) * 100
      : 0;

    const cacheHitRate = (this.metrics.cache.hits + this.metrics.cache.misses) > 0
      ? (this.metrics.cache.hits / (this.metrics.cache.hits + this.metrics.cache.misses)) * 100
      : 0;

    return {
      local: {
        total: this.metrics.local.total,
        success: this.metrics.local.success,
        failures: this.metrics.local.failures,
        avgTime: Math.round(localAvgTime),
        successRate: localSuccessRate.toFixed(1)
      },
      cloud: {
        total: this.metrics.cloud.total,
        success: this.metrics.cloud.success,
        failures: this.metrics.cloud.failures,
        avgTime: Math.round(cloudAvgTime),
        successRate: cloudSuccessRate.toFixed(1)
      },
      cache: {
        hits: this.metrics.cache.hits,
        misses: this.metrics.cache.misses,
        hitRate: cacheHitRate.toFixed(1)
      }
    };
  }

  /**
   * Reset metrics
   */
  resetMetrics() {
    this.metrics = {
      local: { total: 0, success: 0, failures: 0, totalTime: 0 },
      cloud: { total: 0, success: 0, failures: 0, totalTime: 0 },
      cache: { hits: 0, misses: 0 }
    };
    console.log('[SmartRouter] Metrics reset');
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    console.log('[SmartRouter] Configuration updated:', this.config);
  }

  /**
   * Get current configuration
   */
  getConfig() {
    return { ...this.config };
  }
}

export default SmartRouter;
