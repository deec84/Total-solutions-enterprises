package ai.parkshield.android.feature.auth.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import ai.parkshield.android.feature.auth.domain.AuthFailure
import kotlinx.coroutines.launch

sealed interface AuthUiState { data object Restoring : AuthUiState; data object SignedOut : AuthUiState; data object SignedIn : AuthUiState; data class Failed(val error: AuthFailure) : AuthUiState }

@Composable
fun AuthApp(restore: suspend () -> AuthUiState, login: suspend (String, CharArray) -> AuthUiState, logout: suspend () -> AuthUiState) {
    var session by remember { mutableStateOf<AuthUiState>(AuthUiState.Restoring) }
    LaunchedEffect(Unit) { session = restore() }
    when (session) {
        AuthUiState.Restoring -> Splash()
        AuthUiState.SignedIn -> AuthenticatedShell(onLogout = { session = logout() })
        AuthUiState.SignedOut -> Login(onLogin = { email, password -> session = login(email, password) })
        is AuthUiState.Failed -> Login(error = (session as AuthUiState.Failed).error, onLogin = { email, password -> session = login(email, password) })
    }
}

@Composable private fun Splash() = Column(Modifier.fillMaxSize().semantics { contentDescription = "Restoring session" }, verticalArrangement = Arrangement.Center) { CircularProgressIndicator(Modifier.padding(24.dp)) }

@Composable private fun Login(error: AuthFailure? = null, onLogin: suspend (String, CharArray) -> Unit) {
    var email by remember { mutableStateOf("") }; var password by remember { mutableStateOf("") }; var loading by remember { mutableStateOf(false) }
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("Welcome to ParkShield AI")
        OutlinedTextField(email, { email = it }, Modifier.fillMaxWidth().semantics { contentDescription = "Email" }, label = { Text("Email") }, enabled = !loading)
        OutlinedTextField(password, { password = it }, Modifier.fillMaxWidth().semantics { contentDescription = "Password" }, label = { Text("Password") }, visualTransformation = PasswordVisualTransformation(), enabled = !loading)
        error?.let { Text(errorMessage(it), Modifier.semantics { contentDescription = "Login error" }) }
        Button(enabled = !loading && email.isNotBlank() && password.isNotEmpty(), onClick = { loading = true; scope.launch { onLogin(email, password.toCharArray()); password = ""; loading = false } }, modifier = Modifier.fillMaxWidth()) { Text(if (loading) "Signing in" else "Sign in") }
    }
}

@Composable private fun AuthenticatedShell(onLogout: suspend () -> Unit) { val scope = androidx.compose.runtime.rememberCoroutineScope(); Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) { Text("You are signed in"); Button(onClick = { scope.launch { onLogout() } }) { Text("Sign out") } } }

private fun errorMessage(error: AuthFailure): String = when (error) { AuthFailure.SessionInvalid -> "Your session has ended. Please sign in again."; is AuthFailure.Remote -> if (error.code == "RATE_LIMITED") "Too many attempts. Please wait and try again." else "Email or password is incorrect."; AuthFailure.Transport -> "Unable to sign in right now."; AuthFailure.SecureStorage -> "Secure storage is unavailable." }
