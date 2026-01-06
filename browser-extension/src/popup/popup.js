/**
 * Popup UI Logic
 * Phase 9.1.4: Extension UI
 * Phase 9.2.4: Queue Management UI
 */

import { StorageManager } from '../utils/storage.js';

// State
let tools = [];
let articles = [];
let queueStats = null;
let performanceMetrics = null;
let currentTab = 'tools';
let queueUpdateInterval = null;
let metricsUpdateInterval = null;

/**
 * Initialize popup
 */
async function initialize() {
  console.log('Initializing popup...');

  // Setup tabs
  setupTabs();

  // Setup event listeners
  setupEventListeners();

  // Check extension status
  await checkStatus();

  // Load tools
  await loadTools();

  // Load articles
  await loadArticles();

  // Update stats
  await updateStats();

  // Start queue updates
  startQueueUpdates();

  // Start metrics updates
  startMetricsUpdates();
}

/**
 * Cleanup on popup close
 */
window.addEventListener('beforeunload', () => {
  stopQueueUpdates();
  stopMetricsUpdates();
});

/**
 * Check extension status
 */
async function checkStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_STATUS' });

    const statusEl = document.getElementById('status');

    if (response.initialized) {
      statusEl.textContent = `Ready • ${response.toolCount} tools loaded`;
      statusEl.classList.remove('loading');
    } else {
      statusEl.textContent = 'Initializing...';
      statusEl.classList.add('loading');

      // Retry after 2 seconds
      setTimeout(checkStatus, 2000);
    }
  } catch (error) {
    console.error('Failed to check status:', error);
  }
}

/**
 * Load tools from background
 */
async function loadTools() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_TOOLS' });

    if (response.success) {
      tools = response.tools;
      renderTools(tools);
    }
  } catch (error) {
    console.error('Failed to load tools:', error);
    showError('Failed to load tools');
  }
}

/**
 * Render tools list
 */
function renderTools(toolsToRender) {
  const toolList = document.getElementById('tool-list');

  if (!toolsToRender || toolsToRender.length === 0) {
    toolList.innerHTML = '<div class="loading">No tools available</div>';
    return;
  }

  toolList.innerHTML = '';

  for (const tool of toolsToRender) {
    const toolItem = document.createElement('div');
    toolItem.className = 'tool-item';
    toolItem.innerHTML = `
      <div class="name">${formatToolName(tool.name)}</div>
      <div class="category">${tool.category}</div>
    `;

    toolItem.addEventListener('click', () => {
      openToolDialog(tool);
    });

    toolList.appendChild(toolItem);
  }
}

/**
 * Format tool name for display
 */
function formatToolName(name) {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Open tool execution dialog
 */
function openToolDialog(tool) {
  // For now, just show a simple prompt
  // In production, would open a modal dialog

  const input = prompt(`Execute ${formatToolName(tool.name)}:\n\nEnter text to analyze:`);

  if (input) {
    executeTool(tool.name, { text: input });
  }
}

/**
 * Execute tool
 */
async function executeTool(toolName, parameters) {
  try {
    const statusEl = document.getElementById('status');
    statusEl.textContent = 'Executing tool...';
    statusEl.classList.add('loading');

    const response = await chrome.runtime.sendMessage({
      type: 'EXECUTE_TOOL',
      toolName: toolName,
      parameters: parameters
    });

    statusEl.classList.remove('loading');

    if (response.success) {
      showResult(toolName, response.result);
      statusEl.textContent = 'Ready';
    } else {
      showError(response.error);
      statusEl.textContent = 'Error';
    }
  } catch (error) {
    console.error('Tool execution failed:', error);
    showError(error.message);
  }
}

/**
 * Show result
 */
function showResult(toolName, result) {
  // Format result as string
  const resultStr = JSON.stringify(result, null, 2);

  alert(`${formatToolName(toolName)} Result:\n\n${resultStr}`);
}

/**
 * Show error
 */
function showError(message) {
  alert(`Error: ${message}`);
}

/**
 * Load articles from storage
 */
async function loadArticles() {
  try {
    // Initialize storage
    await StorageManager.initialize();

    articles = await StorageManager.getArticles();
    renderArticles(articles);
  } catch (error) {
    console.error('Failed to load articles:', error);
  }
}

/**
 * Render articles list
 */
function renderArticles(articlesToRender) {
  const articlesList = document.getElementById('articles-list');

  if (!articlesToRender || articlesToRender.length === 0) {
    articlesList.innerHTML = '<div class="loading">No articles saved yet</div>';
    return;
  }

  articlesList.innerHTML = '';

  for (const article of articlesToRender) {
    const articleItem = document.createElement('div');
    articleItem.className = 'article-item';

    const timestamp = new Date(article.timestamp).toLocaleDateString();

    articleItem.innerHTML = `
      <div class="title">${article.content.substring(0, 50)}...</div>
      <div class="meta">${timestamp} • ${article.url}</div>
    `;

    articleItem.addEventListener('click', () => {
      viewArticle(article);
    });

    articlesList.appendChild(articleItem);
  }
}

/**
 * View article
 */
function viewArticle(article) {
  const content = `
Content: ${article.content}

URL: ${article.url}
Saved: ${new Date(article.timestamp).toLocaleString()}
Tags: ${article.tags.join(', ')}
  `.trim();

  alert(content);
}

/**
 * Update stats
 */
async function updateStats() {
  // Tool count
  document.getElementById('tool-count').textContent = tools.length;

  // Article count
  document.getElementById('article-count').textContent = articles.length;

  // Memory usage (approximate)
  if (performance.memory) {
    const memoryMB = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
    document.getElementById('memory-usage').textContent = memoryMB;
  }

  // Pyodide version
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_STATUS' });
    document.getElementById('pyodide-version').textContent = '0.25.0';
  } catch (error) {
    console.error('Failed to get version:', error);
  }
}

