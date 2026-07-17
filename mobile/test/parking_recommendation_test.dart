import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/recommendations/domain/parking_recommendation.dart';

void main() {
  test('parses ranked and explainable parking recommendations', () {
    final ParkingRecommendationList list =
        ParkingRecommendationList.fromJson(<String, dynamic>{
      'disclaimer': 'Confirm posted terms.',
      'recommendations': <Map<String, dynamic>>[
        <String, dynamic>{
          'id': 'facility-1',
          'name': 'Safe Garage',
          'address': '100 Safe Parking Way',
          'walking_distance_meters': 220,
          'hourly_price_cents': 1200,
          'safety_score': 92,
          'towing_incidents_per_1000': 2.0,
          'rating': 4.7,
          'available_spaces': 18,
          'capacity': 100,
          'navigation_url': 'https://maps.example.com/safe',
          'provenance': 'official',
          'confidence': 0.95,
          'ranking_score': 87,
          'reasons': <String>['Safety score 92/100.'],
        },
      ],
    });

    expect(list.options.single.name, 'Safe Garage');
    expect(list.options.single.rankingScore, 87);
    expect(list.options.single.provenance, 'official');
    expect(list.options.single.reasons, isNotEmpty);
  });
}
