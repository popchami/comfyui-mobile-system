import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class ComfyApiClient {
  ComfyApiClient({required String baseUrl}) : baseUri = Uri.parse(_normalizeBaseUrl(baseUrl));

  final Uri baseUri;

  static String _normalizeBaseUrl(String value) {
    return value.endsWith('/') ? value.substring(0, value.length - 1) : value;
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return baseUri.replace(
      path: normalizedPath,
      queryParameters: query,
    );
  }

  Future<Map<String, dynamic>> getSystemStats() async {
    final response = await http.get(_uri('/system_stats'));
    return _decodeJsonResponse(response);
  }

  Future<List<dynamic>> getRemoteProfiles() async {
    final response = await http.get(_uri('/mobile_analyzer/profiles'));
    final decoded = _decodeJson(response);
    if (decoded is List<dynamic>) return decoded;
    throw ComfyApiException('Profile list response is not a list');
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
