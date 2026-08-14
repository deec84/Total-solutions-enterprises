package ai.parkshield.android.core.network

import java.net.URL

fun interface ApiBaseUrlProvider { fun url(): URL }

class StaticApiBaseUrlProvider(private val value: String, allowedHosts: String = "api.invalid") : ApiBaseUrlProvider {
    private val allowed = allowedHosts.split(',').map(String::trim).filter(String::isNotEmpty).toSet()
    override fun url(): URL = URL(value).also { require(it.protocol == "https" && it.host in allowed) }
}
