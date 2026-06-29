package com.example.asrbuswidget.util

import com.example.asrbuswidget.data.BusSchedule
import com.example.asrbuswidget.model.BusArrival
import com.example.asrbuswidget.model.BusResult
import com.example.asrbuswidget.model.Trip
import java.util.Calendar
import java.util.Locale

object ScheduleCalculator {

    fun getNextBuses(
        stopKey: String,
        now: Calendar,
        holidays: Map<String, List<String>>?,
        locale: Locale = Locale.getDefault()
    ): BusResult {
        val dayType = getDayType(now, holidays)
        val trips = getTripsForDay(dayType) ?: return BusResult.NoSundayService

        val stop = BusSchedule.STOPS[stopKey] ?: return BusResult.NoMoreBuses
        val nowMins = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE)
        val results = mutableListOf<BusArrival>()

        val destinations = if (locale.language == "zh") BusSchedule.DESTINATIONS_ZH else BusSchedule.DESTINATIONS_EN

        for (trip in trips) {
            val tripStops = BusSchedule.TRIP_STOPS[trip.type] ?: continue
            if (stopKey !in tripStops) continue

            val arrivalTime = addMinutes(trip.departureTime, stop.offsetMinutes)
            val arrivalMins = timeToMinutes(arrivalTime)
            if (arrivalMins >= nowMins) {
                results.add(
                    BusArrival(
                        arrivalTime = arrivalTime,
                        minutesAway = arrivalMins - nowMins,
                        destination = destinations[trip.type] ?: "",
                        tripType = trip.type
                    )
                )
            }
            if (results.size >= 2) break
        }

        return if (results.isEmpty()) BusResult.NoMoreBuses else BusResult.Upcoming(results)
    }

    fun getTripsForDay(dayType: DayType): List<Trip>? {
        return when (dayType) {
            DayType.WEEKDAY -> BusSchedule.WEEKDAY_TRIPS
            DayType.SATURDAY -> BusSchedule.SATURDAY_TRIPS
            DayType.SUNDAY -> null
        }
    }

    fun getAllTripsForStop(stopKey: String, dayType: DayType, locale: Locale = Locale.getDefault()): List<BusArrival> {
        val trips = getTripsForDay(dayType) ?: return emptyList()
        val stop = BusSchedule.STOPS[stopKey] ?: return emptyList()
        val destinations = if (locale.language == "zh") BusSchedule.DESTINATIONS_ZH else BusSchedule.DESTINATIONS_EN
        val results = mutableListOf<BusArrival>()

        for (trip in trips) {
            val tripStops = BusSchedule.TRIP_STOPS[trip.type] ?: continue
            if (stopKey !in tripStops) continue

            val arrivalTime = addMinutes(trip.departureTime, stop.offsetMinutes)
            val arrivalMins = timeToMinutes(arrivalTime)
            results.add(
                BusArrival(
                    arrivalTime = arrivalTime,
                    minutesAway = arrivalMins,
                    destination = destinations[trip.type] ?: "",
                    tripType = trip.type
                )
            )
        }
        return results
    }
}
