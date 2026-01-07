import 'dart:async';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

/**
 * BackendService - Unified API for embedded Python backend
 *
 * This service provides a Flutter API for controlling the embedded
 * Python FastAPI backend on both Android (Chaquopy) and iOS (PythonKit).
 *
 * Features:
 * - Start/stop backend
 * - Health monitoring
 * - Automatic restart on failures
 * - HTTP client wrapper
 * - Status information
 */
class BackendService {
  // Platform channel (must match native side)
  static const platform = MethodChannel('com.data20/backend');

  // Backend configuration
  static const String baseUrl = 'http://127.0.0.1:8001';
  static const String healthEndpoint = '/health';
  static const int maxHealthCheckAttempts = 120; // 120 seconds (increased for slow initialization)
  static const Duration healthCheckInterval = Duration(seconds: 1);

  // State
  bool _isRunning = false;
  bool _isStarting = false;
  Map<String, dynamic>? _status;

  // Stream controller for status updates
  final _statusController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get statusStream => _statusController.stream;

  // Getters
  bool get isRunning => _isRunning;
  bool get isStarting => _isStarting;
  Map<String, dynamic>? get status => _status;
  String get apiUrl => baseUrl;

  // MARK: - Backend Control

  /**
   * Start embedded backend
   *
   * Returns: true if started successfully, false otherwise
   * Throws: Exception if startup fails
   */
  Future<bool> startBackend() async {
    if (_isRunning) {
      print('⚠️ Backend already running');
      return true;
    }

    if (_isStarting) {
      print('⚠️ Backend already starting');
      return false;
    }

    _isStarting = true;
    _notifyStatus({'status': 'starting'});

    try {
      print('🚀 Starting embedded backend...');

      // Call native method to start backend
      final result = await platform.invokeMethod('startBackend');

      if (result is Map && result['success'] == true) {
        print('✅ Backend start initiated: ${result['message']}');

        // Wait for backend to be ready
        final isReady = await _waitForReady();

        if (isReady) {
          _isRunning = true;
          _isStarting = false;

          // Get full status
          await refreshStatus();

          print('✅ Backend is ready and running');
          _notifyStatus({'status': 'running'});

          return true;
        } else {
          throw Exception('Backend failed to become ready within timeout');
        }
      } else {
        throw Exception('Failed to start backend: ${result['message']}');
      }
    } catch (e) {
      print('❌ Failed to start backend: $e');
      _isRunning = false;
      _isStarting = false;
      _notifyStatus({'status': 'error', 'error': e.toString()});
      rethrow;
    }
  }

  /**
   * Stop embedded backend
   *
   * Returns: true if stopped successfully
   */
  Future<bool> stopBackend() async {
    if (!_isRunning) {
      print('⚠️ Backend not running');
      return true;
    }

    try {
      print('🛑 Stopping backend...');

      final result = await platform.invokeMethod('stopBackend');

      if (result is Map && result['success'] == true) {
        _isRunning = false;
        _status = null;

        print('✅ Backend stopped: ${result['message']}');
        _notifyStatus({'status': 'stopped'});

        return true;
      }

      return false;
    } catch (e) {
      print('❌ Failed to stop backend: $e');
      return false;
    }
  }

  /**
   * Restart backend (stop then start)
   */
  Future<bool> restartBackend() async {
    print('🔄 Restarting backend...');

    try {
      final result = await platform.invokeMethod('restartBackend');

      if (result is Map && result['success'] == true) {
        // Wait for backend to be ready
        final isReady = await _waitForReady();

        if (isReady) {
          _isRunning = true;
          await refreshStatus();

          print('✅ Backend restarted successfully');
          _notifyStatus({'status': 'running'});

          return true;
        }
      }

      return false;
    } catch (e) {
      print('❌ Failed to restart backend: $e');
      return false;
    }
  }

  /**
   * Check if backend is running (from native side)
   */
  Future<bool> checkIsRunning() async {
    try {
      final isRunning = await platform.invokeMethod('isBackendRunning');
      _isRunning = isRunning as bool;
      return _isRunning;
    } catch (e) {
      print('Failed to check backend status: $e');
      return false;
    }
  }

