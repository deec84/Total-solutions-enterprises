import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({required this.controller, super.key});

  final AuthController controller;

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final GlobalKey<FormState> _form = GlobalKey<FormState>();
  final TextEditingController _email = TextEditingController();
  final TextEditingController _password = TextEditingController();

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Create account')),
        body: ListView(
          padding: const EdgeInsets.all(24),
          children: <Widget>[
            Form(
              key: _form,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const <String>[AutofillHints.newUsername],
                    decoration: const InputDecoration(labelText: 'Email'),
                    validator: _validateEmail,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _password,
                    obscureText: true,
                    autofillHints: const <String>[AutofillHints.newPassword],
                    decoration: const InputDecoration(labelText: 'Password'),
                    validator: _validatePassword,
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: widget.controller.submitting ? null : _submit,
                    child: const Text('Create account'),
                  ),
                ],
              ),
            ),
          ],
        ),
      );

  String? _validateEmail(String? value) =>
      value != null && value.contains('@') ? null : 'Enter a valid email.';

  String? _validatePassword(String? value) =>
      value != null && value.length >= 12
          ? null
          : 'Password must contain at least 12 characters.';

  Future<void> _submit() async {
    if (!(_form.currentState?.validate() ?? false)) return;
    final bool created = await widget.controller.register(
      email: _email.text,
      password: _password.text,
    );
    if (!mounted) return;
    if (created) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Check your email to verify your account.')),
      );
      Navigator.of(context).pop();
    }
  }
}
