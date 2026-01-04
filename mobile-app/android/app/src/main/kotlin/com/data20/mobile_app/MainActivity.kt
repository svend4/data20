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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize Python
        initializePython()
    }

    /**
     * Initialize Python environment
     */
    private fun initializePython() {
        if (!Python.isStarted()) {
            try {
                Python.start(AndroidPlatform(this))
                python = Python.getInstance()
                Log.i(TAG, "Python initialized successfully")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to initialize Python: ${e.message}")
                e.printStackTrace()
            }
        } else {
            python = Python.getInstance()
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

        Log.i(TAG, "Starting Python backend...")

        // Track if we've already sent a result to Flutter
        var resultSent = false

        try {
            backendJob = CoroutineScope(Dispatchers.IO).launch {
                try {
                    Log.i(TAG, "1. Setting up environment...")
                    setupEnvironment()

                    Log.i(TAG, "2. Getting backend_main module...")
                    val mainModule = try {
                        python!!.getModule("backend_main")
                    } catch (e: Exception) {
                        throw Exception("Failed to load backend_main module: ${e.message}")
                    }

                    Log.i(TAG, "3. Setting up Android paths...")
                    try {
                        mainModule.callAttr(
                            "setup_environment",
                            getDatabasePath(),
                            getUploadPath(),
                            getLogsPath()
                        )
                    } catch (e: Exception) {
                        throw Exception("Failed to setup environment: ${e.message}")
                    }

                    // Start server - send success BEFORE run_server
                    // (run_server blocks, so we must notify Flutter first)
                    isBackendRunning = true

                    withContext(Dispatchers.Main) {
                        if (!resultSent) {
                            Log.i(TAG, "✅ Setup complete, notifying Flutter")
                            result.success(mapOf(
                                "success" to true,
                                "message" to "Backend starting...",
                                "port" to 8001,
                                "host" to "127.0.0.1"
                            ))
                            resultSent = true
                        }
                    }

                    // Now run server (this blocks until server stops)
                    Log.i(TAG, "4. Starting FastAPI server on 127.0.0.1:8001...")
                    try {
                        mainModule.callAttr("run_server", "127.0.0.1", 8001)
                        Log.i(TAG, "Server exited normally")
                    } catch (e: Exception) {
                        Log.e(TAG, "Server failed: ${e.message}")
                        e.printStackTrace()
                        isBackendRunning = false
                        // Server failed, but we already sent success
                        // Health check will fail and Flutter will detect the problem
                    }

                } catch (e: Exception) {
                    Log.e(TAG, "Backend error: ${e.message}")
                    e.printStackTrace()
                    isBackendRunning = false

                    withContext(Dispatchers.Main) {
                        if (!resultSent) {
                            result.error(
                                "BACKEND_ERROR",
                                e.message ?: "Unknown error",
                                e.stackTraceToString()
                            )
                            resultSent = true
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to launch backend coroutine: ${e.message}")
            e.printStackTrace()
            if (!resultSent) {
                result.error(
                    "LAUNCH_ERROR",
                    "Failed to launch backend: ${e.message}",
                    e.stackTraceToString()
                )
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
            "port" to 8001,
            "host" to "127.0.0.1",
            "url" to "http://127.0.0.1:8001",
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
