import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:parkshield_mobile/src/features/billing/data/billing_api.dart';
import 'package:parkshield_mobile/src/features/billing/domain/billing_models.dart';

import 'support/memory_token_store.dart';

void main() {
  test('billing API loads catalog and entitlement then verifies store evidence',
      () async {
    final List<http.Request> requests = <http.Request>[];
    final BillingApi api = BillingApi(
      baseUrl: 'https://api.test',
      tokenStore: MemoryTokenStore(accessToken: 'access'),
      client: MockClient((http.Request request) async {
        requests.add(request);
        expect(request.headers['Authorization'], 'Bearer access');
        if (request.url.path.endsWith('/configuration')) {
          return _json(<String, Object>{
            'enabled': true,
            'products': <Object>[_product()],
            'pricing_source': 'app_store_or_google_play',
          });
        }
        if (request.url.path.endsWith('/entitlement')) {
          return _json(_entitlement('free'));
        }
        return _json(_entitlement('premium'));
      }),
    );

    final BillingConfiguration configuration = await api.configuration();
    final EntitlementStatus initial = await api.entitlement();
    final EntitlementStatus verified = await api.verify(
      const StorePurchaseEvidence(
        platform: StorePlatform.appleAppStore,
        productId: 'ai.parkshield.synthetic.premium',
        signedPayload: 'SYNTHETIC SIGNED PAYLOAD — NOT A REAL RECEIPT',
      ),
    );

    expect(configuration.enabled, isTrue);
    expect(configuration.products.single.platform, StorePlatform.appleAppStore);
    expect(initial.premium, isFalse);
    expect(verified.premium, isTrue);
    expect(requests.map((http.Request item) => item.method),
        <String>['GET', 'GET', 'POST']);
    expect(
      jsonDecode(requests.last.body),
      <String, dynamic>{
        'platform': 'apple_app_store',
        'product_id': 'ai.parkshield.synthetic.premium',
        'signed_payload': 'SYNTHETIC SIGNED PAYLOAD — NOT A REAL RECEIPT',
      },
    );
    api.close();
  });

  test('billing API requires authentication and fails closed on server errors',
      () async {
    final BillingApi unauthenticated = BillingApi(
      baseUrl: 'https://api.test',
      tokenStore: MemoryTokenStore(),
      client:
          MockClient((http.Request request) async => http.Response('', 500)),
    );
    await expectLater(unauthenticated.entitlement(), throwsStateError);

    final BillingApi failing = BillingApi(
      baseUrl: 'https://api.test',
      tokenStore: MemoryTokenStore(accessToken: 'access'),
      client:
          MockClient((http.Request request) async => http.Response('', 503)),
    );
    await expectLater(failing.configuration(), throwsStateError);
    await expectLater(failing.entitlement(), throwsStateError);
    await expectLater(
      failing.verify(
        const StorePurchaseEvidence(
          platform: StorePlatform.googlePlay,
          productId: 'synthetic',
          signedPayload: 'synthetic',
        ),
      ),
      throwsStateError,
    );
    unauthenticated.close();
    failing.close();
  });
}

Map<String, Object> _product() => <String, Object>{
      'platform': 'apple_app_store',
      'product_id': 'ai.parkshield.synthetic.premium',
      'entitlement': 'premium',
    };

Map<String, Object?> _entitlement(String tier) => <String, Object?>{
      'tier': tier,
      'status': tier == 'premium' ? 'active' : 'inactive',
      'platform': tier == 'premium' ? 'apple_app_store' : null,
      'product_id':
          tier == 'premium' ? 'ai.parkshield.synthetic.premium' : null,
      'expires_at': tier == 'premium' ? '2026-08-17T12:00:00Z' : null,
      'auto_renews': tier == 'premium',
      'last_verified_at': tier == 'premium' ? '2026-07-17T12:00:00Z' : null,
    };

http.Response _json(Object body) => http.Response(
      jsonEncode(body),
      200,
      headers: <String, String>{'content-type': 'application/json'},
    );
