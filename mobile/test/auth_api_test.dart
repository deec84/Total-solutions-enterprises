import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:parkshield_mobile/src/features/auth/data/auth_api.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

import 'support/memory_token_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('secure token store persists and clears both session tokens', () async {
    FlutterSecureStorage.setMockInitialValues(<String, String>{});
    final SecureTokenStore store = SecureTokenStore();

    await store.save(
      const AuthSession(accessToken: 'access', refreshToken: 'refresh'),
    );
    expect(await store.readAccessToken(), 'access');
    expect(await store.readRefreshToken(), 'refresh');

    await store.clear();
    expect(await store.readAccessToken(), isNull);
    expect(await store.readRefreshToken(), isNull);
  });

  test('login stores tokens and loads the authoritative profile role',
      () async {
    final MemoryTokenStore store = MemoryTokenStore();
    final List<http.Request> requests = <http.Request>[];
    final AuthApi api = AuthApi(
      baseUrl: 'https://api.test',
      tokenStore: store,
      client: MockClient((http.Request request) async {
        requests.add(request);
        if (request.url.path == '/api/v1/auth/login') {
          expect(jsonDecode(request.body), <String, dynamic>{
            'email': 'person@example.com',
            'password': 'correct-password',
          });
          return _json(<String, Object>{
            'access_token': 'access-1',
            'refresh_token': 'refresh-1',
          });
        }
        expect(request.headers['authorization'], 'Bearer access-1');
        return _json(<String, Object>{'role': 'admin'});
      }),
    );

    final AuthSession session = await api.login(
      email: 'person@example.com',
      password: 'correct-password',
    );

    expect(session.accessToken, 'access-1');
    expect(store.saveCalls, 1);
    expect(api.currentRole, 'admin');
    expect(requests.map((http.Request item) => item.url.path), <String>[
      '/api/v1/auth/login',
      '/api/v1/auth/me',
    ]);
  });

  test('account lifecycle sends every documented authentication contract',
      () async {
    final List<http.Request> requests = <http.Request>[];
    final AuthApi api = AuthApi(
      baseUrl: 'https://api.test',
      tokenStore: MemoryTokenStore(),
      client: MockClient((http.Request request) async {
        requests.add(request);
        return http.Response(
          '',
          request.url.path == '/api/v1/auth/register' ? 201 : 200,
        );
      }),
    );

    await api.register(email: 'new@example.com', password: 'password-123');
    await api.requestPasswordReset('new@example.com');
    await api.verifyEmail('verify-token');
    await api.resetPassword(token: 'reset-token', newPassword: 'new-password');

    expect(requests, hasLength(4));
    expect(
      requests.map((http.Request item) => item.url.path),
      <String>[
        '/api/v1/auth/register',
        '/api/v1/auth/password-reset/request',
        '/api/v1/auth/verify-email',
        '/api/v1/auth/password-reset/confirm',
      ],
    );
    expect(
      jsonDecode(requests.last.body),
      <String, dynamic>{
        'token': 'reset-token',
        'new_password': 'new-password',
      },
    );
  });

  test('restore rotates tokens, loads profile, and rejects failed sessions',
      () async {
    final MemoryTokenStore successfulStore =
        MemoryTokenStore(refreshToken: 'old-refresh');
    final AuthApi successful = AuthApi(
      baseUrl: 'https://api.test',
      tokenStore: successfulStore,
      client: MockClient((http.Request request) async {
        if (request.url.path.endsWith('/refresh')) {
          return _json(<String, Object>{
            'access_token': 'new-access',
            'refresh_token': 'new-refresh',
          });
        }
        return _json(<String, Object>{'role': 'moderator'});
      }),
    );
    expect(await successful.restoreSession(), isTrue);
    expect(successfulStore.refreshToken, 'new-refresh');
    expect(successful.currentRole, 'moderator');

    final MemoryTokenStore missingStore = MemoryTokenStore();
    expect(
      await AuthApi(
        baseUrl: 'https://api.test',
        tokenStore: missingStore,
        client:
            MockClient((http.Request request) async => http.Response('', 500)),
      ).restoreSession(),
      isFalse,
    );

    final MemoryTokenStore rejectedStore =
        MemoryTokenStore(refreshToken: 'rejected');
    expect(
      await AuthApi(
        baseUrl: 'https://api.test',
        tokenStore: rejectedStore,
        client:
            MockClient((http.Request request) async => http.Response('', 401)),
      ).restoreSession(),
      isFalse,
    );
    expect(rejectedStore.clearCalls, 1);

    final MemoryTokenStore brokenStore =
        MemoryTokenStore(refreshToken: 'broken');
    expect(
      await AuthApi(
        baseUrl: 'https://api.test',
        tokenStore: brokenStore,
        client: MockClient(
            (http.Request request) async => throw Exception('offline')),
      ).restoreSession(),
      isFalse,
    );
    expect(brokenStore.clearCalls, 1);
  });

  test('logout is best effort and always clears local credentials', () async {
    final MemoryTokenStore store = MemoryTokenStore(
      accessToken: 'access',
      refreshToken: 'refresh',
    );
    final AuthApi api = AuthApi(
      baseUrl: 'https://api.test',
      tokenStore: store,
      client: MockClient(
          (http.Request request) async => throw Exception('offline')),
    );

    await expectLater(api.logout(), throwsException);
    expect(store.clearCalls, 1);

    final MemoryTokenStore emptyStore = MemoryTokenStore();
    await AuthApi(
      baseUrl: 'https://api.test',
      tokenStore: emptyStore,
      client:
          MockClient((http.Request request) async => http.Response('', 500)),
    ).logout();
    expect(emptyStore.clearCalls, 1);
  });

  test('authentication failures expose safe stable client errors', () async {
    for (final String path in <String>[
      '/api/v1/auth/login',
      '/api/v1/auth/register',
      '/api/v1/auth/password-reset/request',
      '/api/v1/auth/verify-email',
      '/api/v1/auth/password-reset/confirm',
      '/api/v1/auth/me',
    ]) {
      final MemoryTokenStore store = MemoryTokenStore();
      final AuthApi api = AuthApi(
        baseUrl: 'https://api.test',
        tokenStore: store,
        client: MockClient((http.Request request) async {
          if (request.url.path == path) return http.Response('', 500);
          return _json(<String, Object>{
            'access_token': 'access',
            'refresh_token': 'refresh',
          });
        }),
      );
      final Future<Object?> action = switch (path) {
        '/api/v1/auth/login' =>
          api.login(email: 'a@b.com', password: 'password'),
        '/api/v1/auth/register' =>
          api.register(email: 'a@b.com', password: 'password'),
        '/api/v1/auth/password-reset/request' =>
          api.requestPasswordReset('a@b.com'),
        '/api/v1/auth/verify-email' => api.verifyEmail('token'),
        '/api/v1/auth/password-reset/confirm' =>
          api.resetPassword(token: 'token', newPassword: 'password'),
        _ => api.login(email: 'a@b.com', password: 'password'),
      };
      await expectLater(action, throwsA(isA<AuthenticationException>()));
    }
  });
}

http.Response _json(Map<String, Object> body, [int status = 200]) =>
    http.Response(
      jsonEncode(body),
      status,
      headers: <String, String>{'content-type': 'application/json'},
    );
