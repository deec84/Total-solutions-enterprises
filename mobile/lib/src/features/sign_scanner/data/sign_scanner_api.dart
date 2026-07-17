import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/domain/sign_scan_result.dart';

class SignScannerApi {
  SignScannerApi({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  void close() => _client.close();

  Future<SignScanResult> scan({
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) throw StateError('authenticated session required');
    if (bytes.length > 10 * 1024 * 1024) {
      throw StateError('image exceeds 10 MB');
    }
    final http.MultipartRequest request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/v1/signs/scan'),
    )
      ..headers['Authorization'] = 'Bearer $token'
      ..files.add(
        http.MultipartFile.fromBytes(
          'image',
          bytes,
          filename: filename,
          contentType: _mediaType(contentType),
        ),
      );
    final http.StreamedResponse streamed = await _client.send(request).timeout(
          const Duration(seconds: 30),
        );
    final http.Response response = await http.Response.fromStream(streamed);
    if (response.statusCode != 200) throw StateError('sign scan failed');
    return SignScanResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  MediaType _mediaType(String value) {
    final List<String> parts = value.split('/');
    return MediaType(parts[0], parts.length > 1 ? parts[1] : 'jpeg');
  }
}
