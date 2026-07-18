import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/billing/domain/billing_models.dart';
import 'package:parkshield_mobile/src/features/billing/presentation/membership_page.dart';

class FakeBillingGateway implements BillingGateway {
  FakeBillingGateway({this.enabled = true});

  bool enabled;
  bool fail = false;
  int verifyCalls = 0;
  bool closed = false;
  EntitlementStatus current = const EntitlementStatus(
    tier: 'free',
    status: 'inactive',
    autoRenews: false,
  );

  @override
  Future<BillingConfiguration> configuration() async {
    if (fail) throw Exception('synthetic failure');
    return BillingConfiguration(
      enabled: enabled,
      products: const <BillingProduct>[
        BillingProduct(
          platform: StorePlatform.appleAppStore,
          productId: 'ai.parkshield.synthetic.premium',
          entitlement: 'premium',
        ),
      ],
      pricingSource: 'app_store_or_google_play',
    );
  }

  @override
  Future<EntitlementStatus> entitlement() async {
    if (fail) throw Exception('synthetic failure');
    return current;
  }

  @override
  Future<EntitlementStatus> verify(StorePurchaseEvidence evidence) async {
    if (fail) throw Exception('synthetic failure');
    verifyCalls += 1;
    current = EntitlementStatus(
      tier: 'premium',
      status: 'active',
      platform: evidence.platform,
      productId: evidence.productId,
      expiresAt: DateTime.utc(2026, 8, 17),
      autoRenews: true,
      lastVerifiedAt: DateTime.utc(2026, 7, 17),
    );
    return current;
  }

  @override
  void close() => closed = true;
}

class FakeStorePurchaseBridge implements StorePurchaseBridge {
  int purchaseCalls = 0;
  int restoreCalls = 0;

  @override
  bool get available => true;

  @override
  Future<StorePurchaseEvidence?> purchase(BillingProduct product) async {
    purchaseCalls += 1;
    return StorePurchaseEvidence(
      platform: product.platform,
      productId: product.productId,
      signedPayload: 'SYNTHETIC PAYLOAD — NOT A REAL RECEIPT',
    );
  }

  @override
  Future<List<StorePurchaseEvidence>> restore() async {
    restoreCalls += 1;
    return const <StorePurchaseEvidence>[
      StorePurchaseEvidence(
        platform: StorePlatform.appleAppStore,
        productId: 'ai.parkshield.synthetic.premium',
        signedPayload: 'SYNTHETIC RESTORE — NOT A REAL RECEIPT',
      ),
    ];
  }
}

void main() {
  testWidgets('membership page never offers a charge while billing is disabled',
      (WidgetTester tester) async {
    final FakeBillingGateway gateway = FakeBillingGateway(enabled: false);
    await _pump(
      tester,
      MembershipPage(apiBaseUrl: 'https://api.test', gateway: gateway),
    );

    expect(find.text('ParkShield Free'), findsOneWidget);
    expect(
      find.text(
          'Purchases are not available in this build. No charge can be initiated.'),
      findsOneWidget,
    );
    expect(find.textContaining('Continue in'), findsNothing);
  });

  testWidgets(
      'membership page verifies synthetic purchase and restore evidence',
      (WidgetTester tester) async {
    final FakeBillingGateway gateway = FakeBillingGateway();
    final FakeStorePurchaseBridge bridge = FakeStorePurchaseBridge();
    await _pump(
      tester,
      MembershipPage(
        apiBaseUrl: 'https://api.test',
        gateway: gateway,
        storeBridge: bridge,
      ),
    );

    await tester.tap(find.text('Continue in App Store'));
    await tester.pumpAndSettle();
    expect(find.text('ParkShield Premium'), findsOneWidget);
    expect(find.text('Membership verified by the store.'), findsOneWidget);
    expect(bridge.purchaseCalls, 1);
    expect(gateway.verifyCalls, 1);

    await tester.tap(find.text('Restore store purchases'));
    await tester.pumpAndSettle();
    expect(find.text('Store purchases were restored and verified.'),
        findsOneWidget);
    expect(bridge.restoreCalls, 1);
    expect(gateway.verifyCalls, 2);
  });

  testWidgets('membership page fails closed when verification is unavailable',
      (WidgetTester tester) async {
    final FakeBillingGateway gateway = FakeBillingGateway();
    final FakeStorePurchaseBridge bridge = FakeStorePurchaseBridge();
    await _pump(
      tester,
      MembershipPage(
        apiBaseUrl: 'https://api.test',
        gateway: gateway,
        storeBridge: bridge,
      ),
    );
    gateway.fail = true;
    await tester.tap(find.text('Continue in App Store'));
    await tester.pumpAndSettle();
    expect(
      find.text(
          'The store purchase could not be verified. No access was granted.'),
      findsOneWidget,
    );
    expect(find.text('ParkShield Free'), findsOneWidget);
  });
}

Future<void> _pump(WidgetTester tester, Widget child) async {
  await tester.binding.setSurfaceSize(const Size(1200, 1800));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      theme: ThemeData(splashFactory: InkRipple.splashFactory),
      home: Scaffold(body: child),
    ),
  );
  await tester.pumpAndSettle();
}
