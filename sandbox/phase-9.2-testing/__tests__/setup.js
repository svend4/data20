/**
 * Jest Setup - Chrome Extension API Mocks
 * Phase 9.2 Testing
 */

// Mock Chrome extension API
global.chrome = {
  runtime: {
    sendMessage: jest.fn(),
    onMessage: {
      addListener: jest.fn(),
      removeListener: jest.fn()
    },
    getManifest: jest.fn(() => ({
      version: '1.0.0',
      name: 'Data20 Test'
    })),
    id: 'test-extension-id'
  },

  storage: {
    local: {
      get: jest.fn((keys, callback) => {
        if (typeof keys === 'function') {
          keys({});
        } else if (callback) {
          callback({});
        }
        return Promise.resolve({});
      }),
      set: jest.fn((items, callback) => {
        if (callback) callback();
        return Promise.resolve();
      }),
      remove: jest.fn((keys, callback) => {
        if (callback) callback();
        return Promise.resolve();
      }),
      clear: jest.fn((callback) => {
        if (callback) callback();
        return Promise.resolve();
      })
    },
    sync: {
      get: jest.fn(),
      set: jest.fn()
    }
  },

  notifications: {
    create: jest.fn((id, options, callback) => {
      if (callback) callback(id || 'notification-id');
      return Promise.resolve(id || 'notification-id');
    }),
    clear: jest.fn((id, callback) => {
      if (callback) callback(true);
      return Promise.resolve(true);
    }),
    onClicked: {
      addListener: jest.fn(),
      removeListener: jest.fn()
    },
    onButtonClicked: {
      addListener: jest.fn(),
      removeListener: jest.fn()
    },
    onClosed: {
      addListener: jest.fn(),
      removeListener: jest.fn()
    }
  },

  tabs: {
    query: jest.fn(),
    sendMessage: jest.fn(),
    create: jest.fn()
  },

  windows: {
    getCurrent: jest.fn()
  }
};

// Mock IndexedDB
const indexedDB = {
  open: jest.fn(() => ({
    onsuccess: null,
    onerror: null,
    onupgradeneeded: null
  })),
  deleteDatabase: jest.fn()
};

global.indexedDB = indexedDB;

// Mock performance API
global.performance = {
  now: jest.fn(() => Date.now()),
  memory: {
    usedJSHeapSize: 10000000,
    totalJSHeapSize: 20000000,
    jsHeapSizeLimit: 50000000
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
};

global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob())
  })
);

// Mock console methods for cleaner test output
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});
