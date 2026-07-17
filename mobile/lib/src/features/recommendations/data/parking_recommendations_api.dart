import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/recommendations/domain/parking_recommendation.dart';

class ParkingRecommendationsApi {
  ParkingRecommendationsApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<ParkingRecommendationList> nearby({
    required double latitude,
    required double longitude,
    required int radiusMeters,
    int? maxHourlyPriceCents,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final http.Response response = await _client
        .post(
          Uri.parse('$baseUrl/api/v1/recommendations/nearby'),
          headers: <String, String>{
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(<String, Object?>{
            'latitude': latitude,
            'longitude': longitude,
            'radius_meters': radiusMeters,
            'max_hourly_price_cents': maxHourlyPriceCents,
            'limit': 10,
          }),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw StateError('recommendations unavailable');
    }
    return ParkingRecommendationList.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
