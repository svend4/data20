/**
 * E2E Test Helper - Extension Setup with Puppeteer
 * Phase 9.2 Stage 5
 */

import puppeteer from 'puppeteer';
import path from 'path';

/**
 * Launch Chrome with extension loaded
 */
export async function launchBrowserWithExtension() {
  const extensionPath = path.resolve(__dirname, '../../../dist');

  const browser = await puppeteer.launch({
    headless: false, // Extensions don't work in headless mode
    args: [
      `--disable-extensions-except=${extensionPath}`,
      `--load-extension=${extensionPath}`,
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-web-security'
    ]
  });

  return browser;
}

/**
 * Get extension ID from chrome://extensions page
 */
export async function getExtensionId(browser) {
  const page = await browser.newPage();
  await page.goto('chrome://extensions');

  // Enable developer mode to see extension IDs
  await page.evaluate(() => {
    const devModeToggle = document.querySelector('extensions-manager')
      .shadowRoot.querySelector('extensions-toolbar')
      .shadowRoot.querySelector('#devMode');
    if (!devModeToggle.checked) {
      devModeToggle.click();
    }
  });

  // Get extension ID
  const extensionId = await page.evaluate(() => {
    const extensionItems = document.querySelector('extensions-manager')
      .shadowRoot.querySelector('extensions-item-list')
      .shadowRoot.querySelectorAll('extensions-item');

    for (const item of extensionItems) {
      const name = item.shadowRoot.querySelector('#name').textContent;
      if (name.includes('Data20')) {
        return item.id;
      }
    }
    return null;
  });

  await page.close();
  return extensionId;
}

/**
 * Open extension popup
 */
export async function openExtensionPopup(browser, extensionId) {
  const popupUrl = `chrome-extension://${extensionId}/popup.html`;
  const page = await browser.newPage();
  await page.goto(popupUrl);
  await page.waitForSelector('body');
  return page;
}

/**
 * Wait for element to be visible
 */
export async function waitForElement(page, selector, timeout = 5000) {
  await page.waitForSelector(selector, { visible: true, timeout });
}

/**
 * Click element
 */
export async function clickElement(page, selector) {
  await page.waitForSelector(selector);
  await page.click(selector);
}

/**
 * Type into input field
 */
export async function typeIntoField(page, selector, text) {
  await page.waitForSelector(selector);
  await page.type(selector, text);
}

/**
 * Get text content of element
 */
export async function getElementText(page, selector) {
  await page.waitForSelector(selector);
  return await page.$eval(selector, el => el.textContent);
}

/**
 * Check if element exists
 */
export async function elementExists(page, selector) {
  try {
    await page.waitForSelector(selector, { timeout: 1000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Take screenshot
 */
export async function takeScreenshot(page, filename) {
  await page.screenshot({
    path: `__tests__/e2e/screenshots/${filename}`,
    fullPage: true
  });
}

/**
 * Wait for navigation
 */
export async function waitForNavigation(page) {
  await page.waitForNavigation({ waitUntil: 'networkidle0' });
}

/**
 * Get all tabs
 */
export async function getAllTabs(browser) {
  return await browser.pages();
}

/**
 * Close all tabs except first
 */
export async function closeAllTabsExceptFirst(browser) {
  const pages = await browser.pages();
  for (let i = 1; i < pages.length; i++) {
    await pages[i].close();
  }
}

/**
 * Wait for milliseconds
 */
export async function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Get computed style of element
 */
export async function getComputedStyle(page, selector, property) {
  return await page.$eval(selector, (el, prop) => {
    return window.getComputedStyle(el).getPropertyValue(prop);
  }, property);
}

/**
 * Check if element is visible
 */
export async function isElementVisible(page, selector) {
  try {
    const element = await page.$(selector);
    if (!element) return false;

    const isVisible = await element.evaluate(el => {
      const style = window.getComputedStyle(el);
      return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    });

    return isVisible;
  } catch {
    return false;
  }
}

/**
 * Get element attribute
 */
export async function getElementAttribute(page, selector, attribute) {
  return await page.$eval(selector, (el, attr) => el.getAttribute(attr), attribute);
}

/**
 * Set local storage item
 */
export async function setLocalStorage(page, key, value) {
  await page.evaluate((k, v) => {
    localStorage.setItem(k, JSON.stringify(v));
  }, key, value);
}

/**
 * Get local storage item
 */
export async function getLocalStorage(page, key) {
  return await page.evaluate((k) => {
    const value = localStorage.getItem(k);
    return value ? JSON.parse(value) : null;
  }, key);
}

/**
 * Clear local storage
 */
export async function clearLocalStorage(page) {
  await page.evaluate(() => localStorage.clear());
}

/**
 * Mock chrome.storage API
 */
export async function mockChromeStorage(page, initialData = {}) {
  await page.evaluateOnNewDocument((data) => {
    const storage = data;

    window.chrome = {
      storage: {
        local: {
          get: (keys, callback) => {
            const result = {};
            if (Array.isArray(keys)) {
              keys.forEach(key => {
                if (storage[key]) result[key] = storage[key];
              });
            } else if (typeof keys === 'string') {
              if (storage[keys]) result[keys] = storage[keys];
            }
            callback(result);
          },
          set: (items, callback) => {
            Object.assign(storage, items);
            if (callback) callback();
          }
        }
      }
    };
  }, initialData);
}

/**
 * Wait for condition
 */
export async function waitForCondition(page, conditionFn, timeout = 5000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const result = await page.evaluate(conditionFn);
    if (result) return true;
    await wait(100);
  }

  throw new Error('Condition not met within timeout');
}

/**
 * Clean up browser instance
 */
export async function cleanupBrowser(browser) {
  if (browser) {
    await browser.close();
  }
}
