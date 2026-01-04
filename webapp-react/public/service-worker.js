/**
 * Service Worker for Data20 Knowledge Base PWA
 * Phase 7.2: Progressive Web App with Offline Support
 *
 * This service worker implements:
 * - Static asset caching (app shell)
 * - API response caching with network-first strategy
 * - Offline fallback page
 * - Background sync for failed requests
 * - Cache versioning and cleanup
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `data20-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline.html';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
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
  /\/api\/jobs$/,            // Job creation
];

/**
 * Install event - precache essential assets
 */
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');

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
  console.log('[Service Worker] Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Activated successfully');
        // Take control of all clients immediately
        return self.clients.claim();
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
 * Handle API requests - Network First strategy
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
    }

    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Network request failed, trying cache:', url.pathname);

    // Fallback to cache if available
    if (cacheable) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('[Service Worker] Serving from cache:', url.pathname);
        return cachedResponse;
      }
    }

    // Return offline response for failed API requests
    return new Response(
      JSON.stringify({
        error: 'offline',
        message: 'You are currently offline. Please check your internet connection.',
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
            p { font-size: 1.2rem; opacity: 0.9; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>📡 You're Offline</h1>
            <p>Please check your internet connection and try again.</p>
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
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect fill="#ddd" width="200" height="200"/><text x="50%" y="50%" text-anchor="middle" fill="#999">Offline</text></svg>',
        { headers: { 'Content-Type': 'image/svg+xml' } }
      );
    }

    return new Response('Not available offline', {
      status: 503,
      statusText: 'Service Unavailable',
    });
  }
}

/**
 * Background Sync event - retry failed requests
 */
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);

  if (event.tag === 'sync-jobs') {
    event.waitUntil(syncPendingJobs());
  }
});

/**
 * Sync pending jobs when back online
 */
async function syncPendingJobs() {
  try {
    // Get pending jobs from IndexedDB (would need to implement)
    console.log('[Service Worker] Syncing pending jobs...');

    // This is a placeholder - actual implementation would:
    // 1. Get pending jobs from IndexedDB
    // 2. Retry failed API requests
    // 3. Update job status
    // 4. Notify user of success/failure

    return Promise.resolve();
  } catch (error) {
    console.error('[Service Worker] Background sync failed:', error);
    return Promise.reject(error);
  }
}

/**
 * Message event - handle messages from clients
 */
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    const urls = event.data.urls || [];
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then((cache) => cache.addAll(urls))
    );
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys()
        .then((cacheNames) => Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        ))
        .then(() => {
          event.ports[0].postMessage({ success: true });
        })
    );
  }
});

/**
 * Push event - handle push notifications (future feature)
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
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('[Service Worker] Loaded successfully');
