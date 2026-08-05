package ai.parkshield.android.core.security

/** Platform secure storage boundary; no credential implementation is introduced in this phase. */
interface SecureValueStore {
    suspend fun read(key: String): String?
    suspend fun write(key: String, value: String)
    suspend fun remove(key: String)
}
