class AuthSession {
  const AuthSession({required this.accessToken, required this.refreshToken});

  final String accessToken;
  final String refreshToken;
}

abstract interface class AuthGateway {
  String get currentRole;
  Future<AuthSession> login({required String email, required String password});
  Future<void> register({required String email, required String password});
  Future<void> requestPasswordReset(String email);
  Future<void> resetPassword(
      {required String token, required String newPassword});
  Future<void> verifyEmail(String token);
  Future<void> logout();
  Future<bool> restoreSession();
}
