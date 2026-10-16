package com.nad.riyadalsalheen.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

const val DEFAULT_FONT_SIZE = 24f

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class AppPreferences(private val context: Context) {
    companion object {
        val SYSTEM_THEME = booleanPreferencesKey("SYSTEM_THEME")
        val FONT_SIZE = floatPreferencesKey("font_size")
        val BOOKMARKS = stringPreferencesKey("bookmarks")
        val READING_PROGRESS = intPreferencesKey("reading_progress")
    }

    // Save dark theme preference
    // Save theme mode preference
    suspend fun saveSystemTheme(systemTheme: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[SYSTEM_THEME] = systemTheme
        }
    }

    // Get theme mode preference
    val systemTheme: Flow<Boolean> = context.dataStore.data
        .map { preferences ->
            preferences[SYSTEM_THEME] ?: true
        }

    // Save font size
    suspend fun saveFontSize(size: Float) {
        context.dataStore.edit { preferences ->
            preferences[FONT_SIZE] = size
        }
    }

    // Get font size
    val fontSize: Flow<Float> = context.dataStore.data
        .map { preferences ->
            preferences[FONT_SIZE] ?: DEFAULT_FONT_SIZE
        }

    suspend fun toggleBookmark(hadithId: Int) {
        context.dataStore.edit { preferences ->
            // Get as comma-separated string and convert to list
            val bookmarksString = preferences[BOOKMARKS] ?: ""
            val currentBookmarks = if (bookmarksString.isEmpty()) {
                emptyList()
            } else {
                bookmarksString.split(",")
            }

            if(currentBookmarks.contains(hadithId.toString())) {
                // Remove the bookmark
                val updated = currentBookmarks - hadithId.toString()
                preferences[BOOKMARKS] = updated.joinToString(",")
            } else {
                // Add at the start (most recent first)
                val updated = listOf(hadithId.toString()) + currentBookmarks
                preferences[BOOKMARKS] = updated.joinToString(",")
            }
        }
    }

    // Get bookmarks
    val bookmarks: Flow<List<String>> = context.dataStore.data
        .map { preferences ->
            val bookmarksString = preferences[BOOKMARKS] ?: ""
            if (bookmarksString.isEmpty()) {
                emptyList()
            } else {
                bookmarksString.split(",")
            }
        }

    // Save reading progress
    suspend fun saveReadingProgress(hadithId: Int) {
        context.dataStore.edit { preferences ->
            preferences[READING_PROGRESS] = hadithId
        }
    }

    // Get reading progress
    val readingProgress: Flow<Int> = context.dataStore.data
        .map { preferences ->
            preferences[READING_PROGRESS] ?: 1
        }

    // Clear all preferences
    suspend fun clearAll() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }
}