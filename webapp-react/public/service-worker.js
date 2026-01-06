/**
 * Service Worker for Data20 Knowledge Base PWA
 * Phase 8.1.4: Service Worker Integration with IndexedDB
 *
 * Enhanced service worker with:
 * - Static asset caching (app shell)
 * - API response caching with network-first strategy
 * - IndexedDB integration for offline queue
 * - Background Sync API for automatic retry
 * - Periodic background sync for data updates
 * - Two-way communication with main app
 */

const CACHE_VERSION = 'v2.0.0'; // Updated for Phase 8.1
const CACHE_NAME = `data20-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline.html';

// Database configuration
const DB_NAME = 'data20-offline-db';
const DB_VERSION = 1;
const STORES = {
  TOOLS: 'tools',
  JOBS: 'jobs',
  OFFLINE_QUEUE: 'offlineQueue',
  CACHE: 'cache',
  PREFERENCES: 'preferences',
};

// Queue statuses
const QUEUE_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

// Queue types
const QUEUE_TYPES = {
  EXECUTE_TOOL: 'execute_tool',
  UPDATE_JOB: 'update_job',
  DELETE_JOB: 'delete_job',
  CACHE_TOOL: 'cache_tool',
  CUSTOM: 'custom',
};

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
  '/manifest.json',
];

// API endpoints that can be cached
const CACHEABLE_API_PATTERNS = [
  /\/api\/tools$/,           // Tools list
  /\/api\/tools\/[^/]+$/,    // Tool details
];

// API endpoints that should never be cached
const NO_CACHE_API_PATTERNS = [
  /\/auth\//,                // Auth endpoints
  /\/api\/run$/,             // Tool execution
  /\/api\/jobs$/,            // Job creation (POST)
];

// ========================================
// IndexedDB Helper Functions
// ========================================

/**
 * Open IndexedDB database
 */
async function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Create stores if they don't exist
      if (!db.objectStoreNames.contains(STORES.TOOLS)) {
        const toolsStore = db.createObjectStore(STORES.TOOLS, { keyPath: 'name' });
        toolsStore.createIndex('category', 'category', { unique: false });
        toolsStore.createIndex('updatedAt', 'updatedAt', { unique: false });
      }

      if (!db.objectStoreNames.contains(STORES.JOBS)) {
        const jobsStore = db.createObjectStore(STORES.JOBS, { keyPath: 'id' });
        jobsStore.createIndex('status', 'status', { unique: false });
        jobsStore.createIndex('toolName', 'toolName', { unique: false });
        jobsStore.createIndex('createdAt', 'createdAt', { unique: false });
      }

      if (!db.objectStoreNames.contains(STORES.OFFLINE_QUEUE)) {
        const queueStore = db.createObjectStore(STORES.OFFLINE_QUEUE, {
          keyPath: 'id',
          autoIncrement: true,
        });
        queueStore.createIndex('type', 'type', { unique: false });
        queueStore.createIndex('status', 'status', { unique: false });
        queueStore.createIndex('priority', 'priority', { unique: false });
        queueStore.createIndex('createdAt', 'createdAt', { unique: false });
      }

      if (!db.objectStoreNames.contains(STORES.CACHE)) {
        db.createObjectStore(STORES.CACHE, { keyPath: 'key' });
      }

      if (!db.objectStoreNames.contains(STORES.PREFERENCES)) {
        db.createObjectStore(STORES.PREFERENCES, { keyPath: 'key' });
      }
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(new Error(`Failed to open database: ${request.error}`));
    };
  });
}

/**
 * Get all items from a store by index
 */
async function getAllByIndex(storeName, indexName, indexValue) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const index = store.index(indexName);
    const request = index.getAll(indexValue);

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Get all items from a store
 */
async function getAllFromStore(storeName) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Get single item from store
 */
async function getFromStore(storeName, key) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.get(key);

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Put item to store
 */
async function putToStore(storeName, value) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.put(value);

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Delete item from store
 */
async function deleteFromStore(storeName, key) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(key);

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Get pending queue items
 */
async function getPendingQueueItems() {
  return getAllByIndex(STORES.OFFLINE_QUEUE, 'status', QUEUE_STATUS.PENDING);
}

/**
 * Update queue item status
 */
async function updateQueueItemStatus(id, status, error = null) {
  const item = await getFromStore(STORES.OFFLINE_QUEUE, id);
  if (!item) {
    return;
  }

  item.status = status;
  item.updatedAt = Date.now();

  if (status === QUEUE_STATUS.COMPLETED) {
    item.completedAt = Date.now();
  }

  if (status === QUEUE_STATUS.FAILED || status === QUEUE_STATUS.PENDING) {
    item.retries = (item.retries || 0) + 1;
    if (error) {
      item.error = error;
    }
  }

  await putToStore(STORES.OFFLINE_QUEUE, item);
}

// ========================================
// Service Worker Lifecycle Events
// ========================================

/**
 * Install event - precache essential assets
 */
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing v2.0.0 (Phase 8.1.4)...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Precaching app shell');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => {
        console.log('[Service Worker] Installed successfully');
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Precaching failed:', error);
      })
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating v2.0.0...');

  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Take control of all clients immediately
      self.clients.claim(),
    ])
      .then(() => {
        console.log('[Service Worker] Activated successfully');
        // Notify clients about activation
        notifyClients({ type: 'SW_ACTIVATED', version: CACHE_VERSION });
      })
  );
});

/**
 * Fetch event - implement caching strategies
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle requests from the same origin
  if (url.origin !== location.origin) {
    return;
  }

  // Handle different types of requests
  if (isAPIRequest(url)) {
    event.respondWith(handleAPIRequest(request, url));
  } else if (isNavigationRequest(request)) {
    event.respondWith(handleNavigationRequest(request));
  } else {
    event.respondWith(handleStaticAssetRequest(request));
  }
});

// ========================================
// Request Handlers
// ========================================

/**
 * Check if request is an API request
 */
function isAPIRequest(url) {
  return url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/');
}

/**
 * Check if request is a navigation request
 */
function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

/**
 * Check if API request should be cached
 */
function shouldCacheAPI(url) {
  // Don't cache if matches no-cache patterns
  if (NO_CACHE_API_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return false;
  }

  // Cache if matches cacheable patterns
  if (CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return true;
  }

  return false;
}

/**
 * Handle API requests - Network First strategy with IndexedDB fallback
 */
async function handleAPIRequest(request, url) {
  const cacheable = shouldCacheAPI(url);

  try {
    // Try network first
    const networkResponse = await fetch(request);

    // Cache successful responses if cacheable
    if (cacheable && networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());

      // Also cache to IndexedDB for tools and jobs
      if (url.pathname === '/api/tools' && request.method === 'GET') {
        const data = await networkResponse.clone().json();
        await cacheToolsToIndexedDB(data);
      }
    }

    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Network request failed, trying cache:', url.pathname);

    // Try Cache API first
    if (cacheable) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('[Service Worker] Serving from Cache API:', url.pathname);
        return cachedResponse;
      }
    }

    // Try IndexedDB for tools
    if (url.pathname === '/api/tools') {
      const tools = await getAllFromStore(STORES.TOOLS);
      if (tools && tools.length > 0) {
        console.log('[Service Worker] Serving from IndexedDB:', url.pathname);
        return new Response(JSON.stringify(tools), {
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    // Return offline response for failed API requests
    return new Response(
      JSON.stringify({
        error: 'offline',
        message: 'You are currently offline. Please check your internet connection.',
        cached: false,
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

/**
 * Cache tools data to IndexedDB
 */
async function cacheToolsToIndexedDB(tools) {
  try {
    if (!Array.isArray(tools)) {
      return;
    }

    const db = await openDatabase();
    const transaction = db.transaction(STORES.TOOLS, 'readwrite');
    const store = transaction.objectStore(STORES.TOOLS);

    for (const tool of tools) {
      const toolWithTimestamp = {
        ...tool,
        cachedAt: Date.now(),
        updatedAt: tool.updatedAt || Date.now(),
      };
      store.put(toolWithTimestamp);
    }

    console.log(`[Service Worker] Cached ${tools.length} tools to IndexedDB`);
  } catch (error) {
    console.error('[Service Worker] Failed to cache tools to IndexedDB:', error);
  }
}

/**
 * Handle navigation requests - Cache First with network fallback
 */
async function handleNavigationRequest(request) {
  try {
    // Try network first for HTML pages
    const networkResponse = await fetch(request);

    // Cache the response
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, networkResponse.clone());

    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Navigation request failed, trying cache');

    // Try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page as last resort
    const offlineResponse = await caches.match(OFFLINE_URL);
    if (offlineResponse) {
      return offlineResponse;
    }

    // Fallback offline HTML
    return new Response(
      `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Offline - Data20 Knowledge Base</title>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
              display: flex;
              align-items: center;
              justify-content: center;
              height: 100vh;
              margin: 0;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white;
            }
            .container {
              text-align: center;
              padding: 2rem;
            }
            h1 { font-size: 2.5rem; margin: 0 0 1rem 0; }
            p { font-size: 1.2rem; opacity: 0.9; margin: 0.5rem 0; }
            .retry-btn {
              margin-top: 2rem;
              padding: 1rem 2rem;
              font-size: 1rem;
              background: white;
              color: #764ba2;
              border: none;
              border-radius: 0.5rem;
              cursor: pointer;
              font-weight: 600;
            }
            .retry-btn:hover {
              opacity: 0.9;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>📡 You're Offline</h1>
            <p>Please check your internet connection and try again.</p>
            <p>Some features may still be available offline.</p>
            <button class="retry-btn" onclick="location.reload()">Retry</button>
          </div>
        </body>
      </html>
      `,
      {
        headers: { 'Content-Type': 'text/html' },
      }
    );
  }
}

/**
 * Handle static assets - Cache First strategy
 */
async function handleStaticAssetRequest(request) {
  // Try cache first
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    // Fetch from network
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Static asset request failed:', request.url);

    // Return a fallback response for images
    if (request.destination === 'image') {
      return new Response(
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect fill="#ddd" width="200" height="200"/><text x="50%" y="50%" text-anchor="middle" fill="#999" dy=".3em">Offline</text></svg>',
        { headers: { 'Content-Type': 'image/svg+xml' } }
      );
    }

    return new Response('Not available offline', {
      status: 503,
      statusText: 'Service Unavailable',
    });
  }
}

// ========================================
// Background Sync Event
// ========================================

/**
 * Background Sync event - retry failed requests
 */
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);

  if (event.tag === 'sync-queue') {
    event.waitUntil(syncOfflineQueue());
  }

  if (event.tag === 'sync-tools') {
    event.waitUntil(syncTools());
  }

  if (event.tag === 'sync-jobs') {
    event.waitUntil(syncJobs());
  }
});

/**
 * Sync offline queue - process pending items
 */
async function syncOfflineQueue() {
  try {
    console.log('[Service Worker] Starting offline queue sync...');

    const pendingItems = await getPendingQueueItems();

    if (pendingItems.length === 0) {
      console.log('[Service Worker] No pending items in queue');
      return;
    }

    console.log(`[Service Worker] Processing ${pendingItems.length} pending items`);

    let completed = 0;
    let failed = 0;

    for (const item of pendingItems) {
      try {
        await updateQueueItemStatus(item.id, QUEUE_STATUS.PROCESSING);

        let result;
        switch (item.type) {
          case QUEUE_TYPES.EXECUTE_TOOL:
            result = await executeToolOperation(item);
            break;
          case QUEUE_TYPES.UPDATE_JOB:
            result = await updateJobOperation(item);
            break;
          case QUEUE_TYPES.DELETE_JOB:
            result = await deleteJobOperation(item);
            break;
          default:
            throw new Error(`Unknown queue type: ${item.type}`);
        }

        await updateQueueItemStatus(item.id, QUEUE_STATUS.COMPLETED);
        completed++;

        console.log(`[Service Worker] Queue item ${item.id} completed`);
      } catch (error) {
        console.error(`[Service Worker] Queue item ${item.id} failed:`, error);

        const shouldRetry = (item.retries || 0) < (item.maxRetries || 3);
        if (shouldRetry) {
          await updateQueueItemStatus(item.id, QUEUE_STATUS.PENDING, error.message);
        } else {
          await updateQueueItemStatus(item.id, QUEUE_STATUS.FAILED, error.message);
        }

        failed++;
      }
    }

    console.log(`[Service Worker] Queue sync completed: ${completed} succeeded, ${failed} failed`);

    // Notify clients about sync completion
    notifyClients({
      type: 'QUEUE_SYNC_COMPLETED',
      completed,
      failed,
    });
  } catch (error) {
    console.error('[Service Worker] Queue sync failed:', error);
    throw error;
  }
}

/**
 * Execute tool operation from queue
 */
async function executeToolOperation(item) {
  const { toolName, parameters } = item.data;

  const response = await fetch('/api/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tool_name: toolName,
      parameters: parameters || {},
    }),
  });

  if (!response.ok) {
    throw new Error(`Tool execution failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update job operation from queue
 */
async function updateJobOperation(item) {
  const { jobId, updates } = item.data;

  const response = await fetch(`/api/jobs/${jobId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Job update failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete job operation from queue
 */
async function deleteJobOperation(item) {
  const { jobId } = item.data;

  const response = await fetch(`/api/jobs/${jobId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Job deletion failed: ${response.statusText}`);
  }

  return { deleted: true };
}

/**
 * Sync tools from API to IndexedDB
 */
async function syncTools() {
  try {
    console.log('[Service Worker] Syncing tools...');

    const response = await fetch('/api/tools');
    if (!response.ok) {
      throw new Error(`Failed to fetch tools: ${response.statusText}`);
    }

    const tools = await response.json();
    await cacheToolsToIndexedDB(tools);

    console.log('[Service Worker] Tools synced successfully');

    notifyClients({
      type: 'TOOLS_SYNCED',
      count: tools.length,
    });
  } catch (error) {
    console.error('[Service Worker] Tools sync failed:', error);
    throw error;
  }
}

/**
 * Sync jobs from API to IndexedDB
 */
async function syncJobs() {
  try {
    console.log('[Service Worker] Syncing jobs...');

    const response = await fetch('/api/jobs');
    if (!response.ok) {
      throw new Error(`Failed to fetch jobs: ${response.statusText}`);
    }

    const jobs = await response.json();

    const db = await openDatabase();
    const transaction = db.transaction(STORES.JOBS, 'readwrite');
    const store = transaction.objectStore(STORES.JOBS);

    for (const job of jobs) {
      store.put(job);
    }

    console.log('[Service Worker] Jobs synced successfully');

    notifyClients({
      type: 'JOBS_SYNCED',
      count: jobs.length,
    });
  } catch (error) {
    console.error('[Service Worker] Jobs sync failed:', error);
    throw error;
  }
}

// ========================================
// Periodic Background Sync (Chrome 80+)
// ========================================

/**
 * Periodic sync event - update data in background
 */
self.addEventListener('periodicsync', (event) => {
  console.log('[Service Worker] Periodic sync:', event.tag);

  if (event.tag === 'sync-data') {
    event.waitUntil(periodicDataSync());
  }
});

/**
 * Periodic data sync - update tools and jobs
 */
async function periodicDataSync() {
  try {
    console.log('[Service Worker] Starting periodic data sync...');

    await Promise.all([
      syncTools(),
      syncJobs(),
    ]);

    console.log('[Service Worker] Periodic data sync completed');
  } catch (error) {
    console.error('[Service Worker] Periodic data sync failed:', error);
  }
}

// ========================================
// Message Event - Communication with App
// ========================================

/**
 * Message event - handle messages from clients
 */
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);

  const { type, data } = event.data || {};

  if (type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (type === 'CACHE_URLS') {
    const urls = data?.urls || [];
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then((cache) => cache.addAll(urls))
        .then(() => {
          event.ports[0]?.postMessage({ success: true });
        })
    );
  }

  if (type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys()
        .then((cacheNames) => Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        ))
        .then(() => {
          event.ports[0]?.postMessage({ success: true });
        })
    );
  }

  if (type === 'SYNC_QUEUE') {
    event.waitUntil(
      syncOfflineQueue()
        .then(() => {
          event.ports[0]?.postMessage({ success: true });
        })
        .catch((error) => {
          event.ports[0]?.postMessage({ success: false, error: error.message });
        })
    );
  }

  if (type === 'SYNC_TOOLS') {
    event.waitUntil(
      syncTools()
        .then(() => {
          event.ports[0]?.postMessage({ success: true });
        })
        .catch((error) => {
          event.ports[0]?.postMessage({ success: false, error: error.message });
        })
    );
  }

  if (type === 'SYNC_JOBS') {
    event.waitUntil(
      syncJobs()
        .then(() => {
          event.ports[0]?.postMessage({ success: true });
        })
        .catch((error) => {
          event.ports[0]?.postMessage({ success: false, error: error.message });
        })
    );
  }

  if (type === 'GET_QUEUE_STATS') {
    event.waitUntil(
      getPendingQueueItems()
        .then((items) => {
          event.ports[0]?.postMessage({
            success: true,
            stats: {
              pending: items.length,
              total: items.length,
            },
          });
        })
        .catch((error) => {
          event.ports[0]?.postMessage({ success: false, error: error.message });
        })
    );
  }
});

/**
 * Notify all clients with a message
 */
async function notifyClients(message) {
  const allClients = await self.clients.matchAll({
    includeUncontrolled: true,
    type: 'window',
  });

  allClients.forEach((client) => {
    client.postMessage(message);
  });
}

// ========================================
// Push Notifications (Future Feature)
// ========================================

/**
 * Push event - handle push notifications
 */
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received');

  if (!event.data) {
    return;
  }

  const data = event.data.json();

  const options = {
    body: data.body || 'New notification',
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.primaryKey || 1,
      url: data.url || '/',
    },
    actions: [
      { action: 'open', title: 'Open App' },
      { action: 'close', title: 'Close' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Data20', options)
  );
});

/**
 * Notification click event
 */
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification click:', event.action);

  event.notification.close();

  if (event.action === 'open') {
    const url = event.notification.data?.url || '/';
    event.waitUntil(
      clients.openWindow(url)
    );
  }
});

console.log('[Service Worker] v2.0.0 (Phase 8.1.4) loaded successfully');
