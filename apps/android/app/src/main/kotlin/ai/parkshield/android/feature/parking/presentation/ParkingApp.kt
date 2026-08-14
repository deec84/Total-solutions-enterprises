package ai.parkshield.android.feature.parking.presentation

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import ai.parkshield.android.feature.parking.domain.CoverageStatus
import ai.parkshield.android.feature.parking.domain.ForegroundLocationProvider
import ai.parkshield.android.feature.parking.domain.LocationState
import ai.parkshield.android.feature.parking.domain.ParkingDecision
import ai.parkshield.android.feature.parking.domain.ParkingDecisionRepository
import ai.parkshield.android.feature.parking.domain.ParkingFailure
import ai.parkshield.android.feature.parking.domain.ParkingOutcome
import ai.parkshield.android.feature.parking.domain.ParkingResult
import kotlinx.coroutines.launch

sealed interface ParkingUiState { data object Ready : ParkingUiState; data object Loading : ParkingUiState; data class Decision(val value: ParkingDecision) : ParkingUiState; data class LocationIssue(val message: String) : ParkingUiState; data class Failure(val value: ParkingFailure) : ParkingUiState }

@Composable
fun ParkingApp(provider: ForegroundLocationProvider, repository: ParkingDecisionRepository, accessToken: suspend () -> String?, onSessionInvalid: suspend () -> Unit, onLogout: suspend () -> Unit) {
    var state by remember { mutableStateOf<ParkingUiState>(ParkingUiState.Ready) }
    val scope = androidx.compose.runtime.rememberCoroutineScope(); val context = LocalContext.current
    suspend fun evaluate() {
        state = ParkingUiState.Loading
        when (val location = provider.current()) {
            LocationState.PermissionDenied -> state = ParkingUiState.LocationIssue("Location permission is required to check parking.")
            LocationState.Unavailable -> state = ParkingUiState.LocationIssue("Your location is unavailable. Try again when GPS is ready.")
            is LocationState.Available -> {
                val token = accessToken()
                if (token == null) { onSessionInvalid(); return }
                when (val result = repository.evaluate(location.value, token)) {
                    is ParkingResult.Decision -> state = ParkingUiState.Decision(result.value)
                    is ParkingResult.Failure -> if (result.value == ParkingFailure.SessionInvalid) onSessionInvalid() else state = ParkingUiState.Failure(result.value)
                }
            }
        }
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { granted ->
        if (granted.values.any { it }) scope.launch { evaluate() } else state = ParkingUiState.LocationIssue("Location permission was denied. You can enable it in system settings.")
    }
    fun requestDecision() { if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) scope.launch { evaluate() } else permission.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)) }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        when (val current = state) {
            ParkingUiState.Ready -> Text("Check parking at your current location")
            ParkingUiState.Loading -> CircularProgressIndicator(Modifier.semantics { contentDescription = "Checking parking" })
            is ParkingUiState.LocationIssue -> Notice(current.message)
            is ParkingUiState.Failure -> Notice(if (current.value == ParkingFailure.Offline) "No connection. Check your network and try again." else "Parking service is unavailable. Please try again.")
            is ParkingUiState.Decision -> Decision(current.value)
        }
        Button(enabled = state !is ParkingUiState.Loading, onClick = ::requestDecision, modifier = Modifier.fillMaxWidth()) { Text("Check parking") }
        Button(onClick = { scope.launch { onLogout() } }, modifier = Modifier.fillMaxWidth()) { Text("Sign out") }
    }
}
@Composable private fun Notice(message: String) { Text(message, Modifier.semantics { contentDescription = "Parking status: $message" }) }
@Composable private fun Decision(value: ParkingDecision) {
    val headline = when (value.outcome) { ParkingOutcome.PARK -> "Parking may be allowed"; ParkingOutcome.CAUTION -> "Use caution"; ParkingOutcome.DO_NOT_PARK -> "Do not park"; ParkingOutcome.INDETERMINATE -> "Parking cannot be determined" }
    Column(Modifier.semantics { contentDescription = "Parking decision: $headline" }) {
        Text(headline)
        value.reasons.forEach { Text(it.message) }
        Text("Coverage: ${value.coverageStatus.name.replace('_', ' ').lowercase()}")
        value.evidence?.let { Text("Source: ${it.provenance}. Confidence: ${(it.confidence * 100).toInt()}%. Observed: ${it.observedAt}. Expires: ${it.expiresAt ?: "not provided"}.") }
        if (value.outcome != ParkingOutcome.PARK || value.coverageStatus != CoverageStatus.VERIFIED_COVERAGE) Text("Review current parking signs before parking.")
    }
}
