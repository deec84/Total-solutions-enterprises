import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
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
  late AppLocalizations _l10n;
  bool _initialized = false;
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
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _l10n = context.l10n;
    if (!_initialized) {
      _initialized = true;
      _loadConsents();
    }
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
          Text(context.l10n.privacyTitle,
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(context.l10n.privacyIntro),
          const SizedBox(height: 16),
          ...ConsentPurpose.values.map(
            (ConsentPurpose purpose) => SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(_purposeLabel(context.l10n, purpose)),
              subtitle: Text(_purposeDescription(context.l10n, purpose)),
              value: _consents[purpose] ?? false,
              onChanged: _loading
                  ? null
                  : (bool value) => _updateConsent(purpose, value),
            ),
          ),
          const Divider(height: 32),
          Text(context.l10n.exportDataTitle,
              style: Theme.of(context).textTheme.titleLarge),
          Text(context.l10n.exportDataDescription),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: _loading ? null : _export,
            icon: const Icon(Icons.download_outlined),
            label: Text(context.l10n.createDataExport),
          ),
          if (_exportJson case final String value) ...<Widget>[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => _copyExport(value),
              icon: const Icon(Icons.copy_outlined),
              label: Text(context.l10n.copyExportJson),
            ),
            Semantics(
              label: context.l10n.generatedDataExport,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 220),
                child: SingleChildScrollView(child: SelectableText(value)),
              ),
            ),
          ],
          const Divider(height: 32),
          Text(context.l10n.deleteAccountTitle,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(color: Theme.of(context).colorScheme.error)),
          Text(context.l10n.deleteAccountDescription),
          const SizedBox(height: 12),
          TextField(
            controller: _password,
            obscureText: true,
            autofillHints: const <String>[AutofillHints.password],
            decoration: InputDecoration(
              labelText: context.l10n.currentPassword,
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _mfaCode,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: InputDecoration(
              labelText: context.l10n.mfaCodeOptional,
              border: const OutlineInputBorder(),
            ),
          ),
          OutlinedButton.icon(
            onPressed: _loading ? null : _confirmDeletion,
            icon: const Icon(Icons.delete_forever_outlined),
            label: Text(context.l10n.permanentlyDeleteAccount),
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
      _message = _l10n.privacyLoadError;
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
      _message = _l10n.preferenceSaved(
        _purposeLabel(_l10n, purpose),
      );
    } on Exception {
      _message = _l10n.privacySaveError;
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
      _message = _l10n.dataExportReady;
    } on Exception {
      _message = _l10n.dataExportError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _copyExport(String value) async {
    await Clipboard.setData(ClipboardData(text: value));
    if (mounted) setState(() => _message = _l10n.dataExportCopied);
  }

  Future<void> _confirmDeletion() async {
    if (_password.text.isEmpty) {
      setState(() => _message = context.l10n.enterCurrentPassword);
      return;
    }
    final bool confirmed = await showDialog<bool>(
          context: context,
          builder: (BuildContext context) => AlertDialog(
            title: Text(context.l10n.deleteAccountQuestion),
            content: Text(context.l10n.deleteAccountConfirmation),
            actions: <Widget>[
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: Text(context.l10n.cancel),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: Text(context.l10n.deletePermanently),
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
      _message = _l10n.deleteAccountError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _purposeLabel(AppLocalizations l10n, ConsentPurpose purpose) =>
      switch (purpose) {
        ConsentPurpose.productAnalytics => l10n.consentProductAnalytics,
        ConsentPurpose.personalizedRecommendations =>
          l10n.consentPersonalizedRecommendations,
        ConsentPurpose.communityResearch => l10n.consentCommunityResearch,
      };

  String _purposeDescription(AppLocalizations l10n, ConsentPurpose purpose) =>
      switch (purpose) {
        ConsentPurpose.productAnalytics =>
          l10n.consentProductAnalyticsDescription,
        ConsentPurpose.personalizedRecommendations =>
          l10n.consentPersonalizedRecommendationsDescription,
        ConsentPurpose.communityResearch =>
          l10n.consentCommunityResearchDescription,
      };
}
