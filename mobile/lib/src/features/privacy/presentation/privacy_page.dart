import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/privacy/data/privacy_api.dart';
import 'package:parkshield_mobile/src/features/privacy/domain/privacy_models.dart';

class PrivacyPage extends StatefulWidget {
  const PrivacyPage({
    required this.apiBaseUrl,
    this.gateway,
    this.onAccountDeleted,
    super.key,
  });

  final String apiBaseUrl;
  final PrivacyGateway? gateway;
  final VoidCallback? onAccountDeleted;

  @override
  State<PrivacyPage> createState() => _PrivacyPageState();
}

class _PrivacyPageState extends State<PrivacyPage> {
  late final PrivacyGateway _gateway;
  final TextEditingController _password = TextEditingController();
  final TextEditingController _mfaCode = TextEditingController();
  final Map<ConsentPurpose, bool> _consents = <ConsentPurpose, bool>{};
  bool _loading = true;
  String? _message;
  String? _exportJson;

  @override
  void initState() {
    super.initState();
    _gateway = widget.gateway ??
        PrivacyApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
    _loadConsents();
  }

  @override
  void dispose() {
    _password.dispose();
    _mfaCode.dispose();
    _gateway.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Privacy and your data',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
            'Optional uses are off until you enable them. Essential security and parking '
            'requests are processed to provide the service.',
          ),
          const SizedBox(height: 16),
          ...ConsentPurpose.values.map(
            (ConsentPurpose purpose) => SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(purpose.label),
              subtitle: Text(_purposeDescription(purpose)),
              value: _consents[purpose] ?? false,
              onChanged: _loading
                  ? null
                  : (bool value) => _updateConsent(purpose, value),
            ),
          ),
          const Divider(height: 32),
          Text('Export your data',
              style: Theme.of(context).textTheme.titleLarge),
          const Text(
              'Creates a current JSON copy without passwords, MFA secrets, push tokens, or storage keys.'),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: _loading ? null : _export,
            icon: const Icon(Icons.download_outlined),
            label: const Text('Create data export'),
          ),
          if (_exportJson case final String value) ...<Widget>[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => _copyExport(value),
              icon: const Icon(Icons.copy_outlined),
              label: const Text('Copy export JSON'),
            ),
            Semantics(
              label: 'Generated account data export',
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 220),
                child: SingleChildScrollView(child: SelectableText(value)),
              ),
            ),
          ],
          const Divider(height: 32),
          Text('Delete account',
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(color: Theme.of(context).colorScheme.error)),
          const Text(
            'This permanently removes the account, sessions, preferences, reports, appeals, '
            'and retained community evidence. It does not cancel an Apple or Google '
            'subscription; cancel that in the store. Pseudonymous billing evidence may be '
            'retained for reconciliation and legal obligations. This cannot be undone.',
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _password,
            obscureText: true,
            autofillHints: const <String>[AutofillHints.password],
            decoration: const InputDecoration(
              labelText: 'Current password',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _mfaCode,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: const InputDecoration(
              labelText: 'MFA code (if enabled)',
              border: OutlineInputBorder(),
            ),
          ),
          OutlinedButton.icon(
            onPressed: _loading ? null : _confirmDeletion,
            icon: const Icon(Icons.delete_forever_outlined),
            label: const Text('Permanently delete account'),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            ),
          if (_message case final String value)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Semantics(liveRegion: true, child: Text(value)),
            ),
        ],
      );

  Future<void> _loadConsents() async {
    try {
      final List<PrivacyConsent> decisions = await _gateway.consents();
      for (final PrivacyConsent item in decisions) {
        _consents[item.purpose] = item.granted;
      }
    } on Exception {
      _message = 'Privacy choices could not be loaded.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _updateConsent(ConsentPurpose purpose, bool granted) async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final PrivacyConsent decision =
          await _gateway.setConsent(purpose, granted);
      _consents[purpose] = decision.granted;
      _message = '${purpose.label} preference saved.';
    } on Exception {
      _message = 'The privacy choice could not be saved.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _export() async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final AccountDataExport export = await _gateway.exportData();
      _exportJson = const JsonEncoder.withIndent('  ').convert(<String, Object>{
        'request_id': export.requestId,
        'generated_at': export.generatedAt.toIso8601String(),
        'policy_version': export.policyVersion,
        'data': export.data,
      });
      _message = 'Your data export is ready.';
    } on Exception {
      _message = 'Your data export could not be created.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _copyExport(String value) async {
    await Clipboard.setData(ClipboardData(text: value));
    if (mounted) setState(() => _message = 'Data export copied.');
  }

  Future<void> _confirmDeletion() async {
    if (_password.text.isEmpty) {
      setState(() => _message = 'Enter your current password first.');
      return;
    }
    final bool confirmed = await showDialog<bool>(
          context: context,
          builder: (BuildContext context) => AlertDialog(
            title: const Text('Delete your ParkShield account?'),
            content: const Text(
                'Your account and owned data will be permanently deleted.'),
            actions: <Widget>[
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Delete permanently'),
              ),
            ],
          ),
        ) ??
        false;
    if (!confirmed || !mounted) return;
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      await _gateway.deleteAccount(
        password: _password.text,
        mfaCode: _mfaCode.text.trim().isEmpty ? null : _mfaCode.text.trim(),
      );
      _password.clear();
      _mfaCode.clear();
      widget.onAccountDeleted?.call();
    } on Exception {
      _message =
          'The account was not deleted. Verify your password, MFA code, and connection.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _purposeDescription(ConsentPurpose purpose) => switch (purpose) {
        ConsentPurpose.productAnalytics =>
          'Share de-identified product usage to improve reliability.',
        ConsentPurpose.personalizedRecommendations =>
          'Use your prior choices to rank safer parking alternatives.',
        ConsentPurpose.communityResearch =>
          'Include de-identified reports in parking-safety research.',
      };
}
