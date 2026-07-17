import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class MemoryTokenStore implements TokenStore {
  MemoryTokenStore({this.accessToken, this.refreshToken});

  String? accessToken;
  String? refreshToken;
  int saveCalls = 0;
  int clearCalls = 0;

  @override
  Future<void> save(AuthSession session) async {
    accessToken = session.accessToken;
    refreshToken = session.refreshToken;
    saveCalls += 1;
  }

  @override
  Future<String?> readAccessToken() async => accessToken;

  @override
  Future<String?> readRefreshToken() async => refreshToken;

  @override
  Future<void> clear() async {
    accessToken = null;
    refreshToken = null;
    clearCalls += 1;
  }
}
