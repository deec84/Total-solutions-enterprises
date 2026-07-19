import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/features/privacy/domain/privacy_models.dart';
import 'package:parkshield_mobile/src/features/privacy/presentation/privacy_page.dart';

class FakePrivacyGateway implements PrivacyGateway {
  bool fail = false;
  int consentUpdates = 0;
  int exportCalls = 0;
  int deletionCalls = 0;
  bool closed = false;

  @override
  Future<List<PrivacyConsent>> consents() async {
    if (fail) throw Exception('failure');
    return <PrivacyConsent>[
      PrivacyConsent(
        purpose: ConsentPurpose.productAnalytics,
        policyVersion: 'v1',
        granted: false,
        occurredAt: DateTime.utc(2026, 7, 17),
      ),
    ];
  }

  @override
  Future<PrivacyConsent> setConsent(
      ConsentPurpose purpose, bool granted) async {
    if (fail) throw Exception('failure');
    consentUpdates += 1;
    return PrivacyConsent(
      purpose: purpose,
      policyVersion: 'v1',
      granted: granted,
      occurredAt: DateTime.utc(2026, 7, 17),
    );
  }

  @override
  Future<AccountDataExport> exportData() async {
    if (fail) throw Exception('failure');
    exportCalls += 1;
    return AccountDataExport(
      requestId: 'request-1',
      generatedAt: DateTime.utc(2026, 7, 17),
      policyVersion: 'v1',
      data: const <String, dynamic>{
        'profile': <String, dynamic>{'email': 'person@example.com'}
      },
    );
  }

  @override
  Future<void> deleteAccount(
      {required String password, String? mfaCode}) async {
    if (fail) throw Exception('failure');
    deletionCalls += 1;
  }

  @override
  void close() => closed = true;
}

void main() {
  testWidgets('privacy page saves choices, exports, and confirms deletion',
      (WidgetTester tester) async {
    final FakePrivacyGateway gateway = FakePrivacyGateway();
    bool accountDeleted = false;
    await _pump(
      tester,
      PrivacyPage(
        apiBaseUrl: 'https://api.test',
        gateway: gateway,
        onAccountDeleted: () => accountDeleted = true,
      ),
    );

    expect(find.text('Privacy and your data'), findsOneWidget);
    await tester.tap(find.byType(Switch).first);
    await tester.pumpAndSettle();
    expect(find.text('Product analytics preference saved.'), findsOneWidget);
    expect(gateway.consentUpdates, 1);

    await tester.tap(find.text('Create data export'));
    await tester.pumpAndSettle();
    expect(find.text('Your data export is ready.'), findsOneWidget);
    expect(find.text('Copy export JSON'), findsOneWidget);
    expect(find.textContaining('person@example.com'), findsOneWidget);
    await tester.ensureVisible(find.text('Copy export JSON'));
    await tester.tap(find.text('Copy export JSON'));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('Permanently delete account'));
    await tester.tap(find.text('Permanently delete account'));
    await tester.pump();
    expect(find.text('Enter your current password first.'), findsOneWidget);

    await tester.ensureVisible(find.byType(TextField).first);
    await tester.enterText(find.byType(TextField).first, 'secure-password');
    await tester.tap(find.text('Permanently delete account'));
    await tester.pumpAndSettle();
    expect(find.text('Delete your ParkShield account?'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(gateway.deletionCalls, 0);

    await tester.tap(find.text('Permanently delete account'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete permanently'));
    await tester.pumpAndSettle();
    expect(gateway.deletionCalls, 1);
    expect(accountDeleted, isTrue);
  });

  testWidgets('privacy page reports provider failures without deleting account',
      (WidgetTester tester) async {
    final FakePrivacyGateway gateway = FakePrivacyGateway()..fail = true;
    await _pump(
      tester,
      PrivacyPage(apiBaseUrl: 'https://api.test', gateway: gateway),
    );
    expect(find.text('Privacy choices could not be loaded.'), findsOneWidget);

    await tester.tap(find.byType(Switch).first);
    await tester.pumpAndSettle();
    expect(find.text('The privacy choice could not be saved.'), findsOneWidget);
    await tester.tap(find.text('Create data export'));
    await tester.pumpAndSettle();
    expect(find.text('Your data export could not be created.'), findsOneWidget);

    await tester.ensureVisible(find.byType(TextField).first);
    await tester.enterText(find.byType(TextField).first, 'secure-password');
    await tester.tap(find.text('Permanently delete account'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete permanently'));
    await tester.pumpAndSettle();
    expect(
      find.text(
          'The account was not deleted. Verify your password, MFA code, and connection.'),
      findsOneWidget,
    );
    expect(gateway.deletionCalls, 0);
  });
}

Future<void> _pump(WidgetTester tester, Widget child) async {
  await tester.binding.setSurfaceSize(const Size(1200, 1800));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: ThemeData(splashFactory: InkRipple.splashFactory),
      home: Scaffold(body: child),
    ),
  );
  await tester.pumpAndSettle();
}
