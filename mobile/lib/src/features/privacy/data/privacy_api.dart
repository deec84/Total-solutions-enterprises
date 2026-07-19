import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/privacy/domain/privacy_models.dart';

class PrivacyApi implements PrivacyGateway {
  PrivacyApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  static const String deletionConfirmation = 'DELETE MY PARKSHIELD ACCOUNT';

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  @override
  void close() => _client.close();

  @override
  Future<List<PrivacyConsent>> consents() async {
    final http.Response response =
        await _request('GET', '/api/v1/privacy/consents');
    if (response.statusCode != 200) {
      throw StateError('privacy consent request failed');
    }
    return (jsonDecode(response.body) as List<dynamic>)
        .map((dynamic item) =>
            PrivacyConsent.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  @override
  Future<PrivacyConsent> setConsent(
      ConsentPurpose purpose, bool granted) async {
    final http.Response response = await _request(
      'PUT',
      '/api/v1/privacy/consents/${purpose.apiValue}',
      <String, Object>{'granted': granted},
    );
    if (response.statusCode != 200) {
      throw StateError('privacy consent update failed');
    }
    return PrivacyConsent.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  @override
  Future<AccountDataExport> exportData() async {
    final http.Response response =
        await _request('POST', '/api/v1/privacy/export');
    if (response.statusCode != 200) {
      throw StateError('account export failed');
    }
    return AccountDataExport.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  @override
  Future<void> deleteAccount({
    required String password,
    String? mfaCode,
  }) async {
    final Map<String, Object> body = <String, Object>{
      'password': password,
      'confirmation': deletionConfirmation,
      if (mfaCode != null && mfaCode.isNotEmpty) 'mfa_code': mfaCode,
    };
    final http.Response response =
        await _request('DELETE', '/api/v1/privacy/account', body);
    if (response.statusCode != 204) {
      throw StateError('account deletion failed');
    }
    await _tokenStore.clear();
  }

  Future<http.Response> _request(String method, String path,
      [Map<String, Object>? body]) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final Uri uri = Uri.parse('$baseUrl$path');
    final Map<String, String> headers = <String, String>{
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
    return switch (method) {
      'GET' => _client.get(uri, headers: headers),
      'PUT' => _client.put(uri, headers: headers, body: jsonEncode(body)),
      'POST' => _client.post(uri, headers: headers, body: jsonEncode(body)),
      'DELETE' => _client.delete(uri, headers: headers, body: jsonEncode(body)),
      _ => throw ArgumentError.value(method, 'method'),
    }
        .timeout(const Duration(seconds: 15));
  }
}
