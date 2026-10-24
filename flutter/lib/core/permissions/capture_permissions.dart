/// Permission rationale scaffolding for the Sensory Moment Vault (HWGA05).
///
/// CAMERA and RECORD_AUDIO are declared in the manifest but are only ever
/// requested in-context, when the user starts the matching capture — never at
/// app launch (TRD §7). Runtime request plumbing arrives with the capture UI;
/// this file pins the user-facing rationale copy so it stays consistent.
abstract final class CapturePermissions {
  static const cameraRationale =
      'Photos you capture are stored privately on your own server. '
      'Nothing is shared or uploaded anywhere else.';

  static const microphoneRationale =
      'Audio capsules and voice scraps are recorded only when you tap record. '
      'Voice notes may be transcribed on your server; ambient audio never leaves it.';
}
