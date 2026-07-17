import 'package:latlong2/latlong.dart';

class ParkingZone {
  const ParkingZone({
    required this.id,
    required this.name,
    required this.points,
    required this.parkingScore,
    required this.riskLevel,
    required this.provenance,
    required this.confidence,
    required this.zoneType,
    required this.towingHotspot,
    this.restrictionSummary,
    this.averageTowingCostCents,
  });

  factory ParkingZone.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> geometry =
        json['geometry'] as Map<String, dynamic>;
    final List<dynamic> rings = geometry['coordinates'] as List<dynamic>;
    final List<dynamic> exterior = rings.first as List<dynamic>;
    return ParkingZone(
      id: json['id'] as String,
      name: json['name'] as String,
      points: exterior.map((dynamic coordinate) {
        final List<dynamic> pair = coordinate as List<dynamic>;
        return LatLng((pair[1] as num).toDouble(), (pair[0] as num).toDouble());
      }).toList(growable: false),
      parkingScore: json['parking_score'] as int,
      riskLevel: json['risk_level'] as String,
      provenance: json['provenance'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      zoneType: json['zone_type'] as String,
      towingHotspot: json['towing_hotspot'] as bool,
      restrictionSummary: json['restriction_summary'] as String?,
      averageTowingCostCents: json['average_towing_cost_cents'] as int?,
    );
  }

  final String id;
  final String name;
  final List<LatLng> points;
  final int parkingScore;
  final String riskLevel;
  final String provenance;
  final double confidence;
  final String zoneType;
  final bool towingHotspot;
  final String? restrictionSummary;
  final int? averageTowingCostCents;
}
