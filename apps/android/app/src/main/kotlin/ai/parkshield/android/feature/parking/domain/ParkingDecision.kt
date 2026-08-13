package ai.parkshield.android.feature.parking.domain

import java.time.Instant

enum class ParkingOutcome { PARK, CAUTION, DO_NOT_PARK, INDETERMINATE }
enum class CoverageStatus { VERIFIED_COVERAGE, NO_VERIFIED_COVERAGE, STALE_DATA, LOCATION_PRECISION_INSUFFICIENT, UNVERIFIABLE_SOURCE, LOCATION_CONSENT_REQUIRED, LOCATION_STALE }

data class ParkingReason(val code: String, val message: String)
data class ParkingEvidence(val provenance: String, val confidence: Double, val observedAt: Instant, val expiresAt: Instant?, val sourceId: String?, val importBatchId: String?, val restrictionSummary: String?)
data class ParkingDecision(val outcome: ParkingOutcome, val coverageStatus: CoverageStatus, val reasons: List<ParkingReason>, val evidence: ParkingEvidence?)

sealed interface ParkingFailure { data object Offline : ParkingFailure; data object Service : ParkingFailure; data object SessionInvalid : ParkingFailure }
sealed interface ParkingResult { data class Decision(val value: ParkingDecision) : ParkingResult; data class Failure(val value: ParkingFailure) : ParkingResult }
data class ForegroundLocation(val latitude: Double, val longitude: Double, val accuracyMeters: Double, val locatedAt: Instant)
sealed interface LocationState { data object PermissionDenied : LocationState; data object Unavailable : LocationState; data class Available(val value: ForegroundLocation) : LocationState }

interface ParkingDecisionRepository { suspend fun evaluate(location: ForegroundLocation, accessToken: String): ParkingResult }
interface ForegroundLocationProvider { suspend fun current(): LocationState }
