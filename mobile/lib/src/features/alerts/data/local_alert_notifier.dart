import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';

class LocalAlertNotifier {
  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      ),
    );
    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
    await _plugin
        .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>()
        ?.requestPermissions(alert: true, badge: true, sound: true);
  }

  Future<void> show(AlertDecision decision) => _plugin.show(
        id: DateTime.now().millisecondsSinceEpoch.remainder(1 << 31),
        title: 'Parking risk ${decision.parkingScore ?? '--'}/100',
        body: decision.reason,
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            'parking-risk-alerts',
            'Parking risk alerts',
            channelDescription:
                'Preventive warnings when a parking location is risky.',
            importance: Importance.high,
            priority: Priority.high,
          ),
          iOS:
              DarwinNotificationDetails(presentAlert: true, presentSound: true),
        ),
        payload: decision.riskLevel,
      );
}
