package ai.hwga.hwga.widget

import org.json.JSONObject
import java.io.BufferedReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * Thin synchronous HTTP calls for the widgets. Always invoked from a
 * background thread via BroadcastReceiver.goAsync — never on the main thread.
 */
object WidgetApi {
    private const val TIMEOUT_MS = 10_000

    sealed class Result {
        data class Ok(val code: Int, val body: JSONObject?) : Result()
        data class HttpError(val code: Int) : Result()
        object NetworkError : Result()
    }

    fun getWidgetState(baseUrl: String, token: String): Result =
        request("GET", "$baseUrl/widget/state", token, null)

    fun postEvent(
        baseUrl: String,
        token: String,
        type: String,
        kind: String?,
        idempotencyKey: String,
    ): Result {
        val payload = JSONObject().apply {
            put("type", type)
            if (kind != null) put("kind", kind)
            put("idempotency_key", idempotencyKey)
        }
        return request("POST", "$baseUrl/events", token, payload)
    }

    private fun request(
        method: String,
        url: String,
        token: String,
        body: JSONObject?,
    ): Result = try {
        val conn = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = TIMEOUT_MS
            readTimeout = TIMEOUT_MS
            setRequestProperty("Authorization", "Bearer $token")
            setRequestProperty("Accept", "application/json")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }
        try {
            if (body != null) {
                OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use {
                    it.write(body.toString())
                }
            }
            val code = conn.responseCode
            val text = (if (code in 200..299) conn.inputStream else conn.errorStream)
                ?.bufferedReader()?.use(BufferedReader::readText)
            when {
                code in 200..299 -> Result.Ok(
                    code,
                    text?.takeIf { it.isNotBlank() }?.let {
                        runCatching { JSONObject(it) }.getOrNull()
                    },
                )
                else -> Result.HttpError(code)
            }
        } finally {
            conn.disconnect()
        }
    } catch (e: Exception) {
        Result.NetworkError
    }
}
