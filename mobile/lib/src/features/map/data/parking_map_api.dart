import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/map/domain/parking_zone.dart';

class ParkingMapApi {
  ParkingMapApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<List<ParkingZone>> viewport({
    required double west,
    required double south,
    required double east,
    required double north,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final Uri uri = Uri.parse('$baseUrl/api/v1/parking/zones').replace(
      queryParameters: <String, String>{
        'west': '$west',
        'south': '$south',
        'east': '$east',
        'north': '$north',
      },
    );
    final http.Response response = await _client.get(uri,
        headers: <String, String>{
          'Authorization': 'Bearer $token'
        }).timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) throw StateError('map data unavailable');
    final Map<String, dynamic> payload =
        jsonDecode(response.body) as Map<String, dynamic>;
    return (payload['zones'] as List<dynamic>)
        .map((dynamic item) =>
            ParkingZone.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<ParkingZone?> decision({
    required double latitude,
    required double longitude,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final Uri uri = Uri.parse('$baseUrl/api/v1/parking/decision').replace(
      queryParameters: <String, String>{
        'latitude': '$latitude',
        'longitude': '$longitude',
      },
    );
    final http.Response response = await _client.get(uri,
        headers: <String, String>{
          'Authorization': 'Bearer $token'
        }).timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw StateError('parking decision unavailable');
    }
    final Map<String, dynamic> payload =
        jsonDecode(response.body) as Map<String, dynamic>;
    final Object? zone = payload['zone'];
    return zone is Map<String, dynamic> ? ParkingZone.fromJson(zone) : null;
  }
}
