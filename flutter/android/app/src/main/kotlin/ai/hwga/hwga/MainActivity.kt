package ai.hwga.hwga

import android.content.Intent
import ai.hwga.hwga.widget.QuickTapsWidgetProvider
import ai.hwga.hwga.widget.WidgetStore
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    // singleTop: keep the latest deep-link intent visible to getLaunchUri.
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "ai.hwga.hwga/widget",
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "sync" -> {
                    val token = call.argument<String>("token")
                    val baseUrl = call.argument<String>("baseUrl") ?: ""
                    val stateJson = call.argument<String>("stateJson")
                    WidgetStore.mirror(this, token, baseUrl, stateJson)
                    QuickTapsWidgetProvider.requestRefresh(this)
                    result.success(null)
                }
                // Cold-start deep-link URI so Dart can route (V2C: hwga://auth).
                "getLaunchUri" -> result.success(intent?.dataString)
                else -> result.notImplemented()
            }
        }
    }
}
