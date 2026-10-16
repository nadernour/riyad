package com.nad.riyadalsalheen.data.repository

import android.content.Context
import android.database.Cursor
import com.nad.riyadalsalheen.data.DatabaseHelper
import com.nad.riyadalsalheen.model.Book
import com.nad.riyadalsalheen.model.Door
import com.nad.riyadalsalheen.model.Hadith


class RiyadSalheenRepository(context: Context) {
    private val dbHelper = DatabaseHelper(context)
    private val database by lazy { dbHelper.readableDatabase }
    companion object {
        private const val TABLE_BOOKS = "books"
        private const val TABLE_DOORS = "doors"
        private const val TABLE_HADITHS = "hadiths"

        private const val COLUMN_ID = "id"
        private const val COLUMN_BOOK_ID = "book_id"
        private const val COLUMN_DOOR_ID = "door_id"
        private const val COLUMN_TITLE = "title"
        private const val COLUMN_HADITH = "hadith"
        private const val COLUMN_SHARH = "sharh"
        private const val COLUMN_HADITH_NORMAL = "hadith_normal"

    }

    fun getAllBooks(): List<Book> {
        val books = mutableListOf<Book>()
        val query = "SELECT * FROM $TABLE_BOOKS ORDER BY $COLUMN_ID ASC"
        database.rawQuery(query, null).use { cursor ->
            while (cursor.moveToNext()) {
                books.add(Book(
                    id = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_ID)),
                    title = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_TITLE))
                ))
            }
        }
        return books
    }

    fun getAllDoors(): List<Door> {
        val doors = mutableListOf<Door>()
        val query = "SELECT * FROM $TABLE_DOORS ORDER BY $COLUMN_ID ASC"
        database.rawQuery(query, null).use { cursor ->
            while (cursor.moveToNext()) {
                doors.add(Door(
                    id = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_ID)),
                    bookId = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_BOOK_ID)),
                    title = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_TITLE))
                ))
            }
        }
        return doors
    }

    private fun getHadithFromCursor(cursor: Cursor) : Hadith {
        return Hadith(
            id = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_ID)),
            doorId = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_DOOR_ID)),
            bookId = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_BOOK_ID)),
            title = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_TITLE)),
            matn = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_HADITH)),
            sharh = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_SHARH)),
            matn_normal = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_HADITH_NORMAL))
        )
    }

    // TODO return hadith detail instead of Hadith
    fun getHadithsByDoor(doorId: Int): List<Hadith> {
        val hadiths = mutableListOf<Hadith>()
        val query = "SELECT * FROM $TABLE_HADITHS WHERE $COLUMN_DOOR_ID = ? ORDER BY $COLUMN_ID ASC"
        val selectionArgs = arrayOf(doorId.toString())

        database.rawQuery(query, selectionArgs).use { cursor ->
            while (cursor.moveToNext()) {
                hadiths.add(getHadithFromCursor(cursor))
            }
        }
        return hadiths
    }

    fun getFirstHadithIdInDoor(doorId: Int): Int? {
        val query = "SELECT $COLUMN_ID FROM $TABLE_HADITHS WHERE $COLUMN_DOOR_ID = ? ORDER BY $COLUMN_ID ASC LIMIT 1"
        val selectionArgs = arrayOf(doorId.toString())

        database.rawQuery(query, selectionArgs).use { cursor ->
            if (cursor.moveToFirst()) {
                return cursor.getInt(0) // Get the ID from the first (and only) column
            }
        }
        return null
    }

    fun getHadithById(hadithId: Int): Hadith? {
        val query = "SELECT * FROM $TABLE_HADITHS WHERE $COLUMN_ID = ?"
        val selectionArgs = arrayOf(hadithId.toString())

        database.rawQuery(query, selectionArgs).use { cursor ->
            if (cursor.moveToFirst()) {
                return getHadithFromCursor(cursor)
            }
        }
        return null
    }

    fun getHadithsByIds(ids: List<Int>): List<Hadith> {
        if (ids.isEmpty()) return emptyList()

        val hadiths = mutableListOf<Hadith>()
        val placeholders = ids.joinToString(",") { "?" }
        val query =
            "SELECT * FROM $TABLE_HADITHS WHERE $COLUMN_ID IN ($placeholders) ORDER BY $COLUMN_ID ASC"
        val selectionArgs = ids.map { it.toString() }.toTypedArray()

        database.rawQuery(query, selectionArgs).use { cursor ->
            while (cursor.moveToNext()) {
                hadiths.add(getHadithFromCursor(cursor))
            }
        }
        return hadiths
    }

    fun searchHadiths(searchQuery: String): List<Hadith> {
        val hadiths = mutableListOf<Hadith>()
        val query = """
            SELECT * FROM $TABLE_HADITHS 
            WHERE $COLUMN_HADITH_NORMAL LIKE ?
            ORDER BY $COLUMN_ID ASC
            LIMIT 100
        """
        val searchPattern = "%$searchQuery%"
        val selectionArgs = arrayOf(searchPattern)

        database.rawQuery(query, selectionArgs).use { cursor ->
            while (cursor.moveToNext()) {
                hadiths.add(getHadithFromCursor(cursor))
            }
        }
        return hadiths
    }

    fun close() {
        database.close()
        dbHelper.close()
    }

    fun getHadithsCount(): Int {
        val query = "SELECT COUNT(*) FROM $TABLE_HADITHS"
        database.rawQuery(query, null).use { cursor ->
            if (cursor.moveToFirst()) {
                return cursor.getInt(0) // Returns the count from the first column
            }
        }
        return 0
    }
}