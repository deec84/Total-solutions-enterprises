package ai.parkshield.android.core.security

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Stores encrypted blobs in private preferences; the AES key is non-exportable Android Keystore material. */
class AndroidKeyStoreSecureValueStore(context: Context) : SecureValueStore {
    private val preferences = context.applicationContext.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

    override suspend fun read(key: String): String? {
        val stored = preferences.getString(key, null) ?: return null
        return try {
            val parts = stored.split(":", limit = 2)
            if (parts.size != 2) throw IllegalArgumentException("invalid encrypted value")
            val iv = Base64.decode(parts[0], Base64.NO_WRAP)
            val ciphertext = Base64.decode(parts[1], Base64.NO_WRAP)
            val cipher = Cipher.getInstance(TRANSFORMATION).apply {
                init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(TAG_LENGTH, iv))
            }
            String(cipher.doFinal(ciphertext), StandardCharsets.UTF_8)
        } catch (error: Exception) {
            throw SecureStorageException.Corrupted(error)
        }
    }

    override suspend fun write(key: String, value: String) {
        try {
            val cipher = Cipher.getInstance(TRANSFORMATION).apply { init(Cipher.ENCRYPT_MODE, secretKey()) }
            val encrypted = cipher.doFinal(value.toByteArray(StandardCharsets.UTF_8))
            val stored = "${Base64.encodeToString(cipher.iv, Base64.NO_WRAP)}:${Base64.encodeToString(encrypted, Base64.NO_WRAP)}"
            check(preferences.edit().putString(key, stored).commit()) { "secure preferences write failed" }
        } catch (error: SecureStorageException) {
            throw error
        } catch (error: Exception) {
            throw SecureStorageException.Unavailable(error)
        }
    }

    override suspend fun remove(key: String) {
        if (!preferences.edit().remove(key).commit()) throw SecureStorageException.Unavailable()
    }

    private fun secretKey(): SecretKey = try {
        val store = KeyStore.getInstance(ANDROID_KEY_STORE).apply { load(null) }
        (store.getKey(KEY_ALIAS, null) as? SecretKey) ?: KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            ANDROID_KEY_STORE,
        ).apply {
            init(
                KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setRandomizedEncryptionRequired(true)
                    .build(),
            )
        }.generateKey()
    } catch (error: Exception) {
        throw SecureStorageException.Unavailable(error)
    }

    private companion object {
        const val PREFERENCES = "parkshield.secure.session"
        const val ANDROID_KEY_STORE = "AndroidKeyStore"
        const val KEY_ALIAS = "parkshield.session.v1"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val TAG_LENGTH = 128
    }
}
