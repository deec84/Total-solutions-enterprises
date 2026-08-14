package ai.parkshield.android.core.network

import org.junit.Assert.assertEquals
import org.junit.Test

class ApiBaseUrlProviderTest {
    @Test fun `accepts injectable placeholder url`() { assertEquals("api.invalid", StaticApiBaseUrlProvider("https://api.invalid/").url().host) }
    @Test fun `rejects HTTP and hosts outside the allowlist`() {
        runCatching { StaticApiBaseUrlProvider("http://api.invalid/").url() }.onSuccess { throw AssertionError("Expected rejection") }
        runCatching { StaticApiBaseUrlProvider("https://other.invalid/", "api.invalid").url() }.onSuccess { throw AssertionError("Expected rejection") }
    }
}
