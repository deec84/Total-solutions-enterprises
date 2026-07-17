import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class AuthenticationException implements Exception {
  const AuthenticationException(this.message);

  final String message;
}

class AuthApi implements AuthGateway {
  AuthApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;
  String _currentRole = 'user';

  @override
  String get currentRole => _currentRole;

  @override
  Future<AuthSession> login(
      {required String email, required String password}) async {
    final http.Response response = await _client
        .post(
          Uri.parse('$baseUrl/api/v1/auth/login'),
          headers: const <String, String>{'Content-Type': 'application/json'},
          body: jsonEncode(
              <String, String>{'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw const AuthenticationException(
          'Unable to sign in. Check your credentials.');
    }
    final Map<String, dynamic> payload =
        jsonDecode(response.body) as Map<String, dynamic>;
    final AuthSession session = AuthSession(
      accessToken: payload['access_token'] as String,
      refreshToken: payload['refresh_token'] as String,
    );
    await _tokenStore.save(session);
    await _loadProfile(session.accessToken);
    return session;
  }

  @override
  Future<void> register(
      {required String email, required String password}) async {
    final http.Response response = await _post(
      '/api/v1/auth/register',
      <String, String>{'email': email, 'password': password},
    );
    if (response.statusCode != 201) {
      throw const AuthenticationException('Unable to create the account.');
    }
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    final http.Response response = await _post(
      '/api/v1/auth/password-reset/request',
      <String, String>{'email': email},
    );
    if (response.statusCode != 200) {
      throw const AuthenticationException(
          'Unable to request password recovery.');
    }
  }

  @override
  Future<void> verifyEmail(String token) async {
    final http.Response response = await _post(
      '/api/v1/auth/verify-email',
      <String, String>{'token': token},
    );
    if (response.statusCode != 200) {
      throw const AuthenticationException(
          'The verification link is invalid or expired.');
    }
  }

  @override
  Future<bool> restoreSession() async {
    final String? refreshToken = await _tokenStore.readRefreshToken();
    if (refreshToken == null) return false;
    try {
      final http.Response response = await _post(
        '/api/v1/auth/refresh',
        <String, String>{'refresh_token': refreshToken},
      );
      if (response.statusCode != 200) {
        await _tokenStore.clear();
        return false;
      }
      await _tokenStore.save(_sessionFromResponse(response));
      final String? accessToken = await _tokenStore.readAccessToken();
      if (accessToken == null) return false;
      await _loadProfile(accessToken);
      return true;
    } on Exception {
      await _tokenStore.clear();
      return false;
    }
  }

  @override
  Future<void> logout() async {
    final String? refreshToken = await _tokenStore.readRefreshToken();
    try {
      if (refreshToken != null) {
        await _post(
          '/api/v1/auth/logout',
          <String, String>{'refresh_token': refreshToken},
        );
      }
    } finally {
      await _tokenStore.clear();
    }
  }

  @override
  Future<void> resetPassword(
      {required String token, required String newPassword}) async {
    final http.Response response = await _post(
      '/api/v1/auth/password-reset/confirm',
      <String, String>{'token': token, 'new_password': newPassword},
    );
    if (response.statusCode != 200) {
      throw const AuthenticationException(
          'The recovery link is invalid or expired.');
    }
  }

  Future<http.Response> _post(String path, Map<String, String> payload) =>
      _client
          .post(
            Uri.parse('$baseUrl$path'),
            headers: const <String, String>{'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 15));

  AuthSession _sessionFromResponse(http.Response response) {
    final Map<String, dynamic> payload =
        jsonDecode(response.body) as Map<String, dynamic>;
    return AuthSession(
      accessToken: payload['access_token'] as String,
      refreshToken: payload['refresh_token'] as String,
    );
  }

  Future<void> _loadProfile(String accessToken) async {
    final http.Response response = await _client.get(
      Uri.parse('$baseUrl/api/v1/auth/me'),
      headers: <String, String>{'Authorization': 'Bearer $accessToken'},
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw const AuthenticationException('Unable to load account profile.');
    }
    final Map<String, dynamic> profile =
        jsonDecode(response.body) as Map<String, dynamic>;
    _currentRole = profile['role'] as String? ?? 'user';
  }
}
