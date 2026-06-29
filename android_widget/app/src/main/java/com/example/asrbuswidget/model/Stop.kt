package com.example.asrbuswidget.model

data class Stop(
    val key: String,
    val nameEn: String,
    val nameZh: String,
    val emoji: String,
    val offsetMinutes: Int,
    val lat: Double,
    val lon: Double
)
