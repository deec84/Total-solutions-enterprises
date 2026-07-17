import 'dart:math' as math;

class ParkingStopObservation {
  const ParkingStopObservation({
    required this.latitude,
    required this.longitude,
    required this.observedAt,
    required this.speedMetersPerSecond,
    required this.horizontalAccuracyMeters,
  });

  final double latitude;
  final double longitude;
  final DateTime observedAt;
  final double speedMetersPerSecond;
  final double horizontalAccuracyMeters;
}

/// Detects a likely parking stop without transmitting the full location trail.
///
/// The detector first observes automotive movement, then requires a stable,
/// low-speed cluster before emitting once. A new driving segment is required to
/// re-arm it, preventing repeated evaluations while the vehicle remains parked.
class ParkingStopDetector {
  ParkingStopDetector({
    this.movingSpeedMetersPerSecond = 3,
    this.stoppedSpeedMetersPerSecond = 1.2,
    this.stationaryRadiusMeters = 25,
    this.maximumAccuracyMeters = 50,
    this.minimumDwell = const Duration(seconds: 45),
    this.minimumStationarySamples = 3,
  })  : assert(movingSpeedMetersPerSecond > stoppedSpeedMetersPerSecond),
        assert(stationaryRadiusMeters > 0),
        assert(maximumAccuracyMeters > 0),
        assert(minimumStationarySamples >= 2);

  final double movingSpeedMetersPerSecond;
  final double stoppedSpeedMetersPerSecond;
  final double stationaryRadiusMeters;
  final double maximumAccuracyMeters;
  final Duration minimumDwell;
  final int minimumStationarySamples;

  bool _armed = false;
  ParkingStopObservation? _previous;
  ParkingStopObservation? _stationaryAnchor;
  int _stationarySamples = 0;

  bool add(ParkingStopObservation observation) {
    if (!_isUsable(observation)) return false;

    final double resolvedSpeed = _resolvedSpeed(observation);
    _previous = observation;

    if (resolvedSpeed >= movingSpeedMetersPerSecond) {
      _armed = true;
      _clearCandidate();
      return false;
    }
    if (!_armed || resolvedSpeed > stoppedSpeedMetersPerSecond) {
      _clearCandidate();
      return false;
    }

    final ParkingStopObservation? anchor = _stationaryAnchor;
    if (anchor == null ||
        observation.observedAt.isBefore(anchor.observedAt) ||
        _distanceMeters(anchor, observation) > stationaryRadiusMeters) {
      _stationaryAnchor = observation;
      _stationarySamples = 1;
      return false;
    }

    _stationarySamples += 1;
    final bool dwelled =
        observation.observedAt.difference(anchor.observedAt) >= minimumDwell;
    if (!dwelled || _stationarySamples < minimumStationarySamples) return false;

    _armed = false;
    _clearCandidate();
    return true;
  }

  void reset() {
    _armed = false;
    _previous = null;
    _clearCandidate();
  }

  bool _isUsable(ParkingStopObservation observation) =>
      observation.latitude.isFinite &&
      observation.longitude.isFinite &&
      observation.latitude >= -90 &&
      observation.latitude <= 90 &&
      observation.longitude >= -180 &&
      observation.longitude <= 180 &&
      observation.horizontalAccuracyMeters.isFinite &&
      observation.horizontalAccuracyMeters >= 0 &&
      observation.horizontalAccuracyMeters <= maximumAccuracyMeters;

  double _resolvedSpeed(ParkingStopObservation observation) {
    if (observation.speedMetersPerSecond.isFinite &&
        observation.speedMetersPerSecond >= 0) {
      return observation.speedMetersPerSecond;
    }
    final ParkingStopObservation? previous = _previous;
    if (previous == null) return double.infinity;
    final int elapsedMilliseconds =
        observation.observedAt.difference(previous.observedAt).inMilliseconds;
    if (elapsedMilliseconds <= 0) return double.infinity;
    return _distanceMeters(previous, observation) /
        (elapsedMilliseconds / Duration.millisecondsPerSecond);
  }

  void _clearCandidate() {
    _stationaryAnchor = null;
    _stationarySamples = 0;
  }

  static double _distanceMeters(
    ParkingStopObservation from,
    ParkingStopObservation to,
  ) {
    const double earthRadiusMeters = 6371000;
    final double latitudeDelta = _radians(to.latitude - from.latitude);
    final double longitudeDelta = _radians(to.longitude - from.longitude);
    final double fromLatitude = _radians(from.latitude);
    final double toLatitude = _radians(to.latitude);
    final double haversine =
        math.pow(math.sin(latitudeDelta / 2), 2).toDouble() +
            math.cos(fromLatitude) *
                math.cos(toLatitude) *
                math.pow(math.sin(longitudeDelta / 2), 2).toDouble();
    final double clampedHaversine = haversine.clamp(0, 1).toDouble();
    return earthRadiusMeters *
        2 *
        math.atan2(
          math.sqrt(clampedHaversine),
          math.sqrt(1 - clampedHaversine),
        );
  }

  static double _radians(double degrees) => degrees * math.pi / 180;
}
