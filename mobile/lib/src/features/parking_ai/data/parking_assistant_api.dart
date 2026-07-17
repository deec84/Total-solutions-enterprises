import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/parking_ai/domain/parking_assessment.dart';

class ParkingAssistantApi {
  ParkingAssistantApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<ParkingAssessment> ask({
    required String question,
    required double latitude,
    required double longitude,
    required bool hasResidentPermit,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final http.Response response = await _client
        .post(
          Uri.parse('$baseUrl/api/v1/ai/parking-assistant'),
          headers: <String, String>{
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(<String, Object>{
            'question': question,
            'latitude': latitude,
            'longitude': longitude,
            'has_resident_permit': hasResidentPermit,
          }),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) throw StateError('assistant unavailable');
    return ParkingAssessment.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
