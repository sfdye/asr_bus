package com.example.asrbuswidget.data

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

class HolidayRepository(private val context: Context) {

    private val url = "https://raw.githubusercontent.com/sfdye/asr_bus/master/ios_widget/holidays.json"
    private val cacheFileName = "holidays_cache.json"

    fun getHolidays(): Map<String, List<String>>? {
        return try {
            val json = fetchFromNetwork()
            saveToCache(json)
            parseHolidays(json)
        } catch (_: Exception) {
            loadFromCache()
        }
    }

    private fun fetchFromNetwork(): String {
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.connectTimeout = 5000
        connection.readTimeout = 5000
        return try {
            connection.inputStream.bufferedReader().readText()
        } finally {
            connection.disconnect()
        }
    }

    private fun saveToCache(json: String) {
        try {
            File(context.filesDir, cacheFileName).writeText(json)
        } catch (_: Exception) {}
    }

    private fun loadFromCache(): Map<String, List<String>>? {
        return try {
            val file = File(context.filesDir, cacheFileName)
            if (file.exists()) parseHolidays(file.readText()) else null
        } catch (_: Exception) {
            null
        }
    }

    private fun parseHolidays(json: String): Map<String, List<String>> {
        val obj = JSONObject(json)
        val result = mutableMapOf<String, List<String>>()
        for (year in obj.keys()) {
            val array = obj.getJSONArray(year)
            val dates = mutableListOf<String>()
            for (i in 0 until array.length()) {
                dates.add(array.getString(i))
            }
            result[year] = dates
        }
        return result
    }
}
