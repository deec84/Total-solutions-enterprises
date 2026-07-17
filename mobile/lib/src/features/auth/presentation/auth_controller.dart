import 'package:flutter/foundation.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

enum AuthStatus { checking, signedOut, signedIn }

class AuthController extends ChangeNotifier {
  AuthController(this._gateway);

  final AuthGateway _gateway;
  AuthStatus status = AuthStatus.checking;
  bool submitting = false;
  String? errorMessage;
  String userRole = 'user';

  Future<void> initialize() async {
    status = await _gateway.restoreSession()
        ? AuthStatus.signedIn
        : AuthStatus.signedOut;
    userRole = _gateway.currentRole;
    notifyListeners();
  }

  Future<void> login({required String email, required String password}) async {
    submitting = true;
    errorMessage = null;
    notifyListeners();
    try {
      await _gateway.login(email: email.trim(), password: password);
      userRole = _gateway.currentRole;
      status = AuthStatus.signedIn;
    } on Exception {
      errorMessage = 'Unable to sign in. Check your credentials.';
    } finally {
      submitting = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _gateway.logout();
    status = AuthStatus.signedOut;
    userRole = 'user';
    notifyListeners();
  }

  Future<bool> register(
          {required String email, required String password}) async =>
      _runAction(
          () => _gateway.register(email: email.trim(), password: password));

  Future<bool> requestPasswordReset(String email) async =>
      _runAction(() => _gateway.requestPasswordReset(email.trim()));

  Future<bool> verifyEmail(String token) async =>
      _runAction(() => _gateway.verifyEmail(token.trim()));

  Future<bool> resetPassword(
          {required String token, required String newPassword}) async =>
      _runAction(
        () => _gateway.resetPassword(
            token: token.trim(), newPassword: newPassword),
      );

  Future<bool> _runAction(Future<void> Function() action) async {
    submitting = true;
    errorMessage = null;
    notifyListeners();
    try {
      await action();
      return true;
    } on Exception {
      errorMessage = 'The request could not be completed. Please try again.';
      return false;
    } finally {
      submitting = false;
      notifyListeners();
    }
  }
}
