package com.nad.riyadalsalheen.ui.viewmodel

import android.app.Application
import android.util.Log
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nad.riyadalsalheen.data.AppPreferences
import com.nad.riyadalsalheen.data.DEFAULT_FONT_SIZE
import com.nad.riyadalsalheen.data.repository.RiyadSalheenRepository
import com.nad.riyadalsalheen.model.Book
import com.nad.riyadalsalheen.model.Door
import com.nad.riyadalsalheen.model.Hadith
import com.nad.riyadalsalheen.model.HadithDetails
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

const val MIN_SEARCH_LENGTH = 3

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = RiyadSalheenRepository(application)
    private val preferences = AppPreferences(application)
    val packageInfo = application.packageManager.getPackageInfo(application.packageName, 0)

    // UI States
    var books = emptyList<Book>()
    var doors = emptyList<Door>()
    var hadithCount = 0

    val cachedHadiths: MutableMap<Int, HadithDetails> = mutableMapOf()

    var currentHadithId = 0
    val searchResults = mutableStateOf(emptyList<Hadith>())
    val searchQuery = mutableStateOf("")
    val systemTheme = mutableStateOf(true)
    val fontSize = mutableFloatStateOf(DEFAULT_FONT_SIZE)
    val bookmarks = mutableStateOf(emptyList<Hadith>())

    // Loading states
    val isInitialDataLoaded = mutableStateOf(false)
    val isSearching = mutableStateOf(false)

    init {
        viewModelScope.launch {
            books = repository.getAllBooks()
            doors = repository.getAllDoors()
            hadithCount = repository.getHadithsCount()

            fontSize.floatValue = preferences.fontSize.first()
            systemTheme.value = preferences.systemTheme.first()
            updateBookmarks()

            currentHadithId = preferences.readingProgress.first()
            updateCachedHadiths()

            isInitialDataLoaded.value = true
        }
    }

    private fun loadHadithDetails(hadithId: Int): HadithDetails? {
        if(hadithId < 1 || hadithId > hadithCount) {
            return null
        }

        if (cachedHadiths.containsKey(hadithId)) {
            return cachedHadiths[hadithId]
        }

        val hadith = repository.getHadithById(hadithId)
        if (hadith != null) {
            val newHadith = HadithDetails(
                hadith = hadith,
                door = doors[hadith.doorId - 1], // convert door/book id from 1 based to zero based
                book = books[hadith.bookId - 1]
            )
            cachedHadiths[hadithId] = newHadith
            return newHadith
        }
        Log.e("Riad", "Hadith $hadithId doesn't exist in database")
        return null
    }

    private fun updateCachedHadiths() {
        val currentId = currentHadithId
        val minId = (currentId - 3).coerceIn(1, hadithCount)
        val maxId = (currentId + 3).coerceIn(1, hadithCount)

        // Remove unneeded items first for efficiency
        cachedHadiths.entries.removeIf { kotlin.math.abs(it.key - currentId) > 3 }

        (minId..maxId).forEach { idx ->
            loadHadithDetails(idx)
        }
    }

    fun getCurrentHadith(): HadithDetails? {
        return cachedHadiths[currentHadithId]
    }

    fun loadAndGetHadith(hadithId: Int): HadithDetails? {
        if(currentHadithId != hadithId) {
            currentHadithId = hadithId
            updateCachedHadiths()
            viewModelScope.launch {
                preferences.saveReadingProgress(hadithId)
            }
        }
        return cachedHadiths[hadithId]
    }

    fun getFirstHadithIdInDoor(doorId: Int): Int?{
        return repository.getFirstHadithIdInDoor(doorId)
    }

    fun searchHadiths(query: String) {
        if(searchQuery.value == query){
            return
        }

        searchQuery.value = query
        if (query.isBlank()) {
            searchResults.value = emptyList()
            return
        }

        viewModelScope.launch {
            isSearching.value = true
            val trimmedQuery = query.trim()
            val hadithId = trimmedQuery.toIntOrNull()

            searchResults.value = if (hadithId != null) {
                val hadith = repository.getHadithById(hadithId)
                hadith?.let { listOf(it) } ?: repository.searchHadiths(trimmedQuery)
            } else if (trimmedQuery.length >= MIN_SEARCH_LENGTH) {
                repository.searchHadiths(trimmedQuery)
            } else {
                emptyList()
            }
            isSearching.value = false
        }
    }

    private suspend fun updateBookmarks() {
        val initialBookmarks = preferences.bookmarks.first()
        val bookmarkIds = initialBookmarks.mapNotNull { it.toIntOrNull() }
        bookmarks.value = repository.getHadithsByIds(bookmarkIds)
            .sortedBy { hadith -> bookmarkIds.indexOf(hadith.id) }
    }

    fun toggleBookmark(hadithId: Int) {
        viewModelScope.launch {
            preferences.toggleBookmark(hadithId)
            updateBookmarks()
        }
    }

    fun toggleSystemTheme() {
        viewModelScope.launch {
            systemTheme.value = !systemTheme.value
            preferences.saveSystemTheme(systemTheme.value)
        }
    }

    fun updateFontSize(size: Float) {
        viewModelScope.launch {
            fontSize.floatValue = size.coerceIn(14f, 30f)
            preferences.saveFontSize(fontSize.floatValue)
        }
    }

    override fun onCleared() {
        super.onCleared()
        repository.close()
    }

}