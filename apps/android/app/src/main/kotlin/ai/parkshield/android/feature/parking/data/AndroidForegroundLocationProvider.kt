package ai.parkshield.android.feature.parking.data

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationManager
import android.os.Handler
import android.os.Looper
import ai.parkshield.android.feature.parking.domain.ForegroundLocation
import ai.parkshield.android.feature.parking.domain.ForegroundLocationProvider
import ai.parkshield.android.feature.parking.domain.LocationState
import kotlinx.coroutines.suspendCancellableCoroutine
import java.time.Instant
import kotlin.coroutines.resume

/** One foreground fix only. This adapter neither logs nor persists device coordinates. */
class AndroidForegroundLocationProvider(private val context: Context) : ForegroundLocationProvider {
    private val manager = context.getSystemService(LocationManager::class.java)
    @SuppressLint("MissingPermission") override suspend fun current(): LocationState = suspendCancellableCoroutine { continuation ->
        val provider = when { manager.isProviderEnabled(LocationManager.GPS_PROVIDER) -> LocationManager.GPS_PROVIDER; manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER) -> LocationManager.NETWORK_PROVIDER; else -> null }
        if (provider == null) { continuation.resume(LocationState.Unavailable); return@suspendCancellableCoroutine }
        manager.getCurrentLocation(provider, null, { command -> Handler(Looper.getMainLooper()).post(command) }) { location: Location? ->
            if (!continuation.isCompleted) continuation.resume(location?.toState() ?: LocationState.Unavailable)
        }
    }
    private fun Location.toState() = LocationState.Available(ForegroundLocation(latitude, longitude, accuracy.toDouble(), Instant.ofEpochMilli(time)))
}
