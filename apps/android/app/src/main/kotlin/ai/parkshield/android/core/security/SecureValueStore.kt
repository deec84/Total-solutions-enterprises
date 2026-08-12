package ai.parkshield.android.core.security

/** Credential boundary. Implementations must never log values written through this interface. */
interface SecureValueStore {
    suspend fun read(key: String): String?
    suspend fun write(key: String, value: String)
    suspend fun remove(key: String)
}

sealed class SecureStorageException(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class Unavailable(cause: Throwable? = null) : SecureStorageException("Secure storage is unavailable", cause)
    class Corrupted(cause: Throwable? = null) : SecureStorageException("Secure storage value is corrupted", cause)
}
