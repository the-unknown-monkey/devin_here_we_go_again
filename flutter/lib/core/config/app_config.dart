/// Compile-time app configuration.
///
/// The phone reaches the dev backend through `adb reverse tcp:8000 tcp:8000`
/// (D15), so `127.0.0.1:8000` on the device is correct (some devices cannot resolve `localhost`). Demo/ngrok builds pass
/// a different origin with `--dart-define=HWGA_API_BASE_URL=...`; tunnel URLs
/// are never committed.
abstract final class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'HWGA_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  /// Optional dev-only seed for the token field
  /// (`--dart-define=HWGA_DEV_TOKEN=...`). Never committed; the real token is
  /// kept in platform secure storage via [TokenStore].
  static const String devToken = String.fromEnvironment('HWGA_DEV_TOKEN');
}
