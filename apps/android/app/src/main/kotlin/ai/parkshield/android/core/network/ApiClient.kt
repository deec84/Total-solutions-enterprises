package ai.parkshield.android.core.network

import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedOutputStream
import java.net.HttpURLConnection
import java.net.URL

/** Feature-owned adapters provide endpoint-specific requests in later vertical slices. */
interface ApiClient {
    suspend fun execute(request: ApiRequest): ApiResult
}

data class ApiRequest(
    val method: String,
    val path: String,
    val body: ByteArray? = null,
    val headers: Map<String, String> = emptyMap(),
)

sealed interface ApiResult {
    data class Success(val statusCode: Int, val body: ByteArray) : ApiResult
    data class Failure(val statusCode: Int, val error: ApiError?) : ApiResult
}

class HttpUrlConnectionApiClient(private val baseUrl: URL) : ApiClient {
    override suspend fun execute(request: ApiRequest): ApiResult {
        val url = URL(baseUrl, request.path.removePrefix("/"))
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = request.method
            connectTimeout = TIMEOUT_MS
            readTimeout = TIMEOUT_MS
            setRequestProperty("Accept", "application/json")
            request.headers.forEach(::setRequestProperty)
            request.body?.let { payload ->
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                BufferedOutputStream(outputStream).use { it.write(payload) }
            }
        }
        return try {
            val status = connection.responseCode
            val body = (if (status in 200..299) connection.inputStream else connection.errorStream)
                ?.use { it.readBytes() } ?: ByteArray(0)
            if (status in 200..299) ApiResult.Success(status, body)
            else ApiResult.Failure(status, parseError(body))
        } finally {
            connection.disconnect()
        }
    }

    private fun parseError(body: ByteArray): ApiError? = try {
        val json = JSONObject(body.decodeToString())
        val details = json.optJSONArray("details")?.toDetails() ?: emptyList()
        ApiError(
            version = json.getString("version"), code = json.getString("code"),
            message = json.getString("message"), correlationId = json.getString("correlation_id"), details = details,
        ).takeIf(ApiErrorContract::isValid)
    } catch (_: Exception) { null }

    private fun JSONArray.toDetails(): List<ApiErrorDetail> = buildList {
        for (index in 0 until length()) {
            val value = getJSONObject(index)
            add(ApiErrorDetail(value.getString("field"), value.getString("code")))
        }
    }

    private companion object { const val TIMEOUT_MS = 15_000 }
}
