package com.example.asrbuswidget.model

enum class TripType { A, B }

data class Trip(
    val departureTime: String,
    val type: TripType
)
