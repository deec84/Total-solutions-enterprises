import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';

void main() {
  test('parses consent and alert decision contracts', () {
    final AlertPreferences preferences =
        AlertPreferences.fromJson(<String, dynamic>{
      'parking_alerts_enabled': true,
      'background_location_enabled': true,
      'quiet_start_hour': 22,
      'quiet_end_hour': 7,
      'timezone': 'America/New_York',
    });
    final AlertDecision decision = AlertDecision.fromJson(<String, dynamic>{
      'should_alert': true,
      'reason': 'Tow-away restriction',
      'parking_score': 20,
      'risk_level': 'very_high_risk',
      'estimated_towing_cost_cents': 25000,
      'deduplicated': false,
    });
    expect(preferences.backgroundLocationEnabled, isTrue);
    expect(decision.shouldAlert, isTrue);
    expect(decision.parkingScore, 20);
    expect(decision.estimatedTowingCostCents, 25000);
  });
}
