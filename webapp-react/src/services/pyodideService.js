/**
 * Pyodide Service
 * Phase 8.1.5: WebAssembly Tools (Pyodide Integration)
 *
 * High-level service for running Python tools via Pyodide (WebAssembly).
 * Manages the Web Worker and provides a simple API for tool execution.
 */

class PyodideService {
  constructor() {
    this.worker = null;
    this.messageId = 0;
    this.pendingMessages = new Map();
    this.isInitialized = false;
    this.initializationPromise = null;
    this.eventListeners = new Map();
  }

  /**
   * Initialize the Pyodide worker
   */
  async initialize() {
    if (this.isInitialized && this.worker) {
      return;
    }

    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = new Promise((resolve, reject) => {
      try {
        console.log('[PyodideService] Initializing Pyodide worker...');

        // Create worker
        this.worker = new Worker(new URL('./pyodideWorker.js', import.meta.url), {
          type: 'module',
        });

        // Setup message handler
        this.worker.onmessage = (event) => {
          this.handleWorkerMessage(event.data);
        };

        // Setup error handler
        this.worker.onerror = (error) => {
          console.error('[PyodideService] Worker error:', error);
          this.emit('error', error);
        };

        // Send initialization message
        this.sendMessage('INIT', {})
          .then(() => {
            this.isInitialized = true;
            console.log('[PyodideService] Pyodide worker initialized successfully');
            this.emit('initialized');
            resolve();
          })
          .catch((error) => {
            console.error('[PyodideService] Initialization failed:', error);
            this.initializationPromise = null;
            reject(error);
          });
      } catch (error) {
        console.error('[PyodideService] Failed to create worker:', error);
        this.initializationPromise = null;
        reject(error);
      }
    });

    return this.initializationPromise;
  }

  /**
   * Send message to worker
   */
  sendMessage(type, data) {
    return new Promise((resolve, reject) => {
      const id = ++this.messageId;

      // Store promise callbacks
      this.pendingMessages.set(id, { resolve, reject });

      // Send message to worker
      this.worker.postMessage({ id, type, data });

      // Timeout after 60 seconds
      setTimeout(() => {
        if (this.pendingMessages.has(id)) {
          this.pendingMessages.delete(id);
          reject(new Error('Pyodide worker timeout'));
        }
      }, 60000);
    });
  }

  /**
   * Handle worker messages
   */
  handleWorkerMessage(message) {
    const { id, type, result, error } = message;

    const pending = this.pendingMessages.get(id);
    if (!pending) {
      return;
    }

    this.pendingMessages.delete(id);

    if (type === 'ERROR' || error) {
      pending.reject(error || new Error('Unknown error'));
    } else {
      pending.resolve(result);
    }
  }

  /**
   * Execute Python code
   */
  async executePython(code, context = {}) {
    await this.initialize();

    console.log('[PyodideService] Executing Python code...');

    const result = await this.sendMessage('EXECUTE', {
      code,
      context,
    });

    if (!result.success) {
      throw new Error(result.error || 'Python execution failed');
    }

    return result.result;
  }

  /**
   * Execute a Python tool
   */
  async executeTool(toolCode, functionName, parameters) {
    await this.initialize();

    console.log(`[PyodideService] Executing tool: ${functionName}`);
    this.emit('tool:executing', { functionName, parameters });

    const startTime = Date.now();

    try {
      const result = await this.sendMessage('EXECUTE_TOOL', {
        toolCode,
        functionName,
        parameters,
      });

      const executionTime = Date.now() - startTime;

      if (!result.success) {
        this.emit('tool:error', {
          functionName,
          error: result.error,
          executionTime,
        });
        throw new Error(result.error || 'Tool execution failed');
      }

      console.log(`[PyodideService] Tool executed successfully in ${executionTime}ms`);
      this.emit('tool:completed', {
        functionName,
        result: result.result,
        executionTime,
      });

      return result.result;
    } catch (error) {
      const executionTime = Date.now() - startTime;
      this.emit('tool:error', { functionName, error, executionTime });
      throw error;
    }
  }

  /**
   * Install Python packages
   */
  async installPackages(packages) {
    await this.initialize();

    console.log(`[PyodideService] Installing packages: ${packages.join(', ')}`);

    const result = await this.sendMessage('INSTALL_PACKAGES', { packages });

    if (!result.success) {
      throw new Error(result.error || 'Package installation failed');
    }

    console.log('[PyodideService] Packages installed successfully');
    return result.installed;
  }

  /**
   * Get Pyodide status
   */
  async getStatus() {
    if (!this.worker) {
      return {
        initialized: false,
        version: null,
      };
    }

    return this.sendMessage('GET_STATUS', {});
  }

  /**
   * Terminate worker
   */
  terminate() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
      this.isInitialized = false;
      this.initializationPromise = null;
      this.pendingMessages.clear();
      console.log('[PyodideService] Worker terminated');
    }
  }

  /**
   * Event emitter - on
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  /**
   * Event emitter - off
   */
  off(event, callback) {
    if (!this.eventListeners.has(event)) {
      return;
    }

    const listeners = this.eventListeners.get(event);
    const index = listeners.indexOf(callback);

    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  /**
   * Event emitter - emit
   */
  emit(event, data) {
    if (!this.eventListeners.has(event)) {
      return;
    }

    const listeners = this.eventListeners.get(event);
    listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[PyodideService] Event listener error (${event}):`, error);
      }
    });
  }
}

// Create singleton instance
const pyodideService = new PyodideService();

// Export singleton and class
export default pyodideService;
export { PyodideService };

console.log('[PyodideService] Service loaded');
