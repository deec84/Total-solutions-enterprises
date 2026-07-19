import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/recovery_page.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/register_page.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/verify_email_page.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({required this.controller, super.key});

  final AuthController controller;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
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
        appBar: AppBar(title: Text(context.l10n.appTitle)),
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 480),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      const Icon(Icons.shield_outlined, size: 72),
                      const SizedBox(height: 24),
                      Text(context.l10n.parkWithConfidence,
                          style: Theme.of(context).textTheme.headlineSmall),
                      const SizedBox(height: 24),
                      TextFormField(
                        controller: _email,
                        autofillHints: const <String>[AutofillHints.email],
                        keyboardType: TextInputType.emailAddress,
                        decoration:
                            InputDecoration(labelText: context.l10n.email),
                        validator: (String? value) =>
                            value != null && value.contains('@')
                                ? null
                                : context.l10n.enterValidEmail,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _password,
                        obscureText: true,
                        autofillHints: const <String>[AutofillHints.password],
                        decoration:
                            InputDecoration(labelText: context.l10n.password),
                        validator: (String? value) =>
                            value != null && value.length >= 12
                                ? null
                                : context.l10n.passwordMinimum,
                      ),
                      if (widget.controller.failure
                          case final AuthFailure failure) ...<Widget>[
                        const SizedBox(height: 16),
                        Semantics(
                          liveRegion: true,
                          child: Text(switch (failure) {
                            AuthFailure.signIn => context.l10n.authSignInError,
                            AuthFailure.request =>
                              context.l10n.authRequestError,
                          }),
                        ),
                      ],
                      const SizedBox(height: 24),
                      FilledButton(
                        onPressed:
                            widget.controller.submitting ? null : _submit,
                        child: widget.controller.submitting
                            ? const SizedBox.square(
                                dimension: 20,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : Text(context.l10n.signIn),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).push<void>(
                          MaterialPageRoute<void>(
                            builder: (_) =>
                                RecoveryPage(controller: widget.controller),
                          ),
                        ),
                        child: Text(context.l10n.forgotPassword),
                      ),
                      OutlinedButton(
                        onPressed: () => Navigator.of(context).push<void>(
                          MaterialPageRoute<void>(
                            builder: (_) =>
                                RegisterPage(controller: widget.controller),
                          ),
                        ),
                        child: Text(context.l10n.createAccount),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).push<void>(
                          MaterialPageRoute<void>(
                            builder: (_) =>
                                VerifyEmailPage(controller: widget.controller),
                          ),
                        ),
                        child: Text(context.l10n.verifyEmail),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      );

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    await widget.controller.login(email: _email.text, password: _password.text);
  }
}
