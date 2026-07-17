import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/community/domain/community_report.dart';

class CommunityReportApi {
  CommunityReportApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<CommunityReport> submit({
    required String category,
    required double latitude,
    required double longitude,
    required String description,
    XFile? photo,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    final http.Response response;
    if (photo == null) {
      response = await _client
          .post(
            Uri.parse('$baseUrl/api/v1/reports'),
            headers: <String, String>{
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
            body: jsonEncode(<String, Object>{
              'category': category,
              'latitude': latitude,
              'longitude': longitude,
              'description': description,
            }),
          )
          .timeout(const Duration(seconds: 20));
    } else {
      final List<int> bytes = await photo.readAsBytes();
      if (bytes.length > 10 * 1024 * 1024) {
        throw StateError('image exceeds 10 MB');
      }
      final http.MultipartRequest request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/v1/reports/with-photo'),
      )
        ..headers['Authorization'] = 'Bearer $token'
        ..fields.addAll(<String, String>{
          'category': category,
          'latitude': '$latitude',
          'longitude': '$longitude',
          'description': description,
        })
        ..files.add(
          http.MultipartFile.fromBytes(
            'photo',
            bytes,
            filename: photo.name,
            contentType: MediaType.parse(photo.mimeType ?? 'image/jpeg'),
          ),
        );
      response = await http.Response.fromStream(
        await _client.send(request).timeout(const Duration(seconds: 30)),
      );
    }
    if (response.statusCode != 201) {
      throw StateError('report submission failed');
    }
    return CommunityReport.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