/**
 * Setup tabs
 */
function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;

      // Remove active class from all tabs
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));

      // Add active class to clicked tab
      tab.classList.add('active');
      document.getElementById(`${tabName}-tab`).classList.add('active');

      currentTab = tabName;
    });
  });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Tool search
  const toolSearch = document.getElementById('tool-search');
  toolSearch.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = tools.filter(tool =>
      tool.name.toLowerCase().includes(query) ||
      tool.category.toLowerCase().includes(query)
    );
    renderTools(filtered);
  });

  // Article search
  const articleSearch = document.getElementById('article-search');
  articleSearch.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = articles.filter(article =>
      article.content.toLowerCase().includes(query) ||
      article.url.toLowerCase().includes(query)
    );
    renderArticles(filtered);
  });

  // Clear articles button
  const clearBtn = document.getElementById('clear-articles');
  clearBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear all articles?')) {
      // Clear from storage
      for (const article of articles) {
        await StorageManager.deleteArticle(article.id);
      }

      articles = [];
      renderArticles(articles);
      updateStats();
    }
  });

  // Options button
  const optionsBtn = document.getElementById('options-btn');
  optionsBtn.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  // Queue management buttons
  const triggerSyncBtn = document.getElementById('trigger-sync');
  triggerSyncBtn.addEventListener('click', async () => {
    try {
      const statusEl = document.getElementById('status');
      statusEl.textContent = 'Syncing queue...';
      statusEl.classList.add('loading');

      const response = await chrome.runtime.sendMessage({ type: 'TRIGGER_QUEUE_SYNC' });

      if (response.success) {
        statusEl.textContent = 'Queue synced';
        await updateQueueStats();
      }

      setTimeout(() => {
        statusEl.textContent = 'Ready';
        statusEl.classList.remove('loading');
      }, 2000);
    } catch (error) {
      console.error('Failed to trigger sync:', error);
    }
  });

  const retryFailedBtn = document.getElementById('retry-failed');
  retryFailedBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'RETRY_ALL_FAILED' });

      if (response.success) {
        alert(`${response.count} failed jobs queued for retry`);
        await updateQueueStats();
      }
    } catch (error) {
      console.error('Failed to retry jobs:', error);
    }
  });

  const clearCompletedBtn = document.getElementById('clear-completed');
  clearCompletedBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'CLEAR_COMPLETED_JOBS' });

      if (response.success) {
        alert(response.message);
        await updateQueueStats();
      }
    } catch (error) {
      console.error('Failed to clear completed:', error);
    }
  });

  const clearFailedBtn = document.getElementById('clear-failed');
  clearFailedBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'CLEAR_FAILED_JOBS' });

      if (response.success) {
        alert(response.message);
        await updateQueueStats();
      }
    } catch (error) {
      console.error('Failed to clear failed:', error);
    }
  });

  // Metrics management buttons
  const exportJsonBtn = document.getElementById('export-json');
  exportJsonBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'EXPORT_METRICS_JSON' });

      if (response.success) {
        alert('Metrics exported as JSON');
      }
    } catch (error) {
      console.error('Failed to export metrics:', error);
    }
  });

  const exportCsvBtn = document.getElementById('export-csv');
  exportCsvBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'EXPORT_METRICS_CSV' });

      if (response.success) {
        alert('Metrics exported as CSV');
      }
    } catch (error) {
      console.error('Failed to export metrics:', error);
    }
  });

  const resetMetricsBtn = document.getElementById('reset-metrics');
  resetMetricsBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to reset all performance metrics?')) {
      try {
        const response = await chrome.runtime.sendMessage({ type: 'RESET_PERFORMANCE_METRICS' });

        if (response.success) {
          alert('Performance metrics reset');
          await updatePerformanceMetrics();
        }
      } catch (error) {
        console.error('Failed to reset metrics:', error);
      }
    }
  });
}

/**
 * Update queue statistics
 */
