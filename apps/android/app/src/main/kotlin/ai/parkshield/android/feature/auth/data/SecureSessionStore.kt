package ai.parkshield.android.feature.auth.data

import ai.parkshield.android.core.security.SecureStorageException
import ai.parkshield.android.core.security.SecureValueStore
import ai.parkshield.android.feature.auth.domain.AuthFailure
import ai.parkshield.android.feature.auth.domain.AuthResult
import ai.parkshield.android.feature.auth.domain.TokenPair

class SecureSessionStore(private val store: SecureValueStore) {
    suspend fun save(pair: TokenPair): AuthResult<Unit> = try {
        // Write refresh first; access is only useful with a matching durable refresh token.
        store.write(REFRESH, pair.refreshToken)
        store.write(ACCESS, pair.accessToken)
        AuthResult.Success(Unit)
    } catch (_: SecureStorageException) { clear(); AuthResult.Failure(AuthFailure.SecureStorage) }

    suspend fun refreshToken(): AuthResult<String?> = try { AuthResult.Success(store.read(REFRESH)) }
    catch (_: SecureStorageException) { AuthResult.Failure(AuthFailure.SecureStorage) }

    suspend fun accessToken(): AuthResult<String?> = try { AuthResult.Success(store.read(ACCESS)) }
    catch (_: SecureStorageException) { AuthResult.Failure(AuthFailure.SecureStorage) }

    suspend fun clear() { runCatching { store.remove(ACCESS) }; runCatching { store.remove(REFRESH) } }

    private companion object { const val ACCESS = "access-token-v1"; const val REFRESH = "refresh-token-v1" }
}
