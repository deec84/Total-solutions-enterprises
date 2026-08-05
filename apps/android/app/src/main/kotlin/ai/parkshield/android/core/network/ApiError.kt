package ai.parkshield.android.core.network

data class ApiError(
    val version: String,
    val code: String,
    val message: String,
    val correlationId: String,
    val details: List<ApiErrorDetail> = emptyList(),
)

data class ApiErrorDetail(val field: String, val code: String)

object ApiErrorContract {
    const val VERSION = "1"
    private val allowedDetailCodes = setOf("MISSING_FIELD", "INVALID_FIELD")

    fun isValid(error: ApiError): Boolean =
        error.version == VERSION &&
            error.code.isNotBlank() &&
            error.message.isNotBlank() &&
            error.correlationId.matches(Regex("[A-Za-z0-9._:-]{1,128}")) &&
            error.details.all { it.field.matches(Regex("[A-Za-z0-9_.\\[\\]-]{1,128}")) && it.code in allowedDetailCodes }
}
