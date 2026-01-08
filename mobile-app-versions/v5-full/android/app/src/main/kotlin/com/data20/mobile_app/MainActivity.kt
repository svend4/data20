package com.data20.mobile_app

import android.os.Bundle
import android.util.Log
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.*
import java.io.File

/**
 * MainActivity with embedded Python backend
 *
 * This activity manages the lifecycle of the Python FastAPI backend
 * and provides a bridge between Flutter and Python via MethodChannel.
 */
class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.data20/backend"
    private val TAG = "MainActivity"

    private var python: Python? = null
    private var backendJob: Job? = null
    private var isBackendRunning = false
    private var isPythonInitialized = false

    /**
     * Initialize Python environment (lazy - only when needed)
     * Returns true if Python is ready, false otherwise
     */
    private fun ensurePythonInitialized(): Boolean {
        if (isPythonInitialized && python != null) {
            Log.i(TAG, "Python already initialized, skipping")
            return true
        }

        if (!Python.isStarted()) {
            try {
                val startTime = System.currentTimeMillis()
                Log.i(TAG, "⏱️  [TIMER] Starting Python initialization...")

                Python.start(AndroidPlatform(this))
                python = Python.getInstance()
                isPythonInitialized = true

                val elapsedMs = System.currentTimeMillis() - startTime
                Log.i(TAG, "✅ Python initialized successfully")
                Log.i(TAG, "⏱️  [TIMER] Python initialization took: ${elapsedMs}ms (${elapsedMs / 1000}s)")
                return true
            } catch (e: Exception) {
                Log.e(TAG, "❌ Failed to initialize Python: ${e.message}")
                e.printStackTrace()
                isPythonInitialized = false
                return false
            }
        } else {
            python = Python.getInstance()
            isPythonInitialized = true
            Log.i(TAG, "Python was already started, got instance")
            return true
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Setup method channel for Flutter <-> Native communication
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "startBackend" -> startBackend(result)
                "stopBackend" -> stopBackend(result)
                "isBackendRunning" -> result.success(isBackendRunning)
                "getBackendStatus" -> getBackendStatus(result)
                "restartBackend" -> restartBackend(result)
                else -> result.notImplemented()
            }
        }
    }

    /**
     * Start Python backend server
     */
    private fun startBackend(result: MethodChannel.Result) {
        if (isBackendRunning) {
            result.success(mapOf(
                "success" to true,
                "message" to "Backend already running"
            ))
            return
        }

        val totalStartTime = System.currentTimeMillis()
        Log.i(TAG, "⏱️  [TIMER] ===== BACKEND START - TOTAL TIMER STARTED =====")

        // Ensure Python is initialized first
        val pythonInitStart = System.currentTimeMillis()
        if (!ensurePythonInitialized()) {
            result.error(
                "PYTHON_ERROR",
                "Failed to initialize Python environment. Please check logs.",
                null
            )
            return
        }
        val pythonInitElapsed = System.currentTimeMillis() - pythonInitStart
        Log.i(TAG, "⏱️  [TIMER] Python init step: ${pythonInitElapsed}ms")

        Log.i(TAG, "Starting Python backend...")

        backendJob = CoroutineScope(Dispatchers.IO).launch {
            try {
                // Setup environment
                val envSetupStart = System.currentTimeMillis()
                setupEnvironment()
                val envSetupElapsed = System.currentTimeMillis() - envSetupStart
                Log.i(TAG, "⏱️  [TIMER] Environment setup: ${envSetupElapsed}ms")

                // Get Python main module
                // Using SIMPLIFIED backend to avoid crashes from heavy dependencies
                Log.i(TAG, "Loading simplified backend module...")
                val moduleLoadStart = System.currentTimeMillis()
                val mainModule = try {
                    python!!.getModule("backend_main_simple")
                } catch (e: Exception) {
                    Log.e(TAG, "❌ Failed to load backend_main_simple, trying backend_main...")
                    python!!.getModule("backend_main")
                }
                val moduleLoadElapsed = System.currentTimeMillis() - moduleLoadStart
                Log.i(TAG, "⏱️  [TIMER] Module loading: ${moduleLoadElapsed}ms (${moduleLoadElapsed / 1000}s)")

                // Setup Android-specific paths
                val setupEnvStart = System.currentTimeMillis()
                mainModule.callAttr(
                    "setup_environment",
                    getDatabasePath(),
                    getUploadPath(),
                    getLogsPath()
                )
                val setupEnvElapsed = System.currentTimeMillis() - setupEnvStart
                Log.i(TAG, "⏱️  [TIMER] Python setup_environment call: ${setupEnvElapsed}ms")

                // Mark as running
                isBackendRunning = true

                // Notify Flutter that backend started
                val totalElapsed = System.currentTimeMillis() - totalStartTime
                Log.i(TAG, "⏱️  [TIMER] ===== BACKEND INITIALIZATION COMPLETE =====")
                Log.i(TAG, "⏱️  [TIMER] TOTAL TIME TO START: ${totalElapsed}ms (${totalElapsed / 1000}s)")

                withContext(Dispatchers.Main) {
                    result.success(mapOf(
                        "success" to true,
                        "message" to "Backend started successfully",
                        "port" to BuildConfig.BACKEND_PORT,
                        "host" to "127.0.0.1"
                    ))
                }

                // Run server (blocks until stopped)
                Log.i(TAG, "Running server on 127.0.0.1:${BuildConfig.BACKEND_PORT} (this call blocks)...")
                val runServerStart = System.currentTimeMillis()
                mainModule.callAttr("run_server", "127.0.0.1", BuildConfig.BACKEND_PORT)
                val runServerElapsed = System.currentTimeMillis() - runServerStart
                Log.i(TAG, "⏱️  [TIMER] run_server call finished after: ${runServerElapsed}ms")

            } catch (e: Exception) {
                val totalElapsed = System.currentTimeMillis() - totalStartTime
                Log.e(TAG, "❌ Backend error after ${totalElapsed}ms: ${e.message}")
                e.printStackTrace()
                isBackendRunning = false

                withContext(Dispatchers.Main) {
                    result.error(
                        "BACKEND_ERROR",
                        "Failed to start backend: ${e.message}",
                        null
                    )
                }
            }
        }
    }

    /**
     * Stop Python backend server
     */
    private fun stopBackend(result: MethodChannel.Result) {
        if (!isBackendRunning) {
            result.success(mapOf(
                "success" to true,
                "message" to "Backend not running"
            ))
            return
        }

        Log.i(TAG, "Stopping Python backend...")

        try {
            // Cancel the coroutine
            backendJob?.cancel()
            backendJob = null
            isBackendRunning = false

            // Try graceful shutdown via Python
            try {
                val mainModule = python!!.getModule("backend_main")
                mainModule.callAttr("stop_server")
            } catch (e: Exception) {
                Log.w(TAG, "Graceful shutdown failed: ${e.message}")
            }

            result.success(mapOf(
                "success" to true,
                "message" to "Backend stopped successfully"
            ))

            Log.i(TAG, "Backend stopped")

        } catch (e: Exception) {
            Log.e(TAG, "Failed to stop backend: ${e.message}")
            result.error("STOP_ERROR", e.message, null)
        }
    }

    /**
     * Get backend status information
     */
    private fun getBackendStatus(result: MethodChannel.Result) {
        val status = mapOf(
            "isRunning" to isBackendRunning,
            "port" to BuildConfig.BACKEND_PORT,
            "host" to "127.0.0.1",
            "url" to "http://127.0.0.1:${BuildConfig.BACKEND_PORT}",
            "databasePath" to getDatabasePath(),
            "uploadPath" to getUploadPath(),
            "logsPath" to getLogsPath()
        )
        result.success(status)
    }

    /**
     * Restart backend (stop then start)
     */
    private fun restartBackend(result: MethodChannel.Result) {
        Log.i(TAG, "Restarting backend...")

        // Stop first
        stopBackend(object : MethodChannel.Result {
            override fun success(stopResult: Any?) {
                // Then start
                Thread.sleep(1000)  // Wait 1 second
                startBackend(result)
            }

            override fun error(errorCode: String, errorMessage: String?, errorDetails: Any?) {
                result.error(errorCode, errorMessage, errorDetails)
            }

            override fun notImplemented() {
                result.notImplemented()
            }
        })
    }

    /**
     * Setup environment variables for Python
     */
    private fun setupEnvironment() {
        // Set Python environment variables if needed
        val filesDir = applicationContext.filesDir.absolutePath

        System.setProperty("DATA20_DATABASE_PATH", getDatabasePath())
        System.setProperty("DATA20_UPLOAD_PATH", getUploadPath())
        System.setProperty("DATA20_LOGS_PATH", getLogsPath())
    }

    /**
     * Get database file path
     */
    private fun getDatabasePath(): String {
        val dbDir = File(applicationContext.filesDir, "database")
        if (!dbDir.exists()) {
            dbDir.mkdirs()
        }
        return File(dbDir, "data20.db").absolutePath
    }

    /**
     * Get upload directory path
     */
    private fun getUploadPath(): String {
        val uploadDir = File(applicationContext.filesDir, "uploads")
        if (!uploadDir.exists()) {
            uploadDir.mkdirs()
        }
        return uploadDir.absolutePath
    }

    /**
     * Get logs directory path
     */
    private fun getLogsPath(): String {
        val logsDir = File(applicationContext.filesDir, "logs")
        if (!logsDir.exists()) {
            logsDir.mkdirs()
        }
        return logsDir.absolutePath
    }

    override fun onDestroy() {
        super.onDestroy()

        // Stop backend when activity is destroyed
        if (isBackendRunning) {
            stopBackend(object : MethodChannel.Result {
                override fun success(result: Any?) {
                    Log.i(TAG, "Backend stopped on destroy")
                }
                override fun error(errorCode: String, errorMessage: String?, errorDetails: Any?) {}
                override fun notImplemented() {}
            })
        }
    }
}
