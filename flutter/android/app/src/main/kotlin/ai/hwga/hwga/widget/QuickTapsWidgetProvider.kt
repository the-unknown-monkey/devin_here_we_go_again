package ai.hwga.hwga.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.view.View
import android.widget.RemoteViews
import ai.hwga.hwga.MainActivity
import ai.hwga.hwga.R
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

/**
 * Quick-taps widget (V2C): six CONFIRMATION/QUIET_MOMENT taps, each POSTing
 * /events with a fresh UUID idempotency_key per user tap. Rendering always
 * reflects the last known truth — sending / saved / failed states are shown
 * explicitly, never implied.
 */
class QuickTapsWidgetProvider : AppWidgetProvider() {

    private data class Tap(val label: String, val type: String, val kind: String?)

    companion object {
        const val ACTION_TAP = "ai.hwga.hwga.action.QUICK_TAP"
        const val EXTRA_TAP_LABEL = "tap_label"

        private val TAPS = listOf(
            Tap("WATER", "CONFIRMATION", "WATER"),
            Tap("FOOD", "CONFIRMATION", "FOOD_CLEAN"),
            Tap("STRETCH", "CONFIRMATION", "STRETCH"),
            Tap("POSTURE", "CONFIRMATION", "POSTURE_RESET"),
            Tap("WALK", "CONFIRMATION", "WALK"),
            Tap("QUIET", "QUIET_MOMENT", null),
        )

        private val BUTTON_IDS = intArrayOf(
            R.id.btn_water, R.id.btn_food, R.id.btn_stretch,
            R.id.btn_posture, R.id.btn_walk, R.id.btn_quiet,
        )

        fun widgetIds(context: Context): IntArray =
            AppWidgetManager.getInstance(context).getAppWidgetIds(
                ComponentName(context, QuickTapsWidgetProvider::class.java)
            )

        /** Ask the platform to run the normal update path for all instances. */
        fun requestRefresh(context: Context) {
            val ids = widgetIds(context)
            if (ids.isEmpty()) return
            context.sendBroadcast(
                Intent(context, QuickTapsWidgetProvider::class.java)
                    .setAction(AppWidgetManager.ACTION_APPWIDGET_UPDATE)
                    .putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, ids)
            )
        }
    }

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray,
    ) {
        // Render the last known state immediately, then refresh it.
        for (id in appWidgetIds) updateOne(context, appWidgetManager, id, null)
        val pending = goAsync()
        Thread {
            try {
                fetchState(context)
                for (id in appWidgetIds) {
                    updateOne(context, appWidgetManager, id, null)
                }
            } finally {
                pending.finish()
            }
        }.start()
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION_TAP) {
            super.onReceive(context, intent)
            return
        }
        val label = intent.getStringExtra(EXTRA_TAP_LABEL) ?: return
        val tap = TAPS.firstOrNull { it.label == label } ?: return
        val mgr = AppWidgetManager.getInstance(context)
        val ids = widgetIds(context)
        val pending = goAsync()
        Thread {
            try {
                handleTap(context, mgr, ids, tap)
            } finally {
                pending.finish()
            }
        }.start()
    }

    private fun handleTap(
        context: Context,
        mgr: AppWidgetManager,
        ids: IntArray,
        tap: Tap,
    ) {
        val baseUrl = WidgetStore.baseUrl(context)
        val token = WidgetStore.readToken(context)
        if (baseUrl == null || token == null) {
            for (id in ids) updateOne(context, mgr, id, null)
            return
        }
        for (id in ids) updateOne(context, mgr, id, "Sending…")
        val result = WidgetApi.postEvent(
            baseUrl, token, tap.type, tap.kind, UUID.randomUUID().toString(),
        )
        when (result) {
            is WidgetApi.Result.Ok -> {
                fetchState(context)
                for (id in ids) updateOne(context, mgr, id, "Saved")
            }
            is WidgetApi.Result.HttpError ->
                for (id in ids) updateOne(
                    context, mgr, id, "Failed (HTTP ${result.code})",
                )
            WidgetApi.Result.NetworkError ->
                for (id in ids) updateOne(
                    context, mgr, id, "Not sent — no connection",
                )
        }
    }

    private fun fetchState(context: Context) {
        val baseUrl = WidgetStore.baseUrl(context) ?: return
        val token = WidgetStore.readToken(context) ?: return
        val res = WidgetApi.getWidgetState(baseUrl, token)
        if (res is WidgetApi.Result.Ok && res.body != null) {
            WidgetStore.cacheState(context, res.body.toString())
        }
    }

    private fun updateOne(
        context: Context,
        mgr: AppWidgetManager,
        id: Int,
        status: String?,
    ) {
        mgr.updateAppWidget(id, buildViews(context, id, status))
    }

    private fun buildViews(context: Context, widgetId: Int, status: String?): RemoteViews {
        val views = RemoteViews(context.packageName, R.layout.widget_quick_taps)
        val baseUrl = WidgetStore.baseUrl(context)
        val token = WidgetStore.readToken(context)

        when {
            baseUrl == null -> {
                views.setTextViewText(
                    R.id.widget_status,
                    "Open the app once to finish setup",
                )
                views.setViewVisibility(R.id.widget_status, View.VISIBLE)
                setOpenAppIntent(context, views, "hwga://auth")
            }
            token == null -> {
                views.setTextViewText(
                    R.id.widget_status,
                    "Set up your token in the app",
                )
                views.setViewVisibility(R.id.widget_status, View.VISIBLE)
                setOpenAppIntent(context, views, "hwga://auth")
            }
            else -> {
                renderState(context, views, status)
                for ((i, tap) in TAPS.withIndex()) {
                    views.setOnClickPendingIntent(
                        BUTTON_IDS[i], tapIntent(context, widgetId, tap),
                    )
                }
                setOpenAppIntent(context, views, "hwga://today")
            }
        }
        return views
    }

    private fun renderState(context: Context, views: RemoteViews, status: String?) {
        val state = WidgetStore.cachedState(context)
        val confirmations = state?.optJSONObject("today_confirmations")
        val quietToday = state?.optInt("quiet_moments_today", -1) ?: -1
        for ((i, tap) in TAPS.withIndex()) {
            val count = if (tap.kind != null) {
                confirmations?.optInt(tap.kind, -1) ?: -1
            } else {
                quietToday
            }
            views.setTextViewText(
                BUTTON_IDS[i],
                if (count >= 0) "${tap.label}\n$count" else "${tap.label}\n—",
            )
        }
        val freshness = state?.optString("generated_at")
            ?.let { formatInstant(it) }
        views.setTextViewText(R.id.widget_updated, freshness ?: "")
        if (status != null) {
            views.setTextViewText(R.id.widget_status, status)
            views.setViewVisibility(R.id.widget_status, View.VISIBLE)
        } else if (state == null) {
            views.setTextViewText(R.id.widget_status, "No data yet")
            views.setViewVisibility(R.id.widget_status, View.VISIBLE)
        } else {
            views.setViewVisibility(R.id.widget_status, View.GONE)
        }
    }

    private fun formatInstant(raw: String): String = runCatching {
        val parser = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
            .apply { timeZone = TimeZone.getTimeZone("UTC") }
        val instant = parser.parse(raw.substringBefore('.').substringBefore('+'))
        "as of " + SimpleDateFormat("HH:mm", Locale.getDefault()).format(instant!!)
    }.getOrDefault("")

    private fun tapIntent(context: Context, widgetId: Int, tap: Tap): PendingIntent {
        val intent = Intent(context, QuickTapsWidgetProvider::class.java)
            .setAction(ACTION_TAP)
            .putExtra(EXTRA_TAP_LABEL, tap.label)
        return PendingIntent.getBroadcast(
            context,
            widgetId * 100 + TAPS.indexOf(tap),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun setOpenAppIntent(context: Context, views: RemoteViews, uri: String) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(uri), context, MainActivity::class.java)
        val pending = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        views.setOnClickPendingIntent(R.id.widget_root, pending)
    }
}
