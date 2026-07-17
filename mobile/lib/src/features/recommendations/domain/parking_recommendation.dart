class ParkingRecommendation {
  const ParkingRecommendation({
    required this.id,
    required this.name,
    required this.address,
    required this.walkingDistanceMeters,
    required this.hourlyPriceCents,
    required this.safetyScore,
    required this.towingIncidentsPer1000,
    required this.rating,
    required this.availableSpaces,
    required this.capacity,
    required this.navigationUrl,
    required this.provenance,
    required this.confidence,
    required this.rankingScore,
    required this.reasons,
  });

  factory ParkingRecommendation.fromJson(Map<String, dynamic> json) =>
      ParkingRecommendation(
        id: json['id'] as String,
        name: json['name'] as String,
        address: json['address'] as String,
        walkingDistanceMeters: json['walking_distance_meters'] as int,
        hourlyPriceCents: json['hourly_price_cents'] as int?,
        safetyScore: json['safety_score'] as int,
        towingIncidentsPer1000:
            (json['towing_incidents_per_1000'] as num).toDouble(),
        rating: (json['rating'] as num?)?.toDouble(),
        availableSpaces: json['available_spaces'] as int?,
        capacity: json['capacity'] as int?,
        navigationUrl: json['navigation_url'] as String,
        provenance: json['provenance'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        rankingScore: json['ranking_score'] as int,
        reasons: (json['reasons'] as List<dynamic>).cast<String>(),
      );

  final String id;
  final String name;
  final String address;
  final int walkingDistanceMeters;
  final int? hourlyPriceCents;
  final int safetyScore;
  final double towingIncidentsPer1000;
  final double? rating;
  final int? availableSpaces;
  final int? capacity;
  final String navigationUrl;
  final String provenance;
  final double confidence;
  final int rankingScore;
  final List<String> reasons;
}

class ParkingRecommendationList {
  const ParkingRecommendationList({
    required this.options,
    required this.disclaimer,
  });

  factory ParkingRecommendationList.fromJson(Map<String, dynamic> json) =>
      ParkingRecommendationList(
        options: (json['recommendations'] as List<dynamic>)
            .map((dynamic item) =>
                ParkingRecommendation.fromJson(item as Map<String, dynamic>))
            .toList(growable: false),
        disclaimer: json['disclaimer'] as String,
      );

  final List<ParkingRecommendation> options;
  final String disclaimer;
}
