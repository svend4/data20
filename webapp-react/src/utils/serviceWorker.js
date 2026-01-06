/**
 * Service Worker Utilities
 * Phase 8.1.4: Service Worker Integration
 *
 * Utilities for registering, updating, and communicating with the service worker.
 * Provides easy-to-use functions for the React app to interact with SW.
 */

/**
 * Service worker registration configuration
 */
const SW_URL = '/service-worker.js';
const SW_SCOPE = '/';

/**
 * Register service worker
 * @returns {Promise<ServiceWorkerRegistration>}
 */
export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    console.warn('[SW] Service workers are not supported in this browser');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register(SW_URL, {
      scope: SW_SCOPE,
    });

    console.log('[SW] Service worker registered successfully:', registration.scope);

    // Handle updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      console.log('[SW] New service worker found, installing...');

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          console.log('[SW] New service worker installed, reload to activate');
          // Notify user about update
          notifyUpdate(newWorker);
        }
      });
    });

    // Check for updates periodically (every hour)
    setInterval(() => {
      registration.update();
    }, 60 * 60 * 1000);

    // Setup message listener
    setupMessageListener();

    // Register background sync (if supported)
    if ('sync' in registration) {
      await registerBackgroundSync(registration);
    }

    // Register periodic sync (if supported)
    if ('periodicSync' in registration) {
      await registerPeriodicSync(registration);
    }

    return registration;
  } catch (error) {
    console.error('[SW] Service worker registration failed:', error);
    throw error;
  }
}

/**
 * Unregister service worker
 */
export async function unregisterServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const success = await registration.unregister();
    console.log('[SW] Service worker unregistered:', success);
    return success;
  } catch (error) {
    console.error('[SW] Service worker unregistration failed:', error);
    return false;
  }
}

/**
 * Update service worker
 */
export async function updateServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    await registration.update();
    console.log('[SW] Service worker update check triggered');
    return registration;
  } catch (error) {
    console.error('[SW] Service worker update failed:', error);
    return null;
  }
}

/**
 * Skip waiting for new service worker
 */
export function skipWaiting() {
  if (!navigator.serviceWorker.controller) {
    return;
  }

  navigator.serviceWorker.controller.postMessage({
    type: 'SKIP_WAITING',
  });
}

/**
 * Notify user about update
 */
function notifyUpdate(worker) {
  // This would typically show a snackbar or notification to the user
  // You can integrate this with your notification system
  console.log('[SW] Update available! Reload to get the latest version.');

  // Dispatch custom event that components can listen to
  window.dispatchEvent(new CustomEvent('sw-update-available', {
    detail: { worker },
  }));
}

// ============================================
// Background Sync Functions
// ============================================

/**
 * Register background sync
 */
async function registerBackgroundSync(registration) {
  try {
    await registration.sync.register('sync-queue');
    console.log('[SW] Background sync registered for queue');
  } catch (error) {
    console.error('[SW] Background sync registration failed:', error);
  }
}

/**
 * Register periodic background sync (Chrome 80+)
 * Syncs data every 24 hours when app is not in use
 */
async function registerPeriodicSync(registration) {
  try {
    const status = await navigator.permissions.query({
      name: 'periodic-background-sync',
    });

    if (status.state === 'granted') {
      await registration.periodicSync.register('sync-data', {
        minInterval: 24 * 60 * 60 * 1000, // 24 hours
      });
      console.log('[SW] Periodic sync registered (24h interval)');
    } else {
      console.log('[SW] Periodic sync permission not granted');
    }
  } catch (error) {
    console.error('[SW] Periodic sync registration failed:', error);
  }
}

/**
 * Trigger manual sync for queue
 */
export async function syncQueue() {
  return sendMessage({ type: 'SYNC_QUEUE' });
}

/**
 * Trigger manual sync for tools
 */
export async function syncTools() {
  return sendMessage({ type: 'SYNC_TOOLS' });
}

/**
 * Trigger manual sync for jobs
 */
export async function syncJobs() {
  return sendMessage({ type: 'SYNC_JOBS' });
}

/**
 * Get queue statistics from service worker
 */
export async function getQueueStats() {
  return sendMessage({ type: 'GET_QUEUE_STATS' });
}

// ============================================
// Cache Management Functions
// ============================================

/**
 * Cache specific URLs
 */
export async function cacheURLs(urls) {
  return sendMessage({
    type: 'CACHE_URLS',
    data: { urls },
  });
}

/**
 * Clear all caches
 */
export async function clearCache() {
  return sendMessage({ type: 'CLEAR_CACHE' });
}

