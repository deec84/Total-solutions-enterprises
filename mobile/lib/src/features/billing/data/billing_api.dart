import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/billing/domain/billing_models.dart';

class BillingApi implements BillingGateway {
  BillingApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  @override
  void close() => _client.close();

  @override
  Future<BillingConfiguration> configuration() async {
    final http.Response response =
        await _request('GET', '/api/v1/billing/configuration');
    if (response.statusCode != 200) {
      throw StateError('billing configuration request failed');
    }
    return BillingConfiguration.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  @override
  Future<EntitlementStatus> entitlement() async {
    final http.Response response =
        await _request('GET', '/api/v1/billing/entitlement');
    if (response.statusCode != 200) {
      throw StateError('entitlement request failed');
    }
    return EntitlementStatus.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  @override
  Future<EntitlementStatus> verify(StorePurchaseEvidence evidence) async {
    final http.Response response = await _request(
      'POST',
      '/api/v1/billing/purchases/verify',
      <String, Object>{
        'platform': evidence.platform.apiValue,
        'product_id': evidence.productId,
        'signed_payload': evidence.signedPayload,
      },
    );
    if (response.statusCode != 200) {
      throw StateError('store purchase verification failed');
    }
    return EntitlementStatus.fromJson(
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
      'POST' => _client.post(uri, headers: headers, body: jsonEncode(body)),
      _ => throw ArgumentError.value(method, 'method'),
    }
        .timeout(const Duration(seconds: 15));
  }
}
