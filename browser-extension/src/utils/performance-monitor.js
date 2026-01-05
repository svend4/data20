/**
 * Performance Monitor & Analytics
 * Phase 9.2.5: Comprehensive metrics tracking and analytics
 *
 * Tracks:
 * - Tool execution performance
 * - Resource usage (memory, CPU estimation)
 * - Router efficiency (local vs cloud)
 * - Cache effectiveness
 * - Queue throughput
 * - Error rates and patterns
 */

export class PerformanceMonitor {
  constructor(storageManager) {
    this.storage = storageManager;

    // Real-time metrics
    this.metrics = {
      tools: {
        executions: 0,
        totalTime: 0,
        byTool: {}, // { toolName: { count, totalTime, avgTime, errors } }
        byComplexity: {
          simple: { count: 0, totalTime: 0, errors: 0 },
          medium: { count: 0, totalTime: 0, errors: 0 },
          complex: { count: 0, totalTime: 0, errors: 0 }
        }
      },
      routing: {
        local: { count: 0, totalTime: 0, errors: 0 },
        cloud: { count: 0, totalTime: 0, errors: 0 },
        cache: { hits: 0, misses: 0 },
        queued: { count: 0 }
      },
      resources: {
        peakMemory: 0,
        avgMemory: 0,
        memorySamples: [],
        pyodideLoadTime: 0
      },
      errors: {
        total: 0,
        byType: {}, // { errorType: count }
        recent: [] // Last 50 errors with timestamps
      },
      session: {
        startTime: Date.now(),
        toolsAvailable: 0,
        articlesStored: 0
      }
    };

    // Configuration
    this.config = {
      memorySampleInterval: 60000,    // Sample memory every 60s
      maxRecentErrors: 50,
      persistMetricsInterval: 300000, // Persist to storage every 5 minutes
      enableDetailedTracking: true
    };

    // Intervals
    this.memorySampleInterval = null;
    this.persistInterval = null;
  }

  /**
   * Initialize monitor
   */
  async initialize() {
    console.log('[PerformanceMonitor] Initializing...');

    // Load historical metrics
    await this.loadHistoricalMetrics();

    // Start memory sampling
    this.startMemorySampling();

    // Start periodic persistence
    this.startPeriodicPersistence();

    console.log('[PerformanceMonitor] Initialized');
  }

  /**
   * Record tool execution
   */
  recordToolExecution(toolName, complexity, location, executionTime, success = true, error = null) {
    // Update total executions
    this.metrics.tools.executions++;
    this.metrics.tools.totalTime += executionTime;

    // Update by tool
    if (!this.metrics.tools.byTool[toolName]) {
      this.metrics.tools.byTool[toolName] = {
        count: 0,
        totalTime: 0,
        avgTime: 0,
        errors: 0,
        lastExecution: null
      };
    }

    const toolMetrics = this.metrics.tools.byTool[toolName];
    toolMetrics.count++;
    toolMetrics.totalTime += executionTime;
    toolMetrics.avgTime = toolMetrics.totalTime / toolMetrics.count;
    toolMetrics.lastExecution = Date.now();

    if (!success) {
      toolMetrics.errors++;
    }

    // Update by complexity
    if (this.metrics.tools.byComplexity[complexity]) {
      this.metrics.tools.byComplexity[complexity].count++;
      this.metrics.tools.byComplexity[complexity].totalTime += executionTime;

      if (!success) {
        this.metrics.tools.byComplexity[complexity].errors++;
      }
    }

    // Update by location
    if (location === 'local') {
      this.metrics.routing.local.count++;
      this.metrics.routing.local.totalTime += executionTime;
      if (!success) this.metrics.routing.local.errors++;
    } else if (location === 'cloud') {
      this.metrics.routing.cloud.count++;
      this.metrics.routing.cloud.totalTime += executionTime;
      if (!success) this.metrics.routing.cloud.errors++;
    } else if (location === 'cache') {
      this.metrics.routing.cache.hits++;
    } else if (location === 'queued') {
      this.metrics.routing.queued.count++;
    }

    // Record error if present
    if (error) {
      this.recordError(error, toolName);
    }

    console.log(`[PerformanceMonitor] Recorded: ${toolName} (${location}) - ${executionTime.toFixed(2)}ms`);
  }

