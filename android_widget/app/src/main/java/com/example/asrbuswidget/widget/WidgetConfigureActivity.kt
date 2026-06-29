package com.example.asrbuswidget.widget

import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.asrbuswidget.ui.theme.ASRBusWidgetTheme

class WidgetConfigureActivity : ComponentActivity() {

    private var appWidgetId = AppWidgetManager.INVALID_APPWIDGET_ID
    private val selectedStop = mutableStateOf("asr")
    private val textScale = mutableFloatStateOf(1.0f)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setResult(RESULT_CANCELED)

        appWidgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID
        ) ?: AppWidgetManager.INVALID_APPWIDGET_ID

        if (appWidgetId == AppWidgetManager.INVALID_APPWIDGET_ID) {
            finish()
            return
        }

        if (savedInstanceState != null) {
            selectedStop.value = savedInstanceState.getString("selectedStop", "asr")
            textScale.floatValue = savedInstanceState.getFloat("textScale", 1.0f)
        } else {
            selectedStop.value = BusWidgetProvider.loadStopPref(this, appWidgetId)
            textScale.floatValue = BusWidgetProvider.loadTextScale(this, appWidgetId)
        }

        setContent {
            ASRBusWidgetTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    ConfigureScreen(
                        modifier = Modifier.padding(innerPadding),
                        selectedStop = selectedStop.value,
                        textScale = textScale.floatValue,
                        onStopSelected = { selectedStop.value = it },
                        onTextScaleChanged = { textScale.floatValue = it },
                        onConfirm = { confirmSelection() }
                    )
                }
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString("selectedStop", selectedStop.value)
        outState.putFloat("textScale", textScale.floatValue)
    }

    private fun confirmSelection() {
        BusWidgetProvider.saveStopPref(this, appWidgetId, selectedStop.value)
        BusWidgetProvider.saveTextScale(this, appWidgetId, textScale.floatValue)

        val appWidgetManager = AppWidgetManager.getInstance(this)
        Thread {
            BusWidgetProvider.updateWidget(this, appWidgetManager, appWidgetId)
        }.start()
        BusWidgetProvider.scheduleNextUpdate(this)

        val resultValue = Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        setResult(RESULT_OK, resultValue)
        finish()
    }
}

data class StopOption(val key: String, val labelEn: String, val labelZh: String)

private val STOP_OPTIONS = listOf(
    StopOption("asr", "🏠 ASR", "🏠 ASR"),
    StopOption("outram6", "🚇 Outram Exit 6", "🚇 欧南园6号口"),
    StopOption("outram7", "🚇 Outram Exit 7", "🚇 欧南园7号口"),
    StopOption("harbourfront", "🛍️ Harbourfront", "🛍️ 港湾"),
    StopOption("auto", "📍 Auto (GPS)", "📍 自动定位 (GPS)"),
)

@Composable
fun ConfigureScreen(
    modifier: Modifier = Modifier,
    selectedStop: String,
    textScale: Float,
    onStopSelected: (String) -> Unit,
    onTextScaleChanged: (Float) -> Unit,
    onConfirm: () -> Unit
) {
    val locale = java.util.Locale.getDefault()
    val isZh = locale.language == "zh"

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp)
    ) {
        Text(
            text = if (isZh) "选择站点" else "Select Stop",
            style = MaterialTheme.typography.headlineMedium
        )

        Spacer(modifier = Modifier.height(16.dp))

        for (option in STOP_OPTIONS) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onStopSelected(option.key) }
                    .padding(vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                RadioButton(
                    selected = selectedStop == option.key,
                    onClick = { onStopSelected(option.key) }
                )
                Text(
                    text = if (isZh) option.labelZh else option.labelEn,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.padding(start = 8.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = if (isZh) "文字大小" else "Text Size",
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("A", style = MaterialTheme.typography.bodySmall)
            Slider(
                value = textScale,
                onValueChange = onTextScaleChanged,
                valueRange = 0.8f..1.6f,
                steps = 3,
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 8.dp)
            )
            Text("A", style = MaterialTheme.typography.headlineSmall)
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = onConfirm,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(if (isZh) "确认" else "Confirm")
        }
    }
}
