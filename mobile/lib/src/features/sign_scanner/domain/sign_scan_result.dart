class SignScanResult {
  const SignScanResult({
    required this.detectedText,
    required this.summary,
    required this.restrictions,
    required this.towingRiskScore,
    required this.confidence,
    required this.requiresHumanReview,
    required this.disclaimer,
  });

  factory SignScanResult.fromJson(Map<String, dynamic> json) => SignScanResult(
        detectedText: json['redacted_text'] as String,
        summary: json['summary'] as String,
        restrictions: (json['restrictions'] as List<dynamic>).cast<String>(),
        towingRiskScore: json['towing_risk_score'] as int,
        confidence: (json['confidence'] as num).toDouble(),
        requiresHumanReview: json['requires_human_review'] as bool,
        disclaimer: json['disclaimer'] as String,
      );

  final String detectedText;
  final String summary;
  final List<String> restrictions;
  final int towingRiskScore;
  final double confidence;
  final bool requiresHumanReview;
  final String disclaimer;
}
