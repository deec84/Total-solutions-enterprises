package ai.parkshield.android.core.network

/** Feature-owned adapters provide endpoint-specific requests in later vertical slices. */
interface ApiClient {
    suspend fun execute(request: ApiRequest): ApiResult
}

data class ApiRequest(
    val method: String,
    val path: String,
    val body: ByteArray? = null,
)

sealed interface ApiResult {
    data class Success(val statusCode: Int, val body: ByteArray) : ApiResult
    data class Failure(val statusCode: Int, val error: ApiError?) : ApiResult
}
