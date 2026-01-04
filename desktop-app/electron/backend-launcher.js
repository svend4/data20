/**
 * Backend Launcher for Embedded Python Backend
 * Phase 7.1: Desktop Embedded Backend
 *
 * This module manages the lifecycle of the embedded Python FastAPI backend:
 * - Starts the backend process (Python executable or development server)
 * - Monitors health and readiness
 * - Handles graceful shutdown
 * - Provides restart capabilities
 *
 * Usage:
 *   const BackendLauncher = require('./backend-launcher');
 *   const launcher = new BackendLauncher();
 *   await launcher.start();
 *   // ... use backend ...
 *   launcher.stop();
 */

const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');
const { app } = require('electron');
const fs = require('fs');

class BackendLauncher {
  constructor(options = {}) {
    this.process = null;
    this.port = options.port || 8001;
    this.host = options.host || '127.0.0.1';
    this.baseUrl = `http://${this.host}:${this.port}`;
    this.isReady = false;
    this.startTime = null;
    this.logs = [];
    this.maxLogs = 1000; // Keep last 1000 log lines
  }

  /**
   * Get the path to the backend executable or Python script
   * @returns {Object} Command and args to execute
   */
  getExecutablePath() {
    const isDev = !app.isPackaged;

    if (isDev) {
      // Development mode: use Python interpreter
      console.log('🔧 Development mode: using Python interpreter');

      // Try to find python3, then python
      const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

      return {
        command: pythonCmd,
        args: [
          path.join(__dirname, '../../backend/server.py')
        ],
        isDev: true
      };
    } else {
      // Production mode: use packaged executable
      console.log('📦 Production mode: using packaged executable');

      const resourcePath = process.resourcesPath;
      const platform = process.platform;

      let exeName = 'data20-backend';
      if (platform === 'win32') {
        exeName += '.exe';
      }

      const exePath = path.join(resourcePath, 'backend', exeName);

      // Verify executable exists
      if (!fs.existsSync(exePath)) {
        throw new Error(`Backend executable not found: ${exePath}`);
      }

      return {
        command: exePath,
        args: [],
        isDev: false
      };
    }
  }

  /**
   * Get the database path in user data directory
   * @returns {string} Absolute path to SQLite database
   */
  getDatabasePath() {
    const userDataPath = app.getPath('userData');
    const dbPath = path.join(userDataPath, 'data20.db');

    // Ensure directory exists
    const dbDir = path.dirname(dbPath);
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }

