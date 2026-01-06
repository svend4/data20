import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/tool.dart';
import '../models/job.dart';
import '../models/user.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() => message;
}

class ApiService {
  String _baseUrl = 'http://localhost:8001';
  String? _accessToken;

  void setBaseUrl(String url) {
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  void setAccessToken(String? token) {
    _accessToken = token;
  }

  Map<String, String> _getHeaders({bool includeAuth = true}) {
    final headers = {
      'Content-Type': 'application/json',
    };

    if (includeAuth && _accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }

    return headers;
  }

  Future<dynamic> _handleResponse(http.Response response) async {
    final statusCode = response.statusCode;

    if (statusCode >= 200 && statusCode < 300) {
      if (response.body.isEmpty) return null;
      return json.decode(response.body);
    }

    String errorMessage = 'Ошибка запроса';
    try {
      final errorData = json.decode(response.body);
      errorMessage = errorData['detail'] ?? errorData['message'] ?? errorMessage;
    } catch (_) {
      errorMessage = response.body.isNotEmpty ? response.body : errorMessage;
    }

    throw ApiException(errorMessage, statusCode);
  }

  // Authentication
  Future<Map<String, dynamic>> login(String username, String password) async {
    print('🔵 [API] Starting login request...');
    print('🔵 [API] Base URL: $_baseUrl');
    print('🔵 [API] Username: $username');

    try {
      final uri = Uri.parse('$_baseUrl/auth/login');
      print('🔵 [API] URI parsed: $uri');

      final headers = _getHeaders(includeAuth: false);
      print('🔵 [API] Headers: $headers');

      final bodyData = {
        'username': username,
        'password': password,
      };
      final bodyJson = json.encode(bodyData);
      print('🔵 [API] Request body: $bodyJson');

      print('🔵 [API] Sending POST request...');
      final response = await http.post(
        uri,
        headers: headers,
        body: bodyJson,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          print('🔴 [API] Request timeout after 10 seconds!');
          throw ApiException('Timeout: backend не отвечает');
        },
      );

      print('🔵 [API] Response received!');
      print('🔵 [API] Status code: ${response.statusCode}');
      print('🔵 [API] Response body: ${response.body}');

      final result = await _handleResponse(response);
      print('🟢 [API] Login successful!');
      return result;
    } catch (e, stackTrace) {
      print('🔴 [API] Login error: $e');
      print('🔴 [API] Stack trace: $stackTrace');
      rethrow;
    }
  }

  Future<User> register({
    required String username,
    required String email,
    required String password,
    String? fullName,
  }) async {
    print('🔵 [API] Starting register request...');
    print('🔵 [API] Base URL: $_baseUrl');
    print('🔵 [API] Username: $username, Email: $email');

    try {
      final uri = Uri.parse('$_baseUrl/auth/register');
      print('🔵 [API] URI parsed: $uri');

      final headers = _getHeaders(includeAuth: false);
      print('🔵 [API] Headers: $headers');

      final bodyData = {
        'username': username,
        'email': email,
        'password': password,
        'full_name': fullName,
      };
      final bodyJson = json.encode(bodyData);
      print('🔵 [API] Request body: $bodyJson');

      print('🔵 [API] Sending POST request...');
      final response = await http.post(
        uri,
        headers: headers,
        body: bodyJson,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          print('🔴 [API] Request timeout after 10 seconds!');
          throw ApiException('Timeout: backend не отвечает');
        },
      );

      print('🔵 [API] Response received!');
      print('🔵 [API] Status code: ${response.statusCode}');
      print('🔵 [API] Response body: ${response.body}');

      final data = await _handleResponse(response);
      print('🟢 [API] Register successful!');
      return User.fromJson(data);
    } catch (e, stackTrace) {
      print('🔴 [API] Register error: $e');
      print('🔴 [API] Stack trace: $stackTrace');
      rethrow;
    }
  }

  Future<User> getCurrentUser() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/auth/me'),
      headers: _getHeaders(),
    );

    final data = await _handleResponse(response);
    return User.fromJson(data);
  }

  // Tools
  Future<List<Tool>> getTools() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/tools'),
      headers: _getHeaders(),
    );

    final data = await _handleResponse(response);
    final toolsList = data['tools'] as List;
    return toolsList.map((json) => Tool.fromJson(json)).toList();
  }

  Future<Tool> getTool(String toolName) async {
    final tools = await getTools();
    try {
      return tools.firstWhere((tool) => tool.name == toolName);
    } catch (e) {
      throw ApiException('Инструмент не найден');
    }
  }

  // Jobs
  Future<Map<String, dynamic>> runTool(
    String toolName,
    Map<String, dynamic> parameters,
  ) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/jobs/execute'),
      headers: _getHeaders(),
      body: json.encode({
        'tool_name': toolName,
        'parameters': parameters,
      }),
    );

    return await _handleResponse(response);
  }

  Future<List<Job>> getJobs() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/jobs'),
      headers: _getHeaders(),
    );

    final data = await _handleResponse(response) as List;
    return data.map((json) => Job.fromJson(json)).toList();
  }

  Future<Job> getJob(String jobId) async {
    final response = await http.get(
      Uri.parse('$_baseUrl/jobs/$jobId'),
      headers: _getHeaders(),
    );

    final data = await _handleResponse(response);
    return Job.fromJson(data);
  }

  // Health check
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/health'),
        headers: _getHeaders(includeAuth: false),
      ).timeout(const Duration(seconds: 3));

      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (e) {
      return false;
    }
  }
}
