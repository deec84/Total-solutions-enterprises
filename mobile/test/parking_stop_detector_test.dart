import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/alerts/application/parking_stop_detector.dart';

void main() {
  final DateTime start = DateTime.utc(2026, 7, 17, 12);

  ParkingStopObservation observation({
    required int seconds,
    required double speed,
    double latitude = 25.7617,
    double longitude = -80.1918,
    double accuracy = 8,
  }) =>
      ParkingStopObservation(
        latitude: latitude,
        longitude: longitude,
        observedAt: start.add(Duration(seconds: seconds)),
        speedMetersPerSecond: speed,
        horizontalAccuracyMeters: accuracy,
      );

  test('requires an observed driving segment before detecting a stop', () {
    final ParkingStopDetector detector = ParkingStopDetector();

    expect(detector.add(observation(seconds: 0, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 30, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 60, speed: 0)), isFalse);
  });

  test('emits once after an armed stable dwell', () {
    final ParkingStopDetector detector = ParkingStopDetector();

    expect(detector.add(observation(seconds: 0, speed: 12)), isFalse);
    expect(detector.add(observation(seconds: 15, speed: 0.4)), isFalse);
    expect(detector.add(observation(seconds: 40, speed: 0.2)), isFalse);
    expect(detector.add(observation(seconds: 65, speed: 0)), isTrue);
    expect(detector.add(observation(seconds: 120, speed: 0)), isFalse);
  });

  test('movement outside the stationary radius restarts dwell timing', () {
    final ParkingStopDetector detector = ParkingStopDetector();

    expect(detector.add(observation(seconds: 0, speed: 8)), isFalse);
    expect(detector.add(observation(seconds: 10, speed: 0)), isFalse);
    expect(
      detector.add(observation(
        seconds: 50,
        speed: 0,
        latitude: 25.7622,
      )),
      isFalse,
    );
    expect(
      detector.add(observation(
        seconds: 80,
        speed: 0,
        latitude: 25.7622,
      )),
      isFalse,
    );
    expect(
      detector.add(observation(
        seconds: 100,
        speed: 0,
        latitude: 25.7622,
      )),
      isTrue,
    );
  });

  test('ignores inaccurate locations and rearms only after driving', () {
    final ParkingStopDetector detector = ParkingStopDetector();

    expect(detector.add(observation(seconds: 0, speed: 9)), isFalse);
    expect(
      detector.add(observation(seconds: 20, speed: 0, accuracy: 100)),
      isFalse,
    );
    expect(detector.add(observation(seconds: 30, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 55, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 80, speed: 0)), isTrue);
    expect(detector.add(observation(seconds: 140, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 150, speed: 10)), isFalse);
    expect(detector.add(observation(seconds: 160, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 190, speed: 0)), isFalse);
    expect(detector.add(observation(seconds: 210, speed: 0)), isTrue);
  });

  test('derives speed when the platform does not provide it', () {
    final ParkingStopDetector detector = ParkingStopDetector(
      minimumDwell: const Duration(seconds: 20),
    );

    expect(detector.add(observation(seconds: 0, speed: -1)), isFalse);
    expect(
      detector.add(observation(
        seconds: 10,
        speed: -1,
        latitude: 25.7622,
      )),
      isFalse,
    );
    expect(
      detector.add(observation(
        seconds: 20,
        speed: -1,
        latitude: 25.7622,
      )),
      isFalse,
    );
    expect(
      detector.add(observation(
        seconds: 30,
        speed: -1,
        latitude: 25.7622,
      )),
      isFalse,
    );
    expect(
      detector.add(observation(
        seconds: 40,
        speed: -1,
        latitude: 25.7622,
      )),
      isTrue,
    );
  });
}
