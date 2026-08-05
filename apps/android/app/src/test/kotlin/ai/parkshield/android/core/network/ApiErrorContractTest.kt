package ai.parkshield.android.core.network

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ApiErrorContractTest {
    @Test
    fun `accepts the public v1 validation error`() {
        assertTrue(
            ApiErrorContract.isValid(
                ApiError(
                    version = "1",
                    code = "VALIDATION_FAILED",
                    message = "Invalid request.",
                    correlationId = "fixture-validation-failed",
                    details = listOf(ApiErrorDetail("password", "MISSING_FIELD")),
                ),
            ),
        )
    }

    @Test
    fun `rejects non allowlisted error detail`() {
        assertFalse(
            ApiErrorContract.isValid(
                ApiError("1", "VALIDATION_FAILED", "Invalid request.", "fixture", listOf(ApiErrorDetail("password", "RAW_MESSAGE"))),
            ),
        )
    }
}
