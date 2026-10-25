package ai.hwga.hwga.widget

import android.content.Context
import android.content.SharedPreferences
import android.util.Base64
import ai.hwga.hwga.BuildConfig
import org.json.JSONObject
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Widget-side config + credential access (V2-D03, V2-D04).
 *
 * Token: prefers a direct decrypt of the flutter_secure_storage 11.2.0
 * shared-prefs ciphertext (AES/GCM key unwrapped via the Keystore RSA-OAEP
 * alias); falls back to the plaintext mirror that widget_bridge.dart pushes
 * into [PREFS] on each app resume. Any failure yields null, which the widget
 * renders as its auth-required state.
 *
 * Base URL: prefers the runtime URL mirrored by the app; falls back to the
 * compiled-in [BuildConfig.HWGA_API_BASE_URL]. Blank/absent yields the
 * "open the app once" state — never a guessed URL.
 */
object WidgetStore {
    const val PREFS = "hwga_widget_prefs"
    private const val KEY_BASE_URL = "base_url"
    private const val KEY_TOKEN_MIRROR = "token_mirror"
    private const val KEY_STATE_JSON = "widget_state_json"

    // flutter_secure_storage 11.2.0 constants (verified in V2A probe 1).
    private const val FSS_PREFS = "FlutterSecureStorage"
    private const val FSS_KEY_PREFS = "FlutterSecureKeyStorage"
    private const val FSS_PREFIX =
        "VGhpcyBpcyB0aGUgcHJlZml4IGZvciBhIHNlY3VyZSBzdG9yYWdlCg"
    private const val FSS_AES_KEY_NAME =
        "AESVGhpcyBpcyB0aGUga2V5IGZvciBhIHNlY3VyZSBzdG9yYWdlIEFFUyBLZXkK"
    private const val FSS_KEYSTORE_ALIAS =
        "ai.hwga.hwga.FlutterSecureStoragePluginKeyOAEP"
    private const val TOKEN_KEY = "hwga_auth_token"
    private const val GCM_IV_LEN = 12
    private const val GCM_TAG_BITS = 128

    fun prefs(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun baseUrl(context: Context): String? {
        val mirrored = prefs(context).getString(KEY_BASE_URL, null)
        if (!mirrored.isNullOrBlank()) return mirrored
        val compiled = BuildConfig.HWGA_API_BASE_URL
        return compiled.ifBlank { null }
    }

    fun readToken(context: Context): String? =
        readSecureStorageToken(context)
            ?: prefs(context).getString(KEY_TOKEN_MIRROR, null)?.takeIf { it.isNotBlank() }

    fun mirror(context: Context, token: String?, baseUrl: String, stateJson: String?) {
        prefs(context).edit()
            .putString(KEY_TOKEN_MIRROR, token)
            .putString(KEY_BASE_URL, baseUrl)
            .putString(KEY_STATE_JSON, stateJson)
            .apply()
    }

    fun cachedState(context: Context): JSONObject? =
        prefs(context).getString(KEY_STATE_JSON, null)
            ?.let { runCatching { JSONObject(it) }.getOrNull() }

    fun cacheState(context: Context, json: String) {
        prefs(context).edit().putString(KEY_STATE_JSON, json).apply()
    }

    /** Direct decrypt of the flutter_secure_storage ciphertext; null on any failure. */
    private fun readSecureStorageToken(context: Context): String? = runCatching {
        val storagePrefs = context.getSharedPreferences(FSS_PREFS, Context.MODE_PRIVATE)
        val encoded = storagePrefs.getString("${FSS_PREFIX}_$TOKEN_KEY", null)
            ?: return null
        val payload = Base64.decode(encoded.filterNot { it.isWhitespace() }, Base64.DEFAULT)

        val keyPrefs = context.getSharedPreferences(FSS_KEY_PREFS, Context.MODE_PRIVATE)
        val wrappedKey = keyPrefs.getString(FSS_AES_KEY_NAME, null)
            ?.let { Base64.decode(it.filterNot(Char::isWhitespace), Base64.DEFAULT) }
            ?: return null

        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val privateKey = (ks.getEntry(FSS_KEYSTORE_ALIAS, null)
                as? KeyStore.PrivateKeyEntry)?.privateKey ?: return null
        val rsa = Cipher.getInstance("RSA/ECB/OAEPwithSHA-256andMGF1Padding")
        rsa.init(Cipher.DECRYPT_MODE, privateKey)
        val aesKey = SecretKeySpec(rsa.doFinal(wrappedKey), "AES")

        val iv = payload.copyOfRange(0, GCM_IV_LEN)
        val ciphertext = payload.copyOfRange(GCM_IV_LEN, payload.size)
        val aes = Cipher.getInstance("AES/GCM/NoPadding")
        aes.init(Cipher.DECRYPT_MODE, aesKey, GCMParameterSpec(GCM_TAG_BITS, iv))
        String(aes.doFinal(ciphertext), Charsets.UTF_8).takeIf { it.isNotBlank() }
    }.getOrNull()
}
