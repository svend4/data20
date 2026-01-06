# E2E Tests with Puppeteer

End-to-end testing suite for the Data20 Browser Extension using Puppeteer.

## Overview

These tests run the extension in a real Chrome browser instance and test actual user workflows.

## Test Files

1. **popup-navigation.test.js** (350+ lines, 50+ tests)
   - Popup opening and initialization
   - Tab navigation (Tools, Queue, Metrics, Settings)
   - Tab content verification
   - Keyboard navigation
   - Visual regression tests
   - Responsive design tests

2. **tool-execution.test.js** (400+ lines, 40+ tests)
   - Tool selection and filtering
   - Parameter entry and validation
   - Simple tool execution
   - Medium tool execution
   - Cache behavior
   - Error handling
   - Tool history
   - Result display and formatting

3. **queue-offline.test.js** (450+ lines, 35+ tests)
   - Queue tab display and statistics
   - Offline tool queuing
   - Queue item display
   - Queue actions (retry, delete, clear)
   - Online/offline transitions
   - Queue persistence
   - Priority queue behavior
   - Queue notifications
   - Error handling

## Prerequisites

```bash
npm install
npm run build  # Build the extension first
```

## Running E2E Tests

### Run all E2E tests:
```bash
npm run test:e2e
```

### Run specific test file:
```bash
npx jest __tests__/e2e/popup-navigation.test.js
npx jest __tests__/e2e/tool-execution.test.js
npx jest __tests__/e2e/queue-offline.test.js
```

### Run with coverage:
```bash
npx jest __tests__/e2e --coverage
```

## Configuration

E2E tests require:
- Built extension in `dist/` directory
- Chrome/Chromium browser installed
- Puppeteer configured for extension testing

## Test Environment

- **Browser**: Chrome (headless: false - extensions require visible browser)
- **Viewport**: 400x600 (default popup size)
- **Timeout**: Extended timeouts (30s for browser launch, 10-20s for tests)

## Helper Functions

The `helpers/extension-helper.js` provides utilities:

### Browser Management
- `launchBrowserWithExtension()` - Launch Chrome with extension loaded
- `getExtensionId()` - Get extension ID from chrome://extensions
- `openExtensionPopup()` - Open extension popup page
- `cleanupBrowser()` - Close browser instance

### Element Interaction
- `waitForElement(page, selector, timeout)` - Wait for element to appear
- `clickElement(page, selector)` - Click element
- `typeIntoField(page, selector, text)` - Type into input field
- `getElementText(page, selector)` - Get element text content
- `elementExists(page, selector)` - Check if element exists
- `isElementVisible(page, selector)` - Check if element is visible

### Navigation & State
- `waitForNavigation(page)` - Wait for page navigation
- `waitForCondition(page, fn, timeout)` - Wait for custom condition
- `wait(ms)` - Wait for milliseconds

### Storage & State
- `setLocalStorage(page, key, value)` - Set localStorage item
- `getLocalStorage(page, key)` - Get localStorage item
- `clearLocalStorage(page)` - Clear all localStorage
- `mockChromeStorage(page, data)` - Mock chrome.storage API

### Debugging
- `takeScreenshot(page, filename)` - Take screenshot
- `getComputedStyle(page, selector, property)` - Get computed CSS

## Writing New Tests

### Basic Test Structure:

```javascript
import {
  launchBrowserWithExtension,
  getExtensionId,
  openExtensionPopup,
  clickElement,
  waitForElement,
  cleanupBrowser
} from './helpers/extension-helper.js';

describe('E2E: Feature Name', () => {
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

  test('should perform action', async () => {
    await waitForElement(page, '.some-element');
    await clickElement(page, '.button');

    const result = await elementExists(page, '.result');
    expect(result).toBe(true);
  }, 15000);
});
```

### Important Notes:

1. **Timeouts**: Extension loading is slow, use generous timeouts
2. **Headless**: Extensions don't work in headless mode (`headless: false`)
3. **Build First**: Always build extension before running E2E tests
4. **Cleanup**: Always close browser in `afterAll` to prevent resource leaks
5. **Screenshots**: Use for debugging failing tests
6. **Async/Await**: All Puppeteer operations are async

## Debugging

### Take screenshots during tests:
```javascript
await takeScreenshot(page, 'debug-screenshot.png');
```

### Slow down execution:
```javascript
const browser = await puppeteer.launch({
  headless: false,
  slowMo: 100  // Slow down by 100ms
});
```

### View console logs:
```javascript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

### View errors:
```javascript
page.on('pageerror', error => console.log('PAGE ERROR:', error));
```

## Common Issues

### Extension not loading
- Ensure `dist/` directory exists and contains built extension
- Check `manifest.json` is valid
- Verify extension path in `launchBrowserWithExtension()`

### Tests timing out
- Increase timeout in test: `test('...', async () => {...}, 30000)`
- Check if element selectors are correct
- Ensure extension is fully loaded before testing

### Element not found
- Use `waitForElement()` before interacting
- Check element selector (use browser DevTools)
- Verify element is visible (not hidden or display:none)

## Coverage Goals

- **Popup Navigation**: 90%+ coverage
- **Tool Execution**: 85%+ coverage
- **Queue Operations**: 85%+ coverage
- **Overall E2E**: 85%+ coverage

## CI/CD Integration

For CI/CD pipelines:

```yaml
# .github/workflows/e2e-tests.yml
- name: Run E2E Tests
  run: |
    npm run build
    npm run test:e2e
```

Note: Use `xvfb` for headless environments:

```bash
xvfb-run --auto-servernum npm run test:e2e
```

## Future Enhancements

- Visual regression testing with screenshot comparison
- Performance metrics collection
- Cross-browser testing (Firefox, Edge)
- Parallel test execution
- Video recording of test runs
- Accessibility testing (a11y)

---

**Version**: 1.0
**Last Updated**: 2026-01-06
**Test Coverage**: 125+ test cases across 3 test suites
