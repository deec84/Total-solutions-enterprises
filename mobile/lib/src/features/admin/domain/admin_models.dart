class AdminOverview {
  const AdminOverview({
    required this.users,
    required this.activeSessions,
    required this.pendingReports,
    required this.publishedReports,
    required this.rejectedReports,
  });

  factory AdminOverview.fromJson(Map<String, dynamic> json) => AdminOverview(
        users: json['users'] as int,
        activeSessions: json['active_sessions'] as int,
        pendingReports: json['pending_reports'] as int,
        publishedReports: json['published_reports'] as int,
        rejectedReports: json['rejected_reports'] as int,
      );

  final int users;
  final int activeSessions;
  final int pendingReports;
  final int publishedReports;
  final int rejectedReports;
}

class ModerationReport {
  const ModerationReport({
    required this.id,
    required this.category,
    required this.description,
    required this.validationScore,
  });

  factory ModerationReport.fromJson(Map<String, dynamic> json) =>
      ModerationReport(
        id: json['id'] as String,
        category: json['category'] as String,
        description: json['description'] as String,
        validationScore: (json['validation_score'] as num).toDouble(),
      );

  final String id;
  final String category;
  final String description;
  final double validationScore;
}

class MfaSetup {
  const MfaSetup({required this.secret, required this.provisioningUri});

  factory MfaSetup.fromJson(Map<String, dynamic> json) => MfaSetup(
        secret: json['secret'] as String,
        provisioningUri: json['provisioning_uri'] as String,
      );

  final String secret;
  final String provisioningUri;
}

class AuditIntegrity {
  const AuditIntegrity({required this.valid, required this.recordsChecked});

  factory AuditIntegrity.fromJson(Map<String, dynamic> json) => AuditIntegrity(
        valid: json['valid'] as bool,
        recordsChecked: json['records_checked'] as int,
      );

  final bool valid;
  final int recordsChecked;
}
