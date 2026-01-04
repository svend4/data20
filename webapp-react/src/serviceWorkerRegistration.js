/**
 * Service Worker Registration
 * Phase 7.2: Progressive Web App Support
 *
 * This module handles the registration, updates, and lifecycle
 * of the service worker for offline functionality.
 */

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
    window.location.hostname === '[::1]' ||
    window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/)
);

/**
 * Configuration for service worker registration
 */
const config = {
  onSuccess: null,
  onUpdate: null,
  onOffline: null,
  onOnline: null,
};

/**
 * Register the service worker
 * @param {Object} callbacks - Callback functions for SW events
 */
export function register(callbacks = {}) {
  if (process.env.NODE_ENV === 'production' && 'serviceWorker' in navigator) {
    // Override default callbacks
    Object.assign(config, callbacks);

    // The URL constructor is available in all browsers that support SW.
    const publicUrl = new URL(process.env.PUBLIC_URL, window.location.href);
    if (publicUrl.origin !== window.location.origin) {
      // Service worker won't work if PUBLIC_URL is on a different origin
      return;
    }

    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

      if (isLocalhost) {
        // This is running on localhost. Check if a service worker still exists or not.
        checkValidServiceWorker(swUrl);

        // Add some additional logging to localhost, pointing to the service worker/PWA docs
        navigator.serviceWorker.ready.then(() => {
          console.log(
            'This web app is being served cache-first by a service ' +
              'worker. To learn more, visit https://cra.link/PWA'
          );
        });
      } else {
        // Is not localhost. Just register service worker
        registerValidSW(swUrl);
      }
    });

    // Listen for online/offline events
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
  }
}

/**
 * Register a valid service worker
 */
function registerValidSW(swUrl) {
  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log('[SW Registration] Service worker registered:', registration);

      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) {
          return;
        }

        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              // At this point, the updated precached content has been fetched,
              // but the previous service worker will still serve the older
              // content until all client tabs are closed.
              console.log(
                '[SW Registration] New content is available and will be used when all ' +
                  'tabs for this page are closed. See https://cra.link/PWA.'
              );

              // Execute callback
              if (config.onUpdate) {
                config.onUpdate(registration);
              }
            } else {
              // At this point, everything has been precached.
              // It's the perfect time to display a "Content is cached for offline use." message.
              console.log('[SW Registration] Content is cached for offline use.');

              // Execute callback
              if (config.onSuccess) {
                config.onSuccess(registration);
              }
            }
          }
        };
      };

      // Check for updates every hour
      setInterval(() => {
        registration.update();
      }, 60 * 60 * 1000); // Check every hour
    })
    .catch((error) => {
      console.error('[SW Registration] Error during service worker registration:', error);
    });
}

/**
 * Check if the service worker can be found. If it can't, reload the page.
 */
function checkValidServiceWorker(swUrl) {
  // Check if the service worker can be found. If it can't, reload the page.
  fetch(swUrl, {
    headers: { 'Service-Worker': 'script' },
  })
    .then((response) => {
      // Ensure service worker exists, and that we really are getting a JS file.
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf('javascript') === -1)
      ) {
        // No service worker found. Probably a different app. Reload the page.
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        // Service worker found. Proceed as normal.
        registerValidSW(swUrl);
      }
    })
    .catch(() => {
      console.log('[SW Registration] No internet connection found. App is running in offline mode.');
    });
}

/**
 * Unregister the service worker
 */
export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
        console.log('[SW Registration] Service worker unregistered');
      })
      .catch((error) => {
        console.error('[SW Registration] Error unregistering service worker:', error.message);
      });
  }
}

/**
 * Update the service worker
 */
export function update() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.update();
        console.log('[SW Registration] Checking for service worker updates...');
      })
      .catch((error) => {
        console.error('[SW Registration] Error updating service worker:', error.message);
      });
  }
}

/**
 * Skip waiting and activate new service worker immediately
 */
export function skipWaiting() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        if (registration.waiting) {
          registration.waiting.postMessage({ type: 'SKIP_WAITING' });
          console.log('[SW Registration] Activating new service worker...');
        }
      })
      .catch((error) => {
        console.error('[SW Registration] Error activating service worker:', error.message);
      });
  }
}

/**
 * Clear all caches
 */
export function clearCache() {
  return new Promise((resolve, reject) => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready
        .then((registration) => {
          const messageChannel = new MessageChannel();

          messageChannel.port1.onmessage = (event) => {
            if (event.data.success) {
              console.log('[SW Registration] All caches cleared');
              resolve();
            } else {
              reject(new Error('Failed to clear caches'));
            }
          };

          registration.active.postMessage(
            { type: 'CLEAR_CACHE' },
            [messageChannel.port2]
          );
        })
        .catch(reject);
    } else {
      reject(new Error('Service Worker not supported'));
    }
  });
}

/**
 * Cache specific URLs
 */
export function cacheURLs(urls) {
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
      type: 'CACHE_URLS',
      urls,
    });
    console.log('[SW Registration] Requested caching of URLs:', urls);
  }
}

/**
 * Check if the app is running in standalone mode (installed PWA)
 */
export function isStandalone() {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone ||
    document.referrer.includes('android-app://')
  );
}

/**
 * Get the installation prompt
 */
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  // Stash the event so it can be triggered later
  deferredPrompt = e;
  console.log('[PWA] Install prompt available');
});

/**
 * Show the install prompt
 */
export async function showInstallPrompt() {
  if (!deferredPrompt) {
    console.log('[PWA] Install prompt not available');
    return { outcome: 'not-available' };
  }

  // Show the install prompt
  deferredPrompt.prompt();

  // Wait for the user to respond to the prompt
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`[PWA] User response to install prompt: ${outcome}`);

  // Clear the deferredPrompt
  deferredPrompt = null;

  return { outcome };
}

/**
 * Check if install prompt is available
 */
export function canInstall() {
  return deferredPrompt !== null;
}

/**
 * Handle online event
 */
function handleOnline() {
  console.log('[PWA] App is online');
  if (config.onOnline) {
    config.onOnline();
  }
}

/**
 * Handle offline event
 */
function handleOffline() {
  console.log('[PWA] App is offline');
  if (config.onOffline) {
    config.onOffline();
  }
}

/**
 * Get connection status
 */
export function getConnectionStatus() {
  return {
    online: navigator.onLine,
    type: navigator.connection?.effectiveType || 'unknown',
    downlink: navigator.connection?.downlink || null,
    rtt: navigator.connection?.rtt || null,
    saveData: navigator.connection?.saveData || false,
  };
}

/**
 * Listen for connection changes
 */
export function onConnectionChange(callback) {
  const handleChange = () => {
    callback(getConnectionStatus());
  };

  window.addEventListener('online', handleChange);
  window.addEventListener('offline', handleChange);

  if (navigator.connection) {
    navigator.connection.addEventListener('change', handleChange);
  }

  // Return cleanup function
  return () => {
    window.removeEventListener('online', handleChange);
    window.removeEventListener('offline', handleChange);
    if (navigator.connection) {
      navigator.connection.removeEventListener('change', handleChange);
    }
  };
}

/**
 * Export default registration object
 */
export default {
  register,
  unregister,
  update,
  skipWaiting,
  clearCache,
  cacheURLs,
  isStandalone,
  showInstallPrompt,
  canInstall,
  getConnectionStatus,
  onConnectionChange,
};
