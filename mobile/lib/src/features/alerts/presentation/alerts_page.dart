import 'package:flutter/material.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/alerts/application/parking_alert_coordinator.dart';
import 'package:parkshield_mobile/src/features/alerts/data/alerts_api.dart';
import 'package:parkshield_mobile/src/features/alerts/data/local_alert_notifier.dart';
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';

class AlertsPage extends StatefulWidget {
  const AlertsPage({
    required this.apiBaseUrl,
    this.api,
    this.coordinator,
    super.key,
  });

  final String apiBaseUrl;
  final AlertsApi? api;
  final ParkingAlertCoordinator? coordinator;

  @override
  State<AlertsPage> createState() => _AlertsPageState();
}

class _AlertsPageState extends State<AlertsPage> {
  late final AlertsApi _api;
  late final ParkingAlertCoordinator _coordinator;
  late AppLocalizations _l10n;
  bool _initialized = false;
  bool _enabled = false;
  bool _loading = true;
  int _quietStart = 22;
  int _quietEnd = 7;
  String _timezone = 'America/New_York';
  String? _message;

  @override
  void initState() {
    super.initState();
    _api = widget.api ??
        AlertsApi(baseUrl: widget.apiBaseUrl, tokenStore: SecureTokenStore());
    _coordinator = widget.coordinator ??
        ParkingAlertCoordinator(_api, LocalAlertNotifier());
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _l10n = context.l10n;
    if (!_initialized) {
      _initialized = true;
      _load();
    }
  }

  @override
  void dispose() {
    _coordinator.stop();
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text(context.l10n.alertsTitle,
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(context.l10n.alertsIntro),
          const SizedBox(height: 16),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(context.l10n.automaticAlerts),
            subtitle: Text(context.l10n.automaticAlertsPermission),
            value: _enabled,
            onChanged: _loading ? null : _toggle,
          ),
          const Divider(),
          Text(context.l10n.quietHours,
              style: Theme.of(context).textTheme.titleMedium),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<int>(
                  initialValue: _quietStart,
                  decoration: InputDecoration(labelText: context.l10n.start),
                  items: _hours(),
                  onChanged: _loading
                      ? null
                      : (int? value) => setState(() => _quietStart = value!),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: DropdownButtonFormField<int>(
                  initialValue: _quietEnd,
                  decoration: InputDecoration(labelText: context.l10n.end),
                  items: _hours(),
                  onChanged: _loading
                      ? null
                      : (int? value) => setState(() => _quietEnd = value!),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _timezone,
            decoration: InputDecoration(labelText: context.l10n.timeZone),
            items: <DropdownMenuItem<String>>[
              DropdownMenuItem(
                  value: 'America/New_York', child: Text(context.l10n.eastern)),
              DropdownMenuItem(
                  value: 'America/Chicago', child: Text(context.l10n.central)),
              DropdownMenuItem(
                  value: 'America/Denver', child: Text(context.l10n.mountain)),
              DropdownMenuItem(
                  value: 'America/Los_Angeles',
                  child: Text(context.l10n.pacific)),
              DropdownMenuItem(
                  value: 'America/Anchorage', child: Text(context.l10n.alaska)),
              DropdownMenuItem(
                  value: 'Pacific/Honolulu', child: Text(context.l10n.hawaii)),
            ],
            onChanged: _loading
                ? null
                : (String? value) => setState(() => _timezone = value!),
          ),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: _loading ? null : _save,
            child: Text(context.l10n.saveQuietHours),
          ),
          if (_loading) const Center(child: CircularProgressIndicator()),
          if (_message case final String message)
            Padding(
                padding: const EdgeInsets.only(top: 12), child: Text(message)),
        ],
      );

  List<DropdownMenuItem<int>> _hours() => List<DropdownMenuItem<int>>.generate(
        24,
        (int hour) => DropdownMenuItem<int>(
            value: hour, child: Text('${hour.toString().padLeft(2, '0')}:00')),
      );

  Future<void> _load() async {
    try {
      final AlertPreferences preferences = await _api.preferences();
      _enabled = preferences.parkingAlertsEnabled &&
          preferences.backgroundLocationEnabled;
      _quietStart = preferences.quietStartHour;
      _quietEnd = preferences.quietEndHour;
      _timezone = preferences.timezone;
      if (_enabled && !await _coordinator.start()) {
        _message = _l10n.alertsPermissionResume;
      }
    } on Exception {
      _message = _l10n.alertsLoadError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggle(bool enabled) async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      await _api.updatePreferences(
        enabled: enabled,
        quietStartHour: _quietStart,
        quietEndHour: _quietEnd,
        timezone: _timezone,
      );
      if (enabled) {
        final bool started = await _coordinator.start();
        if (!started) {
          await _api.updatePreferences(
            enabled: false,
            quietStartHour: _quietStart,
            quietEndHour: _quietEnd,
            timezone: _timezone,
          );
          _enabled = false;
          _message = _l10n.alertsPermissionRequired;
        } else {
          _enabled = true;
          _message = _l10n.alertsActive;
        }
      } else {
        await _coordinator.stop();
        _enabled = false;
        _message = _l10n.alertsOff;
      }
    } on Exception {
      _message = _l10n.alertsUpdateError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() => _toggle(_enabled);
}
