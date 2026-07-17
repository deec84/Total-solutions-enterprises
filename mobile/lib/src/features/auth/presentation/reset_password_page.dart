import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';

class ResetPasswordPage extends StatefulWidget {
  const ResetPasswordPage(
      {required this.controller, this.initialToken, super.key});

  final AuthController controller;
  final String? initialToken;

  @override
  State<ResetPasswordPage> createState() => _ResetPasswordPageState();
}

class _ResetPasswordPageState extends State<ResetPasswordPage> {
  final GlobalKey<FormState> _form = GlobalKey<FormState>();
  late final TextEditingController _token;
  final TextEditingController _password = TextEditingController();

  @override
  void initState() {
    super.initState();
    _token = TextEditingController(text: widget.initialToken);
  }

  @override
  void dispose() {
    _token.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Set new password')),
        body: Form(
          key: _form,
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: <Widget>[
              TextFormField(
                controller: _token,
                autocorrect: false,
                decoration: const InputDecoration(labelText: 'Recovery token'),
                validator: (String? value) =>
                    value == null || value.trim().isEmpty
                        ? 'Enter the recovery token.'
                        : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _password,
                obscureText: true,
                autofillHints: const <String>[AutofillHints.newPassword],
                decoration: const InputDecoration(labelText: 'New password'),
                validator: (String? value) =>
                    value != null && value.length >= 12
                        ? null
                        : 'Password must contain at least 12 characters.',
              ),
              const SizedBox(height: 24),
              FilledButton(
                  onPressed: _submit, child: const Text('Update password')),
            ],
          ),
        ),
      );

  Future<void> _submit() async {
    if (!(_form.currentState?.validate() ?? false)) return;
    final bool changed = await widget.controller.resetPassword(
      token: _token.text,
      newPassword: _password.text,
    );
    if (!mounted) return;
    if (changed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Password updated. Sign in with your new password.')),
      );
      Navigator.of(context).popUntil((Route<dynamic> route) => route.isFirst);
    }
  }
}
