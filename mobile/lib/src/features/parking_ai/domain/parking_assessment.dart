class ParkingAssessment {
  const ParkingAssessment({
    required this.answer,
    required this.interpretedIntent,
    required this.parkingScore,
    required this.riskLevel,
    required this.recommendation,
    required this.provenance,
    required this.confidence,
    required this.reasons,
    required this.disclaimer,
    required this.requiresHumanReview,
  });

  factory ParkingAssessment.fromJson(Map<String, dynamic> json) =>
      ParkingAssessment(
        answer: json['answer'] as String,
        interpretedIntent: json['interpreted_intent'] as String,
        parkingScore: json['parking_score'] as int,
        riskLevel: json['risk_level'] as String,
        recommendation: json['recommendation'] as String,
        provenance: json['provenance'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        reasons: (json['reasons'] as List<dynamic>).cast<String>(),
        disclaimer: json['disclaimer'] as String,
        requiresHumanReview: json['requires_human_review'] as bool,
      );

  final String answer;
  final String interpretedIntent;
  final int parkingScore;
  final String riskLevel;
  final String recommendation;
  final String provenance;
  final double confidence;
  final List<String> reasons;
  final String disclaimer;
  final bool requiresHumanReview;
}
