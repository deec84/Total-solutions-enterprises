import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';

class AlertsApi {
  AlertsApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<AlertPreferences> preferences() async {
    final http.Response response =
        await _request('GET', '/api/v1/notifications/preferences');
    if (response.statusCode != 200) throw StateError('preferences failed');
    return AlertPreferences.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<AlertPreferences> updatePreferences({
    required bool enabled,
    required int quietStartHour,
    required int quietEndHour,
    required String timezone,
  }) async {
    final http.Response response = await _request(
      'PUT',
      '/api/v1/notifications/preferences',
      <String, Object>{
        'parking_alerts_enabled': enabled,
        'background_location_enabled': enabled,
        'push_enabled': false,
        'quiet_start_hour': quietStartHour,
        'quiet_end_hour': quietEndHour,
        'timezone': timezone,
      },
    );
    if (response.statusCode != 200) {
      throw StateError('preferences update failed');
    }
    return AlertPreferences.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<AlertDecision> evaluate(double latitude, double longitude) async {
    final http.Response response = await _request(
      'POST',
      '/api/v1/notifications/evaluate-location',
      <String, Object>{'latitude': latitude, 'longitude': longitude},
    );
    if (response.statusCode != 200) {
      throw StateError('location evaluation failed');
    }
    return AlertDecision.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
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
      _ => throw ArgumentError.value(method, 'method'),
    }
        .timeout(const Duration(seconds: 15));
  }
}
