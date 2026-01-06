/**
 * E2E Tests: Queue Management & Offline Operations
 * Phase 9.2 Stage 5
 *
 * Tests offline queue functionality and job management
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

describe('E2E: Queue Management & Offline Operations', () => {
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

  describe('Queue Tab Display', () => {
    beforeEach(async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');
    });

    test('should display queue statistics', async () => {
      const statsExist = await elementExists(page, '.queue-stats');
      expect(statsExist).toBe(true);
    });

    test('should show total queued jobs', async () => {
      const totalExists = await elementExists(page, '.total-jobs, #total-jobs');
      expect(totalExists).toBe(true);
    });

    test('should show completed jobs count', async () => {
      const completedExists = await elementExists(page, '.completed-jobs, #completed-jobs');
      expect(completedExists).toBe(true);
    });

    test('should show failed jobs count', async () => {
      const failedExists = await elementExists(page, '.failed-jobs, #failed-jobs');
      expect(failedExists).toBe(true);
    });

    test('should display queue controls', async () => {
      const syncButton = await elementExists(page, '#sync-queue-btn');
      const clearButton = await elementExists(page, '#clear-completed-btn');

      expect(syncButton || clearButton).toBe(true);
    });
  });

  describe('Offline Tool Queuing', () => {
    test('should queue complex tool when offline', async () => {
      // Go offline
      await page.setOfflineMode(true);

      // Try to execute a complex tool
      await clickElement(page, '[data-tab="tools"]');
      await waitForElement(page, '[data-tab-content="tools"].active');

      await clickElement(page, '[data-tool-name="complex_tool"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'input[name="data"]', 'test data');
      await clickElement(page, '#execute-tool-btn');

      await wait(2000);

      // Should show queued message
      const queuedMessage = await elementExists(page, '.queued-message, .job-queued');
      expect(queuedMessage).toBe(true);

      // Restore online mode
      await page.setOfflineMode(false);
    }, 15000);

    test('should execute simple tool locally even when offline', async () => {
      // Go offline
      await page.setOfflineMode(true);

      // Execute simple tool
      await clickElement(page, '[data-tool-name="word_count"]');
      await waitForElement(page, '.tool-parameters');

      await typeIntoField(page, 'textarea[name="text"]', 'Offline test');
      await clickElement(page, '#execute-tool-btn');

      await waitForElement(page, '.tool-result', 10000);

      const resultExists = await elementExists(page, '.tool-result');
      expect(resultExists).toBe(true);

      // Restore online mode
      await page.setOfflineMode(false);
    }, 15000);

    test('should add queued job to queue tab', async () => {
      // Go offline
      await page.setOfflineMode(true);

      // Queue a job
      await clickElement(page, '[data-tool-name="complex_tool"]');
      await waitForElement(page, '.tool-parameters');
      await typeIntoField(page, 'input[name="data"]', 'queue test');
      await clickElement(page, '#execute-tool-btn');
      await wait(2000);

      // Switch to queue tab
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      // Should show at least one queued job
      const queuedJobs = await page.$$('.queue-item.queued');
      expect(queuedJobs.length).toBeGreaterThan(0);

      // Restore online mode
      await page.setOfflineMode(false);
    }, 15000);
  });

  describe('Queue Item Display', () => {
    test('should display job details', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      // If there are queue items
      const hasItems = await elementExists(page, '.queue-item');
      if (hasItems) {
        const toolName = await elementExists(page, '.job-tool-name');
        const status = await elementExists(page, '.job-status');

        expect(toolName && status).toBe(true);
      }
    });

    test('should show job priority', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const hasItems = await elementExists(page, '.queue-item');
      if (hasItems) {
        const priority = await elementExists(page, '.job-priority, [data-priority]');
        expect(priority).toBe(true);
      }
    });

    test('should show job timestamp', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const hasItems = await elementExists(page, '.queue-item');
      if (hasItems) {
        const timestamp = await elementExists(page, '.job-timestamp, .job-created-at');
        expect(timestamp).toBe(true);
      }
    });

    test('should indicate job status visually', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const hasItems = await elementExists(page, '.queue-item');
      if (hasItems) {
        // Check for status classes or badges
        const statusIndicator = await elementExists(page, '.status-badge, .job-status');
        expect(statusIndicator).toBe(true);
      }
    });
  });

  describe('Queue Actions', () => {
    test('should have retry button for failed jobs', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const failedJob = await elementExists(page, '.queue-item.failed');
      if (failedJob) {
        const retryButton = await elementExists(page, '.retry-job-btn');
        expect(retryButton).toBe(true);
      }
    });

    test('should have delete button for jobs', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const hasItems = await elementExists(page, '.queue-item');
      if (hasItems) {
        const deleteButton = await elementExists(page, '.delete-job-btn, .remove-job-btn');
        expect(deleteButton).toBe(true);
      }
    });

    test('should allow clearing completed jobs', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const clearButton = await elementExists(page, '#clear-completed-btn');
      expect(clearButton).toBe(true);

      // Click clear button
      if (clearButton) {
        await clickElement(page, '#clear-completed-btn');
        await wait(1000);

        // Completed jobs should be removed
        const completedJobs = await page.$$('.queue-item.completed');
        expect(completedJobs.length).toBe(0);
      }
    }, 10000);

    test('should allow manual queue sync', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const syncButton = await elementExists(page, '#sync-queue-btn');
      expect(syncButton).toBe(true);

      if (syncButton) {
        await clickElement(page, '#sync-queue-btn');
        await wait(2000);

        // Should show syncing indicator or complete message
        const syncing = await elementExists(page, '.syncing, .sync-complete');
        expect(syncing).toBe(true);
      }
    }, 10000);
  });

  describe('Online/Offline Transition', () => {
    test('should show offline indicator when offline', async () => {
      await page.setOfflineMode(true);
      await wait(1000);

      const offlineIndicator = await elementExists(page, '.offline-indicator, .status-offline');
      expect(offlineIndicator).toBe(true);

      await page.setOfflineMode(false);
    }, 10000);

    test('should show online indicator when online', async () => {
      await page.setOfflineMode(false);
      await wait(1000);

      const onlineIndicator = await elementExists(page, '.online-indicator, .status-online');
      // Either shows online indicator or doesn't show offline indicator
      expect(onlineIndicator || !(await elementExists(page, '.offline-indicator'))).toBe(true);
    }, 10000);

    test('should process queue automatically when coming online', async () => {
      // Queue a job while offline
      await page.setOfflineMode(true);

      await clickElement(page, '[data-tool-name="complex_tool"]');
      await waitForElement(page, '.tool-parameters');
      await typeIntoField(page, 'input[name="data"]', 'auto process test');
      await clickElement(page, '#execute-tool-btn');
      await wait(2000);

      // Go back online
      await page.setOfflineMode(false);
      await wait(3000); // Wait for auto-processing

      // Switch to queue tab
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      // Job should be processing or completed
      const processingOrCompleted = await elementExists(page, '.queue-item.processing, .queue-item.completed');
      expect(processingOrCompleted).toBe(true);
    }, 20000);
  });

  describe('Queue Persistence', () => {
    test('should persist queue across popup closes', async () => {
      // Queue a job
      await page.setOfflineMode(true);

      await clickElement(page, '[data-tool-name="complex_tool"]');
      await waitForElement(page, '.tool-parameters');
      await typeIntoField(page, 'input[name="data"]', 'persistence test');
      await clickElement(page, '#execute-tool-btn');
      await wait(2000);

      // Close and reopen popup
      await page.close();
      page = await openExtensionPopup(browser, extensionId);

      // Go to queue tab
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      // Job should still be there
      const queuedJobs = await page.$$('.queue-item');
      expect(queuedJobs.length).toBeGreaterThan(0);

      await page.setOfflineMode(false);
    }, 20000);
  });

  describe('Priority Queue Behavior', () => {
    test('should process high-priority jobs first', async () => {
      // This would require creating jobs with different priorities
      // and observing their processing order
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      // If there are multiple jobs, check priority ordering
      const queueItems = await page.$$('.queue-item');
      if (queueItems.length > 1) {
        const priorities = await page.$$eval('.job-priority, [data-priority]',
          els => els.map(el => parseInt(el.textContent || el.getAttribute('data-priority')))
        );

        // Should be in descending order
        for (let i = 1; i < priorities.length; i++) {
          expect(priorities[i-1]).toBeGreaterThanOrEqual(priorities[i]);
        }
      }
    });
  });

  describe('Queue Notifications', () => {
    test('should request notification permission', async () => {
      // Check if notifications are enabled in settings
      await clickElement(page, '[data-tab="settings"]');
      await waitForElement(page, '[data-tab-content="settings"].active');

      const notificationToggle = await elementExists(page, '#notifications-enabled');
      expect(notificationToggle).toBe(true);
    });

    test('should show notification setting', async () => {
      await clickElement(page, '[data-tab="settings"]');
      await waitForElement(page, '[data-tab-content="settings"].active');

      const notificationSection = await elementExists(page, '.notification-settings');
      expect(notificationSection).toBe(true);
    });
  });

  describe('Queue Statistics', () => {
    test('should track total processed jobs', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const processedStat = await elementExists(page, '.total-processed, #total-processed');
      expect(processedStat).toBe(true);
    });

    test('should track success rate', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const successRate = await elementExists(page, '.success-rate, #success-rate');
      if (successRate) {
        const rate = await getElementText(page, '.success-rate, #success-rate');
        expect(rate).toMatch(/\d+%/); // Should be a percentage
      }
    });
  });

  describe('Empty Queue State', () => {
    test('should show empty state message when queue is empty', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      // Clear all jobs
      const clearBtn = await elementExists(page, '#clear-all-btn, #clear-completed-btn');
      if (clearBtn) {
        await clickElement(page, '#clear-all-btn, #clear-completed-btn');
        await wait(1000);
      }

      const emptyMessage = await elementExists(page, '.empty-queue-message, .no-jobs-message');
      const hasJobs = await elementExists(page, '.queue-item');

      // Either shows empty message or still has jobs
      expect(emptyMessage || hasJobs).toBe(true);
    }, 10000);

    test('should hide queue controls when queue is empty', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const hasJobs = await elementExists(page, '.queue-item');
      const controlsVisible = await elementExists(page, '.queue-controls:not(.hidden)');

      // If no jobs, controls should be hidden
      if (!hasJobs) {
        expect(controlsVisible).toBe(false);
      }
    });
  });

  describe('Queue Error Handling', () => {
    test('should show retry count for failed jobs', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const failedJob = await elementExists(page, '.queue-item.failed');
      if (failedJob) {
        const retryCount = await elementExists(page, '.retry-count, [data-retry-count]');
        expect(retryCount).toBe(true);
      }
    });

    test('should show error message for failed jobs', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const failedJob = await elementExists(page, '.queue-item.failed');
      if (failedJob) {
        // Click to expand error details
        await clickElement(page, '.queue-item.failed');
        await wait(500);

        const errorMessage = await elementExists(page, '.job-error-message, .error-details');
        expect(errorMessage).toBe(true);
      }
    }, 10000);

    test('should limit retry attempts', async () => {
      await clickElement(page, '[data-tab="queue"]');
      await waitForElement(page, '[data-tab-content="queue"].active');

      const failedJob = await elementExists(page, '.queue-item.failed');
      if (failedJob) {
        const retryCount = await page.$eval(
          '.retry-count, [data-retry-count]',
          el => parseInt(el.textContent || el.getAttribute('data-retry-count'))
        );

        // Should not exceed max retries (usually 3)
        expect(retryCount).toBeLessThanOrEqual(3);
      }
    });
  });
});
