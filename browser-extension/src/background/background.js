/**
 * Background Service Worker
 * Phase 9.1: Browser Extension + WASM Backend
 * Phase 9.2.3: Integrated Smart Router
 *
 * Manages:
 * - Pyodide initialization
 * - Python runtime
 * - Tool execution (via Smart Router)
 * - Context menus
 * - Message handling
 * - Intelligent routing (local/cloud)
 */

import { PyodideManager } from './pyodide-manager.js';
import { ToolRegistry } from './tool-registry.js';
import { SmartRouter } from './smart-router.js';
import { StorageManager } from '../utils/storage.js';

// Global state
let pyodideManager = null;
let toolRegistry = null;
let smartRouter = null;
let isInitialized = false;

/**
 * Initialize extension
 */
async function initialize() {
  console.log('🚀 Data20 Extension initializing...');

  try {
    // Initialize storage
    await StorageManager.initialize();

    // Initialize Pyodide
    console.log('📦 Loading Pyodide...');
    pyodideManager = new PyodideManager();
    await pyodideManager.initialize();
    console.log('✅ Pyodide loaded successfully');

    // Initialize tool registry
    console.log('🔧 Loading tools...');
    toolRegistry = new ToolRegistry(pyodideManager);
    await toolRegistry.loadTools();
    console.log(`✅ Loaded ${toolRegistry.getToolCount()} tools`);

    // Initialize smart router
    console.log('🧭 Initializing Smart Router...');
    smartRouter = new SmartRouter(toolRegistry, StorageManager);
    console.log('✅ Smart Router ready');

    // Setup context menus
    setupContextMenus();

    // Setup message listeners
    setupMessageListeners();

    isInitialized = true;
    console.log('✅ Data20 Extension ready!');

    // Notify popup
    chrome.runtime.sendMessage({
      type: 'INITIALIZATION_COMPLETE',
      toolCount: toolRegistry.getToolCount()
    }).catch(() => {
      // Popup might not be open
    });

  } catch (error) {
    console.error('❌ Initialization failed:', error);
    isInitialized = false;
  }
}

/**
 * Setup context menus
 */
function setupContextMenus() {
  // Remove existing menus
  chrome.contextMenus.removeAll();

  // Create parent menu
  chrome.contextMenus.create({
    id: 'data20-main',
    title: 'Data20 Tools',
    contexts: ['selection', 'page', 'link']
  });

  // Text analysis submenu
  chrome.contextMenus.create({
    id: 'data20-analyze-text',
    parentId: 'data20-main',
    title: 'Analyze selected text',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'data20-reading-time',
    parentId: 'data20-analyze-text',
    title: 'Calculate reading time',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'data20-extract-keywords',
    parentId: 'data20-analyze-text',
    title: 'Extract keywords',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'data20-count-words',
    parentId: 'data20-analyze-text',
    title: 'Count words',
    contexts: ['selection']
  });

  // Page actions
  chrome.contextMenus.create({
    id: 'data20-analyze-page',
    parentId: 'data20-main',
    title: 'Analyze current page',
    contexts: ['page']
  });

  // Save to knowledge base
  chrome.contextMenus.create({
    id: 'data20-save-selection',
    parentId: 'data20-main',
    title: 'Save to knowledge base',
    contexts: ['selection']
  });

  console.log('✅ Context menus created');
}

/**
 * Handle context menu clicks
 */
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  console.log('Context menu clicked:', info.menuItemId);

  if (!isInitialized) {
    console.warn('Extension not initialized yet');
    return;
  }

  const selectedText = info.selectionText || '';

  try {
    let result;

    switch (info.menuItemId) {
      case 'data20-reading-time':
        result = await smartRouter.executeTool('calculate_reading_time', {
          text: selectedText
        });
        showNotification('Reading Time', `${result.result.reading_time_minutes} minutes (${result.execution.location})`);
        break;

      case 'data20-extract-keywords':
        result = await smartRouter.executeTool('extract_keywords', {
          text: selectedText
        });
        showNotification('Keywords', result.result.keywords.join(', '));
        break;

      case 'data20-count-words':
        result = await smartRouter.executeTool('count_words', {
          text: selectedText
        });
        showNotification('Word Count', `${result.result.total_words} words`);
        break;

      case 'data20-save-selection':
        await saveToKnowledgeBase(selectedText, tab.url);
        showNotification('Saved', 'Selection saved to knowledge base');
        break;

      case 'data20-analyze-page':
        // Send message to content script to extract page content
        chrome.tabs.sendMessage(tab.id, {
          type: 'EXTRACT_PAGE_CONTENT'
        });
        break;
    }
  } catch (error) {
    console.error('Tool execution failed:', error);
    showNotification('Error', error.message);
  }
});

