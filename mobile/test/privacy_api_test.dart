import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:parkshield_mobile/src/features/privacy/data/privacy_api.dart';
import 'package:parkshield_mobile/src/features/privacy/domain/privacy_models.dart';

import 'support/memory_token_store.dart';

void main() {
  test('privacy API records consent, exports data, and deletes account',
      () async {
    final MemoryTokenStore store =
        MemoryTokenStore(accessToken: 'access', refreshToken: 'refresh');
    final List<http.Request> requests = <http.Request>[];
    final PrivacyApi api = PrivacyApi(
      baseUrl: 'https://api.test',
      tokenStore: store,
      client: MockClient((http.Request request) async {
        requests.add(request);
        expect(request.headers['Authorization'], 'Bearer access');
        if (request.method == 'GET') {
          return _json(<Object>[_consent(false)]);
        }
        if (request.method == 'PUT') return _json(_consent(true));
        if (request.method == 'POST') {
          return _json(<String, Object>{
            'request_id': 'request-1',
            'generated_at': '2026-07-17T12:00:00Z',
            'policy_version': 'v1',
            'data': <String, Object>{
              'profile': <String, Object>{'email': 'person@example.com'}
            },
          });
        }
        return http.Response('', 204);
      }),
    );

    final List<PrivacyConsent> consents = await api.consents();
    final PrivacyConsent updated =
        await api.setConsent(ConsentPurpose.productAnalytics, true);
    final AccountDataExport export = await api.exportData();
    await api.deleteAccount(password: 'secure-password', mfaCode: '123456');

    expect(consents.single.granted, isFalse);
    expect(updated.granted, isTrue);
    expect(export.requestId, 'request-1');
    expect(store.clearCalls, 1);
    expect(requests.map((http.Request item) => item.method),
        <String>['GET', 'PUT', 'POST', 'DELETE']);
    expect(
      jsonDecode(requests[1].body),
      <String, dynamic>{'granted': true},
    );
    expect(
      jsonDecode(requests.last.body),
      <String, dynamic>{
        'password': 'secure-password',
        'confirmation': PrivacyApi.deletionConfirmation,
        'mfa_code': '123456',
      },
    );
    api.close();
  });

  test('privacy API requires a session and never clears tokens after failure',
      () async {
    final MemoryTokenStore missing = MemoryTokenStore();
    final PrivacyApi unauthenticated = PrivacyApi(
      baseUrl: 'https://api.test',
      tokenStore: missing,
      client:
          MockClient((http.Request request) async => http.Response('', 500)),
    );
    await expectLater(unauthenticated.consents(), throwsStateError);

    for (final String method in <String>['GET', 'PUT', 'POST', 'DELETE']) {
      final MemoryTokenStore store = MemoryTokenStore(accessToken: 'access');
      final PrivacyApi api = PrivacyApi(
        baseUrl: 'https://api.test',
        tokenStore: store,
        client:
            MockClient((http.Request request) async => http.Response('', 503)),
      );
      final Future<Object?> action = switch (method) {
        'GET' => api.consents(),
        'PUT' => api.setConsent(ConsentPurpose.communityResearch, true),
        'POST' => api.exportData(),
        _ => api.deleteAccount(password: 'secure-password'),
      };
      await expectLater(action, throwsStateError);
      expect(store.clearCalls, 0);
      api.close();
    }
    unauthenticated.close();
  });
}

Map<String, Object> _consent(bool granted) => <String, Object>{
      'purpose': 'product_analytics',
      'policy_version': 'v1',
      'granted': granted,
      'occurred_at': '2026-07-17T12:00:00Z',
    };

http.Response _json(Object body) => http.Response(
      jsonEncode(body),
      200,
      headers: <String, String>{'content-type': 'application/json'},
    );
