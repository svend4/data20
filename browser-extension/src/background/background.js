/**
 * Background Service Worker
 * Phase 9.1: Browser Extension + WASM Backend
 *
 * Manages:
 * - Pyodide initialization
 * - Python runtime
 * - Tool execution
 * - Context menus
 * - Message handling
 */

import { PyodideManager } from './pyodide-manager.js';
import { ToolRegistry } from './tool-registry.js';
import { StorageManager } from '../utils/storage.js';

// Global state
let pyodideManager = null;
let toolRegistry = null;
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
        result = await toolRegistry.executeTool('calculate_reading_time', {
          text: selectedText
        });
        showNotification('Reading Time', `${result.reading_time_minutes} minutes`);
        break;

      case 'data20-extract-keywords':
        result = await toolRegistry.executeTool('extract_keywords', {
          text: selectedText
        });
        showNotification('Keywords', result.keywords.join(', '));
        break;

      case 'data20-count-words':
        result = await toolRegistry.executeTool('count_words', {
          text: selectedText
        });
        showNotification('Word Count', `${result.total_words} words`);
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

            const result = await toolRegistry.executeTool(
              message.toolName,
              message.parameters
            );

            sendResponse({
              success: true,
              result: result
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
 * Analyze page content
 */
async function analyzePageContent(content) {
  const results = {};

  // Calculate reading time
  results.readingTime = await toolRegistry.executeTool('calculate_reading_time', {
    text: content.text
  });

  // Extract keywords
  results.keywords = await toolRegistry.executeTool('extract_keywords', {
    text: content.text
  });

  // Count words
  results.wordCount = await toolRegistry.executeTool('count_words', {
    text: content.text
  });

  // Detect language
  results.language = await toolRegistry.executeTool('detect_language', {
    text: content.text
  });

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
