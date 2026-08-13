package ai.parkshield.android.feature.parking

import ai.parkshield.android.core.network.ApiClient
import ai.parkshield.android.core.network.ApiRequest
import ai.parkshield.android.core.network.ApiResult
import ai.parkshield.android.feature.parking.data.RestParkingDecisionRepository
import ai.parkshield.android.feature.parking.domain.ForegroundLocation
import ai.parkshield.android.feature.parking.domain.ParkingOutcome
import ai.parkshield.android.feature.parking.domain.ParkingResult
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
}
