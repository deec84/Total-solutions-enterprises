package ai.parkshield.android.core.persistence

/** Non-sensitive feature cache boundary. Persistent schemas remain feature-owned. */
interface KeyValueStore {
    suspend fun read(key: String): String?
    suspend fun write(key: String, value: String)
    suspend fun remove(key: String)
}
