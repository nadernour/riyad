package com.nad.riyadalsalheen.ui.components

import android.app.Activity
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat

@Composable
fun HideSystemBars() {
    val view = LocalView.current
    // A DisposableEffect runs side effects that need to be cleaned up
    // when the composable leaves the composition.
    DisposableEffect(Unit) {
        // Get the window insets controller
        val window = (view.context as Activity).window
        val windowInsetsController = WindowCompat.getInsetsController(window, view)

        // Configure the behavior for showing transient bars by swipe
        windowInsetsController.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE

        // Hide the system bars
        windowInsetsController.hide(WindowInsetsCompat.Type.systemBars())

        onDispose {
            // Re-show the system bars when the composable is disposed
            windowInsetsController.show(WindowInsetsCompat.Type.systemBars())
        }
    }
}