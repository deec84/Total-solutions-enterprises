enum StorePlatform {
  appleAppStore('apple_app_store', 'App Store'),
  googlePlay('google_play', 'Google Play');

  const StorePlatform(this.apiValue, this.label);
  final String apiValue;
  final String label;

  static StorePlatform parse(String value) => values.firstWhere(
        (StorePlatform item) => item.apiValue == value,
        orElse: () => throw const FormatException('invalid store platform'),
      );
}

class BillingProduct {
  const BillingProduct({
    required this.platform,
    required this.productId,
    required this.entitlement,
  });

  factory BillingProduct.fromJson(Map<String, dynamic> json) => BillingProduct(
        platform: StorePlatform.parse(json['platform'] as String),
        productId: json['product_id'] as String,
        entitlement: json['entitlement'] as String,
      );

  final StorePlatform platform;
  final String productId;
  final String entitlement;
}

class BillingConfiguration {
  const BillingConfiguration({
    required this.enabled,
    required this.products,
    required this.pricingSource,
  });

  factory BillingConfiguration.fromJson(Map<String, dynamic> json) =>
      BillingConfiguration(
        enabled: json['enabled'] as bool,
        products: (json['products'] as List<dynamic>)
            .map((dynamic item) =>
                BillingProduct.fromJson(item as Map<String, dynamic>))
            .toList(growable: false),
        pricingSource: json['pricing_source'] as String,
      );

  final bool enabled;
  final List<BillingProduct> products;
  final String pricingSource;
}

class EntitlementStatus {
  const EntitlementStatus({
    required this.tier,
    required this.status,
    required this.autoRenews,
    this.platform,
    this.productId,
    this.expiresAt,
    this.lastVerifiedAt,
  });

  factory EntitlementStatus.fromJson(Map<String, dynamic> json) =>
      EntitlementStatus(
        tier: json['tier'] as String,
        status: json['status'] as String,
        platform: json['platform'] == null
            ? null
            : StorePlatform.parse(json['platform'] as String),
        productId: json['product_id'] as String?,
        expiresAt: json['expires_at'] == null
            ? null
            : DateTime.parse(json['expires_at'] as String),
        autoRenews: json['auto_renews'] as bool,
        lastVerifiedAt: json['last_verified_at'] == null
            ? null
            : DateTime.parse(json['last_verified_at'] as String),
      );

  final String tier;
  final String status;
  final StorePlatform? platform;
  final String? productId;
  final DateTime? expiresAt;
  final bool autoRenews;
  final DateTime? lastVerifiedAt;

  bool get premium => tier == 'premium';
}

class StorePurchaseEvidence {
  const StorePurchaseEvidence({
    required this.platform,
    required this.productId,
    required this.signedPayload,
  });

  final StorePlatform platform;
  final String productId;
  final String signedPayload;
}

abstract interface class BillingGateway {
  Future<BillingConfiguration> configuration();
  Future<EntitlementStatus> entitlement();
  Future<EntitlementStatus> verify(StorePurchaseEvidence evidence);
  void close();
}

abstract interface class StorePurchaseBridge {
  bool get available;
  Future<StorePurchaseEvidence?> purchase(BillingProduct product);
  Future<List<StorePurchaseEvidence>> restore();
}

class DisabledStorePurchaseBridge implements StorePurchaseBridge {
  const DisabledStorePurchaseBridge();

  @override
  bool get available => false;

  @override
  Future<StorePurchaseEvidence?> purchase(BillingProduct product) async => null;

  @override
  Future<List<StorePurchaseEvidence>> restore() async =>
      const <StorePurchaseEvidence>[];
}