/**
 * Setup message listeners
 */
function setupMessageListeners() {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Message received:', message.type);

    // Handle async responses
    (async () => {
      try {
        switch (message.type) {
          case 'GET_STATUS':
            sendResponse({
              initialized: isInitialized,
              toolCount: toolRegistry ? toolRegistry.getToolCount() : 0
            });
            break;

          case 'EXECUTE_TOOL':
            if (!isInitialized) {
              throw new Error('Extension not initialized');
            }

            const result = await smartRouter.executeTool(
              message.toolName,
              message.parameters
            );

            sendResponse({
              success: true,
              result: result.result,
              execution: result.execution
            });
            break;

          case 'GET_TOOLS':
            if (!isInitialized) {
              throw new Error('Extension not initialized');
            }

            const tools = toolRegistry.getTools();
            sendResponse({
              success: true,
              tools: tools
            });
            break;

          case 'PAGE_CONTENT_EXTRACTED':
            // Received page content from content script
            const pageResult = await analyzePageContent(message.content);
            sendResponse({
              success: true,
              result: pageResult
            });
            break;

          case 'GET_ROUTER_METRICS':
            if (!isInitialized || !smartRouter) {
              throw new Error('Router not initialized');
            }

            const metrics = smartRouter.getMetrics();
            sendResponse({
              success: true,
              metrics: metrics
            });
            break;

          case 'GET_ROUTER_CONFIG':
            if (!isInitialized || !smartRouter) {
              throw new Error('Router not initialized');
            }

            const config = smartRouter.getConfig();
            sendResponse({
              success: true,
              config: config
            });
            break;

          case 'UPDATE_ROUTER_CONFIG':
            if (!isInitialized || !smartRouter) {
              throw new Error('Router not initialized');
            }

            smartRouter.updateConfig(message.config);
            sendResponse({
              success: true,
              message: 'Configuration updated'
            });
            break;

          case 'RESET_ROUTER_METRICS':
            if (!isInitialized || !smartRouter) {
              throw new Error('Router not initialized');
            }

            smartRouter.resetMetrics();
            sendResponse({
              success: true,
              message: 'Metrics reset'
            });
            break;

          default:
            sendResponse({
              success: false,
              error: `Unknown message type: ${message.type}`
            });
        }
      } catch (error) {
        console.error('Message handler error:', error);
        sendResponse({
          success: false,
          error: error.message
        });
      }
    })();

    // Return true to indicate async response
    return true;
  });
}

/**
 * Analyze page content (using Smart Router)
 */
async function analyzePageContent(content) {
  const results = {};

  // Calculate reading time
  const readingTimeResult = await smartRouter.executeTool('calculate_reading_time', {
    text: content.text
  });
  results.readingTime = readingTimeResult.result;

  // Extract keywords
  const keywordsResult = await smartRouter.executeTool('extract_keywords', {
    text: content.text
  });
  results.keywords = keywordsResult.result;

  // Count words
  const wordCountResult = await smartRouter.executeTool('count_words', {
    text: content.text
  });
  results.wordCount = wordCountResult.result;

  // Detect language
  const languageResult = await smartRouter.executeTool('detect_language', {
    text: content.text
  });
  results.language = languageResult.result;

  return results;
}

/**
 * Save content to knowledge base
 */
async function saveToKnowledgeBase(content, url) {
  const article = {
    id: Date.now(),
    content: content,
    url: url,
    timestamp: new Date().toISOString(),
    tags: []
  };

  // Extract keywords as tags
  const keywordResult = await toolRegistry.executeTool('extract_keywords', {
    text: content
  });
  article.tags = keywordResult.keywords.slice(0, 5);

  // Save to IndexedDB
  await StorageManager.saveArticle(article);
}

/**
 * Show notification
 */
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('public/icons/icon-128.png'),
    title: title,
    message: message
  });
}

/**
 * Handle installation
 */
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Extension installed:', details.reason);

  if (details.reason === 'install') {
    // First installation
    chrome.tabs.create({
      url: 'options.html'
    });
  }
});

/**
 * Start initialization
 */
initialize().catch(error => {
  console.error('Failed to initialize extension:', error);
});

// Export for testing
export { initialize, toolRegistry, pyodideManager };
