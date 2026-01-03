/**
 * PWA Manager - Progressive Web App Features
 * Handles installation, offline support, updates, and cache management
 * Version 3.0
 */

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.swRegistration = null;
        this.updateAvailable = false;

        this.init();
    }

    async init() {
        // Check if already installed
        this.checkInstallation();

        // Register service worker
        await this.registerServiceWorker();

        // Setup event listeners
        this.setupEventListeners();

        // Setup UI
        this.setupUI();

        // Check for updates periodically
        this.startUpdateCheck();

        console.log('[PWA] Manager initialized');
    }

    // ========================
    // Service Worker
    // ========================

    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[PWA] Service Workers not supported');
            return;
        }

        try {
            this.swRegistration = await navigator.serviceWorker.register('/service-worker.js', {
                scope: '/'
            });

            console.log('[PWA] Service Worker registered:', this.swRegistration);

            // Check for updates
            this.swRegistration.addEventListener('updatefound', () => {
                const newWorker = this.swRegistration.installing;
                console.log('[PWA] New Service Worker found');

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // New version available
                        this.updateAvailable = true;
                        this.showUpdateNotification();
                    }
                });
            });

            // Listen for controller change (update activated)
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                console.log('[PWA] New Service Worker activated');
                if (this.updateAvailable) {
                    window.location.reload();
                }
            });

        } catch (error) {
            console.error('[PWA] Service Worker registration failed:', error);
        }
    }

    async unregisterServiceWorker() {
        if (!this.swRegistration) return;

        try {
            await this.swRegistration.unregister();
            console.log('[PWA] Service Worker unregistered');
        } catch (error) {
            console.error('[PWA] Failed to unregister Service Worker:', error);
        }
    }

    // ========================
    // Installation
    // ========================

    checkInstallation() {
        // Check if running as PWA
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                           window.navigator.standalone ||
                           document.referrer.includes('android-app://');

        this.isInstalled = isStandalone;

        if (isStandalone) {
            console.log('[PWA] Running as installed app');
            this.hideInstallPrompt();
        }
    }

    setupEventListeners() {
        // Listen for install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });

        // Listen for successful installation
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] App installed successfully');
            this.isInstalled = true;
            this.hideInstallPrompt();
            this.showNotification('Успешно установлено!', 'success');
        });

        // Online/Offline events
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));

        // Visibility change (for update checks)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkForUpdates();
            }
        });
    }

    async installApp() {
        if (!this.deferredPrompt) {
            console.warn('[PWA] No install prompt available');
            return;
        }

        // Show install prompt
        this.deferredPrompt.prompt();

        // Wait for user response
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log(`[PWA] Install prompt outcome: ${outcome}`);

        if (outcome === 'accepted') {
            this.showNotification('Установка началась...', 'info');
        }

        // Clear the prompt
        this.deferredPrompt = null;
    }

    // ========================
    // Updates
    // ========================

    async checkForUpdates() {
        if (!this.swRegistration) return;

        try {
            await this.swRegistration.update();
            console.log('[PWA] Checked for updates');
        } catch (error) {
            console.error('[PWA] Update check failed:', error);
        }
    }

    startUpdateCheck() {
        // Check for updates every 5 minutes
        setInterval(() => {
            this.checkForUpdates();
        }, 5 * 60 * 1000);
    }

    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'pwa-update-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span>🔄 Доступно обновление</span>
                <button onclick="pwaManager.applyUpdate()" class="btn btn-sm btn-primary">
                    Обновить
                </button>
                <button onclick="this.parentElement.parentElement.remove()" class="btn btn-sm btn-secondary">
                    Позже
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 30000);
    }

    applyUpdate() {
        if (!this.swRegistration || !this.swRegistration.waiting) return;

        // Tell the waiting service worker to activate
        this.swRegistration.waiting.postMessage({ action: 'skipWaiting' });
    }

    // ========================
    // Online/Offline Status
    // ========================

    handleOnlineStatus(online) {
        this.isOnline = online;
        console.log(`[PWA] ${online ? 'Online' : 'Offline'}`);

        // Update UI
        this.updateStatusIndicator(online);

        // Show notification
        const message = online ?
            '🟢 Подключение восстановлено' :
            '🔴 Работа в оффлайн режиме';

        this.showNotification(message, online ? 'success' : 'warning');
    }

    updateStatusIndicator(online) {
        const indicator = document.getElementById('online-status');
        if (!indicator) return;

        indicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
        indicator.textContent = online ? '🟢 Онлайн' : '🔴 Оффлайн';
    }

    // ========================
    // Cache Management
    // ========================

    async getCacheStatus() {
        if (!this.swRegistration) return null;

        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();
            messageChannel.port1.onmessage = (event) => {
                resolve(event.data);
            };

            this.swRegistration.active.postMessage(
                { action: 'getCacheStatus' },
                [messageChannel.port2]
            );
        });
    }

    async clearCache() {
        if (!this.swRegistration) return;

        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();
            messageChannel.port1.onmessage = (event) => {
                if (event.data.success) {
                    this.showNotification('Кеш очищен', 'success');
                    resolve(true);
                }
            };

            this.swRegistration.active.postMessage(
                { action: 'clearCache' },
                [messageChannel.port2]
            );
        });
    }

    async showCacheStats() {
        const stats = await this.getCacheStatus();
        if (!stats) return;

        const modal = document.createElement('div');
        modal.className = 'pwa-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>📊 Статистика кеша</h3>
                <div class="cache-stats">
                    <div class="stat-item">
                        <span>Версия:</span>
                        <strong>${stats.version}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Статических файлов:</span>
                        <strong>${stats.staticCached}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Динамических файлов:</span>
                        <strong>${stats.dynamicCached}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Всего в кеше:</span>
                        <strong>${stats.totalCached}</strong>
                    </div>
                </div>
                <div class="modal-actions">
                    <button onclick="pwaManager.clearCache().then(() => this.closest('.pwa-modal').remove())" class="btn btn-danger">
                        🗑️ Очистить кеш
                    </button>
                    <button onclick="this.closest('.pwa-modal').remove()" class="btn btn-secondary">
                        Закрыть
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    // ========================
    // UI Components
    // ========================

    setupUI() {
        // Add online status indicator
        this.addStatusIndicator();

        // Add install prompt if not installed
        if (!this.isInstalled && this.deferredPrompt) {
            this.showInstallPrompt();
        }

        // Add PWA controls to nav (if exists)
        this.addNavControls();
    }

    addStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'online-status';
        indicator.className = `status-indicator ${this.isOnline ? 'online' : 'offline'}`;
        indicator.textContent = this.isOnline ? '🟢 Онлайн' : '🔴 Оффлайн';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 10px 15px;
            background: var(--bg-primary);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 500;
            z-index: 9999;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        `;

        document.body.appendChild(indicator);
    }

    showInstallPrompt() {
        // Remove existing prompt if any
        this.hideInstallPrompt();

        const prompt = document.createElement('div');
        prompt.id = 'pwa-install-prompt';
        prompt.className = 'install-prompt show';
        prompt.innerHTML = `
            <div class="prompt-content">
                <span>📱 Установить приложение?</span>
                <button onclick="pwaManager.installApp()" class="btn btn-primary">
                    Установить
                </button>
                <button onclick="pwaManager.hideInstallPrompt()" class="btn btn-text close-prompt">
                    ✕
                </button>
            </div>
        `;

        document.body.appendChild(prompt);
    }

    hideInstallPrompt() {
        const prompt = document.getElementById('pwa-install-prompt');
        if (prompt) {
            prompt.remove();
        }
    }

    addNavControls() {
        const navActions = document.querySelector('.nav-actions');
        if (!navActions) return;

        // PWA Menu button
        const pwaMenu = document.createElement('div');
        pwaMenu.className = 'pwa-menu-container';
        pwaMenu.innerHTML = `
            <button class="btn btn-icon" onclick="pwaManager.toggleMenu()" title="PWA настройки">
                ⚙️
            </button>
            <div class="pwa-dropdown" id="pwa-dropdown" style="display: none;">
                ${!this.isInstalled ? '<button onclick="pwaManager.installApp()">📱 Установить приложение</button>' : ''}
                <button onclick="pwaManager.checkForUpdates()">🔄 Проверить обновления</button>
                <button onclick="pwaManager.showCacheStats()">📊 Статистика кеша</button>
                <button onclick="pwaManager.clearCache()">🗑️ Очистить кеш</button>
                <hr>
                <button onclick="window.location.reload()">↻ Перезагрузить</button>
            </div>
        `;

        navActions.appendChild(pwaMenu);
    }

    toggleMenu() {
        const dropdown = document.getElementById('pwa-dropdown');
        if (!dropdown) return;

        const isVisible = dropdown.style.display !== 'none';
        dropdown.style.display = isVisible ? 'none' : 'block';

        if (!isVisible) {
            // Close on outside click
            setTimeout(() => {
                document.addEventListener('click', function closeMenu(e) {
                    if (!e.target.closest('.pwa-menu-container')) {
                        dropdown.style.display = 'none';
                        document.removeEventListener('click', closeMenu);
                    }
                });
            }, 0);
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `pwa-notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 20px;
            background: var(--bg-primary);
            border: 2px solid var(--border-color);
            border-left: 4px solid ${type === 'success' ? '#27ae60' : type === 'warning' ? '#f39c12' : '#667eea'};
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            z-index: 10001;
            animation: slideIn 0.3s ease-out;
            max-width: 300px;
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // ========================
    // Utility Methods
    // ========================

    getInstallStatus() {
        return {
            isInstalled: this.isInstalled,
            canInstall: !!this.deferredPrompt,
            isOnline: this.isOnline,
            hasServiceWorker: !!this.swRegistration,
            updateAvailable: this.updateAvailable
        };
    }

    async requestPersistentStorage() {
        if (navigator.storage && navigator.storage.persist) {
            const isPersisted = await navigator.storage.persist();
            console.log(`[PWA] Persistent storage: ${isPersisted ? 'granted' : 'denied'}`);
            return isPersisted;
        }
        return false;
    }

    async getStorageEstimate() {
        if (navigator.storage && navigator.storage.estimate) {
            const estimate = await navigator.storage.estimate();
            const usage = (estimate.usage / 1024 / 1024).toFixed(2);
            const quota = (estimate.quota / 1024 / 1024).toFixed(2);
            console.log(`[PWA] Storage: ${usage}MB / ${quota}MB`);
            return { usage, quota, percentage: (estimate.usage / estimate.quota * 100).toFixed(1) };
        }
        return null;
    }
}

// ========================
// Auto-initialize
// ========================

let pwaManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        pwaManager = new PWAManager();
    });
} else {
    pwaManager = new PWAManager();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}
