import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

abstract interface class TokenStore {
  Future<void> save(AuthSession session);

  Future<String?> readRefreshToken();

  Future<String?> readAccessToken();

  Future<void> clear();
}

class SecureTokenStore implements TokenStore {
  SecureTokenStore({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const String _accessKey = 'parkshield.access_token';
  static const String _refreshKey = 'parkshield.refresh_token';

  final FlutterSecureStorage _storage;

  @override
  Future<void> save(AuthSession session) async {
    await _storage.write(key: _accessKey, value: session.accessToken);
    await _storage.write(key: _refreshKey, value: session.refreshToken);
  }

  @override
  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  @override
  Future<String?> readAccessToken() => _storage.read(key: _accessKey);

  @override
  Future<void> clear() => _storage.deleteAll();
}
