package com.example.asrbuswidget.data

import com.example.asrbuswidget.model.Stop
import com.example.asrbuswidget.model.Trip
import com.example.asrbuswidget.model.TripType

object BusSchedule {

    val STOPS = mapOf(
        "asr" to Stop("asr", "ASR", "ASR", "🏠", 0, 1.276626, 103.830288),
        "outram6" to Stop("outram6", "Outram Exit 6", "欧南园6号口", "🚇", 6, 1.2789872116033196, 103.83856904062411),
        "outram7" to Stop("outram7", "Outram Exit 7", "欧南园7号口", "🚇", 8, 1.280980927082586, 103.83878336326352),
        "harbourfront" to Stop("harbourfront", "Harbourfront", "港湾", "🛍️", 10, 1.265883572108345, 103.82149497860111),
    )

    val TRIP_STOPS = mapOf(
        TripType.A to listOf("asr", "outram6", "outram7"),
        TripType.B to listOf("asr", "harbourfront"),
    )

    val DESTINATIONS_EN = mapOf(
        TripType.A to "🚇 Outram Park",
        TripType.B to "🛍️ Harbourfront",
    )

    val DESTINATIONS_ZH = mapOf(
        TripType.A to "🚇 欧南园",
        TripType.B to "🛍️ 港湾",
    )

    val WEEKDAY_TRIPS = listOf(
        Trip("07:20", TripType.A), Trip("07:40", TripType.A),
        Trip("08:00", TripType.A), Trip("08:20", TripType.A),
        Trip("08:40", TripType.A), Trip("09:00", TripType.A),
        Trip("09:30", TripType.A), Trip("10:00", TripType.B),
        Trip("10:30", TripType.A), Trip("11:00", TripType.B),
        Trip("11:30", TripType.A), Trip("13:00", TripType.B),
        Trip("13:30", TripType.A), Trip("14:00", TripType.B),
        Trip("14:30", TripType.A), Trip("15:00", TripType.B),
        Trip("16:30", TripType.A), Trip("17:00", TripType.B),
        Trip("17:30", TripType.A), Trip("18:00", TripType.B),
        Trip("18:30", TripType.A), Trip("19:00", TripType.B),
        Trip("19:30", TripType.A), Trip("20:00", TripType.B),
    )

    val SATURDAY_TRIPS = listOf(
        Trip("09:00", TripType.A), Trip("09:30", TripType.B),
        Trip("10:00", TripType.A), Trip("10:30", TripType.B),
        Trip("11:00", TripType.A), Trip("11:30", TripType.B),
        Trip("12:00", TripType.A), Trip("12:30", TripType.B),
        Trip("14:00", TripType.A), Trip("14:30", TripType.B),
        Trip("15:00", TripType.A), Trip("15:30", TripType.B),
        Trip("16:00", TripType.A), Trip("16:30", TripType.B),
        Trip("18:00", TripType.A), Trip("18:30", TripType.B),
        Trip("19:00", TripType.A), Trip("19:30", TripType.B),
        Trip("20:00", TripType.A), Trip("20:30", TripType.B),
    )
}
