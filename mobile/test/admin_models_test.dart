import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/admin/domain/admin_models.dart';

void main() {
  test('parses administrative overview contract', () {
    final AdminOverview overview = AdminOverview.fromJson(<String, dynamic>{
      'users': 25,
      'active_sessions': 8,
      'pending_reports': 3,
      'published_reports': 40,
      'rejected_reports': 2,
    });
    expect(overview.users, 25);
    expect(overview.pendingReports, 3);
    expect(overview.publishedReports, 40);
  });

  test('parses moderation evidence and MFA setup', () {
    final ModerationReport report = ModerationReport.fromJson(<String, dynamic>{
      'id': 'report-id',
      'category': 'towing',
      'description': 'Tow truck observed',
      'validation_score': 0.7,
    });
    final MfaSetup setup = MfaSetup.fromJson(<String, dynamic>{
      'secret': 'SECRET',
      'provisioning_uri': 'otpauth://totp/example',
    });
    expect(report.validationScore, 0.7);
    expect(setup.provisioningUri, startsWith('otpauth://'));
    final AuditIntegrity integrity = AuditIntegrity.fromJson(<String, dynamic>{
      'valid': true,
      'records_checked': 12,
    });
    expect(integrity.valid, isTrue);
    expect(integrity.recordsChecked, 12);
  });
}
