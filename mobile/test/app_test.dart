import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/app.dart';
import 'package:parkshield_mobile/src/core/config/app_config.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class FakeAuthGateway implements AuthGateway {
  @override
  String get currentRole => 'user';

  @override
  Future<bool> restoreSession() async => false;

  @override
  Future<AuthSession> login(
          {required String email, required String password}) async =>
      const AuthSession(accessToken: 'access', refreshToken: 'refresh');

  @override
  Future<void> register(
      {required String email, required String password}) async {}

  @override
  Future<void> requestPasswordReset(String email) async {}

  @override
  Future<void> resetPassword(
      {required String token, required String newPassword}) async {}

  @override
  Future<void> verifyEmail(String token) async {}

  @override
  Future<void> logout() async {}
}

void main() {
  testWidgets('renders the application shell', (WidgetTester tester) async {
    await tester.pumpWidget(
      ParkShieldApp(
        config: const AppConfig(apiBaseUrl: 'https://api.test'),
        authGateway: FakeAuthGateway(),
        linkStream: const Stream<Uri>.empty(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('ParkShield AI'), findsOneWidget);
    expect(find.byIcon(Icons.shield_outlined), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
