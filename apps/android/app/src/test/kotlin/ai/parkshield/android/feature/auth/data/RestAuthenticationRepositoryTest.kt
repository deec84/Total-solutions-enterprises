package ai.parkshield.android.feature.auth.data

import ai.parkshield.android.core.network.ApiClient
import ai.parkshield.android.core.network.ApiError
import ai.parkshield.android.core.network.ApiRequest
import ai.parkshield.android.core.network.ApiResult
import ai.parkshield.android.feature.auth.domain.AuthFailure
import ai.parkshield.android.feature.auth.domain.AuthResult
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RestAuthenticationRepositoryTest {
    @Test fun `login maps public token pair from v1 endpoint`() = runBlocking {
        val client = RecordingClient(ApiResult.Success(200, """{"access_token":"access","refresh_token":"refresh","expires_in":900,"token_type":"bearer"}""".encodeToByteArray()))
        val result = RestAuthenticationRepository(client).login("person@example.test", "password".toCharArray())
        assertEquals("/api/v1/auth/login", client.request?.path)
        assertTrue(result is AuthResult.Success)
    }

    @Test fun `session invalid maps to terminal typed failure`() = runBlocking {
        val error = ApiError("1", "SESSION_INVALID", "Session is invalid.", "correlation-test")
        val result = RestAuthenticationRepository(RecordingClient(ApiResult.Failure(401, error))).refresh("refresh")
        assertEquals(AuthResult.Failure(AuthFailure.SessionInvalid), result)
    }

    @Test fun `remote failures retain only code and correlation id`() = runBlocking {
        val error = ApiError("1", "AUTHENTICATION_FAILED", "Authentication failed.", "correlation-test")
        val result = RestAuthenticationRepository(RecordingClient(ApiResult.Failure(401, error))).login("person@example.test", "password".toCharArray())
        assertEquals(AuthResult.Failure(AuthFailure.Remote("AUTHENTICATION_FAILED", "correlation-test")), result)
    }

    @Test fun `logout accepts only no content success`() = runBlocking {
        val client = RecordingClient(ApiResult.Success(204, ByteArray(0)))
        assertEquals(AuthResult.Success(Unit), RestAuthenticationRepository(client).logout("refresh"))
        assertEquals("/api/v1/auth/logout", client.request?.path)
    }

    @Test fun `login clears the caller password buffer`() = runBlocking {
        val password = "password".toCharArray()
        RestAuthenticationRepository(RecordingClient(ApiResult.Failure(401, null))).login("person@example.test", password)
        assertTrue(password.all { it == '\u0000' })
    }

    private class RecordingClient(private val response: ApiResult) : ApiClient {
        var request: ApiRequest? = null
        override suspend fun execute(request: ApiRequest): ApiResult { this.request = request; return response }
    }
}
