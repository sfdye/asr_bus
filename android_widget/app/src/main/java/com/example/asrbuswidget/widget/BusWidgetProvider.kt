package com.example.asrbuswidget.widget

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.util.TypedValue
import android.view.View
import android.widget.RemoteViews
import com.example.asrbuswidget.R
import com.example.asrbuswidget.data.BusSchedule
import com.example.asrbuswidget.data.HolidayRepository
import com.example.asrbuswidget.model.BusResult
import com.example.asrbuswidget.util.LocationHelper
import com.example.asrbuswidget.util.ScheduleCalculator
import com.example.asrbuswidget.util.getSGTime
import java.util.Locale

class BusWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        val pendingResult = goAsync()
        Thread {
            try {
                for (appWidgetId in appWidgetIds) {
                    updateWidget(context, appWidgetManager, appWidgetId)
                }
            } finally {
                pendingResult.finish()
            }
        }.start()
        scheduleNextUpdate(context)
    }

    override fun onAppWidgetOptionsChanged(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int, newOptions: Bundle) {
        val pendingResult = goAsync()
        Thread {
            try {
                updateWidget(context, appWidgetManager, appWidgetId)
            } finally {
                pendingResult.finish()
            }
        }.start()
    }

    override fun onEnabled(context: Context) {
        scheduleNextUpdate(context)
    }

    override fun onDisabled(context: Context) {
        cancelUpdates(context)
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_REFRESH) {
            val forceRefresh = intent.getBooleanExtra(EXTRA_FORCE_REFRESH, false)
            val pendingResult = goAsync()
            Thread {
                try {
                    val appWidgetManager = AppWidgetManager.getInstance(context)
                    val ids = appWidgetManager.getAppWidgetIds(
                        ComponentName(context, BusWidgetProvider::class.java)
                    )
                    for (id in ids) {
                        updateWidget(context, appWidgetManager, id, forceRefresh)
                    }
                } finally {
                    pendingResult.finish()
                }
            }.start()
            scheduleNextUpdate(context)
        }
    }

    companion object {
        const val ACTION_REFRESH = "com.example.asrbuswidget.ACTION_REFRESH"
        private const val EXTRA_FORCE_REFRESH = "force_refresh"
        private const val PREFS_NAME = "com.example.asrbuswidget.widget"
        private const val PREF_STOP_PREFIX = "stop_"
        private const val PREF_SCALE_PREFIX = "scale_"
        private const val UPDATE_INTERVAL_MS = 5 * 60 * 1000L

        fun saveStopPref(context: Context, appWidgetId: Int, stopKey: String) {
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .edit()
                .putString(PREF_STOP_PREFIX + appWidgetId, stopKey)
                .apply()
        }

        fun loadStopPref(context: Context, appWidgetId: Int): String {
            return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .getString(PREF_STOP_PREFIX + appWidgetId, "asr") ?: "asr"
        }

        fun deleteStopPref(context: Context, appWidgetId: Int) {
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .edit()
                .remove(PREF_STOP_PREFIX + appWidgetId)
                .remove(PREF_SCALE_PREFIX + appWidgetId)
                .apply()
        }

        fun saveTextScale(context: Context, appWidgetId: Int, scale: Float) {
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .edit()
                .putFloat(PREF_SCALE_PREFIX + appWidgetId, scale)
                .apply()
        }

        fun loadTextScale(context: Context, appWidgetId: Int): Float {
            return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .getFloat(PREF_SCALE_PREFIX + appWidgetId, 1.0f)
        }

        private fun getScale(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int): Float {
            val options = appWidgetManager.getAppWidgetOptions(appWidgetId)
            val minHeight = options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT, 110)
            val sizeScale = when {
                minHeight >= 200 -> 1.8f
                minHeight >= 150 -> 1.4f
                else -> 1.0f
            }
            val userScale = loadTextScale(context, appWidgetId)
            return sizeScale * userScale
        }

        fun updateWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int, forceRefresh: Boolean = false) {
            val stopKey = loadStopPref(context, appWidgetId)
            val isAuto = stopKey == "auto"
            val resolvedStop = resolveStop(context, stopKey)

            val holidays = try {
                HolidayRepository(context).getHolidays(forceRefresh)
            } catch (_: Exception) {
                null
            }

            val now = getSGTime()
            val locale = Locale.getDefault()
            val result = ScheduleCalculator.getNextBuses(resolvedStop, now, holidays, locale)
            val stop = BusSchedule.STOPS[resolvedStop]
            val scale = getScale(context, appWidgetManager, appWidgetId)

            val views = RemoteViews(context.packageName, R.layout.widget_bus)

            when (result) {
                is BusResult.NoSundayService -> {
                    showStatus(views, if (locale.language == "zh") "🚌 周日无班车" else "🚌 No Sun service", scale)
                }
                is BusResult.NoMoreBuses -> {
                    showStatus(views, if (locale.language == "zh") "🚌 今日已无班车" else "🚌 No more bus today", scale)
                }
                is BusResult.Upcoming -> {
                    showBusInfo(views, result, stop, resolvedStop, locale, isAuto, scale)
                }
            }

            val refreshIntent = Intent(context, BusWidgetProvider::class.java).apply {
                action = ACTION_REFRESH
                putExtra(EXTRA_FORCE_REFRESH, true)
            }
            val pendingIntent = PendingIntent.getBroadcast(
                context, 0, refreshIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_root, pendingIntent)

            appWidgetManager.updateAppWidget(appWidgetId, views)
        }

        private fun resolveStop(context: Context, stopKey: String): String {
            if (stopKey != "auto") return stopKey
            return try {
                val hasPerm = androidx.core.content.ContextCompat.checkSelfPermission(
                    context, android.Manifest.permission.ACCESS_COARSE_LOCATION
                ) == android.content.pm.PackageManager.PERMISSION_GRANTED
                if (!hasPerm) return "asr"

                val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as android.location.LocationManager

                var location = locationManager.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER)
                if (location == null) {
                    location = locationManager.getLastKnownLocation(android.location.LocationManager.NETWORK_PROVIDER)
                }
                if (location == null) {
                    location = locationManager.getLastKnownLocation(android.location.LocationManager.FUSED_PROVIDER)
                }

                if (location == null) {
                    val latch = java.util.concurrent.CountDownLatch(1)
                    var freshLocation: android.location.Location? = null
                    val listener = object : android.location.LocationListener {
                        override fun onLocationChanged(loc: android.location.Location) {
                            freshLocation = loc
                            latch.countDown()
                            locationManager.removeUpdates(this)
                        }
                        @Deprecated("Deprecated") override fun onStatusChanged(p: String?, s: Int, e: android.os.Bundle?) {}
                        override fun onProviderEnabled(p: String) {}
                        override fun onProviderDisabled(p: String) {}
                    }
                    val provider = when {
                        locationManager.isProviderEnabled(android.location.LocationManager.GPS_PROVIDER) -> android.location.LocationManager.GPS_PROVIDER
                        locationManager.isProviderEnabled(android.location.LocationManager.NETWORK_PROVIDER) -> android.location.LocationManager.NETWORK_PROVIDER
                        else -> null
                    }
                    if (provider != null) {
                        locationManager.requestSingleUpdate(provider, listener, android.os.Looper.getMainLooper())
                        latch.await(5, java.util.concurrent.TimeUnit.SECONDS)
                        location = freshLocation
                    }
                }

                if (location != null) LocationHelper.getNearestStop(location) else "asr"
            } catch (_: Exception) {
                "asr"
            }
        }

        private fun showStatus(views: RemoteViews, message: String, scale: Float) {
            views.setViewVisibility(R.id.text_stop_name, View.GONE)
            views.setViewVisibility(R.id.text_minutes, View.GONE)
            views.setViewVisibility(R.id.text_arrival_time, View.GONE)
            views.setViewVisibility(R.id.text_destination, View.GONE)
            views.setViewVisibility(R.id.text_next_bus, View.GONE)
            views.setViewVisibility(R.id.text_status, View.VISIBLE)
            views.setTextViewText(R.id.text_status, message)
            views.setTextViewTextSize(R.id.text_status, TypedValue.COMPLEX_UNIT_SP, 16f * scale)
        }

        private fun showBusInfo(
            views: RemoteViews,
            result: BusResult.Upcoming,
            stop: com.example.asrbuswidget.model.Stop?,
            stopKey: String,
            locale: Locale,
            isAuto: Boolean,
            scale: Float
        ) {
            views.setViewVisibility(R.id.text_stop_name, View.VISIBLE)
            views.setViewVisibility(R.id.text_minutes, View.VISIBLE)
            views.setViewVisibility(R.id.text_arrival_time, View.VISIBLE)
            views.setViewVisibility(R.id.text_destination, View.VISIBLE)
            views.setViewVisibility(R.id.text_next_bus, View.VISIBLE)
            views.setViewVisibility(R.id.text_status, View.GONE)

            val name = if (locale.language == "zh") stop?.nameZh else stop?.nameEn
            val header = if (isAuto) "📍 ${name ?: "ASR"}" else "🚌 ${name ?: "ASR"}"
            views.setTextViewText(R.id.text_stop_name, header)
            views.setTextViewTextSize(R.id.text_stop_name, TypedValue.COMPLEX_UNIT_SP, 15f * scale)

            val bus = result.buses[0]
            val minLabel = if (locale.language == "zh") "分钟" else "min"
            if (bus.minutesAway <= 60) {
                views.setTextViewText(R.id.text_minutes, "~${bus.minutesAway} $minLabel")
                views.setTextViewText(R.id.text_arrival_time, bus.arrivalTime)
            } else {
                val hrs = String.format("%.1f", bus.minutesAway / 60.0).replace("\\.0$".toRegex(), "")
                val hrsLabel = if (locale.language == "zh") "约${hrs}小时后" else "in ~$hrs hrs"
                views.setTextViewText(R.id.text_minutes, bus.arrivalTime)
                views.setTextViewText(R.id.text_arrival_time, hrsLabel)
            }
            views.setTextViewTextSize(R.id.text_minutes, TypedValue.COMPLEX_UNIT_SP, 32f * scale)
            views.setTextViewTextSize(R.id.text_arrival_time, TypedValue.COMPLEX_UNIT_SP, 16f * scale)

            val destLabel = if (stopKey == "asr") "→ ${bus.destination}" else "→ 🏠 ASR"
            views.setTextViewText(R.id.text_destination, destLabel)
            views.setTextViewTextSize(R.id.text_destination, TypedValue.COMPLEX_UNIT_SP, 14f * scale)

            if (result.buses.size > 1) {
                val next = result.buses[1]
                val nextPrefix = if (locale.language == "zh") "下一班:" else "Next:"
                val nextLabel = if (stopKey == "asr") "$nextPrefix ${next.arrivalTime} → ${next.destination}" else "$nextPrefix ${next.arrivalTime}"
                views.setTextViewText(R.id.text_next_bus, nextLabel)
                views.setTextViewTextSize(R.id.text_next_bus, TypedValue.COMPLEX_UNIT_SP, 14f * scale)
                views.setViewVisibility(R.id.text_next_bus, View.VISIBLE)
            } else {
                views.setViewVisibility(R.id.text_next_bus, View.GONE)
            }
        }

        fun scheduleNextUpdate(context: Context) {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(context, BusWidgetProvider::class.java).apply {
                action = ACTION_REFRESH
            }
            val pendingIntent = PendingIntent.getBroadcast(
                context, 1, intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            val triggerAt = SystemClock.elapsedRealtime() + UPDATE_INTERVAL_MS

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !alarmManager.canScheduleExactAlarms()) {
                alarmManager.setAndAllowWhileIdle(
                    AlarmManager.ELAPSED_REALTIME_WAKEUP,
                    triggerAt,
                    pendingIntent
                )
            } else {
                alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.ELAPSED_REALTIME_WAKEUP,
                    triggerAt,
                    pendingIntent
                )
            }
        }

        fun cancelUpdates(context: Context) {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(context, BusWidgetProvider::class.java).apply {
                action = ACTION_REFRESH
            }
            val pendingIntent = PendingIntent.getBroadcast(
                context, 1, intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            alarmManager.cancel(pendingIntent)
        }
    }
}
