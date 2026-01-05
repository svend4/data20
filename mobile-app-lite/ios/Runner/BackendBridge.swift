//
//  BackendBridge.swift
//  Runner
//
//  Python Backend Bridge for iOS
//  Manages lifecycle of embedded Python FastAPI backend
//

import Foundation
import PythonKit

/**
 * BackendBridge manages the embedded Python backend on iOS
 *
 * This class:
 * - Initializes Python environment
 * - Starts/stops FastAPI server
 * - Manages backend lifecycle
 * - Provides status information
 */
class BackendBridge {

    // MARK: - Properties

    private var pythonModule: PythonObject?
    private var serverThread: Thread?
    private var isRunning: Bool = false

    private let host = "127.0.0.1"
    private let port = 8001

    // Paths
    private var databasePath: String = ""
    private var uploadPath: String = ""
    private var logsPath: String = ""

    // MARK: - Initialization

    init() {
        setupPaths()
        initializePython()
    }

    // MARK: - Setup

    /**
     * Setup file paths for backend storage
     */
    private func setupPaths() {
        let documentsPath = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true)[0]

        // Database
        let dbDir = "\(documentsPath)/database"
        createDirectoryIfNeeded(dbDir)
        databasePath = "\(dbDir)/data20.db"

        // Uploads
        uploadPath = "\(documentsPath)/uploads"
        createDirectoryIfNeeded(uploadPath)

        // Logs
        logsPath = "\(documentsPath)/logs"
        createDirectoryIfNeeded(logsPath)

        print("📁 Paths configured:")
        print("   Database: \(databasePath)")
        print("   Uploads: \(uploadPath)")
        print("   Logs: \(logsPath)")
    }

    /**
     * Create directory if it doesn't exist
     */
    private func createDirectoryIfNeeded(_ path: String) {
        let fileManager = FileManager.default
        if !fileManager.fileExists(atPath: path) {
            try? fileManager.createDirectory(atPath: path, withIntermediateDirectories: true, attributes: nil)
        }
    }

    /**
     * Initialize Python environment
     */
    private func initializePython() {
        do {
            // Set Python home (if using embedded Python)
            if let pythonHome = Bundle.main.path(forResource: "python", ofType: nil) {
                setenv("PYTHONHOME", pythonHome, 1)
                print("🐍 Python home set to: \(pythonHome)")
            }

            // Initialize PythonKit
            print("🐍 Initializing Python...")

            // Import sys to configure Python path
            let sys = Python.import("sys")

            // Add custom module paths if needed
            if let resourcePath = Bundle.main.resourcePath {
                let pythonPath = "\(resourcePath)/python"
                sys.path.append(pythonPath)
                print("🐍 Added Python path: \(pythonPath)")
            }

            print("✅ Python initialized successfully")
            print("   Python version: \(sys.version)")

        } catch {
            print("❌ Failed to initialize Python: \(error)")
        }
    }

    // MARK: - Backend Control

    /**
     * Start Python backend server
     *
     * Returns: Result with success status and message
     */
    func startBackend(completion: @escaping (Result<[String: Any], Error>) -> Void) {

        if isRunning {
            completion(.success([
                "success": true,
                "message": "Backend already running"
            ]))
            return
        }

        print("🚀 Starting Python backend...")

        // Run in background thread
        serverThread = Thread {
            do {
                // Import backend module
                guard let backendModule = try? Python.attemptImport("backend_main") else {
                    throw NSError(domain: "BackendBridge", code: 1, userInfo: [
                        NSLocalizedDescriptionKey: "Failed to import backend_main module"
                    ])
                }

                self.pythonModule = backendModule

                // Setup environment
                backendModule.setup_environment(
                    self.databasePath,
                    self.uploadPath,
                    self.logsPath
                )

                print("✅ Environment configured")

                // Mark as running
                self.isRunning = true

                // Notify completion
                DispatchQueue.main.async {
                    completion(.success([
                        "success": true,
                        "message": "Backend started successfully",
                        "host": self.host,
                        "port": self.port,
                        "url": "http://\(self.host):\(self.port)"
                    ]))
                }

                // Run server (blocking)
                print("🌐 Starting FastAPI server on \(self.host):\(self.port)")
                backendModule.run_server(self.host, self.port)

            } catch {
                print("❌ Backend error: \(error)")
                self.isRunning = false

                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }

        serverThread?.start()
    }

    /**
     * Stop Python backend server
     *
     * Returns: Result with success status
     */
    func stopBackend(completion: @escaping (Result<[String: Any], Error>) -> Void) {

        if !isRunning {
            completion(.success([
                "success": true,
                "message": "Backend not running"
            ]))
            return
        }

        print("🛑 Stopping Python backend...")

        do {
            // Call stop_server() on Python module
            if let module = pythonModule {
                module.stop_server()
            }

            // Cancel thread
            serverThread?.cancel()
            serverThread = nil

            isRunning = false

            print("✅ Backend stopped")

            completion(.success([
                "success": true,
                "message": "Backend stopped successfully"
            ]))

        } catch {
            print("❌ Failed to stop backend: \(error)")
            completion(.failure(error))
        }
    }

    /**
     * Restart backend (stop then start)
     */
    func restartBackend(completion: @escaping (Result<[String: Any], Error>) -> Void) {
        print("🔄 Restarting backend...")

        stopBackend { stopResult in
            // Wait 1 second
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                self.startBackend(completion: completion)
            }
        }
    }

    /**
     * Get backend status
     *
     * Returns: Status information dictionary
     */
    func getStatus() -> [String: Any] {
        return [
            "isRunning": isRunning,
            "host": host,
            "port": port,
            "url": "http://\(host):\(port)",
            "databasePath": databasePath,
            "uploadPath": uploadPath,
            "logsPath": logsPath
        ]
    }

    /**
     * Check if backend is running
     */
    func isBackendRunning() -> Bool {
        return isRunning
    }

    // MARK: - Cleanup

    deinit {
        if isRunning {
            stopBackend { _ in
                print("Backend stopped in deinit")
            }
        }
    }
}
