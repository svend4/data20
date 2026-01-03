// Service Worker for Data20 Knowledge Base PWA
// Version 3.0 - Multi-page Architecture with offline support

const CACHE_VERSION = 'data20-kb-v3.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const MAX_DYNAMIC_CACHE_SIZE = 50;

// Static assets to cache immediately on install
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/pages/explorer.html',
    '/pages/visualizations.html',
    '/pages/reports.html',
    '/pages/graph.html',
    '/pages/search.html',
    '/assets/css/enhanced.css',
    '/assets/css/multipage.css',
    '/assets/js/enhanced.js',
    '/assets/js/data-explorer.js',
    '/assets/js/dashboard.js',
    '/assets/js/graph-viewer.js',
    '/assets/js/pwa.js',
    '/manifest.json'
];

// CDN resources (cache separately)
const CDN_RESOURCES = [
    'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js',
    'https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js'
];

// ========================
// Install Event
// ========================
self.addEventListener('install', event => {
    console.log('[SW] Installing Service Worker v' + CACHE_VERSION);

    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE).then(cache => {
                console.log('[SW] Precaching static assets');
                return cache.addAll(STATIC_ASSETS).catch(err => {
                    console.warn('[SW] Failed to cache some static assets:', err);
                    // Cache individually to avoid one failure breaking everything
                    return Promise.allSettled(
                        STATIC_ASSETS.map(url =>
                            cache.add(url).catch(e => console.warn(`[SW] Failed to cache ${url}:`, e))
                        )
                    );
                });
            }),
            // Cache CDN resources
            caches.open(DYNAMIC_CACHE).then(cache => {
                console.log('[SW] Precaching CDN resources');
                return Promise.allSettled(
                    CDN_RESOURCES.map(url =>
                        cache.add(url).catch(e => console.warn(`[SW] Failed to cache CDN ${url}:`, e))
                    )
                );
            })
        ]).then(() => {
            console.log('[SW] Installation complete');
            return self.skipWaiting(); // Activate immediately
        })
    );
});

// ========================
// Activate Event
// ========================
self.addEventListener('activate', event => {
    console.log('[SW] Activating Service Worker v' + CACHE_VERSION);

    event.waitUntil(
        caches.keys().then(cacheNames => {
            // Delete old caches
            return Promise.all(
                cacheNames
                    .filter(name => name.startsWith('data20-kb-') && name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
                    .map(name => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => {
            console.log('[SW] Activation complete');
            return self.clients.claim(); // Take control immediately
        })
    );
});

// ========================
// Fetch Event
// ========================
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension and other non-http(s) URLs
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // Different strategies for different resources
    if (isCDNResource(url)) {
        // CDN: Stale-while-revalidate
        event.respondWith(staleWhileRevalidate(request));
    } else if (isStaticAsset(url)) {
        // Static assets: Cache-first
        event.respondWith(cacheFirst(request));
    } else if (isDataFile(url)) {
        // Data files: Network-first (always get fresh data if online)
        event.respondWith(networkFirst(request));
    } else {
        // Everything else: Network-first with fallback
        event.respondWith(networkFirst(request));
    }
});

// ========================
// Caching Strategies
// ========================

/**
 * Cache First: Try cache, fallback to network
 * Best for: Static assets that don't change often
 */
async function cacheFirst(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(request);

    if (cached) {
        console.log('[SW] Cache hit:', request.url);
        return cached;
    }

    console.log('[SW] Cache miss, fetching:', request.url);
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[SW] Fetch failed:', request.url, error);
        return new Response('Offline - resource not cached', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({ 'Content-Type': 'text/plain' })
        });
    }
}

/**
 * Network First: Try network, fallback to cache
 * Best for: Data that should be fresh but needs offline fallback
 */
async function networkFirst(request) {
    const cache = await caches.open(DYNAMIC_CACHE);

    try {
        const response = await fetch(request);

        if (response.ok) {
            // Cache successful responses
            cache.put(request, response.clone());
            // Limit cache size
            limitCacheSize(DYNAMIC_CACHE, MAX_DYNAMIC_CACHE_SIZE);
        }

        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        const cached = await cache.match(request);

        if (cached) {
            return cached;
        }

        // Return offline page for HTML requests
        if (request.headers.get('Accept')?.includes('text/html')) {
            return caches.match('/index.html');
        }

        return new Response('Offline', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({ 'Content-Type': 'text/plain' })
        });
    }
}

/**
 * Stale While Revalidate: Return cache immediately, update in background
 * Best for: CDN resources that should be fast but eventually updated
 */
async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cached = await cache.match(request);

    // Fetch in background
    const fetchPromise = fetch(request).then(response => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(err => {
        console.warn('[SW] Background fetch failed:', request.url, err);
    });

    // Return cached version immediately if available
    return cached || fetchPromise;
}

// ========================
// Helper Functions
// ========================

function isCDNResource(url) {
    return url.hostname.includes('cdn.jsdelivr.net') ||
           url.hostname.includes('unpkg.com') ||
           url.hostname.includes('cdnjs.cloudflare.com');
}

function isStaticAsset(url) {
    const path = url.pathname;
    return path.match(/\.(css|js|png|jpg|jpeg|svg|woff2?|ttf|eot)$/);
}

function isDataFile(url) {
    const path = url.pathname;
    return path.match(/\.(json|csv|html)$/) &&
           !path.includes('/pages/') &&
           !path.includes('manifest.json');
}

async function limitCacheSize(cacheName, maxSize) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();

    if (keys.length > maxSize) {
        // Delete oldest entries (FIFO)
        const toDelete = keys.slice(0, keys.length - maxSize);
        await Promise.all(toDelete.map(key => cache.delete(key)));
        console.log(`[SW] Cleaned ${toDelete.length} old entries from ${cacheName}`);
    }
}

// ========================
// Message Handler
// ========================
self.addEventListener('message', event => {
    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }

    if (event.data.action === 'clearCache') {
        event.waitUntil(
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(name => caches.delete(name))
                );
            }).then(() => {
                console.log('[SW] All caches cleared');
                event.ports[0].postMessage({ success: true });
            })
        );
    }

    if (event.data.action === 'getCacheStatus') {
        event.waitUntil(
            Promise.all([
                caches.open(STATIC_CACHE).then(cache => cache.keys()),
                caches.open(DYNAMIC_CACHE).then(cache => cache.keys())
            ]).then(([staticKeys, dynamicKeys]) => {
                event.ports[0].postMessage({
                    version: CACHE_VERSION,
                    staticCached: staticKeys.length,
                    dynamicCached: dynamicKeys.length,
                    totalCached: staticKeys.length + dynamicKeys.length
                });
            })
        );
    }
});

// ========================
// Background Sync (future enhancement)
// ========================
self.addEventListener('sync', event => {
    if (event.tag === 'sync-data') {
        console.log('[SW] Background sync triggered');
        // Implement background data sync logic here
    }
});

// ========================
// Push Notifications (future enhancement)
// ========================
self.addEventListener('push', event => {
    if (event.data) {
        const data = event.data.json();
        console.log('[SW] Push notification received:', data);

        const options = {
            body: data.body || 'New update available',
            icon: '/assets/icons/icon-192x192.png',
            badge: '/assets/icons/icon-72x72.png',
            vibrate: [200, 100, 200],
            data: data
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'Data20 KB', options)
        );
    }
});

self.addEventListener('notificationclick', event => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data?.url || '/')
    );
});

console.log('[SW] Service Worker loaded');
