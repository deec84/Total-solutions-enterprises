import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/admin/domain/admin_models.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';

class AdminApi {
  AdminApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<MfaSetup> setupMfa() async {
    final http.Response response =
        await _request('POST', '/api/v1/admin/mfa/setup');
    if (response.statusCode != 200) throw StateError('MFA setup failed');
    return MfaSetup.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> confirmMfa(String code) async {
    final http.Response response = await _request(
      'POST',
      '/api/v1/admin/mfa/confirm',
      body: <String, Object>{'code': code},
    );
    if (response.statusCode != 204) throw StateError('MFA confirmation failed');
  }

  Future<AdminOverview> overview(String code) async {
    final http.Response response = await _request(
      'GET',
      '/api/v1/admin/overview',
      mfaCode: code,
    );
    if (response.statusCode != 200) throw StateError('overview failed');
    return AdminOverview.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<List<ModerationReport>> moderationQueue(String code) async {
    final http.Response response = await _request(
      'GET',
      '/api/v1/reports/moderation',
      mfaCode: code,
    );
    if (response.statusCode != 200) throw StateError('moderation queue failed');
    return (jsonDecode(response.body) as List<dynamic>)
        .map((dynamic item) =>
            ModerationReport.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<AuditIntegrity> auditIntegrity(String code) async {
    final http.Response response = await _request(
      'GET',
      '/api/v1/admin/audit/integrity',
      mfaCode: code,
    );
    if (response.statusCode != 200) {
      throw StateError('audit verification failed');
    }
    return AuditIntegrity.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<void> moderate({
    required String reportId,
    required bool approved,
    required String reason,
    required String mfaCode,
  }) async {
    final http.Response response = await _request(
      'POST',
      '/api/v1/reports/$reportId/moderate',
      mfaCode: mfaCode,
      body: <String, Object>{'approved': approved, 'reason': reason},
    );
    if (response.statusCode != 200) throw StateError('moderation failed');
  }

  Future<http.Response> _request(
    String method,
    String path, {
    String? mfaCode,
    Map<String, Object>? body,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final Map<String, String> headers = <String, String>{
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
      if (mfaCode != null) 'X-ParkShield-MFA': mfaCode,
    };
    final Uri uri = Uri.parse('$baseUrl$path');
    return switch (method) {
      'GET' => _client.get(uri, headers: headers),
      'POST' => _client.post(uri,
          headers: headers, body: jsonEncode(body ?? <String, Object>{})),
      _ => throw ArgumentError.value(method, 'method'),
    }
        .timeout(const Duration(seconds: 20));
  }
}
