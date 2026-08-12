package ai.parkshield.android.core.network

import org.junit.Assert.assertEquals
import org.junit.Test

class ApiBaseUrlProviderTest {
    @Test fun `accepts injectable placeholder url`() { assertEquals("api.invalid", StaticApiBaseUrlProvider("https://api.invalid/").url().host) }
    @Test fun `rejects non placeholder url`() { runCatching { StaticApiBaseUrlProvider("https://example.com/").url() }.onSuccess { throw AssertionError("Expected rejection") } }
}
