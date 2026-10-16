package com.nad.riyadalsalheen.model

data class Hadith(
    val id: Int,
    val doorId: Int,
    val bookId: Int,
    val title: String,
    val matn: String,
    val sharh: String,
    val matn_normal: String
)

data class HadithDetails(val hadith: Hadith, val door: Door, val book: Book)