  /**
   * Record cache hit/miss
   */
  recordCache(hit) {
    if (hit) {
      this.metrics.routing.cache.hits++;
    } else {
      this.metrics.routing.cache.misses++;
    }
  }

  /**
   * Record error
   */
  recordError(error, context = null) {
    this.metrics.errors.total++;

    // Categorize error
    const errorType = error.name || 'UnknownError';

    if (!this.metrics.errors.byType[errorType]) {
      this.metrics.errors.byType[errorType] = 0;
    }
    this.metrics.errors.byType[errorType]++;

    // Store recent error
    this.metrics.errors.recent.unshift({
      timestamp: Date.now(),
      type: errorType,
      message: error.message,
      context: context
    });

    // Limit recent errors
    if (this.metrics.errors.recent.length > this.config.maxRecentErrors) {
      this.metrics.errors.recent = this.metrics.errors.recent.slice(0, this.config.maxRecentErrors);
    }
  }

  /**
   * Sample memory usage
   */
  sampleMemory() {
    if (performance.memory) {
      const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024;

      this.metrics.resources.memorySamples.push({
        timestamp: Date.now(),
        value: memoryMB
      });

      // Keep last 100 samples
      if (this.metrics.resources.memorySamples.length > 100) {
        this.metrics.resources.memorySamples.shift();
      }

      // Update peak
      if (memoryMB > this.metrics.resources.peakMemory) {
        this.metrics.resources.peakMemory = memoryMB;
      }

      // Update average
      const sum = this.metrics.resources.memorySamples.reduce((acc, s) => acc + s.value, 0);
      this.metrics.resources.avgMemory = sum / this.metrics.resources.memorySamples.length;
    }
  }

  /**
   * Start memory sampling
   */
  startMemorySampling() {
    // Initial sample
    this.sampleMemory();

    // Periodic sampling
    this.memorySampleInterval = setInterval(() => {
      this.sampleMemory();
    }, this.config.memorySampleInterval);

    console.log('[PerformanceMonitor] Memory sampling started');
  }

  /**
   * Stop memory sampling
   */
  stopMemorySampling() {
    if (this.memorySampleInterval) {
      clearInterval(this.memorySampleInterval);
      this.memorySampleInterval = null;
    }
  }

  /**
   * Start periodic metrics persistence
   */
  startPeriodicPersistence() {
    this.persistInterval = setInterval(async () => {
      await this.persistMetrics();
    }, this.config.persistMetricsInterval);

    console.log('[PerformanceMonitor] Periodic persistence started');
  }

  /**
   * Stop periodic persistence
   */
  stopPeriodicPersistence() {
    if (this.persistInterval) {
      clearInterval(this.persistInterval);
      this.persistInterval = null;
    }
  }

  /**
   * Persist metrics to storage
   */
  async persistMetrics() {
    try {
      const snapshot = {
        timestamp: Date.now(),
        metrics: this.getMetrics(),
        sessionDuration: Date.now() - this.metrics.session.startTime
      };

      await this.storage.saveSetting('performance_metrics', snapshot);
      console.log('[PerformanceMonitor] Metrics persisted');
    } catch (error) {
      console.error('[PerformanceMonitor] Failed to persist metrics:', error);
    }
  }