    return dbPath;
  }

  /**
   * Get upload and output directories
   * @returns {Object} Paths for uploads and outputs
   */
  getStoragePaths() {
    const userDataPath = app.getPath('userData');

    const uploadDir = path.join(userDataPath, 'uploads');
    const outputDir = path.join(userDataPath, 'output');

    // Create directories if they don't exist
    [uploadDir, outputDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });

    return { uploadDir, outputDir };
  }

  /**
   * Build environment variables for backend process
   * @returns {Object} Environment variables
   */
  buildEnvironment() {
    const dbPath = this.getDatabasePath();
    const { uploadDir, outputDir } = this.getStoragePaths();

    return {
      ...process.env,

      // Deployment mode
      DEPLOYMENT_MODE: 'standalone',

      // Database (SQLite)
      DATABASE_URL: `sqlite:///${dbPath}`,

      // Disable external services
      REDIS_ENABLED: 'false',
      CELERY_ENABLED: 'false',

      // Server configuration
      HOST: this.host,
      PORT: this.port.toString(),

      // Storage paths
      UPLOAD_DIR: uploadDir,
      OUTPUT_DIR: outputDir,

      // Logging
      LOG_LEVEL: 'INFO',
      LOG_FORMAT: 'json',

      // Prevent Python from buffering output
      PYTHONUNBUFFERED: '1',
    };
  }

  /**
   * Add log entry
   * @param {string} source - Log source (stdout/stderr)
   * @param {string} message - Log message
   */
  addLog(source, message) {
    const entry = {
      timestamp: new Date().toISOString(),
      source,
      message: message.trim()
    };

    this.logs.push(entry);

    // Keep only last N logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
  }

  /**
   * Get recent logs
   * @param {number} count - Number of logs to retrieve
   * @returns {Array} Recent log entries
   */
  getLogs(count = 100) {
    return this.logs.slice(-count);
  }

  /**
   * Start the backend process
   * @returns {Promise<boolean>} True if started successfully
   */
  async start() {
    if (this.process) {
      console.warn('⚠️  Backend already running');
      return true;
    }

    console.log('🚀 Starting backend...');
    this.startTime = Date.now();

    try {
      const { command, args, isDev } = this.getExecutablePath();
      const env = this.buildEnvironment();

      console.log(`📦 Command: ${command} ${args.join(' ')}`);
      console.log(`📊 Database: ${this.getDatabasePath()}`);
      console.log(`🌐 URL: ${this.baseUrl}`);

      // Spawn the process
      this.process = spawn(command, args, {
        env,
        stdio: ['ignore', 'pipe', 'pipe'], // stdin ignored, stdout/stderr piped
        windowsHide: true, // Hide console window on Windows
      });

      // Setup logging
      this.process.stdout.on('data', (data) => {
        const message = data.toString();
        console.log(`[Backend] ${message.trim()}`);
        this.addLog('stdout', message);
      });

      this.process.stderr.on('data', (data) => {
        const message = data.toString();
        console.error(`[Backend Error] ${message.trim()}`);
        this.addLog('stderr', message);
      });

      // Handle process errors
      this.process.on('error', (error) => {
        console.error('❌ Backend process error:', error);
        this.isReady = false;
        this.addLog('error', `Process error: ${error.message}`);
      });

      // Handle process exit
      this.process.on('exit', (code, signal) => {
        const exitMessage = `Backend exited with code ${code}, signal ${signal}`;
        console.log(`⚠️  ${exitMessage}`);
        this.addLog('exit', exitMessage);
        this.isReady = false;
        this.process = null;
      });

      // Wait for backend to be ready
      await this.waitForReady();

      const startupTime = Date.now() - this.startTime;
      console.log(`✅ Backend ready! (startup time: ${startupTime}ms)`);
      this.isReady = true;

      return true;

    } catch (error) {
      console.error('❌ Failed to start backend:', error);
      this.stop();
      throw error;
    }
  }

  /**
   * Wait for backend to become ready
   * @param {number} maxAttempts - Maximum number of attempts
   * @param {number} interval - Interval between attempts (ms)
   * @returns {Promise<boolean>} True if backend is ready
   */
  async waitForReady(maxAttempts = 60, interval = 1000) {
    console.log(`⏳ Waiting for backend to be ready (max ${maxAttempts}s)...`);

    for (let i = 0; i < maxAttempts; i++) {
      try {
        // Try to connect to health endpoint
        const response = await axios.get(`${this.baseUrl}/health`, {
          timeout: 2000,
          validateStatus: (status) => status === 200
        });

        if (response.status === 200) {
          console.log(`✅ Backend health check passed (attempt ${i + 1})`);
          return true;
        }
      } catch (error) {
        // Backend not ready yet, wait and retry
        if (i % 10 === 0 && i > 0) {
          console.log(`⏳ Still waiting... (${i}s elapsed)`);
        }
      }

      // Check if process is still alive
      if (!this.process || this.process.exitCode !== null) {
        throw new Error('Backend process exited during startup');
      }

      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('Backend failed to start within timeout');
  }

  /**
   * Stop the backend process
   * @param {number} timeout - Graceful shutdown timeout (ms)
   * @returns {Promise<void>}
   */
  async stop(timeout = 5000) {
    if (!this.process) {
      console.log('ℹ️  Backend not running');
      return;
    }

    console.log('🛑 Stopping backend...');

    // Try graceful shutdown first
    this.process.kill('SIGTERM');

    // Wait for graceful shutdown
    const shutdownPromise = new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (!this.process || this.process.exitCode !== null) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);
    });

    // Force kill if timeout exceeded
    const timeoutPromise = new Promise((resolve) => {
      setTimeout(() => {
        if (this.process && this.process.exitCode === null) {
          console.warn('⚠️  Force killing backend...');
          this.process.kill('SIGKILL');
        }
        resolve();
      }, timeout);
    });

    await Promise.race([shutdownPromise, timeoutPromise]);

    this.process = null;
    this.isReady = false;

    console.log('✅ Backend stopped');
  }

  /**
   * Restart the backend
   * @returns {Promise<boolean>}
   */
  async restart() {
    console.log('🔄 Restarting backend...');
    await this.stop();
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s
    return await this.start();
  }

  /**
   * Check backend health status
   * @returns {Promise<Object>} Health status
   */
  async checkHealth() {
    if (!this.isReady) {
      return {
        status: 'offline',
        ready: false,
        message: 'Backend not running'
      };
    }

    try {
      const response = await axios.get(`${this.baseUrl}/health`, {
        timeout: 2000
      });

      return {
        status: 'online',
        ready: true,
        data: response.data,
        uptime: Date.now() - this.startTime
      };
    } catch (error) {
      return {
        status: 'error',
        ready: false,
        error: error.message
      };
    }
  }

  /**
   * Get backend URL
   * @returns {string} Base URL
   */
  getUrl() {
    return this.baseUrl;
  }

  /**
   * Get backend info
   * @returns {Object} Backend information
   */
  getInfo() {
    return {
      url: this.baseUrl,
      ready: this.isReady,
      running: this.process !== null,
      uptime: this.startTime ? Date.now() - this.startTime : 0,
      database: this.getDatabasePath(),
      storage: this.getStoragePaths(),
      logCount: this.logs.length
    };
  }

  /**
   * Check if backend is running
   * @returns {boolean}
   */
  isRunning() {
    return this.process !== null && this.process.exitCode === null;
  }
}

module.exports = BackendLauncher;
