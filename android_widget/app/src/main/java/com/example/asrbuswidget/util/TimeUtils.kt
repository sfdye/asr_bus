package com.example.asrbuswidget.util

import java.util.Calendar
import java.util.TimeZone

enum class DayType { WEEKDAY, SATURDAY, SUNDAY }

fun getSGTime(): Calendar {
    return Calendar.getInstance(TimeZone.getTimeZone("Asia/Singapore"))
}

fun timeToMinutes(timeStr: String): Int {
    val parts = timeStr.split(":")
    return parts[0].toInt() * 60 + parts[1].toInt()
}

fun addMinutes(timeStr: String, mins: Int): String {
    val total = timeToMinutes(timeStr) + mins
    val h = total / 60
    val m = total % 60
    return "%02d:%02d".format(h, m)
}

fun getDayType(date: Calendar, holidays: Map<String, List<String>>?): DayType {
    val day = date.get(Calendar.DAY_OF_WEEK)
    if (day == Calendar.SUNDAY) return DayType.SUNDAY
    if (day == Calendar.SATURDAY || isHoliday(date, holidays)) return DayType.SATURDAY
    return DayType.WEEKDAY
}

fun isHoliday(date: Calendar, holidays: Map<String, List<String>>?): Boolean {
    if (holidays == null) return false
    val year = date.get(Calendar.YEAR).toString()
    val dateStr = "%d-%02d-%02d".format(
        date.get(Calendar.YEAR),
        date.get(Calendar.MONTH) + 1,
        date.get(Calendar.DAY_OF_MONTH)
    )
    return holidays[year]?.contains(dateStr) == true
}
