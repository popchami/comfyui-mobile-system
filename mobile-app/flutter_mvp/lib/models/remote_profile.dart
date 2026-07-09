class RemoteProfile {
  const RemoteProfile({
    required this.id,
    required this.name,
    required this.file,
    required this.status,
    required this.sizeBytes,
    required this.modifiedAt,
    required this.downloadUrl,
  });

  final String id;
  final String name;
  final String file;
  final String status;
  final int sizeBytes;
  final String modifiedAt;
  final String downloadUrl;

  factory RemoteProfile.fromJson(Map<String, dynamic> json) {
    return RemoteProfile(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? json['id'] as String? ?? 'profile',
      file: json['file'] as String? ?? '',
      status: json['status'] as String? ?? '',
      sizeBytes: _asInt(json['size_bytes']),
      modifiedAt: json['modified_at'] as String? ?? '',
      downloadUrl: json['download_url'] as String? ?? '',
    );
  }

  static int _asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }
}
