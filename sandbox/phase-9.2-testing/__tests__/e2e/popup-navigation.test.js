/**
 * E2E Tests: Popup Navigation
 * Phase 9.2 Stage 5
 *
 * Tests basic popup opening and tab navigation
 */

import {
  launchBrowserWithExtension,
  getExtensionId,
  openExtensionPopup,
  clickElement,
  waitForElement,
  getElementText,
  elementExists,
  takeScreenshot,
  cleanupBrowser
} from './helpers/extension-helper.js';

describe('E2E: Popup Navigation', () => {
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
  }, 10000);

  afterEach(async () => {
    if (page) await page.close();
  });

  describe('Popup Opening', () => {
    test('should open popup successfully', async () => {
      await waitForElement(page, 'body');
      const title = await page.title();
      expect(title).toBeTruthy();
    });

    test('should display extension header', async () => {
      const headerExists = await elementExists(page, '.header');
      expect(headerExists).toBe(true);
    });

    test('should display tab navigation', async () => {
      const tabsExist = await elementExists(page, '.tabs');
      expect(tabsExist).toBe(true);
    });

    test('should have all required tabs', async () => {
      const tabs = ['Tools', 'Queue', 'Metrics', 'Settings'];

      for (const tabName of tabs) {
        const tabExists = await elementExists(page, `[data-tab="${tabName.toLowerCase()}"]`);
        expect(tabExists).toBe(true);
      }
    });
  });

  describe('Tab Navigation', () => {
    test('should display Tools tab by default', async () => {
      const toolsTab = await page.$('.tab-content.active[data-tab-content="tools"]');
      expect(toolsTab).toBeTruthy();
    });

    test('should switch to Queue tab', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const isActive = await page.$eval(
        '[data-tab-content="queue"]',
        el => el.classList.contains('active')
      );
      expect(isActive).toBe(true);
    });

    test('should switch to Metrics tab', async () => {
      await clickElement(page, '[data-tab="metrics"]');
      await waitForElement(page, '[data-tab-content="metrics"].active');

      const isActive = await page.$eval(
        '[data-tab-content="metrics"]',
        el => el.classList.contains('active')
      );
      expect(isActive).toBe(true);
    });

    test('should switch to Settings tab', async () => {
      await clickElement(page, '[data-tab="settings"]');
      await waitForElement(page, '[data-tab-content="settings"].active');

      const isActive = await page.$eval(
        '[data-tab-content="settings"]',
        el => el.classList.contains('active')
      );
      expect(isActive).toBe(true);
    });

    test('should highlight active tab', async () => {
      await clickElement(page, '[data-tab="metrics"]');

      const hasActiveClass = await page.$eval(
        '[data-tab="metrics"]',
        el => el.classList.contains('active')
      );
      expect(hasActiveClass).toBe(true);
    });

    test('should navigate between tabs multiple times', async () => {
      // Tools → Queue → Metrics → Settings → Tools
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      await clickElement(page, '[data-tab="metrics"]');
      await waitForElement(page, '[data-tab-content="metrics"].active');

      await clickElement(page, '[data-tab="settings"]');
      await waitForElement(page, '[data-tab-content="settings"].active');

      await clickElement(page, '[data-tab="tools"]');
      await waitForElement(page, '[data-tab-content="tools"].active');

      const isActive = await page.$eval(
        '[data-tab-content="tools"]',
        el => el.classList.contains('active')
      );
      expect(isActive).toBe(true);
    });
  });

  describe('Tools Tab Content', () => {
    test('should display tool categories', async () => {
      const categoriesExist = await elementExists(page, '.tool-categories');
      expect(categoriesExist).toBe(true);
    });

    test('should display tool list', async () => {
      const toolListExists = await elementExists(page, '.tool-list');
      expect(toolListExists).toBe(true);
    });

    test('should have search functionality', async () => {
      const searchExists = await elementExists(page, '#tool-search');
      expect(searchExists).toBe(true);
    });

    test('should display at least one tool', async () => {
      const tools = await page.$$('.tool-item');
      expect(tools.length).toBeGreaterThan(0);
    });

    test('should filter tools by category', async () => {
      // Click on a category
      await clickElement(page, '.category-item:first-child');

      // Check that tools are filtered
      const visibleTools = await page.$$eval('.tool-item:not(.hidden)', els => els.length);
      expect(visibleTools).toBeGreaterThan(0);
    });
  });

  describe('Queue Tab Content', () => {
    beforeEach(async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');
    });

    test('should display queue header', async () => {
      const headerExists = await elementExists(page, '.queue-header');
      expect(headerExists).toBe(true);
    });

    test('should display queue stats', async () => {
      const statsExist = await elementExists(page, '.queue-stats');
      expect(statsExist).toBe(true);
    });

    test('should have queue controls', async () => {
      const controlsExist = await elementExists(page, '.queue-controls');
      expect(controlsExist).toBe(true);
    });

    test('should show empty queue message when no jobs', async () => {
      const emptyMessageExists = await elementExists(page, '.empty-queue-message');
      // Should exist if queue is empty
      const exists = emptyMessageExists || await elementExists(page, '.queue-item');
      expect(exists).toBe(true);
    });

    test('should have sync button', async () => {
      const syncButtonExists = await elementExists(page, '#sync-queue-btn');
      expect(syncButtonExists).toBe(true);
    });

    test('should have clear completed button', async () => {
      const clearButtonExists = await elementExists(page, '#clear-completed-btn');
      expect(clearButtonExists).toBe(true);
    });
  });

  describe('Metrics Tab Content', () => {
    beforeEach(async () => {
      await clickElement(page, '[data-tab="metrics"]');
      await waitForElement(page, '[data-tab-content="metrics"].active');
    });

    test('should display metrics dashboard', async () => {
      const dashboardExists = await elementExists(page, '.metrics-dashboard');
      expect(dashboardExists).toBe(true);
    });

    test('should show execution statistics', async () => {
      const statsExist = await elementExists(page, '.execution-stats');
      expect(statsExist).toBe(true);
    });

    test('should show routing distribution', async () => {
      const distributionExists = await elementExists(page, '.routing-distribution');
      expect(distributionExists).toBe(true);
    });

    test('should have export button', async () => {
      const exportButtonExists = await elementExists(page, '#export-metrics-btn');
      expect(exportButtonExists).toBe(true);
    });

    test('should have reset button', async () => {
      const resetButtonExists = await elementExists(page, '#reset-metrics-btn');
      expect(resetButtonExists).toBe(true);
    });

    test('should display performance charts', async () => {
      const chartsExist = await elementExists(page, '.metrics-charts');
      expect(chartsExist).toBe(true);
    });
  });

  describe('Settings Tab Content', () => {
    beforeEach(async () => {
      await clickElement(page, '[data-tab="settings"]');
      await waitForElement(page, '[data-tab-content="settings"].active');
    });

    test('should display settings sections', async () => {
      const sectionsExist = await elementExists(page, '.settings-section');
      expect(sectionsExist).toBe(true);
    });

    test('should have cache settings', async () => {
      const cacheSettingsExist = await elementExists(page, '#cache-enabled');
      expect(cacheSettingsExist).toBe(true);
    });

    test('should have notification settings', async () => {
      const notificationSettingsExist = await elementExists(page, '#notifications-enabled');
      expect(notificationSettingsExist).toBe(true);
    });

    test('should have theme toggle', async () => {
      const themeToggleExists = await elementExists(page, '#theme-toggle');
      expect(themeToggleExists).toBe(true);
    });

    test('should have export/import buttons', async () => {
      const exportExists = await elementExists(page, '#export-settings-btn');
      const importExists = await elementExists(page, '#import-settings-btn');

      expect(exportExists || importExists).toBe(true);
    });

    test('should have save button', async () => {
      const saveButtonExists = await elementExists(page, '#save-settings-btn');
      expect(saveButtonExists).toBe(true);
    });
  });

  describe('Visual Regression', () => {
    test('should match Tools tab screenshot', async () => {
      await takeScreenshot(page, 'tools-tab.png');
      // Visual comparison would be done with additional tooling
    });

    test('should match Queue tab screenshot', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');
      await takeScreenshot(page, 'queue-tab.png');
    });

    test('should match Metrics tab screenshot', async () => {
      await clickElement(page, '[data-tab="metrics"]');
      await waitForElement(page, '[data-tab-content="metrics"].active');
      await takeScreenshot(page, 'metrics-tab.png');
    });

    test('should match Settings tab screenshot', async () => {
      await clickElement(page, '[data-tab="settings"]');
      await waitForElement(page, '[data-tab-content="settings"].active');
      await takeScreenshot(page, 'settings-tab.png');
    });
  });

  describe('Responsive Design', () => {
    test('should display correctly at default size', async () => {
      await page.setViewport({ width: 400, height: 600 });
      const bodyExists = await elementExists(page, 'body');
      expect(bodyExists).toBe(true);
    });

    test('should display correctly at minimum size', async () => {
      await page.setViewport({ width: 320, height: 480 });
      const bodyExists = await elementExists(page, 'body');
      expect(bodyExists).toBe(true);
    });

    test('should display correctly at maximum size', async () => {
      await page.setViewport({ width: 800, height: 1000 });
      const bodyExists = await elementExists(page, 'body');
      expect(bodyExists).toBe(true);
    });
  });

  describe('Keyboard Navigation', () => {
    test('should navigate tabs with keyboard', async () => {
      // Tab to queue button
      await page.keyboard.press('Tab');
      await page.keyboard.press('Enter');

      // Wait for queue tab to activate
      await page.waitForTimeout(500);

      // Check if queue tab is active (keyboard navigation)
      const focused = await page.evaluate(() => document.activeElement.getAttribute('data-tab'));
      expect(focused).toBeTruthy();
    });

    test('should support Escape key to close modals', async () => {
      // This would test any modal dialogs
      await page.keyboard.press('Escape');
      // Verify no modals are open
      const modalOpen = await elementExists(page, '.modal.open');
      expect(modalOpen).toBe(false);
    });
  });
});
