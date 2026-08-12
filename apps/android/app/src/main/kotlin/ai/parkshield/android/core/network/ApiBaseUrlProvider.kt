package ai.parkshield.android.core.network

import java.net.URL

fun interface ApiBaseUrlProvider { fun url(): URL }

class StaticApiBaseUrlProvider(private val value: String) : ApiBaseUrlProvider {
    override fun url(): URL = URL(value).also { require(it.protocol == "https" && it.host.endsWith(".invalid")) }
}
