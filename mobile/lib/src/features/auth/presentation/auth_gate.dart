import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/data/auth_api.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/login_page.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/reset_password_page.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';
import 'package:parkshield_mobile/src/features/bootstrap/presentation/bootstrap_page.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({
    required this.apiBaseUrl,
    required this.mapTileUrl,
    this.gateway,
    this.linkStream,
    super.key,
  });

  final String apiBaseUrl;
  final String mapTileUrl;
  final AuthGateway? gateway;
  final Stream<Uri>? linkStream;

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  late final AuthController _controller;
  StreamSubscription<Uri>? _linkSubscription;

  @override
  void initState() {
    super.initState();
    _controller = AuthController(
      widget.gateway ??
          AuthApi(baseUrl: widget.apiBaseUrl, tokenStore: SecureTokenStore()),
    )..addListener(_rebuild);
    final Stream<Uri> links = widget.linkStream ?? AppLinks().uriLinkStream;
    _linkSubscription = links.listen(_handleLink);
    _controller.initialize();
  }

  @override
  void dispose() {
    _controller
      ..removeListener(_rebuild)
      ..dispose();
    _linkSubscription?.cancel();
    super.dispose();
  }

  void _rebuild() => setState(() {});

  Future<void> _handleLink(Uri uri) async {
    if (uri.scheme != 'parkshield') return;
    final String? token = uri.queryParameters['token'];
    if (token == null || token.isEmpty || !mounted) return;
    if (uri.host == 'verify-email') {
      final bool verified = await _controller.verifyEmail(token);
      if (verified && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.emailVerified)),
        );
      }
    } else if (uri.host == 'reset-password') {
      await Navigator.of(context).push<void>(
        MaterialPageRoute<void>(
          builder: (_) => ResetPasswordPage(
            controller: _controller,
            initialToken: token,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) => switch (_controller.status) {
        AuthStatus.checking => const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          ),
        AuthStatus.signedOut => LoginPage(controller: _controller),
        AuthStatus.signedIn => BootstrapPage(
            apiBaseUrl: widget.apiBaseUrl,
            mapTileUrl: widget.mapTileUrl,
            userRole: _controller.userRole,
            onLogout: _controller.logout,
            onAccountDeleted: _controller.accountDeleted,
          ),
      };
}
