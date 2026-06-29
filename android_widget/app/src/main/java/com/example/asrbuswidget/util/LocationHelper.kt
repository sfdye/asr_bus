package com.example.asrbuswidget.util

import android.location.Location
import com.example.asrbuswidget.data.BusSchedule
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

object LocationHelper {

    fun getNearestStop(location: Location): String {
        return getNearestStop(location.latitude, location.longitude)
    }

    fun getNearestStop(lat: Double, lon: Double): String {
        var bestKey = "asr"
        var bestDist = Double.MAX_VALUE

        for ((key, stop) in BusSchedule.STOPS) {
            val d = haversineDistance(lat, lon, stop.lat, stop.lon)
            if (d < bestDist) {
                bestDist = d
                bestKey = key
            }
        }
        return bestKey
    }

    private fun haversineDistance(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val r = 6371000.0
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        val a = sin(dLat / 2) * sin(dLat / 2) +
            cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) *
            sin(dLon / 2) * sin(dLon / 2)
        return r * 2 * atan2(sqrt(a), sqrt(1 - a))
    }
}
