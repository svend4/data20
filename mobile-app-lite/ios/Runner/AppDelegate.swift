import UIKit
import Flutter

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {

    // Backend bridge instance
    private var backendBridge: BackendBridge?

    // Method channel name (must match Android)
    private let CHANNEL = "com.data20/backend"

    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {

        // Initialize Flutter
        let controller: FlutterViewController = window?.rootViewController as! FlutterViewController

        // Setup method channel for Flutter <-> Native communication
        let methodChannel = FlutterMethodChannel(
            name: CHANNEL,
            binaryMessenger: controller.binaryMessenger
        )

        // Initialize backend bridge
        backendBridge = BackendBridge()

        // Handle method calls from Flutter
        methodChannel.setMethodCallHandler { [weak self] (call: FlutterMethodCall, result: @escaping FlutterResult) in

            guard let self = self else {
                result(FlutterError(code: "UNAVAILABLE", message: "AppDelegate not available", details: nil))
                return
            }

            switch call.method {
            case "startBackend":
                self.startBackend(result: result)

            case "stopBackend":
                self.stopBackend(result: result)

            case "isBackendRunning":
                let isRunning = self.backendBridge?.isBackendRunning() ?? false
                result(isRunning)

            case "getBackendStatus":
                self.getBackendStatus(result: result)

            case "restartBackend":
                self.restartBackend(result: result)

            default:
                result(FlutterMethodNotImplemented)
            }
        }

        GeneratedPluginRegistrant.register(with: self)
        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }

    // MARK: - Method Channel Handlers

    /**
     * Start backend
     */
    private func startBackend(result: @escaping FlutterResult) {
        backendBridge?.startBackend { [weak self] backendResult in
            switch backendResult {
            case .success(let data):
                result(data)

            case .failure(let error):
                result(FlutterError(
                    code: "BACKEND_ERROR",
                    message: "Failed to start backend: \(error.localizedDescription)",
                    details: nil
                ))
            }
        }
    }

    /**
     * Stop backend
     */
    private func stopBackend(result: @escaping FlutterResult) {
        backendBridge?.stopBackend { backendResult in
            switch backendResult {
            case .success(let data):
                result(data)

            case .failure(let error):
                result(FlutterError(
                    code: "STOP_ERROR",
                    message: "Failed to stop backend: \(error.localizedDescription)",
                    details: nil
                ))
            }
        }
    }

    /**
     * Get backend status
     */
    private func getBackendStatus(result: @escaping FlutterResult) {
        let status = backendBridge?.getStatus() ?? [:]
        result(status)
    }

    /**
     * Restart backend
     */
    private func restartBackend(result: @escaping FlutterResult) {
        backendBridge?.restartBackend { backendResult in
            switch backendResult {
            case .success(let data):
                result(data)

            case .failure(let error):
                result(FlutterError(
                    code: "RESTART_ERROR",
                    message: "Failed to restart backend: \(error.localizedDescription)",
                    details: nil
                ))
            }
        }
    }

    // MARK: - App Lifecycle

    override func applicationWillTerminate(_ application: UIApplication) {
        // Stop backend when app terminates
        backendBridge?.stopBackend { _ in
            print("Backend stopped on app termination")
        }
    }

    override func applicationDidEnterBackground(_ application: UIApplication) {
        // Optionally stop backend when app goes to background
        // Uncomment if you want to stop backend in background
        // backendBridge?.stopBackend { _ in
        //     print("Backend stopped in background")
        // }
    }

    override func applicationWillEnterForeground(_ application: UIApplication) {
        // Optionally restart backend when app comes to foreground
        // Uncomment if you stopped it in background
        // backendBridge?.startBackend { _ in }
    }
}