// ============================================
// Message Communication
// ============================================

/**
 * Send message to service worker and wait for response
 */
async function sendMessage(message) {
  if (!navigator.serviceWorker.controller) {
    console.warn('[SW] No active service worker controller');
    return { success: false, error: 'No active service worker' };
  }

  return new Promise((resolve) => {
    const messageChannel = new MessageChannel();

    messageChannel.port1.onmessage = (event) => {
      resolve(event.data);
    };

    navigator.serviceWorker.controller.postMessage(message, [messageChannel.port2]);

    // Timeout after 30 seconds
    setTimeout(() => {
      resolve({ success: false, error: 'Timeout waiting for response' });
    }, 30000);
  });
}

/**
 * Setup message listener for SW notifications
 */
function setupMessageListener() {
  navigator.serviceWorker.addEventListener('message', (event) => {
    const { type, data } = event.data || {};

    console.log('[SW] Message from service worker:', type, data);

    // Dispatch custom events that React components can listen to
    switch (type) {
      case 'SW_ACTIVATED':
        window.dispatchEvent(new CustomEvent('sw-activated', { detail: data }));
        break;

      case 'QUEUE_SYNC_COMPLETED':
        window.dispatchEvent(new CustomEvent('queue-sync-completed', { detail: data }));
        break;

      case 'TOOLS_SYNCED':
        window.dispatchEvent(new CustomEvent('tools-synced', { detail: data }));
        break;

      case 'JOBS_SYNCED':
        window.dispatchEvent(new CustomEvent('jobs-synced', { detail: data }));
        break;

      default:
        window.dispatchEvent(new CustomEvent('sw-message', { detail: event.data }));
    }
  });
}

// ============================================
// Service Worker Status
// ============================================

/**
 * Check if service worker is supported
 */
export function isServiceWorkerSupported() {
  return 'serviceWorker' in navigator;
}

/**
 * Check if service worker is registered
 */
export async function isServiceWorkerRegistered() {
  if (!isServiceWorkerSupported()) {
    return false;
  }

  const registration = await navigator.serviceWorker.getRegistration(SW_SCOPE);
  return !!registration;
}

/**
 * Check if service worker is controlling the page
 */
export function isServiceWorkerActive() {
  return !!navigator.serviceWorker.controller;
}

/**
 * Get service worker registration
 */
export async function getServiceWorkerRegistration() {
  if (!isServiceWorkerSupported()) {
    return null;
  }

  return navigator.serviceWorker.getRegistration(SW_SCOPE);
}

/**
 * Get service worker state
 */
export async function getServiceWorkerState() {
  const registration = await getServiceWorkerRegistration();

  if (!registration) {
    return {
      supported: isServiceWorkerSupported(),
      registered: false,
      active: false,
      waiting: false,
      installing: false,
    };
  }

  return {
    supported: true,
    registered: true,
    active: !!registration.active,
    waiting: !!registration.waiting,
    installing: !!registration.installing,
    scope: registration.scope,
    updateViaCache: registration.updateViaCache,
  };
}

// ============================================
// React Hook Integration
// ============================================

/**
 * Custom event listener helper
 * Use this in React components with useEffect
 */
export function addServiceWorkerListener(eventType, handler) {
  window.addEventListener(eventType, handler);
  return () => window.removeEventListener(eventType, handler);
}

/**
 * Wait for service worker to be ready
 */
export async function waitForServiceWorker() {
  if (!isServiceWorkerSupported()) {
    throw new Error('Service workers are not supported');
  }

  return navigator.serviceWorker.ready;
}

// ============================================
// Development Helpers
// ============================================

/**
 * Check for service worker updates (for development)
 */
export async function checkForUpdates() {
  const registration = await getServiceWorkerRegistration();
  if (registration) {
    await registration.update();
    console.log('[SW] Checked for updates');
  }
}

/**
 * Get all caches (for debugging)
 */
export async function getAllCaches() {
  const cacheNames = await caches.keys();
  const allCaches = {};

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    allCaches[cacheName] = keys.map((request) => request.url);
  }

  return allCaches;
}

/**
 * Log service worker info (for debugging)
 */
export async function logServiceWorkerInfo() {
  const state = await getServiceWorkerState();
  const caches = await getAllCaches();

  console.group('[SW] Service Worker Info');
  console.log('State:', state);
  console.log('Caches:', caches);
  console.log('Controller:', navigator.serviceWorker.controller);
  console.groupEnd();

  return { state, caches, controller: navigator.serviceWorker.controller };
}

console.log('[SW Utils] Service worker utilities loaded');
