/**
 * Performance Optimizer
 * Phase 8.3.3: Performance & Memory Optimization
 *
 * Features:
 * - Memory usage monitoring (target: < 200MB idle)
 * - Startup time tracking (target: < 5s)
 * - Garbage collection hints
 * - Memory leak detection
 * - Performance metrics
 */

const log = require('electron-log');
const { app } = require('electron');

class PerformanceOptimizer {
  constructor(options = {}) {
    this.enabled = options.enabled !== false;
    this.memoryThreshold = options.memoryThreshold || 200; // MB
    this.gcInterval = options.gcInterval || 60000; // 60 seconds
    this.monitorInterval = options.monitorInterval || 30000; // 30 seconds

    this.metrics = {
      startupTime: null,
      startTime: Date.now(),
      memoryUsage: [],
      gcRuns: 0,
      peakMemory: 0,
    };

    this.monitoringTimer = null;
    this.gcTimer = null;

    if (this.enabled) {
      this.init();
    }
  }

  /**
   * Initialize performance optimizer
   */
  init() {
    log.info('Performance optimizer initialized');

    // Record startup time
    app.on('ready', () => {
      this.metrics.startupTime = Date.now() - this.metrics.startTime;
      log.info(`Startup time: ${this.metrics.startupTime}ms`);

      if (this.metrics.startupTime > 5000) {
        log.warn(`⚠️ Startup time (${this.metrics.startupTime}ms) exceeds target (5000ms)`);
      }
    });

    // Start monitoring
    this.startMonitoring();

    // Enable GC in development mode
    if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
      this.enableGCProfiling();
    }
  }

  /**
   * Enable GC profiling (development only)
   */
  enableGCProfiling() {
    try {
      app.commandLine.appendSwitch('js-flags', '--expose-gc');
      log.info('GC profiling enabled');

      // Start periodic GC if memory threshold exceeded
      this.startPeriodicGC();
    } catch (error) {
      log.error('Failed to enable GC profiling:', error);
    }
  }

  /**
   * Start memory monitoring
   */
  startMonitoring() {
    if (this.monitoringTimer) {
      return;
    }

    this.monitoringTimer = setInterval(() => {
      const usage = this.getMemoryUsage();

      // Record memory usage
      this.metrics.memoryUsage.push({
        timestamp: Date.now(),
        heapUsed: usage.heapUsed,
        heapTotal: usage.heapTotal,
        external: usage.external,
        rss: usage.rss,
      });

      // Keep only last 100 measurements
      if (this.metrics.memoryUsage.length > 100) {
        this.metrics.memoryUsage.shift();
      }

      // Update peak memory
      if (usage.heapUsed > this.metrics.peakMemory) {
        this.metrics.peakMemory = usage.heapUsed;
      }

      // Log if memory usage is high
      if (usage.heapUsed > this.memoryThreshold) {
        log.warn(
          `⚠️ High memory usage: ${usage.heapUsed.toFixed(2)}MB (threshold: ${this.memoryThreshold}MB)`
        );
      }

      // Log current usage
      if (process.env.NODE_ENV === 'development') {
        log.info(
          `Memory: Heap ${usage.heapUsed.toFixed(2)}MB / ${usage.heapTotal.toFixed(2)}MB, RSS ${usage.rss.toFixed(2)}MB`
        );
      }
    }, this.monitorInterval);

    log.info('Memory monitoring started');
  }

  /**
   * Stop memory monitoring
   */
  stopMonitoring() {
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
      log.info('Memory monitoring stopped');
    }
  }

  /**
   * Start periodic garbage collection
   */
  startPeriodicGC() {
    if (this.gcTimer || !global.gc) {
      return;
    }

    this.gcTimer = setInterval(() => {
      const beforeUsage = this.getMemoryUsage();

      // Only run GC if memory usage is above threshold
      if (beforeUsage.heapUsed > this.memoryThreshold * 0.75) {
        try {
          global.gc();
          this.metrics.gcRuns++;

          const afterUsage = this.getMemoryUsage();
          const freed = beforeUsage.heapUsed - afterUsage.heapUsed;

          log.info(
            `GC: Freed ${freed.toFixed(2)}MB (${beforeUsage.heapUsed.toFixed(2)}MB → ${afterUsage.heapUsed.toFixed(2)}MB)`
          );
        } catch (error) {
          log.error('GC failed:', error);
        }
      }
    }, this.gcInterval);

    log.info('Periodic GC started');
  }

  /**
   * Stop periodic garbage collection
   */
  stopPeriodicGC() {
    if (this.gcTimer) {
      clearInterval(this.gcTimer);
      this.gcTimer = null;
      log.info('Periodic GC stopped');
    }
  }

  /**
   * Get current memory usage in MB
   */
  getMemoryUsage() {
    const usage = process.memoryUsage();

    return {
      heapUsed: usage.heapUsed / 1024 / 1024,
      heapTotal: usage.heapTotal / 1024 / 1024,
      external: usage.external / 1024 / 1024,
      rss: usage.rss / 1024 / 1024,
    };
  }

  /**
   * Get performance metrics
   */
  getMetrics() {
    const currentUsage = this.getMemoryUsage();
    const uptime = Date.now() - this.metrics.startTime;

    // Calculate average memory usage
    let avgMemory = 0;
    if (this.metrics.memoryUsage.length > 0) {
      avgMemory =
        this.metrics.memoryUsage.reduce((sum, m) => sum + m.heapUsed, 0) /
        this.metrics.memoryUsage.length;
    }

    return {
      startupTime: this.metrics.startupTime,
      uptime: uptime,
      memory: {
        current: currentUsage,
        average: avgMemory,
        peak: this.metrics.peakMemory,
        history: this.metrics.memoryUsage.slice(-10), // Last 10 measurements
      },
      gc: {
        runs: this.metrics.gcRuns,
        available: !!global.gc,
      },
      performance: {
        startupTarget: 5000,
        startupTargetMet: this.metrics.startupTime ? this.metrics.startupTime < 5000 : null,
        memoryTarget: this.memoryThreshold,
        memoryTargetMet: currentUsage.heapUsed < this.memoryThreshold,
      },
    };
  }

  /**
   * Generate performance report
   */
  generateReport() {
    const metrics = this.getMetrics();

    const report = {
      summary: {
        startupTime: `${metrics.startupTime}ms`,
        uptime: `${Math.floor(metrics.uptime / 1000)}s`,
        memoryUsed: `${metrics.memory.current.heapUsed.toFixed(2)}MB`,
        peakMemory: `${metrics.memory.peak.toFixed(2)}MB`,
        gcRuns: metrics.gc.runs,
      },
      targets: {
        startup: {
          target: `${metrics.performance.startupTarget}ms`,
          actual: `${metrics.startupTime}ms`,
          met: metrics.performance.startupTargetMet ? '✅' : '❌',
        },
        memory: {
          target: `${metrics.performance.memoryTarget}MB`,
          actual: `${metrics.memory.current.heapUsed.toFixed(2)}MB`,
          met: metrics.performance.memoryTargetMet ? '✅' : '❌',
        },
      },
      recommendations: this.generateRecommendations(metrics),
    };

    return report;
  }

  /**
   * Generate performance recommendations
   */
  generateRecommendations(metrics) {
    const recommendations = [];

    // Startup time
    if (metrics.startupTime && metrics.startupTime > 5000) {
      recommendations.push({
        type: 'warning',
        category: 'startup',
        message: `Startup time (${metrics.startupTime}ms) exceeds target (5000ms)`,
        suggestions: [
          'Defer backend initialization',
          'Reduce preloaded modules',
          'Optimize bundle size',
          'Use lazy loading for non-critical features',
        ],
      });
    }

    // Memory usage
    if (metrics.memory.current.heapUsed > this.memoryThreshold) {
      recommendations.push({
        type: 'warning',
        category: 'memory',
        message: `Memory usage (${metrics.memory.current.heapUsed.toFixed(2)}MB) exceeds target (${this.memoryThreshold}MB)`,
        suggestions: [
          'Check for memory leaks',
          'Reduce cache sizes',
          'Unload unused modules',
          'Enable periodic GC',
        ],
      });
    }

    // Memory growth
    if (this.metrics.memoryUsage.length >= 10) {
      const recent = this.metrics.memoryUsage.slice(-10);
      const growth =
        recent[recent.length - 1].heapUsed - recent[0].heapUsed;

      if (growth > 50) {
        // More than 50MB growth
        recommendations.push({
          type: 'warning',
          category: 'memory-leak',
          message: `Possible memory leak detected: ${growth.toFixed(2)}MB growth in last ${this.monitorInterval * 10 / 1000}s`,
          suggestions: [
            'Check for event listener leaks',
            'Verify proper cleanup in components',
            'Review backend process management',
            'Use Chrome DevTools memory profiler',
          ],
        });
      }
    }

    // All good
    if (recommendations.length === 0) {
      recommendations.push({
        type: 'success',
        category: 'overall',
        message: '✅ Performance is good!',
        suggestions: [],
      });
    }

    return recommendations;
  }

  /**
   * Force garbage collection
   */
  forceGC() {
    if (global.gc) {
      const before = this.getMemoryUsage();
      global.gc();
      const after = this.getMemoryUsage();
      const freed = before.heapUsed - after.heapUsed;

      log.info(`Manual GC: Freed ${freed.toFixed(2)}MB`);
      return { freed, before, after };
    }

    return null;
  }

  /**
   * Clear memory history
   */
  clearHistory() {
    this.metrics.memoryUsage = [];
    log.info('Memory history cleared');
  }

  /**
   * Destroy optimizer
   */
  destroy() {
    this.stopMonitoring();
    this.stopPeriodicGC();
    log.info('Performance optimizer destroyed');
  }
}

module.exports = PerformanceOptimizer;
