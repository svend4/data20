/**
 * Storage Manager
 * Uses IndexedDB for local data storage
 */

const DB_NAME = 'data20_extension';
const DB_VERSION = 2;  // Incremented for Phase 9.2.3 - added queue store
const STORES = {
  articles: 'articles',
  tools: 'tools',
  settings: 'settings',
  cache: 'cache',
  queue: 'queue'
};

export class StorageManager {
  static db = null;

  /**
   * Initialize IndexedDB
   */
  static async initialize() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create object stores
        if (!db.objectStoreNames.contains(STORES.articles)) {
          const articlesStore = db.createObjectStore(STORES.articles, {
            keyPath: 'id',
            autoIncrement: true
          });
          articlesStore.createIndex('timestamp', 'timestamp', { unique: false });
          articlesStore.createIndex('url', 'url', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.tools)) {
          db.createObjectStore(STORES.tools, { keyPath: 'name' });
        }

        if (!db.objectStoreNames.contains(STORES.settings)) {
          db.createObjectStore(STORES.settings, { keyPath: 'key' });
        }

        if (!db.objectStoreNames.contains(STORES.cache)) {
          const cacheStore = db.createObjectStore(STORES.cache, {
            keyPath: 'key'
          });
          cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORES.queue)) {
          const queueStore = db.createObjectStore(STORES.queue, {
            keyPath: 'id'
          });
          queueStore.createIndex('status', 'status', { unique: false });
          queueStore.createIndex('priority', 'priority', { unique: false });
          queueStore.createIndex('createdAt', 'createdAt', { unique: false });
        }
      };
    });
  }

  /**
   * Save article
   */
  static async saveArticle(article) {
    return this._add(STORES.articles, article);
  }

  /**
   * Get all articles
   */
  static async getArticles() {
    return this._getAll(STORES.articles);
  }

  /**
   * Delete article
   */
  static async deleteArticle(id) {
    return this._delete(STORES.articles, id);
  }

  /**
   * Save setting
   */
  static async saveSetting(key, value) {
    return this._put(STORES.settings, { key, value });
  }

  /**
   * Get setting
   */
  static async getSetting(key, defaultValue = null) {
    const result = await this._get(STORES.settings, key);
    return result ? result.value : defaultValue;
  }

  /**
   * Cache result
   */
  static async cacheResult(key, data, ttl = 3600000) {
    const entry = {
      key,
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl
    };
    return this._put(STORES.cache, entry);
  }

  /**
   * Get cached result
   */
  static async getCachedResult(key) {
    const entry = await this._get(STORES.cache, key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (entry.expiresAt < Date.now()) {
      await this._delete(STORES.cache, key);
      return null;
    }

    return entry.data;
  }

  /**
   * Get cached result (alias for getCachedResult)
   */
  static async getCached(key) {
    const entry = await this._get(STORES.cache, key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (entry.expiresAt < Date.now()) {
      await this._delete(STORES.cache, key);
      return null;
    }

    return entry;
  }

  /**
   * Remove cached entry
   */
  static async removeCached(key) {
    return this._delete(STORES.cache, key);
  }

  /**
   * Clear expired cache
   */
  static async clearExpiredCache() {
    const cache = await this._getAll(STORES.cache);
    const now = Date.now();

    for (const entry of cache) {
      if (entry.expiresAt < now) {
        await this._delete(STORES.cache, entry.key);
      }
    }
  }

  /**
   * Add job to queue
   */
  static async addToQueue(job) {
    return this._add(STORES.queue, job);
  }

  /**
   * Get all queued jobs
   */
  static async getQueuedJobs(status = 'queued') {
    return new Promise((resolve, reject) => {
      const store = this._getObjectStore(STORES.queue);
      const index = store.index('status');
      const request = index.getAll(status);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Update queue job
   */
  static async updateQueueJob(id, updates) {
    const job = await this._get(STORES.queue, id);
    if (!job) {
      throw new Error(`Job ${id} not found`);
    }

    const updatedJob = { ...job, ...updates };
    return this._put(STORES.queue, updatedJob);
  }

  /**
   * Remove job from queue
   */
  static async removeFromQueue(id) {
    return this._delete(STORES.queue, id);
  }

  /**
   * Get queue stats
   */
  static async getQueueStats() {
    const allJobs = await this._getAll(STORES.queue);

    const stats = {
      total: allJobs.length,
      queued: 0,
      processing: 0,
      completed: 0,
      failed: 0
    };

    for (const job of allJobs) {
      if (stats.hasOwnProperty(job.status)) {
        stats[job.status]++;
      }
    }

    return stats;
  }

  // Internal methods

  static _getObjectStore(storeName, mode = 'readonly') {
    const tx = this.db.transaction(storeName, mode);
    return tx.objectStore(storeName);
  }

  static async _add(storeName, data) {
    return new Promise((resolve, reject) => {
      const store = this._getObjectStore(storeName, 'readwrite');
      const request = store.add(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  static async _put(storeName, data) {
    return new Promise((resolve, reject) => {
      const store = this._getObjectStore(storeName, 'readwrite');
      const request = store.put(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  static async _get(storeName, key) {
    return new Promise((resolve, reject) => {
      const store = this._getObjectStore(storeName);
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  static async _getAll(storeName) {
    return new Promise((resolve, reject) => {
      const store = this._getObjectStore(storeName);
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  static async _delete(storeName, key) {
    return new Promise((resolve, reject) => {
      const store = this._getObjectStore(storeName, 'readwrite');
      const request = store.delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

export default StorageManager;
