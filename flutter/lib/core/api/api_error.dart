/// Client-side mirror of the locked `ErrorResponse` contract
/// (`contracts.md` §2/§4): `{code, message, details}`.
class ApiError {
  const ApiError({
    required this.code,
    required this.message,
    this.details = const {},
  });

  factory ApiError.fromJson(Map<String, dynamic> json) => ApiError(
    code: json['code'] as String? ?? 'ERROR',
    message: json['message'] as String? ?? 'Unknown error',
    details: (json['details'] as Map?)?.cast<String, dynamic>() ?? const {},
  );

  final String code;
  final String message;
  final Map<String, dynamic> details;
}
