import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/reset_password_page.dart';

class RecoveryPage extends StatefulWidget {
  const RecoveryPage({required this.controller, super.key});

  final AuthController controller;

  @override
  State<RecoveryPage> createState() => _RecoveryPageState();
}

class _RecoveryPageState extends State<RecoveryPage> {
  final TextEditingController _email = TextEditingController();

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(context.l10n.recoverPassword)),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(context.l10n.recoveryInstructions),
              const SizedBox(height: 16),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(labelText: context.l10n.email),
              ),
              const SizedBox(height: 24),
              FilledButton(
                  onPressed: _submit,
                  child: Text(context.l10n.sendInstructions)),
              TextButton(
                onPressed: () => Navigator.of(context).push<void>(
                  MaterialPageRoute<void>(
                    builder: (_) =>
                        ResetPasswordPage(controller: widget.controller),
                  ),
                ),
                child: Text(context.l10n.haveRecoveryToken),
              ),
            ],
          ),
        ),
      );

  Future<void> _submit() async {
    if (!_email.text.contains('@')) return;
    await widget.controller.requestPasswordReset(_email.text);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(context.l10n.recoverySent)),
    );
  }
}
