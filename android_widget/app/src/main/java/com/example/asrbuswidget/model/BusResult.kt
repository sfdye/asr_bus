package com.example.asrbuswidget.model

sealed class BusResult {
    object NoSundayService : BusResult()
    object NoMoreBuses : BusResult()
    data class Upcoming(val buses: List<BusArrival>) : BusResult()
}

data class BusArrival(
    val arrivalTime: String,
    val minutesAway: Int,
    val destination: String,
    val tripType: TripType
)
