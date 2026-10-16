package com.nad.riyadalsalheen.ui.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp

enum class TextType {
    HADITH,
    SHARH;
}

@Composable
fun HtmlText(
    htmlText: String,
    textType: TextType,
    modifier: Modifier = Modifier,
    fontSize: TextUnit = 18.sp,
    lineHeight: TextUnit = TextUnit.Unspecified,
    color: Color = MaterialTheme.colorScheme.onSurface,
    style: TextStyle = LocalTextStyle.current
) {
    val styleList = when (textType) {
        TextType.HADITH -> listOf(
            SpanStyle(fontWeight = FontWeight.Bold),
            SpanStyle(fontWeight = FontWeight.SemiBold),
            SpanStyle(fontWeight = FontWeight.Medium)
        )

        TextType.SHARH -> listOf(
            SpanStyle(fontWeight = FontWeight.Bold),
            SpanStyle(fontWeight = FontWeight.Bold),
            SpanStyle(fontWeight = FontWeight.Bold)
        )
    }
    // Regex to split the string by all known tags, keeping the tags
    val tagPattern = "(</?p[0-2]>|<bullet>|\\n)"
    val regex = Regex("(?=${tagPattern})|(?<=${tagPattern})")
    val tokens = htmlText.split(regex).filter { it.isNotEmpty() }

    val annotatedString = buildAnnotatedString {
        // These booleans track the *current* style state
        var isP0 = false
        var isP1 = false
        var isP2 = false

        for (token in tokens) {
            when (token) {
                // Update state on open tags
                "<p0>" -> isP0 = true
                "<p1>" -> isP1 = true
                "<p2>" -> isP2 = true
                "</p0>" -> isP0 = false
                "</p1>" -> isP1 = false
                "</p2>" -> isP2 = false
                // Handle newlines
                "\n" -> append("\n")
                "<bullet>" -> append("■")
                // Handle a text token
                else -> {
                    val currentStyle = if (isP0) {
                        styleList[0]
                    } else if (isP1) {
                        styleList[1]
                    } else if (isP2) {
                        styleList[2]
                    } else {
                        SpanStyle() // Default style for untagged text
                    }

                    // Append the text with the final, merged style
                    withStyle(style = currentStyle) {
                        append(token)
                    }
                }
            }
        }
    }
    Text(
        text = annotatedString,
        modifier = modifier.fillMaxWidth(),
        fontSize = fontSize,
        lineHeight = lineHeight,
        color = color,
        style = style
    )
}