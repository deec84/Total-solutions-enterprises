import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/app.dart';
import 'package:parkshield_mobile/src/core/config/app_config.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class SignedOutGateway implements AuthGateway {
  @override
  String get currentRole => 'user';

  @override
  Future<bool> restoreSession() async => false;

  @override
  Future<AuthSession> login(
          {required String email, required String password}) async =>
      const AuthSession(
        accessToken: 'test-access-token',
        refreshToken: 'test-refresh-token',
      );

  @override
  Future<void> logout() async {}

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
}

void main() {
  for (final Locale locale in const <Locale>[Locale('en'), Locale('es')]) {
    testWidgets(
        'authentication surface meets contrast and target-size guidelines in ${locale.languageCode}',
        (WidgetTester tester) async {
      final SemanticsHandle semantics = tester.ensureSemantics();
      await tester.pumpWidget(
        ParkShieldApp(
          config: const AppConfig(apiBaseUrl: 'https://api.test'),
          authGateway: SignedOutGateway(),
          linkStream: const Stream<Uri>.empty(),
          locale: locale,
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(TextField), findsNWidgets(2));
      await expectLater(tester, meetsGuideline(textContrastGuideline));
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
      semantics.dispose();
    });
  }

  testWidgets('Spanish locale and 200 percent text scale remain usable',
      (WidgetTester tester) async {
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.binding.setSurfaceSize(const Size(430, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      ParkShieldApp(
        config: const AppConfig(apiBaseUrl: 'https://api.test'),
        authGateway: SignedOutGateway(),
        linkStream: const Stream<Uri>.empty(),
        locale: const Locale('es'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Estaciona con confianza'), findsOneWidget);
    expect(find.text('Iniciar sesión'), findsOneWidget);
    expect(find.bySemanticsLabel('Correo electrónico'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
