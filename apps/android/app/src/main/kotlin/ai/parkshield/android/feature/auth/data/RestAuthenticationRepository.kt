package ai.parkshield.android.feature.auth.data

import ai.parkshield.android.core.network.ApiClient
import ai.parkshield.android.core.network.ApiRequest
import ai.parkshield.android.core.network.ApiResult
import ai.parkshield.android.feature.auth.domain.AuthFailure
import ai.parkshield.android.feature.auth.domain.AuthResult
import ai.parkshield.android.feature.auth.domain.AuthenticatedUser
import ai.parkshield.android.feature.auth.domain.AuthenticationRepository
import ai.parkshield.android.feature.auth.domain.TokenPair
import org.json.JSONObject

class RestAuthenticationRepository(private val client: ApiClient) : AuthenticationRepository {
    override suspend fun login(email: String, password: CharArray): AuthResult<TokenPair> = try {
        executePair("/api/v1/auth/login", JSONObject().put("email", email).put("password", password.concatToString()))
    } finally {
        password.fill('\u0000')
    }

    override suspend fun refresh(refreshToken: String): AuthResult<TokenPair> =
        executePair("/api/v1/auth/refresh", JSONObject().put("refresh_token", refreshToken))

    override suspend fun logout(refreshToken: String): AuthResult<Unit> = when (val result = client.execute(
        ApiRequest("POST", "/api/v1/auth/logout", JSONObject().put("refresh_token", refreshToken).toString().encodeToByteArray()),
    )) {
        is ApiResult.Success -> if (result.statusCode == 204) AuthResult.Success(Unit) else AuthResult.Failure(AuthFailure.Transport)
        is ApiResult.Failure -> AuthResult.Failure(result.failure())
    }

    override suspend fun profile(accessToken: String): AuthResult<AuthenticatedUser> = when (val result = client.execute(
        ApiRequest("GET", "/api/v1/auth/me", headers = mapOf("Authorization" to "Bearer $accessToken")),
    )) {
        is ApiResult.Success -> try {
            val body = JSONObject(result.body.decodeToString())
            AuthResult.Success(AuthenticatedUser(body.getString("id"), body.getString("email"), body.getString("role"), body.getBoolean("is_verified")))
        } catch (_: Exception) { AuthResult.Failure(AuthFailure.Transport) }
        is ApiResult.Failure -> AuthResult.Failure(result.failure())
    }

    private suspend fun executePair(path: String, body: JSONObject): AuthResult<TokenPair> = when (val result = client.execute(
        ApiRequest("POST", path, body.toString().encodeToByteArray()),
    )) {
        is ApiResult.Success -> try {
            val json = JSONObject(result.body.decodeToString())
            AuthResult.Success(TokenPair(json.getString("access_token"), json.getString("refresh_token"), json.getLong("expires_in"), json.optString("token_type", "bearer")))
        } catch (_: Exception) { AuthResult.Failure(AuthFailure.Transport) }
        is ApiResult.Failure -> AuthResult.Failure(result.failure())
    }

    private fun ApiResult.Failure.failure(): AuthFailure = when (error?.code) {
        "SESSION_INVALID" -> AuthFailure.SessionInvalid
        null -> AuthFailure.Transport
        else -> AuthFailure.Remote(error.code, error.correlationId)
    }
}
