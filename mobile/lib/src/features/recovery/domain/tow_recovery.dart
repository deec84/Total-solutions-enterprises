class TowRecord {
  const TowRecord({
    required this.towCompany,
    required this.storageLocation,
    required this.phoneNumber,
    required this.businessHours,
    required this.requiredDocuments,
    required this.estimatedFeesCents,
    required this.paymentMethods,
    required this.navigationUrl,
    required this.provenance,
    required this.confidence,
    required this.lastVerifiedAt,
  });

  factory TowRecord.fromJson(Map<String, dynamic> json) => TowRecord(
        towCompany: json['tow_company'] as String,
        storageLocation: json['storage_location'] as String,
        phoneNumber: json['phone_number'] as String,
        businessHours: json['business_hours'] as String,
        requiredDocuments:
            (json['required_documents'] as List<dynamic>).cast<String>(),
        estimatedFeesCents: json['estimated_fees_cents'] as int?,
        paymentMethods:
            (json['payment_methods'] as List<dynamic>).cast<String>(),
        navigationUrl: json['navigation_url'] as String,
        provenance: json['provenance'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        lastVerifiedAt: DateTime.parse(json['last_verified_at'] as String),
      );

  final String towCompany;
  final String storageLocation;
  final String phoneNumber;
  final String businessHours;
  final List<String> requiredDocuments;
  final int? estimatedFeesCents;
  final List<String> paymentMethods;
  final String navigationUrl;
  final String provenance;
  final double confidence;
  final DateTime lastVerifiedAt;
}

class TowLookupResult {
  const TowLookupResult({
    required this.found,
    required this.message,
    required this.record,
    required this.privacyNotice,
  });

  factory TowLookupResult.fromJson(Map<String, dynamic> json) =>
      TowLookupResult(
        found: json['found'] as bool,
        message: json['message'] as String,
        record: json['record'] == null
            ? null
            : TowRecord.fromJson(json['record'] as Map<String, dynamic>),
        privacyNotice: json['privacy_notice'] as String,
      );

  final bool found;
  final String message;
  final TowRecord? record;
  final String privacyNotice;
}
