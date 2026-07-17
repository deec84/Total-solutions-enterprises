import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/recovery/domain/tow_recovery.dart';

class TowRecoveryApi {
  TowRecoveryApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<TowLookupResult> lookup({
    required String state,
    required String licensePlate,
    String? vinLastSix,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final http.Response response = await _client
        .post(
          Uri.parse('$baseUrl/api/v1/recovery/lookup'),
          headers: <String, String>{
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(<String, Object?>{
            'state': state,
            'license_plate': licensePlate,
            'vin_last_six': vinLastSix,
          }),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw StateError('towing lookup unavailable');
    }
    return TowLookupResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
