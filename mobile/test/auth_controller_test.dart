import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_controller.dart';

class ConfigurableGateway implements AuthGateway {
  ConfigurableGateway({this.sessionExists = false, this.failLogin = false});

  bool sessionExists;
  bool failLogin;

  @override
  String get currentRole => 'user';

  @override
  Future<bool> restoreSession() async => sessionExists;

  @override
  Future<AuthSession> login(
      {required String email, required String password}) async {
    if (failLogin) throw Exception('failure');
    sessionExists = true;
    return const AuthSession(accessToken: 'access', refreshToken: 'refresh');
  }

  @override
  Future<void> register(
      {required String email, required String password}) async {
    if (failLogin) throw Exception('failure');
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    if (failLogin) throw Exception('failure');
  }

  @override
  Future<void> resetPassword(
      {required String token, required String newPassword}) async {
    if (failLogin) throw Exception('failure');
  }

  @override
  Future<void> verifyEmail(String token) async {
    if (failLogin) throw Exception('failure');
  }

  @override
  Future<void> logout() async => sessionExists = false;
}

void main() {
  test('initializes, signs in, and signs out', () async {
    final ConfigurableGateway gateway = ConfigurableGateway();
    final AuthController controller = AuthController(gateway);

    await controller.initialize();
    expect(controller.status, AuthStatus.signedOut);
    await controller.login(
        email: 'person@example.com', password: 'secure-password');
    expect(controller.status, AuthStatus.signedIn);
    expect(controller.errorMessage, isNull);
    await controller.logout();
    expect(controller.status, AuthStatus.signedOut);

    await controller.login(
        email: 'person@example.com', password: 'secure-password');
    controller.accountDeleted();
    expect(controller.status, AuthStatus.signedOut);
    expect(controller.userRole, 'user');
  });

  test('keeps the user signed out after a login failure', () async {
    final AuthController controller = AuthController(
      ConfigurableGateway(failLogin: true),
    );
    await controller.initialize();

    await controller.login(
        email: 'person@example.com', password: 'wrong-password');

    expect(controller.status, AuthStatus.signedOut);
    expect(controller.submitting, isFalse);
    expect(controller.errorMessage, isNotNull);
  });
}
