import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StorageService {
  late SharedPreferences _prefs;
  final _secureStorage = const FlutterSecureStorage();

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Regular storage (non-sensitive data)
  Future<void> setString(String key, String value) async {
    await _prefs.setString(key, value);
  }

  String? getString(String key) {
    return _prefs.getString(key);
  }

  Future<void> setBool(String key, bool value) async {
    await _prefs.setBool(key, value);
  }

  bool? getBool(String key) {
    return _prefs.getBool(key);
  }

  Future<void> setInt(String key, int value) async {
    await _prefs.setInt(key, value);
  }

  int? getInt(String key) {
    return _prefs.getInt(key);
  }

  Future<void> remove(String key) async {
    await _prefs.remove(key);
  }

  Future<void> clear() async {
    await _prefs.clear();
  }

  // Secure storage (sensitive data like tokens)
  Future<void> setSecure(String key, String value) async {
    await _secureStorage.write(key: key, value: value);
  }

  Future<String?> getSecure(String key) async {
    return await _secureStorage.read(key: key);
  }

  Future<void> deleteSecure(String key) async {
    await _secureStorage.delete(key: key);
  }

  Future<void> clearSecure() async {
    await _secureStorage.deleteAll();
  }

  // Token management
  Future<void> setAccessToken(String token) async {
    await setSecure('access_token', token);
  }

  Future<String?> getAccessToken() async {
    return await getSecure('access_token');
  }

  Future<void> setRefreshToken(String token) async {
    await setSecure('refresh_token', token);
  }

  Future<String?> getRefreshToken() async {
    return await getSecure('refresh_token');
  }

  Future<void> clearTokens() async {
    await deleteSecure('access_token');
    await deleteSecure('refresh_token');
  }

  // Backend URL configuration
  String get backendUrl {
    return getString('backend_url') ?? 'http://localhost:8001';
  }

  Future<void> setBackendUrl(String url) async {
    await setString('backend_url', url);
  }
}
