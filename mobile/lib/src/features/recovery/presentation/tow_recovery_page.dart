import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/recovery/data/tow_recovery_api.dart';
import 'package:parkshield_mobile/src/features/recovery/domain/tow_recovery.dart';
import 'package:url_launcher/url_launcher.dart';

class TowRecoveryPage extends StatefulWidget {
  const TowRecoveryPage({required this.apiBaseUrl, this.api, super.key});

  final String apiBaseUrl;
  final TowRecoveryApi? api;

  @override
  State<TowRecoveryPage> createState() => _TowRecoveryPageState();
}

class _TowRecoveryPageState extends State<TowRecoveryPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _state = TextEditingController();
  final TextEditingController _plate = TextEditingController();
  final TextEditingController _vin = TextEditingController();
  late final TowRecoveryApi _api;
  TowLookupResult? _result;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _api = widget.api ??
        TowRecoveryApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
  }

  @override
  void dispose() {
    _api.close();
    _state.dispose();
    _plate.dispose();
    _vin.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Find a towed vehicle',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
            'Search verified municipal and towing-provider records. Never pay from an '
            'unverified message or phone call.',
          ),
          const SizedBox(height: 20),
          Form(
            key: _formKey,
            child: Column(
              children: <Widget>[
                TextFormField(
                  controller: _state,
                  textCapitalization: TextCapitalization.characters,
                  maxLength: 2,
                  decoration: const InputDecoration(
                    labelText: 'Vehicle state',
                    hintText: 'FL',
                    border: OutlineInputBorder(),
                  ),
                  validator: (String? value) => value?.trim().length == 2
                      ? null
                      : 'Enter a 2-letter state code',
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _plate,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'License plate',
                    border: OutlineInputBorder(),
                  ),
                  validator: (String? value) => (value?.trim().length ?? 0) >= 2
                      ? null
                      : 'Enter the license plate',
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _vin,
                  textCapitalization: TextCapitalization.characters,
                  maxLength: 6,
                  decoration: const InputDecoration(
                    labelText: 'Last 6 VIN characters (optional)',
                    border: OutlineInputBorder(),
                  ),
                  validator: (String? value) {
                    final int length = value?.trim().length ?? 0;
                    return length == 0 || length == 6
                        ? null
                        : 'Enter exactly 6 characters';
                  },
                ),
                FilledButton.icon(
                  onPressed: _loading ? null : _lookup,
                  icon: const Icon(Icons.search),
                  label: const Text('Search tow records'),
                ),
              ],
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            ),
          if (_error case final String message)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(message,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          if (_result case final TowLookupResult result)
            _RecoveryResult(result: result),
        ],
      );

  Future<void> _lookup() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });
    try {
      final TowLookupResult result = await _api.lookup(
        state: _state.text.trim(),
        licensePlate: _plate.text.trim(),
        vinLastSix: _vin.text.trim().isEmpty ? null : _vin.text.trim(),
      );
      if (mounted) setState(() => _result = result);
    } on Exception {
      if (mounted) {
        setState(() => _error = 'Tow lookup is temporarily unavailable.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}

class _RecoveryResult extends StatelessWidget {
  const _RecoveryResult({required this.result});

  final TowLookupResult result;

  @override
  Widget build(BuildContext context) {
    final TowRecord? record = result.record;
    return Card(
      margin: const EdgeInsets.only(top: 20),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(result.found ? 'Verified record found' : 'No verified record',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(result.message),
            if (record != null) ...<Widget>[
              const Divider(height: 28),
              Text(record.towCompany,
                  style: Theme.of(context).textTheme.titleMedium),
              Text(record.storageLocation),
              Text(record.businessHours),
              const SizedBox(height: 12),
              Text('Bring: ${record.requiredDocuments.join(', ')}'),
              Text('Payment: ${record.paymentMethods.join(', ')}'),
              Text(
                record.estimatedFeesCents == null
                    ? 'Fees: confirm directly'
                    : 'Estimated fees: '
                        '\$${(record.estimatedFeesCents! / 100).toStringAsFixed(2)}',
              ),
              Text('Source: ${record.provenance} · '
                  '${(record.confidence * 100).round()}% confidence'),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: <Widget>[
                  OutlinedButton.icon(
                    onPressed: () =>
                        launchUrl(Uri.parse('tel:${record.phoneNumber}')),
                    icon: const Icon(Icons.call_outlined),
                    label: const Text('Call'),
                  ),
                  FilledButton.icon(
                    onPressed: () => launchUrl(
                      Uri.parse(record.navigationUrl),
                      mode: LaunchMode.externalApplication,
                    ),
                    icon: const Icon(Icons.navigation_outlined),
                    label: const Text('Navigate'),
                  ),
                ],
              ),
            ],
            const Divider(height: 28),
            Text(result.privacyNotice,
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}
