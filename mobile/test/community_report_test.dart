import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/community/domain/community_report.dart';

void main() {
  test('parses community report status and evidence score', () {
    final CommunityReport report = CommunityReport.fromJson(<String, dynamic>{
      'id': 'report-1',
      'status': 'pending',
      'validation_score': 0.7,
      'expires_at': '2026-08-17T12:00:00Z',
    });

    expect(report.status, 'pending');
    expect(report.validationScore, 0.7);
    expect(report.expiresAt.isUtc, isTrue);
  });
}
