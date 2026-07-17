import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/features/admin/data/admin_api.dart';
import 'package:parkshield_mobile/src/features/admin/domain/admin_models.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';

class AdminPage extends StatefulWidget {
  const AdminPage({required this.apiBaseUrl, this.api, super.key});

  final String apiBaseUrl;
  final AdminApi? api;

  @override
  State<AdminPage> createState() => _AdminPageState();
}

class _AdminPageState extends State<AdminPage> {
  final TextEditingController _mfaCode = TextEditingController();
  late final AdminApi _api;
  AdminOverview? _overview;
  List<ModerationReport> _reports = const <ModerationReport>[];
  MfaSetup? _setup;
  AuditIntegrity? _auditIntegrity;
  bool _loading = false;
  String? _message;

  @override
  void initState() {
    super.initState();
    _api = widget.api ??
        AdminApi(baseUrl: widget.apiBaseUrl, tokenStore: SecureTokenStore());
  }

  @override
  void dispose() {
    _api.close();
    _mfaCode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Administration',
              style: Theme.of(context).textTheme.headlineSmall),
          const Text('Privileged actions require a fresh authenticator code.'),
          const SizedBox(height: 16),
          TextField(
            controller: _mfaCode,
            keyboardType: TextInputType.number,
            maxLength: 6,
            obscureText: true,
            decoration: const InputDecoration(labelText: '6-digit MFA code'),
          ),
          Wrap(
            spacing: 12,
            children: <Widget>[
              OutlinedButton(
                  onPressed: _loading ? null : _setupMfa,
                  child: const Text('Enroll MFA')),
              FilledButton(
                  onPressed: _loading ? null : _load,
                  child: const Text('Open dashboard')),
            ],
          ),
          if (_setup case final MfaSetup setup) ...<Widget>[
            const SizedBox(height: 16),
            const Text(
                'Add this secret to your authenticator, then enter its code:'),
            SelectableText(setup.secret),
            TextButton(
                onPressed: _loading ? null : _confirmMfa,
                child: const Text('Confirm MFA')),
          ],
          if (_message case final String message)
            Padding(
                padding: const EdgeInsets.only(top: 12), child: Text(message)),
          if (_overview case final AdminOverview overview) ...<Widget>[
            const Divider(height: 32),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: <Widget>[
                _Metric(label: 'Users', value: overview.users),
                _Metric(label: 'Sessions', value: overview.activeSessions),
                _Metric(label: 'Pending', value: overview.pendingReports),
                _Metric(label: 'Published', value: overview.publishedReports),
                _Metric(label: 'Rejected', value: overview.rejectedReports),
              ],
            ),
            const SizedBox(height: 24),
            if (_auditIntegrity case final AuditIntegrity integrity)
              ListTile(
                leading: Icon(
                  integrity.valid ? Icons.verified_user : Icons.warning_amber,
                ),
                title: Text(
                  integrity.valid
                      ? 'Audit chain verified'
                      : 'Audit integrity failure',
                ),
                subtitle: Text('${integrity.recordsChecked} records checked'),
              ),
            Text('Moderation queue',
                style: Theme.of(context).textTheme.titleLarge),
            ..._reports.map(
              (ModerationReport report) => Card(
                child: ListTile(
                  title: Text(report.category),
                  subtitle: Text(
                      '${report.description}\nEvidence ${(report.validationScore * 100).round()}%'),
                  isThreeLine: true,
                  trailing: PopupMenuButton<bool>(
                    onSelected: (bool approved) => _moderate(report, approved),
                    itemBuilder: (_) => const <PopupMenuEntry<bool>>[
                      PopupMenuItem(value: true, child: Text('Approve')),
                      PopupMenuItem(value: false, child: Text('Reject')),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ],
      );

  Future<void> _setupMfa() async => _run(() async {
        final MfaSetup setup = await _api.setupMfa();
        if (mounted) setState(() => _setup = setup);
      });

  Future<void> _confirmMfa() async => _run(() async {
        await _api.confirmMfa(_mfaCode.text.trim());
        if (mounted) setState(() => _message = 'MFA enabled.');
      });

  Future<void> _load() async => _run(() async {
        final String code = _mfaCode.text.trim();
        final AdminOverview overview = await _api.overview(code);
        final List<ModerationReport> reports = await _api.moderationQueue(code);
        final AuditIntegrity integrity = await _api.auditIntegrity(code);
        if (mounted) {
          setState(() {
            _overview = overview;
            _reports = reports;
            _auditIntegrity = integrity;
          });
        }
      });

  Future<void> _moderate(ModerationReport report, bool approved) async {
    final String? reason = await _reasonDialog(approved);
    if (reason == null || reason.trim().length < 5) return;
    await _run(() async {
      await _api.moderate(
        reportId: report.id,
        approved: approved,
        reason: reason,
        mfaCode: _mfaCode.text.trim(),
      );
      await _load();
    });
  }

  Future<String?> _reasonDialog(bool approved) async {
    return showDialog<String>(
      context: context,
      builder: (BuildContext context) => _ModerationReasonDialog(
        approved: approved,
      ),
    );
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      await action();
    } on Exception {
      if (mounted) {
        setState(() =>
            _message = 'Administrative request failed. Verify role and MFA.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}

class _ModerationReasonDialog extends StatefulWidget {
  const _ModerationReasonDialog({required this.approved});

  final bool approved;

  @override
  State<_ModerationReasonDialog> createState() =>
      _ModerationReasonDialogState();
}

class _ModerationReasonDialogState extends State<_ModerationReasonDialog> {
  final TextEditingController _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: Text(widget.approved ? 'Approve report' : 'Reject report'),
        content: TextField(
          controller: _controller,
          decoration: const InputDecoration(labelText: 'Reason'),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, _controller.text),
            child: const Text('Confirm'),
          ),
        ],
      );
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});
  final String label;
  final int value;

  @override
  Widget build(BuildContext context) => Chip(label: Text('$label: $value'));
}
