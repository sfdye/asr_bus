package com.example.asrbuswidget

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.asrbuswidget.data.BusSchedule
import com.example.asrbuswidget.model.BusArrival
import com.example.asrbuswidget.model.BusResult
import com.example.asrbuswidget.ui.theme.ASRBusWidgetTheme
import com.example.asrbuswidget.util.DayType
import com.example.asrbuswidget.util.ScheduleCalculator
import com.example.asrbuswidget.util.getDayType
import com.example.asrbuswidget.util.getSGTime
import com.example.asrbuswidget.util.timeToMinutes
import java.util.Calendar
import java.util.Locale

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ASRBusWidgetTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    ScheduleScreen(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

@Composable
fun ScheduleScreen(modifier: Modifier = Modifier) {
    val locale = Locale.getDefault()
    val isZh = locale.language == "zh"
    val now = remember { getSGTime() }
    val dayType = remember { getDayType(now, null) }
    val selectedStop = remember { mutableStateOf("asr") }

    val stopKeys = BusSchedule.STOPS.keys.toList()
    val result = remember(selectedStop.value) {
        ScheduleCalculator.getNextBuses(selectedStop.value, now, null, locale)
    }
    val allTrips = remember(selectedStop.value) {
        ScheduleCalculator.getAllTripsForStop(selectedStop.value, dayType, locale)
    }

    Column(modifier = modifier.padding(16.dp)) {
        Text(
            text = if (isZh) "🚌 ASR 班车" else "🚌 ASR Bus",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )

        val dayLabel = when (dayType) {
            DayType.WEEKDAY -> if (isZh) "工作日" else "Weekday"
            DayType.SATURDAY -> if (isZh) "周六" else "Saturday"
            DayType.SUNDAY -> if (isZh) "周日（无服务）" else "Sunday (No Service)"
        }
        Text(
            text = dayLabel,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            for (key in stopKeys) {
                val stop = BusSchedule.STOPS[key]!!
                val label = if (isZh) stop.nameZh else stop.nameEn
                FilterChip(
                    selected = selectedStop.value == key,
                    onClick = { selectedStop.value = key },
                    label = { Text(label, fontSize = 12.sp) }
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        when (result) {
            is BusResult.NoSundayService -> {
                StatusCard(if (isZh) "周日无班车服务" else "No service on Sundays")
            }
            is BusResult.NoMoreBuses -> {
                StatusCard(if (isZh) "今日已无班车" else "No more buses today")
            }
            is BusResult.Upcoming -> {
                NextBusCard(result.buses[0], selectedStop.value, isZh)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = if (isZh) "今日时刻表" else "Today's Schedule",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(8.dp))

        val nowMins = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE)

        LazyColumn {
            items(allTrips) { trip ->
                val isPast = timeToMinutes(trip.arrivalTime) < nowMins
                ScheduleRow(trip, selectedStop.value, isZh, isPast)
            }
        }
    }
}

@Composable
fun StatusCard(message: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(text = message, style = MaterialTheme.typography.bodyLarge)
        }
    }
}

@Composable
fun NextBusCard(bus: BusArrival, stopKey: String, isZh: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            val minLabel = if (isZh) "分钟" else "min"
            Text(
                text = "~${bus.minutesAway} $minLabel",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Text(
                text = bus.arrivalTime,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )
            val dest = if (stopKey == "asr") "→ ${bus.destination}" else "→ 🏠 ASR"
            Text(
                text = dest,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
fun ScheduleRow(trip: BusArrival, stopKey: String, isZh: Boolean, isPast: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (isPast) 0.4f else 1f)
            .padding(vertical = 8.dp, horizontal = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = trip.arrivalTime,
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = if (!isPast) FontWeight.Medium else FontWeight.Normal
        )
        val dest = if (stopKey == "asr") trip.destination else "🏠 ASR"
        Text(
            text = dest,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
