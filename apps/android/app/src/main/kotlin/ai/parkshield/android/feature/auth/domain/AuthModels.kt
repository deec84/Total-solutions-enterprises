package ai.parkshield.android.feature.auth.domain

data class TokenPair(
    val accessToken: String,
    val refreshToken: String,
    val expiresInSeconds: Long,
    val tokenType: String,
)

data class AuthenticatedUser(val id: String, val email: String, val role: String, val isVerified: Boolean)

sealed interface AuthFailure {
    data class Remote(val code: String, val correlationId: String?) : AuthFailure
    data object SessionInvalid : AuthFailure
    data object Transport : AuthFailure
    data object SecureStorage : AuthFailure
}

sealed interface AuthResult<out T> {
    data class Success<T>(val value: T) : AuthResult<T>
    data class Failure(val error: AuthFailure) : AuthResult<Nothing>
}

interface AuthenticationRepository {
    suspend fun login(email: String, password: CharArray): AuthResult<TokenPair>
    suspend fun refresh(refreshToken: String): AuthResult<TokenPair>
    suspend fun logout(refreshToken: String): AuthResult<Unit>
    suspend fun profile(accessToken: String): AuthResult<AuthenticatedUser>
}
