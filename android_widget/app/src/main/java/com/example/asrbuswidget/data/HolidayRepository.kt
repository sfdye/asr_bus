package com.example.asrbuswidget.data

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

class HolidayRepository(private val context: Context) {

    private val url = "https://raw.githubusercontent.com/sfdye/asr_bus/master/ios_widget/holidays.json"
    private val cacheFileName = "holidays_cache.json"
    private val cacheMaxAgeMs = 7 * 24 * 60 * 60 * 1000L

    fun getHolidays(forceRefresh: Boolean = false): Map<String, List<String>>? {
        if (!forceRefresh) {
            val cacheFile = File(context.filesDir, cacheFileName)
            if (cacheFile.exists() && System.currentTimeMillis() - cacheFile.lastModified() < cacheMaxAgeMs) {
                return loadFromCache()
            }
        }
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
        return obj.keys().asSequence().associate { year ->
            val array = obj.getJSONArray(year)
            year to (0 until array.length()).map { array.getString(it) }
        }
    }
}
