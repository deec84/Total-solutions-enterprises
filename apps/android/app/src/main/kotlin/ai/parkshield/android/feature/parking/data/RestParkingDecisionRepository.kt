package ai.parkshield.android.feature.parking.data

import ai.parkshield.android.core.network.ApiClient
import ai.parkshield.android.core.network.ApiRequest
import ai.parkshield.android.core.network.ApiResult
import ai.parkshield.android.feature.parking.domain.CoverageStatus
import ai.parkshield.android.feature.parking.domain.ForegroundLocation
import ai.parkshield.android.feature.parking.domain.ParkingDecision
import ai.parkshield.android.feature.parking.domain.ParkingDecisionRepository
import ai.parkshield.android.feature.parking.domain.ParkingEvidence
import ai.parkshield.android.feature.parking.domain.ParkingFailure
import ai.parkshield.android.feature.parking.domain.ParkingOutcome
import ai.parkshield.android.feature.parking.domain.ParkingReason
import ai.parkshield.android.feature.parking.domain.ParkingResult
import org.json.JSONObject
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.time.Instant

/** Transport adapter only: the backend remains the sole parking decision authority. */
class RestParkingDecisionRepository(private val client: ApiClient) : ParkingDecisionRepository {
    override suspend fun evaluate(location: ForegroundLocation, accessToken: String): ParkingResult = try {
        val query = mapOf("latitude" to location.latitude, "longitude" to location.longitude, "accuracy_meters" to location.accuracyMeters, "located_at" to location.locatedAt.toString(), "location_consent" to true).entries.joinToString("&") { "${it.key}=${URLEncoder.encode(it.value.toString(), StandardCharsets.UTF_8)}" }
        when (val response = client.execute(ApiRequest("GET", "/api/v1/parking/decision/evaluate?$query", headers = mapOf("Authorization" to "Bearer $accessToken")))) {
            is ApiResult.Success -> parse(response.body.decodeToString())
            is ApiResult.Failure -> ParkingResult.Failure(if (response.error?.code == "SESSION_INVALID") ParkingFailure.SessionInvalid else ParkingFailure.Service)
        }
    } catch (_: Exception) { ParkingResult.Failure(ParkingFailure.Offline) }

    private fun parse(raw: String): ParkingResult = try {
        val json = JSONObject(raw)
        val reasons = json.getJSONArray("reasons").let { items -> List(items.length()) { i -> items.getJSONObject(i).let { ParkingReason(it.getString("code"), it.getString("message")) } } }
        val evidence = json.optJSONObject("evidence")?.let { item -> ParkingEvidence(item.getString("provenance"), item.getDouble("confidence"), Instant.parse(item.getString("observed_at")), item.optString("expires_at").takeIf { it.isNotBlank() }?.let(Instant::parse), item.optString("source_id").takeIf { it.isNotBlank() }, item.optString("import_batch_id").takeIf { it.isNotBlank() }, item.optString("restriction_summary").takeIf { it.isNotBlank() }) }
        ParkingResult.Decision(ParkingDecision(ParkingOutcome.valueOf(json.getString("outcome")), CoverageStatus.valueOf(json.getString("coverage_status")), reasons, evidence))
    } catch (_: Exception) { ParkingResult.Failure(ParkingFailure.Service) }
}
