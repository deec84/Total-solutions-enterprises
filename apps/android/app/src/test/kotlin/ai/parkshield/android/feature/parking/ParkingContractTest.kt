package ai.parkshield.android.feature.parking

import ai.parkshield.android.core.network.ApiClient
import ai.parkshield.android.core.network.ApiRequest
import ai.parkshield.android.core.network.ApiResult
import ai.parkshield.android.feature.parking.data.RestParkingDecisionRepository
import ai.parkshield.android.feature.parking.domain.ForegroundLocation
import ai.parkshield.android.feature.parking.domain.ParkingOutcome
import ai.parkshield.android.feature.parking.domain.ParkingResult
import ai.parkshield.android.feature.parking.domain.ParkingFailure
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.Instant

class ParkingContractTest {
    @Test fun `backend PARK is displayed as PARK without client calculation`() = runBlocking {
        val client = ApiClient { _: ApiRequest -> ApiResult.Success(200, """{"outcome":"PARK","coverage_status":"VERIFIED_COVERAGE","reasons":[{"code":"OFFICIAL_RESTRICTION","message":"Official evidence permits parking."}],"evaluated_at":"2026-01-01T00:00:00Z","evidence":null}""".encodeToByteArray()) }
        val result = RestParkingDecisionRepository(client).evaluate(ForegroundLocation(1.0, 2.0, 10.0, Instant.now()), "synthetic-token")
        assertEquals(ParkingOutcome.PARK, (result as ParkingResult.Decision).value.outcome)
    }

    @Test fun `all backend outcomes are preserved without local rules`() = runBlocking {
        listOf("CAUTION", "DO_NOT_PARK", "INDETERMINATE").forEach { outcome ->
            val body = """{"outcome":"$outcome","coverage_status":"NO_VERIFIED_COVERAGE","reasons":[{"code":"NO_VERIFIED_COVERAGE","message":"No verified coverage."}],"evaluated_at":"2026-01-01T00:00:00Z","evidence":null}"""
            val result = RestParkingDecisionRepository(ApiClient { ApiResult.Success(200, body.encodeToByteArray()) }).evaluate(ForegroundLocation(1.0, 2.0, 10.0, Instant.now()), "synthetic-token")
            assertEquals(outcome, (result as ParkingResult.Decision).value.outcome.name)
        }
    }

    @Test fun `invalid session is distinct from service and offline failures`() = runBlocking {
        val invalid = RestParkingDecisionRepository(ApiClient { ApiResult.Failure(401, ai.parkshield.android.core.network.ApiError("1", "SESSION_INVALID", "Safe", "correlation", emptyList())) }).evaluate(ForegroundLocation(1.0, 2.0, 10.0, Instant.now()), "synthetic-token")
        assertEquals(ParkingFailure.SessionInvalid, (invalid as ParkingResult.Failure).value)
    }
}
