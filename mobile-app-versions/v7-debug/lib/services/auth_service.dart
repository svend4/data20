import 'package:flutter/foundation.dart';
import '../models/user.dart';
import 'api_service.dart';
import 'storage_service.dart';

class AuthService extends ChangeNotifier {
  final ApiService _apiService;
  final StorageService _storageService;

  User? _user;
  bool _isLoading = false;

  AuthService(this._apiService, this._storageService);

  User? get user => _user;
  bool get isAuthenticated => _user != null;
  bool get isLoading => _isLoading;

  Future<void> checkAuth() async {
    final token = await _storageService.getAccessToken();
    if (token != null) {
      _apiService.setAccessToken(token);
      try {
        _user = await _apiService.getCurrentUser();
        notifyListeners();
      } catch (e) {
        // Token is invalid, clear it
        await logout();
      }
    }
  }

  Future<void> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiService.login(username, password);

      final accessToken = response['access_token'];
      final refreshToken = response['refresh_token'];

      await _storageService.setAccessToken(accessToken);
      await _storageService.setRefreshToken(refreshToken);

      _apiService.setAccessToken(accessToken);

      _user = await _apiService.getCurrentUser();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> register({
    required String username,
    required String email,
    required String password,
    String? fullName,
  }) async {
    _isLoading = true;
    notifyListeners();

    try {
      await _apiService.register(
        username: username,
        email: email,
        password: password,
        fullName: fullName,
      );
      // User registered successfully, but not logged in yet
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    _user = null;
    _apiService.setAccessToken(null);
    await _storageService.clearTokens();
    notifyListeners();
  }

  void setBackendUrl(String url) {
    _apiService.setBaseUrl(url);
    _storageService.setBackendUrl(url);
  }

  Future<bool> checkBackendConnection() async {
    return await _apiService.checkHealth();
  }
}
