package com.nad.riyadalsalheen.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import com.nad.riyadalsalheen.R

// Set of Material typography styles to start with
val AmiriFontFamily = FontFamily(
    Font(R.font.amiri, FontWeight.Normal),
    Font(R.font.amiri_bold, FontWeight.Bold)
)

val CairoFontFamily = FontFamily(
    Font(R.font.cairo, FontWeight.Normal),
    Font(R.font.cairo_semibold, FontWeight.SemiBold),
    Font(R.font.cairo_bold, FontWeight.Bold)
)

val NotoSansFontFamily = FontFamily(
    Font(R.font.noto_sans_arabic, FontWeight.Normal),
    Font(R.font.noto_sans_arabic_medium, FontWeight.Medium),
    Font(R.font.noto_sans_arabic_medium, FontWeight.SemiBold),
    Font(R.font.noto_sans_arabic_bold, FontWeight.Bold)
)

// Default Material 3 typography values
val baseline = Typography()

val Typography = Typography(
    displayLarge = baseline.displayLarge.copy(fontFamily = CairoFontFamily),
    displayMedium = baseline.displayMedium.copy(fontFamily = CairoFontFamily),
    displaySmall = baseline.displaySmall.copy(fontFamily = CairoFontFamily),
    headlineLarge = baseline.headlineLarge.copy(fontFamily = CairoFontFamily),
    headlineMedium = baseline.headlineMedium.copy(fontFamily = CairoFontFamily),
    headlineSmall = baseline.headlineSmall.copy(fontFamily = CairoFontFamily),
    titleLarge = baseline.titleLarge.copy(fontFamily = CairoFontFamily),
    titleMedium = baseline.titleMedium.copy(fontFamily = CairoFontFamily),
    titleSmall = baseline.titleSmall.copy(fontFamily = CairoFontFamily),
    bodyLarge = baseline.bodyLarge.copy(fontFamily = AmiriFontFamily),
    bodyMedium = baseline.bodyMedium.copy(fontFamily = CairoFontFamily),
    bodySmall = baseline.bodySmall.copy(fontFamily = CairoFontFamily),
    labelLarge = baseline.labelLarge.copy(fontFamily = CairoFontFamily),
    labelMedium = baseline.labelMedium.copy(fontFamily = CairoFontFamily),
    labelSmall = baseline.labelSmall.copy(fontFamily = CairoFontFamily),
)

val Typography2 = Typography(
    displayLarge = baseline.displayLarge.copy(fontFamily = NotoSansFontFamily),
    displayMedium = baseline.displayMedium.copy(fontFamily = NotoSansFontFamily),
    displaySmall = baseline.displaySmall.copy(fontFamily = NotoSansFontFamily),
    headlineLarge = baseline.headlineLarge.copy(fontFamily = NotoSansFontFamily),
    headlineMedium = baseline.headlineMedium.copy(fontFamily = NotoSansFontFamily),
    headlineSmall = baseline.headlineSmall.copy(fontFamily = NotoSansFontFamily),
    titleLarge = baseline.titleLarge.copy(fontFamily = NotoSansFontFamily),
    titleMedium = baseline.titleMedium.copy(fontFamily = NotoSansFontFamily),
    titleSmall = baseline.titleSmall.copy(fontFamily = NotoSansFontFamily),
    bodyLarge = baseline.bodyLarge.copy(fontFamily = NotoSansFontFamily),
    bodyMedium = baseline.bodyMedium.copy(fontFamily = NotoSansFontFamily),
    bodySmall = baseline.bodySmall.copy(fontFamily = NotoSansFontFamily),
    labelLarge = baseline.labelLarge.copy(fontFamily = NotoSansFontFamily),
    labelMedium = baseline.labelMedium.copy(fontFamily = NotoSansFontFamily),
    labelSmall = baseline.labelSmall.copy(fontFamily = NotoSansFontFamily),
)