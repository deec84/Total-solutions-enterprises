import 'package:flutter/material.dart';
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
        appBar: AppBar(title: const Text('Recover password')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const Text(
                'Enter your email. If an account exists, we will send recovery instructions.',
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(labelText: 'Email'),
              ),
              const SizedBox(height: 24),
              FilledButton(
                  onPressed: _submit, child: const Text('Send instructions')),
              TextButton(
                onPressed: () => Navigator.of(context).push<void>(
                  MaterialPageRoute<void>(
                    builder: (_) =>
                        ResetPasswordPage(controller: widget.controller),
                  ),
                ),
                child: const Text('I have a recovery token'),
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
      const SnackBar(
          content: Text('If the account exists, instructions were sent.')),
    );
  }
}
