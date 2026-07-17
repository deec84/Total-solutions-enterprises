class CommunityReport {
  const CommunityReport({
    required this.id,
    required this.status,
    required this.validationScore,
    required this.expiresAt,
  });

  factory CommunityReport.fromJson(Map<String, dynamic> json) =>
      CommunityReport(
        id: json['id'] as String,
        status: json['status'] as String,
        validationScore: (json['validation_score'] as num).toDouble(),
        expiresAt: DateTime.parse(json['expires_at'] as String),
      );

  final String id;
  final String status;
  final double validationScore;
  final DateTime expiresAt;
}
