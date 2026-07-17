import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/domain/sign_scan_result.dart';

void main() {
  test('parses the sign scanner API contract', () {
    final SignScanResult result = SignScanResult.fromJson(<String, dynamic>{
      'redacted_text': 'NO PARKING [REDACTED PHONE]',
      'summary': 'Parking is prohibited.',
      'restrictions': <String>['No parking', 'Tow-away zone'],
      'towing_risk_score': 95,
      'confidence': 0.91,
      'requires_human_review': false,
      'disclaimer': 'Verify the physical sign.',
    });

    expect(result.detectedText, contains('[REDACTED PHONE]'));
    expect(result.restrictions, hasLength(2));
    expect(result.towingRiskScore, 95);
    expect(result.confidence, 0.91);
    expect(result.requiresHumanReview, isFalse);
  });
}