  /**
   * Get backend status information
   */
  Future<Map<String, dynamic>?> refreshStatus() async {
    try {
      final status = await platform.invokeMethod('getBackendStatus');
      _status = Map<String, dynamic>.from(status);
      _notifyStatus(_status!);
      return _status;
    } catch (e) {
      print('Failed to get backend status: $e');
      return null;
    }
  }

  // MARK: - Health Check

  /**
   * Wait for backend to be ready
   *
   * Polls the /health endpoint until it responds or timeout
   */
  Future<bool> _waitForReady({int? maxAttempts}) async {
    final attempts = maxAttempts ?? maxHealthCheckAttempts;

    print('⏳ Waiting for backend to be ready (max ${attempts}s)...');

    for (int i = 0; i < attempts; i++) {
      try {
        final response = await http
            .get(
              Uri.parse('$baseUrl$healthEndpoint'),
              headers: {'Accept': 'application/json'},
            )
            .timeout(Duration(seconds: 2));

        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          print('✅ Backend health check passed: ${data['status']}');
          return true;
        }
      } catch (e) {
        // Not ready yet, wait and retry
        if (i % 10 == 0) {
          print('⏳ Still waiting... (${i}s elapsed)');
        }
      }

      await Future.delayed(healthCheckInterval);
    }

    print('❌ Backend failed to become ready within ${attempts}s');
    return false;
  }

  /**
   * Check backend health
   */
  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl$healthEndpoint'))
          .timeout(Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // MARK: - HTTP Client

  /**
   * Make API request to embedded backend
   *
   * Automatically starts backend if not running
   */
  Future<dynamic> apiRequest(
    String endpoint, {
    String method = 'GET',
    Map<String, String>? headers,
    dynamic body,
    bool autoStart = true,
  }) async {
    // Auto-start backend if needed
    if (!_isRunning && autoStart) {
      print('🚀 Auto-starting backend for API request...');
      await startBackend();
    }

    final uri = Uri.parse('$baseUrl$endpoint');

    http.Response response;
    final requestHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...?headers,
    };

    try {
      switch (method.toUpperCase()) {
        case 'GET':
          response = await http.get(uri, headers: requestHeaders);
          break;

        case 'POST':
          response = await http.post(
            uri,
            headers: requestHeaders,
            body: body != null ? json.encode(body) : null,
          );
          break;

        case 'PUT':
          response = await http.put(
            uri,
            headers: requestHeaders,
            body: body != null ? json.encode(body) : null,
          );
          break;

        case 'DELETE':
          response = await http.delete(uri, headers: requestHeaders);
          break;

        case 'PATCH':
          response = await http.patch(
            uri,
            headers: requestHeaders,
            body: body != null ? json.encode(body) : null,
          );
          break;

        default:
          throw Exception('Unsupported HTTP method: $method');
      }

      // Check response status
      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (response.body.isNotEmpty) {
          return json.decode(response.body);
        } else {
          return null;
        }
      } else {
        throw Exception(
          'API request failed: ${response.statusCode} ${response.reasonPhrase}\n'
          'Body: ${response.body}',
        );
      }
    } catch (e) {
      print('❌ API request failed: $e');
      rethrow;
    }
  }

  /**
   * GET request helper
   */
  Future<dynamic> get(String endpoint, {Map<String, String>? headers}) {
    return apiRequest(endpoint, method: 'GET', headers: headers);
  }

  /**
   * POST request helper
   */
  Future<dynamic> post(
    String endpoint, {
    dynamic body,
    Map<String, String>? headers,
  }) {
    return apiRequest(endpoint, method: 'POST', body: body, headers: headers);
  }

  /**
   * PUT request helper
   */
  Future<dynamic> put(
    String endpoint, {
    dynamic body,
    Map<String, String>? headers,
  }) {
    return apiRequest(endpoint, method: 'PUT', body: body, headers: headers);
  }

  /**
   * DELETE request helper
   */
  Future<dynamic> delete(String endpoint, {Map<String, String>? headers}) {
    return apiRequest(endpoint, method: 'DELETE', headers: headers);
  }

  // MARK: - Status Updates

  /**
   * Notify listeners of status change
   */
  void _notifyStatus(Map<String, dynamic> status) {
    if (!_statusController.isClosed) {
      _statusController.add(status);
    }
  }

  /**
   * Dispose resources
   */
  void dispose() {
    _statusController.close();
  }
}
