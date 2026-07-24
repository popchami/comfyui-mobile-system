import 'dart:convert';

import 'app_profile.dart';

class LocalProfile {
  const LocalProfile({
    required this.id,
    required this.name,
    required this.profileVersion,
    required this.workflowId,
    required this.savedAt,
    required this.rawAppProfileJson,
    required this.rawWorkflowJson,
    this.comfyUrl = '',
  });

  final String id;
  final String name;
  final String profileVersion;
  final String workflowId;
  final DateTime savedAt;
  final Map<String, dynamic> rawAppProfileJson;
  final Map<String, dynamic> rawWorkflowJson;
  final String comfyUrl;

  AppProfile get appProfile => AppProfile.fromJson(rawAppProfileJson);

  factory LocalProfile.fromBundle({
    required Map<String, dynamic> appProfileJson,
    required Map<String, dynamic> workflowJson,
    String comfyUrl = '',
  }) {
    final id = appProfileJson['profile_id'] as String? ?? 'profile_${DateTime.now().millisecondsSinceEpoch}';
    return LocalProfile(
      id: id,
      name: appProfileJson['profile_name'] as String? ?? id,
      profileVersion: appProfileJson['profile_version'] as String? ?? '0.0.0',
      workflowId: appProfileJson['workflow_id'] as String? ?? '',
      savedAt: DateTime.now(),
      rawAppProfileJson: appProfileJson,
      rawWorkflowJson: workflowJson,
      comfyUrl: comfyUrl,
    );
  }

  factory LocalProfile.fromJson(Map<String, dynamic> json) {
    return LocalProfile(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      profileVersion: json['profileVersion'] as String? ?? '0.0.0',
      workflowId: json['workflowId'] as String? ?? '',
      savedAt: DateTime.tryParse(json['savedAt'] as String? ?? '') ?? DateTime.fromMillisecondsSinceEpoch(0),
      rawAppProfileJson: _decodeMap(json['rawAppProfileJson']),
      rawWorkflowJson: _decodeMap(json['rawWorkflowJson']),
      comfyUrl: json['comfyUrl'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'profileVersion': profileVersion,
      'workflowId': workflowId,
      'savedAt': savedAt.toIso8601String(),
      'rawAppProfileJson': rawAppProfileJson,
      'rawWorkflowJson': rawWorkflowJson,
      'comfyUrl': comfyUrl,
    };
  }

  String encode() => jsonEncode(toJson());

  static LocalProfile decode(String value) {
    final decoded = jsonDecode(value);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('LocalProfile JSON is not an object');
    }
    return LocalProfile.fromJson(decoded);
  }

  static Map<String, dynamic> _decodeMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return <String, dynamic>{};
  }
}
