import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
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
          Text(context.l10n.adminTitle,
              style: Theme.of(context).textTheme.headlineSmall),
          Text(context.l10n.adminMfaNotice),
          const SizedBox(height: 16),
          TextField(
            controller: _mfaCode,
            keyboardType: TextInputType.number,
            maxLength: 6,
            obscureText: true,
            decoration:
                InputDecoration(labelText: context.l10n.mfaCodeSixDigit),
          ),
          Wrap(
            spacing: 12,
            children: <Widget>[
              OutlinedButton(
                  onPressed: _loading ? null : _setupMfa,
                  child: Text(context.l10n.enrollMfa)),
              FilledButton(
                  onPressed: _loading ? null : _load,
                  child: Text(context.l10n.openDashboard)),
            ],
          ),
          if (_setup case final MfaSetup setup) ...<Widget>[
            const SizedBox(height: 16),
            Text(context.l10n.mfaSetupHelp),
            SelectableText(setup.secret),
            TextButton(
                onPressed: _loading ? null : _confirmMfa,
                child: Text(context.l10n.confirmMfa)),
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
                _Metric(label: context.l10n.metricUsers, value: overview.users),
                _Metric(
                    label: context.l10n.metricSessions,
                    value: overview.activeSessions),
                _Metric(
                    label: context.l10n.metricPending,
                    value: overview.pendingReports),
                _Metric(
                    label: context.l10n.metricPublished,
                    value: overview.publishedReports),
                _Metric(
                    label: context.l10n.metricRejected,
                    value: overview.rejectedReports),
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
                      ? context.l10n.auditVerified
                      : context.l10n.auditFailure,
                ),
                subtitle:
                    Text(context.l10n.recordsChecked(integrity.recordsChecked)),
              ),
            Text(context.l10n.moderationQueue,
                style: Theme.of(context).textTheme.titleLarge),
            ..._reports.map(
              (ModerationReport report) => Card(
                child: ListTile(
                  title: Text(report.category),
                  subtitle: Text(context.l10n.evidencePercent(
                    report.description,
                    (report.validationScore * 100).round(),
                  )),
                  isThreeLine: true,
                  trailing: PopupMenuButton<bool>(
                    onSelected: (bool approved) => _moderate(report, approved),
                    itemBuilder: (_) => <PopupMenuEntry<bool>>[
                      PopupMenuItem(
                          value: true, child: Text(context.l10n.approve)),
                      PopupMenuItem(
                          value: false, child: Text(context.l10n.reject)),
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
        if (mounted) setState(() => _message = context.l10n.mfaEnabled);
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
        setState(() => _message = context.l10n.adminRequestError);
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
        title: Text(widget.approved
            ? context.l10n.approveReport
            : context.l10n.rejectReport),
        content: TextField(
          controller: _controller,
          decoration: InputDecoration(labelText: context.l10n.reason),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, _controller.text),
            child: Text(context.l10n.confirm),
          ),
        ],
      );
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});
  final String label;
  final int value;

  @override
  Widget build(BuildContext context) =>
      Chip(label: Text(context.l10n.metricValue(label, value)));
}
