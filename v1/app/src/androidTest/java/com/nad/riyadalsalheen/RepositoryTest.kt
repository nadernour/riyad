package com.nad.riyadalsalheen

import android.util.Log
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.nad.riyadalsalheen.data.repository.RiyadSalheenRepository
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Instrumented test, which will execute on an Android device.
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
@RunWith(AndroidJUnit4::class)
class RepositoryTest {

    private lateinit var repository: RiyadSalheenRepository

    companion object {
        private const val TAG = "RepositoryTest"
    }

    @Before
    fun setup() {
        Log.d(TAG, "Setting up test...")
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        repository = RiyadSalheenRepository(context)
        Log.d(TAG, "Repository initialized")
    }

    @Test
    fun testAllBookDoors_returnsNonEmptyList() {
        Log.d(TAG, "Starting test: testGetFirstBookDoors_returnsNonEmptyList")

        // When
        val doors = repository.getAllDoors()
        val books = repository.getAllBooks()
        Log.d(TAG, "Retrieved books ${books.size} books")
        Log.d(TAG, "Retrieved doors ${doors.size} doors")

        // Then
        assertTrue("Books list should not be empty", books.isNotEmpty())
        assertTrue("Doors list should not be empty", doors.isNotEmpty())
        Log.d(TAG, "Test passed: door and book list is not empty")

        // Log door details for debugging
        var allDoorIndicesExist = true
        for(i in 1..doors.size) {
            if(doors[i - 1].id != i) {
                allDoorIndicesExist = false
                Log.d(TAG, "Could not find door with index: $i")
                break
            }
        }

        assertTrue("Some doors are missing", allDoorIndicesExist)
        Log.d(TAG, "Test passed: no doors are missing")


        // Log book details for debugging
        var allBookIndicesExist = true
        for(i in 1..books.size) {
            if(books[i - 1].id != i) {
                allBookIndicesExist = false
                Log.d(TAG, "Could not find book with index: $i")
                break
            }
        }

        assertTrue("Some books are missing", allBookIndicesExist)
        Log.d(TAG, "Test passed: no books are missing")
    }

    @Test
    fun testGetAllHadithsAvailable_returnNonEmptyTitle() {
        Log.d(TAG, "Starting test: testGetFirstAndLastHadith_returnNonEmptyTitle")

        val count = repository.getHadithsCount()
        Log.d(TAG, "Retrieved hadiths count ${count} hadiths")

        // Then
        assertTrue("Hadiths list should not be empty", count > 0)
        Log.d(TAG, "Test passed: hadith count retrieved $count")

        // When
        var allHadithIndicesExist = true
        for(i in 1..count) {
            val hadith = repository.getHadithById(i)
            if(hadith == null) {
                allHadithIndicesExist = false
                Log.d(TAG, "Could not find hadith with index: $i")
            }
        }

        assertTrue("Some hadiths are missing", allHadithIndicesExist)
        Log.d(TAG, "Test passed: no hadiths are missing")
    }
}