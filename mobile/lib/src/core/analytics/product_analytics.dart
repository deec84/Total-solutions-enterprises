import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';

enum ProductEvent {
  screenViewed('screen_viewed'),
  sessionStarted('session_started'),
  signInCompleted('sign_in_completed'),
  parkingDecisionViewed('parking_decision_viewed'),
  parkingRecommendationOpened('parking_recommendation_opened'),
  signScanCompleted('sign_scan_completed'),
  communityReportSubmitted('community_report_submitted'),
  towRecoverySearched('tow_recovery_searched'),
  billingVerificationCompleted('billing_verification_completed');

  const ProductEvent(this.apiValue);
  final String apiValue;
}

const Map<ProductEvent, Set<String>> _allowedProperties =
    <ProductEvent, Set<String>>{
  ProductEvent.screenViewed: <String>{'screen'},
  ProductEvent.sessionStarted: <String>{'platform', 'app_version'},
  ProductEvent.signInCompleted: <String>{'outcome', 'mfa_used'},
  ProductEvent.parkingDecisionViewed: <String>{'risk_band', 'source_level'},
  ProductEvent.parkingRecommendationOpened: <String>{
    'distance_band',
    'price_band'
  },
  ProductEvent.signScanCompleted: <String>{
    'outcome',
    'source_level',
    'restriction_count'
  },
  ProductEvent.communityReportSubmitted: <String>{'report_type', 'outcome'},
  ProductEvent.towRecoverySearched: <String>{'outcome', 'result_band'},
  ProductEvent.billingVerificationCompleted: <String>{'provider', 'outcome'},
};

const Set<String> _prohibitedFragments = <String>{
  'authorization',
  'cookie',
  'credential',
  'email',
  'latitude',
  'location',
  'longitude',
  'message',
  'password',
  'payload',
  'photo',
  'receipt',
  'secret',
  'signed',
  'token',
  'vin',
};

abstract interface class ProductAnalyticsProvider {
  Future<bool> publish(ProductEvent event, Map<String, Object> properties);
  void close();
}

class DisabledAnalyticsProvider implements ProductAnalyticsProvider {
  const DisabledAnalyticsProvider();

  @override
  Future<bool> publish(
          ProductEvent event, Map<String, Object> properties) async =>
      false;

  @override
  void close() {}
}

class InMemoryAnalyticsProvider implements ProductAnalyticsProvider {
  InMemoryAnalyticsProvider({this.maximumEvents = 500});

  final int maximumEvents;
  final List<({ProductEvent event, Map<String, Object> properties})> events =
      <({ProductEvent event, Map<String, Object> properties})>[];

  @override
  Future<bool> publish(
      ProductEvent event, Map<String, Object> properties) async {
    events.add((event: event, properties: Map<String, Object>.of(properties)));
    if (events.length > maximumEvents) {
      events.removeRange(0, events.length - maximumEvents);
    }
    return true;
  }

  @override
  void close() => events.clear();
}

class BackendAnalyticsProvider implements ProductAnalyticsProvider {
  BackendAnalyticsProvider({
    required this.baseUrl,
    required TokenStore tokenStore,
    http.Client? client,
  })  : _tokenStore = tokenStore,
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenStore _tokenStore;
  final http.Client _client;

  @override
  Future<bool> publish(
      ProductEvent event, Map<String, Object> properties) async {
    final String? token = await _tokenStore.readAccessToken();
    if (token == null) return false;
    try {
      final http.Response response = await _client
          .post(
            Uri.parse('$baseUrl/api/v1/analytics/events'),
            headers: <String, String>{
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
            body: jsonEncode(<String, Object>{
              'name': event.apiValue,
              'properties': properties,
            }),
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 202) return false;
      final Object? body = jsonDecode(response.body);
      return body is Map<String, dynamic> && body['accepted'] == true;
    } on Exception {
      return false;
    }
  }

  @override
  void close() => _client.close();
}

class ProductAnalyticsController {
  ProductAnalyticsController({
    required this.enabled,
    required ProductAnalyticsProvider provider,
  }) : _provider = provider;

  final bool enabled;
  final ProductAnalyticsProvider _provider;
  bool _consentGranted = false;

  void updateConsent(bool granted) => _consentGranted = granted;

  Future<bool> track(ProductEvent event, Map<String, Object> properties) async {
    if (!enabled || !_consentGranted || !_valid(event, properties)) {
      return false;
    }
    return _provider.publish(event, properties);
  }

  bool _valid(ProductEvent event, Map<String, Object> properties) {
    if (properties.keys
        .toSet()
        .difference(_allowedProperties[event]!)
        .isNotEmpty) {
      return false;
    }
    for (final MapEntry<String, Object> property in properties.entries) {
      final String key = property.key.toLowerCase().replaceAll('-', '_');
      if (_prohibitedFragments.any(key.contains)) {
        return false;
      }
      final Object value = property.value;
      if (value is! String && value is! num && value is! bool) return false;
      if (value is String && value.length > 80) return false;
    }
    return true;
  }

  void close() => _provider.close();
}
