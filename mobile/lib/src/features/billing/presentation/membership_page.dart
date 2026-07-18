import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/billing/data/billing_api.dart';
import 'package:parkshield_mobile/src/features/billing/domain/billing_models.dart';

class MembershipPage extends StatefulWidget {
  const MembershipPage({
    required this.apiBaseUrl,
    this.gateway,
    this.storeBridge = const DisabledStorePurchaseBridge(),
    super.key,
  });

  final String apiBaseUrl;
  final BillingGateway? gateway;
  final StorePurchaseBridge storeBridge;

  @override
  State<MembershipPage> createState() => _MembershipPageState();
}

class _MembershipPageState extends State<MembershipPage> {
  late final BillingGateway _gateway;
  late AppLocalizations _l10n;
  bool _initialized = false;
  BillingConfiguration? _configuration;
  EntitlementStatus? _entitlement;
  bool _loading = true;
  String? _message;

  @override
  void initState() {
    super.initState();
    _gateway = widget.gateway ??
        BillingApi(
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
      _load();
    }
  }

  @override
  void dispose() {
    _gateway.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final BillingConfiguration? configuration = _configuration;
    final EntitlementStatus? entitlement = _entitlement;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        Text(context.l10n.membershipTitle,
            style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text(context.l10n.membershipVerificationNotice),
        const SizedBox(height: 20),
        Card(
          child: ListTile(
            leading: Icon(entitlement?.premium == true
                ? Icons.workspace_premium
                : Icons.shield_outlined),
            title: Text(entitlement?.premium == true
                ? context.l10n.membershipPremium
                : context.l10n.membershipFree),
            subtitle: Text(_statusText(context.l10n, entitlement)),
          ),
        ),
        const SizedBox(height: 16),
        if (configuration != null && !configuration.enabled)
          Text(context.l10n.purchasesDisabled),
        if (configuration?.enabled == true && !widget.storeBridge.available)
          Text(context.l10n.storeBridgeDisabled),
        if (configuration?.enabled == true &&
            widget.storeBridge.available) ...<Widget>[
          Text(context.l10n.storePresentsTerms),
          const SizedBox(height: 12),
          ...configuration!.products.map(
            (BillingProduct product) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: FilledButton.icon(
                onPressed: _loading ? null : () => _purchase(product),
                icon: const Icon(Icons.workspace_premium_outlined),
                label: Text(context.l10n.continueInStore(
                  _storeName(product.platform),
                )),
              ),
            ),
          ),
          OutlinedButton.icon(
            onPressed: _loading ? null : _restore,
            icon: const Icon(Icons.restore),
            label: Text(context.l10n.restorePurchases),
          ),
        ],
        const SizedBox(height: 16),
        TextButton.icon(
          onPressed: _loading ? null : _load,
          icon: const Icon(Icons.refresh),
          label: Text(context.l10n.refreshMembership),
        ),
        Text(context.l10n.subscriptionDeletionNotice),
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
  }

  String _statusText(AppLocalizations l10n, EntitlementStatus? value) {
    if (value == null) return l10n.statusUnavailable;
    final String store = value.platform == null
        ? l10n.noStoreSubscription
        : _storeName(value.platform!);
    final String status = switch (value.status) {
      'free' => l10n.membershipStatusFree,
      'active' => l10n.membershipStatusActive,
      'grace_period' => l10n.membershipStatusGracePeriod,
      'paused' => l10n.membershipStatusPaused,
      'expired' => l10n.membershipStatusExpired,
      'revoked' => l10n.membershipStatusRevoked,
      _ => value.status.replaceAll('_', ' '),
    };
    if (value.expiresAt == null) return l10n.membershipStatus(store, status);
    final String date =
        DateFormat.yMd(l10n.localeName).format(value.expiresAt!.toLocal());
    return l10n.membershipStatusThrough(store, status, date);
  }

  String _storeName(StorePlatform platform) => switch (platform) {
        StorePlatform.appleAppStore => 'App Store',
        StorePlatform.googlePlay => 'Google Play',
      };

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final (BillingConfiguration, EntitlementStatus) result = await (
        _gateway.configuration(),
        _gateway.entitlement(),
      ).wait;
      _configuration = result.$1;
      _entitlement = result.$2;
    } on Exception {
      _message = _l10n.membershipLoadError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _purchase(BillingProduct product) async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final StorePurchaseEvidence? evidence =
          await widget.storeBridge.purchase(product);
      if (evidence == null) {
        _message = _l10n.purchaseNotCompleted;
      } else {
        _entitlement = await _gateway.verify(evidence);
        _message = _l10n.membershipVerified;
      }
    } on Exception {
      _message = _l10n.purchaseVerificationError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _restore() async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final List<StorePurchaseEvidence> evidence =
          await widget.storeBridge.restore();
      for (final StorePurchaseEvidence item in evidence) {
        _entitlement = await _gateway.verify(item);
      }
      _message = evidence.isEmpty
          ? _l10n.noPurchaseToRestore
          : _l10n.purchasesRestored;
    } on Exception {
      _message = _l10n.restorePurchasesError;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}
