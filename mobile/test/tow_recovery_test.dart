import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/recovery/domain/tow_recovery.dart';

void main() {
  test('parses a verified towing recovery result', () {
    final TowLookupResult result = TowLookupResult.fromJson(<String, dynamic>{
      'found': true,
      'message': 'Verified record found.',
      'privacy_notice': 'Identifiers are not retained.',
      'record': <String, dynamic>{
        'tow_company': 'City Tow Services',
        'storage_location': '100 Secure Lot Drive',
        'phone_number': '+1-305-555-0100',
        'business_hours': 'Open 24 hours',
        'required_documents': <String>['Government photo ID'],
        'estimated_fees_cents': 24500,
        'payment_methods': <String>['Credit card'],
        'navigation_url': 'https://maps.example.com/lot',
        'provenance': 'official',
        'confidence': 0.98,
        'last_verified_at': '2026-07-17T12:00:00Z',
      },
    });

    expect(result.found, isTrue);
    expect(result.record?.towCompany, 'City Tow Services');
    expect(result.record?.estimatedFeesCents, 24500);
    expect(result.record?.provenance, 'official');
  });

  test('parses a safe not-found response without a record', () {
    final TowLookupResult result = TowLookupResult.fromJson(<String, dynamic>{
      'found': false,
      'message': 'No verified tow record was found.',
      'privacy_notice': 'Identifiers are not retained.',
      'record': null,
    });

    expect(result.found, isFalse);
    expect(result.record, isNull);
  });
}
