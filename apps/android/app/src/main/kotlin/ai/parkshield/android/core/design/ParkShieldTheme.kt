package ai.parkshield.android.core.design

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

object ParkShieldTokens {
    val Brand = Color(0xFF155EEF)
    val Surface = Color(0xFFFFFFFF)
    val OnSurface = Color(0xFF101828)
    val Danger = Color(0xFFB42318)
}

@Composable
fun ParkShieldTheme(content: @Composable () -> Unit = {}) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = ParkShieldTokens.Brand,
            surface = ParkShieldTokens.Surface,
            onSurface = ParkShieldTokens.OnSurface,
            error = ParkShieldTokens.Danger,
        ),
        content = content,
    )
}