  /**
   * Load historical metrics
   */
  async loadHistoricalMetrics() {
    try {
      const saved = await this.storage.getSetting('performance_metrics');

      if (saved) {
        console.log('[PerformanceMonitor] Loaded historical metrics');
        // Could merge with current metrics or display separately
      }
    } catch (error) {
      console.error('[PerformanceMonitor] Failed to load historical metrics:', error);
    }
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    // Calculate derived metrics
    const totalExecutions = this.metrics.tools.executions;
    const avgExecutionTime = totalExecutions > 0
      ? this.metrics.tools.totalTime / totalExecutions
      : 0;

    const localAvgTime = this.metrics.routing.local.count > 0
      ? this.metrics.routing.local.totalTime / this.metrics.routing.local.count
      : 0;

    const cloudAvgTime = this.metrics.routing.cloud.count > 0
      ? this.metrics.routing.cloud.totalTime / this.metrics.routing.cloud.count
      : 0;

    const cacheHitRate = (this.metrics.routing.cache.hits + this.metrics.routing.cache.misses) > 0
      ? (this.metrics.routing.cache.hits / (this.metrics.routing.cache.hits + this.metrics.routing.cache.misses)) * 100
      : 0;

    const errorRate = totalExecutions > 0
      ? (this.metrics.errors.total / totalExecutions) * 100
      : 0;

    const sessionDuration = Date.now() - this.metrics.session.startTime;

    // Top tools by usage
    const topTools = Object.entries(this.metrics.tools.byTool)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Top errors
    const topErrors = Object.entries(this.metrics.errors.byType)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    return {
      summary: {
        totalExecutions,
        avgExecutionTime: Math.round(avgExecutionTime),
        errorRate: errorRate.toFixed(2),
        cacheHitRate: cacheHitRate.toFixed(1),
        sessionDuration: Math.round(sessionDuration / 1000 / 60), // minutes
        uptime: this.formatDuration(sessionDuration)
      },
      tools: {
        total: totalExecutions,
        byComplexity: {
          simple: {
            ...this.metrics.tools.byComplexity.simple,
            avgTime: this.metrics.tools.byComplexity.simple.count > 0
              ? Math.round(this.metrics.tools.byComplexity.simple.totalTime / this.metrics.tools.byComplexity.simple.count)
              : 0
          },
          medium: {
            ...this.metrics.tools.byComplexity.medium,
            avgTime: this.metrics.tools.byComplexity.medium.count > 0
              ? Math.round(this.metrics.tools.byComplexity.medium.totalTime / this.metrics.tools.byComplexity.medium.count)
              : 0
          },
          complex: {
            ...this.metrics.tools.byComplexity.complex,
            avgTime: this.metrics.tools.byComplexity.complex.count > 0
              ? Math.round(this.metrics.tools.byComplexity.complex.totalTime / this.metrics.tools.byComplexity.complex.count)
              : 0
          }
        },
        topTools: topTools
      },
      routing: {
        local: {
          ...this.metrics.routing.local,
          avgTime: Math.round(localAvgTime),
          percentage: totalExecutions > 0
            ? ((this.metrics.routing.local.count / totalExecutions) * 100).toFixed(1)
            : '0.0'
        },
        cloud: {
          ...this.metrics.routing.cloud,
          avgTime: Math.round(cloudAvgTime),
          percentage: totalExecutions > 0
            ? ((this.metrics.routing.cloud.count / totalExecutions) * 100).toFixed(1)
            : '0.0'
        },
        cache: {
          ...this.metrics.routing.cache,
          hitRate: cacheHitRate.toFixed(1)
        },
        queued: this.metrics.routing.queued
      },
      resources: {
        memory: {
          current: performance.memory
            ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024)
            : 0,
          peak: Math.round(this.metrics.resources.peakMemory),
          avg: Math.round(this.metrics.resources.avgMemory)
        },
        pyodideLoadTime: this.metrics.resources.pyodideLoadTime
      },
      errors: {
        total: this.metrics.errors.total,
        rate: errorRate.toFixed(2),
        topErrors: topErrors,
        recent: this.metrics.errors.recent.slice(0, 10)
      },
      session: {
        startTime: this.metrics.session.startTime,
        duration: sessionDuration,
        toolsAvailable: this.metrics.session.toolsAvailable,
        articlesStored: this.metrics.session.articlesStored
      }
    };
  }

  /**
   * Get metrics for export
   */
  getExportData() {
    return {
      exportTime: new Date().toISOString(),
      version: '1.0',
      metrics: this.getMetrics(),
      rawData: this.metrics
    };
  }

  /**
   * Export metrics as JSON
   */
  exportAsJSON() {
    const data = this.getExportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `data20-metrics-${Date.now()}.json`;
    a.click();

    URL.revokeObjectURL(url);
    console.log('[PerformanceMonitor] Metrics exported as JSON');
  }

  /**
   * Export metrics as CSV
   */
  exportAsCSV() {
    const metrics = this.getMetrics();

    // Create CSV header
    let csv = 'Metric,Value\n';

    // Summary section
    csv += '\n# Summary\n';
    csv += `Total Executions,${metrics.summary.totalExecutions}\n`;
    csv += `Average Execution Time (ms),${metrics.summary.avgExecutionTime}\n`;
    csv += `Error Rate (%),${metrics.summary.errorRate}\n`;
    csv += `Cache Hit Rate (%),${metrics.summary.cacheHitRate}\n`;
    csv += `Session Duration (min),${metrics.summary.sessionDuration}\n`;

    // Routing section
    csv += '\n# Routing\n';
    csv += `Local Executions,${metrics.routing.local.count}\n`;
    csv += `Local Avg Time (ms),${metrics.routing.local.avgTime}\n`;
    csv += `Local Percentage,${metrics.routing.local.percentage}%\n`;
    csv += `Cloud Executions,${metrics.routing.cloud.count}\n`;
    csv += `Cloud Avg Time (ms),${metrics.routing.cloud.avgTime}\n`;
    csv += `Cloud Percentage,${metrics.routing.cloud.percentage}%\n`;
    csv += `Cache Hits,${metrics.routing.cache.hits}\n`;
    csv += `Cache Misses,${metrics.routing.cache.misses}\n`;

    // Resources section
    csv += '\n# Resources\n';
    csv += `Current Memory (MB),${metrics.resources.memory.current}\n`;
    csv += `Peak Memory (MB),${metrics.resources.memory.peak}\n`;
    csv += `Average Memory (MB),${metrics.resources.memory.avg}\n`;

    // Top tools
    csv += '\n# Top Tools\n';
    csv += 'Tool Name,Executions,Avg Time (ms),Errors\n';
    for (const tool of metrics.tools.topTools) {
      csv += `${tool.name},${tool.count},${Math.round(tool.avgTime)},${tool.errors}\n`;
    }

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `data20-metrics-${Date.now()}.csv`;
    a.click();

    URL.revokeObjectURL(url);
    console.log('[PerformanceMonitor] Metrics exported as CSV');
  }

  /**
   * Reset metrics
   */
  resetMetrics() {
    this.metrics = {
      tools: {
        executions: 0,
        totalTime: 0,
        byTool: {},
        byComplexity: {
          simple: { count: 0, totalTime: 0, errors: 0 },
          medium: { count: 0, totalTime: 0, errors: 0 },
          complex: { count: 0, totalTime: 0, errors: 0 }
        }
      },
      routing: {
        local: { count: 0, totalTime: 0, errors: 0 },
        cloud: { count: 0, totalTime: 0, errors: 0 },
        cache: { hits: 0, misses: 0 },
        queued: { count: 0 }
      },
      resources: {
        peakMemory: 0,
        avgMemory: 0,
        memorySamples: [],
        pyodideLoadTime: 0
      },
      errors: {
        total: 0,
        byType: {},
        recent: []
      },
      session: {
        startTime: Date.now(),
        toolsAvailable: this.metrics.session.toolsAvailable,
        articlesStored: this.metrics.session.articlesStored
      }
    };

    console.log('[PerformanceMonitor] Metrics reset');
  }

  /**
   * Update session info
   */
  updateSessionInfo(toolsAvailable, articlesStored) {
    this.metrics.session.toolsAvailable = toolsAvailable;
    this.metrics.session.articlesStored = articlesStored;
  }

  /**
   * Set Pyodide load time
   */
  setPyodideLoadTime(loadTime) {
    this.metrics.resources.pyodideLoadTime = loadTime;
  }

  /**
   * Format duration
   */
  formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * Shutdown monitor
   */
  shutdown() {
    console.log('[PerformanceMonitor] Shutting down...');
    this.stopMemorySampling();
    this.stopPeriodicPersistence();
    this.persistMetrics(); // Final persist
  }
}

export default PerformanceMonitor;
