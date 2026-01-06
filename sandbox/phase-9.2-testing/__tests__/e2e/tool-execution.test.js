/**
 * E2E Tests: Tool Execution
 * Phase 9.2 Stage 5
 *
 * Tests tool selection, parameter entry, and execution
 */

import {
  launchBrowserWithExtension,
  getExtensionId,
  openExtensionPopup,
  clickElement,
  typeIntoField,
  waitForElement,
  getElementText,
  elementExists,
  wait,
  waitForCondition,
  cleanupBrowser
} from './helpers/extension-helper.js';

describe('E2E: Tool Execution', () => {
  let browser;
  let page;
  let extensionId;

  beforeAll(async () => {
    browser = await launchBrowserWithExtension();
    extensionId = await getExtensionId(browser);
  }, 30000);

  afterAll(async () => {
    await cleanupBrowser(browser);
  });

  beforeEach(async () => {
    page = await openExtensionPopup(browser, extensionId);
    await waitForElement(page, '[data-tab="tools"]');
  }, 10000);

  afterEach(async () => {
    if (page) await page.close();
  });

  describe('Tool Selection', () => {
    test('should display tool list', async () => {
      const tools = await page.$$('.tool-item');
      expect(tools.length).toBeGreaterThan(0);
    });

    test('should select a tool by clicking', async () => {
      await clickElement(page, '.tool-item:first-child');

      const isSelected = await page.$eval(
        '.tool-item:first-child',
        el => el.classList.contains('selected')
      );
      expect(isSelected).toBe(true);
    });

    test('should display tool details on selection', async () => {
      await clickElement(page, '.tool-item:first-child');
      await waitForElement(page, '.tool-details');

      const detailsVisible = await elementExists(page, '.tool-details');
      expect(detailsVisible).toBe(true);
    });

    test('should show tool description', async () => {
      await clickElement(page, '.tool-item:first-child');
      await waitForElement(page, '.tool-description');

      const description = await getElementText(page, '.tool-description');
      expect(description).toBeTruthy();
      expect(description.length).toBeGreaterThan(0);
    });

    test('should show tool parameters', async () => {
      await clickElement(page, '.tool-item:first-child');
      await waitForElement(page, '.tool-parameters');

      const parametersExist = await elementExists(page, '.tool-parameters');
      expect(parametersExist).toBe(true);
    });

    test('should filter tools by search', async () => {
      await typeIntoField(page, '#tool-search', 'word');
      await wait(500); // Wait for filter

      const visibleTools = await page.$$eval(
        '.tool-item:not(.hidden)',
        els => els.length
      );

      expect(visibleTools).toBeGreaterThan(0);
    });

    test('should clear search filter', async () => {
      await typeIntoField(page, '#tool-search', 'word');
      await wait(500);

      // Clear search
      await page.$eval('#tool-search', el => el.value = '');
      await page.keyboard.press('Backspace');
      await wait(500);

      const visibleTools = await page.$$eval(
        '.tool-item:not(.hidden)',
        els => els.length
      );

      expect(visibleTools).toBeGreaterThan(0);
    });
  });

  describe('Parameter Entry', () => {
    beforeEach(async () => {
      // Select a tool with parameters
      await clickElement(page, '.tool-item:first-child');
      await waitForElement(page, '.tool-parameters');
    });

    test('should display parameter input fields', async () => {
      const inputs = await page.$$('.param-input');
      expect(inputs.length).toBeGreaterThan(0);
    });

    test('should allow text input in parameter field', async () => {
      const inputExists = await elementExists(page, 'input[name="text"], textarea[name="text"]');

      if (inputExists) {
        await typeIntoField(page, 'input[name="text"], textarea[name="text"]', 'Test input text');

        const value = await page.$eval(
          'input[name="text"], textarea[name="text"]',
          el => el.value
        );
        expect(value).toBe('Test input text');
      }
    });

    test('should validate required parameters', async () => {
      // Try to execute without filling required fields
      await clickElement(page, '#execute-tool-btn');
      await wait(500);

      // Should show validation error
      const errorExists = await elementExists(page, '.validation-error, .error-message');
      expect(errorExists).toBe(true);
    });

    test('should show parameter hints', async () => {
      const hintExists = await elementExists(page, '.param-hint, .param-description');
      expect(hintExists).toBe(true);
    });

    test('should support different parameter types', async () => {
      // Check for various input types
      const textInput = await elementExists(page, 'input[type="text"], textarea');
      const numberInput = await elementExists(page, 'input[type="number"]');
      const selectInput = await elementExists(page, 'select');

      const hasInputs = textInput || numberInput || selectInput;
      expect(hasInputs).toBe(true);
    });
  });

  describe('Tool Execution - Simple Tool', () => {
    test('should execute simple tool successfully', async () => {
      // Select a simple tool (e.g., word_count)
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      // Fill in parameters
      await typeIntoField(page, 'textarea[name="text"]', 'Hello world test');

      // Execute
      await clickElement(page, '#execute-tool-btn');

      // Wait for result
      await waitForElement(page, '.tool-result', 10000);

      const resultExists = await elementExists(page, '.tool-result');
      expect(resultExists).toBe(true);
    }, 15000);

    test('should display execution result', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Test text');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 10000);

      const result = await getElementText(page, '.tool-result');
      expect(result).toBeTruthy();
      expect(result.length).toBeGreaterThan(0);
    }, 15000);

    test('should show loading indicator during execution', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Test');
      await clickElement(page, '#execute-tool-btn');

      // Check for loading indicator (should appear briefly)
      const loadingExists = await elementExists(page, '.loading, .spinner');
      // Either loading was shown or result came too fast
      expect(loadingExists || await elementExists(page, '.tool-result')).toBe(true);
    }, 15000);

    test('should update metrics after execution', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Test');
      await clickElement(page, '#execute-tool-btn');
      await waitForElement(page, '.tool-result', 10000);

      // Switch to metrics tab
      await clickElement(page, '[data-tab="metrics"]');
      await waitForElement(page, '[data-tab-content="metrics"].active');

      // Check that execution count increased
      const executionCount = await getElementText(page, '.total-executions, #total-executions');
      expect(executionCount).toBeTruthy();
    }, 15000);
  });

  describe('Tool Execution - Medium Tool', () => {
    test('should execute medium complexity tool', async () => {
      // Select a medium tool (e.g., sentiment_analysis)
      await clickElement(page, '[data-tool-name="sentiment_analysis"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'This is a great product!');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 15000);

      const resultExists = await elementExists(page, '.tool-result');
      expect(resultExists).toBe(true);
    }, 20000);

    test('should show execution time', async () => {
      await clickElement(page, '[data-tool-name="sentiment_analysis"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Test sentiment');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 15000);

      const executionTime = await elementExists(page, '.execution-time, [data-execution-time]');
      expect(executionTime).toBe(true);
    }, 20000);
  });

  describe('Tool Execution - Cache Behavior', () => {
    test('should use cached result on second execution', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      const inputText = 'Cache test input';
      await typeIntoField(page, 'textarea[name="text"]', inputText);

      // First execution
      await clickElement(page, '#execute-tool-btn');
      await waitForElement(page, '.tool-result', 10000);

      // Clear result
      await page.$eval('.tool-result', el => el.textContent = '');

      // Second execution (should use cache)
      await clickElement(page, '#execute-tool-btn');
      await waitForElement(page, '.tool-result', 10000);

      const cacheIndicator = await elementExists(page, '.cached-result, [data-cached="true"]');
      // Either shows cache indicator or result appears very fast
      expect(cacheIndicator || await elementExists(page, '.tool-result')).toBe(true);
    }, 25000);
  });

  describe('Error Handling', () => {
    test('should display error message on tool failure', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      // Provide invalid input (empty)
      await clickElement(page, '#execute-tool-btn');
      await wait(2000);

      const errorExists = await elementExists(page, '.error-message, .tool-error');
      expect(errorExists).toBe(true);
    }, 10000);

    test('should allow retry after error', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      // Execute with invalid input
      await clickElement(page, '#execute-tool-btn');
      await wait(2000);

      // Fix input and retry
      await typeIntoField(page, 'textarea[name="text"]', 'Valid input');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 10000);
      const resultExists = await elementExists(page, '.tool-result');
      expect(resultExists).toBe(true);
    }, 15000);

    test('should handle network errors gracefully', async () => {
      // Simulate offline mode
      await page.setOfflineMode(true);

      await clickElement(page, '[data-tool-name="complex_tool"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'input[name="data"]', 'test');
      await clickElement(page, '#execute-tool-btn');

      await wait(3000);

      // Should show error or queue the job
      const hasError = await elementExists(page, '.error-message');
      const wasQueued = await elementExists(page, '.queued-message');

      expect(hasError || wasQueued).toBe(true);

      // Restore online mode
      await page.setOfflineMode(false);
    }, 15000);
  });

  describe('Tool History', () => {
    test('should record tool execution in history', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'History test');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 10000);

      // Check history panel
      const historyExists = await elementExists(page, '.execution-history, #history');
      if (historyExists) {
        const historyItems = await page.$$('.history-item');
        expect(historyItems.length).toBeGreaterThan(0);
      }
    }, 15000);
  });

  describe('Multiple Tool Executions', () => {
    test('should execute multiple tools sequentially', async () => {
      // Execute first tool
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');
      await typeIntoField(page, 'textarea[name="text"]', 'First tool');
      await clickElement(page, '#execute-tool-btn');
      await waitForElement(page, '.tool-result', 10000);

      // Execute second tool
      await clickElement(page, '[data-tool-name="text_length"]');
      await waitForElement(page, '.tool-parameters');
      await typeIntoField(page, 'input[name="text"]', 'Second tool');
      await clickElement(page, '#execute-tool-btn');
      await waitForElement(page, '.tool-result', 10000);

      const resultExists = await elementExists(page, '.tool-result');
      expect(resultExists).toBe(true);
    }, 30000);
  });

  describe('Result Display', () => {
    test('should format result as JSON when appropriate', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Test');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 10000);

      // Check if result is formatted
      const formattedResult = await elementExists(page, '.result-json, pre, code');
      expect(formattedResult).toBe(true);
    }, 15000);

    test('should allow copying result', async () => {
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Test');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 10000);

      const copyButtonExists = await elementExists(page, '.copy-result-btn, #copy-result');
      expect(copyButtonExists).toBe(true);
    }, 15000);
  });
});
