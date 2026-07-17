class AlertPreferences {
  const AlertPreferences({
    required this.parkingAlertsEnabled,
    required this.backgroundLocationEnabled,
    required this.quietStartHour,
    required this.quietEndHour,
    required this.timezone,
  });

  factory AlertPreferences.fromJson(Map<String, dynamic> json) =>
      AlertPreferences(
        parkingAlertsEnabled: json['parking_alerts_enabled'] as bool,
        backgroundLocationEnabled: json['background_location_enabled'] as bool,
        quietStartHour: json['quiet_start_hour'] as int,
        quietEndHour: json['quiet_end_hour'] as int,
        timezone: json['timezone'] as String,
      );

  final bool parkingAlertsEnabled;
  final bool backgroundLocationEnabled;
  final int quietStartHour;
  final int quietEndHour;
  final String timezone;
}

class AlertDecision {
  const AlertDecision({
    required this.shouldAlert,
    required this.reason,
    required this.parkingScore,
    required this.riskLevel,
    required this.estimatedTowingCostCents,
    required this.deduplicated,
  });

  factory AlertDecision.fromJson(Map<String, dynamic> json) => AlertDecision(
        shouldAlert: json['should_alert'] as bool,
        reason: json['reason'] as String,
        parkingScore: json['parking_score'] as int?,
        riskLevel: json['risk_level'] as String?,
        estimatedTowingCostCents: json['estimated_towing_cost_cents'] as int?,
        deduplicated: json['deduplicated'] as bool,
      );

  final bool shouldAlert;
  final String reason;
  final int? parkingScore;
  final String? riskLevel;
  final int? estimatedTowingCostCents;
  final bool deduplicated;
}
