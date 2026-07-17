import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/map/domain/parking_zone.dart';

void main() {
  test('parses GeoJSON longitude-latitude coordinates safely', () {
    final ParkingZone zone = ParkingZone.fromJson(<String, dynamic>{
      'id': 'zone-1',
      'name': 'Test zone',
      'geometry': <String, dynamic>{
        'type': 'Polygon',
        'coordinates': <dynamic>[
          <dynamic>[
            <dynamic>[-80.2, 25.7],
            <dynamic>[-80.1, 25.7],
            <dynamic>[-80.2, 25.7],
          ],
        ],
      },
      'parking_score': 80,
      'risk_level': 'safe',
      'provenance': 'official',
      'confidence': 1.0,
      'zone_type': 'general',
      'towing_hotspot': false,
      'restriction_summary': 'No restriction',
      'average_towing_cost_cents': 18500,
    });

    expect(zone.points.first.latitude, 25.7);
    expect(zone.points.first.longitude, -80.2);
    expect(zone.parkingScore, 80);
    expect(zone.provenance, 'official');
  });
}
