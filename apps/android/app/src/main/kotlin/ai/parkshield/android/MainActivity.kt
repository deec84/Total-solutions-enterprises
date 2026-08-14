package ai.parkshield.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import ai.parkshield.android.core.design.ParkShieldTheme
import ai.parkshield.android.BuildConfig
import ai.parkshield.android.core.network.HttpUrlConnectionApiClient
import ai.parkshield.android.core.network.StaticApiBaseUrlProvider
import ai.parkshield.android.core.security.AndroidKeyStoreSecureValueStore
import ai.parkshield.android.feature.auth.data.RestAuthenticationRepository
import ai.parkshield.android.feature.auth.data.SecureSessionStore
import ai.parkshield.android.feature.auth.data.SessionController
import ai.parkshield.android.feature.auth.presentation.AuthApp
import ai.parkshield.android.feature.auth.presentation.AuthUiState
import ai.parkshield.android.feature.auth.data.SessionState
import ai.parkshield.android.feature.auth.domain.AuthResult
import ai.parkshield.android.feature.parking.data.AndroidForegroundLocationProvider
import ai.parkshield.android.feature.parking.data.RestParkingDecisionRepository
import ai.parkshield.android.feature.parking.presentation.ParkingApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val controller = SessionController(
            RestAuthenticationRepository(HttpUrlConnectionApiClient(StaticApiBaseUrlProvider(BuildConfig.PARKSHIELD_API_BASE_URL, BuildConfig.PARKSHIELD_API_ALLOWED_HOSTS).url())),
            SecureSessionStore(AndroidKeyStoreSecureValueStore(this)),
        )
        fun uiState(state: SessionState): AuthUiState = when (state) { SessionState.Restoring -> AuthUiState.Restoring; SessionState.SignedIn -> AuthUiState.SignedIn; SessionState.SignedOut -> AuthUiState.SignedOut; is SessionState.Failed -> AuthUiState.Failed(state.error) }
        val client = HttpUrlConnectionApiClient(StaticApiBaseUrlProvider(BuildConfig.PARKSHIELD_API_BASE_URL, BuildConfig.PARKSHIELD_API_ALLOWED_HOSTS).url())
        val parking = RestParkingDecisionRepository(client)
        setContent { ParkShieldTheme { AuthApp(restore = { uiState(controller.restore()) }, login = { email, password -> uiState(controller.login(email, password)) }, logout = { uiState(controller.logout()) }) { logout -> ParkingApp(AndroidForegroundLocationProvider(this), parking, accessToken = { when (val token = controller.accessToken()) { is AuthResult.Success -> token.value; is AuthResult.Failure -> null } }, onSessionInvalid = { controller.logout() }, onLogout = logout) } } }
    }
}
