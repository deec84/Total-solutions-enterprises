import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';

class VerifyEmailPage extends StatefulWidget {
  const VerifyEmailPage({required this.controller, super.key});

  final AuthController controller;

  @override
  State<VerifyEmailPage> createState() => _VerifyEmailPageState();
}

class _VerifyEmailPageState extends State<VerifyEmailPage> {
  final TextEditingController _token = TextEditingController();

  @override
  void dispose() {
    _token.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Verify email')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const Text(
                  'Open your verification link, or paste its token below.'),
              const SizedBox(height: 16),
              TextField(
                controller: _token,
                autocorrect: false,
                decoration:
                    const InputDecoration(labelText: 'Verification token'),
              ),
              const SizedBox(height: 24),
              FilledButton(
                  onPressed: _submit, child: const Text('Verify account')),
            ],
          ),
        ),
      );

  Future<void> _submit() async {
    if (_token.text.trim().isEmpty) return;
    final bool verified = await widget.controller.verifyEmail(_token.text);
    if (!mounted) return;
    if (verified) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Email verified. You can now sign in.')),
      );
      Navigator.of(context).pop();
    }
  }
}
