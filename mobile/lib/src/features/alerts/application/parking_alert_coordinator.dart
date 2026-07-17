import 'dart:async';
import 'dart:io';

import 'package:geolocator/geolocator.dart';
import 'package:parkshield_mobile/src/features/alerts/application/parking_stop_detector.dart';
import 'package:parkshield_mobile/src/features/alerts/data/alerts_api.dart';
import 'package:parkshield_mobile/src/features/alerts/data/local_alert_notifier.dart';
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';

class ParkingAlertCoordinator {
  ParkingAlertCoordinator(
    this._api,
    this._notifier, {
    ParkingStopDetector? stopDetector,
  }) : _stopDetector = stopDetector ?? ParkingStopDetector();

  final AlertsApi _api;
  final LocalAlertNotifier _notifier;
  final ParkingStopDetector _stopDetector;
  StreamSubscription<Position>? _subscription;

  Future<bool> start() async {
    if (!await Geolocator.isLocationServiceEnabled()) return false;
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission != LocationPermission.always) return false;
    await _notifier.initialize();
    await _subscription?.cancel();
    _stopDetector.reset();
    _subscription =
        Geolocator.getPositionStream(locationSettings: _settings()).listen(
      (Position position) async {
        final bool likelyParkingStop = _stopDetector.add(
          ParkingStopObservation(
            latitude: position.latitude,
            longitude: position.longitude,
            observedAt: position.timestamp,
            speedMetersPerSecond: position.speed,
            horizontalAccuracyMeters: position.accuracy,
          ),
        );
        if (!likelyParkingStop) return;
        try {
          final AlertDecision decision = await _api.evaluate(
            position.latitude,
            position.longitude,
          );
          if (decision.shouldAlert) await _notifier.show(decision);
        } on Exception {
          // Location updates are best effort; the next update retries automatically.
        }
      },
    );
    return true;
  }

  Future<void> stop() async {
    await _subscription?.cancel();
    _subscription = null;
    _stopDetector.reset();
  }

  LocationSettings _settings() {
    if (Platform.isAndroid) {
      return AndroidSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
        intervalDuration: const Duration(seconds: 15),
        foregroundNotificationConfig: const ForegroundNotificationConfig(
          notificationTitle: 'ParkShield preventive alerts',
          notificationText: 'Watching for a likely parking stop.',
          enableWakeLock: true,
        ),
      );
    }
    if (Platform.isIOS) {
      return AppleSettings(
        accuracy: LocationAccuracy.high,
        activityType: ActivityType.automotiveNavigation,
        distanceFilter: 10,
        pauseLocationUpdatesAutomatically: true,
        showBackgroundLocationIndicator: true,
        allowBackgroundLocationUpdates: true,
      );
    }
    return const LocationSettings(
        accuracy: LocationAccuracy.high, distanceFilter: 10);
  }
}
