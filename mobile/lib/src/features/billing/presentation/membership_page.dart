import 'package:flutter/material.dart';
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
    _load();
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
        Text('Membership', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        const Text(
          'Store purchases are credited only after server verification. ParkShield never '
          'accepts a client-declared purchase result or displays an invented price.',
        ),
        const SizedBox(height: 20),
        Card(
          child: ListTile(
            leading: Icon(entitlement?.premium == true
                ? Icons.workspace_premium
                : Icons.shield_outlined),
            title: Text(entitlement?.premium == true
                ? 'ParkShield Premium'
                : 'ParkShield Free'),
            subtitle: Text(_statusText(entitlement)),
          ),
        ),
        const SizedBox(height: 16),
        if (configuration != null && !configuration.enabled)
          const Text(
            'Purchases are not available in this build. No charge can be initiated.',
          ),
        if (configuration?.enabled == true && !widget.storeBridge.available)
          const Text(
            'The server catalog is prepared, but this build is not connected to App Store '
            'or Google Play billing. No charge can be initiated.',
          ),
        if (configuration?.enabled == true &&
            widget.storeBridge.available) ...<Widget>[
          const Text(
            'Your device store presents the localized price and terms before confirmation.',
          ),
          const SizedBox(height: 12),
          ...configuration!.products.map(
            (BillingProduct product) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: FilledButton.icon(
                onPressed: _loading ? null : () => _purchase(product),
                icon: const Icon(Icons.workspace_premium_outlined),
                label: Text('Continue in ${product.platform.label}'),
              ),
            ),
          ),
          OutlinedButton.icon(
            onPressed: _loading ? null : _restore,
            icon: const Icon(Icons.restore),
            label: const Text('Restore store purchases'),
          ),
        ],
        const SizedBox(height: 16),
        TextButton.icon(
          onPressed: _loading ? null : _load,
          icon: const Icon(Icons.refresh),
          label: const Text('Refresh membership status'),
        ),
        const Text(
          'Deleting a ParkShield account does not cancel a subscription managed by Apple or '
          'Google. Cancel it in the same store account used to subscribe.',
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
  }

  String _statusText(EntitlementStatus? value) {
    if (value == null) return 'Status unavailable';
    final String store = value.platform?.label ?? 'No store subscription';
    final String expiry = value.expiresAt == null
        ? ''
        : ' · through ${value.expiresAt!.toLocal().toIso8601String().split('T').first}';
    return '$store · ${value.status.replaceAll('_', ' ')}$expiry';
  }

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
      _message = 'Membership status could not be loaded.';
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
        _message = 'The store purchase was not completed.';
      } else {
        _entitlement = await _gateway.verify(evidence);
        _message = 'Membership verified by the store.';
      }
    } on Exception {
      _message =
          'The store purchase could not be verified. No access was granted.';
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
          ? 'No store purchase was available to restore.'
          : 'Store purchases were restored and verified.';
    } on Exception {
      _message = 'Store purchases could not be restored.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}
