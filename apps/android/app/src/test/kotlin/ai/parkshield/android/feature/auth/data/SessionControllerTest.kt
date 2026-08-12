package ai.parkshield.android.feature.auth.data

import ai.parkshield.android.core.security.SecureStorageException
import ai.parkshield.android.core.security.SecureValueStore
import ai.parkshield.android.feature.auth.domain.AuthFailure
import ai.parkshield.android.feature.auth.domain.AuthResult
import ai.parkshield.android.feature.auth.domain.AuthenticatedUser
import ai.parkshield.android.feature.auth.domain.AuthenticationRepository
import ai.parkshield.android.feature.auth.domain.TokenPair
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.atomic.AtomicInteger

class SessionControllerTest {
    @Test fun `login persists only in secure storage`() = runBlocking {
        val secure = MemorySecureStore()
        val controller = SessionController(FakeRepository(loginResult = AuthResult.Success(pair)), SecureSessionStore(secure))
        assertEquals(SessionState.SignedIn, controller.login("person@example.test", "password".toCharArray()))
        assertEquals(pair.refreshToken, secure.values["refresh-token-v1"])
        assertFalse(secure.values.values.any { it.contains("password") })
    }

    @Test fun `restore refreshes expired access token and replaces both credentials`() = runBlocking {
        val secure = MemorySecureStore(mapOf("refresh-token-v1" to "old-refresh", "access-token-v1" to "old-access"))
        val controller = SessionController(FakeRepository(refreshResult = AuthResult.Success(pair)), SecureSessionStore(secure))
        assertEquals(SessionState.SignedIn, controller.restore())
        assertEquals(pair.refreshToken, secure.values["refresh-token-v1"])
        assertEquals(pair.accessToken, secure.values["access-token-v1"])
    }

    @Test fun `concurrent refresh is single flight`() = runBlocking {
        val secure = MemorySecureStore(mapOf("refresh-token-v1" to "old-refresh"))
        val repository = FakeRepository(refreshResult = AuthResult.Success(pair), refreshDelay = true)
        val controller = SessionController(repository, SecureSessionStore(secure))
        val states = List(8) { async { controller.refresh() } }.awaitAll()
        assertTrue(states.all { it == SessionState.SignedIn })
        assertEquals(1, repository.refreshCalls.get())
        assertEquals(SessionState.SignedIn, controller.refresh())
        assertEquals(2, repository.refreshCalls.get())
    }

    @Test fun `concurrent session invalid is shared and clears credentials`() = runBlocking {
        val secure = MemorySecureStore(mapOf("refresh-token-v1" to "old-refresh", "access-token-v1" to "old-access"))
        val repository = FakeRepository(refreshResult = AuthResult.Failure(AuthFailure.SessionInvalid), refreshDelay = true)
        val controller = SessionController(repository, SecureSessionStore(secure))
        val states = List(2) { async { controller.refresh() } }.awaitAll()
        assertTrue(states.all { it == SessionState.SignedOut })
        assertEquals(1, repository.refreshCalls.get())
        assertTrue(secure.values.isEmpty())
        assertEquals(SessionState.SignedOut, controller.refresh())
        assertEquals(1, repository.refreshCalls.get())
    }

    @Test fun `logout invokes remote endpoint then clears credentials even on remote failure`() = runBlocking {
        val secure = MemorySecureStore(mapOf("refresh-token-v1" to "old-refresh", "access-token-v1" to "old-access"))
        val repository = FakeRepository(logoutResult = AuthResult.Failure(AuthFailure.Transport))
        val controller = SessionController(repository, SecureSessionStore(secure))
        assertEquals(SessionState.SignedOut, controller.logout())
        assertEquals(1, repository.logoutCalls.get())
        assertTrue(secure.values.isEmpty())
    }

    @Test fun `secure storage unavailability fails closed`() = runBlocking {
        val secure = MemorySecureStore(failWrites = true)
        val controller = SessionController(FakeRepository(loginResult = AuthResult.Success(pair)), SecureSessionStore(secure))
        assertEquals(SessionState.Failed(AuthFailure.SecureStorage), controller.login("person@example.test", "password".toCharArray()))
        assertTrue(secure.values.isEmpty())
    }

    private class MemorySecureStore(initial: Map<String, String> = emptyMap(), private val failWrites: Boolean = false) : SecureValueStore {
        val values = initial.toMutableMap()
        override suspend fun read(key: String) = values[key]
        override suspend fun write(key: String, value: String) { if (failWrites) throw SecureStorageException.Unavailable(); values[key] = value }
        override suspend fun remove(key: String) { values.remove(key) }
    }

    private class FakeRepository(
        private val loginResult: AuthResult<TokenPair> = AuthResult.Failure(AuthFailure.Transport),
        private val refreshResult: AuthResult<TokenPair> = AuthResult.Failure(AuthFailure.Transport),
        private val logoutResult: AuthResult<Unit> = AuthResult.Success(Unit),
        private val refreshDelay: Boolean = false,
    ) : AuthenticationRepository {
        val refreshCalls = AtomicInteger(); val logoutCalls = AtomicInteger()
        override suspend fun login(email: String, password: CharArray) = loginResult
        override suspend fun refresh(refreshToken: String): AuthResult<TokenPair> { refreshCalls.incrementAndGet(); if (refreshDelay) delay(50); return refreshResult }
        override suspend fun logout(refreshToken: String): AuthResult<Unit> { logoutCalls.incrementAndGet(); return logoutResult }
        override suspend fun profile(accessToken: String): AuthResult<AuthenticatedUser> = AuthResult.Failure(AuthFailure.Transport)
    }
    private companion object { val pair = TokenPair("access-new", "refresh-new", 900, "bearer") }
}
