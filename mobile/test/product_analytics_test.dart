import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/core/analytics/product_analytics.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class FakeTokenStore implements TokenStore {
  FakeTokenStore(this.accessToken);

  String? accessToken;

  @override
  Future<void> clear() async => accessToken = null;

  @override
  Future<String?> readAccessToken() async => accessToken;

  @override
  Future<String?> readRefreshToken() async => null;

  @override
  Future<void> save(AuthSession session) async =>
      accessToken = session.accessToken;
}

void main() {
  test('controller requires feature flag, consent, and allowlisted fields',
      () async {
    final InMemoryAnalyticsProvider provider = InMemoryAnalyticsProvider();
    final ProductAnalyticsController controller = ProductAnalyticsController(
      enabled: true,
      provider: provider,
    );

    expect(
      await controller.track(
        ProductEvent.screenViewed,
        <String, Object>{'screen': 'map'},
      ),
      isFalse,
    );
    controller.updateConsent(true);
    expect(
      await controller.track(
        ProductEvent.screenViewed,
        <String, Object>{'screen': 'map'},
      ),
      isTrue,
    );
    expect(
      await controller.track(
        ProductEvent.screenViewed,
        <String, Object>{'email': 'driver@example.test'},
      ),
      isFalse,
    );
    expect(
      await controller.track(
        ProductEvent.screenViewed,
        <String, Object>{'screen': 'x' * 81},
      ),
      isFalse,
    );
    expect(
        provider.events.single.properties, <String, Object>{'screen': 'map'});
    controller.close();
    expect(provider.events, isEmpty);
  });

  test('memory provider is bounded and disabled provider remains inert',
      () async {
    final InMemoryAnalyticsProvider memory =
        InMemoryAnalyticsProvider(maximumEvents: 1);
    await memory.publish(
        ProductEvent.sessionStarted, <String, Object>{'platform': 'ios'});
    await memory.publish(
        ProductEvent.sessionStarted, <String, Object>{'platform': 'android'});
    const DisabledAnalyticsProvider disabled = DisabledAnalyticsProvider();

    expect(memory.events.single.properties['platform'], 'android');
    expect(
      await disabled.publish(ProductEvent.screenViewed, <String, Object>{}),
      isFalse,
    );
    disabled.close();

    final ProductAnalyticsController off = ProductAnalyticsController(
      enabled: false,
      provider: memory,
    )..updateConsent(true);
    expect(
      await off
          .track(ProductEvent.screenViewed, <String, Object>{'screen': 'map'}),
      isFalse,
    );
  });

  test('backend provider sends only the allowlisted event contract', () async {
    late http.Request captured;
    final MockClient client = MockClient((http.Request request) async {
      captured = request;
      return http.Response(jsonEncode(<String, Object>{'accepted': true}), 202);
    });
    final BackendAnalyticsProvider provider = BackendAnalyticsProvider(
      baseUrl: 'https://api.test',
      tokenStore: FakeTokenStore('access-token'),
      client: client,
    );

    expect(
      await provider.publish(
        ProductEvent.parkingDecisionViewed,
        <String, Object>{'risk_band': 'safe'},
      ),
      isTrue,
    );
    expect(captured.url.path, '/api/v1/analytics/events');
    expect(captured.headers['Authorization'], 'Bearer access-token');
    expect(jsonDecode(captured.body)['name'], 'parking_decision_viewed');
    provider.close();
  });

  test('backend provider fails closed without session or valid response',
      () async {
    final BackendAnalyticsProvider noSession = BackendAnalyticsProvider(
      baseUrl: 'https://api.test',
      tokenStore: FakeTokenStore(null),
      client: MockClient((http.Request _) async => http.Response('{}', 202)),
    );
    final BackendAnalyticsProvider rejected = BackendAnalyticsProvider(
      baseUrl: 'https://api.test',
      tokenStore: FakeTokenStore('access'),
      client: MockClient((http.Request _) async => http.Response('{}', 503)),
    );
    final BackendAnalyticsProvider malformed = BackendAnalyticsProvider(
      baseUrl: 'https://api.test',
      tokenStore: FakeTokenStore('access'),
      client:
          MockClient((http.Request _) async => http.Response('invalid', 202)),
    );

    expect(
      await noSession.publish(ProductEvent.screenViewed, <String, Object>{}),
      isFalse,
    );
    expect(
      await rejected.publish(ProductEvent.screenViewed, <String, Object>{}),
      isFalse,
    );
    expect(
      await malformed.publish(ProductEvent.screenViewed, <String, Object>{}),
      isFalse,
    );
  });
}
