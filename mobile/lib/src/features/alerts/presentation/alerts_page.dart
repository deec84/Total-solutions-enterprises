import 'package:flutter/material.dart';
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
    _load();
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
          Text('Preventive alerts',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
            'When enabled, ParkShield may access location in the background to warn you after '
            'significant movement. Location checks are sent only for parking-risk evaluation.',
          ),
          const SizedBox(height: 16),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Automatic parking-risk alerts'),
            subtitle: const Text(
                'Requires Always Allow location permission. You can revoke it anytime.'),
            value: _enabled,
            onChanged: _loading ? null : _toggle,
          ),
          const Divider(),
          Text('Quiet hours', style: Theme.of(context).textTheme.titleMedium),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<int>(
                  initialValue: _quietStart,
                  decoration: const InputDecoration(labelText: 'Start'),
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
                  decoration: const InputDecoration(labelText: 'End'),
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
            decoration: const InputDecoration(labelText: 'Time zone'),
            items: const <DropdownMenuItem<String>>[
              DropdownMenuItem(
                  value: 'America/New_York', child: Text('Eastern')),
              DropdownMenuItem(
                  value: 'America/Chicago', child: Text('Central')),
              DropdownMenuItem(
                  value: 'America/Denver', child: Text('Mountain')),
              DropdownMenuItem(
                  value: 'America/Los_Angeles', child: Text('Pacific')),
              DropdownMenuItem(
                  value: 'America/Anchorage', child: Text('Alaska')),
              DropdownMenuItem(
                  value: 'Pacific/Honolulu', child: Text('Hawaii')),
            ],
            onChanged: _loading
                ? null
                : (String? value) => setState(() => _timezone = value!),
          ),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: _loading ? null : _save,
            child: const Text('Save quiet hours'),
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
        _message =
            'Enable Always Allow location permission to resume automatic alerts.';
      }
    } on Exception {
      _message = 'Alert preferences could not be loaded.';
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
          _message =
              'Alerts remain off. Grant Always Allow location permission, then try again.';
        } else {
          _enabled = true;
          _message = 'Preventive parking alerts are active.';
        }
      } else {
        await _coordinator.stop();
        _enabled = false;
        _message = 'Preventive parking alerts are off.';
      }
    } on Exception {
      _message = 'Alert settings could not be updated.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() => _toggle(_enabled);
}
