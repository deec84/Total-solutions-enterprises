package ai.parkshield.android.feature.auth.data

import ai.parkshield.android.feature.auth.domain.AuthFailure
import ai.parkshield.android.feature.auth.domain.AuthResult
import ai.parkshield.android.feature.auth.domain.AuthenticationRepository
import ai.parkshield.android.feature.auth.domain.TokenPair
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

sealed interface SessionState { data object SignedOut : SessionState; data object Restoring : SessionState; data object SignedIn : SessionState; data class Failed(val error: AuthFailure) : SessionState }

/** Composition-root state holder. The mutex makes refresh single-flight within this app process. */
class SessionController(private val repository: AuthenticationRepository, private val sessions: SecureSessionStore) {
    private val refreshMutex = Mutex()
    var state: SessionState = SessionState.SignedOut
        private set

    suspend fun restore(): SessionState {
        return refreshMutex.withLock {
            state = SessionState.Restoring
            refreshInternal()
        }
    }

    suspend fun login(email: String, password: CharArray): SessionState = when (val result = repository.login(email, password)) {
        is AuthResult.Success -> persist(result.value)
        is AuthResult.Failure -> fail(result.error)
    }

    suspend fun refresh(): SessionState = refreshMutex.withLock { refreshInternal() }

    suspend fun logout(): SessionState {
        val refresh = sessions.refreshToken()
        if (refresh is AuthResult.Success && refresh.value != null) repository.logout(refresh.value)
        sessions.clear()
        state = SessionState.SignedOut
        return state
    }

    private suspend fun refreshInternal(): SessionState = when (val stored = sessions.refreshToken()) {
        is AuthResult.Failure -> fail(stored.error)
        is AuthResult.Success -> when (val token = stored.value) {
            null -> { state = SessionState.SignedOut; state }
            else -> when (val result = repository.refresh(token)) {
                is AuthResult.Success -> persist(result.value)
                is AuthResult.Failure -> { sessions.clear(); fail(result.error) }
            }
        }
    }

    private suspend fun persist(pair: TokenPair): SessionState = when (val saved = sessions.save(pair)) {
        is AuthResult.Success -> { state = SessionState.SignedIn; state }
        is AuthResult.Failure -> fail(saved.error)
    }

    private fun fail(error: AuthFailure): SessionState { state = SessionState.Failed(error); return state }
}