async function updateQueueStats() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_QUEUE_STATS' });

    if (response.success) {
      queueStats = response.stats;

      // Update queue stats cards
      document.getElementById('queue-queued').textContent = queueStats.queue.queued || 0;
      document.getElementById('queue-completed').textContent = queueStats.queue.completed || 0;
      document.getElementById('queue-processing').textContent = queueStats.queue.processing || 0;
      document.getElementById('queue-failed').textContent = queueStats.queue.failed || 0;

      // Update network status
      const networkEl = document.getElementById('queue-network');
      networkEl.textContent = queueStats.network.online ? 'Online ✓' : 'Offline';
      networkEl.style.color = queueStats.network.online ? '#4ade80' : '#f87171';

      // Update success rate
      document.getElementById('queue-success-rate').textContent =
        queueStats.lifetime.successRate ? `${queueStats.lifetime.successRate}%` : '-';

      // Update last sync
      const lastSyncEl = document.getElementById('queue-last-sync');
      if (queueStats.sync.lastSuccess) {
        const lastSync = new Date(queueStats.sync.lastSuccess);
        const now = new Date();
        const diffMinutes = Math.floor((now - lastSync) / 60000);

        if (diffMinutes < 1) {
          lastSyncEl.textContent = 'Just now';
        } else if (diffMinutes < 60) {
          lastSyncEl.textContent = `${diffMinutes}m ago`;
        } else {
          lastSyncEl.textContent = lastSync.toLocaleTimeString();
        }
      } else {
        lastSyncEl.textContent = 'Never';
      }
    }
  } catch (error) {
    console.error('Failed to update queue stats:', error);
  }
}

/**
 * Start periodic queue updates
 */
function startQueueUpdates() {
  // Initial update
  updateQueueStats();

  // Update every 5 seconds
  queueUpdateInterval = setInterval(() => {
    if (currentTab === 'queue') {
      updateQueueStats();
    }
  }, 5000);
}

/**
 * Stop queue updates
 */
function stopQueueUpdates() {
  if (queueUpdateInterval) {
    clearInterval(queueUpdateInterval);
    queueUpdateInterval = null;
  }
}

/**
 * Update performance metrics
 */
async function updatePerformanceMetrics() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_PERFORMANCE_METRICS' });

    if (response.success) {
      performanceMetrics = response.metrics;

      // Summary section
      document.getElementById('metrics-total-exec').textContent = performanceMetrics.summary.totalExecutions;
      document.getElementById('metrics-avg-time').textContent = `${performanceMetrics.summary.avgExecutionTime}ms`;
      document.getElementById('metrics-cache-rate').textContent = `${performanceMetrics.summary.cacheHitRate}%`;
      document.getElementById('metrics-error-rate').textContent = `${performanceMetrics.summary.errorRate}%`;

      // Routing section
      document.getElementById('metrics-local-pct').textContent =
        `${performanceMetrics.routing.local.percentage}% (${performanceMetrics.routing.local.avgTime}ms avg)`;
      document.getElementById('metrics-cloud-pct').textContent =
        `${performanceMetrics.routing.cloud.percentage}% (${performanceMetrics.routing.cloud.avgTime}ms avg)`;
      document.getElementById('metrics-cache-hits').textContent = performanceMetrics.routing.cache.hits;

      // Resources section
      document.getElementById('metrics-mem-current').textContent = `${performanceMetrics.resources.memory.current} MB`;
      document.getElementById('metrics-mem-peak').textContent = `${performanceMetrics.resources.memory.peak} MB`;
      document.getElementById('metrics-pyodide-load').textContent = `${performanceMetrics.resources.pyodideLoadTime}ms`;

      // Top tools
      const topToolsEl = document.getElementById('metrics-top-tools');
      if (performanceMetrics.tools.topTools && performanceMetrics.tools.topTools.length > 0) {
        topToolsEl.innerHTML = '';

        for (const tool of performanceMetrics.tools.topTools.slice(0, 5)) {
          const toolDiv = document.createElement('div');
          toolDiv.style.cssText = 'display: flex; justify-content: space-between; margin-bottom: 4px; padding: 4px; background: rgba(255, 255, 255, 0.05); border-radius: 4px;';

          toolDiv.innerHTML = `
            <span style="flex: 1;">${formatToolName(tool.name)}</span>
            <span style="font-weight: 600;">${tool.count}x</span>
            <span style="margin-left: 8px; opacity: 0.8;">${Math.round(tool.avgTime)}ms</span>
          `;

          topToolsEl.appendChild(toolDiv);
        }
      } else {
        topToolsEl.innerHTML = '<div style="opacity: 0.7;">No data yet</div>';
      }
    }
  } catch (error) {
    console.error('Failed to update performance metrics:', error);
  }
}

/**
 * Start periodic metrics updates
 */
function startMetricsUpdates() {
  // Initial update
  updatePerformanceMetrics();

  // Update every 5 seconds
  metricsUpdateInterval = setInterval(() => {
    if (currentTab === 'metrics') {
      updatePerformanceMetrics();
    }
  }, 5000);
}

/**
 * Stop metrics updates
 */
function stopMetricsUpdates() {
  if (metricsUpdateInterval) {
    clearInterval(metricsUpdateInterval);
    metricsUpdateInterval = null;
  }
}

/**
 * Listen for messages from background
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'INITIALIZATION_COMPLETE') {
    checkStatus();
    loadTools();
  }
});

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', initialize);
