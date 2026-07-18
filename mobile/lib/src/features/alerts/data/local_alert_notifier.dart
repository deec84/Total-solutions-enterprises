import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/widgets.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';

class LocalAlertNotifier {
  LocalAlertNotifier({Locale? locale})
      : _l10n = lookupAppLocalizations(_supportedLocale(
          locale ?? WidgetsBinding.instance.platformDispatcher.locale,
        ));

  final AppLocalizations _l10n;
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
        title: _l10n.notificationRisk(decision.parkingScore ?? '--'),
        body: decision.reason,
        notificationDetails: NotificationDetails(
          android: AndroidNotificationDetails(
            'parking-risk-alerts',
            _l10n.notificationChannel,
            channelDescription: _l10n.notificationChannelDescription,
            importance: Importance.high,
            priority: Priority.high,
          ),
          iOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentSound: true,
          ),
        ),
        payload: decision.riskLevel,
      );
}

Locale _supportedLocale(Locale locale) =>
    locale.languageCode == 'es' ? const Locale('es') : const Locale('en');
