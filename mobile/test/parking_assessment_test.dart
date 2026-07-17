import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/parking_ai/domain/parking_assessment.dart';

void main() {
  test('parses assistant provenance, confidence, and reasons', () {
    final ParkingAssessment assessment =
        ParkingAssessment.fromJson(<String, dynamic>{
      'answer': 'Do not park here.',
      'interpreted_intent': 'parking_legality',
      'parking_score': 0,
      'risk_level': 'do_not_park',
      'recommendation': 'do_not_park',
      'provenance': 'official',
      'confidence': 1.0,
      'reasons': <String>['Private property.'],
      'disclaimer': 'Follow official signs.',
      'requires_human_review': false,
    });

    expect(assessment.parkingScore, 0);
    expect(assessment.interpretedIntent, 'parking_legality');
    expect(assessment.provenance, 'official');
    expect(assessment.reasons, contains('Private property.'));
  });
}
