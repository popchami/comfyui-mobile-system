import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../models/remote_profile.dart';

class ComfyApiClient {
  ComfyApiClient({required String baseUrl}) : baseUri = Uri.parse(_normalizeBaseUrl(baseUrl));

  final Uri baseUri;

  static String _normalizeBaseUrl(String value) {
    return value.endsWith('/') ? value.substring(0, value.length - 1) : value;
  }

  static String _joinPaths(String basePath, String childPath) {
    final left = basePath.endsWith('/') ? basePath.substring(0, basePath.length - 1) : basePath;
    final right = childPath.startsWith('/') ? childPath.substring(1) : childPath;
    if (left.isEmpty || left == '/') return '/$right';
    return '$left/$right';
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    return baseUri.replace(
      path: _joinPaths(baseUri.path, path),
      queryParameters: query,
    );
  }

  Future<Map<String, dynamic>> getSystemStats() async {
    final response = await http.get(_uri('/system_stats'));
    return _decodeJsonResponse(response);
  }

  Future<Map<String, dynamic>> getObjectInfo() async {
    final response = await http.get(_uri('/object_info'));
    return _decodeJsonResponse(response);
  }

  Future<List<String>> getModels({String folder = 'checkpoints'}) async {
    final response = await http.get(_uri('/models/$folder'));
    final decoded = _decodeJson(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ComfyApiException('Models request failed: HTTP ${response.statusCode}: ${response.body}');
    }
    if (decoded is List) {
      return decoded.map((value) => value.toString()).toList();
    }
    throw ComfyApiException('Models response is not a list');
  }

  Future<List<RemoteProfile>> getRemoteProfiles() async {
    final response = await http.get(_uri('/mobile_analyzer/profiles'));
    final decoded = _decodeJson(response);
    if (decoded is! List<dynamic>) {
      throw ComfyApiException('Profile list response is not a list');
    }
    return decoded
        .whereType<Map<String, dynamic>>()
        .map(RemoteProfile.fromJson)
        .where((profile) => profile.id.isNotEmpty)
        .toList();
  }

  Future<List<int>> downloadProfileZip(String profileId) async {
    final response = await http.get(_uri('/mobile_analyzer/profiles/$profileId/download'));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ComfyApiException('Download failed: ${response.statusCode}');
    }
    return response.bodyBytes;
  }

  Future<String> queuePrompt({
    required Map<String, dynamic> workflow,
    String? clientId,
  }) async {
    final body = <String, dynamic>{'prompt': workflow};
    if (clientId != null && clientId.isNotEmpty) {
      body['client_id'] = clientId;
    }

    final response = await http.post(
      _uri('/prompt'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    final decoded = _decodeJsonResponse(response);
    final promptId = decoded['prompt_id'];
    if (promptId is String && promptId.isNotEmpty) return promptId;
    throw ComfyApiException('prompt_id missing from /prompt response');
  }

  Future<Map<String, dynamic>> getQueue() async {
    final response = await http.get(_uri('/queue'));
    return _decodeJsonResponse(response);
  }

  Future<void> interrupt() async {
    final response = await http.post(_uri('/interrupt'));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ComfyApiException('Interrupt failed: HTTP ${response.statusCode}: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getHistory(String promptId) async {
    final response = await http.get(_uri('/history/$promptId'));
    return _decodeJsonResponse(response);
  }

  Uri buildViewUri({
    required String filename,
    String subfolder = '',
    String type = 'output',
  }) {
    return _uri('/view', {
      'filename': filename,
      'subfolder': subfolder,
      'type': type,
    });
  }

  Future<String> uploadImage(File file) async {
    final request = http.MultipartRequest('POST', _uri('/upload/image'));
    request.fields['type'] = 'input';
    request.fields['overwrite'] = 'true';
    request.files.add(await http.MultipartFile.fromPath('image', file.path));

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);
    final decoded = _decodeJsonResponse(response);
    final name = decoded['name'] ?? decoded['filename'];
    if (name is String && name.isNotEmpty) return name;
    throw ComfyApiException('Uploaded image name missing from response');
  }

  Map<String, dynamic> _decodeJsonResponse(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ComfyApiException('HTTP ${response.statusCode}: ${response.body}');
    }
    final decoded = _decodeJson(response);
    if (decoded is Map<String, dynamic>) return decoded;
    throw ComfyApiException('Response is not a JSON object');
  }

  dynamic _decodeJson(http.Response response) {
    try {
      return jsonDecode(response.body);
    } catch (e) {
      throw ComfyApiException('Invalid JSON response: $e');
    }
  }
}

class ComfyApiException implements Exception {
  ComfyApiException(this.message);

  final String message;

  @override
  String toString() => 'ComfyApiException: $message';
}
