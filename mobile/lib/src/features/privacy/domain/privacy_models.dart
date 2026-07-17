enum ConsentPurpose {
  productAnalytics('product_analytics', 'Product analytics'),
  personalizedRecommendations(
      'personalized_recommendations', 'Personalized recommendations'),
  communityResearch('community_research', 'Community research');

  const ConsentPurpose(this.apiValue, this.label);

  final String apiValue;
  final String label;
}

class PrivacyConsent {
  const PrivacyConsent({
    required this.purpose,
    required this.policyVersion,
    required this.granted,
    required this.occurredAt,
  });

  factory PrivacyConsent.fromJson(Map<String, dynamic> json) => PrivacyConsent(
        purpose: ConsentPurpose.values.firstWhere(
          (ConsentPurpose value) => value.apiValue == json['purpose'],
        ),
        policyVersion: json['policy_version'] as String,
        granted: json['granted'] as bool,
        occurredAt: DateTime.parse(json['occurred_at'] as String),
      );

  final ConsentPurpose purpose;
  final String policyVersion;
  final bool granted;
  final DateTime occurredAt;
}

class AccountDataExport {
  const AccountDataExport({
    required this.requestId,
    required this.generatedAt,
    required this.policyVersion,
    required this.data,
  });

  factory AccountDataExport.fromJson(Map<String, dynamic> json) =>
      AccountDataExport(
        requestId: json['request_id'] as String,
        generatedAt: DateTime.parse(json['generated_at'] as String),
        policyVersion: json['policy_version'] as String,
        data: json['data'] as Map<String, dynamic>,
      );

  final String requestId;
  final DateTime generatedAt;
  final String policyVersion;
  final Map<String, dynamic> data;
}

abstract interface class PrivacyGateway {
  Future<List<PrivacyConsent>> consents();
  Future<PrivacyConsent> setConsent(ConsentPurpose purpose, bool granted);
  Future<AccountDataExport> exportData();
  Future<void> deleteAccount({
    required String password,
    String? mfaCode,
  });
  void close();
}
