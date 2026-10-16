package com.nad.riyadalsalheen.data

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class DatabaseHelper(context: Context)
    : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {
    companion object {
        private const val DATABASE_NAME = "riyad_salheen.db"
        private const val DATABASE_VERSION = 1
    }

    private val databasePath by lazy {
        context.getDatabasePath(DATABASE_NAME).path
    }

    init{
        if (!checkDatabase()) {
            try {
                copyDatabase(context)
            } catch (e: IOException) {
                throw Error("Error copying database: ${e.message}")
            }
        }
    }

    private fun checkDatabase(): Boolean {
        try {
            val dbFile = File(databasePath)
            if (!dbFile.exists() || !dbFile.canRead()  || dbFile.length() == 0L) {
                return false
            }
            val dp = SQLiteDatabase.openDatabase(databasePath, null, SQLiteDatabase.OPEN_READONLY)
            if (dp.version != DATABASE_VERSION) {
                return false
            }

            dp.close()
            return true
        } catch (_: Exception) {
            return false
        }
    }

    private fun copyDatabase(context: Context) {
        Log.d("databaseLogs", "copyDatabase")
        val input = context.assets.open("databases/$DATABASE_NAME")
        val output = FileOutputStream(databasePath)
        input.copyTo(output)
        input.close()
        output.close()

        // Now that the file is copied, open it and set its version
        val db = SQLiteDatabase.openDatabase(databasePath, null, SQLiteDatabase.OPEN_READWRITE)
        db.version = DATABASE_VERSION // This sets the pragma to 1
        db.close()
    }

    override fun getReadableDatabase(): SQLiteDatabase {
        return SQLiteDatabase.openDatabase(databasePath, null, SQLiteDatabase.OPEN_READONLY)
    }

    override fun onCreate(db: SQLiteDatabase) {
        // Database is copied from assets
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // Handle database upgrades
    }
}