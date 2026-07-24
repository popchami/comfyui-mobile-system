import 'dart:convert';

import 'package:archive/archive.dart';

import '../models/app_profile.dart';

class ProfileZipBundle {
  const ProfileZipBundle({
    required this.appProfile,
    required this.workflow,
    required this.rawAppProfileJson,
    required this.rawWorkflowJson,
  });

  final AppProfile appProfile;
  final Map<String, dynamic> workflow;
  final Map<String, dynamic> rawAppProfileJson;
  final Map<String, dynamic> rawWorkflowJson;
}

class ProfileZipService {
  static ProfileZipBundle parseProfileZip(List<int> bytes) {
    final archive = ZipDecoder().decodeBytes(bytes);

    final appProfileFile = _findFile(archive, 'app_profile.json');
    final workflowFile = _findFile(archive, 'workflow.json');

    final appProfileText = utf8.decode(appProfileFile.content as List<int>);
    final workflowText = utf8.decode(workflowFile.content as List<int>);

    final appProfileJson = _decodeObject(appProfileText, 'app_profile.json');
    final workflowJson = _decodeObject(workflowText, 'workflow.json');

    _validateProfileJson(appProfileJson, workflowJson);

    return ProfileZipBundle(
      appProfile: AppProfile.fromJson(appProfileJson),
      workflow: workflowJson,
      rawAppProfileJson: appProfileJson,
      rawWorkflowJson: workflowJson,
    );
  }

  static ArchiveFile _findFile(Archive archive, String name) {
    for (final file in archive.files) {
      if (file.name == name && file.isFile) {
        return file;
      }
    }
    throw ProfileZipException('Missing $name in profile zip');
  }

  static Map<String, dynamic> _decodeObject(String text, String filename) {
    final decoded = jsonDecode(text);
    if (decoded is Map<String, dynamic>) return decoded;
    throw ProfileZipException('$filename is not a JSON object');
  }

  static void _validateProfileJson(Map<String, dynamic> appProfile, Map<String, dynamic> workflow) {
    if ((appProfile['schema_version'] as String? ?? '').isEmpty) {
      throw ProfileZipException('app_profile.json missing schema_version');
    }
    if (appProfile['ui'] is! Map<String, dynamic>) {
      throw ProfileZipException('app_profile.json missing ui');
    }
    if (appProfile['patch_targets'] is! List<dynamic>) {
      throw ProfileZipException('app_profile.json missing patch_targets');
    }
    if (workflow.isEmpty) {
      throw ProfileZipException('workflow.json is empty');
    }
  }
}

class ProfileZipException implements Exception {
  ProfileZipException(this.message);

  final String message;

  @override
  String toString() => 'ProfileZipException: $message';
}
